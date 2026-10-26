"""
E3 — warstwa „DG” w PyTorch: stała, losowa ekspansja pikseli na N_DG neuronów
impulsowych z tonicznym hamowaniem K (jeden skalar dla całej warstwy).

Dwa typy neuronu (decyzja Q1):
  izh — Izhikevich z parametrami GC z dg_core (a,b,c,d = 0.02, 0.2, −65, 6),
        K wchodzi wprost do równania napięcia, jak w dg_core/circuit.py:
        dv/dt = 0.04 v² + 5 v + 140 − u + g_ex − g_in − K
  lif — LIF: dv/dt = (−v + g_ex − g_in − K) / τ_m, próg θ, reset 0.

Opcjonalnie pula FS (Izhikevich FS z dg_core) daje hamowanie FAZOWE w pętli
GC → FS → GC (tylko E3.2). Bez opóźnień synaptycznych i bez gałęzi PP→FS —
to uproszczenie względem dg_core, opisane w README.

Kluczowa własność: symulujemy WIELE poziomów K naraz na TYCH SAMYCH impulsach
wejściowych (stan ma kształt [B, L, N]). Dzięki temu kody dla różnych K różnią się
tylko progiem, a nie realizacją szumu Poissona — przy hamowaniu tonicznym kod
rzadszy jest wtedy (prawie) podzbiorem gęstszego.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, asdict

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..')))

from dg_core.params import (  # noqa: E402  — jedno źródło parametrów neuronów
    A_GC, B_GC, C_GC, D_GC, A_FS, B_FS, C_FS, D_FS,
    TAU_EX_GC, TAU_IN_GC, TAU_EX_FS,
)


@dataclass(frozen=True)
class LayerCfg:
    neuron: str = 'izh'          # 'izh' | 'lif'
    n_dg: int = 2000
    fan_in: int = 30             # losowe piksele na neuron (z puli „żywych” pikseli)
    w_pp: float = 1.0            # mV na impuls wejściowy (E3.0: 200 Hz × 1 mV zamiast 50 Hz × 4 mV — ten sam średni napęd, mniej szumu)
    rate_max: float = 200.0      # Hz dla piksela o jasności 1 (po normalizacji wejścia)
    T_ms: float = 100.0
    dt: float = 0.1              # ms, jak DT_MS w dg_core
    tau_ex: float = TAU_EX_GC
    refractory_ms: float = 2.0
    # LIF
    lif_tau_m: float = 20.0
    lif_theta: float = 10.0
    # pula FS — hamowanie fazowe (E3.2); w_fs_gc = 0 wyłącza pulę całkowicie
    n_fs: int = 20
    p_gc_fs: float = 0.40
    w_gc_fs: float = 10.0
    p_fs_gc: float = 0.50
    w_fs_gc: float = 0.0
    k_fs: float = 5.0

    def to_dict(self):
        return asdict(self)


def live_pixels(X_train: np.ndarray, min_mean: float = 0.05) -> np.ndarray:
    """Piksele, które w ogóle bywają jasne. Brzegi obrazka MNIST są zawsze czarne;
    neuron patrzący tylko na nie nigdy by nie odpalił, więc ich nie losujemy."""
    return np.where(X_train.mean(0) > min_mean)[0].astype(np.int64)


def make_connectivity(cfg: LayerCfg, pool: np.ndarray, seed: int) -> dict:
    rng = np.random.default_rng(10_000 + seed)
    fan = rng.choice(pool, size=(cfg.n_dg, cfg.fan_in), replace=True)
    M = np.zeros((784, cfg.n_dg), np.float32)        # krotność połączenia piksel→neuron
    np.add.at(M, (fan, np.repeat(np.arange(cfg.n_dg)[:, None], cfg.fan_in, 1)), 1.0)
    C_gc_fs = (rng.random((cfg.n_dg, cfg.n_fs)) < cfg.p_gc_fs).astype(np.float32)
    C_fs_gc = (rng.random((cfg.n_fs, cfg.n_dg)) < cfg.p_fs_gc).astype(np.float32)
    return {'fan': fan, 'M': M, 'C_gc_fs': C_gc_fs, 'C_fs_gc': C_fs_gc}


class DGLayer:
    """Symulator warstwy na GPU/CPU. `run(X, K_levels)` → liczby impulsów [B, L, N]."""

    def __init__(self, cfg: LayerCfg, conn: dict, device: str = 'cpu'):
        self.cfg = cfg
        self.dev = torch.device(device)
        self.M = torch.from_numpy(conn['M']).to(self.dev)
        self.C_gc_fs = torch.from_numpy(conn['C_gc_fs']).to(self.dev)
        self.C_fs_gc = torch.from_numpy(conn['C_fs_gc']).to(self.dev)

    @torch.no_grad()
    def run(self, X: torch.Tensor, K_levels, gen: torch.Generator | None = None,
            input_spikes: torch.Tensor | None = None) -> torch.Tensor:
        """
        X: [B, 784] jasności w [0, 1].
        K_levels: lista / tensor L wartości K (wspólne wejście dla wszystkich).
        input_spikes: opcjonalnie gotowe impulsy [steps, B, 784] (testy zgodności).
        Zwraca uint8 [B, L, N] — liczbę impulsów każdego neuronu w oknie T.
        """
        c = self.cfg
        dev = self.dev
        X = X.to(dev, torch.float32)
        B = X.shape[0]
        K = torch.as_tensor(K_levels, dtype=torch.float32, device=dev).view(1, -1, 1)
        L, N = K.shape[1], c.n_dg
        steps = int(round(c.T_ms / c.dt))
        p_spk = X * (c.rate_max * c.dt / 1000.0)               # [B, 784]

        dec_ex = 1.0 - c.dt / c.tau_ex                          # Euler, jak Brian2 'euler'
        dec_in = 1.0 - c.dt / TAU_IN_GC
        dec_fs = 1.0 - c.dt / TAU_EX_FS
        ref_steps = int(round(c.refractory_ms / c.dt))
        use_fs = c.w_fs_gc > 0.0

        if c.neuron == 'izh':
            v = torch.full((B, L, N), -70.0, device=dev)
            u = B_GC * v
        elif c.neuron == 'lif':
            v = torch.zeros((B, L, N), device=dev)
            u = None
        else:
            raise ValueError(c.neuron)
        g_ex = torch.zeros((B, 1, N), device=dev)              # wejście wspólne dla poziomów
        g_in = torch.zeros((B, L, N), device=dev) if use_fs else None
        ref = torch.zeros((B, L, N), dtype=torch.int16, device=dev)
        count = torch.zeros((B, L, N), dtype=torch.int16, device=dev)
        if use_fs:
            vf = torch.full((B, L, c.n_fs), -70.0, device=dev)
            uf = B_FS * vf
            gf = torch.zeros((B, L, c.n_fs), device=dev)
            reff = torch.zeros((B, L, c.n_fs), dtype=torch.int16, device=dev)

        for t in range(steps):
            # ── aktualizacja stanu (Euler, wszystkie zmienne ze starych wartości) ──
            inh = g_in if use_fs else 0.0
            free = ref <= 0
            if c.neuron == 'izh':
                dv = 0.04 * v * v + 5.0 * v + 140.0 - u + g_ex - inh - K
                du = A_GC * (B_GC * v - u)
                v = torch.where(free, v + c.dt * dv, v)
                u = u + c.dt * du
            else:
                dv = (-v + g_ex - inh - K) / c.lif_tau_m
                v = torch.where(free, v + c.dt * dv, v)
            g_ex = g_ex * dec_ex
            if use_fs:
                g_in = g_in * dec_in
                dvf = 0.04 * vf * vf + 5.0 * vf + 140.0 - uf + gf - c.k_fs
                duf = A_FS * (B_FS * vf - uf)
                vf = torch.where(reff <= 0, vf + c.dt * dvf, vf)
                uf = uf + c.dt * duf
                gf = gf * dec_fs
            ref = ref - 1

            # ── próg i reset ──
            if c.neuron == 'izh':
                spk = v >= 30.0
                v = torch.where(spk, torch.full_like(v, C_GC), v)
                u = torch.where(spk, u + D_GC, u)
            else:
                spk = v >= c.lif_theta
                v = torch.where(spk, torch.zeros_like(v), v)
            # Brian2: refrakcja trwa, dopóki t − t_spike < 2 ms → 19 zablokowanych kroków
            ref = torch.where(spk, torch.full_like(ref, ref_steps - 1), ref)
            count += spk.to(torch.int16)

            if use_fs:
                spkf = vf >= 30.0
                vf = torch.where(spkf, torch.full_like(vf, C_FS), vf)
                uf = torch.where(spkf, uf + D_FS, uf)
                reff = torch.where(spkf, torch.full_like(reff, int(round(1.0 / c.dt)) - 1), reff - 1)
                gf = gf + c.w_gc_fs * (spk.float() @ self.C_gc_fs)
                g_in = g_in + c.w_fs_gc * (spkf.float() @ self.C_fs_gc)

            # ── synapsy wejściowe PP → DG ──
            if input_spikes is not None:
                s_in = input_spikes[t].to(dev, torch.float32)
            else:
                s_in = (torch.rand(p_spk.shape, generator=gen, device=dev) < p_spk).float()
            g_ex = g_ex + c.w_pp * (s_in @ self.M).unsqueeze(1)

        return count.clamp_(max=255).to(torch.uint8)


def active_fraction(counts: torch.Tensor | np.ndarray):
    """f per obraz i poziom: odsetek neuronów z ≥ 1 impulsem. counts [B, L, N] → [B, L]."""
    if isinstance(counts, np.ndarray):
        return (counts > 0).mean(-1)
    return (counts > 0).float().mean(-1)


def pick_device() -> str:
    return 'cuda' if torch.cuda.is_available() else 'cpu'


def make_generator(device: str, seed: int) -> torch.Generator:
    g = torch.Generator(device=device)
    g.manual_seed(int(seed))
    return g


F_LEVELS = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12,
            0.14, 0.17, 0.20, 0.25, 0.30, 0.40, 0.50]


def nearest_level(f: float, levels=F_LEVELS) -> int:
    """Indeks poziomu najbliższego w skali log."""
    lf = math.log(max(f, 1e-6))
    return int(np.argmin([abs(lf - math.log(x)) for x in levels]))
