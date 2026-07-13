"""
make_en_figures.py — English-labelled figures for the DG presentation.

Builds (into prezentacja/):
  fig_network_en.png     — small DG network (connections actually visible)
  fig_circuit_en.png     — circuit + FF/FB/full comparison
  fig_freq_en.png        — frequency audit (steady-state g_ex + measured GC output)
  fig_bifurcation_en.png — K_tonic bifurcation (f-I curves, G_crit(K), phase plane)
  fig_capacity_en.png    — pattern capacity: mean correlation vs number of patterns

Originals (Polish) in the repo root are left untouched.

Run:  snn_sep_venv/Scripts/python.exe prezentacja/make_en_figures.py
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch, Circle
from matplotlib.collections import LineCollection

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from brian2 import (
    start_scope, NeuronGroup, Synapses, SpikeMonitor, SpikeGeneratorGroup,
    PoissonGroup, Network, run, defaultclock, ms, mV, Hz, prefs,
)
prefs.codegen.target = 'numpy'

HERE = os.path.dirname(os.path.abspath(__file__))
def out(name):
    return os.path.join(HERE, name)

# ── Palette ───────────────────────────────────────────────────────────────────
C_GC, C_FS, C_HMC, C_PP = '#1565C0', '#C62828', '#E65100', '#2E7D32'
C_EX, C_IN, C_DIM = '#212121', '#6A1B9A', '#C8C8C8'

# ── Model constants (canon: dg_params) ────────────────────────────────────────
A_GC, B_GC, C_GC_, D_GC = 0.02, 0.2, -65.0, 6.0
A_FS, B_FS, C_FS_, D_FS = 0.10, 0.2, -65.0, 2.0
A_HMC, B_HMC, C_HMC_, D_HMC = 0.02, 0.2, -65.0, 4.0
TAU_EX_GC, TAU_IN_GC, TAU_EX_FS, TAU_EX_HMC = 5.0, 8.0, 3.0, 5.0
K_GC, K_FS, K_HMC = 10.0, 5.0, 10.0
R_EFF_HIGH, R_EFF_LOW = 400.0, 40.0
W_PP_GC, W_PP_FS, W_GC_FS, W_FS_GC = 4.0, 0.25, 10.0, 1.0
W_GC_HMC, W_HMC_FS, W_HMC_GC = 1.0, 1.0, 0.5
P_PP_FS, P_GC_FS, P_FS_GC, P_GC_HMC, P_HMC_FS, P_HMC_GC = .40, .40, .50, .25, .40, .40
DT_MS = 0.1


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — small network (connections visible)
# ══════════════════════════════════════════════════════════════════════════════
def fig_network(N_GC=25, N_FS=6, N_HMC=4):
    rng = np.random.default_rng(0)
    def pairs(Ns, Nt, p):
        s, t = np.where(rng.random((Ns, Nt)) < p)
        return s.astype(int), t.astype(int)
    conn = {
        'pp_fs': pairs(N_GC, N_FS, P_PP_FS), 'gc_fs': pairs(N_GC, N_FS, P_GC_FS),
        'fs_gc': pairs(N_FS, N_GC, P_FS_GC), 'gc_hmc': pairs(N_GC, N_HMC, P_GC_HMC),
        'hmc_fs': pairs(N_HMC, N_FS, P_HMC_FS), 'hmc_gc': pairs(N_HMC, N_GC, P_HMC_GC),
    }

    def column(n, x, y_lo, y_hi):
        ys = np.linspace(y_hi, y_lo, n) if n > 1 else np.array([(y_lo + y_hi) / 2])
        return np.column_stack([np.full(n, x), ys])
    POS = {'PP': column(N_GC, 0.0, 0.0, 10.0), 'GC': column(N_GC, 4.0, 0.0, 10.0),
           'FS': column(N_FS, 8.5, 5.6, 10.0), 'HMC': column(N_HMC, 8.5, 0.0, 4.4)}

    def seg(src, si, dst, ti):
        return np.stack([POS[src][si], POS[dst][ti]], axis=1)
    pp_gc = np.arange(N_GC)
    edges = [
        ('PP→GC  (exc.)',  seg('PP', pp_gc, 'GC', pp_gc),                       C_PP,  0.55, '-'),
        ('PP→FS  (exc.)',  seg('GC', conn['pp_fs'][0], 'FS', conn['pp_fs'][1]),  C_PP,  0.45, '-'),
        ('GC→FS  (exc.)',  seg('GC', conn['gc_fs'][0], 'FS', conn['gc_fs'][1]),  C_GC,  0.40, '-'),
        ('FS→GC  (inhib.)',seg('FS', conn['fs_gc'][0], 'GC', conn['fs_gc'][1]),  C_IN,  0.35, '-'),
        ('GC→HMC (exc.)',  seg('GC', conn['gc_hmc'][0], 'HMC', conn['gc_hmc'][1]),C_HMC, 0.45, '-'),
        ('HMC→FS (exc.)',  seg('HMC', conn['hmc_fs'][0], 'FS', conn['hmc_fs'][1]),C_HMC, 0.55, '-'),
        ('HMC→GC (exc.)',  seg('HMC', conn['hmc_gc'][0], 'GC', conn['hmc_gc'][1]),C_HMC, 0.45, '--'),
    ]
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(-1.2, 11.5); ax.set_ylim(-1.2, 11.4); ax.axis('off')
    legend = []
    for label, segs, color, alpha, ls in edges:
        ax.add_collection(LineCollection(segs, colors=color, linewidths=1.1,
                                         alpha=alpha, linestyles=ls, zorder=1))
        legend.append(mpatches.Patch(color=color, label=f'{label}  —  {segs.shape[0]} synapses'))
    for name, pos, color in [('PP', POS['PP'], C_PP), ('GC', POS['GC'], C_GC),
                             ('FS', POS['FS'], C_FS), ('HMC', POS['HMC'], C_HMC)]:
        ax.scatter(pos[:, 0], pos[:, 1], s=130, c=color, edgecolors='white',
                   linewidths=1.0, zorder=5)
    ax.text(0.0, 10.8, f'PP\n(input, 1:1)\nN={N_GC}', ha='center', va='bottom',
            fontsize=12, fontweight='bold', color=C_PP)
    ax.text(4.0, 10.8, f'GC\n(granule)\nN={N_GC}', ha='center', va='bottom',
            fontsize=12, fontweight='bold', color=C_GC)
    ax.text(8.5, 10.55, f'FS (inhibitory)  N={N_FS}', ha='center', va='bottom',
            fontsize=12, fontweight='bold', color=C_FS)
    ax.text(8.5, 4.6, f'HMC (mossy)  N={N_HMC}', ha='center', va='bottom',
            fontsize=12, fontweight='bold', color=C_HMC)
    n_tot = sum(s.shape[0] for _, s, *_ in edges)
    ax.legend(handles=legend, loc='lower left', fontsize=10, framealpha=0.95,
              edgecolor='gray', bbox_to_anchor=(-0.02, -0.02),
              title=f'Synapses ({n_tot} total)')
    ax.set_title(f'DG network at single-neuron resolution (small example)\n'
                 f'each dot = 1 neuron, each line = 1 synapse  '
                 f'(N_GC={N_GC}, N_FS={N_FS}, N_HMC={N_HMC}, seed=0)',
                 fontsize=14, fontweight='bold', pad=14)
    fig.savefig(out('fig_network_en.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('Saved fig_network_en.png')


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — circuit + FF/FB/full comparison
# ══════════════════════════════════════════════════════════════════════════════
def fig_circuit():
    POS = {'PP': np.array([1.8, 5.0]), 'GC': np.array([5.0, 5.0]),
           'FS': np.array([7.6, 7.6]), 'HMC': np.array([7.6, 2.4])}
    RAD = {'PP': 0.72, 'GC': 1.05, 'FS': 0.75, 'HMC': 0.65}
    FC = {'PP': C_PP, 'GC': C_GC, 'FS': C_FS, 'HMC': C_HMC}
    FULL = {'PP': 'PP\n(input)\n40 fibers\n~10 Hz/fib.',
            'GC': 'GC\n200 cells\nreg. spiking\na=0.02, d=6',
            'FS': 'FS\n20 cells\nfast spiking\na=0.10, d=2',
            'HMC': 'HMC\n10 cells\nreg. spiking\na=0.02, d=4'}
    SHORT = {k: k for k in POS}
    CONNS = [
        ('pp_gc', 'PP', 'GC', 'ex', 0.00, 'AMPA\nW=4mV, τ=5ms\ndelay=4ms', 0.00, 0.68),
        ('pp_fs', 'PP', 'FS', 'ex', 0.15, 'AMPA\nW=0.25mV\nτ=3ms', -0.30, 0.40),
        ('gc_fs', 'GC', 'FS', 'ex', 0.28, 'AMPA\nW=10mV\nτ=3ms', 0.65, 0.15),
        ('fs_gc', 'FS', 'GC', 'in', -0.28, 'GABA-A\nW=1mV\nτ=8ms', -0.65, -0.15),
        ('gc_hmc', 'GC', 'HMC', 'ex', 0.28, 'AMPA\nW=1mV', 0.65, -0.15),
        ('hmc_fs', 'HMC', 'FS', 'ex', 0.00, 'AMPA\nW=1mV', 0.45, 0.25),
        ('hmc_gc', 'HMC', 'GC', 'ex', -0.28, 'AMPA\nW=0.5mV', -0.65, 0.15),
    ]
    COND_C = {'baseline': '#757575', 'ff_only': '#1976D2',
              'fb_only': '#D32F2F', 'full': '#2E7D32'}

    def active(cid, ff, fb):
        if cid in {'pp_gc', 'gc_hmc', 'hmc_fs', 'hmc_gc'}: return True
        if cid == 'pp_fs': return ff
        if cid == 'gc_fs': return fb
        if cid == 'fs_gc': return ff or fb
        return False

    def unit(p1, p2):
        d = p2 - p1; return d / np.linalg.norm(d)

    def arrow(ax, src, dst, st, act, crv, label, loff):
        p1, p2 = POS[src], POS[dst]; u = unit(p1, p2)
        s, e = tuple(p1 + RAD[src]*u), tuple(p2 - RAD[dst]*u)
        col = (C_EX if st == 'ex' else C_IN) if act else C_DIM
        ax.add_patch(FancyArrowPatch(s, e, arrowstyle='->' if st == 'ex' else '-[',
                     color=col, linewidth=2.0 if act else 0.9, alpha=1.0 if act else 0.32,
                     connectionstyle=f'arc3,rad={crv}', mutation_scale=13, zorder=4))
        if label and act:
            mid = 0.5*(np.array(s)+np.array(e))
            span = np.linalg.norm(np.array(e)-np.array(s))
            perp = np.array([-u[1], u[0]])*crv*span*0.5
            lp = mid + perp + np.array(loff)
            ax.text(lp[0], lp[1], label, fontsize=5.2, ha='center', va='center',
                    color=col, zorder=7, bbox=dict(boxstyle='round,pad=0.18', fc='white',
                    ec=col, lw=0.5, alpha=0.93))

    def nodes(ax, full):
        for n, xy in POS.items():
            ax.add_patch(Circle(tuple(xy), RAD[n], fc=FC[n], ec='black', lw=1.4, zorder=5))
            ax.text(*xy, FULL[n] if full else SHORT[n], ha='center', va='center',
                    fontsize=5.0 if full else 8.5, fontweight='bold', color='white',
                    zorder=6, multialignment='center')

    def panel(ax, ff, fb, title, dec=None, full=True, cc='black'):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(title + (f'\n(decorr@100ms = {dec})' if dec else ''),
                     fontsize=8.5 if not full else 11, fontweight='bold', color=cc, pad=5)
        nodes(ax, full)
        for cid, src, dst, stype, crv, lbl, lx, ly in CONNS:
            arrow(ax, src, dst, stype, active(cid, ff, fb), crv,
                  lbl if full else None, (lx, ly))

    fig = plt.figure(figsize=(18, 11))
    gs = gridspec.GridSpec(2, 4, figure=fig, height_ratios=[1.7, 1.0], hspace=0.30, wspace=0.12)
    axm = fig.add_subplot(gs[0, :])
    panel(axm, True, True, 'Full dentate gyrus circuit (DG microcircuit) — Izhikevich neurons')
    axm.legend(handles=[mpatches.Patch(color=C_EX, label='Excitatory (AMPA, →)'),
                        mpatches.Patch(color=C_IN, label='Inhibitory (GABA-A, ⊣)'),
                        mpatches.Patch(color=C_DIM, label='Inactive in this condition')],
               loc='lower left', fontsize=8, framealpha=0.92, edgecolor='gray',
               bbox_to_anchor=(0.01, 0.01))
    info = ('Network parameters:\nN_GC=200  N_FS=20  N_HMC=10\n'
            'dt=0.1 ms,  T_sim=600 ms\nK_tonic: GC=10, FS=5, HMC=10\n'
            'P_active=0.25  R_eff_high=400 Hz\nSpike threshold: v ≥ 30 mV')
    axm.text(9.85, 0.25, info, ha='right', va='bottom', fontsize=6.5, zorder=8,
             bbox=dict(boxstyle='round,pad=0.45', fc='#FAFAFA', ec='#BDBDBD', lw=0.8))
    axm.text(3.6, 8.8, 'FF pathway (feedforward):\nPP→FS→GC', ha='center', va='center',
             fontsize=7.5, color=COND_C['ff_only'],
             bbox=dict(boxstyle='round,pad=0.35', fc='#E3F2FD', ec=COND_C['ff_only'], lw=1.2))
    axm.text(6.6, 1.2, 'FB pathway (feedback):\nGC→FS→GC', ha='center', va='center',
             fontsize=7.5, color=COND_C['fb_only'],
             bbox=dict(boxstyle='round,pad=0.35', fc='#FFEBEE', ec=COND_C['fb_only'], lw=1.2))
    axm.text(3.0, 1.6, 'Always active:\nPP→GC', ha='center', va='center', fontsize=7.5,
             color='#555555', bbox=dict(boxstyle='round,pad=0.35', fc='#F5F5F5', ec='#AAAAAA', lw=0.8))
    conds = [('baseline', False, False, 'Baseline\n(no inhibition)', '+0.153'),
             ('ff_only', True, False, 'Feedforward\nPP→FS→GC', '+0.321'),
             ('fb_only', False, True, 'Feedback\nGC→FS→GC', '+0.254'),
             ('full', True, True, 'Full circuit\nFF + FB', '+0.420')]
    for ci, (cn, ff, fb, ti, dec) in enumerate(conds):
        panel(fig.add_subplot(gs[1, ci]), ff, fb, ti, dec=dec, full=False, cc=COND_C[cn])
    fig.suptitle('Dentate gyrus circuit schematic\nInhibition types — Feedforward vs Feedback',
                 fontsize=13, fontweight='bold', y=1.01)
    fig.savefig(out('fig_circuit_en.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('Saved fig_circuit_en.png')


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — frequency audit
# ══════════════════════════════════════════════════════════════════════════════
GC_EQS_SOLO = (
    f"dv/dt  = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms + g_ex/ms - {K_GC}*mV/ms) : volt (unless refractory)\n"
    f"dg_ex/dt = -g_ex/({TAU_EX_GC}*ms) : volt\n"
    f"du/dt  = {A_GC}/ms*({B_GC}*v - u) : volt\n"
)

def measure_gc_output(r_agg, n_trials=8, T_ms=1000.0):
    start_scope(); defaultclock.dt = DT_MS*ms
    pp = PoissonGroup(n_trials, rates=r_agg*Hz)
    gc = NeuronGroup(n_trials, GC_EQS_SOLO, threshold='v>=30*mV',
                     reset=f'v={C_GC_}*mV; u=u+{D_GC}*mV', refractory=2*ms, method='euler')
    gc.v = -70*mV; gc.u = B_GC*(-70*mV); gc.g_ex = 0*mV
    syn = Synapses(pp, gc, on_pre=f'g_ex_post += {W_PP_GC}*mV', delay=4*ms)
    syn.connect(i=np.arange(n_trials), j=np.arange(n_trials))
    sm = SpikeMonitor(gc); run(T_ms*ms)
    rates = np.array(sm.count)/(T_ms*1e-3)
    return float(rates.mean()), float(rates.std())

def fig_freq():
    G_crit = 4.0 + K_GC
    g_ss = lambda r: r*W_PP_GC*(TAU_EX_GC*1e-3)
    rates_in = [40, 100, 200, 300, 400, 500, 600, 800, 1000]
    om, os_ = [], []
    for r in rates_in:
        m, s = measure_gc_output(r); om.append(m); os_.append(s)
        print(f'  freq: {r:>4} Hz -> GC {m:5.1f} Hz')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    rr = np.linspace(0, 1050, 200); gg = g_ss(rr)
    ax1.plot(rr, gg, color='steelblue', lw=2, label='⟨g_ex⟩ = r·W·τ')
    ax1.axhline(G_crit, color='crimson', ls='--', lw=1.5, label=f'G_crit ≈ {G_crit:.0f} mV (K={K_GC:.0f})')
    ax1.axvline(400, color=C_PP, ls=':', lw=1.5, label='chosen "active" = 400 Hz')
    ax1.axvline(600, color='gray', ls=':', lw=1.2, label='previous = 600 Hz')
    ax1.fill_between(rr, 0, G_crit, color='green', alpha=0.06)
    ax1.fill_between(rr, G_crit, gg.max(), color='red', alpha=0.06)
    ax1.set(xlabel='Aggregate input rate r_agg [Hz]', ylabel='⟨g_ex⟩ [mV]',
            title='A) Steady-state excitation vs bifurcation threshold\n'
                  'green = fluctuation-driven, red = mean-driven')
    ax1.legend(fontsize=8, loc='upper left'); ax1.spines[['top', 'right']].set_visible(False)
    ax2.errorbar(rates_in, om, yerr=os_, fmt='o-', color='darkorange', lw=2, ms=7,
                 capsize=3, label='measured GC output')
    ax2.axhspan(1, 10, color='green', alpha=0.10, label='DG target: 1–10 Hz (active)')
    ax2.axhline(25, color='crimson', ls='--', lw=1.2, label='25 Hz (too fast)')
    ax2.axvline(400, color=C_PP, ls=':', lw=1.5, label='chosen "active" = 400 Hz')
    ax2.set(xlabel='Aggregate input rate r_agg [Hz]', ylabel='GC output firing rate [Hz]',
            title='B) Measured output of a real GC neuron\n(Izhikevich, circuit parameters)')
    ax2.legend(fontsize=8, loc='upper left'); ax2.spines[['top', 'right']].set_visible(False)
    fig.suptitle('DG frequency audit — choosing the input drive (400 Hz → GC ~6 Hz)',
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out('fig_freq_en.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('Saved fig_freq_en.png')


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — K_tonic bifurcation
# ══════════════════════════════════════════════════════════════════════════════
def G_crit_an(b, K):
    return (5.0 - b)**2/0.16 - 140.0 + K

def measure_fi(a, b, c, d, g_vals, K_vals, T_ms=1000.0):
    start_scope(); defaultclock.dt = 0.1*ms
    GG, KK = np.meshgrid(g_vals, K_vals)
    g_flat, k_flat = GG.ravel(), KK.ravel()
    eqs = """
    dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms + gin - Kc) : volt (unless refractory)
    du/dt = a_p*(b_p*v - u) : volt
    gin : volt/second
    Kc  : volt/second
    a_p : 1/second
    b_p : 1
    """
    G = NeuronGroup(g_flat.size, eqs, threshold='v>=30*mV',
                    reset=f'v={c}*mV; u=u+{d}*mV',
                    refractory=(1.0 if a > 0.05 else 2.0)*ms, method='euler')
    G.v = -70*mV; G.u = b*(-70*mV)
    G.gin = g_flat*mV/ms; G.Kc = k_flat*mV/ms; G.a_p = a/ms; G.b_p = b
    sm = SpikeMonitor(G); run(T_ms*ms)
    return (np.array(sm.count)/(T_ms*1e-3)).reshape(GG.shape)

def fig_bifurcation():
    g_drive = R_EFF_HIGH*W_PP_GC*(TAU_EX_GC*1e-3)
    g_vals = np.linspace(0, 30, 121)
    K_show = [0.0, 5.0, 10.0, 15.0]
    fi = measure_fi(A_GC, B_GC, C_GC_, D_GC, g_vals, K_show)
    K_fine = np.linspace(0, 20, 41)
    fi_fine = measure_fi(A_GC, B_GC, C_GC_, D_GC, g_vals, K_fine)
    g_emp = np.array([(g_vals[np.where(fi_fine[i] > 1.0)[0][0]]
                       if np.any(fi_fine[i] > 1.0) else np.nan) for i in range(len(K_fine))])
    fig = plt.figure(figsize=(16, 6.0)); gs = fig.add_gridspec(1, 3, wspace=0.30)
    axA = fig.add_subplot(gs[0, 0])
    colors = plt.cm.viridis(np.linspace(0.1, 0.85, len(K_show)))
    for i, K in enumerate(K_show):
        axA.plot(g_vals, fi[i], color=colors[i], lw=2, label=f'K = {K:.0f}')
        axA.axvline(G_crit_an(B_GC, K), color=colors[i], ls=':', lw=1, alpha=0.6)
    axA.axvline(g_drive, color='crimson', ls='--', lw=1.5, label=f'400 Hz drive ≈ {g_drive:.0f} mV')
    axA.set(xlabel='Constant g_ex [mV]', ylabel='GC firing rate [Hz]',
            title='A) f–I curves: K shifts the threshold right\n(each dotted line = G_crit = 4+K)')
    axA.legend(fontsize=8, loc='upper left'); axA.spines[['top', 'right']].set_visible(False)
    axB = fig.add_subplot(gs[0, 1])
    axB.plot(K_fine, 4.0 + K_fine, color='steelblue', lw=2, label='analytic G_crit = 4 + K')
    axB.plot(K_fine, g_emp, 'o', color='darkorange', ms=3, alpha=0.7, label='measured (Brian2)')
    for K_op, lbl, col in [(K_FS, 'FS', C_FS), (K_GC, 'GC', C_GC)]:
        axB.scatter([K_op], [G_crit_an(0.2, K_op)], s=80, color=col, zorder=5,
                    edgecolor='black', linewidth=0.8)
        axB.annotate(f'{lbl}\nK={K_op:.0f}→{G_crit_an(0.2, K_op):.0f}mV',
                     (K_op, G_crit_an(0.2, K_op)), textcoords='offset points',
                     xytext=(8, -18), fontsize=8, color=col)
    axB.set(xlabel='K_tonic', ylabel='G_crit (g_ex threshold) [mV]',
            title='B) Threshold grows linearly with K\n(tonic GABA → less excitable neuron)')
    axB.legend(fontsize=8, loc='upper left'); axB.spines[['top', 'right']].set_visible(False)
    axC = fig.add_subplot(gs[0, 2])
    v = np.linspace(-80, -40, 300)
    for g_ex_d, style, lbl in [(8.0, '-', 'g_ex=8 (400 Hz, subthreshold)'),
                               (20.0, '--', 'g_ex=20 (suprathreshold)')]:
        axC.plot(v, 0.04*v**2 + 5*v + 140 + (g_ex_d - K_GC), color='teal', ls=style,
                 lw=1.8, label=f'v-nullcline: {lbl}')
    axC.plot(v, B_GC*v, color='purple', lw=1.8, label='u-nullcline: u = b·v')
    axC.set(xlabel='v [mV]', ylabel='u [mV]', ylim=(-20, 10),
            title=f'C) GC phase plane (K={K_GC:.0f})\nintersections = fixed points; none ⟹ neuron fires')
    axC.legend(fontsize=7, loc='upper center'); axC.spines[['top', 'right']].set_visible(False)
    fig.suptitle('K_tonic = tonic inhibitory current → raises the firing threshold G_crit = 4 + K',
                 fontsize=13, fontweight='bold', y=0.99)
    fig.subplots_adjust(top=0.78, bottom=0.12, left=0.05, right=0.98)
    fig.savefig(out('fig_bifurcation_en.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('Saved fig_bifurcation_en.png')


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — pattern capacity (mean correlation vs number of patterns)
# ══════════════════════════════════════════════════════════════════════════════
def _izh_gc():
    return (f"dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms + g_ex/ms - g_in/ms - {K_GC}*mV/ms) : volt (unless refractory)\n"
            f"dg_ex/dt = -g_ex/({TAU_EX_GC}*ms) : volt\n"
            f"dg_in/dt = -g_in/({TAU_IN_GC}*ms) : volt\n"
            f"du/dt = {A_GC}/ms*({B_GC}*v - u) : volt\n")
def _izh_fs():
    return (f"dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms + g_ex/ms - {K_FS}*mV/ms) : volt (unless refractory)\n"
            f"dg_ex/dt = -g_ex/({TAU_EX_FS}*ms) : volt\n"
            f"du/dt = {A_FS}/ms*({B_FS}*v - u) : volt\n")
def _izh_hmc():
    return (f"dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms + g_ex/ms - {K_HMC}*mV/ms) : volt (unless refractory)\n"
            f"dg_ex/dt = -g_ex/({TAU_EX_HMC}*ms) : volt\n"
            f"du/dt = {A_HMC}/ms*({B_HMC}*v - u) : volt\n")

def _conn(N_GC, N_FS, N_HMC):
    rng = np.random.default_rng(0)
    def pairs(Ns, Nt, p):
        s, t = np.where(rng.random((Ns, Nt)) < p)
        return s.astype(int), t.astype(int)
    return {'pp_fs': pairs(N_GC, N_FS, P_PP_FS), 'gc_fs': pairs(N_GC, N_FS, P_GC_FS),
            'fs_gc': pairs(N_FS, N_GC, P_FS_GC), 'gc_hmc': pairs(N_GC, N_HMC, P_GC_HMC),
            'hmc_fs': pairs(N_HMC, N_FS, P_HMC_FS), 'hmc_gc': pairs(N_HMC, N_GC, P_HMC_GC)}

def _patterns(N_GC, N_pat, R_in, P_active, seed=42):
    rng = np.random.default_rng(seed)
    common = rng.random(N_GC) < (P_active*R_in)
    pats = np.zeros((N_pat, N_GC), dtype=bool)
    for k in range(N_pat):
        pats[k] = common | (rng.random(N_GC) < P_active*(1.0-R_in))
    return pats

def _input_spikes(active, T_ms, seed):
    rng = np.random.default_rng(seed)
    n_steps = int(T_ms/DT_MS); idx, tt = [], []
    for i, a in enumerate(active):
        p = (R_EFF_HIGH if a else R_EFF_LOW)*DT_MS*1e-3
        ts = np.where(rng.random(n_steps) < p)[0].astype(float)*DT_MS
        ts = ts[(ts > 0) & (ts < T_ms)]
        if len(ts):
            idx.append(np.full(len(ts), i)); tt.append(ts)
    if idx:
        idx = np.concatenate(idx); tt = np.concatenate(tt); o = np.argsort(tt)
        return idx[o].astype(int), tt[o]
    return np.array([], int), np.array([])

def _simulate(active, conn, N_GC, N_FS, N_HMC, T_ms, seed):
    start_scope(); defaultclock.dt = DT_MS*ms
    idx, t_ms = _input_spikes(active, T_ms, seed)
    pp = SpikeGeneratorGroup(N_GC, idx, t_ms*ms)
    gc = NeuronGroup(N_GC, _izh_gc(), threshold='v>=30*mV',
                     reset=f'v={C_GC_}*mV; u=u+{D_GC}*mV', refractory=2*ms, method='euler')
    fs = NeuronGroup(N_FS, _izh_fs(), threshold='v>=30*mV',
                     reset=f'v={C_FS_}*mV; u=u+{D_FS}*mV', refractory=1*ms, method='euler')
    hmc = NeuronGroup(N_HMC, _izh_hmc(), threshold='v>=30*mV',
                      reset=f'v={C_HMC_}*mV; u=u+{D_HMC}*mV', refractory=2*ms, method='euler')
    gc.v = -70*mV; gc.u = B_GC*(-70*mV)
    fs.v = -70*mV; fs.u = B_FS*(-70*mV)
    hmc.v = -70*mV; hmc.u = B_HMC*(-70*mV)
    objs = [pp, gc, fs, hmc]
    def syn(src, tgt, si, ti, w, var, d):
        if len(si) == 0: return None
        sy = Synapses(src, tgt, on_pre=f'{var}_post += {w}*mV', delay=d*ms)
        sy.connect(i=si, j=ti); return sy
    s = Synapses(pp, gc, on_pre=f'g_ex_post += {W_PP_GC}*mV', delay=4*ms)
    s.connect(i=np.arange(N_GC), j=np.arange(N_GC)); objs.append(s)
    for args in [(pp, fs, conn['pp_fs'][0], conn['pp_fs'][1], W_PP_FS, 'g_ex', 4),
                 (gc, fs, conn['gc_fs'][0], conn['gc_fs'][1], W_GC_FS, 'g_ex', 1),
                 (fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', 1),
                 (gc, hmc, conn['gc_hmc'][0], conn['gc_hmc'][1], W_GC_HMC, 'g_ex', 1),
                 (hmc, fs, conn['hmc_fs'][0], conn['hmc_fs'][1], W_HMC_FS, 'g_ex', 1),
                 (hmc, gc, conn['hmc_gc'][0], conn['hmc_gc'][1], W_HMC_GC, 'g_ex', 1)]:
        o = syn(*args)
        if o is not None: objs.append(o)
    sm = SpikeMonitor(gc); objs.append(sm)
    Network(*objs).run(T_ms*ms)
    return np.array(sm.i), np.array(sm.t/ms)

def _bin(i_arr, t_arr, N, T_ms, bin_ms=100.0):
    n_bins = max(1, int(T_ms/bin_ms)); mat = np.zeros((N, n_bins))
    if len(t_arr):
        bi = np.clip((t_arr/bin_ms).astype(int), 0, n_bins-1)
        for ci, b in zip(i_arr, bi): mat[ci, b] += 1
    return mat

def _mean_pairwise(mats):
    rs = []
    for i in range(len(mats)):
        for j in range(i+1, len(mats)):
            a, b = mats[i].ravel(), mats[j].ravel()
            if a.std() > 1e-9 and b.std() > 1e-9:
                r = float(np.corrcoef(a, b)[0, 1])
                if not np.isnan(r): rs.append(r)
    return float(np.mean(rs)) if rs else 0.0

def _pat_pairwise(pats, upto):
    rs = []
    for i in range(upto):
        for j in range(i+1, upto):
            a, b = pats[i].astype(float), pats[j].astype(float)
            if a.std() > 1e-9 and b.std() > 1e-9:
                rs.append(float(np.corrcoef(a, b)[0, 1]))
    return float(np.mean(rs)) if rs else 0.0

def fig_capacity(N_GC=200, N_FS=20, N_HMC=10, N_max=12, R_in=0.75, P_active=0.25, T_ms=600.0):
    conn = _conn(N_GC, N_FS, N_HMC)
    pats = _patterns(N_GC, N_max, R_in, P_active)
    gc_mats = []
    for k in range(N_max):
        i_arr, t_arr = _simulate(pats[k], conn, N_GC, N_FS, N_HMC, T_ms, seed=1042+k)
        gc_mats.append(_bin(i_arr, t_arr, N_GC, T_ms))
        fr = len(t_arr)/(T_ms*1e-3*N_GC)
        print(f'  capacity: pattern {k+1}/{N_max}  FR_GC={fr:4.1f} Hz')
    ns = list(range(2, N_max+1))
    r_in = [_pat_pairwise(pats, n) for n in ns]
    r_out = [_mean_pairwise(gc_mats[:n]) for n in ns]
    dec = [ri - ro for ri, ro in zip(r_in, r_out)]
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    ax.plot(ns, r_in, 'o-', color='#78909C', lw=2.2, ms=7, label='R_in  (input patterns)')
    ax.plot(ns, r_out, 'o-', color=C_GC, lw=2.2, ms=7, label='R_out  (GC output)')
    ax.fill_between(ns, r_out, r_in, color='green', alpha=0.10)
    ax.annotate('separation\n(decorrelation)', xy=(ns[len(ns)//2], 0.5*(r_in[len(ns)//2]+r_out[len(ns)//2])),
                fontsize=10, color=C_PP, ha='center', fontweight='bold')
    ax.set_xticks(ns)
    ax.set_xlabel('Number of patterns', fontsize=11)
    ax.set_ylabel('Mean pairwise correlation (Pearson R)', fontsize=11)
    ax.set_ylim(0, max(r_in)*1.15)
    ax.set_title('Pattern capacity — DG keeps output decorrelated\nas the number of patterns grows',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=10, loc='center right')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=0.25)
    fig.tight_layout()
    fig.savefig(out('fig_capacity_en.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved fig_capacity_en.png  (R_out spans {min(r_out):.3f}–{max(r_out):.3f})')


if __name__ == '__main__':
    print('Building English figures...')
    fig_network()
    fig_circuit()
    fig_freq()
    fig_bifurcation()
    fig_capacity()
    print('All figures done.')
