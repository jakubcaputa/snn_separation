"""
E3.9h — rozbicie błędów (jak E3.9) dla sieci z warstwą ukrytą z E3.7/E3.7b (prereg.md sek. 6j;
kryteria zapisane przed uruchomieniem, 2026-10-29).

Pytanie: czy prawie całkowite zapominanie wspólnej warstwy ukrytej (`pos_bound`, `agrel_pos`)
to też przewaga nowych klas (wiedza zostaje, przegrywa), czy zniszczenie reprezentacji starych
klas? Kontrola: `pos_pool` (pule na klasę, prawie nie zapomina). Te same sieci, ziarna, η
i regulator co w run_hidden.py --phase run; diagnoza `run_errors.diagnose`.
Warunki: stałe f przy f_c (fixed), g = +1 i jego stałe f (matched_mod), g = −1 i stałe f o jego
średniej oceniane na poziomie spoczynkowym g = −1 (matched_inv_evalrest).
Użycie: python run_hidden_errors.py --variant pos_bound --neuron izh --seed 0 --order-seed 0
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time

import numpy as np

from learning import Controller
from run_errors import N_CAL, diagnose
from run_hidden import F_DENSE, F_SPARSE, OUT, VARIANTS, Data, HiddenNet
from run_split import nearest_by_f


def train(D, variant, eta, level_fn, ctrl, eval_level, cal_idx):
    net = HiddenNet(D.codes.shape[2], variant, eta, D.seed)
    used = []
    for _, seq in D.stream:
        for i in seq:
            l = level_fn()
            _, R, p = net.step(np.asarray(D.codes[i, l, :], np.float32), int(D.ytr[i]))
            if ctrl is not None:
                ctrl.update(p, R)
            used.append(l)
    out = diagnose(net, D.test(eval_level), D.yte, np.asarray(D.codes[cal_idx, eval_level, :], np.float32))
    out['mean_level_f'] = float(np.mean([D.f_mean[l] for l in used]))
    out['eval_level_f'] = float(D.f_mean[eval_level])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', choices=VARIANTS, required=True)
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()
    eta = json.load(open(os.path.join(OUT, 'hparams.json')))[a.neuron][a.variant]['eta']
    pil = json.load(open(os.path.join(OUT, 'pilot.json')))[f'{a.neuron}_{a.variant}']
    D = Data(a.neuron, a.seed, a.order_seed)
    fm = D.f_mean
    rng = np.random.default_rng(7_000 + D.seed)
    cal_idx = np.sort(np.concatenate([rng.choice(np.where(D.ytr == c)[0], N_CAL // 10, replace=False)
                                      for c in range(10)]))
    l_c = nearest_by_f(fm, math.sqrt(F_DENSE * F_SPARSE))
    r = {'fixed': train(D, a.variant, eta, lambda: l_c, None, l_c, cal_idx)}
    for name, (f_rest, f_novel) in (('mod', (F_DENSE, F_SPARSE)), ('inv', (F_SPARSE, F_DENSE))):
        ctrl = Controller(fm, f_rest, f_novel, signal='unc', tau=50.0, a=pil['a'], b=pil['b'])
        l_rest = nearest_by_f(fm, f_rest)
        r[name] = train(D, a.variant, eta, ctrl.level, ctrl, l_rest, cal_idx)
        lm = nearest_by_f(fm, r[name]['mean_level_f'])
        key = 'matched_mod' if name == 'mod' else 'matched_inv_evalrest'
        r[key] = train(D, a.variant, eta, lambda: lm, None, lm if name == 'mod' else l_rest, cal_idx)
    for c, d in r.items():
        print(f"  {a.variant} {c:21s} acc {d['acc_class']:.3f}  w zadaniu {d['acc_within']:.3f}  "
              f"po korekcie {d['acc_debiased']:.3f}  błędy→nowsze {d['err_newer']:.2f} →ostatnie {d['err_last']:.2f}", flush=True)
    os.makedirs(os.path.join(OUT, 'errors'), exist_ok=True)
    fn = os.path.join(OUT, 'errors', f'{a.variant}_{a.neuron}_s{a.seed}_o{a.order_seed}.json')
    json.dump({'variant': a.variant, 'neuron': a.neuron, 'seed': a.seed, 'order_seed': a.order_seed,
               'eta': eta, 'conditions': r, 'elapsed_s': time.time() - t0}, open(fn, 'w'))
    print('saved', fn, f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
