"""
Kalibracja ex vivo — przeszukanie siatki (krok 1 po odpowiedzi prof. Błasiak, 2026-10-22).

Obwód dg_core napędzany protokołem Madara P10Hz R=0.75 (ten sam, co w parach przed/po
gabazynie), 5 pociągów × 10 powtórzeń × 2 s; każdy GC modelu = jedno „nagranie”.
Dla każdego punktu siatki: kontrola i gabazyna (W_FS_GC × 0.7, hamowanie toniczne bez
zmian). K_GC ustalone z V_rest = −76 mV (mediana GC w danych, STATUS sek. 3.8).

Cele (calib_exvivo/results/madar_targets.md, bin 10 ms, 10 powtórzeń):
  GC kontrola: częstotliwość ≈ 3 Hz (pary, ten sam protokół; mediana wszystkich GC 6.25),
               R_w ≈ 0.49, R_b ≈ 0.29
  GC gabazyna: ×FR ≈ 1.6 (mediana par), R_w ≈ 0.80, R_b ≈ 0.55
  FS kontrola: częstotliwość ≈ 8.4 Hz
Strata: suma kwadratów błędów logarytmicznych (FR, ×FR, FS) i bezwzględnych (R_w, R_b),
z wagami równymi; zapisujemy wszystkie punkty, wybór najlepszego jest jawny.

Użycie (z experiments/):
  python -m calib_exvivo.grid --chunk 0 --n-chunks 4 --jobs 16
  python -m calib_exvivo.grid --collect
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import math
import os
import time

import numpy as np

from dg_core import DGConfig, make_connectivity
from dg_core import io_madar as M
from dg_core.calibrate import izh_fixed_points
from dg_core.exvivo import exvivo_config, population_similarity, run_protocol

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results', 'grid_v3')
PROTOCOL = '10Hz_R0.750_CorrelatedPoisson.prt.axgx'
V_REST_TARGET = -76.0

# v2 (2026-10-22): siatka v1 (results/grid_v1/) pokazała, że FS odpalają PO GC
# (opóźnienie od salwy: FS 10.4 ms, GC 8–9 ms), więc hamowanie fazowe przychodzi za późno
# i „gabazyna” nic nie zmienia (×1.02 wobec ×1.6 w danych). Nowa oś: napęd PP→FS, który
# ustala, czy FS zdążą przed GC (hamowanie feedforward).
# v3 (2026-10-23): v2 trafiła kontrolę (GC 2.9 Hz, R_w 0.38, R_b 0.29, FS przed GC), ale
# gabazyna ×1.25 (cel 1.6) i FS 19 Hz (cel 8.4). Oś W_FS_FS — wzajemne hamowanie FS (B2).
GRID = {
    'W_volley': [20.0, 25.0],
    'W_PP_FS': [0.3, 0.4, 0.5],
    'W_FS_GC': [2.0, 5.0, 10.0],
    'p_rel': [0.6],
    'W_GC_FS': [0.0001, 0.5, 1.0],
    'W_FS_FS': [0.0, 1.0, 2.0],
}
TARGET = {'gc_fr': 3.0, 'gc_rw': 0.49, 'gc_rb': 0.29, 'gzn_ratio': 1.6, 'gzn_rw': 0.80,
          'gzn_rb': 0.55, 'fs_fr': 8.4}


def k_for_vrest(v_target: float, b: float = 0.2) -> float:
    """K_GC, przy którym stabilny punkt stały Izhikevicza (V_rest) = v_target.
    Z V_rest = −((5−b) + s)/0.08, s = √((5−b)² − 0.16(140 − K))  ⇒  postać zamknięta."""
    s = -0.08 * v_target - (5.0 - b)
    K = 140.0 - ((5.0 - b) ** 2 - s ** 2) / 0.16
    assert abs(izh_fixed_points(K, b)[0] - v_target) < 1e-6
    return K


def _latency_ms(cells, stim):
    """Mediana opóźnienia impulsu od ostatniej salwy przed nim [ms]."""
    lat = []
    for cell in cells:
        for k, t in enumerate(cell):
            pul = np.asarray(stim[k % len(stim)])
            for s in t:
                d = s - pul[pul <= s]
                if len(d):
                    lat.append(d.min() * 1000.0)
    return float(np.median(lat)) if lat else float('nan')


def summarize(run, stim):
    gc = population_similarity(run, stim, 0.010)
    fs_fr = [sum(len(t) for t in cell) / (len(cell) * 2.0) for cell in run['fs']]
    fin = lambda key: [r[key] for r in gc if np.isfinite(r[key])]
    return {'gc_fr': float(np.median([r['fr_hz'] for r in gc])),
            'gc_frac_active': float(np.mean([r['fr_hz'] > 0 for r in gc])),
            'gc_rw': float(np.median(fin('R_w'))) if fin('R_w') else float('nan'),
            'gc_rb': float(np.median(fin('R_b'))) if fin('R_b') else float('nan'),
            'gc_rw_5rep': float(np.nanmedian([r['R_w'] for r in population_similarity(run, stim, 0.010, 5)])),
            'fs_fr': float(np.median(fs_fr)),
            'gc_lat_ms': _latency_ms(run['gc'], stim), 'fs_lat_ms': _latency_ms(run['fs'], stim)}


def loss(c, g):
    t = TARGET
    lg = lambda a, b: (math.log(max(a, 1e-3)) - math.log(b)) ** 2
    ab = lambda a, b: (a - b) ** 2 if np.isfinite(a) else 1.0
    ratio = g['gc_fr'] / max(c['gc_fr'], 1e-3)
    return (lg(c['gc_fr'], t['gc_fr']) + lg(max(ratio, 1e-3), t['gzn_ratio']) + lg(c['fs_fr'], t['fs_fr'])
            + ab(c['gc_rw'], t['gc_rw']) + ab(c['gc_rb'], t['gc_rb'])
            + ab(g['gc_rw'], t['gzn_rw']) + ab(g['gc_rb'], t['gzn_rb']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunk', type=int, default=0)
    ap.add_argument('--n-chunks', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=16)
    ap.add_argument('--n-repeats', type=int, default=10)
    ap.add_argument('--collect', action='store_true')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.collect:
        rows = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, 'pt_*.json')))]
        rows.sort(key=lambda r: r['loss'])
        json.dump(rows, open(os.path.join(HERE, 'results', 'grid_v3_all.json'), 'w'), indent=1)
        print(f'{len(rows)} punktów; 10 najlepszych:')
        for r in rows[:10]:
            c, g = r['control'], r['gabazine']
            print(f"  loss {r['loss']:.3f} | W_volley {r['W_volley']:5.1f} W_FS_GC {r['W_FS_GC']:4.1f} p_rel {r['p_rel']:.1f} W_GC_FS {r['W_GC_FS']:4.1f} W_PP_FS {r.get('W_PP_FS', 0.25):4.2f} W_FS_FS {r.get('W_FS_FS', 0.0):3.1f} | "
                  f"GC {c['gc_fr']:.2f} Hz Rw {c['gc_rw']:.2f} Rb {c['gc_rb']:.2f} | gzn ×{g['gc_fr'] / max(c['gc_fr'], 1e-3):.2f} "
                  f"Rw {g['gc_rw']:.2f} Rb {g['gc_rb']:.2f} | FS {c['fs_fr']:.1f} Hz | lat GC {c.get('gc_lat_ms', float('nan')):.1f} FS {c.get('fs_lat_ms', float('nan')):.1f} ms")
        return

    stim = M.read_protocol(M._index()[PROTOCOL])
    K = k_for_vrest(V_REST_TARGET)
    base = DGConfig(K_GC=K)
    pts = list(itertools.product(GRID['W_volley'], GRID['W_FS_GC'], GRID['p_rel'], GRID['W_GC_FS'], GRID['W_PP_FS'], GRID['W_FS_FS']))
    mine = pts[a.chunk::a.n_chunks]
    print(f'K_GC = {K:.2f} (V_rest {V_REST_TARGET} mV); punktów w tym fragmencie: {len(mine)} z {len(pts)}', flush=True)
    for (Wv, Wfs, p, Wgf, Wpf, Wff) in mine:
        fn = os.path.join(OUT, f'pt_W{Wv}_fs{Wfs}_p{p}_gf{Wgf}_pf{Wpf}_ff{Wff}.json')
        if os.path.exists(fn):
            continue
        t0 = time.time()
        res = {}
        for name, block in (('control', 0.0), ('gabazine', 0.3)):
            cfg = exvivo_config(base, Wv, p, W_FS_GC=Wfs, W_GC_FS=Wgf, W_PP_FS=Wpf, W_FS_FS=Wff, gabazine_block=block)
            conn = make_connectivity(cfg, seed=0)
            run = run_protocol(cfg, conn, stim, n_repeats=a.n_repeats, seed=0, jobs=a.jobs)
            res[name] = summarize(run, stim)
        rec = {'W_volley': Wv, 'W_FS_GC': Wfs, 'p_rel': p, 'W_GC_FS': Wgf, 'W_PP_FS': Wpf, 'W_FS_FS': Wff, 'K_GC': K, **res,
               'loss': loss(res['control'], res['gabazine']), 'elapsed_s': time.time() - t0}
        json.dump(rec, open(fn, 'w'))
        c, g = res['control'], res['gabazine']
        print(f"W_volley {Wv} W_FS_GC {Wfs} p_rel {p} W_GC_FS {Wgf} W_PP_FS {Wpf}: GC {c['gc_fr']:.2f} Hz Rw {c['gc_rw']:.2f} Rb {c['gc_rb']:.2f} | "
              f"gzn {g['gc_fr']:.2f} Hz | FS {c['fs_fr']:.1f} | loss {rec['loss']:.3f} ({rec['elapsed_s']:.0f}s)", flush=True)


if __name__ == '__main__':
    main()
