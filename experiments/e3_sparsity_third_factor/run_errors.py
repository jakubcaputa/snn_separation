"""
E3.9 — skąd bierze się zapominanie: zniszczenie starych wag czy przewaga nowych klas?
(prereg.md sek. 6h; kryteria zapisane przed uruchomieniem)

Kandydat na mechanizm z E3.8: przy regułach z osłabianiem zapominanie w scenariuszu
class-incremental to głównie *przewaga nowych klas* (ich wyjścia wygrywają na obrazach starych
klas), a nie zniszczenie wiedzy o starych klasach. Standardowa diagnoza (np. Wu i in. 2019 BiC,
Hou i in. 2019 LUCIR, van de Ven & Tolias 2019): po nauce wszystkich zadań, na obrazach testowych
starych zadań (0/1 … 6/7) mierzymy

  acc_class    — zwykła dokładność 10-klasowa (to, co daje BWT),
  acc_within   — dokładność, gdy wybór ograniczamy do 2 klas PRAWDZIWEGO zadania
                 (jeśli wysoka, wiedza o starych klasach jest w wagach, tylko przegrywa),
  err_newer    — odsetek błędów wskazujących klasę NOWSZEGO zadania niż prawdziwe,
  err_last     — odsetek błędów wskazujących klasę OSTATNIEGO zadania (8/9),
  acc_debiased — dokładność 10-klasowa po standaryzacji każdego wyjścia (średnia, SD) na
                 zbalansowanej próbce obrazów treningowych wszystkich klas — korekta „z wyrocznią”
                 (jak BiC: korzysta z danych starych klas), mierzy ile informacji zostało w wagach.

Warunki jak w E3.8: mod (g = +1), inv (g = −1), stałe f o tej samej średniej, oraz stałe f o średniej
inv oceniane na poziomie spoczynkowym inv. Czytniki: rstdp, delta (z osłabianiem), rgate (bez).
Użycie: python run_errors.py --neuron izh --seed 0 --order-seed 0
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from learning import Controller, Readout
from run_mechanism import Ctx
from run_split import RES, nearest_by_f
from tasks import TASKS

RULES = ('rstdp', 'delta', 'rgate')
N_CAL = 2000  # obrazy treningowe do standaryzacji wyjść (zbalansowane klasy)


def diagnose(ro, C_te, yte, C_cal):
    task_of = np.array([j for c in range(10) for j, t in enumerate(TASKS) if c in t])
    old = np.isin(yte, [c for t in TASKS[:-1] for c in t])
    S, y = ro.scores(C_te[old]), yte[old]
    pred = S.argmax(1)
    err = pred != y
    t_true, t_pred = task_of[y], task_of[pred]
    pair = np.array([TASKS[t] for t in t_true])
    within = pair[np.arange(len(y)), np.argmax(np.take_along_axis(S, pair, 1), 1)]
    Sc = ro.scores(C_cal)
    S_db = (S - Sc.mean(0)) / np.maximum(Sc.std(0), 1e-9)
    n_err = max(int(err.sum()), 1)
    per_task = {str(j): float((~err[t_true == j]).mean()) for j in range(len(TASKS) - 1)}
    return {'acc_class': float((~err).mean()), 'acc_within': float((within == y).mean()),
            'acc_debiased': float((S_db.argmax(1) == y).mean()),
            'err_newer': float((err & (t_pred > t_true)).sum() / n_err),
            'err_last': float((err & (t_pred == len(TASKS) - 1)).sum() / n_err),
            'err_same_task': float((err & (t_pred == t_true)).sum() / n_err),
            'err_older': float((err & (t_pred < t_true)).sum() / n_err),
            'acc_class_per_task': per_task,
            'score_margin_last': float(np.mean(S[:, list(TASKS[-1])].max(1) - S[np.arange(len(y)), y]))}


def train(ctx, rule, eta, level_fn, ctrl, eval_level, cal_idx):
    ro = Readout(ctx.codes.shape[2], rule, eta, ctx.seed)
    used = []
    for _, seq in ctx.stream:
        for i in seq:
            l = level_fn()
            _, R, s = ro.step(np.asarray(ctx.codes[i, l, :], np.float32), int(ctx.ytr[i]))
            if ctrl is not None:
                ctrl.update(s, R)
            used.append(l)
    C_cal = np.asarray(ctx.codes[cal_idx, eval_level, :], np.float32)
    out = diagnose(ro, ctx.test_codes(eval_level), ctx.yte, C_cal)
    out['mean_level_f'] = float(np.mean([ctx.f_mean[l] for l in used]))
    out['eval_level_f'] = float(ctx.f_mean[eval_level])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()
    ctx = Ctx(a.neuron, a.seed, a.order_seed)
    hp, fm = ctx.hp, ctx.f_mean
    rng = np.random.default_rng(7_000 + ctx.seed)
    cal_idx = np.sort(np.concatenate([rng.choice(np.where(ctx.ytr == c)[0], N_CAL // 10, replace=False)
                                      for c in range(10)]))
    out = {'neuron': a.neuron, 'seed': a.seed, 'order_seed': a.order_seed, 'rules': {}}
    for rule in RULES:
        h = hp[a.neuron][rule]
        ch = {k: v for k, v in hp['controller'][f'{a.neuron}_{rule}'].items() if k in ('signal', 'a', 'b', 'tau')}
        ch.setdefault('tau', hp.get('tau', 50.0))
        r = {}
        for name, (f_rest, f_novel) in (('mod', (h['f_dense'], h['f_sparse'])), ('inv', (h['f_sparse'], h['f_dense']))):
            ctrl = Controller(fm, f_rest, f_novel, **ch)
            l_rest = nearest_by_f(fm, f_rest)
            r[name] = train(ctx, rule, h['eta'], ctrl.level, ctrl, l_rest, cal_idx)
            lm = nearest_by_f(fm, r[name]['mean_level_f'])
            r[f'matched_{name}'] = train(ctx, rule, h['eta'], lambda: lm, None, lm, cal_idx)
            if name == 'inv':
                r['matched_inv_evalrest'] = train(ctx, rule, h['eta'], lambda: lm, None, l_rest, cal_idx)
        out['rules'][rule] = r
        for c in ('mod', 'matched_mod', 'inv', 'matched_inv', 'matched_inv_evalrest'):
            d = r[c]
            print(f"  {rule:6s} {c:21s} acc {d['acc_class']:.3f}  w zadaniu {d['acc_within']:.3f}  "
                  f"po korekcie {d['acc_debiased']:.3f}  błędy→nowsze {d['err_newer']:.2f} →ostatnie {d['err_last']:.2f}", flush=True)
    out['elapsed_s'] = time.time() - t0
    os.makedirs(os.path.join(RES, 'e39'), exist_ok=True)
    fn = os.path.join(RES, 'e39', f'{a.neuron}_s{a.seed}_o{a.order_seed}.json')
    json.dump(out, open(fn, 'w'))
    print('saved', fn, f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
