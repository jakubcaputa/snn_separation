"""
E3.8 — test mechanizmu „rozcieńczać przy osłabianiu, izolować przy wzmacnianiu”
(README sek. 6f; kryteria zapisane przed uruchomieniem).

Hipoteza (2026-10-26): przy regułach znormalizowanych per obraz jeden obraz zmienia
odpowiedź czytnika o tyle samo niezależnie od gęstości kodu; gęsty kod rozkłada tę zmianę
na więcej synaps (każda zmienia się słabiej). Duże, szkodliwe poprawki (pomyłki na starcie
nowego zadania) przy „nowość → gęściej” są więc rozcieńczone, a przy „nowość → rzadziej”
skoncentrowane na najsilniej pobudzonych neuronach, z których odczytywane są stare klasy.
Przy regule bez osłabiania nie ma czego rozcieńczać — liczy się izolacja (rzadki kod).

Części (Split-MNIST, architektura domyślna, kody z results/codes/):
  A. reguły rstdp, delta (znormalizowane) i rstdp_raw, delta_raw (bez normalizacji):
     mod (g = +1), inv (g = −1), stałe f o średniej mod / inv (ocena na własnym poziomie)
     oraz stałe f o średniej inv OCENIANE na poziomie spoczynkowym inv (brakująca kontrola).
  B. reguła rmix z udziałem osłabiania λ ∈ {0, 0.25, 0.5, 0.75, 1}: mod, inv i ich kontrole.
Dla każdego treningu: ACC, BWT oraz „szkoda” — suma |ΔW| na wagach STARYCH klas, na
neuronach aktywnych (≥ 1% obrazów testowych starego zadania) na poziomie oceny, w oknach
nowości (pierwsze 300 obrazów zadań 2–5) i w całym treningu, wraz z całkowitą sumą |ΔW|.

Użycie:  python run_mechanism.py --neuron izh --seed 0 --order-seed 0
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

NOVEL_WINDOW = 300
LAMBDAS = [0.0, 0.25, 0.5, 0.75, 1.0]


class Ctx:
    def __init__(self, neuron, seed, order_seed):
        with open(HP_FILE) as f:
            self.hp = json.load(f)
        path = os.path.join(CODES, f'{neuron}_s{seed}.npy')
        with open(path.replace('.npy', '.json')) as f:
            self.meta = json.load(f)
        self.codes = np.load(path, mmap_mode='r')
        self.n_tr = self.meta['n_train']
        self.f_mean = self.meta['f_train_mean']
        _, self.ytr, _, self.yte = load_mnist(normalize=False)
        self.seed = 1000 * seed + order_seed
        self.stream = task_stream(self.ytr, self.seed, self.hp.get('epochs_per_task', 1))
        self.test_task = [np.where(np.isin(self.yte, t))[0] for t in TASKS]
        self.neuron = neuron
        self._test, self._fp = {}, {}

    def test_codes(self, l):
        if l not in self._test:
            self._test[l] = np.asarray(self.codes[self.n_tr:, l, :], np.float32)
        return self._test[l]

    def footprint(self, l):
        """[5, N] — neurony aktywne w ≥ 1% obrazów testowych zadania j na poziomie l."""
        if l not in self._fp:
            C = self.test_codes(l) > 0
            self._fp[l] = np.stack([C[idx].mean(0) >= 0.01 for idx in self.test_task])
        return self._fp[l]

    def raw_scale(self, rule, f_c):
        l = nearest_by_f(self.f_mean, f_c)
        C = np.asarray(self.codes[:self.n_tr:20, l, :], np.float32)
        n2 = (C * C).sum(1)
        return float(1.0 / np.sqrt(n2.mean())) if rule == 'rstdp_raw' else float(1.0 / n2.mean())


def train(ctx, rule, eta, level_fn, ctrl, eval_level, **ro_kw):
    ro = Readout(ctx.codes.shape[2], rule, eta, ctx.seed, **ro_kw)
    fp = ctx.footprint(eval_level)
    acc = np.full((len(TASKS), len(TASKS)), np.nan)
    used = []
    dmg = {'novel_old': 0.0, 'novel_all': 0.0, 'all_old': 0.0, 'all_all': 0.0}
    C_eval = ctx.test_codes(eval_level)
    for t, seq in ctx.stream:
        old_cls = [c for j in range(t) for c in TASKS[j]]
        old_mask = fp[:t].any(0) if t > 0 else None
        for k, i in enumerate(seq):
            l = level_fn()
            Wp = ro.W.copy() if t > 0 else None
            _, R, s = ro.step(np.asarray(ctx.codes[i, l, :], np.float32), int(ctx.ytr[i]))
            if ctrl is not None:
                ctrl.update(s, R)
            used.append(l)
            if t > 0:
                dW = np.abs(ro.W - Wp)
                tot = float(dW.sum())
                old = float(dW[old_mask][:, old_cls].sum())
                dmg['all_old'] += old
                dmg['all_all'] += tot
                if k < NOVEL_WINDOW:
                    dmg['novel_old'] += old
                    dmg['novel_all'] += tot
        pred = ro.predict(C_eval)
        acc[t, :t + 1] = [float((pred[idx] == ctx.yte[idx]).mean()) for idx in ctx.test_task][:t + 1]
    T = len(TASKS) - 1
    out = {'ACC': float(np.nanmean(acc[T])), 'BWT': float(np.mean([acc[T, j] - acc[j, j] for j in range(T)])),
           'mean_level_f': float(np.mean([ctx.f_mean[l] for l in used])),
           'eval_level_f': float(ctx.f_mean[eval_level]), 'acc': acc.tolist()}
    out.update(dmg)
    out['damage_frac_novel'] = dmg['novel_old'] / max(dmg['novel_all'], 1e-12)
    out['damage_frac_all'] = dmg['all_old'] / max(dmg['all_all'], 1e-12)
    return out


def dose_block(ctx, rule, hp_rule, ctrl_hp, with_eval_control=False, **ro_kw):
    f_d, f_s = hp_rule['f_dense'], hp_rule['f_sparse']
    fm = ctx.f_mean
    res = {}
    for name, (f_rest, f_novel) in (('mod', (f_d, f_s)), ('inv', (f_s, f_d))):
        ctrl = Controller(fm, f_rest, f_novel, **ctrl_hp)
        l_rest = nearest_by_f(fm, f_rest)
        res[name] = train(ctx, rule, hp_rule['eta'], ctrl.level, ctrl, l_rest, **ro_kw)
        lm = nearest_by_f(fm, res[name]['mean_level_f'])
        res[f'matched_{name}'] = train(ctx, rule, hp_rule['eta'], lambda: lm, None, lm, **ro_kw)
        if with_eval_control and name == 'inv':
            res['matched_inv_evalrest'] = train(ctx, rule, hp_rule['eta'], lambda: lm, None, l_rest, **ro_kw)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()
    ctx = Ctx(a.neuron, a.seed, a.order_seed)
    hp = ctx.hp
    out = {'neuron': a.neuron, 'seed': a.seed, 'order_seed': a.order_seed, 'A': {}, 'B': {}}

    def ctrl_hp(key):
        c = {k: v for k, v in hp['controller'][f'{a.neuron}_{key}'].items() if k in ('signal', 'a', 'b', 'tau')}
        c.setdefault('tau', hp.get('tau', 50.0))
        return c

    # część A — normalizacja per obraz vs bez
    for rule, base in (('rstdp', 'rstdp'), ('delta', 'delta'), ('rstdp_raw', 'rstdp'), ('delta_raw', 'delta')):
        h = hp[a.neuron][base]
        kw = {}
        if rule.endswith('_raw'):
            kw['scale'] = ctx.raw_scale(rule, math.sqrt(h['f_dense'] * h['f_sparse']))
        out['A'][rule] = dose_block(ctx, rule, h, ctrl_hp(base), with_eval_control=True, **kw)
        r = out['A'][rule]
        print(f"  {rule:9s} Δ(+1) {r['mod']['BWT'] - r['matched_mod']['BWT']:+.3f}  Δ(−1) {r['inv']['BWT'] - r['matched_inv']['BWT']:+.3f}"
              f"  Δ(−1, ocena spocz.) {r['inv']['BWT'] - r['matched_inv_evalrest']['BWT']:+.3f}  "
              f"szkoda nowość mod {r['mod']['damage_frac_novel']:.3f} inv {r['inv']['damage_frac_novel']:.3f}", flush=True)
    # część B — udział osłabiania
    h = hp[a.neuron]['rgate']
    for lam in LAMBDAS:
        out['B'][str(lam)] = dose_block(ctx, 'rmix', h, ctrl_hp('rgate'), lam=lam)
        r = out['B'][str(lam)]
        print(f"  rmix λ={lam:.2f} Δ(+1) {r['mod']['BWT'] - r['matched_mod']['BWT']:+.3f}  Δ(−1) {r['inv']['BWT'] - r['matched_inv']['BWT']:+.3f}"
              f"  ACC stałe {r['matched_mod']['ACC']:.3f}", flush=True)
    out['elapsed_s'] = time.time() - t0
    os.makedirs(os.path.join(RES, 'e38'), exist_ok=True)
    fn = os.path.join(RES, 'e38', f'{a.neuron}_s{a.seed}_o{a.order_seed}.json')
    json.dump(out, open(fn, 'w'))
    print('saved', fn, f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
