"""
E3 — kalibracja tablicy K(f): bisekcja po K, aż średni odsetek aktywnych neuronów
warstwy DG (po obrazach kalibracyjnych) trafi w zadane f.

Ta sama logika co `dg_core.calibrate.solve_k_gc_for_active_fraction`, ale
wektoryzowana: wszystkie poziomy f bisekujemy równocześnie, na tych samych
impulsach wejściowych (jedna symulacja na iterację, L poziomów naraz).
"""
from __future__ import annotations

import numpy as np
import torch

from model import DGLayer, make_generator


def solve_k_table(layer: DGLayer, X_cal: np.ndarray, f_targets, k_lo: float, k_hi: float,
                  n_iter: int = 16, batch: int = 500, seed: int = 0, verbose: bool = False):
    """
    Zwraca (K [L], f_osiągnięte [L]). f jest malejące w K (wyższe K → wyższy próg).
    Na każdej iteracji ta sama realizacja szumu (ten sam seed), więc bisekcja jest
    deterministyczna i monotoniczna.
    """
    f_t = np.asarray(f_targets, np.float64)
    lo = np.full(len(f_t), k_lo)
    hi = np.full(len(f_t), k_hi)
    X = torch.from_numpy(X_cal)
    f_mid = None
    for it in range(n_iter):
        mid = 0.5 * (lo + hi)
        f_mid = _mean_f(layer, X, mid, batch, seed)
        too_active = f_mid > f_t           # za dużo aktywnych → podnieść K
        lo = np.where(too_active, mid, lo)
        hi = np.where(too_active, hi, mid)
        if verbose:
            print(f'  iter {it:2d}: max |f − f*| = {np.max(np.abs(f_mid - f_t)):.4f}', flush=True)
    K = 0.5 * (lo + hi)
    return K, _mean_f(layer, X, K, batch, seed)


def _mean_f(layer: DGLayer, X: torch.Tensor, K, batch: int, seed: int) -> np.ndarray:
    gen = make_generator(str(layer.dev), seed)
    tot = np.zeros(len(K))
    for s in range(0, X.shape[0], batch):
        c = layer.run(X[s:s + batch], K, gen)
        tot += (c > 0).float().mean(-1).sum(0).cpu().numpy()
    return tot / X.shape[0]
