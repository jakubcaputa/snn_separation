"""
E3.1 i E3.2 — uczenie na całym MNIST (bez podziału na zadania), stały kod.

E3.1 (H-E3a): dla każdego poziomu f z F_LEVELS:
  kod DG (impulsy) — czytniki rstdp, delta (1 epoka, online) + sufit (regresja logistyczna);
  null: losowa projekcja Gaussa z globalnym progiem dającym to samo średnie f;
  miara dekorelacji dec = r_in − r_out na tych samych parach obrazów testowych.
  Raz: surowe piksele (rstdp, delta, sufit).
E3.2 (H-E3b): kody z pulą FS, W_FS_GC ∈ PHASIC_W, f ∈ {5, 20%} (K skalibrowane dla
  każdego W osobno) — te same czytniki.

Wyjście: results/e31/{neuron}_s{seed}_o{order}.json, results/e32/... .

Użycie:
  python run_static.py --exp e31 --neuron izh --seed 0 --order-seed 0 --jobs 16
  python run_static.py --exp e32 --neuron izh --seed 0 --order-seed 0 --jobs 10
  python run_static.py --exp tune --neuron izh --seed 99          # strojenie η na walidacji
"""
from __future__ import annotations

import argparse
import json
import os
import time
from multiprocessing import Pool

import numpy as np

from learning import Readout, logistic_ceiling, pearson_mean
from tasks import load_mnist

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
CODES = os.path.join(RES, 'codes')
HP_FILE = os.path.join(HERE, 'hparams.json')

N_PAIRS = 2000


def load_hparams(neuron: str):
    """η czytników dla danego typu neuronu (z hparams.json po strojeniu na ziarnie 99)."""
    hp = {'eta': {'rstdp': 0.5, 'delta': 0.05}, 'eps': 0.02}
    if os.path.exists(HP_FILE):
        with open(HP_FILE) as f:
            full = json.load(f)
        hp['eps'] = full.get('eps', 0.02)
        for rule in ('rstdp', 'delta'):
            hp['eta'][rule] = full[neuron][rule]['eta']
    return hp


def train_online(code_tr, ytr, order, rule, eta, seed, eps=0.02):
    ro = Readout(code_tr.shape[1], rule, eta, seed, eps)
    for i in order:
        ro.step(code_tr[i], int(ytr[i]))
    return ro


def pairs(n_test, seed=123):
    rng = np.random.default_rng(seed)
    a = rng.integers(0, n_test, N_PAIRS)
    b = rng.integers(0, n_test, N_PAIRS)
    keep = a != b
    return a[keep], b[keep]


def evaluate_code(code_tr, code_te, ytr, yte, Xte, order, hp, seed, with_ceiling=True):
    out = {'f_train': float((code_tr > 0).mean()), 'f_test': float((code_te > 0).mean())}
    for rule in ('rstdp', 'delta'):
        ro = train_online(code_tr, ytr, order, rule, hp['eta'][rule], seed, hp.get('eps', 0.02))
        out[f'acc_{rule}'] = float((ro.predict(code_te) == yte).mean())
    if with_ceiling:
        out['acc_logistic'] = logistic_ceiling(code_tr, ytr, code_te, yte, seed=seed)
    a, b = pairs(len(code_te))
    out['r_in'] = pearson_mean(Xte[a], Xte[b])
    out['r_out'] = pearson_mean(code_te[a], code_te[b])
    out['dec'] = out['r_in'] - out['r_out']
    same = yte[a] == yte[b]
    out['dec_same_class'] = pearson_mean(Xte[a[same]], Xte[b[same]]) - pearson_mean(code_te[a[same]], code_te[b[same]])
    return out


# ── zadania dla puli procesów (każdy proces czyta swój wycinek z memmap) ──────
def _level_job(args):
    import torch
    torch.set_num_threads(1)
    path, l, n_tr, ytr, yte, Xtr, Xte, order, hp, seed, f_target, rp_seed = args
    codes = np.load(path, mmap_mode='r')
    code = np.asarray(codes[:, l, :], dtype=np.float32)
    rec = {'level': l, 'f_target': f_target, 'code': 'dg'}
    rec.update(evaluate_code(code[:n_tr], code[n_tr:], ytr, yte, Xte, order, hp, seed))
    # null: losowa projekcja Gaussa, globalny próg dający to samo średnie f co DG
    rng = np.random.default_rng(rp_seed)
    G = rng.standard_normal((784, code.shape[1])).astype(np.float32)
    ztr, zte = Xtr @ G, Xte @ G
    theta = np.quantile(ztr[::10], 1.0 - rec['f_train'])
    rtr, rte = np.maximum(ztr - theta, 0), np.maximum(zte - theta, 0)
    rp = {'level': l, 'f_target': f_target, 'code': 'random_projection'}
    rp.update(evaluate_code(rtr, rte, ytr, yte, Xte, order, hp, seed))
    return [rec, rp]


def _pixels_job(args):
    import torch
    torch.set_num_threads(1)
    ytr, yte, Xtr, Xte, order, hp, seed = args
    rec = {'level': None, 'f_target': None, 'code': 'pixels'}
    rec.update(evaluate_code(Xtr, Xte, ytr, yte, Xte, order, hp, seed))
    return [rec]


def _phasic_job(args):
    import torch
    torch.set_num_threads(1)
    path, wi, fi, W, f, n_tr, ytr, yte, Xte, order, hp, seed = args
    codes = np.load(path, mmap_mode='r')
    code = np.asarray(codes[:, wi, fi, :], dtype=np.float32)
    rec = {'W_FS_GC': W, 'f_target': f}
    rec.update(evaluate_code(code[:n_tr], code[n_tr:], ytr, yte, Xte, order, hp, seed))
    return [rec]


def _tune_job(args):
    path, l, n_tr, ytr, order, rule, eta = args
    codes = np.load(path, mmap_mode='r')
    code = np.asarray(codes[:n_tr, l, :], dtype=np.float32)
    n_fit = n_tr - 10_000                     # ostatnie 10k obrazów treningowych = walidacja
    fit = order[order < n_fit]
    ro = train_online(code[:n_fit], ytr[:n_fit], fit, rule, eta, 0)
    acc = float((ro.predict(code[n_fit:]) == ytr[n_fit:n_tr]).mean())
    return {'level': l, 'rule': rule, 'eta': eta, 'val_acc': acc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exp', choices=['e31', 'e32', 'tune'], required=True)
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--quick', action='store_true', help='kody z presetu quick')
    ap.add_argument('--codes-tag', default='', help='2026-10-29: kody {neuron}_s{seed}_{tag}.npy (np. hi = f 70/90%%) → results/e31_{tag}/')
    a = ap.parse_args()

    q = (f'_{a.codes_tag}' if a.codes_tag else '') + ('_quick' if a.quick else '')
    Xtr, ytr, Xte, yte = load_mnist()
    hp = load_hparams(a.neuron)
    seed = 1000 * a.seed + a.order_seed
    t0 = time.time()

    if a.exp in ('e31', 'tune'):
        path = os.path.join(CODES, f'{a.neuron}_s{a.seed}{q}.npy')
        with open(path.replace('.npy', '.json')) as f:
            meta = json.load(f)
        n_tr = meta['n_train']
        Xtr, ytr, Xte, yte = Xtr[:n_tr], ytr[:n_tr], Xte[:meta['n_test']], yte[:meta['n_test']]
        order = np.random.default_rng(seed).permutation(n_tr)
        levels = meta['f_levels']

    if a.exp == 'tune':
        jobs = [(path, l, n_tr, ytr, order, rule, eta)
                for l in range(len(levels))
                for rule, etas in (('rstdp', [0.1, 0.25, 0.5, 1.0, 2.0]), ('delta', [0.01, 0.05, 0.2, 0.5]),
                                   ('rgate', [0.01, 0.02, 0.05, 0.1]))
                for eta in etas]
        with Pool(a.jobs) as p:
            recs = p.map(_tune_job, jobs)
        best = {}
        for rule in ('rstdp', 'delta', 'rgate'):
            by_eta = {}
            for r in recs:
                if r['rule'] == rule:
                    by_eta.setdefault(r['eta'], []).append(r['val_acc'])
            best[rule] = max(by_eta, key=lambda e: np.mean(by_eta[e]))
        out = {'neuron': a.neuron, 'seed': a.seed, 'records': recs, 'best_eta': best}
        os.makedirs(os.path.join(RES, 'tune'), exist_ok=True)
        with open(os.path.join(RES, 'tune', f'{a.neuron}_s{a.seed}{q}.json'), 'w') as f:
            json.dump(out, f, indent=1)
        print('best eta:', best, f'{time.time() - t0:.0f}s')
        return

    if a.exp == 'e31':
        jobs = [(path, l, n_tr, ytr, yte, Xtr, Xte, order, hp, seed, levels[l], 7000 + a.seed)
                for l in range(len(levels))]
        with Pool(a.jobs) as p:
            res = p.map(_level_job, jobs) + [_pixels_job((ytr, yte, Xtr, Xte, order, hp, seed))]
        recs = [r for lst in res for r in lst]
    else:
        path = os.path.join(CODES, f'{a.neuron}_s{a.seed}_fs{q}.npy')
        with open(path.replace('.npy', '.json')) as f:
            meta = json.load(f)
        n_tr = meta['n_train']
        Xte, ytr, yte = Xte[:meta['n_test']], ytr[:n_tr], yte[:meta['n_test']]
        order = np.random.default_rng(seed).permutation(n_tr)
        jobs = [(path, wi, fi, W, f, n_tr, ytr, yte, Xte, order, hp, seed)
                for wi, W in enumerate(meta['W_FS_GC']) for fi, f in enumerate(meta['f_levels'])]
        with Pool(a.jobs) as p:
            recs = [r for lst in p.map(_phasic_job, jobs) for r in lst]

    out_dir = os.path.join(RES, a.exp + (f'_{a.codes_tag}' if a.codes_tag else ''))
    os.makedirs(out_dir, exist_ok=True)
    out = {'exp': a.exp, 'neuron': a.neuron, 'seed': a.seed, 'order_seed': a.order_seed,
           'hparams': hp, 'records': recs, 'elapsed_s': time.time() - t0}
    fn = os.path.join(out_dir, f'{a.neuron}_s{a.seed}_o{a.order_seed}{q}.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1)
    print('saved', fn, f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
