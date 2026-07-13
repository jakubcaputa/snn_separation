"""
kierunek1_readout/run_classification.py

EKSPERYMENT 1A — czy warstwa DG realnie pomaga odbiorcy downstream?

Pytanie badawcze
----------------
Czy separacja typu DG poprawia rozróżnianie SKORELOWANYCH i ZASZUMIONYCH wejść
w zadaniu klasyfikacji? O ile? I przy jakiej statystyce wejścia?

Zadanie
-------
`n_classes` prototypów o kontrolowanym podobieństwie R_in. Każda próba = prototyp
+ szum bit-flip (o zachowanej rzadkości, więc szum nie zmienia gęstości wejścia).
Odbiorca = klasyfikator LINIOWY (regresja logistyczna) — celowo słaby, bo pytamy
czy to DG wykonuje pracę, a nie czy odbiorca potrafi ją nadrobić.

Cztery warunki (to jest sedno eksperymentu)
-------------------------------------------
  raw        — zmierzone częstotliwości PP na GC. Baseline „bez DG".
               UCZCIWY: te same spajki, ten sam szum Poissona, ta sama wymiarowość.
  dg         — częstotliwości wyjściowe GC, pełny obwód.
  dg_noinh   — GC z WYŁĄCZONYM hamowaniem (FF/FB/MC off).
               Rozdziela dwie hipotezy: czy zysk daje OBWÓD, czy sama
               nieliniowość progowa neuronu spajkującego?
  random     — losowa projekcja + k-WTA, rzadkość DOPASOWANA do wyjścia DG.
               Najostrzejszy baseline: czy liczy się STRUKTURA obwodu DG, czy
               wystarczy dowolne rzadkie kodowanie o tej samej rzadkości?
               Bez tego warunku wynik „DG pomaga" jest niepublikowalny.

Metryka
-------
Δ accuracy = acc(dg) − acc(raw), jako funkcja R_in i poziomu szumu.
Plus acc(dg) − acc(random): ile z zysku pochodzi z biologii, a nie z rzadkości.

Uruchomienie
------------
  python run_classification.py --preset quick
  python run_classification.py --preset full -j 14
  python run_classification.py --preset full --shard $SLURM_ARRAY_TASK_ID --n-shards 40
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from joblib import Parallel, delayed  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.model_selection import StratifiedKFold, cross_val_score  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from dg_core import (  # noqa: E402
    DGConfig, make_class_trials, make_connectivity, make_input_spikes,
    pp_rate_vector_empirical, simulate, active_fraction, mean_pairwise_r,
)

RESULTS = Path(__file__).parent / "results"

CONDITIONS = ['raw', 'dg', 'dg_noinh', 'random']

# T_ms = OKNO ODCZYTU odbiorcy, i to jest oś eksperymentu, nie stała.
# Przy T=600 ms aktywny GC dostaje ~240 spajków PP → baseline 'raw' jest praktycznie
# bezszumowy, klasyfikator liniowy czyta z niego klasę bez trudu i DG (transformacja
# STRATNA) może tylko pogorszyć. Dopiero krótkie okno (mało spajków) tworzy reżim,
# w którym separacja ma co poprawiać. Patrz README — to sedno wyniku negatywnego.
PRESETS = {
    'quick': dict(
        R_in=[0.50, 0.85],
        noise=[0.10, 0.30],
        T_ms=[600.0],
        n_classes=4, n_trials=30, seeds=[0],
        p_active=0.25,
    ),
    'full': dict(
        R_in=[0.30, 0.50, 0.65, 0.80, 0.90, 0.95],
        noise=[0.0, 0.05, 0.10, 0.20, 0.30, 0.45],
        T_ms=[600.0],
        n_classes=5, n_trials=80, seeds=[0, 1, 2],
        p_active=0.25,
    ),
    # Reżim, w którym baseline 'raw' faktycznie się łamie — tu DG ma szansę wygrać.
    'hard': dict(
        R_in=[0.85, 0.92, 0.98],
        noise=[0.20, 0.40, 0.60],
        T_ms=[600.0, 150.0, 60.0],       # ← okno odczytu jako oś trudności
        n_classes=8, n_trials=60, seeds=[0, 1, 2],
        p_active=0.25,
    ),
}


def kwta_random_projection(X: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """
    Losowa rzadka ekspansja: X @ W, potem k-WTA (zostaw k najsilniejszych, reszta 0).

    To jest kontrola „rzadkość bez DG": ta sama wymiarowość i ta sama liczba
    aktywnych jednostek co w wyjściu GC, ale selekcja losowa, nie przez obwód.
    """
    n_feat = X.shape[1]
    W = rng.normal(0, 1 / np.sqrt(n_feat), size=(n_feat, n_feat))
    H = X @ W
    if k <= 0 or k >= n_feat:
        return H
    thr = np.partition(H, -k, axis=1)[:, -k][:, None]
    return np.where(H >= thr, H, 0.0)


def run_cell(r_in: float, noise: float, seed: int, n_classes: int, n_trials: int,
             p_active: float, N_GC: int, T_ms: float, n_folds: int = 5) -> dict:
    """
    Jeden punkt siatki (R_in, noise, seed): generuje próby, przepuszcza przez DG,
    trenuje i waliduje krzyżowo klasyfikator liniowy w każdym z 4 warunków.
    """
    # .scaled() skaluje N_FS/N_HMC razem z N_GC — bez tego duża sieć wycisza się do zera
    cfg = DGConfig(T_ms=T_ms).scaled(N_GC)
    cfg_noinh = cfg.with_motifs(False, False, False)
    conn = make_connectivity(cfg, seed=seed)

    trials, labels, protos, r_in_meas = make_class_trials(
        N_GC, n_classes, n_trials, r_in, p_active, noise, seed=7 + 100 * seed)

    X_raw, X_dg, X_noinh = [], [], []
    for t, pat in enumerate(trials):
        # Każda próba = własna realizacja Poissona; ten sam pociąg spajków PP
        # trafia i do baseline'u 'raw', i do DG — więc porównanie jest sparowane.
        idx, ts = make_input_spikes(pat, cfg, seed=10_000 * (seed + 1) + t)
        X_raw.append(pp_rate_vector_empirical(idx, cfg))
        X_dg.append(simulate(cfg, idx, ts, conn)['gc_rates'])
        X_noinh.append(simulate(cfg_noinh, idx, ts, conn)['gc_rates'])

    X = {
        'raw': np.array(X_raw),
        'dg': np.array(X_dg),
        'dg_noinh': np.array(X_noinh),
    }

    # Kontrola losowa z rzadkością dopasowaną do DG
    k_dg = int(round(np.mean([(v > 0.5).sum() for v in X['dg']])))
    X['random'] = kwta_random_projection(
        X['raw'], k_dg, np.random.default_rng(555 + seed))

    out = {'r_in_measured': r_in_meas, 'k_dg': k_dg}
    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

    for cond in CONDITIONS:
        Xc = X[cond]
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, C=1.0),
        )
        scores = cross_val_score(clf, Xc, labels, cv=cv, scoring='accuracy')
        out[f'acc_{cond}'] = float(scores.mean())
        out[f'acc_{cond}_sd'] = float(scores.std())

        # Korelacja reprezentacji między klasami — łącznik z metryką kierunku 4.
        # Jeśli DG podnosi accuracy, R_repr powinno spaść. Jeśli nie spada,
        # to zysk bierze się skądinąd i trzeba to wiedzieć.
        centroids = [Xc[labels == c].mean(0) for c in range(n_classes)]
        out[f'r_repr_{cond}'] = mean_pairwise_r(centroids)
        out[f'sparse_{cond}'] = float(np.mean([active_fraction(v) for v in Xc]))

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--preset', choices=list(PRESETS), default='quick')
    ap.add_argument('-j', '--n-jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument('--n-gc', type=int, default=200)
    ap.add_argument('--t-ms', type=float, default=600.0)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--n-shards', type=int, default=1)
    ap.add_argument('--out', type=str, default=None)
    args = ap.parse_args()

    g = PRESETS[args.preset]
    RESULTS.mkdir(exist_ok=True)

    tasks = [(r, n, T, s)
             for r in g['R_in'] for n in g['noise']
             for T in g['T_ms'] for s in g['seeds']]
    shard = tasks[args.shard::args.n_shards]

    n_sims = len(shard) * g['n_classes'] * g['n_trials'] * 2   # dg + dg_noinh
    print(f"preset={args.preset}  N_GC={args.n_gc}  klasy={g['n_classes']}  "
          f"prób/klasę={g['n_trials']}  okna T={g['T_ms']} ms")
    print(f"punktów: {len(tasks)} (shard {args.shard}/{args.n_shards} → {len(shard)})")
    print(f"symulacji Brian2: {n_sims:,}\n")

    t0 = time.time()
    res = Parallel(n_jobs=args.n_jobs, verbose=10)(
        delayed(run_cell)(r, n, s, g['n_classes'], g['n_trials'], g['p_active'],
                          args.n_gc, T)
        for (r, n, T, s) in shard
    )
    elapsed = time.time() - t0

    payload = {
        'task_r_in':  np.array([t[0] for t in shard]),
        'task_noise': np.array([t[1] for t in shard]),
        'task_t_ms':  np.array([t[2] for t in shard]),
        'task_seed':  np.array([t[3] for t in shard]),
        'grid_R_in':  np.array(g['R_in']),
        'grid_noise': np.array(g['noise']),
        'grid_T_ms':  np.array(g['T_ms']),
        'conditions': np.array(CONDITIONS),
        'n_classes':  g['n_classes'],
        'n_trials':   g['n_trials'],
        'chance':     1.0 / g['n_classes'],
        'N_GC':       args.n_gc,
        'elapsed_s':  elapsed,
    }
    keys = (['r_in_measured', 'k_dg']
            + [f'acc_{c}' for c in CONDITIONS] + [f'acc_{c}_sd' for c in CONDITIONS]
            + [f'r_repr_{c}' for c in CONDITIONS] + [f'sparse_{c}' for c in CONDITIONS])
    for k in keys:
        payload[k] = np.array([r[k] for r in res])

    suffix = f"_shard{args.shard:03d}" if args.n_shards > 1 else ""
    out = Path(args.out) if args.out else RESULTS / f"classification_{args.preset}{suffix}.npz"
    np.savez_compressed(out, **payload)

    print(f"\nGotowe w {elapsed/60:.1f} min → {out}")
    print(f"Analiza:  python analyze_readout.py --in {out.name}")


if __name__ == '__main__':
    main()
