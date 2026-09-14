"""
dg_core/params.py — konfiguracja obwodu DG dla eksperymentów.

Reżim częstotliwości PP pochodzi z JEDYNEGO ŹRÓDŁA PRAWDY w korzeniu repo
(`dg_params.py`): 40 włókien × 10/1 Hz → 400/40 Hz aggregate, output GC ~6 Hz.
Reszta wartości domyślnych = domyślne suwaki `interactive_dg.py`, żeby wyniki
eksperymentów były porównywalne z tym, co użytkownik widzi w narzędziu.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, replace

# Kanon częstotliwości trzymamy w jednym miejscu — importujemy z korzenia repo.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from dg_params import (  # noqa: E402
    N_FIBERS_PER_GC,
    R_FIBER_ACTIVE,
    R_FIBER_BG,
    R_EFF_HIGH,
    R_EFF_LOW,
    W_PP_GC_IZH,
)

# ── Stałe symulacji ───────────────────────────────────────────────────────────
DT_MS = 0.1
T_MS = 600.0

# ── Parametry Izhikevicza (jak w interactive_dg.py) ───────────────────────────
A_GC, B_GC, C_GC, D_GC = 0.02, 0.2, -65.0, 6.0
A_FS, B_FS, C_FS, D_FS = 0.10, 0.2, -65.0, 2.0
A_HMC, B_HMC, C_HMC, D_HMC = 0.02, 0.2, -65.0, 4.0

TAU_EX_GC = 5.0
TAU_IN_GC = 8.0
TAU_EX_FS = 3.0
TAU_EX_HMC = 5.0

PP_DELAY = 4.0
SYN_DELAY = 1.0


@dataclass(frozen=True)
class DGConfig:
    """Pełna konfiguracja obwodu DG. Zamrożona → można jej używać jako klucza cache."""

    # rozmiar sieci
    N_GC: int = 200
    N_FS: int = 20
    N_HMC: int = 10

    # motywy hamowania (to są „gracze" w analizie Shapleya, kierunek 4)
    enable_ff: bool = True     # PP → FS → GC   (feedforward)
    enable_fb: bool = True     # GC → FS → GC   (feedback)
    enable_hmc: bool = True    # GC → HMC → {FS, GC}  (mossy cells)

    # wagi synaptyczne [mV]
    W_PP_GC: float = W_PP_GC_IZH   # 4.0
    W_PP_FS: float = 0.25
    W_GC_FS: float = 10.0
    W_FS_GC: float = 1.0
    W_GC_HMC: float = 1.0
    W_HMC_FS: float = 1.0
    W_HMC_GC: float = 0.5

    # FS → HMC — hamowanie NA mossy cells.
    # DOMYŚLNIE 0.0 = wyłączone → obwód identyczny z interactive_dg.py.
    # Istnieje, bo pętla GC→HMC→GC jest czysto pobudzająca i bez hamulca ucieka
    # (patrz README: MC są albo nieistotne, albo eksplodują — brak reżimu pośredniego).
    # W biologii mossy cells dostają silne hamowanie z interneuronów hilusa.
    W_FS_HMC: float = 0.0
    P_FS_HMC: float = 0.40

    # FS → FS — wzajemne hamowanie interneuronów. DOMYŚLNIE 0.0 = wyłączone.
    # Istnieje, bo w modelu FS nie mają ŻADNEGO hamowania synaptycznego (kanał
    # g_in po prostu nie był w ich równaniu), przez co K_tonic jest ich jedynym
    # hamulcem i strzelają ~46 Hz przy domyślnych ustawieniach, a po kalibracji
    # membranowej nawet ~180 Hz. W biologii koszykowe hamują się wzajemnie i to
    # ta pętla ustala rytm gamma — brak tego kanału jest najprawdopodobniejszą
    # strukturalną przyczyną zawyżonej częstotliwości FS.
    W_FS_FS: float = 0.0
    P_FS_FS: float = 0.30

    # pobudliwość (prąd toniczny hamujący; G_crit = 4 + K)
    K_GC: float = 10.0
    K_FS: float = 5.0
    K_HMC: float = 10.0

    # Parametr `b` neuronu GC (sprzężenie u↔v w modelu Izhikevicza).
    # Jest w konfiguracji, a nie tylko stałą modułu, bo steruje SUMĄ napięć
    # spoczynku i progu: V_rest + V_th_eff = −(5−b)/0.04. Przy b = 0.2 ta suma
    # jest zablokowana na −120 mV, więc np. pary (−70, −45) nie da się uzyskać
    # żadnym K. Kalibracja (`calibrate.py`) musi móc go zmienić, inaczej
    # raportowałaby częstotliwości policzone dla innego neuronu niż ten,
    # dla którego wyliczyła próg.
    b_gc: float = B_GC

    # ── Zawodność synaptyczna („spike-wise noise" Madara) ─────────────────────
    # Prawdopodobieństwo, że pojedynczy spajk presynaptyczny faktycznie przekaże
    # ładunek. 1.0 = synapsa deterministyczna → obwód numerycznie IDENTYCZNY
    # z wersją sprzed wprowadzenia tego parametru (zweryfikowane regresyjnie:
    # przy 1.0 kod nie zużywa ani jednej liczby losowej, bo bierze inną gałąź).
    #
    # Po co to jest: bez źródła zmienności prawdopodobieństwo AP po pulsie jest
    # zero-jedynkowe (zmierzone: 0.00 → 0.99), więc zakresu 20–80% podawanego
    # przez Madara NIE DA SIĘ trafić samą wagą. Przerzedzenie procesu Poissona
    # z prawdopodobieństwem p przy zachowanej średniej (waga W/p) daje wariancję
    # g_ex ∝ 1/p — rzadsze, ale większe zdarzenia, czyli większe fluktuacje V
    # przy TYM SAMYM średnim napędzie. To jest mechanizm, który wytwarza
    # stopniowane P(AP), a nie przebranie wagi pod inną nazwą.
    #
    # ⚠️ Efektywny napęd = rate × W × p_rel × τ, więc p_rel i wagę trzeba
    # kalibrować RAZEM — samo obniżenie p_rel cicho zjeżdża z częstotliwości.
    P_REL_PP_GC: float = 1.0
    P_REL_PP_FS: float = 1.0
    P_REL_GC_FS: float = 1.0
    P_REL_FS_GC: float = 1.0
    P_REL_GC_HMC: float = 1.0
    P_REL_HMC_FS: float = 1.0
    P_REL_HMC_GC: float = 1.0
    P_REL_FS_HMC: float = 1.0
    P_REL_FS_FS: float = 1.0

    # Rozrzut opóźnień synaptycznych [ms] (odchylenie standardowe). 0.0 = wyłączony.
    # UWAGA metodologiczna: Brian2 trzyma `delay` na SYNAPSIE, nie na spajku, więc
    # losujemy je raz przy budowie sieci. To NIE jest jitter per spajk w sensie
    # Madara — na poziomie populacji rozmywa odpowiedź podobnie, ale w metodach
    # trzeba to opisać jako heterogeniczność opóźnień, a nie zmienność próba-próba.
    delay_jitter_ms: float = 0.0

    def p_rel_map(self) -> dict:
        """Prawdopodobieństwa uwolnienia wg nazwy ścieżki (klucze jak w `make_connectivity`)."""
        return {
            'pp_gc': self.P_REL_PP_GC, 'pp_fs': self.P_REL_PP_FS,
            'gc_fs': self.P_REL_GC_FS, 'fs_gc': self.P_REL_FS_GC,
            'gc_hmc': self.P_REL_GC_HMC, 'hmc_fs': self.P_REL_HMC_FS,
            'hmc_gc': self.P_REL_HMC_GC, 'fs_hmc': self.P_REL_FS_HMC,
            'fs_fs': self.P_REL_FS_FS,
        }

    def with_reliability(self, gc: float = 1.0, fs: float = 1.0,
                         hmc: float = 1.0) -> "DGConfig":
        """
        Kopia z zawodnością ustawioną wg TYPU KOMÓRKI DOCELOWEJ — czyli tak, jak
        formułuje to biologia: „GC i HMC odpowiadają mniej niezawodnie niż FS".
        Ustawia wszystkie ścieżki wchodzące do danego typu na to samo p_rel.
        """
        return replace(
            self,
            P_REL_PP_GC=gc, P_REL_FS_GC=gc, P_REL_HMC_GC=gc,
            P_REL_PP_FS=fs, P_REL_GC_FS=fs, P_REL_HMC_FS=fs, P_REL_FS_FS=fs,
            P_REL_GC_HMC=hmc, P_REL_FS_HMC=hmc,
        )

    # prawdopodobieństwa połączeń
    P_PP_FS: float = 0.40
    P_GC_FS: float = 0.40
    P_FS_GC: float = 0.50
    P_GC_HMC: float = 0.25
    P_HMC_FS: float = 0.40
    P_HMC_GC: float = 0.40

    # wejście PP
    per_fiber: bool = False        # False = zagregowany Poisson (szybszy)
    n_syn_pp: int = N_FIBERS_PER_GC
    r_high: float = R_EFF_HIGH     # Hz — aktywny GC (aggregate)
    r_low: float = R_EFF_LOW       # Hz — tło

    # czas
    T_ms: float = T_MS

    def with_motifs(self, ff: bool, fb: bool, hmc: bool) -> "DGConfig":
        """Kopia z ustawionymi motywami — do lezji faktorialnych (kierunek 4)."""
        return replace(self, enable_ff=ff, enable_fb=fb, enable_hmc=hmc)

    def drive_scaled(self, factor: float) -> "DGConfig":
        """Kopia ze skalowanym napędem PP (tempo wejścia) — oś 'tempo' w kierunku 4."""
        return replace(self, r_high=self.r_high * factor, r_low=self.r_low * factor)

    def scaled(self, N_GC: int) -> "DGConfig":
        """
        Kopia przeskalowana do N_GC z zachowaniem BILANSU POBUDZENIE/HAMOWANIE.

        Dwie rzeczy muszą się zgadzać naraz i obie łatwo przeoczyć:

        1. Proporcje populacji GC:FS:HMC — skalujemy wszystkie trzy razem.
        2. LICZBA WEJŚĆ NA NEURON (in-degree) — musi zostać stała, więc
           prawdopodobieństwa połączeń skalujemy ODWROTNIE do rozmiaru populacji
           źródłowej (standard przy skalowaniu sieci spajkujących).

        Bez punktu 2 obwód cicho umiera: każdy GC dostaje P_FS_GC × N_FS synaps
        hamujących, więc przy 4× większej populacji FS hamowanie na GC rośnie 4×,
        podczas gdy pobudzenie PP (1:1) zostaje bez zmian. Zweryfikowane: przy
        N_GC=800 bez korekty prawdopodobieństw wyjście DG jest PUSTE (0% aktywnych GC).

        Wagi synaptyczne zostają bez zmian — skalujemy łączność, nie biofizykę.
        """
        f = N_GC / self.N_GC                       # współczynnik skali populacji
        if f == 1.0:
            return self
        clip = lambda p: float(min(1.0, max(0.0, p / f)))   # zachowaj in-degree
        return replace(
            self,
            N_GC=N_GC,
            N_FS=max(2, int(round(self.N_FS * f))),
            N_HMC=max(2, int(round(self.N_HMC * f))),
            P_PP_FS=clip(self.P_PP_FS),
            P_GC_FS=clip(self.P_GC_FS),
            P_FS_GC=clip(self.P_FS_GC),
            P_GC_HMC=clip(self.P_GC_HMC),
            P_HMC_FS=clip(self.P_HMC_FS),
            P_HMC_GC=clip(self.P_HMC_GC),
            P_FS_HMC=clip(self.P_FS_HMC),
            P_FS_FS=clip(self.P_FS_FS),
        )

    def with_mc_strength(self, drive: float, gain: float) -> "DGConfig":
        """
        Kopia ze skalowaną siłą ścieżki mossy cells — oś 'mc_gain' w kierunku 4.

        `drive` = W_GC_HMC   — jak mocno GC rekrutują MC (poniżej ≈12 mV MC milczą,
                               bo G_crit = 4 + K_HMC = 14 mV).
        `gain`  = mnożnik na WYJŚCIU MC (W_HMC_GC, W_HMC_FS) — jak mocno MC
                               oddziałują z powrotem na obwód.

        Rozdzielamy je, bo to dwa różne pytania biologiczne: „czy MC w ogóle
        strzelają" vs „czy ich wyjście cokolwiek znaczy". Przy domyślnych wagach
        narzędzia odpowiedź brzmi NIE na oba (patrz README).
        """
        return replace(
            self,
            W_GC_HMC=drive,
            W_HMC_GC=MC_BASE_W_HMC_GC * gain,
            W_HMC_FS=MC_BASE_W_HMC_FS * gain,
        )


# Wagi bazowe wyjścia MC (mnożnik `gain=1` = domyślne wartości interactive_dg.py)
MC_BASE_W_HMC_GC = 0.5
MC_BASE_W_HMC_FS = 1.0


# Nazwy motywów — jedno miejsce, używane w sweepach i na wykresach
MOTIFS = ("FF", "FB", "MC")
MOTIF_LABELS = {
    "FF": "Feedforward (PP→FS→GC)",
    "FB": "Feedback (GC→FS→GC)",
    "MC": "Mossy cells (GC→HMC→GC/FS)",
}


def config_from_motif_set(base: DGConfig, active: frozenset) -> DGConfig:
    """Konfiguracja z włączonymi tylko motywami z `active` (podzbiór MOTIFS)."""
    return base.with_motifs(
        ff="FF" in active,
        fb="FB" in active,
        hmc="MC" in active,
    )
