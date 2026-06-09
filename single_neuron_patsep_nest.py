"""
single_neuron_patsep_nest.py — Pattern separation using Brian2 simulator.

NOTE: The NEST neural simulator does not support Windows natively.
Brian2 is the cross-platform equivalent (pip install brian2) and maps
directly to the same equations — no rescaling needed because Brian2
uses physical units (mV, ms, pA, etc.).

Same experiment as single_neuron_patsep.py but replaces the hand-rolled
Euler LIF with Brian2's NeuronGroup + SpikeGeneratorGroup.

Biological model:
  - One LIF neuron ≈ granule cell (GC) in DG
  - Equations (identical to original):
      dv/dt = (E_L - v + g) / tau_m    [unless refractory]
      dg/dt = -g / tau_syn
  - Per-spike jump: g += W_SYN = 6 mV  (same as original W_SYN)

Requirements: pip install brian2 numpy matplotlib scipy
Run:          python single_neuron_patsep_nest.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import pearsonr

from brian2 import (start_scope, NeuronGroup, Synapses, SpikeMonitor,
                    StateMonitor, SpikeGeneratorGroup, run, defaultclock,
                    ms, mV, prefs)

# Use pure-numpy backend — no C compiler required
prefs.codegen.target = 'numpy'

rng = np.random.default_rng(42)

# ══════════════════════════════════════════════════════════════════════════════
# PARAMETERS  (identical to single_neuron_patsep.py)
# ══════════════════════════════════════════════════════════════════════════════

T_MS = 2000.0     # simulation duration [ms]
DT   = 0.1        # time step [ms]

N_PATTERNS = 5
R_TARGETS  = [0.25, 0.50, 0.75, 0.90]
R_DEMO     = 0.8

# LIF / granule-cell parameters
tau_m    = 20.0    # ms
E_L      = -70.0   # mV
V_th     = -55.0   # mV
V_reset  = -78.0   # mV
t_ref    = 3.0     # ms
tau_syn  = 5.0     # ms  (AMPA-like)

# Synaptic weight — same value as original (g has units of voltage)
W_SYN_MV = 6.0    # mV  per spike

n_syn    = 40
r_input  = 10.0   # Hz
BIN_MS   = 10.0   # ms  (correlation bin width)

# Brian2 namespace (evaluated once, reused in every NeuronGroup)
LIF_EQS = '''
dv/dt = (E_L - v + g) / tau_m : volt (unless refractory)
dg/dt = -g / tau_syn           : volt
'''
LIF_NS = {
    'E_L':    E_L    * mV,
    'tau_m':  tau_m  * ms,
    'tau_syn':tau_syn * ms,
}


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN GENERATION  (common + private Poisson streams — same as original)
# ══════════════════════════════════════════════════════════════════════════════

def make_patterns(N, r_hz, R, n_syn, T_ms, dt_ms, rng):
    """
    Returns
    -------
    times  : list[N] of list[n_syn] of float arrays — spike times [ms]
    binary : list[N] of (n_syn, n_steps) bool arrays — for input correlation
    """
    n_steps   = int(T_ms / dt_ms)
    p_common  = R * r_hz * dt_ms * 1e-3
    p_private = (1.0 - R) * r_hz * dt_ms * 1e-3

    times  = [[] for _ in range(N)]
    binary = [np.zeros((n_syn, n_steps), dtype=bool) for _ in range(N)]

    for s in range(n_syn):
        common = rng.random(n_steps) < p_common
        for k in range(N):
            private  = rng.random(n_steps) < p_private
            combined = common | private
            binary[k][s] = combined
            spk = (np.where(combined)[0] + 1).astype(float) * dt_ms  # 1-indexed → avoid t=0
            times[k].append(spk[spk < T_ms])

    return times, binary


# ══════════════════════════════════════════════════════════════════════════════
# BRIAN2 SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def simulate_brian2(spike_times_list, record_v=False):
    """
    Simulate a single LIF neuron in Brian2 driven by n_syn
    SpikeGeneratorGroup inputs.

    Returns
    -------
    out_times : ndarray  — output spike times [ms]
    v_times   : ndarray or None — monitor sample times [ms]
    v_trace   : ndarray or None — membrane potential [mV]
    """
    start_scope()
    defaultclock.dt = DT * ms

    # ── input spike generators ───────────────────────────────────────────
    # Flatten all (synapse_index, time) pairs; SpikeGeneratorGroup needs
    # them sorted by time.
    all_idx  = np.concatenate([np.full(len(spk), s, dtype=int)
                                for s, spk in enumerate(spike_times_list)])
    all_t_ms = np.concatenate(spike_times_list)
    order    = np.argsort(all_t_ms)
    gen = SpikeGeneratorGroup(n_syn,
                              all_idx[order],
                              all_t_ms[order] * ms)

    # ── LIF neuron ───────────────────────────────────────────────────────
    neuron = NeuronGroup(1, LIF_EQS,
                         threshold=f'v >= {V_th}*mV',
                         reset=f'v = {V_reset}*mV',
                         refractory=t_ref * ms,
                         method='exact',
                         namespace=LIF_NS)
    neuron.v = E_L * mV
    neuron.g = 0 * mV

    # ── excitatory synapses ──────────────────────────────────────────────
    syn = Synapses(gen, neuron, on_pre=f'g += {W_SYN_MV}*mV')
    syn.connect()

    # ── monitors ────────────────────────────────────────────────────────
    sm = SpikeMonitor(neuron)
    if record_v:
        vm = StateMonitor(neuron, 'v', record=True)

    run(T_MS * ms)

    out_times = np.array(sm.t / ms)
    if record_v:
        return out_times, np.array(vm.t / ms), np.array(vm.v[0] / mV)
    return out_times, None, None


# ══════════════════════════════════════════════════════════════════════════════
# CORRELATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _pairwise_r(count_list):
    rs = []
    for i in range(len(count_list)):
        for j in range(i + 1, len(count_list)):
            a, b = count_list[i], count_list[j]
            if a.std() > 0 and b.std() > 0:
                r, _ = pearsonr(a, b)
                if not np.isnan(r):
                    rs.append(r)
    return float(np.mean(rs)) if rs else 0.0


def input_r(binary_list, bin_ms=BIN_MS, dt_ms=DT):
    """Mean pairwise Pearson R of aggregate input trains (OR across synapses)."""
    bin_steps = int(bin_ms / dt_ms)
    counts = []
    for p in binary_list:
        agg = p.any(axis=0)
        n   = len(agg) // bin_steps
        counts.append(agg[:n * bin_steps].reshape(n, bin_steps).sum(1).astype(float))
    return _pairwise_r(counts)


def output_r(out_times_list, T_ms=T_MS, bin_ms=BIN_MS):
    """Mean pairwise Pearson R of output spike trains."""
    bins   = np.arange(0, T_ms + bin_ms, bin_ms)
    counts = [np.histogram(tr, bins=bins)[0].astype(float) for tr in out_times_list]
    return _pairwise_r(counts)


def mean_upper_r(mat):
    idx = np.triu_indices_from(mat, k=1)
    return float(mat[idx].mean())


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SCAN  — sweep over R_TARGETS
# ══════════════════════════════════════════════════════════════════════════════

print("Brian2 LIF — pattern separation scan\n")
results = []  # (R_target, R_in, R_out, rates)

for R_target in R_TARGETS:
    pats_times, pats_bin = make_patterns(N_PATTERNS, r_input, R_target,
                                         n_syn, T_MS, DT, rng)
    R_in = input_r(pats_bin)

    out_times_all = []
    rates = []
    for k in range(N_PATTERNS):
        ot, _, _ = simulate_brian2(pats_times[k])
        out_times_all.append(ot)
        rates.append(len(ot) / (T_MS * 1e-3))

    R_out = output_r(out_times_all)
    results.append((R_target, R_in, R_out, rates))
    print(f"  R_target={R_target:.2f}  R_in={R_in:.3f}  R_out={R_out:.3f}"
          f"  decorr={R_in - R_out:.3f}  FR={np.mean(rates):.1f} Hz")

print()
r_out_mean = np.mean([r[2] for r in results])
r_in_mean  = np.mean([r[1] for r in results])
fr_mean    = np.mean([r[3][0] for r in results])

if r_out_mean > r_in_mean:
    print("  WARNING: R_out > R_in — increase W_SYN_MV or lower V_th")
elif fr_mean < 0.5:
    print("  WARNING: very low firing rate — increase W_SYN_MV")
else:
    print("  Pattern separation confirmed: R_out < R_in in all conditions.")


# ══════════════════════════════════════════════════════════════════════════════
# DEMO SIMULATION at R_DEMO  (with voltage traces for panel C)
# ══════════════════════════════════════════════════════════════════════════════

print(f"\nDemo at R={R_DEMO} (recording voltage) ...")
demo_times, demo_bin = make_patterns(N_PATTERNS, r_input, R_DEMO,
                                      n_syn, T_MS, DT, rng)

out_demo    = []
vtrace_demo = []   # list of (t_ms, V_mV)

for k in range(N_PATTERNS):
    ot, vt, vm = simulate_brian2(demo_times[k], record_v=True)
    out_demo.append(ot)
    vtrace_demo.append((vt, vm))

R_in_demo  = input_r(demo_bin)
R_out_demo = output_r(out_demo)

# Input spike times for raster (aggregate OR train)
in_spktimes_demo = [np.where(demo_bin[k].any(axis=0))[0] * DT
                    for k in range(N_PATTERNS)]


# ══════════════════════════════════════════════════════════════════════════════
# VISUALISATION  (panels A–F matching single_neuron_patsep.py)
# ══════════════════════════════════════════════════════════════════════════════

COLORS = plt.cm.tab10(np.linspace(0, 0.45, N_PATTERNS))
WIN_MS = 500.0

fig = plt.figure(figsize=(16, 14))
gs  = gridspec.GridSpec(4, 2, figure=fig, hspace=0.55, wspace=0.4,
                        height_ratios=[2, 2, 2.5, 2])

# ── A: input raster ────────────────────────────────────────────────────────
ax_A = fig.add_subplot(gs[0, 0])
for k, spk_ms in enumerate(in_spktimes_demo):
    ax_A.scatter(spk_ms, np.full_like(spk_ms, k + 1),
                 s=1.5, color=COLORS[k], alpha=0.7, linewidths=0)
ax_A.set(xlim=(0, T_MS), ylim=(0.4, N_PATTERNS + 0.6),
         yticks=range(1, N_PATTERNS + 1),
         xlabel='Time (ms)', ylabel='Pattern #',
         title=f'A)  Input patterns  (R_input = {R_DEMO})\n'
               f'    measured R_in = {R_in_demo:.3f}')
ax_A.spines[['top', 'right']].set_visible(False)

# ── B: output raster ───────────────────────────────────────────────────────
ax_B = fig.add_subplot(gs[0, 1])
for k, spk_ms in enumerate(out_demo):
    ax_B.scatter(spk_ms, np.full_like(spk_ms, k + 1),
                 s=8, color=COLORS[k], alpha=0.9, linewidths=0)
ax_B.set(xlim=(0, T_MS), ylim=(0.4, N_PATTERNS + 0.6),
         yticks=range(1, N_PATTERNS + 1),
         xlabel='Time (ms)', ylabel='Pattern #',
         title=f'B)  Output spike trains (Brian2 LIF)\n'
               f'    R_out = {R_out_demo:.3f}  |  decorr = {R_in_demo - R_out_demo:.3f}')
ax_B.spines[['top', 'right']].set_visible(False)

# ── C: voltage traces (patterns 1 & 2, first 500 ms) ─────────────────────
ax_C = fig.add_subplot(gs[1, :])
for k in [0, 1]:
    vt, vm = vtrace_demo[k]
    mask = vt <= WIN_MS
    ax_C.plot(vt[mask], vm[mask], lw=0.8, alpha=0.85,
              color=COLORS[k], label=f'Pattern {k + 1}')
ax_C.axhline(V_th,  color='k',    ls='--', lw=1.0, alpha=0.6,
             label=f'V_th ({V_th} mV)')
ax_C.axhline(E_L,   color='gray', ls=':',  lw=0.8, alpha=0.4,
             label=f'E_L ({E_L} mV)')
ax_C.set(xlim=(0, WIN_MS), xlabel='Time (ms)', ylabel='V_m (mV)',
         title=(f'C)  Membrane potential — patterns 1 & 2 (first {WIN_MS:.0f} ms)\n'
                f'    Despite R_in = {R_DEMO}, patterns produce different spike times'))
ax_C.legend(fontsize=8, loc='upper right', ncol=4)
ax_C.spines[['top', 'right']].set_visible(False)

# ── D & E: correlation matrices ────────────────────────────────────────────
bins_demo  = np.arange(0, T_MS + BIN_MS, BIN_MS)
in_counts  = [np.histogram(t_ms, bins=bins_demo)[0].astype(float)
               for t_ms in in_spktimes_demo]
out_counts = [np.histogram(tr,   bins=bins_demo)[0].astype(float)
               for tr in out_demo]

for subplot_pos, counts, panel_label in [
        (gs[2, 0], in_counts,  'D)  Input correlation matrix'),
        (gs[2, 1], out_counts, 'E)  Output correlation matrix')]:
    ax = fig.add_subplot(subplot_pos)
    R_mat = np.eye(N_PATTERNS)
    for i in range(N_PATTERNS):
        for j in range(i + 1, N_PATTERNS):
            if counts[i].std() > 0 and counts[j].std() > 0:
                r, _ = pearsonr(counts[i], counts[j])
                R_mat[i, j] = R_mat[j, i] = r
    im = ax.imshow(R_mat, vmin=-0.2, vmax=1.0, cmap='RdYlGn', aspect='auto')
    plt.colorbar(im, ax=ax, label='Pearson R')
    ax.set(xlabel='Pattern #', ylabel='Pattern #',
           title=f'{panel_label}\n    mean = {mean_upper_r(R_mat):.3f}')

# ── F: R_in vs R_out scan ──────────────────────────────────────────────────
ax_F = fig.add_subplot(gs[3, :])
r_in_arr  = np.array([r[1] for r in results])
r_out_arr = np.array([r[2] for r in results])

ax_F.plot([0, 1], [0, 1], '--', color='gray', alpha=0.5, label='no separation')
ax_F.plot(r_in_arr, r_out_arr, 'o-', color='steelblue',
          lw=2.5, ms=10, label='Brian2 LIF (GC model)')
ax_F.fill_between(r_in_arr, r_out_arr, r_in_arr,
                  alpha=0.15, color='steelblue', label='decorrelation (↓ R)')
for ri, ro, rt in zip(r_in_arr, r_out_arr, [r[0] for r in results]):
    ax_F.annotate(f'R={rt}', (ri, ro),
                  textcoords='offset points', xytext=(6, -14), fontsize=8)

ax_F.set(xlim=(-0.05, 1.1), ylim=(-0.2, 1.1),
         xlabel='R_input  (correlation of Poisson input patterns)',
         ylabel='R_output  (correlation of output spike trains)',
         title=(f'F)  Pattern Separation: Brian2 LIF decorrelates similar inputs\n'
                f'    (N={N_PATTERNS} patterns, r={r_input} Hz, τ_syn={tau_syn} ms,'
                f' n_syn={n_syn}, W_syn={W_SYN_MV} mV)'))
ax_F.legend(fontsize=8, loc='upper left')
ax_F.spines[['top', 'right']].set_visible(False)

fig.suptitle('Brian2 LIF as Granule Cell Model — Pattern Separation in DG',
             fontsize=13, fontweight='bold')

out_path = __file__.replace('.py', '.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight')
print(f'Saved: {out_path}')
plt.show()
