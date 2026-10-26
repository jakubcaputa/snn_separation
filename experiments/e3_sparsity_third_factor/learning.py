"""
E3 — czytniki i regulator K. Wszystko na gotowych kodach DG (liczby impulsów).

Czytniki (decyzja Q2: oba + sufit):
  rstdp — czynnik trzeci B, reguła trójczynnikowa z wartością odniesienia nagrody
          (REINFORCE, Williams 1992; wersja impulsowa: Florian 2007). Czytnik to 10
          neuronów wyjściowych; odpala jeden, losowany z p = softmax(β·s), s = Wᵀ ĉ,
          ĉ = c/‖c‖ (pre: liczby impulsów neuronów DG). Ślad uprawnienia
          e_ij = ĉ_i · ([j odpalił] − p_j)  (post minus jego oczekiwanie),
          nagroda R = +1 / −1, wartość odniesienia R̄ (średnia krocząca):
          Δw_ij = η · (R − R̄) · e_ij.  Synapsa od cichego neuronu DG (ĉ_i = 0) się nie zmienia.
          Pierwsza wersja (wzmacnianie tylko zwycięzcy, bez R̄) uczyła się słabo:
          29–45% na czystych kodach — patrz README, E3.0.
  delta — reguła delta (NLMS) z nauczycielem: Δw = η (t − y) cᵀ / (‖c‖² + ε).
  fly   — reguła FlyModel: w[:, y] += β·φ (tylko klasa docelowa, bez osłabiania).

Regulator (czynnik trzeci A): nowość N → wygładzone N̄ → n ∈ [0,1] → docelowe f →
najbliższy poziom z F_LEVELS. Kierunek +1: nowość → rzadziej; −1: nowość → gęściej.
"""
from __future__ import annotations

import math

import numpy as np


class Readout:
    def __init__(self, n_in: int, rule: str, eta: float, seed: int, eps: float = 0.02):
        self.rule = rule
        self.eta = eta
        self.eps = eps
        self.rng = np.random.default_rng(50_000 + seed)
        self.W = np.zeros((n_in, 10), np.float32)
        self.Rbar = 0.0
        self.beta = 1.0
        if rule == 'rgate':
            # start: małe losowe wagi o jednostkowej normie każdej kolumny; ostrzejszy
            # wybór (wyniki to kosinusy w [0, 1]) i eksploracja ε
            W = self.rng.uniform(0.0, 1.0, (n_in, 10)).astype(np.float32)
            self.W = W / np.linalg.norm(W, axis=0, keepdims=True)
            self.beta = 20.0
            self.eps = max(eps, 0.1)

    def scores(self, X: np.ndarray) -> np.ndarray:
        if self.rule in ('rstdp', 'rgate'):
            n = np.linalg.norm(X, axis=-1, keepdims=True)
            return (X / np.maximum(n, 1e-9)) @ self.W
        return X @ self.W

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.scores(X), axis=-1)

    def step(self, x: np.ndarray, y: int, eta_mult: float = 1.0):
        """Jedna prezentacja. Zwraca (odpowiedź, nagroda R, wyniki s)."""
        if self.rule == 'rgate':
            # trójczynnikowa BEZ osłabiania (dodane 2026-10-22, E3.5): odpowiedź losowana
            # z softmax jak w rstdp, ale nagroda bramkuje wyłącznie wzmacnianie synaps
            # aktywnych neuronów DG do wybranego wyjścia, gdy było poprawne
            # (Δw_{·j*} = η·[R = +1]·ĉ, potem normalizacja kolumny). Błąd nie zmienia nic —
            # jak dopamina bramkująca tylko LTP; odpowiednik reguły FlyModelu bez etykiety.
            # Wagi innych wyjść nigdy się nie zmieniają.
            nrm = float(np.linalg.norm(x))
            xh = x / nrm if nrm > 0 else x
            s = xh @ self.W
            z = self.beta * s
            p = np.exp(z - z.max())
            p /= p.sum()
            if self.rng.random() < self.eps:
                win = int(self.rng.integers(10))
            else:
                win = int(self.rng.choice(10, p=p))
            R = 1.0 if win == y else -1.0
            if R > 0:
                col = self.W[:, win] + (self.eta * eta_mult) * xh
                # skalowanie synaptyczne: stała norma wag wyjścia (homeostaza), żeby
                # często nagradzane wyjście nie rosło bez końca i nie wygrywało wszystkiego
                self.W[:, win] = col / max(float(np.linalg.norm(col)), 1e-9)
            return win, R, p
        if self.rule == 'rstdp':
            nrm = float(np.linalg.norm(x))
            xh = x / nrm if nrm > 0 else x
            s = xh @ self.W
            z = self.beta * s
            p = np.exp(z - z.max())
            p /= p.sum()
            win = int(self.rng.choice(10, p=p))
            R = 1.0 if win == y else -1.0
            post = -p
            post[win] += 1.0
            self.W += (self.eta * eta_mult * (R - self.Rbar)) * np.outer(xh, post)
            self.Rbar += (R - self.Rbar) / 100.0
            return win, R, p
        s = x @ self.W
        pred = int(np.argmax(s))
        R = 1.0 if pred == y else -1.0
        if self.rule == 'delta':
            t = np.zeros(10, np.float32)
            t[y] = 1.0
            nrm = float(x @ x)
            if nrm > 0:
                self.W += (self.eta * eta_mult / (nrm + 1e-6)) * np.outer(x, t - s)
        elif self.rule == 'fly':
            self.W[:, y] += self.eta * eta_mult * x
        else:
            raise ValueError(self.rule)
        return pred, R, s


def uncertainty(s: np.ndarray) -> float:
    """N_unc = 1 − (s₁ − s₂)/|s₁|: 0 przy pewnej odpowiedzi, 1 przy remisie."""
    top = np.partition(s, -2)[-2:]
    s2, s1 = float(top[0]), float(top[1])
    if s1 <= s2:
        return 1.0
    return float(np.clip(1.0 - (s1 - s2) / (abs(s1) + 1e-9), 0.0, 1.0))


class Controller:
    """
    signal: 'unc' (niepewność czytnika) albo 'rpe' (|R − R̄|).
    n = clip((N̄ − a)/(b − a), 0, 1); f = f_rest + (f_novel − f_rest)·n, w skali log.
    a, b ustalamy w pilocie na osobnym ziarnie i zamrażamy (README sek. 6).
    """

    def __init__(self, levels, f_rest: float, f_novel: float, signal: str = 'unc',
                 tau: float = 50.0, a: float = 0.0, b: float = 1.0, n0: float = 1.0):
        self.levels = np.asarray(levels)
        self.log_levels = np.log(self.levels)
        self.f_rest, self.f_novel = f_rest, f_novel
        self.signal, self.tau, self.a, self.b = signal, tau, a, b
        self.Nbar = n0 * (b - a) + a       # start: „wszystko jest nowe”
        self.Rbar = 0.0

    def n(self) -> float:
        return float(np.clip((self.Nbar - self.a) / max(self.b - self.a, 1e-9), 0.0, 1.0))

    def level(self, n: float | None = None) -> int:
        n = self.n() if n is None else n
        lf = math.log(self.f_rest) + (math.log(self.f_novel) - math.log(self.f_rest)) * n
        return int(np.argmin(np.abs(self.log_levels - lf)))

    def update(self, s: np.ndarray, R: float):
        if self.signal == 'unc':
            N = uncertainty(s)
        elif self.signal == 'rpe':
            N = abs(R - self.Rbar)
        else:
            raise ValueError(self.signal)
        self.Rbar += (R - self.Rbar) / self.tau
        self.Nbar += (N - self.Nbar) / self.tau
        return N


def kwta_codes(X: np.ndarray, M: np.ndarray, f: float) -> np.ndarray:
    """FlyModel: napęd neuronu = suma jasności jego pikseli (X @ M, M = krotności
    połączeń piksel→neuron); aktywne top-f neuronów per obraz, aktywność = napęd.
    Bez impulsów — jak w oryginale."""
    drive = X @ M                                   # [B, N]
    k = max(1, int(round(f * drive.shape[1])))
    thr = np.partition(drive, -k, axis=1)[:, -k][:, None]
    out = np.where(drive >= thr, drive, 0.0).astype(np.float32)
    return out


def pearson_mean(A: np.ndarray, B: np.ndarray) -> float:
    """Średnia korelacja Pearsona między wierszami A[i] i B[i] (pary obrazów)."""
    A = A.astype(np.float64)
    B = B.astype(np.float64)
    A = A - A.mean(1, keepdims=True)
    B = B - B.mean(1, keepdims=True)
    den = np.sqrt((A * A).sum(1) * (B * B).sum(1))
    ok = den > 0
    r = np.zeros(len(A))
    r[ok] = (A[ok] * B[ok]).sum(1) / den[ok]
    return float(r.mean())


def logistic_ceiling(Xtr, ytr, Xte, yte, epochs: int = 5, seed: int = 0) -> float:
    """Sufit: wieloklasowa regresja logistyczna (Adam, mini-batch) na tych samych kodach."""
    import torch
    torch.manual_seed(seed)
    Xtr_t = torch.from_numpy(Xtr.astype(np.float32))
    Xte_t = torch.from_numpy(Xte.astype(np.float32))
    mu, sd = Xtr_t.mean(0), Xtr_t.std(0) + 1e-3
    Xtr_t, Xte_t = (Xtr_t - mu) / sd, (Xte_t - mu) / sd
    ytr_t = torch.from_numpy(ytr)
    lin = torch.nn.Linear(Xtr.shape[1], 10)
    opt = torch.optim.Adam(lin.parameters(), lr=1e-3, weight_decay=1e-4)
    n = len(Xtr_t)
    for _ in range(epochs):
        perm = torch.randperm(n)
        for s in range(0, n, 256):
            idx = perm[s:s + 256]
            loss = torch.nn.functional.cross_entropy(lin(Xtr_t[idx]), ytr_t[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
    with torch.no_grad():
        return float((lin(Xte_t).argmax(1).numpy() == yte).mean())
