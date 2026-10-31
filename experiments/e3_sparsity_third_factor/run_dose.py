"""
E3.5 — czy obalenie H-E3c jest odporne? Krzywa dawka–odpowiedź po sile modulacji g
w różnych architekturach (prereg.md sek. 6b, kryterium zapisane przed uruchomieniem).

Siła modulacji g ∈ [−1, 1], wokół środka f_c = √(f_gęsty · f_rzadki):
    f_spoczynek = f_c · r^{g/2},  f_nowość = f_c · r^{−g/2},  r = f_gęsty / f_rzadki
  g = +1  → dokładnie `mod_novelty` z E3.3 (nowość → rzadziej)
  g = −1  → dokładnie `mod_novelty_inv` (nowość → gęściej)
  g =  0  → stały kod przy f_c
Dla każdego g ≠ 0 liczymy też kontrolę: stały kod przy średnim f zrealizowanym przez
modulację (null o dopasowanej rzadkości). Efekt: Δ(g) = BWT(mod g) − BWT(stałe f g).

Regulator (sygnał, a, b, τ) i η czytnika — z hparams.json (ziarno 99, architektura
domyślna), bez ponownego strojenia dla innych architektur.

Wyjście: results/e35/{neuron}{arch}_{rule}_s{seed}_o{order}.json
Użycie:  python run_dose.py --neuron izh --rule rgate --n-dg 500 --fan-in 30 --seed 0 --order-seed 0
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time

import numpy as np

from learning import Controller, Readout
from run_split import CODES, HP_FILE, RES, nearest_by_f
from tasks import TASKS, load_mnist, task_stream

GAINS = [-1.0, -0.5, 0.5, 1.0]


def train(codes, n_tr, ytr, yte, stream, rule, eta, seed, level_fn, ctrl, f_mean, eval_level):
    ro = Readout(codes.shape[2], rule, eta, seed)
    test_task = [np.where(np.isin(yte, t))[0] for t in TASKS]
    acc = np.full((len(TASKS), len(TASKS)), np.nan)
    used = []
    C_eval = np.asarray(codes[n_tr:, eval_level, :], np.float32)
    for t, seq in stream:
        for i in seq:
            l = level_fn()
            _, R, s = ro.step(np.asarray(codes[i, l, :], np.float32), int(ytr[i]))
            if ctrl is not None:
                ctrl.update(s, R)
            used.append(l)
        pred = ro.predict(C_eval)
        acc[t, :t + 1] = [float((pred[idx] == yte[idx]).mean()) for idx in test_task][:t + 1]
    T = len(TASKS) - 1
    return {'ACC': float(np.nanmean(acc[T])),
            'BWT': float(np.mean([acc[T, j] - acc[j, j] for j in range(T)])),
            'mean_level_f': float(np.mean([f_mean[l] for l in used])),
            'eval_level_f': float(f_mean[eval_level]), 'acc': acc.tolist()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--rule', choices=['rstdp', 'delta', 'rgate'], required=True)
    ap.add_argument('--n-dg', type=int, default=2000)
    ap.add_argument('--fan-in', type=int, default=30)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()

    arch = '' if (a.n_dg, a.fan_in) == (2000, 30) else f'_n{a.n_dg}_k{a.fan_in}'
    with open(HP_FILE) as f:
        hp = json.load(f)
    h = hp[a.neuron][a.rule]
    ch = {k: v for k, v in hp['controller'][f'{a.neuron}_{a.rule}'].items() if k in ('signal', 'a', 'b', 'tau')}
    ch.setdefault('tau', hp.get('tau', 50.0))
    path = os.path.join(CODES, f'{a.neuron}{arch}_s{a.seed}.npy')
    with open(path.replace('.npy', '.json')) as f:
        meta = json.load(f)
    codes = np.load(path, mmap_mode='r')
    n_tr = meta['n_train']
    f_mean = meta['f_train_mean']
    _, ytr, _, yte = load_mnist(normalize=False)
    seed = 1000 * a.seed + a.order_seed
    stream = task_stream(ytr, seed, hp.get('epochs_per_task', 1))

    f_c = math.sqrt(h['f_dense'] * h['f_sparse'])
    r = h['f_dense'] / h['f_sparse']
    results = []
    l_c = nearest_by_f(f_mean, f_c)
    res = train(codes, n_tr, ytr, yte, stream, a.rule, h['eta'], seed, lambda: l_c, None, f_mean, l_c)
    res.update(g=0.0, kind='fixed')
    results.append(res)
    for g in GAINS:
        f_rest, f_novel = f_c * r ** (g / 2), f_c * r ** (-g / 2)
        ctrl = Controller(f_mean, f_rest, f_novel, **ch)
        mod = train(codes, n_tr, ytr, yte, stream, a.rule, h['eta'], seed, ctrl.level, ctrl, f_mean,
                    nearest_by_f(f_mean, f_rest))
        mod.update(g=g, kind='mod', f_rest=f_rest, f_novel=f_novel)
        lm = nearest_by_f(f_mean, mod['mean_level_f'])
        fix = train(codes, n_tr, ytr, yte, stream, a.rule, h['eta'], seed, lambda: lm, None, f_mean, lm)
        fix.update(g=g, kind='matched')
        results += [mod, fix]
        print(f'  g={g:+.1f}  mod BWT={mod["BWT"]:+.3f} (f {mod["mean_level_f"]:.3f})  '
              f'matched BWT={fix["BWT"]:+.3f} (f {fix["mean_level_f"]:.3f})  Δ={mod["BWT"] - fix["BWT"]:+.3f}', flush=True)

    os.makedirs(os.path.join(RES, 'e35'), exist_ok=True)
    fn = os.path.join(RES, 'e35', f'{a.neuron}{arch}_{a.rule}_s{a.seed}_o{a.order_seed}.json')
    with open(fn, 'w') as f:
        json.dump({'neuron': a.neuron, 'rule': a.rule, 'n_dg': a.n_dg, 'fan_in': a.fan_in,
                   'seed': a.seed, 'order_seed': a.order_seed, 'f_c': f_c, 'r': r,
                   'controller': ch, 'eta': h['eta'], 'results': results,
                   'elapsed_s': time.time() - t0}, f)
    print('saved', fn, f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
