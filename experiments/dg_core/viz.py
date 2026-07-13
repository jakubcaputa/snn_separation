"""
dg_core/viz.py — wspólny styl figur dla obu kierunków.

Paleta: Okabe–Ito (bezpieczna dla daltonizmu). Zwalidowana skryptem
`validate_palette.js`: pasmo jasności PASS, chroma PASS, separacja CVD
ΔE=37.2 przy progu 12 PASS, kontrast do tła PASS.

Zasady (stosowane konsekwentnie we wszystkich wykresach):
  • kategoryczne (motywy FF/FB/MC) — stała kolejność barw, nigdy cyklowana
  • sekwencyjne (wielkość, np. dokładność) — JEDEN odcień, jasny→ciemny
  • rozbieżne (dekorelacja: może być < 0!) — dwa bieguny + SZARA neutralna w zerze
  • żadnych tęcz (jet/rainbow), siatka i osie recesywne, legenda zawsze przy ≥2 seriach
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

# ── Kategoryczne: motywy hamowania (stała kolejność) ──────────────────────────
MOTIF_COLORS = {
    'FF': '#0072B2',   # niebieski
    'FB': '#D55E00',   # cynobrowy
    'MC': '#009E73',   # zielony morski
}
NONE_COLOR = '#8C8C8C'   # „brak dominacji" — neutralny szary, nie czwarty kolor

# ── Kategoryczne: warunki odbiorcy (kierunek 1) ───────────────────────────────
COND_COLORS = {
    'dg':       '#0072B2',   # niebieski
    'raw':      '#D55E00',   # cynobrowy
    'dg_noinh': '#009E73',   # zielony morski
    'random':   '#CC79A7',   # różowy (4. slot Okabe–Ito)
}

# ── Sekwencyjna (magnitude): jeden odcień, jasny → ciemny ─────────────────────
SEQ_CMAP = 'Blues'

# ── Rozbieżna (polarity): dekorelacja bywa ujemna → neutralna szarość w 0 ─────
DIVERGING = LinearSegmentedColormap.from_list(
    'dec_div', ['#8C3B00', '#D55E00', '#F0F0F0', '#4DA6D9', '#00436B'], N=256)


def diverging_norm(vmin: float, vmax: float, center: float = 0.0):
    """Norma rozbieżna z gwarantowanym środkiem w zerze (bez tego mapa kłamie)."""
    lo = min(vmin, center - 1e-6)
    hi = max(vmax, center + 1e-6)
    return TwoSlopeNorm(vmin=lo, vcenter=center, vmax=hi)


def use_style():
    """Recesywna siatka i osie; tekst w kolorach tekstu, nie serii."""
    mpl.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.edgecolor': '#B0B0B0',
        'axes.linewidth': 0.8,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.titlesize': 10,
        'axes.titleweight': 'bold',
        'axes.labelsize': 9,
        'axes.labelcolor': '#2B2B2B',
        'text.color': '#2B2B2B',
        'xtick.color': '#5A5A5A',
        'ytick.color': '#5A5A5A',
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'grid.color': '#E4E4E4',
        'grid.linewidth': 0.6,
        'legend.fontsize': 8,
        'legend.frameon': False,
        'lines.linewidth': 2.0,
        'lines.markersize': 6,
        'figure.dpi': 110,
        'savefig.dpi': 160,
        'savefig.bbox': 'tight',
    })


def grid(ax, axis='y'):
    ax.grid(True, axis=axis, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
