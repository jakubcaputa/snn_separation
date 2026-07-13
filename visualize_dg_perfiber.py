"""
visualize_dg_perfiber.py
Mały obwód DG w trybie PER-FIBER — pokazuje realne 40 włókien PP na każdy GC.

Cel: zilustrować dwie różne osie:
  • OKABLOWANIE  — n_syn_pp = 40 niezależnych włókien PP zbiega się na KAŻDY GC
  • WZORZEC      — P_active = 0.25: ~25% GC jest „aktywnych" (włókna 10 Hz),
                   reszta to tło (włókna 1 Hz)

Każda kropka = 1 neuron / 1 włókno;  każda linia = 1 synapsa.
Łączność rekurencyjna (GC↔FS↔HMC) generowana tą samą logiką i seedem (=0)
co interactive_dg.make_connectivity.

Uruchom:  python visualize_dg_perfiber.py [N_GC N_FS N_HMC n_syn_pp]
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection

# ── Mały obwód (domyślnie) ─────────────────────────────────────────────────────
N_GC     = int(sys.argv[1]) if len(sys.argv) > 1 else 6
N_FS     = int(sys.argv[2]) if len(sys.argv) > 2 else 4
N_HMC    = int(sys.argv[3]) if len(sys.argv) > 3 else 3
N_FIBERS = int(sys.argv[4]) if len(sys.argv) > 4 else 40   # włókna PP / GC
P_ACTIVE = 0.25

# Per-włókno (kanon dg_params): aktywny 10 Hz, tło 1 Hz
R_FIBER_ACTIVE, R_FIBER_BG = 10.0, 1.0

# ── Prawdopodobieństwa łączności — identyczne z interactive_dg.py ──────────────
P_PP_FS, P_GC_FS, P_FS_GC = 0.40, 0.40, 0.50
P_GC_HMC, P_HMC_FS, P_HMC_GC = 0.25, 0.40, 0.40

rng = np.random.default_rng(0)
def pairs(Ns, Nt, p):
    s, t = np.where(rng.random((Ns, Nt)) < p)
    return s.astype(np.int32), t.astype(np.int32)

conn = {
    'pp_fs' : pairs(N_GC,  N_FS,  P_PP_FS),     # włókno 0 każdego GC → FS
    'gc_fs' : pairs(N_GC,  N_FS,  P_GC_FS),
    'fs_gc' : pairs(N_FS,  N_GC,  P_FS_GC),
    'gc_hmc': pairs(N_GC,  N_HMC, P_GC_HMC),
    'hmc_fs': pairs(N_HMC, N_FS,  P_HMC_FS),
    'hmc_gc': pairs(N_HMC, N_GC,  P_HMC_GC),
}

# ── Przykładowy wzorzec: ~25% GC aktywnych ─────────────────────────────────────
n_active = max(1, round(P_ACTIVE * N_GC))
active_gc = np.sort(np.random.default_rng(7).choice(N_GC, n_active, replace=False))
is_active = np.zeros(N_GC, dtype=bool)
is_active[active_gc] = True

# ── Kolory ─────────────────────────────────────────────────────────────────────
C_GC, C_FS, C_HMC = '#1565C0', '#C62828', '#E65100'
C_ACT, C_BG = '#2E7D32', '#BFBFBF'      # włókno aktywne / tło
C_EX, C_IN  = '#1565C0', '#8E24AA'      # synapsy pob. / hamujące

# ── Pozycje ────────────────────────────────────────────────────────────────────
gc_y = np.linspace(9.2, 0.8, N_GC)
pos_GC  = np.column_stack([np.full(N_GC, 5.4), gc_y])
pos_FS  = np.column_stack([np.full(N_FS, 8.7), np.linspace(9.4, 6.2, N_FS)])
pos_HMC = np.column_stack([np.full(N_HMC, 10.4), np.linspace(3.6, 0.8, N_HMC)])
POS = {'GC': pos_GC, 'FS': pos_FS, 'HMC': pos_HMC}

def fiber_cluster(cx, cy, n, cols=5, w=1.5, h=0.95):
    rows = int(np.ceil(n / cols))
    xs = np.linspace(cx - w, cx, cols)
    ys = np.linspace(cy - h / 2, cy + h / 2, rows)
    pts = [(xs[c], ys[r]) for r in range(rows) for c in range(cols)]
    return np.array(pts[:n])

# włókna PP: dla każdego GC klaster n_syn_pp punktów po lewej
fib_pos = {i: fiber_cluster(3.0, gc_y[i], N_FIBERS) for i in range(N_GC)}

# ── Rysowanie ──────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(15, 10))
ax.set_xlim(0.5, 11.4)
ax.set_ylim(0.0, 10.4)
ax.axis('off')

# PP→GC: 40 włókien na GC (kolor wg aktywności wzorca)
seg_act, seg_bg = [], []
for i in range(N_GC):
    tgt = pos_GC[i]
    for f in fib_pos[i]:
        (seg_act if is_active[i] else seg_bg).append([f, tgt])
ax.add_collection(LineCollection(seg_bg,  colors=C_BG,  linewidths=0.4, alpha=0.45, zorder=1))
ax.add_collection(LineCollection(seg_act, colors=C_ACT, linewidths=0.5, alpha=0.55, zorder=2))

# Synapsy rekurencyjne
def seg(src, si, dst, ti):
    return np.stack([POS[src][si], POS[dst][ti]], axis=1)

rec = [
    ('GC→FS (pob.)',   seg('GC', conn['gc_fs'][0],  'FS',  conn['gc_fs'][1]),  C_EX,  0.45, '-'),
    ('FS→GC (hamow.)', seg('FS', conn['fs_gc'][0],  'GC',  conn['fs_gc'][1]),  C_IN,  0.45, '-'),
    ('GC→HMC (pob.)',  seg('GC', conn['gc_hmc'][0], 'HMC', conn['gc_hmc'][1]), C_HMC, 0.55, '-'),
    ('HMC→FS (pob.)',  seg('HMC',conn['hmc_fs'][0], 'FS',  conn['hmc_fs'][1]), C_HMC, 0.55, '-'),
    ('HMC→GC (pob.)',  seg('HMC',conn['hmc_gc'][0], 'GC',  conn['hmc_gc'][1]), C_HMC, 0.45, '--'),
]
for _, segs, color, alpha, ls in rec:
    ax.add_collection(LineCollection(segs, colors=color, linewidths=1.4,
                                     alpha=alpha, linestyles=ls, zorder=3))

# Włókna PP (kropki)
for i in range(N_GC):
    fp = fib_pos[i]
    ax.scatter(fp[:, 0], fp[:, 1], s=12,
               c=(C_ACT if is_active[i] else C_BG),
               edgecolors='none', zorder=4)

# Neurony
ax.scatter(pos_GC[:, 0], pos_GC[:, 1], s=420,
           c=[C_GC if a else '#9FB8D6' for a in is_active],
           edgecolors='black', linewidths=1.3, zorder=6)
ax.scatter(pos_FS[:, 0], pos_FS[:, 1], s=300, c=C_FS,
           edgecolors='black', linewidths=1.2, zorder=6)
ax.scatter(pos_HMC[:, 0], pos_HMC[:, 1], s=300, c=C_HMC,
           edgecolors='black', linewidths=1.2, zorder=6)

# Etykiety GC
for i in range(N_GC):
    ax.text(pos_GC[i, 0], pos_GC[i, 1], f'GC{i}', ha='center', va='center',
            fontsize=7, fontweight='bold', color='white', zorder=7)
for i in range(N_FS):
    ax.text(*pos_FS[i], f'FS{i}', ha='center', va='center',
            fontsize=7, fontweight='bold', color='white', zorder=7)
for i in range(N_HMC):
    ax.text(*pos_HMC[i], f'H{i}', ha='center', va='center',
            fontsize=7, fontweight='bold', color='white', zorder=7)

# Klamra „40 włókien na 1 GC" przy pierwszym aktywnym GC
gi = active_gc[0]
ax.annotate(f'{N_FIBERS} włókien PP\nna 1 GC', xy=(3.05, gc_y[gi]),
            xytext=(1.4, 10.0), fontsize=9, fontweight='bold', color=C_ACT,
            ha='center', va='center',
            arrowprops=dict(arrowstyle='->', color=C_ACT, lw=1.3))

# Nagłówki kolumn
ax.text(2.3, 10.15, 'PP — włókna (per-fiber)', ha='center', fontsize=11,
        fontweight='bold', color='#2E7D32')
ax.text(5.4, 10.15, 'GC', ha='center', fontsize=11, fontweight='bold', color=C_GC)
ax.text(8.7, 10.15, 'FS', ha='center', fontsize=11, fontweight='bold', color=C_FS)
ax.text(10.4, 4.3, 'HMC', ha='center', fontsize=11, fontweight='bold', color=C_HMC)

# Legenda
handles = [
    mpatches.Patch(color=C_ACT, label=f'Włókno AKTYWNE — {R_FIBER_ACTIVE:.0f} Hz '
                   f'(GC w 25% wzorca)'),
    mpatches.Patch(color=C_BG,  label=f'Włókno TŁA — {R_FIBER_BG:.0f} Hz (pozostałe GC)'),
    mpatches.Patch(color=C_EX,  label=f'GC→FS pobudz. ({conn["gc_fs"][0].size} syn.)'),
    mpatches.Patch(color=C_IN,  label=f'FS→GC HAMOW. ({conn["fs_gc"][0].size} syn.)'),
    mpatches.Patch(color=C_HMC, label='HMC ↔ pobudz. (GC→HMC, HMC→FS, HMC→GC)'),
]
ax.legend(handles=handles, loc='lower center', ncol=2, fontsize=8.5,
          framealpha=0.95, edgecolor='gray', bbox_to_anchor=(0.5, -0.08))

ax.set_title(
    f'Mały obwód DG — tryb PER-FIBER\n'
    f'N_GC={N_GC} (aktywne: {[int(x) for x in active_gc]}), N_FS={N_FS}, N_HMC={N_HMC}, '
    f'{N_FIBERS} włókien PP/GC  →  {N_GC*N_FIBERS} włókien łącznie  |  '
    f'P_active={P_ACTIVE}  →  {n_active} aktywnych GC',
    fontsize=12.5, fontweight='bold', pad=12)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'visualize_dg_perfiber.png')
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f'Saved: {out}')
plt.show()
