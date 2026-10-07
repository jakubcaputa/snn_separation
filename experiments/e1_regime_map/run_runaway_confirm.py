"""
e1_regime_map/run_runaway_confirm.py

E1‴ — TEST POTWIERDZAJĄCY wyniku eksploracyjnego z E1″ (STATUS sek. 3.4, 4.4 pkt 0).

Co E1″ pokazało (eksploracyjnie)
--------------------------------
Przy aktywnych mossy cells i słabym hamowaniu fazowym aktywne GC „uciekają" do
częstotliwości rzędu 100–300 Hz, mimo że ich LICZBA jest wyrównana bisekcją po
hamowaniu tonicznym. Od `W_FS_GC` ≈ 1–2 częstotliwość wraca do normy. Bez MC
ucieczki nie ma. Odczyt: toniczne ustala, ILE komórek strzela, fazowe — JAK SZYBKO.

⚠️ WYNIK (2026-10-07, STATUS sek. 3.4): test NIE PRZESZEDŁ (R1a ✗, R1b ✗, R2 ✓,
R3 ✓, R4 ✗). Odczyt „toniczne = ile, fazowe = jak szybko" jest WYCOFANY: miara E1″
(fr_gc z 4 wzorców / af z wzorca 0) mieszała wzorce. Faktyczne zjawisko to zapłon
prawie całej sieci dla części wzorców — rzadki przy λ = 1, częstszy przy λ = 1.5,
nigdy bez MC i nigdy przy W ≥ 3. Opis poniżej to stan sprzed liczenia.

Dwie słabości, które ten test usuwa
-----------------------------------
1. Wynik był eksploracyjny (kryterium E1″ dotyczyło separacji, nie częstotliwości),
   na tych samych seedach, na których go znaleziono → tu NOWE seedy (10–14).
2. Siła pętli MC w `mc_active` (drive 16, gain 20, brake 2) jest dobrana ręcznie,
   więc próg `W` ≈ 1 może być jej artefaktem → tu oś λ skaluje całą pętlę od
   `mc_inert` (λ=0) przez `mc_active` (λ=1) do mocniejszej (λ=1.5).

Dwie części
-----------
A  aktywność ZADANA (bisekcja po K_GC, jak E1″): λ × aktywność × W_FS_GC × seed.
   Pyta: czy ucieczka się powtarza, gdzie jest próg W i jak zależy od λ.
B  BEZ bisekcji — zwykła siatka K_GC × W_FS_GC przy λ ∈ {0, 1}.
   W części A rozdzielenie „toniczne = ile" jest wymuszone konstrukcją (bisekcja
   trzyma liczbę aktywnych). B sprawdza je bez tego: która oś wyjaśnia frakcję
   aktywnych, a która częstotliwość na aktywną komórkę.

KRYTERIUM ZAPISANE PRZED LICZENIEM — `PREREG_RUNAWAY` i `prereg_runaway` niżej.
Nie zmieniać po zobaczeniu wyników; ewentualne dodatki osobno, z datą.

Uruchomienie
------------
    python run_runaway_confirm.py --preset quick              # pilot, kilka minut
    python run_runaway_confirm.py --preset full --jobs 16     # A + B
    python run_runaway_confirm.py --analyze                   # scal shardy, figura, werdykt
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from joblib import Parallel, delayed  # noqa: E402

from dg_core import (  # noqa: E402
    MC_REGIMES, DGConfig, make_connectivity, make_input_spikes, make_patterns,
    simulate,
)
from dg_core.calibrate import solve_k_gc_for_active_fraction  # noqa: E402

RESULTS = Path(__file__).parent / "results"

ACTIVE_HZ = 0.5          # próg „aktywnej" komórki — ten sam co active_fraction()
R_IN = 0.75              # w E1″ częstotliwość nie zależała od R_in — jeden poziom
P_ACTIVE = 0.25
AF_TOL = 0.02            # jak w run_matched_activity

PRESETS = {
    'quick': dict(
        A=dict(lam=[0.0, 1.0], target_af=[0.10, 0.20], W_FS_GC=[0.0, 2.0],
               seeds=[10]),
        B=dict(lam=[0.0, 1.0], K_GC=[10.0, 22.0], W_FS_GC=[0.0, 2.0], seeds=[10]),
        n_patterns=2, k_hi=40.0,
    ),
    'full': dict(
        # λ = 0.5: drive 8.5 mV < próg rekrutacji MC (≈12–14 mV) → spodziewamy się
        # MC milczących; 0.75: tuż nad progiem. 1 = mc_active, 1.5 = mocniej.
        A=dict(lam=[0.0, 0.5, 0.75, 1.0, 1.5], target_af=[0.05, 0.10, 0.20],
               W_FS_GC=[0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0],
               seeds=list(range(10, 20))),
        B=dict(lam=[0.0, 1.0], K_GC=[6.0, 10.0, 14.0, 18.0, 22.0, 26.0],
               W_FS_GC=[0.0, 0.5, 1.0, 2.0, 3.0, 5.0],
               seeds=[10, 11, 12, 13, 14]),
        n_patterns=2, k_hi=40.0,
    ),
}


def config_for_strength(lam: float, N_GC: int, T_ms: float) -> DGConfig:
    """Liniowa interpolacja całej pętli MC między mc_inert (λ=0) a mc_active (λ=1).

    λ=0 i λ=1 dają DOKŁADNIE konfiguracje z `MC_REGIMES` — te same co w E1″."""
    lo, hi = MC_REGIMES['mc_inert'], MC_REGIMES['mc_active']
    mc = {k: lo[k] + lam * (hi[k] - lo[k]) for k in lo}
    base = DGConfig(T_ms=T_ms, W_FS_HMC=mc['brake']).scaled(N_GC)
    return base.with_mc_strength(drive=mc['drive'], gain=mc['gain'])


def _rates_summary(res: dict) -> dict:
    gc = res['gc_rates']
    act = gc > ACTIVE_HZ
    return dict(
        af=float(act.mean()),
        # częstotliwość liczona TYLKO po aktywnych komórkach (E1″ liczyło fr/af —
        # to prawie to samo, ale tu bez wkładu komórek poniżej progu)
        rate_active=float(gc[act].mean()) if act.any() else 0.0,
        rate_max=float(gc.max()),
        hmc_rate=float(res['hmc_rates'].mean()),
        fs_rate=float(res['fs_rates'].mean()),
    )


def _measure(cfg, conn, pats, seed, n_patterns) -> dict:
    rows = []
    for k in range(n_patterns):
        idx, t = make_input_spikes(pats[k], cfg, seed=1000 * (seed + 1) + k)
        rows.append(_rates_summary(simulate(cfg, idx, t, conn)))
    return {key: float(np.mean([r[key] for r in rows])) for key in rows[0]}


def run_A(lam, target, w, seed, grid, N_GC, T_ms) -> dict:
    cfg = replace(config_for_strength(lam, N_GC, T_ms), W_FS_GC=w)
    conn = make_connectivity(cfg, seed=seed)
    pats, _ = make_patterns(N_GC, grid['n_patterns'], R_IN, P_ACTIVE, seed=100 + seed)
    k_gc, af_hit = solve_k_gc_for_active_fraction(
        cfg, conn, pats[0], target, seed=1000 * (seed + 1), k_hi=grid['k_hi'])
    cfg = replace(cfg, K_GC=k_gc)
    row = dict(part='A', lam=lam, target_af=target, W_FS_GC=w, seed=seed,
               K_GC=k_gc, af_hit=af_hit, matched=bool(abs(af_hit - target) <= AF_TOL))
    row.update(_measure(cfg, conn, pats, seed, grid['n_patterns']))
    return row


def run_B(lam, k_gc, w, seed, grid, N_GC, T_ms) -> dict:
    cfg = replace(config_for_strength(lam, N_GC, T_ms), W_FS_GC=w, K_GC=k_gc)
    conn = make_connectivity(cfg, seed=seed)
    pats, _ = make_patterns(N_GC, grid['n_patterns'], R_IN, P_ACTIVE, seed=100 + seed)
    row = dict(part='B', lam=lam, target_af=np.nan, W_FS_GC=w, seed=seed,
               K_GC=k_gc, af_hit=np.nan, matched=True)
    row.update(_measure(cfg, conn, pats, seed, grid['n_patterns']))
    return row


# ══════════════════════════════════════════════════════════════════════════════
# KRYTERIUM ZAPISANE PRZED LICZENIEM — 2026-10-07, przed pilotem i przebiegiem.
# ══════════════════════════════════════════════════════════════════════════════

PREREG_RUNAWAY = dict(
    # R1  ucieczka się powtarza i hamowanie fazowe ją zatrzymuje.
    #     Komórki: λ ∈ {1, 1.5} × aktywność ∈ {10%, 20%} (4 komórki; 5% raportowane).
    #     W każdej: średnia log10(rate_active) przy W=0 vs W=2, Welch jednostronny,
    #     Bonferroni na 4, ORAZ iloraz średnich częstotliwości ≥ 3.
    #     POTWIERDZONE, gdy wszystkie 4 komórki spełniają oba warunki.
    r1_lams=(1.0, 1.5), r1_afs=(0.10, 0.20), w_lo=0.0, w_hi=2.0,
    alpha=0.05, min_ratio=3.0,
    # R2  bez mossy cells ucieczki nie ma: λ=0, każda aktywność, iloraz W=0/W=2 < 3
    #     i żaden punkt nie przekracza progu ucieczki.
    runaway_hz=20.0,
    # R3  próg nie jest artefaktem ręcznie dobranych wag — zapisujemy W_crit(λ, akt.)
    #     = najmniejsze W, od którego WSZYSTKIE wyższe W mają medianę < 20 Hz.
    #     POTWIERDZONE, gdy dla każdego λ, przy którym jest ucieczka, W_crit ≤ 5
    #     (czyli ucieczkę da się zatrzymać w testowanym zakresie). Kierunek
    #     zależności W_crit od λ raportujemy, nie testujemy.
    w_crit_max=5.0,
    # R4  rozdzielenie ról bez bisekcji (część B, λ=1): udział wariancji (η²,
    #     efekty główne w zbalansowanej siatce) —
    #       η²_K(frakcja aktywnych) > η²_W(frakcja aktywnych)   „toniczne = ile"
    #       η²_W(log rate_active)   > η²_K(log rate_active)     „fazowe = jak szybko"
    #     POTWIERDZONE, gdy obie nierówności zachodzą. Przy λ=0 raportujemy te same
    #     liczby jako kontrolę (oczekiwanie: η²_W(log rate) małe).
)

# ── POPRAWKA 2026-10-07, po pilocie (preset quick), PRZED pełnym przebiegiem ──
# Pilot i ponowny wgląd w E1″ pokazały, że ucieczka jest BISTABILNA: punkt albo
# się zapala (100–440 Hz), albo nie (~2 Hz); w E1″ przy 10% aktywności zapaliło
# się ~7/19 punktów przy W=0. Średnia log10 z 5 seedów jest na to za słaba
# (pilot, seed 10: brak zapłonu przy λ=1). Dlatego:
#   • seedy części A: 10–19 zamiast 10–14 (więcej prób dla częstości),
#   • GŁÓWNYM wynikiem R1 staje się CZĘSTOŚĆ zapłonu (rate_active > 20 Hz):
#     R1b — przy λ ∈ {1, 1.5}, aktywność 10% i 20% łącznie, częstość przy W=0
#     vs W=2, Fisher jednostronny, Bonferroni na 2 (po λ); POTWIERDZONE, gdy
#     oba λ istotne ORAZ częstość przy W=2 ≤ 5%. Liczone na WSZYSTKICH punktach A
#     (w stanie bistabilnym bisekcja bywa nieudana — odrzucenie niedopasowanych
#     wycinałoby właśnie zapłony); kierunek ma się zgadzać też na dopasowanych.
#   • R1 z kryterium pierwotnego (średnia log10, Welch) zostaje jako R1a i jest
#     raportowane bez zmian. R2–R4 bez zmian.
PREREG_RUNAWAY.update(r1b_alpha=0.05, r1b_max_incidence_w_hi=0.05)


def _eta2(y: np.ndarray, factor: np.ndarray) -> float:
    """Udział wariancji wyjaśniony przez średnie grup jednego czynnika."""
    y = np.asarray(y, float)
    tot = ((y - y.mean()) ** 2).sum()
    if tot == 0:
        return 0.0
    between = sum(((y[factor == g].mean() - y.mean()) ** 2) * (factor == g).sum()
                  for g in np.unique(factor))
    return float(between / tot)


def prereg_runaway(p: dict) -> dict:
    from scipy import stats
    P = PREREG_RUNAWAY
    A = (p['part'] == 'A') & p['matched'].astype(bool)
    B = p['part'] == 'B'
    lograte = np.log10(np.maximum(p['rate_active'], 1e-2))
    out = {}

    def cell(lam, af, w):
        return A & np.isclose(p['lam'], lam) & np.isclose(p['target_af'], af) & \
            np.isclose(p['W_FS_GC'], w)

    print("\n══ E1‴: test zapisany przed liczeniem ══")
    lams = sorted(set(p['lam'][p['part'] == 'A'].tolist()))
    afs = sorted(set(p['target_af'][A].tolist()))

    # R1
    print(f"\nR1 — ucieczka przy W={P['w_lo']:g} vs W={P['w_hi']:g} (Welch na log10, "
          f"Bonferroni na {len(P['r1_lams']) * len(P['r1_afs'])}, iloraz ≥ {P['min_ratio']:g})")
    thr = P['alpha'] / (len(P['r1_lams']) * len(P['r1_afs']))
    r1 = []
    for lam in lams:
        for af in afs:
            lo, hi = cell(lam, af, P['w_lo']), cell(lam, af, P['w_hi'])
            if lo.sum() < 2 or hi.sum() < 2:
                continue
            ratio = p['rate_active'][lo].mean() / max(p['rate_active'][hi].mean(), 1e-9)
            t = stats.ttest_ind(lograte[lo], lograte[hi], equal_var=False,
                                alternative='greater')
            tested = lam in P['r1_lams'] and af in P['r1_afs']
            ok = bool(t.pvalue < thr and ratio >= P['min_ratio'])
            if tested:
                r1.append(ok)
            print(f"  λ={lam:<4g} akt. {af:4.0%}: {p['rate_active'][lo].mean():7.1f} Hz → "
                  f"{p['rate_active'][hi].mean():6.1f} Hz  (×{ratio:5.1f}, p={t.pvalue:.1e})"
                  + ("  [test] " + ("✓" if ok else "✗") if tested else ""))
    out['R1a'] = bool(r1) and all(r1) and len(r1) == len(P['r1_lams']) * len(P['r1_afs'])
    print(f"  → R1a {'POTWIERDZONE' if out['R1a'] else 'NIEPOTWIERDZONE'} "
          f"({sum(r1)}/{len(r1)} komórek)  [kryterium sprzed pilota]")

    # R1b — częstość zapłonu (poprawka po pilocie, przed pełnym przebiegiem)
    allA = p['part'] == 'A'
    run = p['rate_active'] > P['runaway_hz']
    print(f"\nR1b — częstość zapłonu (> {P['runaway_hz']:g} Hz), W={P['w_lo']:g} vs "
          f"W={P['w_hi']:g}, aktywność {', '.join(f'{a:.0%}' for a in P['r1_afs'])} łącznie, "
          f"Fisher jednostronny, Bonferroni na {len(P['r1_lams'])}")
    thr_b = P['r1b_alpha'] / len(P['r1_lams'])
    r1b = []
    for lam in lams:
        base = allA & np.isclose(p['lam'], lam) & np.isin(p['target_af'], P['r1_afs'])
        lo, hi = base & np.isclose(p['W_FS_GC'], P['w_lo']), base & np.isclose(p['W_FS_GC'], P['w_hi'])
        if not lo.any() or not hi.any():
            continue
        a_, b_ = int(run[lo].sum()), int(run[hi].sum())
        pf = stats.fisher_exact([[a_, lo.sum() - a_], [b_, hi.sum() - b_]],
                                alternative='greater').pvalue
        m_ = p['matched'].astype(bool)
        am, bm = run[lo & m_].mean() if (lo & m_).any() else np.nan, \
            run[hi & m_].mean() if (hi & m_).any() else np.nan
        tested = lam in P['r1_lams']
        ok = bool(pf < thr_b and b_ / hi.sum() <= P['r1b_max_incidence_w_hi'] and am > bm)
        if tested:
            r1b.append(ok)
        print(f"  λ={lam:<4g}: {a_}/{int(lo.sum())} → {b_}/{int(hi.sum())}  p={pf:.1e}   "
              f"(dopasowane: {am:.0%} → {bm:.0%})"
              + ("  [test] " + ("✓" if ok else "✗") if tested else ""))
    out['R1b'] = len(r1b) == len(P['r1_lams']) and all(r1b)
    out['R1'] = out['R1b']
    print(f"  → R1b {'POTWIERDZONE' if out['R1b'] else 'NIEPOTWIERDZONE'}  [wynik główny]")

    # R2
    s0 = (p['part'] == 'A') & np.isclose(p['lam'], 0.0) & p['matched'].astype(bool)
    r2 = True
    for af in afs:
        lo, hi = s0 & np.isclose(p['target_af'], af) & np.isclose(p['W_FS_GC'], P['w_lo']), \
            s0 & np.isclose(p['target_af'], af) & np.isclose(p['W_FS_GC'], P['w_hi'])
        if lo.any() and hi.any():
            ratio = p['rate_active'][lo].mean() / max(p['rate_active'][hi].mean(), 1e-9)
            r2 &= ratio < P['min_ratio']
    n_run0 = int((p['rate_active'][s0] > P['runaway_hz']).sum())
    r2 &= n_run0 == 0
    out['R2'] = bool(r2)
    print(f"\nR2 — bez MC (λ=0): punktów z ucieczką {n_run0}/{int(s0.sum())}  → "
          f"{'POTWIERDZONE' if out['R2'] else 'NIEPOTWIERDZONE'}")

    # R3
    print(f"\nR3 — W_crit (najmniejsze W, od którego mediana < {P['runaway_hz']:g} Hz)")
    ws = sorted(set(p['W_FS_GC'][A].tolist()))
    r3, wcrit = True, {}
    for lam in lams:
        line = []
        for af in afs:
            med = []
            for w in ws:
                s_ = cell(lam, af, w)
                med.append(np.median(p['rate_active'][s_]) if s_.any() else np.nan)
            med = np.array(med)
            bad = np.where(~(med < P['runaway_hz']))[0]      # NaN liczymy jako „nie wiadomo"
            if med[0] < P['runaway_hz'] and not len(bad):
                wc = None                                     # brak ucieczki nawet przy W=0
            elif len(bad) and bad[-1] + 1 < len(ws):
                wc = ws[bad[-1] + 1]
            else:
                wc = np.inf
            wcrit[(lam, af)] = wc
            if wc is not None and not (wc <= P['w_crit_max']):
                r3 = False
            line.append('—' if wc is None else ('>max' if wc == np.inf else f'{wc:g}'))
        print(f"  λ={lam:<4g} " + "  ".join(f"{af:4.0%}: {v:>5s}" for af, v in zip(afs, line)))
    out['R3'] = bool(r3)
    out['W_crit'] = wcrit
    print(f"  → R3 {'POTWIERDZONE' if out['R3'] else 'NIEPOTWIERDZONE'}  "
          f"('—' = brak ucieczki nawet przy W=0)")

    # R4
    print("\nR4 — rozdzielenie ról bez bisekcji (część B), η² efektów głównych")
    for lam in sorted(set(p['lam'][B].tolist())):
        s_ = B & np.isclose(p['lam'], lam)
        if not s_.any():
            continue
        e = dict(K_af=_eta2(p['af'][s_], p['K_GC'][s_]),
                 W_af=_eta2(p['af'][s_], p['W_FS_GC'][s_]),
                 K_rate=_eta2(lograte[s_], p['K_GC'][s_]),
                 W_rate=_eta2(lograte[s_], p['W_FS_GC'][s_]))
        print(f"  λ={lam:g}: frakcja aktywnych  η²_K={e['K_af']:.2f}  η²_W={e['W_af']:.2f}   "
              f"log częstotliwość  η²_K={e['K_rate']:.2f}  η²_W={e['W_rate']:.2f}")
        if np.isclose(lam, 1.0):
            out['R4'] = bool(e['K_af'] > e['W_af'] and e['W_rate'] > e['K_rate'])
            out['R4_eta'] = e
    if 'R4' in out:
        print(f"  → R4 {'POTWIERDZONE' if out['R4'] else 'NIEPOTWIERDZONE'} (ocena przy λ=1)")
    print()
    return out


# ══════════════════════════════════════════════════════════════════════════════

def load(pattern: str) -> dict:
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"Brak plików: {pattern}")
    parts = [dict(np.load(f, allow_pickle=True)) for f in files]
    p = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    print(f"scalono {len(files)} plików → {len(p['part'])} punktów")
    return p


def figure(p: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from dg_core.viz import pct_formatter  # noqa: F401  (spójność z resztą figur)

    A = (p['part'] == 'A') & p['matched'].astype(bool)
    lams = sorted(set(p['lam'][p['part'] == 'A'].tolist()))
    afs = sorted(set(p['target_af'][A].tolist()))
    ws = sorted(set(p['W_FS_GC'][A].tolist()))
    cmap = plt.get_cmap('plasma')
    fig, axes = plt.subplots(1, len(afs) + 1, figsize=(3.6 * (len(afs) + 1), 3.4))
    for j, af in enumerate(afs):
        ax = axes[j]
        for i, lam in enumerate(lams):
            mu = []
            for w in ws:
                s_ = A & np.isclose(p['lam'], lam) & np.isclose(p['target_af'], af) & \
                    np.isclose(p['W_FS_GC'], w)
                mu.append(np.median(p['rate_active'][s_]) if s_.any() else np.nan)
            ax.plot(ws, mu, '-o', ms=3, lw=1.6, color=cmap(i / max(1, len(lams) - 1) * 0.85),
                    label=f'λ = {lam:g}')
        ax.set_yscale('log')
        ax.axhline(PREREG_RUNAWAY['runaway_hz'], color='0.5', ls=':', lw=1)
        ax.set_title(f'{af:.0%} active (matched)')
        ax.set_xlabel('phasic inhibition W_FS→GC')
        ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%g'))
        ax.grid(alpha=0.25, lw=0.5)
    axes[0].set_ylabel('rate per active GC [Hz] (median)')
    axes[0].legend(fontsize=7, title='MC loop strength', title_fontsize=7)

    ax = axes[-1]
    B = (p['part'] == 'B') & np.isclose(p['lam'], 1.0)
    if B.any():
        sc = ax.scatter(p['af'][B], p['rate_active'][B], c=p['W_FS_GC'][B], s=14,
                        cmap='viridis')
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%g'))
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
        fig.colorbar(sc, ax=ax, label='W_FS→GC')
        ax.set_xlabel('fraction of active GC')
        ax.set_title('part B (no matching), λ = 1')
        ax.grid(alpha=0.25, lw=0.5)
    fig.suptitle('E1‴ — confirmatory test of runaway firing (new seeds)', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"figura → {out}")


def main():
    ap = argparse.ArgumentParser(description="E1‴: test potwierdzający ucieczki częstotliwości")
    ap.add_argument('--preset', choices=list(PRESETS), default='quick')
    ap.add_argument('--n-gc', type=int, default=200)
    ap.add_argument('--t-ms', type=float, default=600.0)
    ap.add_argument('-j', '--jobs', type=int, default=-1)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--n-shards', type=int, default=1)
    ap.add_argument('--analyze', action='store_true',
                    help='tylko scal wyniki, narysuj figurę i wydrukuj werdykt')
    args = ap.parse_args()

    pattern = str(RESULTS / f"runaway_confirm_{args.preset}*.npz")
    if args.analyze:
        p = load(pattern)
        figure(p, RESULTS / f"runaway_confirm_{args.preset}.png")
        prereg_runaway(p)
        return

    g = PRESETS[args.preset]
    tasks = [('A', lam, a, w, s) for lam in g['A']['lam'] for a in g['A']['target_af']
             for w in g['A']['W_FS_GC'] for s in g['A']['seeds']]
    tasks += [('B', lam, k, w, s) for lam in g['B']['lam'] for k in g['B']['K_GC']
              for w in g['B']['W_FS_GC'] for s in g['B']['seeds']]
    # A jest ~15× droższe niż B (bisekcja) — przeplatanie wyrównuje shardy
    shard = tasks[args.shard::args.n_shards]
    print(f"preset={args.preset}  punktów {len(tasks)} "
          f"(A {sum(t[0] == 'A' for t in tasks)}, B {sum(t[0] == 'B' for t in tasks)})  "
          f"shard {args.shard}/{args.n_shards} → {len(shard)}")

    t0 = time.time()
    rows = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_A if part == 'A' else run_B)(lam, x, w, s, g, args.n_gc, args.t_ms)
        for part, lam, x, w, s in shard)
    payload = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    RESULTS.mkdir(exist_ok=True)
    suffix = f"_shard{args.shard}" if args.n_shards > 1 else ""
    out = RESULTS / f"runaway_confirm_{args.preset}{suffix}.npz"
    np.savez_compressed(out, **payload)
    print(f"\nGotowe w {(time.time() - t0) / 60:.1f} min → {out}")
    if args.n_shards == 1:
        prereg_runaway(payload)


if __name__ == '__main__':
    main()
