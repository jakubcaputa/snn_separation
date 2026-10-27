"""
Przewidywanie modelu dla eksperymentu z gabazyną (Ola, Kinga) — zapisywane PRZED analizą
ich danych (2026-10-27). Model: najlepszy punkt siatki v4 (results/grid_v4_all.json).

Założenia (do potwierdzenia z zespołem prof. Błasiak): protokół wejściowy jak u Madara
(pociągi 10 Hz, 2 s, 5 pociągów), gabazyna = −30% hamowania fazowego FS→GC (oraz, jeśli
najlepszy punkt v4 tego wymaga, częściowy blok hamowania tonicznego), 5 powtórzeń każdego
pociągu (ich protokół) i 10 (Madar). Każdy GC modelu odpowiadający na salwy (> 0.2 Hz
w kontroli) = jedna „nagrana komórka”; para kontrola/gabazyna = ta sama komórka.

Miary per komórka: częstotliwość, skłonność do burstów (odsetek salw z odpowiedzią, po których
komórka daje ≥ 2 impulsy w 15 ms), R_w, R_b (biny 10/20/50 ms), separacja R_in − R_b.

Wyjście: results/prediction_gabazine.json, PREDICTION_gabazine.md.
Użycie (z experiments/):  python -m calib_exvivo.predict_gabazine --jobs 16
"""
from __future__ import annotations

import argparse
import datetime
import json
import os

import numpy as np

from calib_exvivo.grid import k_for_vrest
from calib_exvivo.grid_v4 import cfg_for
from dg_core import io_madar as M
from dg_core import make_connectivity
from dg_core.exvivo import run_protocol

HERE = os.path.dirname(os.path.abspath(__file__))
PROTOCOLS = {0.50: '10Hz_R0.500_CorrelatedPoisson.prt.axgx', 0.75: '10Hz_R0.750_CorrelatedPoisson.prt.axgx',
             0.95: '10Hz_R0.950_CorrelatedPoisson.prt.axgx'}
NET_SEEDS = [0, 1, 2]
BINS = [0.010, 0.020, 0.050]


def burst_propensity(cell_sweeps, stim, win=0.015):
    resp = burst = 0
    for k, t in enumerate(cell_sweeps):
        t = np.asarray(t)
        for p in stim[k % len(stim)]:
            n = int(((t >= p) & (t < p + win)).sum())
            resp += n >= 1
            burst += n >= 2
    return burst / resp if resp else np.nan


def cell_metrics(run, stim, n_rep):
    out = []
    for cell in run['gc']:
        fr = sum(len(t) for t in cell) / (len(cell) * 2.0)
        m = {'fr': fr, 'burst': burst_propensity(cell, stim)}
        for b in BINS:
            s = M.similarity(stim, cell, b, n_repeats_used=n_rep)
            m[f'Rw_{int(b * 1000)}'] = s['R_w']
            m[f'Rb_{int(b * 1000)}'] = s['R_b']
            m[f'sep_{int(b * 1000)}'] = s['R_in'] - s['R_b']
        out.append(m)
    return out


def q(v):
    v = np.asarray([x for x in v if np.isfinite(x)])
    return [float(np.percentile(v, 25)), float(np.median(v)), float(np.percentile(v, 75)), int(len(v))] if len(v) else [np.nan] * 3 + [0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', type=int, default=16)
    a = ap.parse_args()
    best = json.load(open(os.path.join(HERE, 'results', 'grid_v4_all.json')))[0]
    K = k_for_vrest(-76.0)
    res = {'model': {k: best[k] for k in ('tau_in_gc', 'K_GC_sd', 'gabazine_tonic', 'W_FS_GC', 'loss')},
           'date': datetime.date.today().isoformat(), 'protocols': {}}
    for rin, fn in PROTOCOLS.items():
        stim = M.read_protocol(M._index()[fn])
        per = {f'rep{n}': {'control': [], 'gabazine': []} for n in (5, 10)}
        for seed in NET_SEEDS:
            runs = {}
            for name, gzn in (('control', False), ('gabazine', True)):
                cfg = cfg_for(K, best['tau_in_gc'], best['K_GC_sd'], best['W_FS_GC'], gzn, best['gabazine_tonic'])
                runs[name] = run_protocol(cfg, make_connectivity(cfg, seed=seed), stim, n_repeats=10, seed=seed, jobs=a.jobs)
            for n in (5, 10):
                mc, mg = cell_metrics(runs['control'], stim, n), cell_metrics(runs['gabazine'], stim, n)
                keep = [i for i, m in enumerate(mc) if m['fr'] > 0.2]
                per[f'rep{n}']['control'] += [mc[i] for i in keep]
                per[f'rep{n}']['gabazine'] += [mg[i] for i in keep]
        summ = {}
        for rep, d in per.items():
            s = {}
            for key in d['control'][0]:
                c = [m[key] for m in d['control']]
                g = [m[key] for m in d['gabazine']]
                ratio = [gg / cc for cc, gg in zip(c, g) if np.isfinite(cc) and np.isfinite(gg) and cc > 0] if key == 'fr' else None
                diff = [gg - cc for cc, gg in zip(c, g) if np.isfinite(cc) and np.isfinite(gg)]
                s[key] = {'control': q(c), 'gabazine': q(g), 'paired_diff': q(diff)}
                if ratio is not None:
                    s[key]['paired_ratio'] = q(ratio)
            summ[rep] = s
        res['protocols'][str(rin)] = summ
        print(f'R_in {rin}: FR ×{summ["rep5"]["fr"]["paired_ratio"][1]:.2f}, '
              f'Rw10 {summ["rep5"]["Rw_10"]["control"][1]:.2f}→{summ["rep5"]["Rw_10"]["gabazine"][1]:.2f}, '
              f'Rb10 {summ["rep5"]["Rb_10"]["control"][1]:.2f}→{summ["rep5"]["Rb_10"]["gabazine"][1]:.2f}', flush=True)
    json.dump(res, open(os.path.join(HERE, 'results', 'prediction_gabazine.json'), 'w'), indent=1)

    L = [f'# Przewidywanie modelu: gabazyna (zapisane {res["date"]}, przed analizą danych Oli i Kingi)', '',
         'Model: `dg_core` w reżimie skrawka (salwy, `exvivo_best_config` + najlepszy punkt siatki v4: '
         f'τ_IPSC {best["tau_in_gc"]:.0f} ms, zróżnicowanie K_GC (SD) {best["K_GC_sd"]}, '
         f'blok tonicznego {best["gabazine_tonic"]}, W_FS_GC {best["W_FS_GC"]}). Gabazyna = −30% hamowania fazowego FS→GC'
         + (f' i −{int(best["gabazine_tonic"] * 100)}% tonicznego.' if best['gabazine_tonic'] else '.'),
         f'Komórki: GC modelu odpowiadające na salwy, 3 sieci; pary kontrola/gabazyna = ta sama komórka.',
         'Założenia do potwierdzenia: protokół wejściowy jak u Madara (P10Hz, 5 pociągów po 2 s); '
         'stężenie i działanie gabazyny jak u Madara (100 nM).', '',
         'Mediana [IQR] po komórkach; „zmiana” = różnica parami (gabazyna − kontrola), ×FR = iloraz parami.', '']
    for rin, summ in res['protocols'].items():
        for rep in ('rep5', 'rep10'):
            s = summ[rep]
            L += [f'## R_in = {rin}, {rep[3:]} powtórzeń', '',
                  '| miara | kontrola | gabazyna | zmiana parami |', '|---|---|---|---|']
            for key, lab in (('fr', 'częstotliwość [Hz]'), ('burst', 'skłonność do burstów'),
                             ('Rw_10', 'R_w (10 ms)'), ('Rb_10', 'R_b (10 ms)'), ('sep_10', 'separacja R_in − R_b (10 ms)'),
                             ('Rw_20', 'R_w (20 ms)'), ('Rb_20', 'R_b (20 ms)'), ('Rw_50', 'R_w (50 ms)'), ('Rb_50', 'R_b (50 ms)')):
                c, g, d = s[key]['control'], s[key]['gabazine'], s[key]['paired_diff']
                extra = f' (×{s[key]["paired_ratio"][1]:.2f})' if key == 'fr' else ''
                L.append(f'| {lab} | {c[1]:.2f} [{c[0]:.2f}–{c[2]:.2f}] | {g[1]:.2f} [{g[0]:.2f}–{g[2]:.2f}] | '
                         f'{d[1]:+.3f} [{d[0]:+.3f}–{d[2]:+.3f}]{extra} |')
            L.append('')
    s = res['protocols']['0.75']['rep5']
    sign = lambda x: 'rośnie' if x > 0 else 'maleje'
    L += ['## Przewidywania do sprawdzenia (R_in = 0.75, 5 powtórzeń, bin 10 ms)', '',
          f'1. Częstotliwość GC {sign(s["fr"]["paired_diff"][1])} (mediana ×{s["fr"]["paired_ratio"][1]:.2f}).',
          (f'2. Skłonność do burstów {sign(s["burst"]["paired_diff"][1])} ({s["burst"]["control"][1]:.2f} → {s["burst"]["gabazine"][1]:.2f}).'
           if max(s['burst']['control'][2], s['burst']['gabazine'][2]) > 0 else
           '2. Skłonność do burstów — brak przewidywania: GC modelu nie dają burstów.'),
          f'3. R_w {sign(s["Rw_10"]["paired_diff"][1])} ({s["Rw_10"]["control"][1]:.2f} → {s["Rw_10"]["gabazine"][1]:.2f}).',
          f'4. R_b {sign(s["Rb_10"]["paired_diff"][1])} ({s["Rb_10"]["control"][1]:.2f} → {s["Rb_10"]["gabazine"][1]:.2f}).',
          f'5. Separacja R_in − R_b {sign(s["sep_10"]["paired_diff"][1])} — '
          + ('gorsza separacja po gabazynie, jak u Madara.' if s['sep_10']['paired_diff'][1] < 0 else 'lepsza separacja — niezgodne z Madarem.'),
          '', 'Dane Madara dla porównania (100 nM, n = 7, bin 10 ms): ×FR 1.6 [1.3–11], R_w 0.49 → 0.80, '
          'R_b 0.29 → 0.55 (`results/madar_targets.md`).', '',
          'Ograniczenie: kalibracja v4 — patrz `README.md`; jeśli model nie odtwarza wielkości efektu, '
          'przewidywania dotyczą kierunków, nie wartości.']
    open(os.path.join(HERE, 'PREDICTION_gabazine.md'), 'w').write('\n'.join(L))
    print('zapisano PREDICTION_gabazine.md')


if __name__ == '__main__':
    main()
