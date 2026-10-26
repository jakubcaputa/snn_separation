"""
E3 — kody warstwy DG dla wszystkich obrazów MNIST, liczone RAZ na GPU.

Dlaczego wolno je policzyć z góry: warstwa DG jest stała i nie dostaje niczego
z czytnika, więc jej odpowiedź zależy tylko od obrazu, K i szumu Poissona.
Regulator K wybiera potem jeden z L poziomów (F_LEVELS), a uczenie sekwencyjne
(obraz po obrazie) odczytuje gotowy kod — bez symulowania warstwy w pętli.

Szum: jedna zamrożona realizacja Poissona na obraz, wspólna dla wszystkich
poziomów K (ten sam generator, ten sam batch). Poziomy różnią się więc tylko
progiem.

Wyjście (results/codes/):
  {neuron}_s{seed}.npy           uint8 [70000, L, N]  — 60k train, potem 10k test
  {neuron}_s{seed}.json          K(f), f osiągnięte, konfiguracja, czas
  {neuron}_s{seed}_fs.npy        uint8 [70000, W, 2, N] — E3.2: W_FS_GC × f∈{5,20%}
  {neuron}_s{seed}_fs.json

Użycie:
  python precompute_codes.py --neuron izh --seed 0            # E3.1/E3.3
  python precompute_codes.py --neuron izh --seed 0 --phasic   # E3.2
  python precompute_codes.py --neuron izh --seed 0 --preset quick
"""
from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import replace

import numpy as np
import torch

from calibrate import solve_k_table
from model import (F_LEVELS, DGLayer, LayerCfg, live_pixels, make_connectivity,
                   make_generator, pick_device)
from tasks import calib_indices, load_mnist

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results', 'codes')

PHASIC_W = [0.0, 1.0, 2.0, 3.0, 5.0]
PHASIC_F = [0.05, 0.20]
K_RANGE = (-60.0, 80.0)


def compute(layer, X_all, K, seed, batch, out, tag):
    n = X_all.shape[0]
    t0 = time.time()
    for b, s in enumerate(range(0, n, batch)):
        gen = make_generator(str(layer.dev), seed * 100_000 + b)
        c = layer.run(torch.from_numpy(X_all[s:s + batch]), K, gen).cpu().numpy()
        out[s:s + batch] = c
        if b % 20 == 0:
            el = time.time() - t0
            print(f'  [{tag}] {s + c.shape[0]}/{n}  {el:.0f}s', flush=True)
    return time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--phasic', action='store_true')
    ap.add_argument('--preset', choices=['quick', 'full'], default='full')
    ap.add_argument('--batch', type=int, default=500)
    ap.add_argument('--device', default=None)
    ap.add_argument('--n-dg', type=int, default=2000, help='E3.5: rozmiar warstwy DG')
    ap.add_argument('--fan-in', type=int, default=30, help='E3.5: pikseli na neuron')
    a = ap.parse_args()

    dev = a.device or pick_device()
    Xtr, ytr, Xte, yte = load_mnist()
    if a.preset == 'quick':
        Xtr, ytr, Xte, yte = Xtr[:2000], ytr[:2000], Xte[:500], yte[:500]
    X_all = np.concatenate([Xtr, Xte])
    cfg0 = LayerCfg(neuron=a.neuron, n_dg=a.n_dg, fan_in=a.fan_in)
    conn = make_connectivity(cfg0, live_pixels(Xtr), a.seed)
    X_cal = Xtr[calib_indices(len(Xtr), n=min(1000, len(Xtr)), seed=a.seed)]
    os.makedirs(OUT, exist_ok=True)
    suffix = '_quick' if a.preset == 'quick' else ''
    arch = '' if (a.n_dg, a.fan_in) == (2000, 30) else f'_n{a.n_dg}_k{a.fan_in}'
    print(f'E3 precompute | neuron={a.neuron} seed={a.seed} phasic={a.phasic} '
          f'device={dev} images={len(X_all)}', flush=True)

    if not a.phasic:
        layer = DGLayer(cfg0, conn, dev)
        t0 = time.time()
        K, f_cal = solve_k_table(layer, X_cal, F_LEVELS, *K_RANGE, seed=a.seed, verbose=True)
        t_cal = time.time() - t0
        print('  K(f):', ', '.join(f'{f:.2f}→{k:.2f} ({fc:.3f})' for f, k, fc in zip(F_LEVELS, K, f_cal)), flush=True)
        name = f'{a.neuron}{arch}_s{a.seed}{suffix}'
        out = np.lib.format.open_memmap(os.path.join(OUT, name + '.npy'), mode='w+', dtype=np.uint8,
                                        shape=(len(X_all), len(F_LEVELS), cfg0.n_dg))
        t_run = compute(layer, X_all, K, a.seed, a.batch, out, name)
        f_train = (out[:len(Xtr)] > 0).mean(axis=(0, 2))
        out.flush()
        meta = {'neuron': a.neuron, 'seed': a.seed, 'f_levels': F_LEVELS, 'K': K.tolist(),
                'f_calib': f_cal.tolist(), 'f_train_mean': f_train.tolist(),
                'n_train': len(Xtr), 'n_test': len(Xte), 'cfg': cfg0.to_dict(),
                't_calib_s': t_cal, 't_codes_s': t_run}
    else:
        name = f'{a.neuron}_s{a.seed}_fs{suffix}'
        out = np.lib.format.open_memmap(os.path.join(OUT, name + '.npy'), mode='w+', dtype=np.uint8,
                                        shape=(len(X_all), len(PHASIC_W), len(PHASIC_F), cfg0.n_dg))
        meta = {'neuron': a.neuron, 'seed': a.seed, 'W_FS_GC': PHASIC_W, 'f_levels': PHASIC_F,
                'K': [], 'f_calib': [], 'f_train_mean': [], 'fs_rate_hz': [], 'cfg': cfg0.to_dict()}
        for wi, W in enumerate(PHASIC_W):
            # W = 0 → pula FS wyłączona; dla porównywalności liczymy ją jako 1e-9
            cfg = replace(cfg0, w_fs_gc=max(W, 1e-9))
            layer = DGLayer(cfg, conn, dev)
            K, f_cal = solve_k_table(layer, X_cal, PHASIC_F, *K_RANGE, seed=a.seed)
            print(f'  W_FS_GC={W}: K={K.round(2).tolist()} f={f_cal.round(3).tolist()}', flush=True)
            view = np.zeros((len(X_all), len(PHASIC_F), cfg.n_dg), np.uint8)
            compute(layer, X_all, K, a.seed, a.batch, view, f'{name} W={W}')
            out[:, wi] = view
            meta['K'].append(K.tolist())
            meta['f_calib'].append(f_cal.tolist())
            meta['f_train_mean'].append((view[:len(Xtr)] > 0).mean(axis=(0, 2)).tolist())
        out.flush()
        meta.update(n_train=len(Xtr), n_test=len(Xte))
    with open(os.path.join(OUT, name + '.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print('done', name, flush=True)


if __name__ == '__main__':
    main()
