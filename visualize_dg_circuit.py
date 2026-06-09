"""
visualize_dg_circuit.py
Schemat sieci neuronowej zakrętu zębatego (DG microcircuit) — obwód modułu 3.

Pokazuje:
  - Pełny schemat sieci z opisanymi synapsami (wagi, stałe czasowe)
  - 4 warunki eksperymentalne z zaznaczonymi aktywnymi/nieaktywnymi połączeniami
    (baseline, ff_only, fb_only, full)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Circle
import matplotlib.gridspec as gridspec
import os

# ── Colors ────────────────────────────────────────────────────────────────────
C_GC  = '#1565C0'   # niebieski — granule cells
C_FS  = '#C62828'   # czerwony  — fast-spiking interneurons
C_HMC = '#E65100'   # pomarańczowy — hilar mossy cells
C_PP  = '#2E7D32'   # zielony   — perforant path input
C_EX  = '#212121'   # ciemny    — pobudzające (excitatory)
C_IN  = '#6A1B9A'   # fioletowy — hamujące (inhibitory)
C_DIM = '#C8C8C8'   # jasnoszary — nieaktywne

COND_COLORS = {
    'baseline': '#757575',
    'ff_only' : '#1976D2',
    'fb_only' : '#D32F2F',
    'full'    : '#2E7D32',
}

# ── Node geometry ─────────────────────────────────────────────────────────────
POS = {
    'PP' : np.array([1.8, 5.0]),
    'GC' : np.array([5.0, 5.0]),
    'FS' : np.array([7.6, 7.6]),
    'HMC': np.array([7.6, 2.4]),
}
RAD = {'PP': 0.72, 'GC': 1.05, 'FS': 0.75, 'HMC': 0.65}
FC  = {'PP': C_PP,  'GC': C_GC,  'FS': C_FS,  'HMC': C_HMC}

FULL_LABELS = {
    'PP' : 'PP\n(wejście)\n40 włókien\n~15 Hz/wł.',
    'GC' : 'GC\n200 neuronów\nreg. spiking\na=0.02, d=6',
    'FS' : 'FS\n20 neuronów\nfast spiking\na=0.10, d=2',
    'HMC': 'HMC\n10 neuronów\nreg. spiking\na=0.02, d=4',
}
SHORT_LABELS = {'PP': 'PP', 'GC': 'GC', 'FS': 'FS', 'HMC': 'HMC'}

# ── Connection definitions ─────────────────────────────────────────────────────
# (id, src, dst, syntype, curve_rad, label, label_offset_x, label_offset_y)
CONNS = [
    ('pp_gc',  'PP',  'GC',  'ex',  0.00, 'AMPA\nW=4mV, τ=5ms\ndelay=4ms',   0.00,  0.68),
    ('pp_fs',  'PP',  'FS',  'ex',  0.15, 'AMPA\nW=0.25mV\nτ=3ms',           -0.30,  0.40),
    ('gc_fs',  'GC',  'FS',  'ex',  0.28, 'AMPA\nW=10mV\nτ=3ms',              0.65,  0.15),
    ('fs_gc',  'FS',  'GC',  'in', -0.28, 'GABA-A\nW=1mV\nτ=8ms',            -0.65, -0.15),
    ('gc_hmc', 'GC',  'HMC', 'ex',  0.28, 'AMPA\nW=1mV',                      0.65, -0.15),
    ('hmc_fs', 'HMC', 'FS',  'ex',  0.00, 'AMPA\nW=1mV',                      0.45,  0.25),
    ('hmc_gc', 'HMC', 'GC',  'ex', -0.28, 'AMPA\nW=0.5mV',                   -0.65,  0.15),
]


def conn_active(conn_id, ff, fb):
    always = {'pp_gc', 'gc_hmc', 'hmc_fs', 'hmc_gc'}
    if conn_id in always:   return True
    if conn_id == 'pp_fs':  return ff
    if conn_id == 'gc_fs':  return fb
    if conn_id == 'fs_gc':  return ff or fb
    return False


def _unit(p1, p2):
    d = p2 - p1
    return d / np.linalg.norm(d)


def _perp(u):
    return np.array([-u[1], u[0]])


def draw_arrow(ax, src, dst, syntype, active, curve=0.0,
               label=None, loff=(0, 0)):
    p1, p2 = POS[src], POS[dst]
    u = _unit(p1, p2)
    start = tuple(p1 + RAD[src] * u)
    end   = tuple(p2 - RAD[dst] * u)

    color = (C_EX if syntype == 'ex' else C_IN) if active else C_DIM
    lw    = 2.0 if active else 0.9
    alpha = 1.0 if active else 0.32
    style = '->' if syntype == 'ex' else '-['

    ax.add_patch(FancyArrowPatch(
        start, end,
        arrowstyle=style,
        color=color,
        linewidth=lw,
        alpha=alpha,
        connectionstyle=f'arc3,rad={curve}',
        mutation_scale=13,
        zorder=4,
    ))

    if label and active:
        mid = 0.5 * (np.array(start) + np.array(end))
        span = np.linalg.norm(np.array(end) - np.array(start))
        perp_offset = _perp(u) * curve * span * 0.5
        label_pos = mid + perp_offset + np.array(loff)
        ax.text(label_pos[0], label_pos[1], label,
                fontsize=5.2, ha='center', va='center',
                color=color, zorder=7,
                bbox=dict(boxstyle='round,pad=0.18', fc='white', ec=color,
                          lw=0.5, alpha=0.93))


def draw_nodes(ax, full=True):
    for n, xy in POS.items():
        ax.add_patch(Circle(tuple(xy), RAD[n],
                            fc=FC[n], ec='black', lw=1.4, zorder=5))
        lbl = FULL_LABELS[n] if full else SHORT_LABELS[n]
        ax.text(*xy, lbl, ha='center', va='center',
                fontsize=5.0 if full else 8.5,
                fontweight='bold', color='white', zorder=6,
                multialignment='center')


def setup_ax(ax):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')


def draw_panel(ax, ff, fb, title, dec=None, full_labels=True, ccolor='black'):
    setup_ax(ax)
    t = title + (f'\n(dec@100ms = {dec})' if dec else '')
    ax.set_title(t, fontsize=8.5 if not full_labels else 11,
                 fontweight='bold', color=ccolor, pad=5)
    draw_nodes(ax, full=full_labels)
    for cid, src, dst, stype, crv, lbl, lx, ly in CONNS:
        draw_arrow(ax, src, dst, stype,
                   conn_active(cid, ff, fb), crv,
                   label=lbl if full_labels else None,
                   loff=(lx, ly))


# ── Main figure ────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 11))
gs  = gridspec.GridSpec(2, 4, figure=fig,
                        height_ratios=[1.7, 1.0],
                        hspace=0.30, wspace=0.12)

# Top: pełny schemat obwodu
ax_main = fig.add_subplot(gs[0, :])
draw_panel(ax_main, ff=True, fb=True,
           title='Pełny obwód zakrętu zębatego (DG Microcircuit) — Neurony Izhikevicza',
           full_labels=True, ccolor='black')

# Legenda
ex_patch  = mpatches.Patch(color=C_EX,  label='Pobudzające (AMPA, →)')
in_patch  = mpatches.Patch(color=C_IN,  label='Hamujące (GABA-A, ⊣)')
dim_patch = mpatches.Patch(color=C_DIM, label='Nieaktywne w danym warunku')
ax_main.legend(handles=[ex_patch, in_patch, dim_patch],
               loc='lower left', fontsize=8, framealpha=0.92,
               edgecolor='gray', bbox_to_anchor=(0.01, 0.01))

# Ramka z parametrami
info = ('Parametry sieci:\n'
        'N_GC=200  N_FS=20  N_HMC=10\n'
        'dt=0.1 ms,  T_sim=1000 ms\n'
        'K_tonic: GC=10, FS=5, HMC=10\n'
        'P_active=0.25  R_eff_high=600 Hz\n'
        'Próg spike: v ≥ 30 mV')
ax_main.text(9.85, 0.25, info, ha='right', va='bottom', fontsize=6.5,
             transform=ax_main.transData, zorder=8,
             bbox=dict(boxstyle='round,pad=0.45', fc='#FAFAFA',
                       ec='#BDBDBD', lw=0.8))

# Adnotacje ścieżek
ax_main.text(3.6, 8.8,
             'Ścieżka FF (feedforward):\nPP→FS→GC',
             ha='center', va='center', fontsize=7.5,
             color=COND_COLORS['ff_only'],
             bbox=dict(boxstyle='round,pad=0.35', fc='#E3F2FD',
                       ec=COND_COLORS['ff_only'], lw=1.2))

ax_main.text(6.6, 1.2,
             'Ścieżka FB (feedback):\nGC→FS→GC',
             ha='center', va='center', fontsize=7.5,
             color=COND_COLORS['fb_only'],
             bbox=dict(boxstyle='round,pad=0.35', fc='#FFEBEE',
                       ec=COND_COLORS['fb_only'], lw=1.2))

ax_main.text(3.0, 1.6,
             'Zawsze aktywne:\nPP→GC',
             ha='center', va='center', fontsize=7.5,
             color='#555555',
             bbox=dict(boxstyle='round,pad=0.35', fc='#F5F5F5',
                       ec='#AAAAAA', lw=0.8))

# Bottom row: 4 warunki
cond_list = [
    ('baseline', False, False, 'Baseline\n(brak hamowania)', '+0.153'),
    ('ff_only',  True,  False, 'Feedforward\nPP→FS→GC',      '+0.321'),
    ('fb_only',  False, True,  'Feedback\nGC→FS→GC',          '+0.254'),
    ('full',     True,  True,  'Pełny obwód\nFF + FB',         '+0.420'),
]

for ci, (cname, ff, fb, title, dec) in enumerate(cond_list):
    ax = fig.add_subplot(gs[1, ci])
    draw_panel(ax, ff, fb, title, dec=dec,
               full_labels=False, ccolor=COND_COLORS[cname])

fig.suptitle(
    'Schemat obwodu zakrętu zębatego (DG Microcircuit)\n'
    'Porównanie typów hamowania — Feedforward vs Feedback Inhibition',
    fontsize=13, fontweight='bold', y=1.01)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visualize_dg_circuit.png')
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f'Saved: {out}')
plt.show()
