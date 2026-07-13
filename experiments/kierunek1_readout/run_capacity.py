"""
kierunek1_readout/run_capacity.py

EKSPERYMENT 1B — pojemność pamięci skojarzeniowej (DG → CA3).

Pytanie badawcze
----------------
Ile wzorców można zapisać w pamięci skojarzeniowej BEZ przekłamań, gdy wejście
przechodzi przez DG — i jak ta pojemność zależy od SIŁY HAMOWANIA (W FS→GC)?

To jest druga metryka kierunku 1: nie „czy klasyfikator ma lepiej", tylko
„ile pamięci zyskujemy" — wielkość, o którą naprawdę chodzi w hipotezie
o roli DG jako preprocesora dla CA3.

Model pamięci
-------------
Sieć atraktorowa Hopfielda z regułą KOWARIANCYJNĄ Tsodyksa–Feigelmana:

    W_ij = 1/(N·a·(1−a)) · Σ_p (ξ_i^p − a)(ξ_j^p − a),    W_ii = 0

gdzie a = średnia aktywność wzorca. Klasyczna reguła Hebba ±1 dla RZADKICH
wzorców załamuje się (wszystko zbiega do jednego atraktora) — dla rzadkiego
kodowania, o które tu chodzi, reguła kowariancyjna jest właściwym modelem.
Dynamika: k-WTA (utrzymuje stałą rzadkość, standard w rzadkich sieciach
atraktorowych) — bez tego trzeba by stroić próg θ osobno w każdym warunku,
co samo w sobie zaburzyłoby porównanie.

Pojemność
---------
Zapisujemy P wzorców, odpytujemy zaszumioną wskazówką, iterujemy do zbieżności.
Jakość odtworzenia = podobieństwo Jaccarda z celem.
POJEMNOŚĆ = największe P, przy którym średnia jakość ≥ `--recall-thr` (dom. 0.90).

Warunki: te same co w 1A (raw / dg / dg_noinh), plus oś siły hamowania W_FS_GC.

Uruchomienie
------------
  python run_capacity.py --preset quick
  python run_capacity.py --preset full -j 14
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

from dataclasses import replace  # noqa: E402

from joblib import Parallel, delayed  # noqa: E402

from dg_core import (  # noqa: E402
    DGConfig, make_connectivity, make_input_spikes, make_patterns,
    pp_rate_vector_empirical, simulate, mean_pairwise_r,
)

RESULTS = Path(__file__).parent / "results"

CONDITIONS = ['raw', 'dg', 'dg_noinh']

# Siatka n_store MUSI zaczynać się nisko: przy skorelowanych wzorcach (R_in≥0.75)
# pamięć załamuje się szybko i jeśli najmniejsze P już nie trzyma progu, wszystkie
# warunki siedzą na zerze i niczego nie rozróżniamy. Główny wynik to KRZYWA
# degradacji (ciągła), a nie sam próg pojemności (schodkowy).
PRESETS = {
    'quick': dict(
        W_FS_GC=[0.5, 1.0, 2.0],
        n_store=[2, 3, 4, 6, 8, 12],
        R_in=[0.75],
        seeds=[0],
        cue_noise=0.10, p_active=0.25,
    ),
    'full': dict(
        W_FS_GC=[0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0],
        n_store=[2, 3, 4, 6, 8, 12, 16, 24, 32, 48],
        R_in=[0.50, 0.75, 0.90],
        seeds=[0, 1, 2],
        cue_noise=0.10, p_active=0.25,
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# Pamięć skojarzeniowa
# ══════════════════════════════════════════════════════════════════════════════

def binarize_natural(X: np.ndarray) -> np.ndarray:
    """
    Binaryzacja progiem w połowie zakresu każdego wektora — „naturalny kod"
    danej reprezentacji, z jej własną rzadkością.

    DLACZEGO NIE top-k (ważne, bo to była realna pułapka):
    wektor `raw` jest niemal binarny (400 Hz aktywne vs 40 Hz tło), więc wszystkie
    ~50 aktywnych jednostek ma TĘ SAMĄ częstotliwość nominalną. Wymuszenie top-k=20
    każe wybrać 20 z 50 remisów — a rozstrzyga je czysty jitter Poissona. To losowo
    przetasowuje wzorce, sztucznie DEKORELUJE baseline i daje mu przewagę, której
    w rzeczywistości nie ma. Próg w połowie zakresu zachowuje strukturę wzorca.
    """
    lo = X.min(axis=1, keepdims=True)
    hi = X.max(axis=1, keepdims=True)
    thr = lo + 0.5 * (hi - lo)
    return (X > thr).astype(float)


def binarize_topk(X: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """
    Kontrola z DOPASOWANĄ rzadkością: dokładnie k aktywnych jednostek.

    Remisy rozstrzygamy jawnym, kontrolowanym losowaniem (drobny szum przed
    sortowaniem) zamiast udawać, że o kolejności decyduje sygnał. Ta wersja służy
    jako kontrola „czy przewaga bierze się z rzadkości", a NIE jako główna metryka —
    główną liczy `binarize_natural`, bo pojemność ma zależeć od reprezentacji,
    a nie od tego, jak ją przycięliśmy.
    """
    out = np.zeros_like(X, dtype=float)
    if k <= 0:
        return out
    Xj = X + rng.normal(0, 1e-6, size=X.shape)
    idx = np.argpartition(Xj, -k, axis=1)[:, -k:]
    np.put_along_axis(out, idx, 1.0, axis=1)
    return out


def hopfield_weights(patterns: np.ndarray) -> np.ndarray:
    """Reguła kowariancyjna Tsodyksa–Feigelmana (rzadkie kodowanie)."""
    P, N = patterns.shape
    a = float(patterns.mean())
    if a <= 0 or a >= 1:
        return np.zeros((N, N))
    dev = patterns - a
    W = (dev.T @ dev) / (N * a * (1.0 - a))
    np.fill_diagonal(W, 0.0)
    return W


def recall(W: np.ndarray, cue: np.ndarray, k: int, n_iter: int = 12) -> np.ndarray:
    """Dynamika k-WTA do zbieżności (albo n_iter kroków)."""
    S = cue.copy()
    for _ in range(n_iter):
        h = W @ S
        S_new = np.zeros_like(S)
        if k > 0:
            S_new[np.argpartition(h, -k)[-k:]] = 1.0
        if np.array_equal(S_new, S):
            break
        S = S_new
    return S


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    inter = float(np.sum((a > 0) & (b > 0)))
    union = float(np.sum((a > 0) | (b > 0)))
    return inter / union if union > 0 else 0.0


def corrupt(pattern: np.ndarray, noise: float, rng: np.random.Generator) -> np.ndarray:
    """Wskazówka = wzorzec z `noise` frakcją aktywnych bitów przeniesionych gdzie indziej."""
    on = np.where(pattern > 0)[0]
    off = np.where(pattern == 0)[0]
    n_flip = int(round(noise * len(on)))
    if n_flip == 0 or len(off) < n_flip:
        return pattern.copy()
    cue = pattern.copy()
    cue[rng.choice(on, n_flip, replace=False)] = 0.0
    cue[rng.choice(off, n_flip, replace=False)] = 1.0
    return cue


# ══════════════════════════════════════════════════════════════════════════════

def run_cell(w_fs_gc: float, n_store: int, r_in: float, seed: int,
             cue_noise: float, p_active: float, N_GC: int, T_ms: float,
             k_store: int) -> dict:
    """Zapisz n_store wzorców w każdej reprezentacji i zmierz jakość odtworzenia."""
    # .scaled() skaluje N_FS/N_HMC razem z N_GC — bez tego duża sieć wycisza się do zera
    cfg = replace(DGConfig(T_ms=T_ms).scaled(N_GC), W_FS_GC=w_fs_gc)
    cfg_noinh = cfg.with_motifs(False, False, False)
    conn = make_connectivity(cfg, seed=seed)

    pats, r_in_meas = make_patterns(N_GC, n_store, r_in, p_active, seed=200 + seed)

    reps = {c: [] for c in CONDITIONS}
    fr_gc = []
    for j, pat in enumerate(pats):
        idx, ts = make_input_spikes(pat, cfg, seed=20_000 * (seed + 1) + j)
        reps['raw'].append(pp_rate_vector_empirical(idx, cfg))
        res = simulate(cfg, idx, ts, conn)
        reps['dg'].append(res['gc_rates'])
        fr_gc.append(res['gc_rates'].mean())
        reps['dg_noinh'].append(simulate(cfg_noinh, idx, ts, conn)['gc_rates'])

    rng = np.random.default_rng(999 + seed)
    out = {'r_in_measured': r_in_meas, 'fr_gc': float(np.mean(fr_gc))}

    def measure(stored: np.ndarray, tag: str, cond: str):
        # k dynamiki k-WTA = faktyczna liczba aktywnych jednostek w tym kodzie
        k = max(1, int(round(stored.sum(axis=1).mean())))
        W = hopfield_weights(stored)
        q = [jaccard(recall(W, corrupt(stored[p], cue_noise, rng), k), stored[p])
             for p in range(n_store)]
        out[f'recall{tag}_{cond}'] = float(np.mean(q))
        out[f'recall{tag}_{cond}_sd'] = float(np.std(q))
        out[f'r_repr{tag}_{cond}'] = mean_pairwise_r(list(stored))
        out[f'sparsity{tag}_{cond}'] = float(stored.mean())

    for cond in CONDITIONS:
        X = np.array(reps[cond])
        # metryka GŁÓWNA — naturalny kod reprezentacji (własna rzadkość)
        measure(binarize_natural(X), '', cond)
        # KONTROLA — rzadkość wyrównana między warunkami
        measure(binarize_topk(X, k_store, rng), '_matched', cond)

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--preset', choices=list(PRESETS), default='quick')
    ap.add_argument('-j', '--n-jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument('--n-gc', type=int, default=200)
    ap.add_argument('--t-ms', type=float, default=600.0)
    ap.add_argument('--k-store', type=int, default=20,
                    help='rzadkość zapisywanych wzorców (aktywnych jednostek); '
                         'wspólna dla wszystkich warunków, by porównanie było uczciwe')
    ap.add_argument('--recall-thr', type=float, default=0.90)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--n-shards', type=int, default=1)
    ap.add_argument('--out', type=str, default=None)
    args = ap.parse_args()

    g = PRESETS[args.preset]
    RESULTS.mkdir(exist_ok=True)

    tasks = [(w, n, r, s) for w in g['W_FS_GC'] for n in g['n_store']
             for r in g['R_in'] for s in g['seeds']]
    shard = tasks[args.shard::args.n_shards]
    n_sims = sum(t[1] * 2 for t in shard)

    print(f"preset={args.preset}  N_GC={args.n_gc}  k_store={args.k_store}  "
          f"próg odtworzenia={args.recall_thr}")
    print(f"punktów: {len(tasks)} (shard {args.shard}/{args.n_shards} → {len(shard)})")
    print(f"symulacji Brian2: {n_sims:,}  "
          f"(≈{n_sims * 1.3 / max(1, args.n_jobs) / 60:.0f} min na {args.n_jobs} rdzeniach)\n")

    t0 = time.time()
    res = Parallel(n_jobs=args.n_jobs, verbose=10)(
        delayed(run_cell)(w, n, r, s, g['cue_noise'], g['p_active'],
                          args.n_gc, args.t_ms, args.k_store)
        for (w, n, r, s) in shard
    )
    elapsed = time.time() - t0

    payload = {
        'task_w_fs_gc': np.array([t[0] for t in shard]),
        'task_n_store': np.array([t[1] for t in shard]),
        'task_r_in':    np.array([t[2] for t in shard]),
        'task_seed':    np.array([t[3] for t in shard]),
        'grid_W_FS_GC': np.array(g['W_FS_GC']),
        'grid_n_store': np.array(g['n_store']),
        'grid_R_in':    np.array(g['R_in']),
        'conditions':   np.array(CONDITIONS),
        'recall_thr':   args.recall_thr,
        'k_store':      args.k_store,
        'cue_noise':    g['cue_noise'],
        'N_GC':         args.n_gc,
        'elapsed_s':    elapsed,
    }
    keys = ['r_in_measured', 'fr_gc']
    for tag in ('', '_matched'):
        keys += [f'recall{tag}_{c}' for c in CONDITIONS]
        keys += [f'recall{tag}_{c}_sd' for c in CONDITIONS]
        keys += [f'r_repr{tag}_{c}' for c in CONDITIONS]
        keys += [f'sparsity{tag}_{c}' for c in CONDITIONS]
    for k in keys:
        payload[k] = np.array([r[k] for r in res])

    suffix = f"_shard{args.shard:03d}" if args.n_shards > 1 else ""
    out = Path(args.out) if args.out else RESULTS / f"capacity_{args.preset}{suffix}.npz"
    np.savez_compressed(out, **payload)

    print(f"\nGotowe w {elapsed/60:.1f} min → {out}")
    print(f"Analiza:  python analyze_readout.py --capacity {out.name}")


if __name__ == '__main__':
    main()
