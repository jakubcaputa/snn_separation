"""
visualize_dg_neurons.py
Pełna sieć DG na poziomie POJEDYNCZYCH NEURONÓW.

Każdy neuron = jeden węzeł (kropka), każda synapsa = jedna linia.
Łączność generowana TĄ SAMĄ logiką i seedem (=0) co w interactive_dg.make_connectivity,
więc obraz odpowiada realnie symulowanej sieci.

Pokazuje cztery populacje:
  PP  — wejście perforant path (reprezentacja agregatowa 1:1 do GC)
  GC  — komórki ziarniste (pobudzające)
  FS  — interneurony fast-spiking (hamujące)
  HMC — hilar mossy cells (pobudzające)

Uruchom:  python visualize_dg_neurons.py [N_GC N_FS N_HMC]
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection

# ── Rozmiary sieci (domyślnie jak w aplikacji) ─────────────────────────────────
N_GC  = int(sys.argv[1]) if len(sys.argv) > 1 else 200
N_FS  = int(sys.argv[2]) if len(sys.argv) > 2 else 20
N_HMC = int(sys.argv[3]) if len(sys.argv) > 3 else 10

# ── Prawdopodobieństwa łączności — identyczne z interactive_dg.py ──────────────
P_PP_FS  = 0.40
P_GC_FS  = 0.40
P_FS_GC  = 0.50
P_GC_HMC = 0.25
P_HMC_FS = 0.40
P_HMC_GC = 0.40

# ── Generowanie łączności — ta sama kolejność rng co make_connectivity ─────────
rng = np.random.default_rng(0)
def pairs(Ns, Nt, p):
    mask = rng.random((Ns, Nt)) < p
    s, t = np.where(mask)
    return s.astype(np.int32), t.astype(np.int32)

conn = {
    'pp_fs' : pairs(N_GC,  N_FS,  P_PP_FS),
    'gc_fs' : pairs(N_GC,  N_FS,  P_GC_FS),
    'fs_gc' : pairs(N_FS,  N_GC,  P_FS_GC),
    'gc_hmc': pairs(N_GC,  N_HMC, P_GC_HMC),
    'hmc_fs': pairs(N_HMC, N_FS,  P_HMC_FS),
    'hmc_gc': pairs(N_HMC, N_GC,  P_HMC_GC),
}

# ── Kolory ─────────────────────────────────────────────────────────────────────
C_PP  = '#2E7D32'   # zielony
C_GC  = '#1565C0'   # niebieski
C_FS  = '#C62828'   # czerwony
C_HMC = '#E65100'   # pomarańczowy
C_EX  = '#1565C0'   # pobudzające
C_IN  = '#8E24AA'   # hamujące (fioletowy)

# ── Pozycje neuronów (każdy neuron osobno) ─────────────────────────────────────
def column(n, x, y_lo, y_hi):
    ys = np.linspace(y_hi, y_lo, n) if n > 1 else np.array([(y_lo + y_hi) / 2])
    return np.column_stack([np.full(n, x), ys])

pos_PP  = column(N_GC,  0.0, 0.0, 10.0)   # PP agregat 1:1 → GC
pos_GC  = column(N_GC,  4.0, 0.0, 10.0)
pos_FS  = column(N_FS,  8.5, 5.6, 10.0)
pos_HMC = column(N_HMC, 8.5, 0.0, 4.4)

POS = {'PP': pos_PP, 'GC': pos_GC, 'FS': pos_FS, 'HMC': pos_HMC}

# ── Definicje krawędzi: (etykieta, src_pos, src_idx, dst_pos, dst_idx, kolor, alpha, styl)
def seg(src, si, dst, ti):
    return np.stack([POS[src][si], POS[dst][ti]], axis=1)

pp_gc_i = np.arange(N_GC)   # PP→GC 1:1
edges = [
    ('PP→GC  (pob.)',  seg('PP', pp_gc_i, 'GC', pp_gc_i),            C_PP, 0.30, '-'),
    ('PP→FS  (pob.)',  seg('GC', conn['pp_fs'][0], 'FS', conn['pp_fs'][1]),   C_PP, 0.18, '-'),
    ('GC→FS  (pob.)',  seg('GC', conn['gc_fs'][0], 'FS', conn['gc_fs'][1]),   C_EX, 0.10, '-'),
    ('FS→GC  (hamow.)',seg('FS', conn['fs_gc'][0], 'GC', conn['fs_gc'][1]),   C_IN, 0.07, '-'),
    ('GC→HMC (pob.)',  seg('GC', conn['gc_hmc'][0], 'HMC', conn['gc_hmc'][1]),C_HMC,0.12, '-'),
    ('HMC→FS (pob.)',  seg('HMC', conn['hmc_fs'][0], 'FS', conn['hmc_fs'][1]),C_HMC,0.30, '-'),
    ('HMC→GC (pob.)',  seg('HMC', conn['hmc_gc'][0], 'GC', conn['hmc_gc'][1]),C_HMC,0.12, '--'),
]

# ── Rysowanie ──────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(15, 11))
ax.set_xlim(-1.2, 11.5)
ax.set_ylim(-1.2, 11.2)
ax.axis('off')

# Krawędzie (LineCollection — wydajne dla tysięcy synaps)
legend_handles = []
for label, segs, color, alpha, ls in edges:
    lc = LineCollection(segs, colors=color, linewidths=0.5, alpha=alpha,
                        linestyles=ls, zorder=1)
    ax.add_collection(lc)
    legend_handles.append(mpatches.Patch(color=color,
                          label=f'{label}  —  {segs.shape[0]} synaps'))

# Neurony (kropki na wierzchu)
for name, pos, color in [('PP', pos_PP, C_PP), ('GC', pos_GC, C_GC),
                         ('FS', pos_FS, C_FS), ('HMC', pos_HMC, C_HMC)]:
    ax.scatter(pos[:, 0], pos[:, 1], s=42, c=color, edgecolors='white',
               linewidths=0.6, zorder=5)

# Nagłówki kolumn
heads = [('PP\n(wejście, 1:1)', 0.0, C_PP, N_GC),
         ('GC\n(ziarniste)',    4.0, C_GC, N_GC),
         ('FS\n(hamujące)',     8.5, C_FS, N_FS),
         ('HMC\n(mossy)',       8.5, C_HMC, N_HMC)]
ax.text(0.0, 10.7, f'PP\n(wejście, 1:1)\nN={N_GC}', ha='center', va='bottom',
        fontsize=10, fontweight='bold', color=C_PP)
ax.text(4.0, 10.7, f'GC\n(ziarniste)\nN={N_GC}', ha='center', va='bottom',
        fontsize=10, fontweight='bold', color=C_GC)
ax.text(8.5, 10.55, f'FS (hamujące)  N={N_FS}', ha='center', va='bottom',
        fontsize=10, fontweight='bold', color=C_FS)
ax.text(8.5, 4.6, f'HMC (mossy)  N={N_HMC}', ha='center', va='bottom',
        fontsize=10, fontweight='bold', color=C_HMC)

n_syn_total = sum(s.shape[0] for _, s, *_ in edges)
ax.legend(handles=legend_handles, loc='lower left', fontsize=9,
          framealpha=0.95, edgecolor='gray', bbox_to_anchor=(-0.02, -0.02),
          title=f'Synapsy (łącznie {n_syn_total})')

ax.set_title(
    f'Pełna sieć DG na poziomie pojedynczych neuronów\n'
    f'każda kropka = 1 neuron, każda linia = 1 synapsa  '
    f'(N_GC={N_GC}, N_FS={N_FS}, N_HMC={N_HMC}, seed=0)',
    fontsize=13, fontweight='bold', pad=14)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'visualize_dg_neurons.png')
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f'Saved: {out}')
print('Synapsy: ' + ', '.join(f'{l.split()[0].replace(chr(0x2192), "->")}={s.shape[0]}'
                               for l, s, *_ in edges))
plt.show()
