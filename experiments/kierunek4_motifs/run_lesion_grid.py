"""
kierunek4_motifs/run_lesion_grid.py

EKSPERYMENT 4A — który motyw hamowania odpowiada za separację i KIEDY.

Pytanie badawcze
----------------
Przy jakiej STATYSTYCE wejścia (korelacja R_in, rzadkość P_active, tempo) za
dekorelację odpowiada głównie feedforward, feedback, czy mossy cells?

Metoda
------
Dla każdego punktu siatki (R_in × P_active × drive) uruchamiamy WSZYSTKIE 2^3 = 8
lezji obwodu (FF/FB/MC on-off) na TYCH SAMYCH wzorcach i TEJ SAMEJ sieci — więc
jedyną zmienną jest obecność motywu. Z ośmiu wartości dekorelacji liczymy
wartość Shapleya każdego motywu (patrz dg_core/metrics.py).

Dlaczego Shapley, a nie „on minus off"
--------------------------------------
FF i FB dzielą wspólną drogę wyjściową FS→GC, więc ich efekty NIE są addytywne:
naiwne „włącz/wyłącz" przypisałoby tę samą separację dwa razy. Shapley uśrednia
wkład krańcowy po wszystkich kolejnościach wejścia motywów do obwodu i jako
jedyny podział spełnia Σφ_i = v(pełny) − v(brak hamowania). Dzięki temu zdanie
„FF odpowiada za X% separacji" jest dosłownie prawdziwe, a nie retoryczne.

Dwa reżimy mossy cells
----------------------
Przy DOMYŚLNYCH wagach interactive_dg.py mossy cells są martwe: nie strzelają
(W_GC_HMC=1 << G_crit=14 mV), a nawet zmuszone do strzelania dostarczają ~0.1 mV
wobec ~3.6 mV z FS→GC. Sweep tylko w tym punkcie odpowiadałby na pytanie
z góry ustawione — MC nie mogłyby wygrać, bo są odłączone, a nie dlatego, że
statystyka wejścia im nie sprzyja. Dlatego liczymy siatkę w DWÓCH reżimach:

  mc_inert  — domyślny (drive=1, gain=1, brake=0)      → MC nieaktywne
  mc_active — MC żywe i ustabilizowane (drive=16, gain=20, brake=2)

Różnica między mapami dominacji w tych reżimach JEST wynikiem: pokazuje, ile
z „dominacji FF/FB" bierze się z biologii, a ile z doboru wag.

Uruchomienie
------------
  python run_lesion_grid.py --preset quick          # ~kilka minut, sanity check
  python run_lesion_grid.py --preset full -j 14     # pełna siatka, lokalnie
  python run_lesion_grid.py --preset full --shard $SLURM_ARRAY_TASK_ID --n-shards 50
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:  # konsola Windows domyślnie cp1250 — dławi się strzałkami/φ w logach
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from joblib import Parallel, delayed  # noqa: E402

from dg_core import (  # noqa: E402
    DGConfig, MOTIFS, config_from_motif_set, make_connectivity, simulate,
    make_patterns, make_input_spikes, mean_pairwise_r,
    population_sparseness, active_fraction,
    activity_battery, BATTERY_KEYS, mean_pairwise_cosine, mean_pairwise_jaccard,
    nan_mean,
)

RESULTS = Path(__file__).parent / "results"

# ── Reżimy mossy cells (drive = W_GC_HMC, gain = mnożnik wyjścia, brake = W_FS_HMC) ──
MC_REGIMES = {
    'mc_inert':  dict(drive=1.0,  gain=1.0,  brake=0.0),
    'mc_active': dict(drive=16.0, gain=20.0, brake=2.0),
}

# ── Siatki parametrów ─────────────────────────────────────────────────────────
PRESETS = {
    'quick': dict(
        R_in=[0.40, 0.75, 0.95],
        P_active=[0.10, 0.25],
        drive=[1.0],
        seeds=[0, 1],
        n_patterns=3,
        regimes=['mc_inert', 'mc_active'],
    ),
    'full': dict(
        R_in=[0.20, 0.40, 0.55, 0.70, 0.85, 0.95],
        P_active=[0.05, 0.10, 0.15, 0.25, 0.35, 0.50],
        drive=[0.5, 1.0, 2.0],
        seeds=[0, 1, 2, 3, 4],
        n_patterns=4,
        regimes=['mc_inert', 'mc_active'],
    ),
}

ALL_COALITIONS = [frozenset(c)
                  for k in range(len(MOTIFS) + 1)
                  for c in itertools.combinations(MOTIFS, k)]


def coalition_key(s: frozenset) -> str:
    """Stabilna nazwa koalicji do zapisu w NPZ: '', 'FF', 'FB+MC', 'FF+FB+MC'."""
    return '+'.join(m for m in MOTIFS if m in s)


# ══════════════════════════════════════════════════════════════════════════════
# Jedno zadanie = jeden punkt siatki × jeden seed → 8 lezji
# ══════════════════════════════════════════════════════════════════════════════

def run_cell(r_in: float, p_active: float, drive: float, regime: str,
             seed: int, n_patterns: int, N_GC: int, T_ms: float) -> dict:
    """
    Zwraca dekorelację (+ metryki pomocnicze) dla wszystkich 8 koalicji motywów.

    Kluczowe dla poprawności: wzorce, sieć i spajki PP są IDENTYCZNE we wszystkich
    ośmiu lezjach (te same seedy) — więc różnica w dekorelacji pochodzi wyłącznie
    z obecności/braku motywu, a nie z innej realizacji szumu.
    """
    mc = MC_REGIMES[regime]
    # .scaled() skaluje N_FS/N_HMC razem z N_GC — bez tego duża sieć wycisza się do zera
    base = DGConfig(T_ms=T_ms, W_FS_HMC=mc['brake']).scaled(N_GC)
    base = base.with_mc_strength(drive=mc['drive'], gain=mc['gain'])
    base = base.drive_scaled(drive)

    conn = make_connectivity(base, seed=seed)
    pats, r_in_meas = make_patterns(N_GC, n_patterns, r_in, p_active, seed=100 + seed)

    # Spajki PP generujemy RAZ i podajemy do każdej lezji — wspólne wejście.
    inputs = [make_input_spikes(pats[k], base, seed=1000 * (seed + 1) + k)
              for k in range(n_patterns)]

    out = {
        'r_in': r_in_meas,
        'dec': {}, 'r_out': {}, 'fr_gc': {}, 'fr_gc_active': {},
        'sparseness': {}, 'active_frac': {}, 'fr_fs': {}, 'fr_hmc': {},
        # bateria metryk aktywności/informacji (definicje: doktorat_plan.md §5)
        # + alternatywne miary separacji (kontrola dla dekorelacji Pearsona)
        **{k: {} for k in BATTERY_KEYS},
        'r_out_cos': {}, 'overlap_jac': {},
    }

    for coal in ALL_COALITIONS:
        cfg = config_from_motif_set(base, coal)
        gc_vecs, fs_fr, hmc_fr, batteries = [], [], [], []
        for k, (idx, t) in enumerate(inputs):
            res = simulate(cfg, idx, t, conn)
            gc_vecs.append(res['gc_rates'])
            fs_fr.append(res['fs_rates'].mean())
            hmc_fr.append(res['hmc_rates'].mean())
            batteries.append(activity_battery(res, pats[k], T_ms))

        r_out = mean_pairwise_r(gc_vecs)
        gc0 = gc_vecs[0]
        act = active_fraction(gc0)
        key = coalition_key(coal)

        out['dec'][key] = r_in_meas - r_out
        out['r_out'][key] = r_out
        out['fr_gc'][key] = float(np.mean([v.mean() for v in gc_vecs]))
        # FR liczona po AKTYWNYCH GC — kanon „~6 Hz" z dg_params dotyczy właśnie ich
        out['fr_gc_active'][key] = float(gc0[gc0 > 0.5].mean()) if act > 0 else 0.0
        out['sparseness'][key] = population_sparseness(gc0)
        out['active_frac'][key] = act
        out['fr_fs'][key] = float(np.mean(fs_fr))
        out['fr_hmc'][key] = float(np.mean(hmc_fr))
        for m in BATTERY_KEYS:
            out[m][key] = nan_mean(b[m] for b in batteries)
        out['r_out_cos'][key] = mean_pairwise_cosine(gc_vecs)
        out['overlap_jac'][key] = mean_pairwise_jaccard(gc_vecs)

    return out


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--preset', choices=list(PRESETS), default='quick')
    ap.add_argument('-j', '--n-jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument('--n-gc', type=int, default=200)
    ap.add_argument('--t-ms', type=float, default=600.0)
    ap.add_argument('--shard', type=int, default=0, help='indeks sharda (SLURM array)')
    ap.add_argument('--n-shards', type=int, default=1)
    ap.add_argument('--out', type=str, default=None)
    args = ap.parse_args()

    grid = PRESETS[args.preset]
    RESULTS.mkdir(exist_ok=True)

    tasks = [
        (r, p, d, reg, s)
        for reg in grid['regimes']
        for r in grid['R_in']
        for p in grid['P_active']
        for d in grid['drive']
        for s in grid['seeds']
    ]
    tasks_shard = tasks[args.shard::args.n_shards]

    n_sims = len(tasks_shard) * len(ALL_COALITIONS) * grid['n_patterns']
    print(f"preset={args.preset}  N_GC={args.n_gc}  T={args.t_ms:.0f} ms")
    print(f"punktów siatki × seed: {len(tasks)}  (shard {args.shard}/{args.n_shards} "
          f"→ {len(tasks_shard)})")
    print(f"symulacji Brian2 w tym shardzie: {n_sims:,}  "
          f"(≈{n_sims * 1.3 / max(1, args.n_jobs) / 60:.0f} min na {args.n_jobs} rdzeniach)\n")

    t0 = time.time()
    results = Parallel(n_jobs=args.n_jobs, verbose=10)(
        delayed(run_cell)(r, p, d, reg, s, grid['n_patterns'], args.n_gc, args.t_ms)
        for (r, p, d, reg, s) in tasks_shard
    )
    elapsed = time.time() - t0

    # ── zapis: płaskie tablice + osie, żeby analiza nie musiała znać kolejności ──
    coal_names = [coalition_key(c) for c in ALL_COALITIONS]
    metrics = ['dec', 'r_out', 'fr_gc', 'fr_gc_active', 'sparseness',
               'active_frac', 'fr_fs', 'fr_hmc',
               *BATTERY_KEYS, 'r_out_cos', 'overlap_jac']

    payload = {
        'task_r_in':     np.array([t[0] for t in tasks_shard]),
        'task_p_active': np.array([t[1] for t in tasks_shard]),
        'task_drive':    np.array([t[2] for t in tasks_shard]),
        'task_regime':   np.array([t[3] for t in tasks_shard]),
        'task_seed':     np.array([t[4] for t in tasks_shard]),
        'r_in_measured': np.array([r['r_in'] for r in results]),
        'coalitions':    np.array(coal_names),
        'motifs':        np.array(list(MOTIFS)),
        'grid_R_in':     np.array(grid['R_in']),
        'grid_P_active': np.array(grid['P_active']),
        'grid_drive':    np.array(grid['drive']),
        'grid_regimes':  np.array(grid['regimes']),
        'n_patterns':    grid['n_patterns'],
        'N_GC':          args.n_gc,
        'T_ms':          args.t_ms,
        'elapsed_s':     elapsed,
    }
    # metryka[i, j] = wartość dla zadania i, koalicji j
    for m in metrics:
        payload[m] = np.array([[r[m][c] for c in coal_names] for r in results])

    suffix = f"_shard{args.shard:03d}" if args.n_shards > 1 else ""
    out = Path(args.out) if args.out else RESULTS / f"lesion_grid_{args.preset}{suffix}.npz"
    np.savez_compressed(out, **payload)

    print(f"\nGotowe w {elapsed/60:.1f} min → {out}")
    print(f"Analiza:  python analyze_motifs.py --in {out.name}")


if __name__ == '__main__':
    main()
