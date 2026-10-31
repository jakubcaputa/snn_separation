"""
E3.6 — H-E3c na zadaniu separacji wzorców z dg_core (prereg.md sek. 6c).

Model DG bez zmian: dg_core.circuit.simulate (Brian2, 200 GC + FS + HMC, parametry
domyślne), K_GC ustawiane jak w E1′ (bisekcja do zadanego odsetka aktywnych GC).
Zadanie jak w 1A (readout_deferred/run_classification.py): 10 prototypów o wzajemnym
podobieństwie R_in, p_active = 0.25, szum bit-flip 0.2; tu uczone sekwencyjnie
parami (0/1 → 2/3 → … → 8/9), czytnik 10-klasowy na częstotliwościach GC.

Faza `codes`: częstotliwości GC dla każdej próby przy 7 poziomach K (ta sama
realizacja Poissona wejścia dla wszystkich poziomów). Faza `learn`: dawka–odpowiedź
g ∈ {−1, −0.5, 0, +0.5, +1} z kontrolą stałego f o tej samej średniej (jak run_dose).
Faza `pilot` (sieć 99): a, b regulatora z przebiegu g = +1 (5. i 95. percentyl N̄).

Użycie:
  python run_dgtask.py --phase codes --r-in 0.75 --seed 0 --jobs 16
  python run_dgtask.py --phase pilot --r-in 0.75 --rule rstdp
  python run_dgtask.py --phase learn --r-in 0.75 --seed 0 --order-seed 0 --rule rstdp
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..')))

from learning import Controller  # noqa: E402
from run_dose import train  # noqa: E402

OUT = os.path.join(HERE, 'results', 'e36')
REGIME = 'invivo'          # 'exvivo' → results/e36x/, model skalibrowany do skrawka (sek. 6c, 12e)
F_LEVELS_EXVIVO = [0.03, 0.05, 0.07, 0.10, 0.14, 0.20]   # ~25% GC dostaje wejście → 30% nieosiągalne
VOLLEY_RATE_HZ = 10.0
F_LEVELS6 = [0.03, 0.05, 0.07, 0.10, 0.14, 0.20, 0.30]
N_CLASSES, N_TRAIN, N_TEST = 10, 100, 50
P_ACTIVE, NOISE = 0.25, 0.20
F_C, R_SPAN = 0.10, 4.0            # f_gęsty = 20%, f_rzadki = 5% — ustalone z góry
ETA = {'rstdp': 0.25, 'delta': 0.05, 'rgate': 0.05}   # jak dla MNIST (izh), bez strojenia
EPOCHS_PER_TASK = 3
TAU = 20.0


def _tag(r_in, seed):
    return f'rin{r_in:.2f}_s{seed}'


# ── faza codes ───────────────────────────────────────────────────────────────
def _sim_job(args):
    from dg_core import DGConfig, make_connectivity, make_input_spikes, simulate
    trial, ti, Ks, seed, regime = args
    if regime == 'exvivo':
        from dg_core.exvivo import exvivo_best_config, pattern_volley_input, poisson_train
        cfg = exvivo_best_config()
        conn = make_connectivity(cfg, seed=seed)
        pulses = poisson_train(VOLLEY_RATE_HZ, cfg.T_ms, np.random.default_rng(10_000 * (seed + 1) + ti))
        idx, ts = pattern_volley_input(cfg, trial, pulses)
        from brian2 import seed as bseed
        bseed(20_000 * (seed + 1) + ti)
    else:
        cfg = DGConfig()
        conn = make_connectivity(cfg, seed=seed)
        idx, ts = make_input_spikes(trial, cfg, seed=10_000 * (seed + 1) + ti)
    return np.stack([simulate(replace(cfg, K_GC=float(K)), idx, ts, conn)['gc_rates'] for K in Ks]).astype(np.float32)


def _exvivo_k_for_f(args):
    """Bisekcja K_GC do zadanego odsetka aktywnych GC (rate > 0.5 Hz) w reżimie salw,
    średnio na 3 prototypach, z ustalonymi pociągami salw i ziarnem Brian2."""
    from dg_core import make_connectivity, simulate
    from dg_core.exvivo import exvivo_best_config, pattern_volley_input, poisson_train
    from brian2 import seed as bseed
    f_target, protos, seed = args
    cfg = exvivo_best_config()
    conn = make_connectivity(cfg, seed=seed)
    inputs = [pattern_volley_input(cfg, p, poisson_train(VOLLEY_RATE_HZ, cfg.T_ms, np.random.default_rng(900 + c)))
              for c, p in enumerate(protos)]
    lo, hi = -10.0, 40.0
    for _ in range(12):
        mid = 0.5 * (lo + hi)
        fs = []
        for c, (idx, ts) in enumerate(inputs):
            bseed(777 + c)
            fs.append(float((simulate(replace(cfg, K_GC=mid), idx, ts, conn)['gc_rates'] > 0.5).mean()))
        lo, hi = (mid, hi) if np.mean(fs) > f_target else (lo, mid)
    return 0.5 * (lo + hi)


def phase_codes(a):
    from dg_core import DGConfig, make_class_trials, make_connectivity
    from dg_core.calibrate import solve_k_gc_for_active_fraction
    t0 = time.time()
    cfg = DGConfig()
    conn = make_connectivity(cfg, seed=a.seed)
    trials, labels, protos, r_meas = make_class_trials(cfg.N_GC, N_CLASSES, N_TRAIN + N_TEST, a.r_in,
                                                       P_ACTIVE, NOISE, seed=7 + 100 * a.seed)
    levels = F_LEVELS_EXVIVO if REGIME == 'exvivo' else F_LEVELS6
    # Wyniki pośrednie (K i każda próba osobno) — przerwane zadanie (limit 1 h na plgrid-now)
    # wznawia się od miejsca przerwania przy ponownym uruchomieniu tej samej komendy.
    cache = os.path.join(OUT, f'cache_{_tag(a.r_in, a.seed)}')
    os.makedirs(cache, exist_ok=True)
    final = os.path.join(OUT, f'codes_{_tag(a.r_in, a.seed)}.npy')
    if os.path.exists(final):
        print('już policzone:', final)
        return
    k_file = os.path.join(cache, 'K.json')
    if os.path.exists(k_file):
        Ks = json.load(open(k_file))
    elif REGIME == 'exvivo':
        with Pool(min(a.jobs, len(levels))) as p:
            Ks = p.map(_exvivo_k_for_f, [(f, protos[:3], a.seed) for f in levels])
    else:
        # K dla każdego poziomu: średnia z bisekcji na 3 prototypach
        Ks = []
        for f in levels:
            ks = [solve_k_gc_for_active_fraction(cfg, conn, protos[c], f, seed=a.seed, k_lo=-10.0, k_hi=30.0)[0]
                  for c in range(3)]
            Ks.append(float(np.mean(ks)))
    json.dump([float(k) for k in Ks], open(k_file, 'w'))
    print('K(f):', dict(zip(levels, np.round(Ks, 2))), f'{time.time() - t0:.0f}s', flush=True)
    todo = [i for i in range(len(trials)) if not os.path.exists(os.path.join(cache, f'trial_{i}.npy'))]
    print(f'próby do policzenia: {len(todo)} z {len(trials)}', flush=True)
    jobs = [(trials[i], i, Ks, a.seed, REGIME) for i in todo]
    with Pool(a.jobs) as p:
        for i, r in zip(todo, p.imap(_sim_job, jobs, chunksize=2)):
            np.save(os.path.join(cache, f'trial_{i}.npy'), r)
    rates = np.stack([np.load(os.path.join(cache, f'trial_{i}.npy')) for i in range(len(trials))])
    # podział: pierwsze N_TRAIN prób każdej klasy → trening, reszta → test
    per = N_TRAIN + N_TEST
    tr = np.concatenate([np.arange(c * per, c * per + N_TRAIN) for c in range(N_CLASSES)])
    te = np.concatenate([np.arange(c * per + N_TRAIN, (c + 1) * per) for c in range(N_CLASSES)])
    order = np.concatenate([tr, te])
    os.makedirs(OUT, exist_ok=True)
    np.save(os.path.join(OUT, f'codes_{_tag(a.r_in, a.seed)}.npy'), rates[order])
    f_mean = [float((rates[tr][:, l] > 0.5).mean()) for l in range(len(Ks))]
    meta = {'r_in': a.r_in, 'r_in_measured': float(r_meas), 'seed': a.seed, 'K': Ks, 'f_levels': levels, 'regime': REGIME,
            'f_train_mean': f_mean, 'n_train': len(tr), 'n_test': len(te),
            'labels': labels[order].tolist(), 'elapsed_s': time.time() - t0}
    with open(os.path.join(OUT, f'codes_{_tag(a.r_in, a.seed)}.json'), 'w') as f:
        json.dump(meta, f)
    print('f zmierzone (trening):', np.round(f_mean, 3), f'{time.time() - t0:.0f}s')


# ── faza learn / pilot ───────────────────────────────────────────────────────
def _load(r_in, seed):
    base = os.path.join(OUT, f'codes_{_tag(r_in, seed)}')
    with open(base + '.json') as f:
        meta = json.load(f)
    codes = np.load(base + '.npy', mmap_mode='r')
    y = np.array(meta['labels'])
    return codes, meta, y[:meta['n_train']], y[meta['n_train']:]


def _nearest(f_mean, f):
    return int(np.argmin([abs(math.log(max(x, 1e-6)) - math.log(f)) for x in f_mean]))


def _stream(ytr, seed):
    from tasks import task_stream
    return task_stream(ytr, seed, EPOCHS_PER_TASK)


def phase_pilot(a):
    codes, meta, ytr, yte = _load(a.r_in, 99)
    f_mean = meta['f_train_mean']
    ctrl = Controller(f_mean, F_C * R_SPAN ** 0.5, F_C * R_SPAN ** -0.5, signal='unc', tau=TAU, a=0.0, b=1.0)
    trace = []

    class Tracked(Controller):
        pass
    orig = ctrl.update

    def upd(s, R):
        out = orig(s, R)
        trace.append(ctrl.Nbar)
        return out
    ctrl.update = upd
    train(codes, meta['n_train'], ytr, yte, _stream(ytr, 99000), a.rule, ETA[a.rule], 99000,
          ctrl.level, ctrl, f_mean, _nearest(f_mean, F_C * R_SPAN ** 0.5))
    nb = np.array(trace[100:])
    res = {'a': float(np.percentile(nb, 5)), 'b': float(np.percentile(nb, 95))}
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'pilot.json')
    allp = json.load(open(path)) if os.path.exists(path) else {}
    allp[f'rin{a.r_in:.2f}_{a.rule}'] = res
    json.dump(allp, open(path, 'w'), indent=1)
    print('pilot', a.r_in, a.rule, res)


def phase_learn(a):
    t0 = time.time()
    codes, meta, ytr, yte = _load(a.r_in, a.seed)
    f_mean = meta['f_train_mean']
    pil = json.load(open(os.path.join(OUT, 'pilot.json')))[f'rin{a.r_in:.2f}_{a.rule}']
    seed = 1000 * a.seed + a.order_seed
    stream = _stream(ytr, seed)
    n_tr = meta['n_train']
    l_c = _nearest(f_mean, F_C)
    results = []
    res = train(codes, n_tr, ytr, yte, stream, a.rule, ETA[a.rule], seed, lambda: l_c, None, f_mean, l_c)
    res.update(g=0.0, kind='fixed')
    results.append(res)
    for g in (-1.0, -0.5, 0.5, 1.0):
        f_rest, f_novel = F_C * R_SPAN ** (g / 2), F_C * R_SPAN ** (-g / 2)
        ctrl = Controller(f_mean, f_rest, f_novel, signal='unc', tau=TAU, a=pil['a'], b=pil['b'])
        mod = train(codes, n_tr, ytr, yte, stream, a.rule, ETA[a.rule], seed, ctrl.level, ctrl, f_mean,
                    _nearest(f_mean, f_rest))
        mod.update(g=g, kind='mod')
        lm = _nearest(f_mean, mod['mean_level_f'])
        fix = train(codes, n_tr, ytr, yte, stream, a.rule, ETA[a.rule], seed, lambda: lm, None, f_mean, lm)
        fix.update(g=g, kind='matched')
        results += [mod, fix]
        print(f'  g={g:+.1f} Δ={mod["BWT"] - fix["BWT"]:+.3f}  (mod ACC {mod["ACC"]:.3f}, matched ACC {fix["ACC"]:.3f})', flush=True)
    fn = os.path.join(OUT, f'learn_{_tag(a.r_in, a.seed)}_o{a.order_seed}_{a.rule}.json')
    json.dump({'r_in': a.r_in, 'seed': a.seed, 'order_seed': a.order_seed, 'rule': a.rule,
               'pilot': pil, 'results': results, 'elapsed_s': time.time() - t0}, open(fn, 'w'))
    print('saved', fn, f'{time.time() - t0:.0f}s')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['codes', 'pilot', 'learn'], required=True)
    ap.add_argument('--r-in', type=float, required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    ap.add_argument('--rule', choices=['rstdp', 'delta', 'rgate'], default='rstdp')
    ap.add_argument('--jobs', type=int, default=16)
    ap.add_argument('--regime', choices=['invivo', 'exvivo'], default='invivo',
                    help='exvivo: model skalibrowany do skrawka (salwy, wagi z siatki v3) → results/e36x/')
    a = ap.parse_args()
    global REGIME, OUT
    REGIME = a.regime
    if a.regime == 'exvivo':
        OUT = os.path.join(HERE, 'results', 'e36x')
    {'codes': phase_codes, 'pilot': phase_pilot, 'learn': phase_learn}[a.phase](a)


if __name__ == '__main__':
    main()
