"""
E3.4 — rozdzielenie kodu i reguły czytnika (README sek. 14, dodane 2026-10-13).

Pytanie: dlaczego FlyModel (k-WTA + reguła „tylko klasa docelowa”) zapomina prawie
nic, a nasze warunki dużo — przez kod czy przez regułę uczenia?

Układ 2 × 3 na Split-MNIST (ten sam strumień zadań co E3.3), stałe f = 5%:
  kod:    kwta — k-WTA na napędzie (FlyModel, bez impulsów)
          dg5  — kod impulsowy warstwy DG przy poziomie f najbliższym 5%
          dg5n — ten sam kod DG znormalizowany per obraz (c/‖c‖; dodane 2026-10-22):
                 czy wyrównanie aktywności między obrazami wystarcza, by DG ≈ k-WTA?
  reguła: fly   — w[:, y] += β·φ (tylko wzmacnianie klasy docelowej)
          rstdp — reguła trójczynnikowa z R − R̄ (osłabia inne klasy)
          delta — reguła delta (osłabia inne klasy)
η reguł rstdp/delta z hparams.json (strojone na ziarnie 99), β FlyModelu jak w E3.3.
Warunek kwta × fly to dokładnie `kwta_fly` z E3.3 (kontrola zgodności).

Wyjście: results/e34/{neuron}_s{seed}_o{order}.json
Użycie:  python run_factorial.py --neuron izh --seed 0 --order-seed 0
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from learning import Readout, kwta_codes
from model import LayerCfg, live_pixels, make_connectivity
from run_split import CODES, HP_FILE, RES, nearest_by_f
from tasks import TASKS, load_mnist, task_stream

F_FIXED = 0.05


def run_condition(Ctr, Cte, ytr, yte, stream, rule, eta, seed):
    ro = Readout(Ctr.shape[1], rule, eta, seed)
    test_task = [np.where(np.isin(yte, t))[0] for t in TASKS]
    acc = np.full((len(TASKS), len(TASKS)), np.nan)
    for t, seq in stream:
        for i in seq:
            ro.step(Ctr[i], int(ytr[i]))
        pred = ro.predict(Cte)
        acc[t, :t + 1] = [float((pred[idx] == yte[idx]).mean()) for idx in test_task][:t + 1]
    T = len(TASKS) - 1
    return {'acc': acc.tolist(), 'ACC': float(np.nanmean(acc[T])),
            'BWT': float(np.mean([acc[T, j] - acc[j, j] for j in range(T)])),
            'f_measured': float((Ctr > 0).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()

    with open(HP_FILE) as f:
        hp = json.load(f)
    Xtr, ytr, Xte, yte = load_mnist()
    seed = 1000 * a.seed + a.order_seed
    stream = task_stream(ytr, seed, hp.get('epochs_per_task', 1))

    M = make_connectivity(LayerCfg(), live_pixels(Xtr), a.seed)['M']
    codes = {'kwta': (kwta_codes(Xtr, M, F_FIXED), kwta_codes(Xte, M, F_FIXED))}
    path = os.path.join(CODES, f'{a.neuron}_s{a.seed}.npy')
    with open(path.replace('.npy', '.json')) as f:
        meta = json.load(f)
    l5 = nearest_by_f(meta['f_train_mean'], F_FIXED)
    mm = np.load(path, mmap_mode='r')
    n_tr = meta['n_train']
    codes['dg5'] = (np.asarray(mm[:n_tr, l5, :], np.float32), np.asarray(mm[n_tr:, l5, :], np.float32))
    l2 = lambda C: C / np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-9)
    codes['dg5n'] = (l2(codes['dg5'][0]), l2(codes['dg5'][1]))

    etas = {'fly': hp.get('fly_eta', 0.01), 'rstdp': hp[a.neuron]['rstdp']['eta'],
            'delta': hp[a.neuron]['delta']['eta']}
    results = []
    for code, (Ctr, Cte) in codes.items():
        for rule, eta in etas.items():
            r = run_condition(Ctr, Cte, ytr, yte, stream, rule, eta, seed)
            r.update(code=code, rule=rule, eta=eta)
            results.append(r)
            print(f'  {code:5s} × {rule:6s} ACC={r["ACC"]:.3f} BWT={r["BWT"]:+.3f} f={r["f_measured"]:.3f}', flush=True)

    os.makedirs(os.path.join(RES, 'e34'), exist_ok=True)
    fn = os.path.join(RES, 'e34', f'{a.neuron}_s{a.seed}_o{a.order_seed}.json')
    with open(fn, 'w') as f:
        json.dump({'neuron': a.neuron, 'seed': a.seed, 'order_seed': a.order_seed,
                   'f_fixed': F_FIXED, 'dg_level_f': meta['f_train_mean'][l5],
                   'results': results, 'elapsed_s': time.time() - t0}, f)
    print('saved', fn, f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
