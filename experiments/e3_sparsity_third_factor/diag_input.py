"""E3.0 — diagnostyka wejścia (wejście znormalizowane, tasks.normalize_images): ile informacji niesie kod DG przy różnych ustawieniach
napędu (ten sam średni napęd rate·w·τ, różna liczba i wielkość impulsów, różne T).
Miara: regresja logistyczna i reguła delta na kodzie przy f ≈ 10%, 12k/2k obrazów."""
import sys, time, json
from dataclasses import replace
import numpy as np, torch
from model import *; from tasks import load_mnist; from calibrate import solve_k_table
from learning import logistic_ceiling, kwta_codes, Readout
Xtr, ytr, Xte, yte = load_mnist()
Xa, ya, Xb, yb = Xtr[:12000], ytr[:12000], Xte[:2000], yte[:2000]
dev = pick_device(); out = []
def online(A, B, rule, eta):
    ro = Readout(A.shape[1], rule, eta, 0)
    for i in np.random.default_rng(0).permutation(len(A)): ro.step(A[i], int(ya[i]))
    return float((ro.predict(B) == yb).mean())
variants = [('izh', 50, 4.0, 100), ('izh', 200, 1.0, 100), ('lif', 50, 4.0, 100), ('lif', 200, 1.0, 100)]
for neuron, rate, w, T in variants:
    t0 = time.time()
    cfg = LayerCfg(neuron=neuron, rate_max=rate, w_pp=w, T_ms=T)
    conn = make_connectivity(cfg, live_pixels(Xtr), 99)
    L = DGLayer(cfg, conn, dev)
    K, f = solve_k_table(L, Xa[:500], [0.05, 0.10, 0.20], -60, 80, n_iter=14)
    codes = []
    for X in (Xa, Xb):
        cs = []
        for s in range(0, len(X), 1000):
            cs.append(L.run(torch.from_numpy(X[s:s+1000]), K, make_generator(dev, s)).cpu().numpy())
        codes.append(np.concatenate(cs).astype(np.float32))
    rec = {'neuron': neuron, 'rate': rate, 'w': w, 'T': T, 'K': K.round(2).tolist(), 'f': f.round(3).tolist()}
    for li, ff in enumerate([0.05, 0.10, 0.20]):
        A, B = codes[0][:, li], codes[1][:, li]
        rec[f'logistic_f{ff}'] = logistic_ceiling(A, ya, B, yb)
        rec[f'delta_f{ff}'] = online(A, B, 'delta', 0.05)
        rec[f'rstdp_f{ff}'] = online(A, B, 'rstdp', 0.5)
        rec[f'count_active_f{ff}'] = float(A[A > 0].mean())
    rec['s'] = round(time.time() - t0)
    print(json.dumps(rec), flush=True); out.append(rec)
M = make_connectivity(LayerCfg(), live_pixels(Xtr), 99)['M']
for ff in (0.05, 0.10, 0.20):
    A, B = kwta_codes(Xa, M, ff), kwta_codes(Xb, M, ff)
    print(json.dumps({'kwta_f': ff, 'logistic': logistic_ceiling(A, ya, B, yb), 'delta': online(A, B, 'delta', 0.05), 'rstdp': online(A, B, 'rstdp', 0.5)}), flush=True)
