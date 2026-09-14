"""
dg_core/circuit.py — obwód DG (GC / FS / HMC, Izhikevich) bez Streamlita.

Port `simulate_brian` z interactive_dg.py do postaci nadającej się do sweepów
wsadowych: bez cache Streamlita, bez rysowania, sterowany przez DGConfig.
Model (równania, kanały synaptyczne, opóźnienia) jest identyczny — dzięki temu
wyniki eksperymentów odpowiadają temu, co użytkownik widzi w narzędziu.

Zachowany podział na osobne kanały synaptyczne (g_ex / g_ex2 / g_ex3), bo z nich
liczymy wkład napięciowy każdej ścieżki (obserwowalność — kierunek 4).
"""

from __future__ import annotations

import numpy as np
from brian2 import (
    BrianLogger, Network, NeuronGroup, SpikeGeneratorGroup, SpikeMonitor,
    StateMonitor, Synapses, defaultclock, ms, mV, prefs, start_scope,
)

from .params import (
    A_FS, A_GC, A_HMC, B_FS, B_GC, B_HMC, C_FS, C_GC, C_HMC, D_FS, D_GC, D_HMC,
    DGConfig, DT_MS, PP_DELAY, SYN_DELAY,
    TAU_EX_FS, TAU_EX_GC, TAU_EX_HMC, TAU_IN_GC,
)

prefs.codegen.target = 'numpy'


# ══════════════════════════════════════════════════════════════════════════════
# Łączność (deterministyczna względem seeda — ta sama sieć we wszystkich lezjach)
# ══════════════════════════════════════════════════════════════════════════════

def make_connectivity(cfg: DGConfig, seed: int = 0) -> dict:
    """
    Losowa łączność o zadanych prawdopodobieństwach.

    WAŻNE dla kierunku 4: ten sam `seed` daje tę samą sieć, więc porównując
    lezje (FF/FB/MC on/off) zmieniamy WYŁĄCZNIE obecność motywu, a nie okablowanie.
    """
    rng = np.random.default_rng(seed)

    def pairs(n_src, n_tgt, p):
        s, t = np.where(rng.random((n_src, n_tgt)) < p)
        return s.astype(np.int32), t.astype(np.int32)

    return {
        'pp_fs':  pairs(cfg.N_GC,  cfg.N_FS,  cfg.P_PP_FS),
        'gc_fs':  pairs(cfg.N_GC,  cfg.N_FS,  cfg.P_GC_FS),
        'fs_gc':  pairs(cfg.N_FS,  cfg.N_GC,  cfg.P_FS_GC),
        'gc_hmc': pairs(cfg.N_GC,  cfg.N_HMC, cfg.P_GC_HMC),
        'hmc_fs': pairs(cfg.N_HMC, cfg.N_FS,  cfg.P_HMC_FS),
        'hmc_gc': pairs(cfg.N_HMC, cfg.N_GC,  cfg.P_HMC_GC),
        'fs_hmc': pairs(cfg.N_FS,  cfg.N_HMC, cfg.P_FS_HMC),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Równania
# ══════════════════════════════════════════════════════════════════════════════

def _gc_eqs(K: float, b: float = B_GC) -> str:
    # g_ex = PP→GC, g_ex2 = HMC→GC (re-ekscytacja), g_in = FS→GC
    return (
        f"dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms"
        f" + g_ex/ms + g_ex2/ms - g_in/ms - {K}*mV/ms) : volt (unless refractory)\n"
        f"dg_ex/dt  = -g_ex /({TAU_EX_GC}*ms) : volt\n"
        f"dg_ex2/dt = -g_ex2/({TAU_EX_GC}*ms) : volt\n"
        f"dg_in/dt  = -g_in /({TAU_IN_GC}*ms) : volt\n"
        f"du/dt = {A_GC}/ms*({b}*v - u) : volt\n"
    )


def _fs_eqs(K: float) -> str:
    # g_ex = PP→FS (feedforward), g_ex2 = GC→FS (feedback), g_ex3 = HMC→FS
    return (
        f"dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms"
        f" + g_ex/ms + g_ex2/ms + g_ex3/ms - {K}*mV/ms) : volt (unless refractory)\n"
        f"dg_ex/dt  = -g_ex /({TAU_EX_FS}*ms) : volt\n"
        f"dg_ex2/dt = -g_ex2/({TAU_EX_FS}*ms) : volt\n"
        f"dg_ex3/dt = -g_ex3/({TAU_EX_FS}*ms) : volt\n"
        f"du/dt = {A_FS}/ms*({B_FS}*v - u) : volt\n"
    )


def _hmc_eqs(K: float) -> str:
    # g_in = FS→HMC. Przy W_FS_HMC=0 (domyślnie) kanał zostaje na zerze, więc
    # równanie jest numerycznie równoważne wersji z interactive_dg.py.
    return (
        f"dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms"
        f" + g_ex/ms - g_in/ms - {K}*mV/ms) : volt (unless refractory)\n"
        f"dg_ex/dt = -g_ex/({TAU_EX_HMC}*ms) : volt\n"
        f"dg_in/dt = -g_in/({TAU_IN_GC}*ms) : volt\n"
        f"du/dt = {A_HMC}/ms*({B_HMC}*v - u) : volt\n"
    )


def _on_pre(var, w_mv, p_rel):
    """
    Wyrażenie on_pre. Przy p_rel >= 1.0 zwracamy wersję DETERMINISTYCZNĄ — nie
    dlatego, że tak ładniej, tylko żeby nie zużyć ani jednej liczby losowej:
    dzięki temu domyślna konfiguracja jest bit-w-bit identyczna z wersją sprzed
    wprowadzenia zawodności (regresja w tests/test_reliability_regression.py).
    """
    if p_rel >= 1.0:
        return f'{var}_post += {w_mv}*mV'
    return f'{var}_post += {w_mv}*mV*int(rand() < {p_rel})'


def _set_delay(s, delay_ms, jitter_ms):
    """Opóźnienie stałe albo rozrzucone wokół `delay_ms` (obcięte do ≥ 0)."""
    if jitter_ms and jitter_ms > 0:
        hi = delay_ms + 5.0 * jitter_ms          # skończona górna granica dla clip()
        s.delay = f'clip({delay_ms} + {jitter_ms}*randn(), 0, {hi})*ms'
    else:
        s.delay = delay_ms * ms


def _syn(src, tgt, si, ti, w_mv, var, delay_ms, p_rel=1.0, jitter_ms=0.0):
    if len(si) == 0:
        return None
    s = Synapses(src, tgt, on_pre=_on_pre(var, w_mv, p_rel))
    s.connect(i=si, j=ti)
    _set_delay(s, delay_ms, jitter_ms)
    return s


# ══════════════════════════════════════════════════════════════════════════════
# Symulacja
# ══════════════════════════════════════════════════════════════════════════════

def simulate(cfg: DGConfig, input_idx: np.ndarray, input_t_ms: np.ndarray,
             conn: dict, record_flows: bool = False) -> dict:
    """
    Jedna próba obwodu DG.

    Zwraca dict:
      gc_rates  [N_GC]  — częstotliwość każdego GC [Hz]  ← główny sygnał wyjściowy
      fs_rates, hmc_rates
      gc_spikes (i, t), fs_spikes, hmc_spikes
      flows (opcjonalnie) — średni wkład [mV] każdej ścieżki (obserwowalność)
    """
    start_scope()
    defaultclock.dt = DT_MS * ms

    n_pp = cfg.N_GC * cfg.n_syn_pp if cfg.per_fiber else cfg.N_GC
    pp = SpikeGeneratorGroup(n_pp, input_idx, input_t_ms * ms)

    gc = NeuronGroup(cfg.N_GC, _gc_eqs(cfg.K_GC, cfg.b_gc), threshold='v >= 30*mV',
                     reset=f'v = {C_GC}*mV; u = u + {D_GC}*mV',
                     refractory=2 * ms, method='euler')
    fs = NeuronGroup(cfg.N_FS, _fs_eqs(cfg.K_FS), threshold='v >= 30*mV',
                     reset=f'v = {C_FS}*mV; u = u + {D_FS}*mV',
                     refractory=1 * ms, method='euler')
    hmc = NeuronGroup(cfg.N_HMC, _hmc_eqs(cfg.K_HMC), threshold='v >= 30*mV',
                      reset=f'v = {C_HMC}*mV; u = u + {D_HMC}*mV',
                      refractory=2 * ms, method='euler')

    gc.v = -70 * mV;  gc.u = cfg.b_gc * (-70 * mV)
    fs.v = -70 * mV;  fs.u = B_FS * (-70 * mV)
    hmc.v = -70 * mV; hmc.u = B_HMC * (-70 * mV)

    objs = [pp, gc, fs, hmc]

    # ── PP → GC (zawsze) ─────────────────────────────────────────────────────
    if cfg.per_fiber:
        src = (np.repeat(np.arange(cfg.N_GC, dtype=np.int32) * cfg.n_syn_pp, cfg.n_syn_pp)
               + np.tile(np.arange(cfg.n_syn_pp, dtype=np.int32), cfg.N_GC))
        tgt = np.repeat(np.arange(cfg.N_GC, dtype=np.int32), cfg.n_syn_pp)
    else:
        src = np.arange(cfg.N_GC, dtype=np.int32)
        tgt = np.arange(cfg.N_GC, dtype=np.int32)
    pr = cfg.p_rel_map()
    jit = cfg.delay_jitter_ms

    if any(p < 1.0 for p in pr.values()):
        # Brian2 ostrzega, że `g += w*int(rand()<p)` „may depend on the order of
        # execution". Tutaj jest to nieszkodliwe: wkłady synaps sumują się
        # (dodawanie jest przemienne), a losowania są niezależne — od kolejności
        # zależy tylko to, który synapsie przypadnie która liczba z generatora,
        # co jest statystycznie nierozróżnialne. Wyciszamy WYŁĄCZNIE gdy
        # zawodność jest faktycznie włączona, żeby domyślne przebiegi zostały
        # w pełni gadatliwe, a sweep na 35 tys. symulacji nie tonął w logu.
        BrianLogger.suppress_name('base')
    s = Synapses(pp, gc, on_pre=_on_pre('g_ex', cfg.W_PP_GC, pr['pp_gc']))
    s.connect(i=src, j=tgt)
    _set_delay(s, PP_DELAY, jit)
    objs.append(s)

    # ── motyw FF: PP → FS ────────────────────────────────────────────────────
    if cfg.enable_ff:
        pp_fs_src = conn['pp_fs'][0] * cfg.n_syn_pp if cfg.per_fiber else conn['pp_fs'][0]
        s = _syn(pp, fs, pp_fs_src, conn['pp_fs'][1], cfg.W_PP_FS, 'g_ex', PP_DELAY,
                 pr['pp_fs'], jit)
        if s is not None:
            objs.append(s)

    # ── motyw FB: GC → FS ────────────────────────────────────────────────────
    if cfg.enable_fb:
        s = _syn(gc, fs, *conn['gc_fs'], cfg.W_GC_FS, 'g_ex2', SYN_DELAY,
                 pr['gc_fs'], jit)
        if s is not None:
            objs.append(s)

    # ── FS → GC: wspólna droga wyjściowa FF i FB (istnieje, gdy któryś działa) ─
    if cfg.enable_ff or cfg.enable_fb:
        s = _syn(fs, gc, *conn['fs_gc'], cfg.W_FS_GC, 'g_in', SYN_DELAY,
                 pr['fs_gc'], jit)
        if s is not None:
            objs.append(s)

    # ── motyw MC: GC → HMC → {FS, GC} ────────────────────────────────────────
    if cfg.enable_hmc:
        for args in [
            (gc, hmc, *conn['gc_hmc'], cfg.W_GC_HMC, 'g_ex', SYN_DELAY, pr['gc_hmc'], jit),
            (hmc, fs, *conn['hmc_fs'], cfg.W_HMC_FS, 'g_ex3', SYN_DELAY, pr['hmc_fs'], jit),
            (hmc, gc, *conn['hmc_gc'], cfg.W_HMC_GC, 'g_ex2', SYN_DELAY, pr['hmc_gc'], jit),
        ]:
            s = _syn(*args)
            if s is not None:
                objs.append(s)

        # FS → HMC: hamulec pętli GC→HMC→GC. Domyślnie W_FS_HMC=0 → brak synapsy,
        # czyli obwód dokładnie jak w interactive_dg.py.
        if cfg.W_FS_HMC > 0 and (cfg.enable_ff or cfg.enable_fb):
            s = _syn(fs, hmc, *conn['fs_hmc'], cfg.W_FS_HMC, 'g_in', SYN_DELAY,
                     pr['fs_hmc'], jit)
            if s is not None:
                objs.append(s)

    sm_gc, sm_fs, sm_hmc = SpikeMonitor(gc), SpikeMonitor(fs), SpikeMonitor(hmc)
    objs += [sm_gc, sm_fs, sm_hmc]

    if record_flows:
        stm_gc = StateMonitor(gc, ['g_ex', 'g_ex2', 'g_in'], record=True)
        stm_fs = StateMonitor(fs, ['g_ex', 'g_ex2', 'g_ex3'], record=True)
        stm_hmc = StateMonitor(hmc, ['g_ex', 'g_in'], record=True)
        objs += [stm_gc, stm_fs, stm_hmc]

    Network(*objs).run(cfg.T_ms * ms)

    T_s = cfg.T_ms * 1e-3
    out = {
        'gc_rates':  np.bincount(np.array(sm_gc.i),  minlength=cfg.N_GC) / T_s,
        'fs_rates':  np.bincount(np.array(sm_fs.i),  minlength=cfg.N_FS) / T_s,
        'hmc_rates': np.bincount(np.array(sm_hmc.i), minlength=cfg.N_HMC) / T_s,
        'gc_spikes':  (np.array(sm_gc.i),  np.array(sm_gc.t / ms)),
        'fs_spikes':  (np.array(sm_fs.i),  np.array(sm_fs.t / ms)),
        'hmc_spikes': (np.array(sm_hmc.i), np.array(sm_hmc.t / ms)),
    }

    if record_flows:
        m = lambda a: float(np.asarray(a).mean()) if np.asarray(a).size else 0.0
        out['flows'] = {
            'pp_gc':  m(stm_gc.g_ex / mV),
            'hmc_gc': m(stm_gc.g_ex2 / mV),
            'fs_gc':  m(stm_gc.g_in / mV),
            'pp_fs':  m(stm_fs.g_ex / mV),
            'gc_fs':  m(stm_fs.g_ex2 / mV),
            'hmc_fs': m(stm_fs.g_ex3 / mV),
            'gc_hmc': m(stm_hmc.g_ex / mV),
            'fs_hmc': m(stm_hmc.g_in / mV),
        }

    return out
