"""
dg_module3_inh_comparison.py — Module 3: Feedforward vs Feedback Inhibition

Brian2 simulation of the DG microcircuit comparing four inhibitory circuit
configurations in a 2×2 design:

  baseline  : no inhibitory projections active
  ff_only   : PP → FS → GC  (feedforward — perforant path drives FS directly)
  fb_only   : GC → FS → GC  (feedback   — GC output recruits FS which suppresses GC)
  full      : both FF and FB active simultaneously

Neuron models (Izhikevich):
  GC  — regular spiking  a=0.02, b=0.2, c=−65, d=6
  FS  — fast spiking     a=0.10, b=0.2, c=−65, d=2
  HMC — regular spiking  a=0.02, b=0.2, c=−65, d=4

K_tonic is set to 0 here.  The paper's K=62 represents tonic GABA-A drive that
shifts the Izhikevich fixed point to ~−100 mV, which would require matching the
full conductance-based inhibitory network.  For this exploration we keep K=0
(natural Izhikevich fixed point at −70 mV) and rely on explicit FS→GC synapses
for sparse output — the scientifically relevant comparison.

NOTE on Tsodyks-Markram (TM) synapses: the paper's PP→GC depression (U_SE=0.13,
τ_rec=500 ms) is designed for individual fibres at ~15 Hz. With the aggregate
Poisson model (all 40 fibres lumped at 600 Hz), the TM synapse is severely
over-depressed (x_res_ss ≈ 2.5%) and provides negligible drive. TM at individual
fibre resolution would require 200 × 40 = 8000 input neurons. Module 3b can add
that. Here PP→GC uses a simple AMPA-like exponential synapse calibrated to match
physiological GC firing rates (∼15–20 Hz for active GCs).

Synapses:
  PP→GC  : AMPA (exponential, τ=5ms)  W=12 mV  delay=4ms
  PP→FS  : AMPA (τ=3ms)               W=0.5 mV  (feedforward path)
  GC→FS  : AMPA (τ=3ms)               W=12 mV  (feedback path)
  FS→GC  : GABA-A (τ=8ms)             W=10 mV  (inhibitory)
  GC→HMC, HMC→FS, HMC→GC: AMPA

Metrics at multiple bin sizes (10, 25, 50, 100, 250 ms):
  Pearson R of binned GC population vectors → decorrelation = R_in − R_out

Output: dg_module3_inh_comparison.png
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from brian2 import (
    start_scope, NeuronGroup, Synapses,
    SpikeMonitor, SpikeGeneratorGroup, Network,
    defaultclock, ms, mV, prefs,
)

prefs.codegen.target = 'numpy'

# ── Network size ──────────────────────────────────────────────────────────────
N_GC  = 200
N_FS  = 20
N_HMC = 10

# ── Simulation ────────────────────────────────────────────────────────────────
T_MS  = 1000.0   # ms per trial
DT_MS = 0.1      # ms

# ── Experiment ────────────────────────────────────────────────────────────────
N_PATTERNS = 5
R_TARGETS  = [0.50, 0.75, 0.90]
SEEDS      = [42, 43, 44]
BIN_SIZES  = [10, 25, 50, 100, 250]   # ms — timescales to analyse

# Reżim wejścia z jedynego źródła prawdy (dg_params.py): 400/40 Hz aggregate
# (= 40 włókien × 10/1 Hz). Wcześniej 600 Hz → output GC za wysoki (~16 Hz).
import sys as _sys, os as _os  # archive/: dopnij korzeń repo do ścieżki,
# bo skrypt mieszka teraz poziom niżej niż dg_params.py
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from dg_params import R_EFF_HIGH, R_EFF_LOW
P_ACTIVE   = 0.25   # fraction of GCs active per pattern

# ── Izhikevich parameters ─────────────────────────────────────────────────────
# GC — regular spiking (Izhikevich 2003)
A_GC, B_GC, C_GC, D_GC = 0.02, 0.2, -65.0, 6.0
# FS — fast spiking
A_FS, B_FS, C_FS, D_FS = 0.10, 0.2, -65.0, 2.0
# HMC — regular spiking, slower adaptation
A_HMC, B_HMC, C_HMC, D_HMC = 0.02, 0.2, -65.0, 4.0

# K_tonic calibration (Izhikevich bifurcation analysis):
#   With K=0: bifurcation threshold G_crit ≈ 4 mV → even background (40Hz) causes firing
#   With K=10: G_crit ≈ 14 mV → active GC fires (fluctuation-driven, ~19 Hz), inactive silent
#   Grid search confirmed: K=10, W_PP_GC=4.0 mV → active ~19 Hz, inactive 0 Hz ✓
K_TONIC_GC  = 10.0
K_TONIC_FS  =  5.0   # G_crit_FS ≈ 9 mV — FS fires reliably when driven by PP or GC
K_TONIC_HMC = 10.0

# Synaptic time constants [ms]
TAU_EX_GC  =  5.0   # AMPA on GC
TAU_IN_GC  =  8.0   # GABA-A on GC
TAU_EX_FS  =  3.0   # AMPA on FS
TAU_EX_HMC =  5.0   # AMPA on HMC

# ── Synaptic weights [mV] ─────────────────────────────────────────────────────
# Calibrated so that (P_ACTIVE=0.25, N_GC=200, K_GC=10):
#   Active GC  (600 Hz agg.): g_ex_ss = 600*4e-3*5e-3 = 12 mV < G_crit=14 mV
#     → fluctuation-driven regime → ~4 Hz baseline (pop. avg) ✓
#   Inactive GC (40 Hz agg.): g_ex_ss =  40*4e-3*5e-3 =  0.8 mV → silent ✓
#
#   FS feedforward (PP→FS, N_active=20, N_inactive=60, P=0.4):
#     g_ex_FS = (20*600 + 60*40)*0.25e-3*3e-3*1e3 = 10.8 mV > G_crit_FS=9 → ~50 Hz FS ✓
#   FS feedback (GC→FS, P=0.4): each FS sees 80 GC at ~4 Hz (pop) / ~16 Hz (active)
#     g_ex_FS = 80*3.9*10e-3*3e-3*1e3 = 9.4 mV ≈ G_crit_FS → ~30 Hz FS (fluctuation) ✓
#
#   FS→GC inhibition: 10 FS at ~50 Hz, W=1 mV
#     → g_in = 10*50*1e-3*8e-3*1e3 = 4 mV → net=8 mV → GC at ~2 Hz (suppressed) ✓
W_PP_GC  =  4.0   # PP → GC  (AMPA, perforant-path delay=4ms)
W_PP_FS  =  0.25  # PP → FS  (feedforward path; 0.25 mV → g_ex_FS≈10.8 mV → ~50 Hz FS)
W_GC_FS  = 10.0   # GC → FS  (feedback excitation)
W_FS_GC  =  1.0   # FS → GC  (inhibitory; 1 mV → g_in≈4 mV for FS@50Hz → GC at ~2 Hz)
W_GC_HMC =  1.0   # GC → HMC
W_HMC_FS =  1.0   # HMC → FS
W_HMC_GC =  0.5   # HMC → GC (weak re-excitation)

PP_DELAY  = 4.0    # ms — perforant path delay (from paper)
SYN_DELAY = 1.0    # ms — default delay for recurrent synapses

# ── Connectivity probabilities ────────────────────────────────────────────────
P_PP_FS   = 0.40
P_GC_FS   = 0.40
P_FS_GC   = 0.50
P_GC_HMC  = 0.25
P_HMC_FS  = 0.40
P_HMC_GC  = 0.40


# ── Izhikevich neuron equations ───────────────────────────────────────────────
# Units: dv/dt declared as : volt (Brian2 base unit)
# Each term 0.04/mV/ms * v² etc. evaluates to V/s = mV/ms ✓
# K_tonic multiplied by mV/ms to match other terms.

def _izh_eqs(a, b, tau_ex, tau_in=None, K_tonic=0.0):
    inh_eq   = f"\ndg_in/dt = -g_in / ({tau_in}*ms) : volt" if tau_in else ""
    inh_term = "- g_in/ms " if tau_in else ""
    K_term   = f"- {K_tonic}*mV/ms" if K_tonic != 0.0 else ""
    return (
        f"dv/dt  = (0.04/mV/ms * v**2 + 5/ms * v + 140*mV/ms"
        f" - u/ms + g_ex/ms {inh_term}{K_term}) : volt (unless refractory)\n"
        f"dg_ex/dt = -g_ex / ({tau_ex}*ms) : volt{inh_eq}\n"
        f"du/dt  = {a}/ms * ({b} * v - u) : volt\n"
    )

GC_EQS  = _izh_eqs(A_GC,  B_GC,  TAU_EX_GC,  tau_in=TAU_IN_GC, K_tonic=K_TONIC_GC)
FS_EQS  = _izh_eqs(A_FS,  B_FS,  TAU_EX_FS,  tau_in=None,       K_tonic=K_TONIC_FS)
HMC_EQS = _izh_eqs(A_HMC, B_HMC, TAU_EX_HMC, tau_in=None,       K_tonic=K_TONIC_HMC)


# ── Pattern generation ────────────────────────────────────────────────────────

def make_gc_patterns(N_pat, N_GC, R, p_active, rng):
    """Binary GC activation matrix (N_pat, N_GC) with pairwise overlap ≈ R."""
    common = rng.random(N_GC) < (p_active * R)
    pats = np.zeros((N_pat, N_GC), dtype=bool)
    for k in range(N_pat):
        pats[k] = common | (rng.random(N_GC) < p_active * (1.0 - R))
    return pats


def make_input_spikes(pattern_active, r_high, r_low, T_ms, dt_ms, rng):
    """Aggregate Poisson spike train per GC: r_high if active, r_low otherwise."""
    n_steps = int(T_ms / dt_ms)
    all_idx, all_t = [], []
    for i, active in enumerate(pattern_active):
        rate = r_high if active else r_low
        p    = rate * dt_ms * 1e-3
        ts   = np.where(rng.random(n_steps) < p)[0].astype(float) * dt_ms
        ts   = ts[(ts > 0) & (ts < T_ms)]
        if len(ts):
            all_idx.append(np.full(len(ts), i, dtype=np.int32))
            all_t.append(ts)
    if all_idx:
        idx = np.concatenate(all_idx)
        t   = np.concatenate(all_t)
        order = np.argsort(t)
        return idx[order], t[order]
    return np.array([], dtype=np.int32), np.array([])


def input_r_from_patterns(pats):
    """Mean pairwise Pearson R of binary GC activation vectors."""
    rs = []
    for i in range(len(pats)):
        for j in range(i + 1, len(pats)):
            a, b = pats[i].astype(float), pats[j].astype(float)
            if a.std() > 1e-9 and b.std() > 1e-9:
                rs.append(float(np.corrcoef(a, b)[0, 1]))
    return float(np.mean(rs)) if rs else 0.0


# ── Fixed random connectivity ─────────────────────────────────────────────────

def make_connectivity(rng):
    def _pairs(N_src, N_tgt, p):
        mask = rng.random((N_src, N_tgt)) < p
        s, t = np.where(mask)
        return s.astype(np.int32), t.astype(np.int32)

    return {
        'pp_fs' : _pairs(N_GC,  N_FS,  P_PP_FS),
        'gc_fs' : _pairs(N_GC,  N_FS,  P_GC_FS),
        'fs_gc' : _pairs(N_FS,  N_GC,  P_FS_GC),
        'gc_hmc': _pairs(N_GC,  N_HMC, P_GC_HMC),
        'hmc_fs': _pairs(N_HMC, N_FS,  P_HMC_FS),
        'hmc_gc': _pairs(N_HMC, N_GC,  P_HMC_GC),
    }


# ── Brian2 simulation ─────────────────────────────────────────────────────────

def _syn(src, tgt, si, ti, w_mV, var, delay_ms):
    """Create a fixed-connectivity excitatory or inhibitory synapse."""
    if len(si) == 0:
        return None
    syn = Synapses(src, tgt,
                   on_pre=f'{var}_post += {w_mV}*mV',
                   delay=delay_ms * ms)
    syn.connect(i=si, j=ti)
    return syn


def simulate_dg(gc_input_idx, gc_input_t, conn,
                enable_ff=True, enable_fb=True, enable_hmc=True):
    """
    Run one trial of the DG microcircuit.

    Parameters
    ----------
    gc_input_idx, gc_input_t : PP spike train (SpikeGeneratorGroup)
    conn : connectivity dict from make_connectivity()
    enable_ff  : activate PP → FS → GC (feedforward inhibition)
    enable_fb  : activate GC → FS → GC (feedback inhibition)
    enable_hmc : include hilar mossy cells

    Returns
    -------
    gc_i, gc_t_ms, fs_i, fs_t_ms : spike indices and times
    """
    start_scope()
    defaultclock.dt = DT_MS * ms

    pp = SpikeGeneratorGroup(N_GC, gc_input_idx, gc_input_t * ms)

    gc = NeuronGroup(N_GC, GC_EQS,
                     threshold='v >= 30*mV',
                     reset=f'v = {C_GC}*mV; u = u + {D_GC}*mV',
                     refractory=2*ms, method='euler')
    fs = NeuronGroup(N_FS, FS_EQS,
                     threshold='v >= 30*mV',
                     reset=f'v = {C_FS}*mV; u = u + {D_FS}*mV',
                     refractory=1*ms, method='euler')
    hmc = NeuronGroup(N_HMC, HMC_EQS,
                      threshold='v >= 30*mV',
                      reset=f'v = {C_HMC}*mV; u = u + {D_HMC}*mV',
                      refractory=2*ms, method='euler')

    gc.v  = -70*mV;  gc.u  = B_GC  * (-70*mV);  gc.g_ex  = 0*mV;  gc.g_in = 0*mV
    fs.v  = -70*mV;  fs.u  = B_FS  * (-70*mV);  fs.g_ex  = 0*mV
    hmc.v = -70*mV;  hmc.u = B_HMC * (-70*mV);  hmc.g_ex = 0*mV

    # Collect all objects explicitly — Brian2's magic network drops synapses when
    # the same group appears as both source and target in different Synapses objects
    # created in a certain order.  Using Network(...) bypasses that bug entirely.
    net_objects = [pp, gc, fs, hmc]

    # PP → GC (always present, AMPA with perforant-path delay)
    syn_pp_gc = Synapses(pp, gc,
                         on_pre=f'g_ex_post += {W_PP_GC}*mV',
                         delay=PP_DELAY * ms)
    syn_pp_gc.connect(i=np.arange(N_GC), j=np.arange(N_GC))
    net_objects.append(syn_pp_gc)

    # PP → FS  (feedforward inhibition path)
    if enable_ff:
        s = _syn(pp, fs, conn['pp_fs'][0], conn['pp_fs'][1], W_PP_FS, 'g_ex', PP_DELAY)
        if s is not None: net_objects.append(s)

    # GC → FS  (feedback excitation)
    if enable_fb:
        s = _syn(gc, fs, conn['gc_fs'][0], conn['gc_fs'][1], W_GC_FS, 'g_ex', SYN_DELAY)
        if s is not None: net_objects.append(s)

    # FS → GC  (inhibition; active whenever FS receives any excitation)
    if enable_ff or enable_fb:
        s = _syn(fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', SYN_DELAY)
        if s is not None: net_objects.append(s)

    # HMC connections
    if enable_hmc:
        s = _syn(gc,  hmc, conn['gc_hmc'][0], conn['gc_hmc'][1], W_GC_HMC, 'g_ex', SYN_DELAY)
        if s is not None: net_objects.append(s)
        s = _syn(hmc, fs,  conn['hmc_fs'][0], conn['hmc_fs'][1], W_HMC_FS, 'g_ex', SYN_DELAY)
        if s is not None: net_objects.append(s)
        s = _syn(hmc, gc,  conn['hmc_gc'][0], conn['hmc_gc'][1], W_HMC_GC, 'g_ex', SYN_DELAY)
        if s is not None: net_objects.append(s)

    sm_gc = SpikeMonitor(gc)
    sm_fs = SpikeMonitor(fs)
    net_objects += [sm_gc, sm_fs]

    net = Network(*net_objects)
    net.run(T_MS * ms)

    return (np.array(sm_gc.i), np.array(sm_gc.t / ms),
            np.array(sm_fs.i), np.array(sm_fs.t / ms))


# ── Analysis ──────────────────────────────────────────────────────────────────

def bin_spikes(i_arr, t_arr, N_cells, T_ms, bin_ms):
    n_bins = max(1, int(T_ms / bin_ms))
    mat = np.zeros((N_cells, n_bins))
    if len(t_arr):
        bi = np.clip(np.floor(t_arr / bin_ms).astype(int), 0, n_bins - 1)
        for ci, b in zip(i_arr, bi):
            mat[ci, b] += 1
    return mat


def mean_pairwise_r(binned_list):
    rs = []
    for i in range(len(binned_list)):
        for j in range(i + 1, len(binned_list)):
            a = binned_list[i].ravel().astype(float)
            b = binned_list[j].ravel().astype(float)
            if a.std() > 1e-9 and b.std() > 1e-9:
                r = float(np.corrcoef(a, b)[0, 1])
                if not np.isnan(r):
                    rs.append(r)
    return float(np.mean(rs)) if rs else 0.0


# ── Conditions ────────────────────────────────────────────────────────────────

CONDITIONS = {
    'baseline': dict(enable_ff=False, enable_fb=False),
    'ff_only' : dict(enable_ff=True,  enable_fb=False),
    'fb_only' : dict(enable_ff=False, enable_fb=True),
    'full'    : dict(enable_ff=True,  enable_fb=True),
}
COND_LABELS = ['Baseline\n(no inh)', 'Feedforward\nPP→FS→GC', 'Feedback\nGC→FS→GC', 'Full\ncircuit']
COND_COLORS = ['#aaaaaa', '#4575b4', '#d73027', '#1a9850']


# ── Main simulation loop ──────────────────────────────────────────────────────

print("DG Module 3 — Feedforward vs Feedback Inhibition")
print(f"N_GC={N_GC}, N_FS={N_FS}, N_HMC={N_HMC}  |  Izhikevich neurons  |  K_tonic: GC={K_TONIC_GC}, FS={K_TONIC_FS}, HMC={K_TONIC_HMC}")
print()

rng_conn = np.random.default_rng(0)
conn = make_connectivity(rng_conn)
print(f"Connectivity:  PP→FS={len(conn['pp_fs'][0])} syn  |  "
      f"GC→FS={len(conn['gc_fs'][0])} syn  |  "
      f"FS→GC={len(conn['fs_gc'][0])} syn\n")

all_results = {R: {} for R in R_TARGETS}

for R_target in R_TARGETS:
    print(f"── R_in = {R_target} ──────────────────────────────────────────")
    for cname, ckw in CONDITIONS.items():
        dec_by_bin = {b: [] for b in BIN_SIZES}
        rin_vals, fr_gc_vals, fr_fs_vals = [], [], []

        for seed in SEEDS:
            rng_s = np.random.default_rng(seed)
            pats  = make_gc_patterns(N_PATTERNS, N_GC, R_target, P_ACTIVE, rng_s)
            rin_vals.append(input_r_from_patterns(pats))

            rng_inp = np.random.default_rng(seed + 1000)
            gc_spikes, fs_spikes = [], []

            for k in range(N_PATTERNS):
                idx, t_ms = make_input_spikes(pats[k], R_EFF_HIGH, R_EFF_LOW,
                                              T_MS, DT_MS, rng_inp)
                gc_i, gc_t, fs_i, fs_t = simulate_dg(idx, t_ms, conn, **ckw)
                gc_spikes.append((gc_i, gc_t))
                fs_spikes.append((fs_i, fs_t))

            fr_gc_vals.append(np.mean([len(t) / (T_MS * 1e-3 * N_GC)
                                       for _, t in gc_spikes]))
            fr_fs_vals.append(np.mean([len(t) / (T_MS * 1e-3 * N_FS)
                                       for _, t in fs_spikes]))

            for bms in BIN_SIZES:
                binned = [bin_spikes(i, t, N_GC, T_MS, bms)
                          for i, t in gc_spikes]
                R_out = mean_pairwise_r(binned)
                dec_by_bin[bms].append(rin_vals[-1] - R_out)

        all_results[R_target][cname] = {
            'R_in'   : float(np.mean(rin_vals)),
            'dec'    : {b: float(np.mean(dec_by_bin[b]))  for b in BIN_SIZES},
            'dec_std': {b: float(np.std(dec_by_bin[b]))   for b in BIN_SIZES},
            'fr_gc'  : float(np.mean(fr_gc_vals)),
            'fr_fs'  : float(np.mean(fr_fs_vals)),
        }
        dec100 = all_results[R_target][cname]['dec'][100]
        fr_gc  = all_results[R_target][cname]['fr_gc']
        fr_fs  = all_results[R_target][cname]['fr_fs']
        print(f"  {cname:10s}  dec@100ms={dec100:+.3f}  "
              f"mean_FR_gc={fr_gc:.1f}Hz  mean_FR_fs={fr_fs:.1f}Hz")
    print()

print("All simulations complete.\n")


# ── Visualisation ─────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(16, 11))
gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.52, wspace=0.38)
R_COLORS = ['#4575b4', '#d73027', '#1a9850']

# ── Top row: bar charts per R_in level (100ms bins) ──────────────────────────
for ri, R_target in enumerate(R_TARGETS):
    ax = fig.add_subplot(gs[0, ri])
    cnames = list(CONDITIONS.keys())
    decs   = [all_results[R_target][cn]['dec'][100]     for cn in cnames]
    stds   = [all_results[R_target][cn]['dec_std'][100] for cn in cnames]

    ax.bar(range(len(cnames)), decs, color=COND_COLORS,
           edgecolor='black', linewidth=0.8, alpha=0.85)
    ax.errorbar(range(len(cnames)), decs, yerr=stds,
                fmt='none', color='black', capsize=4, lw=1.2)
    ax.set_xticks(range(len(cnames)))
    ax.set_xticklabels(COND_LABELS, fontsize=7.5)
    ax.axhline(0, color='gray', lw=0.6, ls=':')
    ax.set_ylabel('Decorrelation  (R_in − R_out)', fontsize=8.5)
    ax.set_title(f'R_in ≈ {R_target:.2f}  (100 ms bins)', fontsize=10, fontweight='bold')
    ax.tick_params(labelsize=8)
    for i, cn in enumerate(cnames):
        fr = all_results[R_target][cn]['fr_gc']
        ypos = decs[i] + stds[i] + 0.005
        ax.text(i, ypos, f'{fr:.1f} Hz', ha='center', va='bottom', fontsize=6.5)

# ── Bottom: timescale dependence ──────────────────────────────────────────────
ax_ts = fig.add_subplot(gs[1, :])
linestyles = ['-', '--', '-.', ':']
markers    = ['o', 's', '^', 'D']

for ri, R_target in enumerate(R_TARGETS):
    for ci, (cname, clabel) in enumerate(zip(CONDITIONS.keys(), COND_LABELS)):
        decs = [all_results[R_target][cname]['dec'][b]     for b in BIN_SIZES]
        stds = [all_results[R_target][cname]['dec_std'][b] for b in BIN_SIZES]
        ax_ts.plot(BIN_SIZES, decs,
                   linestyles[ci], color=R_COLORS[ri], lw=1.5,
                   marker=markers[ci], ms=5,
                   label=f'R_in={R_target} — {clabel.replace(chr(10), " ")}')
        ax_ts.fill_between(BIN_SIZES,
                           [d - s for d, s in zip(decs, stds)],
                           [d + s for d, s in zip(decs, stds)],
                           color=R_COLORS[ri], alpha=0.07)

ax_ts.axhline(0, color='gray', lw=0.6, ls=':')
ax_ts.set_xlabel('Bin size (ms)  — analysis timescale', fontsize=9)
ax_ts.set_ylabel('Decorrelation  (R_in − R_out)', fontsize=8.5)
ax_ts.set_title(
    'Pattern separation across timescales\n'
    'Short bins = fine temporal resolution;  long bins = rate-code comparison',
    fontsize=10, fontweight='bold')
ax_ts.set_xscale('log')
ax_ts.set_xticks(BIN_SIZES)
ax_ts.set_xticklabels([str(b) for b in BIN_SIZES])
ax_ts.legend(fontsize=6.5, loc='upper left', ncol=2, framealpha=0.7)
ax_ts.tick_params(labelsize=8)

fig.suptitle(
    f'Module 3: Feedforward vs Feedback Inhibition — DG Microcircuit\n'
    f'N_GC={N_GC}, N_FS={N_FS}, N_HMC={N_HMC}  |  Izhikevich neurons  |  '
    f'W_PP_GC={W_PP_GC} mV  W_PP_FS={W_PP_FS} mV  W_GC_FS={W_GC_FS} mV  W_FS_GC={W_FS_GC} mV',
    fontsize=9.5, fontweight='bold', y=1.01,
)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'dg_module3_inh_comparison.png')
fig.savefig(out_path, dpi=150, bbox_inches='tight')
print(f'Saved: {out_path}')
plt.show()
