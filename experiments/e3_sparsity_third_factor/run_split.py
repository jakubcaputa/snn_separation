"""
E3.3 — Split-MNIST class-incremental (0/1 → 2/3 → … → 8/9), wspólny czytnik
10-klasowy, BRAK informacji o granicach zadań (poza warunkiem oracle_boundary).

Warunki (archiwum_plan.md sek. 5):
  fixed_dense, fixed_sparse     stałe f
  mod_novelty                   regulator: nowość → rzadziej (f_dense → f_sparse)
  mod_novelty_inv               regulator odwrócony: nowość → gęściej
  fixed_matched                 stałe f = średnie f zrealizowane w mod_novelty (null!)
  3f_lr                         f jak fixed_matched, nowość mnoży tempo uczenia
  3f_both                       regulator + mnożnik tempa uczenia
  oracle_boundary               K podniesione przez pierwsze M obrazów każdego zadania
  kwta_fly                      FlyModel: k-WTA (5%) na napędzie + reguła w[y] += β·φ

Metryki: macierz acc[t, j] (dokładność na zadaniu j po zadaniu t, 10-klasowo),
ACC = średnia acc[4, :], BWT = średnia_{j<4}(acc[4, j] − acc[j, j]), nakładanie
„śladów” zadań (neurony DG aktywne w ≥ 1% obrazów zadania), przebieg f, n, N̄.

Użycie:
  python run_split.py --neuron izh --seed 0 --order-seed 0 --rule rstdp
  python run_split.py --neuron izh --seed 99 --rule rstdp --pilot     # ustala a, b regulatora
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time

import numpy as np

from learning import Controller, Readout, kwta_codes
from model import LayerCfg, live_pixels, make_connectivity
from tasks import TASKS, load_mnist, task_stream

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
CODES = os.path.join(RES, 'codes')
HP_FILE = os.path.join(HERE, 'hparams.json')

CONDITIONS = ['fixed_dense', 'fixed_sparse', 'mod_novelty', 'mod_novelty_inv',
              'fixed_matched', '3f_lr', '3f_both', 'oracle_boundary']
TRACE_EVERY = 50


def nearest_by_f(f_level_means, f):
    lf = math.log(f)
    return int(np.argmin([abs(math.log(max(x, 1e-6)) - lf) for x in f_level_means]))


class Run:
    def __init__(self, codes, meta, ytr, yte, stream, hp, neuron, rule, seed):
        self.codes, self.meta = codes, meta
        self.ytr, self.yte = ytr, yte
        self.n_tr = meta['n_train']
        self.stream = stream
        self.hp, self.rule, self.seed = hp, rule, seed
        self.h = hp[neuron][rule]
        self.levels = meta['f_levels']
        self.f_mean = meta['f_train_mean']          # zmierzone średnie f każdego poziomu
        self.l_dense = nearest_by_f(self.f_mean, self.h['f_dense'])
        self.l_sparse = nearest_by_f(self.f_mean, self.h['f_sparse'])
        self.test_task = [np.where(np.isin(yte, t))[0] for t in TASKS]
        self._test_cache = {}

    def test_codes(self, l):
        if l not in self._test_cache:
            self._test_cache[l] = np.asarray(self.codes[self.n_tr:, l, :], np.float32)
        return self._test_cache[l]

    def evaluate(self, ro, l):
        C = self.test_codes(l)
        pred = ro.predict(C)
        return [float((pred[idx] == self.yte[idx]).mean()) for idx in self.test_task]

    def go(self, cond, matched_level=None, ctrl_hp=None, trace=False):
        h, hp = self.h, self.hp
        ro = Readout(self.codes.shape[2], self.rule, h['eta'], self.seed, hp.get('eps', 0.02))
        f_d, f_s = self.f_mean[self.l_dense], self.f_mean[self.l_sparse]
        ctrl = None
        if cond in ('mod_novelty', '3f_both', '3f_lr'):
            ctrl = Controller(self.f_mean, f_d, f_s, **ctrl_hp)
        elif cond == 'mod_novelty_inv':
            ctrl = Controller(self.f_mean, f_s, f_d, **ctrl_hp)
        fixed = {'fixed_dense': self.l_dense, 'fixed_sparse': self.l_sparse,
                 'fixed_matched': matched_level, '3f_lr': matched_level}.get(cond)
        if cond in ('mod_novelty', '3f_both', 'oracle_boundary'):
            l_eval = self.l_dense
        elif cond == 'mod_novelty_inv':
            l_eval = self.l_sparse
        else:
            l_eval = fixed
        acc = np.full((len(TASKS), len(TASKS)), np.nan)
        acc_dense = np.full((len(TASKS), len(TASKS)), np.nan)
        footprint = np.zeros((len(TASKS), self.codes.shape[2]))
        lv_hist, f_hist = [], []
        tr = {'n': [], 'Nbar': [], 'level_f': [], 'f': []}
        for t, seq in self.stream:
            for k, i in enumerate(seq):
                if fixed is not None and cond != '3f_lr':
                    l = fixed
                elif cond == '3f_lr':
                    l = fixed
                elif cond == 'oracle_boundary':
                    l = self.l_sparse if k < hp.get('oracle_M', 300) else self.l_dense
                else:
                    l = ctrl.level()
                x = np.asarray(self.codes[i, l, :], np.float32)
                mult = 1.0
                if cond in ('3f_lr', '3f_both'):
                    mult = 1.0 + hp.get('c_lr', 3.0) * ctrl.n()
                _, R, s = ro.step(x, int(self.ytr[i]), mult)
                if ctrl is not None:
                    ctrl.update(s, R)
                act = x > 0
                footprint[t] += act
                lv_hist.append(l)
                f_hist.append(act.mean())
                if trace and len(f_hist) % TRACE_EVERY == 0:
                    tr['n'].append(ctrl.n() if ctrl else None)
                    tr['Nbar'].append(ctrl.Nbar if ctrl else None)
                    tr['level_f'].append(self.f_mean[l])
                    tr['f'].append(float(np.mean(f_hist[-TRACE_EVERY:])))
            footprint[t] /= len(seq)
            acc[t, :t + 1] = self.evaluate(ro, l_eval)[:t + 1]
            acc_dense[t, :t + 1] = self.evaluate(ro, self.l_dense)[:t + 1]
        fp = footprint >= 0.01
        overlap = np.full((len(TASKS), len(TASKS)), np.nan)
        for a in range(len(TASKS)):
            for b in range(len(TASKS)):
                u = (fp[a] | fp[b]).sum()
                overlap[a, b] = (fp[a] & fp[b]).sum() / u if u else np.nan
        T = len(TASKS) - 1
        out = {
            'condition': cond, 'eval_level_f': self.f_mean[l_eval],
            'acc': acc.tolist(), 'ACC': float(np.nanmean(acc[T])),
            'BWT': float(np.mean([acc[T, j] - acc[j, j] for j in range(T)])),
            'acc_at_dense': acc_dense.tolist(), 'ACC_at_dense': float(np.nanmean(acc_dense[T])),
            'mean_level_f': float(np.mean([self.f_mean[l] for l in lv_hist])),
            'mean_f_measured': float(np.mean(f_hist)),
            'overlap_between_tasks': float(np.nanmean(overlap[~np.eye(len(TASKS), dtype=bool)])),
            'overlap': overlap.tolist(),
        }
        if trace:
            out['trace'] = tr
        return out, lv_hist


def run_fly(Xtr, ytr, Xte, yte, stream, seed, hp, net_seed):
    M = make_connectivity(LayerCfg(), live_pixels(Xtr), net_seed)['M']
    f = hp.get('fly_f', 0.05)
    Ctr = kwta_codes(Xtr, M, f)
    Cte = kwta_codes(Xte, M, f)
    ro = Readout(Ctr.shape[1], 'fly', hp.get('fly_eta', 0.01), seed)
    test_task = [np.where(np.isin(yte, t))[0] for t in TASKS]
    acc = np.full((len(TASKS), len(TASKS)), np.nan)
    for t, seq in stream:
        for i in seq:
            ro.step(Ctr[i], int(ytr[i]))
        pred = ro.predict(Cte)
        acc[t, :t + 1] = [float((pred[idx] == yte[idx]).mean()) for idx in test_task][:t + 1]
    T = len(TASKS) - 1
    return {'condition': 'kwta_fly', 'eval_level_f': f, 'acc': acc.tolist(),
            'ACC': float(np.nanmean(acc[T])),
            'BWT': float(np.mean([acc[T, j] - acc[j, j] for j in range(T)])),
            'mean_level_f': f, 'mean_f_measured': float((Ctr > 0).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    ap.add_argument('--rule', choices=['rstdp', 'delta', 'rgate'], required=True)
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--with-fly', action='store_true')
    a = ap.parse_args()

    with open(HP_FILE) as f:
        hp = json.load(f)
    path = os.path.join(CODES, f'{a.neuron}_s{a.seed}.npy')
    with open(path.replace('.npy', '.json')) as f:
        meta = json.load(f)
    codes = np.load(path, mmap_mode='r')
    Xtr, ytr, Xte, yte = load_mnist()
    seed = 1000 * a.seed + a.order_seed
    stream = task_stream(ytr, seed, hp.get('epochs_per_task', 1))
    run = Run(codes, meta, ytr, yte, stream, hp, a.neuron, a.rule, seed)
    t0 = time.time()
    tag = f'{a.neuron}_{a.rule}'

    if a.pilot:
        # Regulator bez normalizacji (a=0, b=1): n = N̄. Zapisujemy przebieg N̄ dla obu
        # sygnałów i wyznaczamy a, b jako 5. i 95. percentyl N̄ (po 500 pierwszych obrazach).
        res = {}
        for sig in ('unc', 'rpe'):
            ch = {'signal': sig, 'tau': hp.get('tau', 50.0), 'a': 0.0, 'b': 1.0 if sig == 'unc' else 2.0}
            out, _ = run.go('mod_novelty', ctrl_hp=ch, trace=True)
            nb = np.array(out['trace']['Nbar'][500 // TRACE_EVERY:], float)
            # kontrast na granicach zadań: N̄ w pierwszych 300 obrazach zadania vs ostatnich 1000
            bounds = np.cumsum([0] + [len(s) for _, s in stream])
            nb_all = np.array(out['trace']['Nbar'], float)
            starts, ends = [], []
            for t in range(1, len(TASKS)):
                b0 = bounds[t] // TRACE_EVERY
                starts.append(nb_all[b0:b0 + 300 // TRACE_EVERY].mean())
                ends.append(nb_all[max(0, b0 - 1000 // TRACE_EVERY):b0].mean())
            res[sig] = {'a': float(np.percentile(nb, 5)), 'b': float(np.percentile(nb, 95)),
                        'boundary_rise': float(np.mean(np.array(starts) - np.array(ends))),
                        'Nbar_trace': out['trace']['Nbar']}
            print(sig, {k: v for k, v in res[sig].items() if k != 'Nbar_trace'}, flush=True)
        os.makedirs(os.path.join(RES, 'pilot'), exist_ok=True)
        with open(os.path.join(RES, 'pilot', f'{tag}_s{a.seed}.json'), 'w') as f:
            json.dump(res, f)
        return

    # tylko parametry regulatora; pola diagnostyczne z pilotażu (boundary_rise_*) pomijamy
    ch = {k: v for k, v in hp['controller'][tag].items() if k in ('signal', 'a', 'b', 'tau')}
    ch.setdefault('tau', hp.get('tau', 50.0))
    results = []
    mod, lv = run.go('mod_novelty', ctrl_hp=ch, trace=True)
    results.append(mod)
    matched = nearest_by_f(run.f_mean, mod['mean_level_f'])
    for cond in CONDITIONS:
        if cond == 'mod_novelty':
            continue
        out, _ = run.go(cond, matched_level=matched, ctrl_hp=ch,
                        trace=cond in ('mod_novelty_inv', '3f_both'))
        results.append(out)
        print(f'  {cond:16s} ACC={out["ACC"]:.3f} BWT={out["BWT"]:+.3f} f={out["mean_level_f"]:.3f}', flush=True)
    # null o dopasowanej rzadkości dla wariantu odwróconego (dodane 2026-10-13, test
    # potwierdzający H-E3e): stałe f równe średniemu f zrealizowanemu w mod_novelty_inv
    inv = next(r for r in results if r['condition'] == 'mod_novelty_inv')
    m_inv = nearest_by_f(run.f_mean, inv['mean_level_f'])
    out_inv, _ = run.go('fixed_matched', matched_level=m_inv, ctrl_hp=ch)
    out_inv['condition'] = 'fixed_matched_inv'
    results.append(out_inv)
    print(f'  {"fixed_matched_inv":16s} ACC={out_inv["ACC"]:.3f} BWT={out_inv["BWT"]:+.3f} f={out_inv["mean_level_f"]:.3f}', flush=True)
    if a.with_fly:
        results.append(run_fly(Xtr, ytr, Xte, yte, stream, seed, hp, a.seed))
    print(f'  {"mod_novelty":16s} ACC={mod["ACC"]:.3f} BWT={mod["BWT"]:+.3f} f={mod["mean_level_f"]:.3f}')
    out = {'neuron': a.neuron, 'rule': a.rule, 'seed': a.seed, 'order_seed': a.order_seed,
           'hparams': hp, 'controller': ch, 'f_dense': run.f_mean[run.l_dense],
           'f_sparse': run.f_mean[run.l_sparse], 'f_matched': run.f_mean[matched],
           'results': results, 'elapsed_s': time.time() - t0}
    os.makedirs(os.path.join(RES, 'e33'), exist_ok=True)
    fn = os.path.join(RES, 'e33', f'{tag}_s{a.seed}_o{a.order_seed}.json')
    with open(fn, 'w') as f:
        json.dump(out, f)
    print('saved', fn, f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
