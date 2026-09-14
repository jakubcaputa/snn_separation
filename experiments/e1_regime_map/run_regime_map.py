"""
e1_regime_map/run_regime_map.py

EKSPERYMENT 4B — MAPA REŻIMÓW: czy istnieje okno funkcjonalne separacji.

Czym to się różni od `run_lesion_grid.py` (i dlaczego to osobny skrypt)
-----------------------------------------------------------------------
`run_lesion_grid.py` zmienia STATYSTYKĘ WEJŚCIA (R_in, rzadkość, tempo) i pyta
**który motyw hamowania** odpowiada za separację. Nie ma tam ani jednej osi
hamowania, więc nie może odpowiedzieć na pytanie, ile hamowania jest optymalne.

Tutaj jest odwrotnie: zamrażamy statystykę wejścia i zmieniamy **siłę hamowania**
w obu jego postaciach:

    K_GC     — hamowanie TONICZNE  (oś pionowa)
    W_FS_GC  — hamowanie FAZOWE, synaptyczne (oś pozioma)

To jest test hipotezy H1 (`doktorat_plan.md` §5):

> separacja NIE rośnie monotonicznie z hamowaniem, tylko ma optimum przy
> pośredniej frakcji aktywnych GC, a poza nim się załamuje — z jednej strony
> przez wyciszenie sieci, z drugiej przez utratę rzadkości.

Główna figura to separacja w funkcji **ZMIERZONEJ** frakcji aktywnych GC, a nie
w funkcji parametrów. Parametry są tylko sposobem, żeby przesunąć się po osi
aktywności; twierdzenie dotyczy aktywności.

⚠️ Pułapka nr 3 z `doktorat_plan.md` obowiązuje tu podwójnie
------------------------------------------------------------
Dekorelacja przy FR→0 jest artefaktem: korelacja niemal pustego wektora dąży do
zera, więc „separacja" rośnie dokładnie wtedy, gdy sieć przestaje liczyć.
Dlatego każdy punkt dostaje MASKĘ WAŻNOŚCI (`valid`) i analiza bez niej jest
bezwartościowa. Maska wymaga minimum aktywnych GC i minimum częstotliwości.

⚠️ Pułapka nr 4 (nowa, `doktorat_plan.md` §4.4)
-----------------------------------------------
`K_GC` ustala JEDNOCZEŚNIE próg efektywny, potencjał spoczynkowy i budżet
hamowania tonicznego. Przesuwanie się po osi K to więc nie tylko „więcej
hamowania", ale też inne właściwości błony. Dlatego zapisujemy dla każdego
punktu wynikowe (V_rest, V_th_eff) — bez tego wykres byłby nieuczciwy.

Uruchomienie
------------
    python run_regime_map.py --preset quick         # sanity check
    python run_regime_map.py --preset full -j 14
    python run_regime_map.py --preset full --shard $SLURM_ARRAY_TASK_ID --n-shards 20
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
    DGConfig, active_fraction, make_connectivity, make_input_spikes,
    make_patterns, mean_pairwise_cosine, mean_pairwise_jaccard, mean_pairwise_r,
    population_sparseness, simulate,
)
from dg_core.calibrate import izh_fixed_points  # noqa: E402

RESULTS = Path(__file__).parent / "results"

PRESETS = {
    'quick': dict(
        K_GC=[0.0, 5.0, 10.0, 15.0],
        W_FS_GC=[0.0, 1.0, 3.0],
        seeds=[0],
        R_in=0.75, P_active=0.25, n_patterns=3,
    ),
    'full': dict(
        K_GC=[0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0],
        W_FS_GC=[0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0],
        seeds=[0, 1, 2, 3, 4],
        R_in=0.75, P_active=0.25, n_patterns=4,
    ),
}

# ── Maska ważności — patrz ostrzeżenie w nagłówku ────────────────────────────
MIN_ACTIVE_FRAC = 0.02      # co najmniej 2% GC musi strzelać
MIN_FR_ACTIVE = 0.5         # Hz, po aktywnych GC


def run_cell(k_gc: float, w_fs_gc: float, seed: int, grid: dict,
             N_GC: int, T_ms: float) -> dict:
    """Jeden punkt mapy: ustalone hamowanie, zmierzona separacja i aktywność."""
    base = DGConfig(T_ms=T_ms).scaled(N_GC)
    cfg = replace(base, K_GC=k_gc, W_FS_GC=w_fs_gc)

    conn = make_connectivity(cfg, seed=seed)
    pats, r_in_meas = make_patterns(N_GC, grid['n_patterns'], grid['R_in'],
                                    grid['P_active'], seed=100 + seed)

    gc_vecs, fs_fr, hmc_fr = [], [], []
    for k in range(grid['n_patterns']):
        idx, t = make_input_spikes(pats[k], cfg, seed=1000 * (seed + 1) + k)
        res = simulate(cfg, idx, t, conn)
        gc_vecs.append(res['gc_rates'])
        fs_fr.append(res['fs_rates'].mean())
        hmc_fr.append(res['hmc_rates'].mean())

    gc0 = gc_vecs[0]
    act = active_fraction(gc0)
    fr_active = float(gc0[gc0 > 0.5].mean()) if act > 0 else 0.0
    r_out = mean_pairwise_r(gc_vecs)
    v_rest, v_th = izh_fixed_points(k_gc)

    return {
        'K_GC': k_gc, 'W_FS_GC': w_fs_gc, 'seed': seed,
        'r_in': r_in_meas, 'r_out': r_out, 'dec': r_in_meas - r_out,
        'r_out_cos': mean_pairwise_cosine(gc_vecs),
        'overlap_jac': mean_pairwise_jaccard(gc_vecs),
        'active_frac': act,
        'fr_gc': float(np.mean([v.mean() for v in gc_vecs])),
        'fr_gc_active': fr_active,
        'sparseness': population_sparseness(gc0),
        'fr_fs': float(np.mean(fs_fr)),
        'fr_hmc': float(np.mean(hmc_fr)),
        # pułapka §4.4 — K zmienia też błonę, więc zapisujemy co się z nią stało
        'v_rest': v_rest, 'v_th_eff': v_th,
        # maska ważności — bez niej „separacja" przy wyciszeniu jest artefaktem
        'valid': bool(act >= MIN_ACTIVE_FRAC and fr_active >= MIN_FR_ACTIVE),
    }


def main():
    ap = argparse.ArgumentParser(description="Mapa reżimów: separacja vs poziom aktywności")
    ap.add_argument('--preset', choices=list(PRESETS), default='quick')
    ap.add_argument('--n-gc', type=int, default=200)
    ap.add_argument('--t-ms', type=float, default=600.0)
    ap.add_argument('-j', '--jobs', type=int, default=-1)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--n-shards', type=int, default=1)
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    grid = PRESETS[args.preset]
    tasks = [(k, w, s)
             for k in grid['K_GC']
             for w in grid['W_FS_GC']
             for s in grid['seeds']]
    shard = tasks[args.shard::args.n_shards]

    n_sims = len(shard) * grid['n_patterns']
    print(f"preset={args.preset}  N_GC={args.n_gc}  T={args.t_ms:.0f} ms")
    print(f"punktów siatki (K × W_FS_GC × seed): {len(tasks)}  "
          f"(shard {args.shard}/{args.n_shards} → {len(shard)})")
    print(f"symulacji Brian2 w tym shardzie: {n_sims}")

    t0 = time.time()
    rows = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_cell)(k, w, s, grid, args.n_gc, args.t_ms) for k, w, s in shard)

    keys = list(rows[0].keys())
    payload = {k: np.array([r[k] for r in rows]) for k in keys}
    payload['grid_K_GC'] = np.array(grid['K_GC'])
    payload['grid_W_FS_GC'] = np.array(grid['W_FS_GC'])

    RESULTS.mkdir(exist_ok=True)
    suffix = f"_shard{args.shard}" if args.n_shards > 1 else ""
    out = Path(args.out) if args.out else RESULTS / f"regime_map_{args.preset}{suffix}.npz"
    np.savez_compressed(out, **payload)

    n_valid = int(payload['valid'].sum())
    print(f"\nGotowe w {(time.time() - t0) / 60:.1f} min → {out}")
    print(f"punktów ważnych (po masce): {n_valid}/{len(rows)}")
    if n_valid < len(rows):
        print(f"  {len(rows) - n_valid} punktów ODRZUCONYCH jako wyciszone — "
              f"ich 'separacja' byłaby artefaktem pustego wektora.")

    # Szybka diagnoza: czy widać okno, czy tylko monotoniczny wzrost ku ciszy.
    v = payload['valid'].astype(bool)
    if v.sum() >= 3:
        a, dec = payload['active_frac'][v], payload['dec'][v]
        j = np.argsort(a)
        best = a[j][int(np.argmax(dec[j]))]
        mono = bool(np.all(np.diff(dec[j]) <= 0) or np.all(np.diff(dec[j]) >= 0))
        print(f"\nmaksimum separacji przy {best:.1%} aktywnych GC "
              f"(dekorelacja {dec.max():.3f})")
        if mono or best <= a.min() + 1e-9:
            print("  ⚠️ Separacja rośnie MONOTONICZNIE ku rzadszej aktywności, a maksimum")
            print("     leży na KRAŃCU siatki. To jest sygnatura artefaktu wyciszenia,")
            print("     a nie okna funkcjonalnego — H1 NIE jest tym potwierdzona.")
            print("     Rozszerz siatkę, albo zaostrz maskę ważności (MIN_ACTIVE_FRAC,")
            print("     MIN_FR_ACTIVE) i sprawdź, czy maksimum przesuwa się do wnętrza.")
        else:
            print("  Maksimum leży WEWNĄTRZ siatki — zgodne z H1, do potwierdzenia")
            print("  na pełnej siatce z przedziałami ufności.")


if __name__ == '__main__':
    main()
