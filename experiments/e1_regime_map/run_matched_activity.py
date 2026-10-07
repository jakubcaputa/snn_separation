"""
e1_regime_map/run_matched_activity.py

E1′ — SEPARACJA PRZY DOPASOWANEJ AKTYWNOŚCI. Następca `run_regime_map.py`.

Czym to się różni od `run_regime_map.py` i dlaczego tamten nie wystarczył
----------------------------------------------------------------------
`run_regime_map.py` przesuwa `K_GC` i `W_FS_GC`, a frakcję aktywnych GC ODCZYTUJE
jako wynik — i mierzy `dec = r_in − r_out`, które jest monotoniczne względem tej
frakcji. Oś sweepu pokrywa się więc z confounderem i nic nie da się przypisać
obwodowi. Widać to wprost: maksimum separacji jedzie za progiem maski ważności
przy KAŻDYM progu (STATUS sek. 3.3). Szersza siatka tego nie naprawia, bo to nie jest
problem zasięgu, tylko konstrukcji.

Tutaj naprawiamy trzy rzeczy naraz:

1. AKTYWNOŚĆ JEST ZADANA, NIE OBSERWOWANA. Dla każdego celu `a*` bisekcja po
   `K_GC` (`calibrate.solve_k_gc_for_active_fraction`) trafia w tę frakcję, a
   dopiero POTEM przesuwamy hamowanie fazowe `W_FS_GC`. Cisza jest wyrównana
   między warunkami, więc różnice są przypisywalne.

2. MIERZYMY NADWYŻKĘ PONAD NULL, NIE SAMO `dec`. Dwa null-e o dopasowanej
   rzadkości (`dg_core.nulls`): permutacyjny i k-WTA. Nadwyżka znika przy
   wyciszeniu z konstrukcji — artefakt się skraca, zamiast być maskowany maską.

3. `P_active` JEST OSIĄ, NIE STAŁĄ. `retention` miało maksimum przy ~25%
   aktywnych GC, czyli dokładnie przy `P_active` = 0.25 z siatki — co wygląda na
   tautologię estymatora MI, a nie własność obwodu. Jeśli maksimum idzie za
   `P_active`, to tautologia i wypada z pracy; jeśli stoi — to realny punkt pracy.

Hipoteza, którą to testuje (następca obalonego H1)
--------------------------------------------------
    H1′: przy dopasowanej rzadkości wyjścia obwód fazowy FS→GC daje separację
         POWYŻEJ nulla o tej samej rzadkości, a ta nadwyżka ma maksimum przy
         pośredniej sile hamowania fazowego.

⚠️ Wynik zerowy jest tu możliwy i jest wynikiem: kierunek 1A pokazał już, że przy
dopasowanej rzadkości DG przegrywa z `random` w klasyfikacji (STATUS sek. 3.7). Jeśli
nadwyżka wyjdzie ≈0 na całej siatce, to razem z 1A jest to spójna teza
(„separacja przypisywana DG jest w większości rzadkością"), a nie porażka.

E1″ — szerszy sweep (preset `wide`, 2026-10-07)
-----------------------------------------------
E1′ trzymało na sztywno trzy rzeczy, które mogą zmienić odpowiedź: podobieństwo
wejść (`R_in` = 0.75), reżim mossy cells (martwe — konfiguracja domyślna) i miarę
(korelacja częstotliwości z 600 ms, ślepa na czas). E1″ zmienia wszystkie trzy:
`R_in` ∈ {0.5, 0.75, 0.9, 0.95}, reżim ∈ {mc_inert, mc_active}, `W_FS_GC` do 12,
i dokłada **dyskryminowalność** liczoną względem powtórzenia (`sep_rate`, `sep_t`).

Dlaczego względem powtórzenia: korelacja w oknach 20 ms sama spada od szumu
Poissona, więc „separacja czasowa" liczona naiwnie byłaby kolejnym confounderem.
Każdy wzorzec symulujemy dwa razy z innym szumem wejścia i pytamy, o ile bardziej
wzorzec jest podobny DO SIEBIE niż DO INNEGO wzorca. Szum działa na oba człony.

KRYTERIUM ZAPISANE PRZED LICZENIEM (STATUS sek. 3.4) — implementacja: `prereg_test`.

Uruchomienie
------------
    python run_matched_activity.py --preset quick
    python run_matched_activity.py --preset full --jobs 16
    python run_matched_activity.py --preset wide --jobs 16
"""

from __future__ import annotations

import argparse
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
    active_fraction, binary_mi_io, config_for_regime, make_connectivity,
    make_input_spikes, make_patterns, mean_pairwise_jaccard, nan_mean,
    population_sparseness, simulate,
)
from dg_core.metrics import _count_matrix  # noqa: E402
from dg_core.calibrate import solve_k_gc_for_active_fraction  # noqa: E402
from dg_core.nulls import separation_vs_null  # noqa: E402

RESULTS = Path(__file__).parent / "results"

# `quick` i `full` odtwarzają E1′ bit w bit (jeden R_in, mossy cells martwe,
# bez powtórzeń, zakres K jak wcześniej). `wide` to E1″.
PRESETS = {
    'quick': dict(
        target_af=[0.05, 0.15, 0.25],
        W_FS_GC=[0.0, 1.0, 3.0],
        P_active=[0.25],
        seeds=[0],
        R_in=[0.75], regimes=['mc_inert'], n_patterns=3,
        repeats=False, k_hi=24.0,
    ),
    'full': dict(
        target_af=[0.02, 0.05, 0.10, 0.15, 0.20, 0.30],
        W_FS_GC=[0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0],
        P_active=[0.10, 0.25, 0.40],
        seeds=[0, 1, 2, 3, 4],
        R_in=[0.75], regimes=['mc_inert'], n_patterns=4,
        repeats=False, k_hi=24.0,
    ),
    'wide': dict(
        target_af=[0.02, 0.05, 0.10, 0.20],
        W_FS_GC=[0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0],
        P_active=[0.25],
        seeds=[0, 1, 2, 3, 4],
        R_in=[0.50, 0.75, 0.90, 0.95], regimes=['mc_inert', 'mc_active'],
        n_patterns=4, repeats=True,
        # mossy cells dokładają pobudzenia — przy niskich celach może być
        # potrzebne więcej hamowania tonicznego niż 24
        k_hi=32.0,
    ),
    'wide_quick': dict(
        target_af=[0.05, 0.20],
        W_FS_GC=[0.0, 3.0, 12.0],
        P_active=[0.25],
        seeds=[0],
        R_in=[0.75, 0.95], regimes=['mc_inert', 'mc_active'],
        n_patterns=3, repeats=True, k_hi=32.0,
    ),
}

# Okno czasowe dla dyskryminowalności czasowej. 20 ms ≈ jeden cykl gamma —
# skala, na której działa hamowanie fazowe interneuronów koszykowych.
T_BIN_MS = 20.0

# Ile wolno spudłować w aktywność, żeby punkt liczył się jako „dopasowany".
# Punkty spoza tolerancji NIE są wyrzucane — są oznaczane, bo sam fakt, że dla
# danego W_FS_GC nie da się trafić w cel, jest informacją o obwodzie.
AF_TOL = 0.02


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.ravel(a).astype(float), np.ravel(b).astype(float)
    if a.std() == 0 or b.std() == 0:
        return float('nan')
    return float(np.corrcoef(a, b)[0, 1])


def run_cell(r_in: float, regime: str, target: float, w_fs_gc: float,
             p_active: float, seed: int, grid: dict, N_GC: int, T_ms: float) -> dict:
    """Jeden punkt: dobierz K_GC do zadanej aktywności, zmierz separację."""
    cfg = replace(config_for_regime(regime, N_GC, T_ms), W_FS_GC=w_fs_gc)

    conn = make_connectivity(cfg, seed=seed)
    pats, r_in_meas = make_patterns(N_GC, grid['n_patterns'], r_in,
                                    p_active, seed=100 + seed)

    # 1) zadana aktywność — bisekcja po hamowaniu TONICZNYM, przy ustalonym FAZOWYM
    k_gc, af_hit = solve_k_gc_for_active_fraction(
        cfg, conn, pats[0], target, seed=1000 * (seed + 1), k_hi=grid['k_hi'])
    cfg = replace(cfg, K_GC=k_gc)

    # 2) właściwy pomiar przy już wyrównanej aktywności
    gc_vecs, ret, spikes = [], [], []
    for k in range(grid['n_patterns']):
        idx, t = make_input_spikes(pats[k], cfg, seed=1000 * (seed + 1) + k)
        res = simulate(cfg, idx, t, conn)
        gc_vecs.append(res['gc_rates'])
        spikes.append(res['gc_spikes'])
        ret.append(binary_mi_io(pats[k], res['gc_rates'])['retention'])

    rng = np.random.default_rng(7000 + seed)
    nulls = separation_vs_null(gc_vecs, pats, r_in_meas, rng)

    gc0 = gc_vecs[0]
    act = active_fraction(gc0)

    row = {
        'R_in_target': r_in, 'regime': regime,
        'target_af': target, 'W_FS_GC': w_fs_gc, 'P_active': p_active, 'seed': seed,
        'K_GC': k_gc,                      # dobrane, nie zadane
        'af_hit': af_hit,                  # co bisekcja faktycznie osiągnęła
        'af_measured': act,                # aktywność w samym pomiarze
        'matched': bool(abs(af_hit - target) <= AF_TOL),
        'r_in': r_in_meas,
        'overlap_jac': mean_pairwise_jaccard(gc_vecs),
        'sparseness': population_sparseness(gc0),
        'fr_gc': float(np.mean([v.mean() for v in gc_vecs])),
        'retention': nan_mean(ret),
    }
    row.update(nulls)

    # 3) dyskryminowalność względem powtórzenia — tylko gdy preset jej żąda,
    #    żeby `full` zostało bit w bit identyczne z E1′ (te same symulacje).
    if grid.get('repeats'):
        rep_vecs, rep_counts = [], []
        counts = [_count_matrix(sp, N_GC, T_ms, T_BIN_MS) for sp in spikes]
        for k in range(grid['n_patterns']):
            idx, t = make_input_spikes(pats[k], cfg, seed=5000 * (seed + 1) + k)
            res = simulate(cfg, idx, t, conn)
            rep_vecs.append(res['gc_rates'])
            rep_counts.append(_count_matrix(res['gc_spikes'], N_GC, T_ms, T_BIN_MS))
        n = grid['n_patterns']
        pairs = [(a, b) for a in range(n) for b in range(a + 1, n)]
        r_btw_rate = nan_mean(_corr(gc_vecs[a], gc_vecs[b]) for a, b in pairs)
        r_wth_rate = nan_mean(_corr(gc_vecs[k], rep_vecs[k]) for k in range(n))
        r_btw_t = nan_mean(_corr(counts[a], counts[b]) for a, b in pairs)
        r_wth_t = nan_mean(_corr(counts[k], rep_counts[k]) for k in range(n))
        row.update({
            'r_within_rate': r_wth_rate, 'r_between_rate': r_btw_rate,
            'sep_rate': r_wth_rate - r_btw_rate,
            'r_within_t': r_wth_t, 'r_between_t': r_btw_t,
            'sep_t': r_wth_t - r_btw_t,
        })
    return row


def main():
    ap = argparse.ArgumentParser(
        description="E1′: separacja ponad null, przy dopasowanej aktywności")
    ap.add_argument('--preset', choices=list(PRESETS), default='quick')
    ap.add_argument('--n-gc', type=int, default=200)
    ap.add_argument('--t-ms', type=float, default=600.0)
    ap.add_argument('-j', '--jobs', type=int, default=-1)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--n-shards', type=int, default=1)
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    grid = PRESETS[args.preset]
    tasks = [(r, reg, a, w, p, s)
             for r in grid['R_in']
             for reg in grid['regimes']
             for a in grid['target_af']
             for w in grid['W_FS_GC']
             for p in grid['P_active']
             for s in grid['seeds']]
    shard = tasks[args.shard::args.n_shards]

    print(f"preset={args.preset}  N_GC={args.n_gc}  T={args.t_ms:.0f} ms")
    print(f"punktów (R_in × reżim × cel_AF × W_FS_GC × P_active × seed): {len(tasks)}  "
          f"(shard {args.shard}/{args.n_shards} → {len(shard)})")
    n_meas = grid['n_patterns'] * (2 if grid.get('repeats') else 1)
    print(f"każdy punkt = bisekcja (do 14 symulacji) + {n_meas} pomiarowych\n")

    t0 = time.time()
    rows = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_cell)(r, reg, a, w, p, s, grid, args.n_gc, args.t_ms)
        for r, reg, a, w, p, s in shard)

    payload = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    RESULTS.mkdir(exist_ok=True)
    suffix = f"_shard{args.shard}" if args.n_shards > 1 else ""
    out = Path(args.out) if args.out else RESULTS / f"matched_activity_{args.preset}{suffix}.npz"
    np.savez_compressed(out, **payload)

    n_match = int(payload['matched'].sum())
    print(f"\nGotowe w {(time.time() - t0) / 60:.1f} min → {out}")
    print(f"trafionych w zadaną aktywność: {n_match}/{len(rows)} (tol ±{AF_TOL})")
    if n_match < len(rows):
        print(f"  {len(rows) - n_match} punktów NIE dało się dostroić — dla tych")
        print(f"  kombinacji cel aktywności leży poza zasięgiem K_GC ∈ [0, {grid['k_hi']:g}].")

    report(payload)
    if len(grid['R_in']) > 1 or len(grid['regimes']) > 1:
        prereg_test(payload)


def report(p: dict) -> None:
    """Podsumowanie E1′ na punktach o wyrównanej aktywności (STATUS sek. 3.4–3.5)."""
    m = p['matched'].astype(bool)
    if m.sum() < 3:
        print("\nZa mało dopasowanych punktów na podsumowanie.")
        return

    print("\n── separacja przy dopasowanej aktywności ──")
    print(f"{'cel AF':>7} {'n':>4} {'dec':>8} {'−kWTA':>9} {'retention':>10}")
    for a in np.unique(p['target_af'][m]):
        s_ = m & (p['target_af'] == a)
        print(f"{a:>7.2f} {int(s_.sum()):>4} {p['dec'][s_].mean():>8.3f} "
              f"{p['dec_excess_kwta'][s_].mean():>9.3f} {p['retention'][s_].mean():>10.3f}")

    # Czy hamowanie FAZOWE zmienia separację, gdy cisza jest wyrównana?
    # Nachylenie liczone osobno w każdej komórce aktywności (tak jak w STATUS).
    from scipy import stats
    print("\n── czy W_FS_GC zmienia separację przy ustalonej aktywności? ──")
    for a in np.unique(p['target_af'][m]):
        s_ = m & (p['target_af'] == a)
        if len(np.unique(p['W_FS_GC'][s_])) >= 3:
            r = stats.linregress(p['W_FS_GC'][s_], p['dec'][s_])
            print(f"  aktywność {a:.0%}: nachylenie {r.slope:+.4f}  p={r.pvalue:.3f}")
    r = stats.linregress(p['W_FS_GC'][m], p['dec'][m])
    print(f"  łącznie:       nachylenie {r.slope:+.4f}  p={r.pvalue:.3f}")

    # ⚠️ Nadwyżka nad nullem permutacyjnym NIE jest tu raportowana jako wynik:
    # ten null równa się r_in, więc nadwyżka = −r_out (STATUS sek. 3.5).
    # Wcześniejsza wersja tej funkcji czytała ją jako „obwód gorszy niż null" —
    # wycofane 2026-10-06.

    # Tautologia P_active: czy maksimum retention idzie za rzadkością wejścia?
    ps = np.unique(p['P_active'][m])
    if len(ps) > 1:
        print("\n── test tautologii: czy maksimum retention idzie za P_active? ──")
        peaks = []
        for pa in ps:
            s_ = m & (p['P_active'] == pa)
            pk = float(p['af_measured'][s_][np.argmax(p['retention'][s_])])
            peaks.append(pk)
            print(f"  P_active {pa:.2f} → maksimum retention przy AF {pk:.3f}")
        follows = np.corrcoef(ps, peaks)[0, 1] > 0.9 if len(ps) > 2 else \
            abs(peaks[-1] - peaks[0]) > 0.5 * abs(ps[-1] - ps[0])
        print("  → " + ("IDZIE za P_active: tautologia estymatora MI, nie własność obwodu."
                        if follows else
                        "STOI mimo zmiany P_active: realny punkt pracy obwodu."))


# ══════════════════════════════════════════════════════════════════════════════
# E1″ — test zapisany PRZED liczeniem (2026-10-07). Nie zmieniać po zobaczeniu
# wyników; jeśli trzeba, dopisać osobny test z datą i uzasadnieniem.
# ══════════════════════════════════════════════════════════════════════════════

PREREG = dict(
    outcomes=('dec', 'sep_t'),     # separacja częstotliwościowa; dyskryminowalność czasowa
    alpha=0.05,                    # przed korektą Bonferroniego na WSZYSTKIE wykonane testy
    min_w_levels=3,                # komórka oceniana, gdy ≥3 poziomy W ...
    min_points_per_w=3,            # ... po ≥3 dostrojone punkty każdy
    # Dodane PO pilocie (preset wide_quick, 24 pkt, 1 seed), PRZED głównym
    # przebiegiem: przy 5% aktywności dwa powtórzenia tego samego wzorca mają
    # w oknach 20 ms korelację ≈ 0 (r_within_t ≈ −0.002), więc sep_t jest tam
    # z konstrukcji ≈ 0 i test byłby pusty — a pusty test tylko zaostrza próg
    # Bonferroniego dla pozostałych. sep_t oceniamy tylko tam, gdzie taktowanie
    # wyjścia jest w ogóle powtarzalne.
    min_r_within_t=0.05,
)


def prereg_test(p: dict) -> dict:
    """
    Komórka = (reżim MC, R_in, zadana aktywność). W każdej: nachylenie wyniku
    względem W_FS_GC (OLS po dostrojonych punktach) i jego p.

    ZALEŻNOŚĆ zostaje stwierdzona tylko wtedy, gdy nachylenie jest istotne po
    korekcie Bonferroniego na wszystkie wykonane testy ORAZ ma ten sam znak
    i tę samą istotność w co najmniej jednym SĄSIEDNIM R_in (ten sam reżim, ta
    sama aktywność). Pojedyncza istotna komórka to za mało — przy kilkudziesięciu
    testach wypada z przypadku.
    """
    from scipy import stats
    m = p['matched'].astype(bool)
    regimes = list(dict.fromkeys(p['regime'].tolist()))
    rins = sorted(set(p['R_in_target'].tolist()))
    targets = sorted(set(p['target_af'].tolist()))
    tests = {}
    for oc in PREREG['outcomes']:
        if oc not in p:
            continue
        y_all = p[oc]
        for reg in regimes:
            for r in rins:
                for a in targets:
                    s_ = m & (p['regime'] == reg) & (p['R_in_target'] == r) & \
                        (p['target_af'] == a) & np.isfinite(y_all)
                    ws, cnt = np.unique(p['W_FS_GC'][s_], return_counts=True)
                    if (cnt >= PREREG['min_points_per_w']).sum() < PREREG['min_w_levels']:
                        continue
                    if oc == 'sep_t' and \
                            np.nanmean(p['r_within_t'][s_]) < PREREG['min_r_within_t']:
                        continue          # taktowanie niepowtarzalne — miara pusta
                    lr = stats.linregress(p['W_FS_GC'][s_], y_all[s_])
                    span = float(ws.max() - ws.min())
                    tests[(oc, reg, r, a)] = dict(slope=lr.slope, p=lr.pvalue,
                                                  change=lr.slope * span, n=int(s_.sum()))
    n_tests = len(tests)
    if n_tests == 0:
        print("\nE1″: brak komórek spełniających warunki oceny.")
        return {}
    thr = PREREG['alpha'] / n_tests
    for t in tests.values():
        t['sig'] = t['p'] < thr

    found = []
    for (oc, reg, r, a), t in tests.items():
        if not t['sig']:
            continue
        k = rins.index(r)
        for nb in (rins[k - 1] if k > 0 else None, rins[k + 1] if k + 1 < len(rins) else None):
            u = tests.get((oc, reg, nb, a)) if nb is not None else None
            if u and u['sig'] and np.sign(u['slope']) == np.sign(t['slope']):
                found.append((oc, reg, r, a))
                break

    print(f"\n── E1″: test zapisany przed liczeniem ──")
    print(f"wykonanych testów: {n_tests}  →  próg Bonferroniego p < {thr:.2e}")
    for oc in PREREG['outcomes']:
        rows = {k: v for k, v in tests.items() if k[0] == oc}
        if not rows:
            continue
        n_sig = sum(v['sig'] for v in rows.values())
        n_nom = sum(v['p'] < 0.05 for v in rows.values())
        print(f"\n  {oc}: komórek {len(rows)}, nominalnie p<0.05: {n_nom} "
              f"(z przypadku oczekiwane ~{0.05 * len(rows):.1f}), po korekcie: {n_sig}")
        for (o, reg, r, a), v in sorted(rows.items(), key=lambda kv: kv[1]['p'])[:5]:
            flag = '  ← ISTOTNE' if v['sig'] else ''
            print(f"    {reg:9s} R_in {r:.2f} akt. {a:4.0%}: zmiana na całym zakresie W "
                  f"{v['change']:+.3f}  p={v['p']:.1e}{flag}")
    print()
    if found:
        print("WYNIK: ZALEŻNOŚĆ STWIERDZONA w komórkach (wynik, reżim, R_in, aktywność):")
        for f in sorted(found):
            print("   ", f)
    else:
        print("WYNIK: brak zależności spełniającej kryterium — hamowanie fazowe nie zmienia")
        print("   separacji ani dyskryminowalności czasowej przy wyrównanej aktywności,")
        print("   w żadnym R_in i żadnym reżimie mossy cells.")
    return dict(tests=tests, threshold=thr, found=found)


if __name__ == '__main__':
    main()
