"""
E3.7 — czy zasada z E3.5/E3.8 przenosi się na sieć z WARSTWĄ UKRYTĄ uczoną trójczynnikowo?
(prereg.md sek. 6g; kryterium zapisane przed uruchomieniem)

Sieć: kod DG (stały, impulsowy, z results/codes/, poziom f wybierany przez regulator) →
warstwa ukryta (H = 500 jednostek, ReLU) → 10 wyjść. Uczone OBIE warstwy regułą typu AGREL
(Roelfsema & van Ooyen 2005): wyjście losowane z softmax, nagroda R = ±1, błąd predykcji
nagrody δ = R − R̄; zmiana wag wyjścia wybranej klasy ∝ δ·h; zmiana wag warstwy ukrytej
∝ δ · (sprzężenie zwrotne od wybranego wyjścia) · [h > 0] · x — sygnał „uwagi” od wybranego
wyjścia bramkuje plastyczność warstwy ukrytej, nagroda jest trzecim czynnikiem.

Dwa warianty (jedyna różnica):
  agrel      — δ może być ujemne → przy pomyłce wagi są osłabiane (jak R-STDP);
  agrel_pos  — tylko δ > 0 (nagroda) zmienia wagi → bez osłabiania (jak rgate).
W obu: skalowanie synaptyczne (stała norma wag każdej jednostki ukrytej i każdego wyjścia),
eksploracja ε = 0.05, β = 5.

E3.7b (prereg.md sek. 6i, 2026-10-28): skalowanie wag jednostki ukrytej wspólnej dla klas działa jak
osłabianie heterosynaptyczne, więc `agrel_pos` w praktyce osłabiał. Trzy nowe warianty:
  pos_bound    — tylko nagroda; W1 BEZ normalizacji, wagi przycięte do [−w_max, w_max]
                 (w_max = W1_BOUND / √n_in, czyli kilka razy początkowa skala); W2 jak w rgate
                 (normalizacja kolumny — kolumna należy do jednej klasy);
  pos_pool     — tylko nagroda; jednostki ukryte podzielone na 10 pul po H/10, wyjście k czyta
                 tylko swoją pulę (W2 stałe, blokowe), uczy się tylko pula wybranego wyjścia —
                 normalizacja W1 zostaje, ale nie ma już jednostek wspólnych dla klas;
  agrel_bound  — z osłabianiem (δ może być ujemne), W1 ograniczone jak w pos_bound (kontrola). Input = ĉ = c/‖c‖. Jednostki są „częstotliwościowe” (nie impulsowe)
— impulsowa jest warstwa DG.

Fazy:  --phase tune   (sieć 99, MNIST statycznie, walidacja): η z {0.01, 0.03, 0.1, 0.3}
       --phase pilot  (sieć 99, Split-MNIST, g = +1): a, b regulatora (5. i 95. percentyl N̄)
       --phase run    (sieci 0–4 × kolejności 0, 1): g ∈ {−1, 0, +1} + stałe f o tej samej średniej
f_gęsty / f_rzadki = 10% / 3% (jak dla R-STDP), bez strojenia.
Wyjście: results/e37/{hparams.json, pilot.json, run_{variant}_{neuron}_s{seed}_o{order}.json}
"""
from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import time

import numpy as np

from learning import Controller, uncertainty
from run_split import CODES, RES, nearest_by_f
from tasks import TASKS, load_mnist, task_stream

OUT = os.path.join(RES, 'e37')
H = 500
F_DENSE, F_SPARSE = 0.10, 0.03
ETAS = [0.01, 0.03, 0.1, 0.3]
W1_BOUND = 4.0
VARIANTS = ('agrel', 'agrel_pos', 'pos_bound', 'pos_pool', 'agrel_bound')


class HiddenNet:
    def __init__(self, n_in, variant, eta, seed, beta=5.0, eps=0.05):
        rng = np.random.default_rng(70_000 + seed)
        self.rng = rng
        self.W1 = rng.standard_normal((n_in, H)).astype(np.float32)
        self.W1 /= np.linalg.norm(self.W1, axis=0, keepdims=True)
        self.W2 = np.abs(rng.standard_normal((H, 10))).astype(np.float32)
        self.W2 /= np.linalg.norm(self.W2, axis=0, keepdims=True)
        self.variant, self.eta, self.beta, self.eps = variant, eta, beta, eps
        self.Rbar = 0.0
        self.w_max = W1_BOUND / math.sqrt(n_in)
        if variant == 'pos_pool':
            self.pool = np.repeat(np.arange(10), H // 10)
            self.W2 = (self.pool[:, None] == np.arange(10)[None, :]).astype(np.float32) / math.sqrt(H // 10)

    def forward(self, X):
        n = np.linalg.norm(X, axis=-1, keepdims=True)
        Xh = X / np.maximum(n, 1e-9)
        Hh = np.maximum(Xh @ self.W1, 0.0)
        return Xh, Hh, Hh @ self.W2

    def scores(self, X):
        return self.forward(X)[2]

    def predict(self, X):
        return np.argmax(self.forward(X)[2], -1)

    def step(self, x, y, eta_mult=1.0):
        xh, h, s = self.forward(x[None, :])
        xh, h, s = xh[0], h[0], s[0]
        z = self.beta * s
        p = np.exp(z - z.max())
        p /= p.sum()
        k = int(self.rng.integers(10)) if self.rng.random() < self.eps else int(self.rng.choice(10, p=p))
        R = 1.0 if k == y else -1.0
        d = R - self.Rbar
        self.Rbar += (R - self.Rbar) / 100.0
        if self.variant in ('agrel_pos', 'pos_bound', 'pos_pool'):
            d = max(d, 0.0) if R > 0 else 0.0
        if d != 0.0 and self.variant in ('pos_bound', 'agrel_bound', 'pos_pool'):
            return self._step_local(xh, h, k, self.eta * eta_mult * d), R, p
        if d != 0.0:
            lr = self.eta * eta_mult * d
            fb = self.W2[:, k].copy()                       # sprzężenie zwrotne od wybranego wyjścia
            col = self.W2[:, k] + lr * h
            self.W2[:, k] = col / max(float(np.linalg.norm(col)), 1e-9)
            g = fb * (h > 0)
            if g.any():
                idx = np.where(g != 0)[0]
                W = self.W1[:, idx] + lr * np.outer(xh, g[idx])
                self.W1[:, idx] = W / np.maximum(np.linalg.norm(W, axis=0, keepdims=True), 1e-9)
        return k, R, p

    def _step_local(self, xh, h, k, lr):
        """E3.7b: zmiany W1 bez skalowania wspólnego dla klas."""
        if self.variant == 'pos_pool':
            idx = np.where((self.pool == k) & (h > 0))[0]
            if len(idx):
                W = self.W1[:, idx] + lr * np.outer(xh, self.W2[idx, k])
                self.W1[:, idx] = W / np.maximum(np.linalg.norm(W, axis=0, keepdims=True), 1e-9)
            return k
        fb = self.W2[:, k].copy()
        col = np.maximum(self.W2[:, k] + lr * h, 0.0)
        self.W2[:, k] = col / max(float(np.linalg.norm(col)), 1e-9)
        idx = np.where((fb * (h > 0)) != 0)[0]
        if len(idx):
            self.W1[:, idx] = np.clip(self.W1[:, idx] + lr * np.outer(xh, fb[idx]), -self.w_max, self.w_max)
        return k


def update_json(path, key, value, merge=False):
    """Zapis klucza do wspólnego pliku JSON z blokadą (fazy tune/pilot mogą iść równolegle)."""
    with open(path + '.lock', 'w') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        d = json.load(open(path)) if os.path.exists(path) else {}
        if merge:
            d.setdefault(key, {}).update(value)
        else:
            d[key] = value
        json.dump(d, open(path, 'w'), indent=1)


class Data:
    def __init__(self, neuron, seed, order_seed):
        path = os.path.join(CODES, f'{neuron}_s{seed}.npy')
        self.meta = json.load(open(path.replace('.npy', '.json')))
        self.codes = np.load(path, mmap_mode='r')
        self.n_tr = self.meta['n_train']
        self.f_mean = self.meta['f_train_mean']
        _, self.ytr, _, self.yte = load_mnist(normalize=False)
        self.seed = 1000 * seed + order_seed
        self.stream = task_stream(self.ytr, self.seed)
        self.test_task = [np.where(np.isin(self.yte, t))[0] for t in TASKS]
        self._test = {}

    def test(self, l):
        if l not in self._test:
            self._test[l] = np.asarray(self.codes[self.n_tr:, l, :], np.float32)
        return self._test[l]


def train_split(D, variant, eta, level_fn, ctrl, eval_level, trace=None):
    net = HiddenNet(D.codes.shape[2], variant, eta, D.seed)
    acc = np.full((len(TASKS), len(TASKS)), np.nan)
    used = []
    for t, seq in D.stream:
        for i in seq:
            l = level_fn()
            _, R, p = net.step(np.asarray(D.codes[i, l, :], np.float32), int(D.ytr[i]))
            if ctrl is not None:
                ctrl.update(p, R)
                if trace is not None:
                    trace.append(ctrl.Nbar)
            used.append(l)
        pred = net.predict(D.test(eval_level))
        acc[t, :t + 1] = [float((pred[idx] == D.yte[idx]).mean()) for idx in D.test_task][:t + 1]
    T = len(TASKS) - 1
    return {'ACC': float(np.nanmean(acc[T])), 'BWT': float(np.mean([acc[T, j] - acc[j, j] for j in range(T)])),
            'mean_level_f': float(np.mean([D.f_mean[l] for l in used])), 'acc': acc.tolist()}


def phase_tune(a):
    D = Data(a.neuron, 99, 0)
    l = nearest_by_f(D.f_mean, math.sqrt(F_DENSE * F_SPARSE))
    order = np.random.default_rng(99).permutation(D.n_tr - 10_000)[:30_000]
    C = np.asarray(D.codes[:D.n_tr, l, :], np.float32)
    best = {}
    for variant in a.variants:
        scores = {}
        for eta in ETAS:
            net = HiddenNet(C.shape[1], variant, eta, 99)
            for i in order:
                net.step(C[i], int(D.ytr[i]))
            scores[eta] = float((net.predict(C[D.n_tr - 10_000:]) == D.ytr[D.n_tr - 10_000:]).mean())
        best[variant] = {'eta': max(scores, key=scores.get), 'val_acc': scores}
        print(a.neuron, variant, scores, flush=True)
    os.makedirs(OUT, exist_ok=True)
    update_json(os.path.join(OUT, 'hparams.json'), a.neuron, best, merge=True)


def phase_pilot(a):
    hp = json.load(open(os.path.join(OUT, 'hparams.json')))[a.neuron]
    D = Data(a.neuron, 99, 0)
    for variant in a.variants:
        ctrl = Controller(D.f_mean, F_DENSE, F_SPARSE, signal='unc', tau=50.0, a=0.0, b=1.0)
        tr = []
        train_split(D, variant, hp[variant]['eta'], ctrl.level, ctrl, nearest_by_f(D.f_mean, F_DENSE), tr)
        nb = np.array(tr[500:])
        ab = {'a': float(np.percentile(nb, 5)), 'b': float(np.percentile(nb, 95))}
        update_json(os.path.join(OUT, 'pilot.json'), f'{a.neuron}_{variant}', ab)
        print(a.neuron, variant, ab, flush=True)


def phase_run(a):
    t0 = time.time()
    hp = json.load(open(os.path.join(OUT, 'hparams.json')))[a.neuron][a.variant]
    pil = json.load(open(os.path.join(OUT, 'pilot.json')))[f'{a.neuron}_{a.variant}']
    D = Data(a.neuron, a.seed, a.order_seed)
    fm = D.f_mean
    l_c = nearest_by_f(fm, math.sqrt(F_DENSE * F_SPARSE))
    res = [dict(train_split(D, a.variant, hp['eta'], lambda: l_c, None, l_c), g=0.0, kind='fixed')]
    for g, (f_rest, f_novel) in ((1.0, (F_DENSE, F_SPARSE)), (-1.0, (F_SPARSE, F_DENSE))):
        ctrl = Controller(fm, f_rest, f_novel, signal='unc', tau=50.0, a=pil['a'], b=pil['b'])
        mod = train_split(D, a.variant, hp['eta'], ctrl.level, ctrl, nearest_by_f(fm, f_rest))
        lm = nearest_by_f(fm, mod['mean_level_f'])
        fix = train_split(D, a.variant, hp['eta'], lambda: lm, None, lm)
        res += [dict(mod, g=g, kind='mod'), dict(fix, g=g, kind='matched')]
        print(f'  {a.variant} g={g:+.0f} Δ={mod["BWT"] - fix["BWT"]:+.3f} (ACC {mod["ACC"]:.3f} vs {fix["ACC"]:.3f})', flush=True)
    fn = os.path.join(OUT, f'run_{a.variant}_{a.neuron}_s{a.seed}_o{a.order_seed}.json')
    json.dump({'neuron': a.neuron, 'variant': a.variant, 'seed': a.seed, 'order_seed': a.order_seed,
               'eta': hp['eta'], 'pilot': pil, 'results': res, 'elapsed_s': time.time() - t0}, open(fn, 'w'))
    print('saved', fn, f'{time.time() - t0:.0f}s')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['tune', 'pilot', 'run'], required=True)
    ap.add_argument('--neuron', choices=['izh', 'lif'], required=True)
    ap.add_argument('--variant', choices=VARIANTS, default='agrel')
    ap.add_argument('--variants', nargs='+', choices=VARIANTS, default=['agrel', 'agrel_pos'],
                    help='warianty dla faz tune i pilot')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--order-seed', type=int, default=0)
    a = ap.parse_args()
    {'tune': phase_tune, 'pilot': phase_pilot, 'run': phase_run}[a.phase](a)


if __name__ == '__main__':
    main()
