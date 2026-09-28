"""
e1_regime_map/run_matched_activity.py

E1′ — SEPARACJA PRZY DOPASOWANEJ AKTYWNOŚCI. Następca `run_regime_map.py`.

Czym to się różni od `run_regime_map.py` i dlaczego tamten nie wystarczył
----------------------------------------------------------------------
`run_regime_map.py` przesuwa `K_GC` i `W_FS_GC`, a frakcję aktywnych GC ODCZYTUJE
jako wynik — i mierzy `dec = r_in − r_out`, które jest monotoniczne względem tej
frakcji. Oś sweepu pokrywa się więc z confounderem i nic nie da się przypisać
obwodowi. Widać to wprost: maksimum separacji jedzie za progiem maski ważności
przy KAŻDYM progu (STATUS §3.2). Szersza siatka tego nie naprawia, bo to nie jest
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
dopasowanej rzadkości DG przegrywa z `random` w klasyfikacji (STATUS §3.3). Jeśli
nadwyżka wyjdzie ≈0 na całej siatce, to razem z 1A jest to spójna teza
(„separacja przypisywana DG jest w większości rzadkością"), a nie porażka.

Uruchomienie
------------
    python run_matched_activity.py --preset quick
    python run_matched_activity.py --preset full --jobs 16
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
    DGConfig, active_fraction, binary_mi_io, make_connectivity, make_input_spikes,
    make_patterns, mean_pairwise_jaccard, nan_mean, population_sparseness, simulate,
)
from dg_core.calibrate import solve_k_gc_for_active_fraction  # noqa: E402
from dg_core.nulls import separation_vs_null  # noqa: E402

RESULTS = Path(__file__).parent / "results"

PRESETS = {
    'quick': dict(
        target_af=[0.05, 0.15, 0.25],
        W_FS_GC=[0.0, 1.0, 3.0],
        P_active=[0.25],
        seeds=[0],
        R_in=0.75, n_patterns=3,
    ),
    'full': dict(
        target_af=[0.02, 0.05, 0.10, 0.15, 0.20, 0.30],
        W_FS_GC=[0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0],
        P_active=[0.10, 0.25, 0.40],
        seeds=[0, 1, 2, 3, 4],
        R_in=0.75, n_patterns=4,
    ),
}

# Ile wolno spudłować w aktywność, żeby punkt liczył się jako „dopasowany".
# Punkty spoza tolerancji NIE są wyrzucane — są oznaczane, bo sam fakt, że dla
# danego W_FS_GC nie da się trafić w cel, jest informacją o obwodzie.
AF_TOL = 0.02


def run_cell(target: float, w_fs_gc: float, p_active: float, seed: int,
             grid: dict, N_GC: int, T_ms: float) -> dict:
    """Jeden punkt: dobierz K_GC do zadanej aktywności, zmierz nadwyżkę nad nullem."""
    base = DGConfig(T_ms=T_ms).scaled(N_GC)
    cfg = replace(base, W_FS_GC=w_fs_gc)

    conn = make_connectivity(cfg, seed=seed)
    pats, r_in_meas = make_patterns(N_GC, grid['n_patterns'], grid['R_in'],
                                    p_active, seed=100 + seed)

    # 1) zadana aktywność — bisekcja po hamowaniu TONICZNYM, przy ustalonym FAZOWYM
    k_gc, af_hit = solve_k_gc_for_active_fraction(
        cfg, conn, pats[0], target, seed=1000 * (seed + 1))
    cfg = replace(cfg, K_GC=k_gc)

    # 2) właściwy pomiar przy już wyrównanej aktywności
    gc_vecs, ret = [], []
    for k in range(grid['n_patterns']):
        idx, t = make_input_spikes(pats[k], cfg, seed=1000 * (seed + 1) + k)
        res = simulate(cfg, idx, t, conn)
        gc_vecs.append(res['gc_rates'])
        ret.append(binary_mi_io(pats[k], res['gc_rates'])['retention'])

    rng = np.random.default_rng(7000 + seed)
    nulls = separation_vs_null(gc_vecs, pats, r_in_meas, rng)

    gc0 = gc_vecs[0]
    act = active_fraction(gc0)

    row = {
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
    tasks = [(a, w, p, s)
             for a in grid['target_af']
             for w in grid['W_FS_GC']
             for p in grid['P_active']
             for s in grid['seeds']]
    shard = tasks[args.shard::args.n_shards]

    print(f"preset={args.preset}  N_GC={args.n_gc}  T={args.t_ms:.0f} ms")
    print(f"punktów (cel_AF × W_FS_GC × P_active × seed): {len(tasks)}  "
          f"(shard {args.shard}/{args.n_shards} → {len(shard)})")
    print(f"każdy punkt = bisekcja (do 14 symulacji) + {grid['n_patterns']} pomiarowych\n")

    t0 = time.time()
    rows = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_cell)(a, w, p, s, grid, args.n_gc, args.t_ms)
        for a, w, p, s in shard)

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
        print("  kombinacji cel aktywności leży poza zasięgiem K_GC ∈ [0, 24].")

    report(payload)


def report(p: dict) -> None:
    """Werdykt dla H1′ — liczony wyłącznie na punktach o wyrównanej aktywności."""
    m = p['matched'].astype(bool)
    if m.sum() < 3:
        print("\nZa mało dopasowanych punktów na werdykt.")
        return

    print("\n── H1′: nadwyżka separacji ponad null, przy dopasowanej aktywności ──")
    print(f"{'cel AF':>7} {'n':>4} {'dec':>8} {'−shuffle':>10} {'−kWTA':>9} {'retention':>10}")
    for a in np.unique(p['target_af'][m]):
        s = m & (p['target_af'] == a)
        print(f"{a:>7.2f} {int(s.sum()):>4} {p['dec'][s].mean():>8.3f} "
              f"{p['dec_excess_shuffle'][s].mean():>10.3f} "
              f"{p['dec_excess_kwta'][s].mean():>9.3f} "
              f"{p['retention'][s].mean():>10.3f}")

    # Czy hamowanie FAZOWE kupuje cokolwiek, gdy cisza jest wyrównana?
    print("\n── czy W_FS_GC kupuje nadwyżkę przy ustalonej aktywności? ──")
    print(f"{'W_FS_GC':>8} {'n':>4} {'−shuffle':>10} {'−kWTA':>9}")
    for w in np.unique(p['W_FS_GC'][m]):
        s = m & (p['W_FS_GC'] == w)
        print(f"{w:>8.2f} {int(s.sum()):>4} {p['dec_excess_shuffle'][s].mean():>10.3f} "
              f"{p['dec_excess_kwta'][s].mean():>9.3f}")

    ex = p['dec_excess_shuffle'][m]
    sd = float(ex.std(ddof=1)) if ex.size > 1 else 0.0
    sem = sd / np.sqrt(ex.size) if ex.size > 1 else 0.0
    band = max(0.02, 2 * sem)           # nieodróżnialne od zera
    mu = float(ex.mean())
    print(f"\nnadwyżka ponad null permutacyjny: {mu:+.3f} ± {sd:.3f} (SD), "
          f"SEM {sem:.3f}, n={ex.size}")

    # Trójstronnie — znak ma znaczenie. H1′ wymaga nadwyżki DODATNIEJ;
    # ujemna to osobny, mocniejszy wynik, nie „prawie potwierdzenie".
    if mu > band:
        print("WYNIK: nadwyżka DODATNIA — obwód separuje lepiej niż kod o tej samej")
        print("   rzadkości. H1′ wstępnie potwierdzona; sprawdzić, czy nadwyżka ma")
        print("   maksimum w W_FS_GC (tabela wyżej) — to jest pełna treść H1′.")
    elif mu < -band:
        print("WYNIK: nadwyżka UJEMNA — przetasowanie wyjścia daje WIĘCEJ dekorelacji")
        print("   niż prawdziwy obwód. To znaczy, że o tym, KTÓRY GC strzela, decyduje")
        print("   wejście: nakładające się wzorce pobudzają nakładające się GC, więc")
        print("   obwód ZACHOWUJE korelację względem losowego przypisania.")
        print("   H1′ OBALONA — i to mocniej niż wynikiem zerowym. Spójne z 1A (§3.3).")
    else:
        print("WYNIK: nadwyżka nieodróżnialna od zera. Separacja siedzi w RZADKOŚCI,")
        print("   nie w tym, który neuron strzela — spójne z 1A (STATUS §3.3).")
        print("   H1′ NIE potwierdzona.")

    # Tautologia P_active: czy maksimum retention idzie za rzadkością wejścia?
    ps = np.unique(p['P_active'][m])
    if len(ps) > 1:
        print("\n── test tautologii: czy maksimum retention idzie za P_active? ──")
        peaks = []
        for pa in ps:
            s = m & (p['P_active'] == pa)
            pk = float(p['af_measured'][s][np.argmax(p['retention'][s])])
            peaks.append(pk)
            print(f"  P_active {pa:.2f} → maksimum retention przy AF {pk:.3f}")
        follows = np.corrcoef(ps, peaks)[0, 1] > 0.9 if len(ps) > 2 else \
            abs(peaks[-1] - peaks[0]) > 0.5 * abs(ps[-1] - ps[0])
        print("  → " + ("IDZIE za P_active: to tautologia estymatora MI, nie własność"
                        " obwodu.\n     Nie raportować maksimum retention jako wyniku."
                        if follows else
                        "STOI mimo zmiany P_active: to realny punkt pracy obwodu.\n"
                        "     To jest kandydat na tezę nośną w miejsce H1."))


if __name__ == '__main__':
    main()
