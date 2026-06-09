"""
dg_microcircuit_brian2.py — Dentate Gyrus microcircuit (Brian2).

Extends single_neuron_patsep_brian2.py to a full DG population model.

Neurons
-------
GC  — granule cells       (N_GC = 100, principal excitatory)
BC  — basket cells        (N_BC = 10,  fast-spiking inhibitory)
MC  — mossy cells         (N_MC = 10,  excitatory hilar cells)

Connectivity
------------
PP  → GC   perforant-path drive (pattern-specific Poisson, direct 1:1)
GC  → BC   feedback excitation   →  BC fires when many GCs are active
BC  → GC   feedforward inhibition → suppresses weakly-driven GCs   ← KEY
GC  → MC   mossy fiber collaterals
MC  → BC   mossy cell drives basket cells (amplifies inhibition)
MC  → GC   diffuse weak re-excitation (modest completion effect)

Mechanism
---------
Active GCs (high PP drive) fire first; they recruit BCs via GC→BC; BCs
then inhibit ALL GCs via BC→GC; weakly-driven (inactive-pattern) GCs are
pushed below threshold → only the strongly-driven GCs survive → sparser,
more orthogonal output population vectors → R_out << R_in.

Comparison
----------
Two conditions are run for each pattern pair:
  • no_inh  — BC→GC synapse disabled (baseline, lateral inhibition off)
  • full    — complete circuit

Requirements: pip install brian2 numpy matplotlib scipy
Run:          python dg_microcircuit_brian2.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import pearsonr

from brian2 import (
    start_scope, NeuronGroup, Synapses,
    SpikeMonitor, StateMonitor, SpikeGeneratorGroup,
    run, defaultclock, ms, mV, prefs,
)

prefs.codegen.target = 'numpy'

rng = np.random.default_rng(42)

# ══════════════════════════════════════════════════════════════════════════════
# NETWORK SIZE
# ══════════════════════════════════════════════════════════════════════════════

N_GC = 100
N_BC = 10
N_MC = 10

# ══════════════════════════════════════════════════════════════════════════════
# SIMULATION TIMING
# ══════════════════════════════════════════════════════════════════════════════

T_MS = 2000.0      # trial duration [ms]
DT   = 0.1         # time step [ms]

N_PATTERNS = 5
R_TARGETS  = [0.25, 0.50, 0.75, 0.90]
R_DEMO     = 0.75

# ══════════════════════════════════════════════════════════════════════════════
# PATTERN PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

P_ACTIVE   = 0.25     # fraction of GCs active per pattern  (~25 of 100)

# Aggregate Poisson rate for each GC's PP input (represents n_syn=40 fibers)
#   r_eff_high = 40 syn × 15 Hz = 600 Hz  → g_mean = 600 × 0.006 × 0.005 s = 18 mV
#   threshold is 15 mV above rest  → active GC fires at ~20-25 Hz
R_EFF_HIGH = 600.0    # Hz
R_EFF_LOW  = 40.0     # Hz  (background noise,  g_mean ≈ 1.2 mV → near-silent)

# ══════════════════════════════════════════════════════════════════════════════
# NEURON PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

# Granule cell (LIF, same biophysics as single_neuron_patsep_brian2.py)
#   Equations:  dv/dt = (E_L - v + g_ex - g_in) / tau_m
#               dg_ex/dt = -g_ex / tau_syn_ex
#               dg_in/dt = -g_in / tau_syn_in
tau_m_gc      = 20.0    # ms
E_L_gc        = -70.0   # mV
V_th_gc       = -55.0   # mV  (15 mV above rest)
V_reset_gc    = -78.0   # mV
t_ref_gc      = 3.0     # ms
tau_syn_ex_gc = 5.0     # ms  (AMPA)
tau_syn_in_gc = 8.0     # ms  (GABA-A)

# Basket cell (fast-spiking interneuron)
#   dv/dt = (E_L - v + g_ex) / tau_m
tau_m_bc      = 10.0    # ms  (shorter → faster dynamics)
E_L_bc        = -65.0   # mV
V_th_bc       = -50.0   # mV
V_reset_bc    = -60.0   # mV
t_ref_bc      = 1.5     # ms
tau_syn_ex_bc = 3.0     # ms

# Mossy cell (excitatory hilar neuron)
#   dv/dt = (E_L - v + g_ex) / tau_m
tau_m_mc      = 25.0    # ms
E_L_mc        = -68.0   # mV
V_th_mc       = -53.0   # mV
V_reset_mc    = -70.0   # mV
t_ref_mc      = 2.0     # ms
tau_syn_ex_mc = 5.0     # ms

# ══════════════════════════════════════════════════════════════════════════════
# SYNAPTIC WEIGHTS  [mV]  and CONNECTIVITY PROBABILITIES
# ══════════════════════════════════════════════════════════════════════════════

W_PP_GC  = 6.0    # perforant path → GC (aggregate weight, same as single-neuron)

W_GC_BC  = 5.0    # GC → BC  (feedback excitation)
W_BC_GC  = 5.0    # BC → GC  (lateral inhibition — KEY for pattern separation)
#   With 10 BCs each connected to ~50% of GCs, a BC firing at ~40 Hz gives
#   g_in ≈ 5 inputs × 40 Hz × 5 mV × 8 ms ≈ 8 mV → suppresses inactive GCs
#   (whose g_ex ≈ 1.2 mV), leaves active GCs (g_ex ≈ 18 mV) still above threshold

W_GC_MC  = 2.0    # GC → MC
W_MC_GC  = 1.5    # MC → GC  (diffuse weak re-excitation)
W_MC_BC  = 2.0    # MC → BC  (amplifies BC activity via mossy cells)

P_GC_BC  = 0.4    # connectivity probability GC→BC
P_BC_GC  = 0.5    # BC→GC
P_GC_MC  = 0.25   # GC→MC
P_MC_GC  = 0.4    # MC→GC
P_MC_BC  = 0.4    # MC→BC

SYN_DELAY = 1.0   # uniform synaptic delay [ms]

# ══════════════════════════════════════════════════════════════════════════════
# NEURON EQUATIONS
# ══════════════════════════════════════════════════════════════════════════════

GC_EQS = '''
dv/dt    = (E_L - v + g_ex - g_in) / tau_m : volt (unless refractory)
dg_ex/dt = -g_ex / tau_ex                   : volt
dg_in/dt = -g_in / tau_in                   : volt
'''
GC_NS = dict(E_L=E_L_gc*mV, tau_m=tau_m_gc*ms,
             tau_ex=tau_syn_ex_gc*ms, tau_in=tau_syn_in_gc*ms)

BC_EQS = '''
dv/dt    = (E_L - v + g_ex) / tau_m : volt (unless refractory)
dg_ex/dt = -g_ex / tau_ex            : volt
'''
BC_NS = dict(E_L=E_L_bc*mV, tau_m=tau_m_bc*ms, tau_ex=tau_syn_ex_bc*ms)

MC_EQS = '''
dv/dt    = (E_L - v + g_ex) / tau_m : volt (unless refractory)
dg_ex/dt = -g_ex / tau_ex            : volt
'''
MC_NS = dict(E_L=E_L_mc*mV, tau_m=tau_m_mc*ms, tau_ex=tau_syn_ex_mc*ms)


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def make_gc_patterns(N_patterns, N_GC, R, p_active, rng):
    """
    Binary GC activation matrix (N_patterns, N_GC) with pairwise overlap ≈ R.
    Uses common+private Bernoulli: each GC is independently drawn as
      common  with prob p_active * R       → active in ALL patterns
      private with prob p_active * (1-R)   → active in ONE randomly-drawn pattern
    """
    p_common  = p_active * R
    p_private = p_active * (1.0 - R)

    common  = rng.random(N_GC) < p_common          # (N_GC,) bool
    patterns = np.zeros((N_patterns, N_GC), dtype=bool)
    for k in range(N_patterns):
        private = rng.random(N_GC) < p_private
        patterns[k] = common | private
    return patterns                                 # (N_patterns, N_GC)


def make_input_spikes(pattern_active, r_high, r_low, T_ms, dt_ms, rng):
    """
    For each GC, generate an aggregate Poisson spike train at r_high (active)
    or r_low (inactive).  Returns (indices, times_ms) for SpikeGeneratorGroup.
    """
    n_steps = int(T_ms / dt_ms)
    all_idx, all_t = [], []
    for i, active in enumerate(pattern_active):
        rate = r_high if active else r_low
        p    = rate * dt_ms * 1e-3
        spk  = (np.where(rng.random(n_steps) < p)[0] + 1).astype(float) * dt_ms
        spk  = spk[spk < T_ms]
        if len(spk):
            all_idx.append(np.full(len(spk), i, dtype=np.int32))
            all_t.append(spk)
    if all_idx:
        idx = np.concatenate(all_idx)
        t   = np.concatenate(all_t)
        order = np.argsort(t)
        return idx[order], t[order]
    return np.array([], dtype=np.int32), np.array([])


# ══════════════════════════════════════════════════════════════════════════════
# CONNECTIVITY  (generated once, reused for all pattern simulations)
# ══════════════════════════════════════════════════════════════════════════════

def make_connectivity(rng):
    def _pairs(N_src, N_tgt, p):
        mask = rng.random((N_src, N_tgt)) < p
        s, t = np.where(mask)
        return s.astype(np.int32), t.astype(np.int32)

    return {
        'gc_bc': _pairs(N_GC, N_BC, P_GC_BC),
        'bc_gc': _pairs(N_BC, N_GC, P_BC_GC),
        'gc_mc': _pairs(N_GC, N_MC, P_GC_MC),
        'mc_gc': _pairs(N_MC, N_GC, P_MC_GC),
        'mc_bc': _pairs(N_MC, N_BC, P_MC_BC),
    }


# ══════════════════════════════════════════════════════════════════════════════
# BRIAN2 SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def _add_syn(src, tgt, si, ti, weight_mv, tau_var, delay_ms):
    """Helper: create Synapses with fixed (si, ti) connectivity if non-empty."""
    if len(si) == 0:
        return
    syn = Synapses(src, tgt,
                   on_pre=f'{tau_var} += {weight_mv}*mV',
                   delay=delay_ms * ms)
    syn.connect(i=si, j=ti)
    return syn


def simulate_dg(gc_input_idx, gc_input_t, conn,
                with_inh=True, with_mc=True, record_demo=False):
    """
    Simulate one trial of the DG microcircuit.

    Parameters
    ----------
    gc_input_idx / gc_input_t : SpikeGeneratorGroup inputs (aggregate PP drive)
    conn          : dict of fixed (src_idx, tgt_idx) connectivity arrays
    with_inh      : enable BC → GC inhibitory synapse
    with_mc       : enable MC population
    record_demo   : record full rasters and a 500-ms voltage snippet

    Returns
    -------
    gc_i, gc_t, bc_i, bc_t, mc_i, mc_t  — spike indices and times [ms]
    (plus voltage snapshots if record_demo)
    """
    start_scope()
    defaultclock.dt = DT * ms

    # ── input ──────────────────────────────────────────────────────────────
    pp = SpikeGeneratorGroup(N_GC, gc_input_idx, gc_input_t * ms)

    # ── neurons ────────────────────────────────────────────────────────────
    gc = NeuronGroup(N_GC, GC_EQS,
                     threshold=f'v >= {V_th_gc}*mV',
                     reset=f'v = {V_reset_gc}*mV',
                     refractory=t_ref_gc * ms, method='exact',
                     namespace=GC_NS)
    bc = NeuronGroup(N_BC, BC_EQS,
                     threshold=f'v >= {V_th_bc}*mV',
                     reset=f'v = {V_reset_bc}*mV',
                     refractory=t_ref_bc * ms, method='exact',
                     namespace=BC_NS)
    mc = NeuronGroup(N_MC, MC_EQS,
                     threshold=f'v >= {V_th_mc}*mV',
                     reset=f'v = {V_reset_mc}*mV',
                     refractory=t_ref_mc * ms, method='exact',
                     namespace=MC_NS)

    gc.v = E_L_gc * mV;  gc.g_ex = 0 * mV;  gc.g_in = 0 * mV
    bc.v = E_L_bc * mV;  bc.g_ex = 0 * mV
    mc.v = E_L_mc * mV;  mc.g_ex = 0 * mV

    # ── PP → GC (1:1, always present) ─────────────────────────────────────
    syn_pp = Synapses(pp, gc, on_pre=f'g_ex += {W_PP_GC}*mV',
                      delay=SYN_DELAY * ms)
    syn_pp.connect(i=np.arange(N_GC), j=np.arange(N_GC))

    # ── recurrent / inhibitory synapses ────────────────────────────────────
    _add_syn(gc, bc, *conn['gc_bc'], W_GC_BC, 'g_ex', SYN_DELAY)
    if with_inh:
        _add_syn(bc, gc, *conn['bc_gc'], W_BC_GC, 'g_in', SYN_DELAY)
    if with_mc:
        _add_syn(gc, mc, *conn['gc_mc'], W_GC_MC, 'g_ex', SYN_DELAY)
        _add_syn(mc, gc, *conn['mc_gc'], W_MC_GC, 'g_ex', SYN_DELAY)
        _add_syn(mc, bc, *conn['mc_bc'], W_MC_BC, 'g_ex', SYN_DELAY)

    # ── monitors ───────────────────────────────────────────────────────────
    sm_gc = SpikeMonitor(gc)
    sm_bc = SpikeMonitor(bc)
    sm_mc = SpikeMonitor(mc)

    if record_demo:
        vm_gc = StateMonitor(gc, 'v', record=True)

    run(T_MS * ms)

    out = (np.array(sm_gc.i), np.array(sm_gc.t / ms),
           np.array(sm_bc.i), np.array(sm_bc.t / ms),
           np.array(sm_mc.i), np.array(sm_mc.t / ms))

    if record_demo:
        return out + (np.array(vm_gc.t / ms), np.array(vm_gc.v / mV))
    return out


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def gc_rate_vec(gc_i, gc_t, T_ms=T_MS):
    """Firing rate [Hz] of each GC over the whole trial."""
    counts = np.bincount(gc_i, minlength=N_GC) if len(gc_i) else np.zeros(N_GC)
    return counts / (T_ms * 1e-3)


def mean_pairwise_r(vecs):
    """Mean Pearson R over all N*(N-1)/2 pairs of rate vectors."""
    rs = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            a, b = vecs[i], vecs[j]
            if a.std() > 0 and b.std() > 0:
                r, _ = pearsonr(a, b)
                if not np.isnan(r):
                    rs.append(r)
    return float(np.mean(rs)) if rs else 0.0


def input_r_from_patterns(patterns):
    """Mean Pearson R of binary GC activation vectors."""
    return mean_pairwise_r([p.astype(float) for p in patterns])


def mean_upper_r(mat):
    idx = np.triu_indices_from(mat, k=1)
    return float(mat[idx].mean())


# ══════════════════════════════════════════════════════════════════════════════
# PRE-GENERATE FIXED CONNECTIVITY  (shared across all simulations)
# ══════════════════════════════════════════════════════════════════════════════

print("Building fixed random connectivity ...")
conn = make_connectivity(rng)
print(f"  GC→BC: {len(conn['gc_bc'][0])} synapses "
      f"(mean {len(conn['gc_bc'][0])/N_BC:.1f}/BC)")
print(f"  BC→GC: {len(conn['bc_gc'][0])} synapses "
      f"(mean {len(conn['bc_gc'][0])/N_GC:.1f}/GC)")
print(f"  GC→MC: {len(conn['gc_mc'][0])},  MC→GC: {len(conn['mc_gc'][0])},  "
      f"MC→BC: {len(conn['mc_bc'][0])}\n")


# ══════════════════════════════════════════════════════════════════════════════
# SCAN OVER R_TARGETS  (two conditions: no_inh vs full circuit)
# ══════════════════════════════════════════════════════════════════════════════

print("Scanning R_targets — two conditions: [no_inh] vs [full circuit]\n")

results = []   # list of (R_target, R_in, R_out_no_inh, R_out_full)

for R_target in R_TARGETS:
    patterns = make_gc_patterns(N_PATTERNS, N_GC, R_target, P_ACTIVE, rng)
    R_in = input_r_from_patterns(patterns)

    rates_no_inh = []
    rates_full   = []

    for k in range(N_PATTERNS):
        idx, t_ms = make_input_spikes(patterns[k], R_EFF_HIGH, R_EFF_LOW,
                                      T_MS, DT, rng)
        # condition 1: no lateral inhibition
        gc_i, gc_t, *_ = simulate_dg(idx, t_ms, conn,
                                      with_inh=False, with_mc=False)
        rates_no_inh.append(gc_rate_vec(gc_i, gc_t))

        # condition 2: full circuit
        gc_i, gc_t, *_ = simulate_dg(idx, t_ms, conn,
                                      with_inh=True, with_mc=True)
        rates_full.append(gc_rate_vec(gc_i, gc_t))

    R_out_no  = mean_pairwise_r(rates_no_inh)
    R_out_full = mean_pairwise_r(rates_full)
    results.append((R_target, R_in, R_out_no, R_out_full))

    fr_no   = np.mean([r.mean() for r in rates_no_inh])
    fr_full = np.mean([r.mean() for r in rates_full])
    print(f"  R={R_target:.2f}  R_in={R_in:.3f}"
          f"  |  no_inh: R_out={R_out_no:.3f} FR={fr_no:.1f}Hz"
          f"  |  full: R_out={R_out_full:.3f} FR={fr_full:.1f}Hz"
          f"  gain={R_out_no - R_out_full:.3f}")

print()


# ══════════════════════════════════════════════════════════════════════════════
# DEMO SIMULATION at R_DEMO  (full circuit, N_PATTERNS, record rasters)
# ══════════════════════════════════════════════════════════════════════════════

print(f"Running demo at R={R_DEMO} (full circuit, recording rasters) ...")
demo_pats = make_gc_patterns(N_PATTERNS, N_GC, R_DEMO, P_ACTIVE, rng)

demo_gc_spikes  = []   # list of (i, t) per pattern
demo_bc_spikes  = []
demo_mc_spikes  = []
demo_rates_no   = []
demo_rates_full = []

for k in range(N_PATTERNS):
    idx, t_ms = make_input_spikes(demo_pats[k], R_EFF_HIGH, R_EFF_LOW,
                                   T_MS, DT, rng)
    # no-inh for comparison
    gc_i, gc_t, *_ = simulate_dg(idx, t_ms, conn, with_inh=False, with_mc=False)
    demo_rates_no.append(gc_rate_vec(gc_i, gc_t))

    # full circuit
    gc_i, gc_t, bc_i, bc_t, mc_i, mc_t = simulate_dg(
        idx, t_ms, conn, with_inh=True, with_mc=True)
    demo_gc_spikes.append((gc_i, gc_t))
    demo_bc_spikes.append((bc_i, bc_t))
    demo_mc_spikes.append((mc_i, mc_t))
    demo_rates_full.append(gc_rate_vec(gc_i, gc_t))

demo_R_in   = input_r_from_patterns(demo_pats)
demo_R_out_no   = mean_pairwise_r(demo_rates_no)
demo_R_out_full = mean_pairwise_r(demo_rates_full)
print(f"  R_in={demo_R_in:.3f}  "
      f"no_inh: R_out={demo_R_out_no:.3f}  "
      f"full: R_out={demo_R_out_full:.3f}  "
      f"gain={demo_R_out_no - demo_R_out_full:.3f}\n")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE  (6 panels)
# ══════════════════════════════════════════════════════════════════════════════

COLORS_PAT = plt.cm.tab10(np.linspace(0, 0.45, N_PATTERNS))
PAT_LABELS  = [f'Pat {k+1}' for k in range(N_PATTERNS)]

fig = plt.figure(figsize=(16, 16))
gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.55, wspace=0.38)

# ── A: GC raster (full circuit, pattern 0 and 1 overlaid, first 1000 ms) ──
ax_A = fig.add_subplot(gs[0, 0])
WIN = 1000.0   # ms
for k in [0, 1]:
    gc_i, gc_t = demo_gc_spikes[k]
    mask = gc_t < WIN
    ax_A.scatter(gc_t[mask], gc_i[mask],
                 s=3, color=COLORS_PAT[k], alpha=0.6, linewidths=0,
                 label=PAT_LABELS[k])
ax_A.set(xlim=(0, WIN), ylim=(-1, N_GC),
         xlabel='Time (ms)', ylabel='GC index',
         title=f'A)  GC raster — full circuit (first {WIN:.0f} ms)\n'
               f'    patterns 1 & 2 overlaid  (R_demo={R_DEMO})')
ax_A.legend(fontsize=8, markerscale=3, loc='upper right')
ax_A.spines[['top', 'right']].set_visible(False)

# ── B: BC and MC rasters (pattern 0, full circuit) ─────────────────────────
ax_B = fig.add_subplot(gs[0, 1])
bc_i, bc_t = demo_bc_spikes[0]
mc_i, mc_t = demo_mc_spikes[0]
mask_bc = bc_t < WIN;  mask_mc = mc_t < WIN
ax_B.scatter(bc_t[mask_bc], bc_i[mask_bc] + N_MC + 1,
             s=8, color='firebrick', alpha=0.8, linewidths=0, label='Basket cells')
ax_B.scatter(mc_t[mask_mc], mc_i[mask_mc],
             s=8, color='steelblue', alpha=0.8, linewidths=0, label='Mossy cells')
ax_B.axhline(N_MC + 0.5, color='gray', lw=0.8, ls='--', alpha=0.5)
ax_B.set(xlim=(0, WIN), ylim=(-1, N_MC + N_BC + 1),
         xlabel='Time (ms)', ylabel='Cell index',
         title='B)  Interneuron rasters — pattern 1, full circuit\n'
               '    (bottom: MCs, top: BCs)')
ax_B.legend(fontsize=8, markerscale=2, loc='upper right')
ax_B.spines[['top', 'right']].set_visible(False)

# ── C: Input vs output population rate maps ────────────────────────────────
ax_C_in  = fig.add_subplot(gs[1, 0])
ax_C_out = fig.add_subplot(gs[1, 1])

input_map  = demo_pats.astype(float)          # (N_patterns, N_GC)
output_map = np.stack(demo_rates_full)        # (N_patterns, N_GC)

im_in = ax_C_in.imshow(input_map, aspect='auto', cmap='Oranges',
                        interpolation='nearest')
plt.colorbar(im_in, ax=ax_C_in, label='Active (1=yes)')
ax_C_in.set(xlabel='GC index', ylabel='Pattern #',
            yticks=range(N_PATTERNS), yticklabels=PAT_LABELS,
            title=f'C)  Input activation maps\n'
                  f'    R_in = {demo_R_in:.3f}  ({int(P_ACTIVE*N_GC)} active GCs/pattern)')

vmax = max(output_map.max(), 1.0)
im_out = ax_C_out.imshow(output_map, aspect='auto', cmap='Blues',
                          vmin=0, vmax=vmax, interpolation='nearest')
plt.colorbar(im_out, ax=ax_C_out, label='Firing rate (Hz)')
ax_C_out.set(xlabel='GC index', ylabel='Pattern #',
             yticks=range(N_PATTERNS), yticklabels=PAT_LABELS,
             title=f'D)  Output firing-rate maps (full circuit)\n'
                   f'    R_out = {demo_R_out_full:.3f}  '
                   f'(sparser, more orthogonal than input)')

# ── E: Pairwise correlation matrices ───────────────────────────────────────
ax_E_no   = fig.add_subplot(gs[2, 0])
ax_E_full = fig.add_subplot(gs[2, 1])

for ax_e, rate_vecs, cond_label, R_val in [
        (ax_E_no,   demo_rates_no,   'E)  Output corr — NO inhibition',  demo_R_out_no),
        (ax_E_full, demo_rates_full, 'F)  Output corr — FULL circuit',   demo_R_out_full)]:
    R_mat = np.eye(N_PATTERNS)
    for i in range(N_PATTERNS):
        for j in range(i + 1, N_PATTERNS):
            a, b = rate_vecs[i], rate_vecs[j]
            if a.std() > 0 and b.std() > 0:
                r, _ = pearsonr(a, b)
                R_mat[i, j] = R_mat[j, i] = r
    im = ax_e.imshow(R_mat, vmin=-0.3, vmax=1.0, cmap='RdYlGn', aspect='auto')
    plt.colorbar(im, ax=ax_e, label='Pearson R')
    ax_e.set(xlabel='Pattern #', ylabel='Pattern #',
             title=f'{cond_label}\n    mean R_out = {R_val:.3f}')

fig.suptitle(
    f'DG Microcircuit (Brian2) — Lateral Inhibition Enhances Pattern Separation\n'
    f'N_GC={N_GC}, N_BC={N_BC}, N_MC={N_MC}  |  R_demo={R_DEMO}  '
    f'|  gain = {demo_R_out_no - demo_R_out_full:.3f}',
    fontsize=12, fontweight='bold')

out_path = __file__.replace('.py', '.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight')
print(f'Saved figure: {out_path}')
plt.show()

# ── summary table ──────────────────────────────────────────────────────────
print("\nSummary  (R_out lower = better pattern separation)")
print(f"{'R_target':>10} {'R_in':>8} {'no_inh':>10} {'full':>10} {'gain':>8}")
for R_t, R_in, R_no, R_full in results:
    gain = R_no - R_full
    print(f"{R_t:>10.2f} {R_in:>8.3f} {R_no:>10.3f} {R_full:>10.3f} {gain:>8.3f}")
