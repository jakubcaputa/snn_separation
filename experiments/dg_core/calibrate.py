"""
dg_core/calibrate.py — kalibracja obwodu do zadanego PUNKTU PRACY.

Po co to istnieje
-----------------
Dotąd parametry ustawiało się suwakami i sprawdzało, co wyszło. To nie skaluje
się do publikacji: każdy późniejszy wynik (gabazyna, utrata MC, zmiana
pobudliwości) trzeba odnosić do warunku kontrolnego, który ma uzasadnienie
eksperymentalne, a nie do arbitralnej pozycji suwaka.

Tutaj odwracamy kierunek: podajemy SPECYFIKACJĘ punktu pracy (właściwości błony,
prawdopodobieństwo AP po pulsie, bilans hamowania, zakresy częstotliwości),
a kod dobiera parametry tak, żeby ją spełnić — i **uczciwie raportuje, czego
spełnić się nie da**.

Dlaczego to nie jest ślepy optymalizator
----------------------------------------
Problem rozkłada się na kroki, z których każdy jest albo zamknięty analitycznie,
albo jednowymiarowym, monotonicznym szukaniem pierwiastka:

  krok 1  (b, K)      ← właściwości błony            — ZAMKNIĘTY WZÓR
  krok 2  W_PP_GC     ← docelowe P(AP | puls)        — bisekcja 1D
  krok 3  W_FS_GC     ← docelowy bilans toniczne:fazowe — bisekcja 1D
  krok 4  weryfikacja częstotliwości w pełnym obwodzie — pomiar, nie strojenie

Ślepa optymalizacja po 8 parametrach dałaby liczby bez interpretacji; ten podział
daje przy każdym kroku zdanie, które da się napisać w Methods.

Kluczowa własność modelu, którą krok 1 ujawnia
-----------------------------------------------
Dla neuronu Izhikevicza z tonicznym K punkty stałe są pierwiastkami
`0.04·v² + (5−b)·v + (140−K) = 0`, więc:

    V_rest + V_th_eff = −(5−b)/0.04     ← zależy WYŁĄCZNIE od b
    V_th_eff − V_rest = √((5−b)² − 0.16·(140−K)) / 0.04

Czyli **b ustawia SUMĘ obu napięć, a K ich ODSTĘP**. Przy domyślnym b = 0.2 para
(V_rest, V_th) jest zamknięta na sumie −120 mV: można mieć (−70, −50), ale
(−70, −45) jest nieosiągalne bez ruszenia b — a po zmianie b na 0.4 wymagane K
rośnie do 14, czyli POWYŻEJ obecnych 10, nie poniżej. To jest nieoczywiste
i dlatego liczy to kod, a nie intuicja.

Użycie
------
    python -m dg_core.calibrate --preset madar      # z katalogu experiments/
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from brian2 import (
    BrianLogger, Hz, Network, NeuronGroup, PoissonGroup, SpikeGeneratorGroup,
    SpikeMonitor, Synapses, defaultclock, ms, mV, prefs, start_scope,
)

from .circuit import _on_pre, make_connectivity, simulate
from .params import (
    A_GC, B_GC, C_GC, D_GC, DGConfig, DT_MS, TAU_EX_GC, TAU_IN_GC,
)
from .patterns import make_input_spikes, make_patterns

prefs.codegen.target = 'numpy'


# ══════════════════════════════════════════════════════════════════════════════
# Specyfikacja punktu pracy
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class OperatingPoint:
    """
    Czego OCZEKUJEMY od obwodu — nie jak go ustawić.

    Wartości domyślne są zakotwiczone w pracy Madara tam, gdzie on je podaje,
    a w pozostałych miejscach są JAWNYMI ZNAKAMI ZAPYTANIA (patrz `OPEN`).
    Gdy przyjdą odpowiedzi od strony biologicznej, zmieniamy liczby tutaj —
    i nic poza tym plikiem.
    """

    # ── Właściwości błony GC (Madar: natywne wartości GC) ────────────────────
    v_rest_mv: float = -70.0
    v_th_mv: float = -50.0

    # ── P(AP | puls stymulacyjny) ────────────────────────────────────────────
    # Madar (2. praca): „intensywność dobrana tak, by dawała ~50% prawdopodobieństwa
    # AP (zakres 20–80%)".
    p_spike_target: float = 0.45
    p_spike_lo: float = 0.20
    p_spike_hi: float = 0.80

    # Tło synaptyczne w protokole pulsowym — odwzorowuje bieżący napęd sieci.
    # BEZ niego (i bez p_rel < 1) P(AP) jest zero-jedynkowe i cel jest nieosiągalny.
    bg_rate_hz: float = 40.0
    bg_w_mv: float = 4.0

    # ── Bilans hamowania GC ──────────────────────────────────────────────────
    # Ułamek CAŁEGO hamowania GC, który ma pochodzić ze składnika TONICZNEGO.
    # None = nie kalibruj (zostaw jak jest) — bo to jest pytanie otwarte do
    # strony biologicznej. W obecnym modelu wychodzi ≈0.74, co jest wartością
    # przyjętą przypadkiem, a nie wybraną.
    tonic_share: float | None = None

    # ── Zakresy częstotliwości (weryfikacja, nie cel optymalizacji) ──────────
    fr_gc_hz: tuple[float, float] = (2.0, 6.0)      # GC „we wzorcu" — rzadkie kodowanie DG
    fr_fs_hz: tuple[float, float] = (10.0, 40.0)    # OTWARTE: czy 46 Hz to za dużo?
    fr_hmc_hz: tuple[float, float] = (1.0, 15.0)    # OTWARTE: dziś 0 Hz, czyli MC martwe

    def open_questions(self) -> list[str]:
        """Które elementy specyfikacji czekają na rozstrzygnięcie od biologii."""
        out = []
        if self.tonic_share is None:
            out.append("tonic_share — jaki jest realny udział prądu tonicznego "
                       "w całkowitym hamowaniu GC? (dziś w modelu ≈0.74, wartość przypadkowa)")
        out.append(f"fr_fs_hz={self.fr_fs_hz} — czy to fizjologiczny zakres bazowy dla FS? "
                   f"(model daje 46 Hz, a FS nie mają w nim żadnego hamowania synaptycznego)")
        out.append("kotwica: in vitro (Madar, plaster, ~50% P(AP)) czy in vivo "
                   "(GC znacznie rzadsze)? To dwa różne punkty pracy.")
        return out


# Preset „jak u Madara" — zakres, który on sam podaje.
PRESET_MADAR = OperatingPoint()

# Preset dosłownie z uwag biologicznych: spoczynek −70, próg −45.
# UWAGA: ta para NIE jest osiągalna przy b = 0.2 (patrz docstring modułu) —
# kalibracja sama to wykryje i zmieni b.
PRESET_STRICT = OperatingPoint(v_rest_mv=-70.0, v_th_mv=-45.0)


# ══════════════════════════════════════════════════════════════════════════════
# Krok 1 — właściwości błony: (b, K) w postaci zamkniętej
# ══════════════════════════════════════════════════════════════════════════════

def izh_fixed_points(K: float, b: float = B_GC) -> tuple[float, float]:
    """
    (V_rest, V_th_eff) neuronu Izhikevicza z tonicznym prądem K.

    V_rest  = stabilny punkt stały (spoczynek)
    V_th_eff = NIESTABILNY punkt stały = rzeczywisty próg pobudliwości.
               To NIE jest `v >= 30 mV` z kodu — tamto jest tylko odcięciem
               szczytu iglicy, bo Izhikevich nie ma jawnego progu.
    """
    disc = (5.0 - b) ** 2 - 4 * 0.04 * (140.0 - K)
    if disc < 0:
        return float('nan'), float('nan')      # brak punktów stałych → odpala samoistnie
    r = np.sqrt(disc)
    return (-(5.0 - b) - r) / 0.08, (-(5.0 - b) + r) / 0.08


def solve_b_K(v_rest: float, v_th: float) -> tuple[float, float]:
    """
    Odwrotność `izh_fixed_points`: jakie (b, K) dają zadaną parę napięć.

    b bierze się z SUMY napięć, K z ich ODSTĘPU — patrz docstring modułu.
    Rozwiązanie jest jednoznaczne i zamknięte, więc nie ma tu żadnej optymalizacji.
    """
    s, d = v_rest + v_th, v_th - v_rest
    if d <= 0:
        raise ValueError(f"V_th ({v_th}) musi być powyżej V_rest ({v_rest})")
    b = 5.0 + 0.04 * s
    K = 140.0 - ((5.0 - b) ** 2 - (0.04 * d) ** 2) / 0.16
    return b, K


def g_crit(K: float) -> float:
    """Minimalny napęd synaptyczny [mV] potrzebny do odpalenia: G_crit = 4 + K."""
    return 4.0 + K


# ══════════════════════════════════════════════════════════════════════════════
# Krok 2 — P(AP | puls) i dobór wagi
# ══════════════════════════════════════════════════════════════════════════════

def measure_p_spike(W_pulse: float, K: float, p_rel: float = 1.0,
                    bg_rate_hz: float = 40.0, bg_w_mv: float = 4.0,
                    tau_ex: float = TAU_EX_GC, a: float = A_GC, b: float = B_GC,
                    c: float = C_GC, d: float = D_GC,
                    n_pulses: int = 60, isi_ms: float = 80.0,
                    win_ms: float = 15.0, n_cells: int = 60,
                    seed: int | None = None) -> float:
    """
    P(AP | puls) dla POJEDYNCZEJ komórki — protokół stymulacyjny jak u Madara.

    Dlaczego osobna symulacja, a nie odczyt z obwodu: w sieci wejście PP jest
    ciągłym strumieniem Poissona, więc „prawdopodobieństwo AP po pulsie" nie jest
    tam w ogóle zdefiniowane. To jest pomiar KALIBRACYJNY, nie wynik sieci.

    Bez źródła zmienności (p_rel = 1 i brak tła) wynik jest zero-jedynkowy.
    """
    start_scope()
    defaultclock.dt = DT_MS * ms
    if seed is not None:
        np.random.seed(seed)
    if p_rel < 1.0 or bg_rate_hz > 0:
        BrianLogger.suppress_name('base')

    T = n_pulses * isi_ms + 4 * win_ms
    eqs = (
        f"dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms"
        f" + g_ex/ms + g_bg/ms - {K}*mV/ms) : volt (unless refractory)\n"
        f"dg_ex/dt = -g_ex/({tau_ex}*ms) : volt\n"
        f"dg_bg/dt = -g_bg/({tau_ex}*ms) : volt\n"
        f"du/dt = {a}/ms*({b}*v - u) : volt\n"
    )
    cell = NeuronGroup(n_cells, eqs, threshold='v >= 30*mV',
                       reset=f'v = {c}*mV; u = u + {d}*mV',
                       refractory=2 * ms, method='euler')
    cell.v = -70 * mV
    cell.u = b * (-70 * mV)

    pulse_t = np.arange(1, n_pulses + 1) * isi_ms
    stim = SpikeGeneratorGroup(1, np.zeros(n_pulses, dtype=int), pulse_t * ms)
    s = Synapses(stim, cell, on_pre=_on_pre('g_ex', W_pulse, p_rel))
    s.connect()
    objs = [cell, stim, s]

    if bg_rate_hz > 0:
        bg = PoissonGroup(n_cells, bg_rate_hz * Hz)
        sb = Synapses(bg, cell, on_pre=_on_pre('g_bg', bg_w_mv, p_rel))
        sb.connect(j='i')
        objs += [bg, sb]

    sm = SpikeMonitor(cell)
    objs.append(sm)
    Network(*objs).run(T * ms)

    ti = np.array(sm.t / ms)
    ii = np.array(sm.i)
    hits = sum(len(np.unique(ii[(ti > p) & (ti <= p + win_ms)])) for p in pulse_t)
    return hits / (n_pulses * n_cells)


def solve_weight_for_p_spike(target: float, K: float, p_rel: float = 1.0,
                             bg_rate_hz: float = 40.0, bg_w_mv: float = 4.0,
                             w_lo: float = 0.5, w_hi: float = 40.0,
                             tol: float = 0.03, max_iter: int = 12,
                             **kw) -> tuple[float, float]:
    """
    Bisekcja po wadze pulsu, aż P(AP) trafi w `target` z tolerancją `tol`.

    P(AP) jest niemalejące względem wagi, więc bisekcja jest tu właściwym
    narzędziem. Zwraca (waga, osiągnięte P(AP)).

    Gdy krzywa jest SKOKOWA (brak źródła zmienności), bisekcja zbiegnie do
    progu skoku i zwróci P(AP) daleki od celu — to nie jest błąd, tylko
    poprawna informacja, że przy tych ustawieniach cel jest nieosiągalny.
    Rozpoznaje to `calibrate()` i mówi o tym wprost.
    """
    f = lambda w: measure_p_spike(w, K, p_rel, bg_rate_hz, bg_w_mv, **kw)
    p_lo, p_hi = f(w_lo), f(w_hi)
    if p_hi < target:                      # nawet maksymalna waga nie wystarcza
        return w_hi, p_hi
    if p_lo > target:                      # nawet minimalna waga już przestrzeliwuje
        return w_lo, p_lo

    best_w, best_p = w_hi, p_hi
    for _ in range(max_iter):
        w_mid = 0.5 * (w_lo + w_hi)
        p_mid = f(w_mid)
        if abs(p_mid - target) < abs(best_p - target):
            best_w, best_p = w_mid, p_mid
        if abs(p_mid - target) <= tol:
            return w_mid, p_mid
        if p_mid < target:
            w_lo = w_mid
        else:
            w_hi = w_mid
    return best_w, best_p


# ══════════════════════════════════════════════════════════════════════════════
# Krok 3 — bilans hamowania GC
# ══════════════════════════════════════════════════════════════════════════════

def measure_inhibition_balance(cfg: DGConfig, seed: int = 0) -> dict:
    """
    Zmierzony bilans hamowania GC: składnik toniczny (K) vs fazowy (FS→GC).

    Oba są w tych samych jednostkach (wkład do dv/dt), więc porównują się wprost.
    """
    pats, _ = make_patterns(cfg.N_GC, 3, 0.75, 0.25, seed=42)
    conn = make_connectivity(cfg, seed=seed)
    idx, t = make_input_spikes(pats[0], cfg, seed=1042)
    out = simulate(cfg, idx, t, conn, record_flows=True)
    phasic = float(out['flows']['fs_gc'])
    tonic = float(cfg.K_GC)
    total = tonic + phasic
    return {
        'phasic': phasic,
        'tonic': tonic,
        'tonic_share': tonic / total if total > 0 else float('nan'),
        'fr_gc_pattern': float(out['gc_rates'][pats[0]].mean()),
        'fr_gc_all': float(out['gc_rates'].mean()),
        'fr_fs': float(out['fs_rates'].mean()),
        'fr_hmc': float(out['hmc_rates'].mean()),
        'active_frac': float((out['gc_rates'] > 0.5).mean()),
    }


def solve_w_fs_gc_for_share(cfg: DGConfig, target_share: float,
                            w_lo: float = 0.1, w_hi: float = 8.0,
                            tol: float = 0.02, max_iter: int = 10) -> tuple[float, float]:
    """
    Bisekcja po W_FS_GC, aż udział składnika tonicznego spadnie do `target_share`.

    Większe W_FS_GC → większe hamowanie fazowe → MNIEJSZY udział tonicznego,
    więc funkcja jest malejąca i bisekcja idzie w odwrotną stronę niż zwykle.
    """
    f = lambda w: measure_inhibition_balance(replace(cfg, W_FS_GC=w))['tonic_share']
    s_lo, s_hi = f(w_lo), f(w_hi)
    if s_lo < target_share:      # nawet najsłabsze hamowanie fazowe już przeważa
        return w_lo, s_lo
    if s_hi > target_share:      # nawet najsilniejsze nie wystarcza
        return w_hi, s_hi

    best_w, best_s = w_hi, s_hi
    for _ in range(max_iter):
        w_mid = 0.5 * (w_lo + w_hi)
        s_mid = f(w_mid)
        if abs(s_mid - target_share) < abs(best_s - target_share):
            best_w, best_s = w_mid, s_mid
        if abs(s_mid - target_share) <= tol:
            return w_mid, s_mid
        if s_mid > target_share:
            w_lo = w_mid
        else:
            w_hi = w_mid
    return best_w, best_s


# ══════════════════════════════════════════════════════════════════════════════
# Kalibracja
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CalibrationReport:
    """Co osiągnięto, czego nie, i dlaczego. Nigdy nie udaje sukcesu."""
    cfg: DGConfig
    b_gc: float
    checks: list[tuple[str, str, str, bool]]   # (nazwa, cel, osiągnięte, ok)
    notes: list[str]

    @property
    def ok(self) -> bool:
        return all(c[3] for c in self.checks)

    def render(self) -> str:
        w = max(len(c[0]) for c in self.checks) + 2
        lines = ["", "═" * 78, "  RAPORT KALIBRACJI", "═" * 78,
                 f"  {'wielkość'.ljust(w)}{'cel'.ljust(22)}{'osiągnięte'.ljust(22)}status",
                 "  " + "─" * 74]
        for name, want, got, ok in self.checks:
            lines.append(f"  {name.ljust(w)}{want.ljust(22)}{got.ljust(22)}"
                         f"{'OK' if ok else 'NIE'}")
        if self.notes:
            lines += ["", "  UWAGI:"]
            lines += [f"    • {n}" for n in self.notes]
        lines += ["", "═" * 78,
                  f"  WYNIK: {'punkt pracy osiągnięty' if self.ok else 'punkt pracy NIEOSIĄGNIĘTY'}",
                  "═" * 78, ""]
        return "\n".join(lines)


def calibrate(base: DGConfig, spec: OperatingPoint,
              p_rel_gc: float = 1.0, verbose: bool = True) -> CalibrationReport:
    """
    Dobiera parametry obwodu tak, by spełnić `spec` — i raportuje, czego nie da się spełnić.

    Zwraca `CalibrationReport`; skalibrowana konfiguracja jest w `.cfg`.
    Parametr `b` neuronu GC wychodzi poza `DGConfig` (jest stałą modułu), więc
    raport podaje go osobno w `.b_gc` — jeśli różni się od domyślnego, wymaga
    ręcznej zmiany w `params.py` i jest to w raporcie powiedziane wprost.
    """
    checks: list[tuple[str, str, str, bool]] = []
    notes: list[str] = []
    say = (lambda s: print(s, flush=True)) if verbose else (lambda s: None)

    # ── Krok 1: właściwości błony → (b, K), zamknięty wzór ───────────────────
    say("krok 1/4  właściwości błony → (b, K)  [wzór zamknięty]")
    b_gc, K_gc = solve_b_K(spec.v_rest_mv, spec.v_th_mv)
    vr, vt = izh_fixed_points(K_gc, b_gc)
    checks.append(("V_rest GC", f"{spec.v_rest_mv:.1f} mV", f"{vr:.1f} mV",
                   abs(vr - spec.v_rest_mv) < 0.5))
    checks.append(("V_th_eff GC", f"{spec.v_th_mv:.1f} mV", f"{vt:.1f} mV",
                   abs(vt - spec.v_th_mv) < 0.5))
    checks.append(("K_tonic GC", "(wynikowe)", f"{K_gc:.2f}", True))

    if abs(b_gc - B_GC) > 1e-6:
        notes.append(
            f"Żądana para napięć wymaga b = {b_gc:.3f}, a domyślne b = {B_GC}. "
            f"Przy b = {B_GC} suma V_rest + V_th jest ZABLOKOWANA na "
            f"{-(5 - B_GC) / 0.04:.0f} mV, więc tej pary nie da się osiągnąć żadnym K. "
            f"Kalibracja ustawia b = {b_gc:.3f} w konfiguracji, ale to jest ZMIANA "
            f"MODELU NEURONU (sprzężenia u↔v), a nie dobór parametru obwodu — "
            f"wymaga świadomej decyzji i opisu w Methods."
        )
    if K_gc < 0:
        notes.append(f"Wynikowe K = {K_gc:.2f} jest UJEMNE, czyli toniczny prąd musiałby "
                     f"pobudzać, a nie hamować. Cel jest poza zakresem tego modelu.")

    # b_gc MUSI wejść do konfiguracji, inaczej krok 4 mierzyłby częstotliwości
    # innego neuronu niż ten, dla którego kroki 1–2 wyliczyły próg i wagę.
    cfg = replace(base, K_GC=max(0.0, K_gc), b_gc=b_gc)

    # ── Krok 2: waga PP→GC → docelowe P(AP | puls), bisekcja 1D ──────────────
    say(f"krok 2/4  waga PP→GC → P(AP|puls) = {spec.p_spike_target:.2f}  [bisekcja]")
    w_pp, p_got = solve_weight_for_p_spike(
        spec.p_spike_target, K_gc, p_rel_gc, spec.bg_rate_hz, spec.bg_w_mv, b=b_gc)
    in_band = spec.p_spike_lo <= p_got <= spec.p_spike_hi
    checks.append(("P(AP | puls)", f"{spec.p_spike_target:.2f} "
                                   f"[{spec.p_spike_lo:.1f}–{spec.p_spike_hi:.1f}]",
                   f"{p_got:.2f}", in_band))
    checks.append(("W PP→GC", "(wynikowe)", f"{w_pp:.2f} mV", True))
    if not in_band:
        notes.append(
            f"P(AP) = {p_got:.2f} jest poza pasmem Madara. Przy p_rel = {p_rel_gc:.2f} "
            f"krzywa jest praktycznie skokowa — bez zawodności synaptycznej nie ma "
            f"czym wytworzyć pośredniego prawdopodobieństwa. Uruchom z p_rel < 1.0."
        )
    cfg = replace(cfg, W_PP_GC=w_pp)

    # ── Krok 3: bilans hamowania GC (opcjonalnie — czeka na biologię) ────────
    if spec.tonic_share is None:
        say("krok 3/4  bilans hamowania — POMINIĘTY (tonic_share nierozstrzygnięty)")
        bal = measure_inhibition_balance(cfg)
        checks.append(("udział tonicznego", "(nierozstrzygnięty)",
                       f"{bal['tonic_share']:.2f}", True))
        notes.append(
            f"Udział składnika tonicznego w hamowaniu GC wynosi {bal['tonic_share']:.0%} "
            f"(toniczne {bal['tonic']:.1f} vs fazowe {bal['phasic']:.2f} mV/ms). "
            f"To jest wartość WYNIKOWA, nie wybrana — czeka na rozstrzygnięcie, "
            f"ile powinna wynosić. Ustaw `tonic_share` w specyfikacji, gdy będzie znana."
        )
    else:
        say(f"krok 3/4  waga FS→GC → udział tonicznego = {spec.tonic_share:.2f}  [bisekcja]")
        w_fs, s_got = solve_w_fs_gc_for_share(cfg, spec.tonic_share)
        cfg = replace(cfg, W_FS_GC=w_fs)
        checks.append(("udział tonicznego", f"{spec.tonic_share:.2f}", f"{s_got:.2f}",
                       abs(s_got - spec.tonic_share) < 0.05))
        checks.append(("W FS→GC", "(wynikowe)", f"{w_fs:.2f} mV", True))
        bal = measure_inhibition_balance(cfg)

    # ── Krok 4: weryfikacja częstotliwości w PEŁNYM obwodzie ─────────────────
    say("krok 4/4  weryfikacja częstotliwości w pełnym obwodzie")
    for label, val, rng in [
        ("FR GC (we wzorcu)", bal['fr_gc_pattern'], spec.fr_gc_hz),
        ("FR FS", bal['fr_fs'], spec.fr_fs_hz),
        ("FR HMC", bal['fr_hmc'], spec.fr_hmc_hz),
    ]:
        checks.append((label, f"{rng[0]:.0f}–{rng[1]:.0f} Hz", f"{val:.2f} Hz",
                       rng[0] <= val <= rng[1]))
    checks.append(("frakcja aktywnych GC", "(kontrola)", f"{bal['active_frac']:.0%}", True))

    # ── Spójność reżimów wejścia ─────────────────────────────────────────────
    # Waga jest dobierana protokołem PULSOWYM (rzadkie zdarzenia + tło bg_rate_hz),
    # a potem używana w sieci przy CIĄGŁYM napędzie r_high. Jeśli te dwa reżimy
    # różnią się o rząd wielkości, jedna waga nie może obsłużyć obu — i to jest
    # pytanie „in vitro czy in vivo" w wersji liczbowej, a nie retorycznej.
    g_ss = cfg.r_high * cfg.W_PP_GC * TAU_EX_GC * 1e-3     # stan ustalony g_ex [mV]
    gc_thr = g_crit(cfg.K_GC)
    ratio = cfg.r_high / spec.bg_rate_hz if spec.bg_rate_hz > 0 else float('inf')
    checks.append(("napęd ustalony g_ex", f"< G_crit = {gc_thr:.1f} mV",
                   f"{g_ss:.1f} mV", g_ss < gc_thr))
    if ratio > 3.0:
        notes.append(
            f"NIESPÓJNOŚĆ REŻIMÓW: wagę dobrano przy tle {spec.bg_rate_hz:.0f} Hz "
            f"(protokół pulsowy), a w sieci działa ona przy napędzie "
            f"{cfg.r_high:.0f} Hz — {ratio:.0f}× większym. Stąd g_ex w stanie "
            f"ustalonym = {g_ss:.1f} mV wobec progu {gc_thr:.1f} mV i częstotliwość "
            f"GC {bal['fr_gc_pattern']:.0f} Hz zamiast {spec.fr_gc_hz[0]:.0f}–"
            f"{spec.fr_gc_hz[1]:.0f} Hz. JEDNA waga nie obsłuży obu reżimów — trzeba "
            f"zdecydować, który jest warunkiem kontrolnym: rzadka stymulacja "
            f"in vitro (Madar) czy gęsty napęd PP. To jest pytanie nr 3 z maila, "
            f"tyle że policzone."
        )

    if bal['fr_hmc'] < 0.05:
        notes.append(
            f"HMC strzelają {bal['fr_hmc']:.2f} Hz, czyli są MARTWE: napęd GC→HMC "
            f"({cfg.W_GC_HMC:.1f} mV) nie zbliża się do progu G_crit = "
            f"{g_crit(cfg.K_HMC):.0f} mV. Żaden wniosek o roli mossy cells nie "
            f"dotyczy w tym stanie obwodu z MC — dotyczy obwodu bez nich."
        )
    if bal['fr_fs'] > spec.fr_fs_hz[1]:
        notes.append(
            f"FS strzelają {bal['fr_fs']:.0f} Hz, powyżej zakładanego zakresu. "
            f"W modelu FS nie mają ŻADNEGO hamowania synaptycznego (brak FS→FS), "
            f"więc K_tonic jest ich jedynym hamulcem — to jest najprawdopodobniej "
            f"przyczyna, a nie dobór wag."
        )

    return CalibrationReport(cfg=cfg, b_gc=b_gc, checks=checks, notes=notes)


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main(argv=None):
    import argparse

    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--preset', choices=['madar', 'strict'], default='madar',
                    help="madar = (−70, −50), osiągalne przy b=0.2; "
                         "strict = (−70, −45), wymaga zmiany b")
    ap.add_argument('--p-rel', type=float, default=1.0,
                    help="zawodność synaptyczna PP→GC; < 1.0 potrzebne, "
                         "żeby P(AP) w ogóle było stopniowane")
    ap.add_argument('--tonic-share', type=float, default=None,
                    help="docelowy udział hamowania tonicznego w GC (0–1); "
                         "pominięcie = nie kalibruj, tylko zmierz")
    args = ap.parse_args(argv)

    spec = {'madar': PRESET_MADAR, 'strict': PRESET_STRICT}[args.preset]
    if args.tonic_share is not None:
        spec = replace(spec, tonic_share=args.tonic_share)

    print(f"\nPreset: {args.preset}   p_rel(PP→GC) = {args.p_rel}")
    print(f"Cel: V_rest = {spec.v_rest_mv} mV, V_th = {spec.v_th_mv} mV, "
          f"P(AP) = {spec.p_spike_target}\n")

    rep = calibrate(DGConfig(), spec, p_rel_gc=args.p_rel)
    print(rep.render())

    print("  PYTANIA OTWARTE (czekają na stronę biologiczną):")
    for q in spec.open_questions():
        print(f"    ? {q}")
    print()
    return 0 if rep.ok else 1


if __name__ == '__main__':
    sys.exit(main())
