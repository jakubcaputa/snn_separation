"""
Kalibracja ex vivo, siatka v4 (2026-10-27): czy model odtwarza efekt gabazyny?

v3 trafiła kontrolę (GC 3.0 Hz, R_w 0.37, R_b 0.28, FS 9.6 Hz, FS przed GC), ale −30% FS→GC
dawało ×1.25 zamiast ×1.6. Trzy kandydackie wyjaśnienia, jako osie wokół najlepszego punktu v3
(W_salwy 20, W_PP_FS 0.5, p_rel 0.6, W_GC_FS ≈ 0, W_FS_FS 1):
  tau_in_gc       — stała czasowa IPSC na GC: 8 (dotąd), 15, 25 ms
  K_GC_sd         — zróżnicowanie pobudliwości GC (K per neuron): 0, 2.5, 5
                    (w danych V_rest −81…−70 mV ⇔ K ≈ 0…13.6)
  gabazine_tonic  — gabazyna obniża też hamowanie toniczne: 0 (tylko fazowe), 0.3
  W_FS_GC         — 2, 4
Dla zróżnicowanych GC liczymy też rozkład ×FR po komórkach (w danych ×1.3–11, mediana 1.6).

Użycie (z experiments/):
  python -m calib_exvivo.grid_v4 --chunk 0 --n-chunks 2 --jobs 16
  python -m calib_exvivo.grid_v4 --collect
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import time

import numpy as np

from calib_exvivo.grid import PROTOCOL, k_for_vrest, loss, summarize
from dg_core import DGConfig, make_connectivity
from dg_core import io_madar as M
from dg_core.exvivo import EXVIVO_BEST, exvivo_config, run_protocol

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results', 'grid_v4')
GRID = {'tau_in_gc': [8.0, 15.0, 25.0], 'K_GC_sd': [0.0, 2.5, 5.0],
        'gabazine_tonic': [0.0, 0.3], 'W_FS_GC': [2.0, 4.0]}


def cfg_for(K, tau, ksd, wfs, gzn, gzn_tonic):
    b = dict(EXVIVO_BEST)
    b['W_FS_GC'] = wfs
    Wv, p = b.pop('W_volley'), b.pop('p_rel')
    return exvivo_config(DGConfig(K_GC=K, tau_in_gc=tau, K_GC_sd=ksd), Wv, p,
                         gabazine_block=0.3 if gzn else 0.0,
                         gabazine_tonic_block=gzn_tonic if gzn else 0.0, **b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunk', type=int, default=0)
    ap.add_argument('--n-chunks', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=16)
    ap.add_argument('--collect', action='store_true')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.collect:
        rows = sorted([json.load(open(f)) for f in glob.glob(os.path.join(OUT, 'pt_*.json'))], key=lambda r: r['loss'])
        json.dump(rows, open(os.path.join(HERE, 'results', 'grid_v4_all.json'), 'w'), indent=1)
        print(f'{len(rows)} punktów; najlepsze:')
        for r in rows[:10]:
            c, g = r['control'], r['gabazine']
            print(f"  loss {r['loss']:.3f} | τ_in {r['tau_in_gc']:4.0f} K_sd {r['K_GC_sd']:3.1f} gzn_ton {r['gabazine_tonic']:.1f} "
                  f"W_FS_GC {r['W_FS_GC']:.0f} | GC {c['gc_fr']:.2f} Hz Rw {c['gc_rw']:.2f} Rb {c['gc_rb']:.2f} FS {c['fs_fr']:.1f} | "
                  f"gzn ×{r['ratio_median']:.2f} [{r['ratio_q25']:.2f}–{r['ratio_q75']:.2f}] Rw {g['gc_rw']:.2f} Rb {g['gc_rb']:.2f}")
        return
    stim = M.read_protocol(M._index()[PROTOCOL])
    K = k_for_vrest(-76.0)
    pts = list(itertools.product(GRID['tau_in_gc'], GRID['K_GC_sd'], GRID['gabazine_tonic'], GRID['W_FS_GC']))
    for (tau, ksd, gt, wfs) in pts[a.chunk::a.n_chunks]:
        fn = os.path.join(OUT, f'pt_tau{tau}_ksd{ksd}_gt{gt}_fs{wfs}.json')
        if os.path.exists(fn):
            continue
        t0 = time.time()
        res, fr = {}, {}
        for name, gzn in (('control', False), ('gabazine', True)):
            cfg = cfg_for(K, tau, ksd, wfs, gzn, gt)
            conn = make_connectivity(cfg, seed=0)
            run = run_protocol(cfg, conn, stim, n_repeats=10, seed=0, jobs=a.jobs)
            res[name] = summarize(run, stim)
            fr[name] = np.array([sum(len(t) for t in cell) / (len(cell) * 2.0) for cell in run['gc']])
        ok = fr['control'] > 0.2           # komórki, które w ogóle odpowiadają (jak nagrywane w danych)
        ratio = fr['gabazine'][ok] / fr['control'][ok] if ok.any() else np.array([np.nan])
        rec = {'tau_in_gc': tau, 'K_GC_sd': ksd, 'gabazine_tonic': gt, 'W_FS_GC': wfs, 'K_GC': K, **res,
               'ratio_median': float(np.median(ratio)), 'ratio_q25': float(np.percentile(ratio, 25)),
               'ratio_q75': float(np.percentile(ratio, 75)), 'frac_responsive': float(ok.mean())}
        # strata jak w v3, ale ×FR liczony per komórka (mediana), nie z median częstotliwości
        g_eff = dict(res['gabazine'])
        g_eff['gc_fr'] = rec['ratio_median'] * res['control']['gc_fr']
        rec['loss'] = loss(res['control'], g_eff)
        rec['elapsed_s'] = time.time() - t0
        json.dump(rec, open(fn, 'w'))
        print(f"τ_in {tau} K_sd {ksd} gzn_ton {gt} W_FS_GC {wfs}: GC {res['control']['gc_fr']:.2f} Hz "
              f"×{rec['ratio_median']:.2f} Rw {res['control']['gc_rw']:.2f}→{res['gabazine']['gc_rw']:.2f} "
              f"FS {res['control']['fs_fr']:.1f} | loss {rec['loss']:.3f} ({rec['elapsed_s']:.0f}s)", flush=True)


if __name__ == '__main__':
    main()
