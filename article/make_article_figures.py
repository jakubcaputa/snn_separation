"""
article/make_article_figures.py — proste figury objaśniające do article_draft.tex.

Zasada: JEDNA figura = JEDNA myśl. To są figury do TŁUMACZENIA, nie do analizy —
analityczne (gęste) zostają w `experiments/*/results/`.

Proweniencja liczb — ważne, bo nie wszystko da się przeliczyć w tym skrypcie:
  • Fig. 1  — symulacja na żywo, domyślna konfiguracja `DGConfig`.
  • Fig. 2  — schemat, bez danych.
  • Fig. 3  — analitycznie (`calibrate.izh_fixed_points`, `g_crit`) + zmierzone
              właściwości błony z danych Madara, STATUS.md §3.4 (GC n=42 po
              deduplikacji: mediana −76, IQR −81…−70). Dane `dataset/` są poza
              gitem, więc wartości są tu wpisane, a nie przeliczane.
  • Fig. 4a,b — liczone z `e1_regime_map/results/*.npz`.
  • Fig. 4c  — wartości Shapleya z `analyze_motifs.py --in "...shard*.npz"`
              (siatka `full`, 2026-09-14); nie przeliczamy ich tutaj, żeby nie
              mieć drugiej implementacji Shapleya.
  • Fig. 4d  — kierunek 1A, STATUS.md §3.3 (eksperyment zamknięty, bez .npz).

Uruchomienie:
    python article/make_article_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                      # noqa: E402
import numpy as np                                   # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402

HERE = Path(__file__).parent
FIGS = HERE / "figures"
REPO = HERE.parent
sys.path.insert(0, str(REPO / "experiments"))

from dg_core import (                                 # noqa: E402
    DGConfig, make_connectivity, make_input_spikes, make_patterns,
    mean_pairwise_r, simulate,
)
from dg_core.calibrate import g_crit, izh_fixed_points  # noqa: E402

# Okabe–Ito, spójnie z dg_core/viz.py
BLUE, VERM, GREEN, PINK, GREY = '#0072B2', '#D55E00', '#009E73', '#CC79A7', '#8C8C8C'

plt.rcParams.update({
    'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 9,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 150, 'savefig.bbox': 'tight',
})


# ══════════════════════════════════════════════════════════════════════════════
# Fig. 1 — czym jest separacja wzorców (pojęcie + realny pomiar)
# ══════════════════════════════════════════════════════════════════════════════

def fig1_concept():
    N_GC, n_pat = 200, 2
    cfg = DGConfig().scaled(N_GC)
    conn = make_connectivity(cfg, seed=0)
    pats, r_in = make_patterns(N_GC, n_pat, R_in=0.75, p_active=0.25, seed=100)

    outs = []
    for k in range(n_pat):
        idx, t = make_input_spikes(pats[k], cfg, seed=1000 + k)
        outs.append(simulate(cfg, idx, t, conn)['gc_rates'])
    r_out = mean_pairwise_r(outs)

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.1),
                             gridspec_kw={'width_ratios': [1.2, 1.2, 0.8],
                                          'wspace': 0.45})

    show = 80   # pokazujemy wycinek populacji, żeby było co oglądać
    ax = axes[0]
    both = pats[0][:show] & pats[1][:show]
    ax.imshow(np.vstack([pats[0][:show], pats[1][:show]]), aspect='auto',
              cmap='Greys', vmin=0, vmax=1, interpolation='nearest')
    ax.set_yticks([0, 1]); ax.set_yticklabels(['pattern A', 'pattern B'])
    ax.set_xlabel(f'granule cell # (first {show} of {N_GC})')
    ax.set_title(f'INPUT: overlapping\n{both.sum()}/{show} cells driven in both')

    ax = axes[1]
    M = np.vstack([outs[0][:show], outs[1][:show]])
    im = ax.imshow(M, aspect='auto', cmap='Blues', interpolation='nearest')
    ax.set_yticks([0, 1]); ax.set_yticklabels(['output A', 'output B'])
    ax.set_xlabel('granule cell #')
    ax.set_title('OUTPUT: firing rate of each cell')
    # poziomy colorbar POD panelem — pionowy wchodził na sąsiedni wykres
    cb = fig.colorbar(im, ax=ax, label='firing rate [Hz]', orientation='horizontal',
                      fraction=0.08, pad=0.42)
    cb.ax.tick_params(labelsize=7)

    ax = axes[2]
    ax.bar(['input\n$r_{in}$', 'output\n$r_{out}$'], [r_in, r_out],
           color=[GREY, BLUE], width=0.6)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel('pairwise correlation')
    # słupki zajmują x in [-0.3, 0.3] i [0.7, 1.3] — strzałka idzie w przerwę
    ax.annotate('', xy=(0.5, r_out), xytext=(0.5, r_in),
                arrowprops=dict(arrowstyle='<->', color=VERM, lw=1.6))
    ax.text(0.5, r_in + 0.03, f'separation {r_in - r_out:+.2f}',
            color=VERM, va='bottom', ha='center', fontsize=8, fontweight='bold')
    ax.set_title('Pattern separation =\ndrop in correlation')

    fig.suptitle('Figure 1. Pattern separation: similar inputs should give less similar outputs',
                 fontsize=10, y=1.06)
    fig.savefig(FIGS / "fig1-concept.png")
    plt.close(fig)
    print(f"  fig1: r_in={r_in:.3f} r_out={r_out:.3f} sep={r_in - r_out:+.3f}")


# ══════════════════════════════════════════════════════════════════════════════
# Fig. 2 — obwód i dwie osie hamowania
# ══════════════════════════════════════════════════════════════════════════════

def fig2_circuit():
    """Schemat obwodu. Układ pionowy (FS nad GC, HMC pod GC), bo przy układzie
    bocznym strzałka PP->FS przechodziła przez węzeł GC i czytała się jak
    PP->GC->FS, czyli myliła feedforward z feedbackiem."""
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.6); ax.axis('off')

    def node(x, y, r, label, color):
        ax.add_patch(Circle((x, y), r, facecolor=color, edgecolor='k',
                            lw=1.2, alpha=0.9, zorder=3))
        ax.text(x, y, label, ha='center', va='center', fontsize=10,
                fontweight='bold', color='w', zorder=4)

    def exc(p, q, color, lw=1.8):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', color=color, lw=lw,
                                     mutation_scale=14, shrinkA=19, shrinkB=19,
                                     zorder=2))

    def inh(p, q, color, lw=1.8):
        # płaskie zakończenie = hamowanie; wizualnie odróżnialne od grotu
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-[', color=color, lw=lw,
                                     mutation_scale=9, shrinkA=19, shrinkB=21,
                                     zorder=2))

    PP, GC, FS, HMC = (1.5, 3.3), (4.9, 3.3), (4.9, 5.6), (4.9, 1.0)
    node(*PP, 0.60, 'PP', GREY)
    node(*GC, 0.80, 'GC', BLUE)
    node(*FS, 0.62, 'FS', VERM)
    node(*HMC, 0.68, 'HMC', GREEN)

    exc(PP, GC, GREY)                                    # PP -> GC
    exc(PP, FS, VERM)                                    # PP -> FS   (FF)
    exc((4.55, 3.3), (4.55, 5.6), VERM)                  # GC -> FS   (FB)
    inh((5.25, 5.6), (5.25, 3.3), VERM)                  # FS -| GC
    exc((4.60, 3.3), (4.60, 1.0), GREEN)                 # GC -> HMC
    exc((5.20, 1.0), (5.20, 3.3), GREEN)                 # HMC -> GC

    ax.text(2.6, 4.75, 'FF feedforward\nPP$\\to$FS', color=VERM, fontsize=8.5,
            ha='center', rotation=27)
    ax.text(4.32, 3.95, 'FB\nGC$\\to$FS', color=VERM, fontsize=8.5, ha='right')
    ax.text(5.85, 4.45, 'FS$\\dashv$GC\ninhibition', color=VERM, fontsize=8.5,
            ha='left')
    ax.text(5.80, 2.1, 'MC loop\nGC$\\to$HMC$\\to$GC', color=GREEN, fontsize=8.5,
            ha='left')
    ax.text(3.2, 3.52, 'perforant\npath', color=GREY, fontsize=8, ha='center')

    ax.text(8.15, 5.75, '$\\to$  excitatory', fontsize=8, ha='left')
    ax.text(8.15, 5.35, '$\\dashv$  inhibitory', fontsize=8, ha='left')

    ax.add_patch(Rectangle((0.25, 0.25), 3.3, 1.55, facecolor='#F3F3F3',
                           edgecolor=GREY, lw=1))
    ax.text(1.9, 1.52, 'two inhibition axes', fontsize=9, fontweight='bold',
            ha='center')
    ax.text(1.9, 1.04, '$K_{GC}$ — TONIC\ncell-intrinsic, always on', fontsize=7.8,
            ha='center', color=BLUE)
    ax.text(1.9, 0.48, '$W_{FS\\to GC}$ — PHASIC\nsynaptic, spike-driven', fontsize=7.8,
            ha='center', color=VERM)

    ax.set_title('Figure 2. The dentate gyrus microcircuit as modelled\n'
                 '(200 GC / 20 FS / 10 HMC, Izhikevich neurons, Brian2)',
                 fontsize=10)
    fig.savefig(FIGS / "fig2-circuit.png")
    plt.close(fig)
    print("  fig2: schemat zapisany")


# ══════════════════════════════════════════════════════════════════════════════
# Fig. 3 — punkt pracy związany danymi
# ══════════════════════════════════════════════════════════════════════════════

def fig3_operating_point():
    # Madar et al. 2019 (S-BSST219), GC po deduplikacji — STATUS.md §3.4
    MADAR_MED, MADAR_LO, MADAR_HI, MADAR_N = -76.0, -81.0, -70.0, 42

    Ks = np.linspace(0, 20, 201)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))

    ax = axes[0]
    ax.plot(Ks, [g_crit(k) for k in Ks], color=BLUE, lw=2,
            label='$G_{crit} = 4 + K$  (drive needed to spike)')
    ax.axhline(8.0, color=VERM, lw=1.8, ls='--',
               label='actual PP drive $g_{ex}=8$ mV')
    ax.axvline(10.0, color='k', lw=1, ls=':')
    ax.plot([10.0], [g_crit(10.0)], 'o', color=BLUE, ms=7, zorder=5)
    ax.annotate('model operating point\n$K_{GC}=10$: drive is BELOW threshold\n'
                '$\\Rightarrow$ fluctuation-driven, sparse firing',
                xy=(10.0, g_crit(10.0)), xytext=(1.2, 19),
                fontsize=7.6, arrowprops=dict(arrowstyle='->', color='k', lw=1))
    ax.set_xlabel('$K_{GC}$ — tonic inhibition')
    ax.set_ylabel('synaptic drive [mV]')
    ax.set_title('(a) Why granule cells stay sparse')
    ax.legend(fontsize=7.4, loc='lower right')

    ax = axes[1]
    vr = np.array([izh_fixed_points(k)[0] for k in Ks])
    ax.axhspan(MADAR_LO, MADAR_HI, color=GREEN, alpha=0.18,
               label=f'Madar et al. GC data, IQR (n={MADAR_N})')
    ax.axhline(MADAR_MED, color=GREEN, lw=1.8, label='data median $-76$ mV')
    ax.plot(Ks, vr, color=BLUE, lw=2, label='model $V_{rest}(K)$')
    ax.plot([10.0], [izh_fixed_points(10.0)[0]], 'o', color=BLUE, ms=7, zorder=5)
    ax.annotate(f'$K_{{GC}}=10 \\to {izh_fixed_points(10.0)[0]:.1f}$ mV\ninside the data IQR',
                xy=(10.0, izh_fixed_points(10.0)[0]), xytext=(12.2, -74.0),
                fontsize=7.6, arrowprops=dict(arrowstyle='->', color='k', lw=1))
    ax.set_ylim(-88, -66)
    ax.set_xlabel('$K_{GC}$ — tonic inhibition')
    ax.set_ylabel('$V_{rest}$ [mV]')
    ax.set_title('(b) The same knob is pinned by patch-clamp data')
    ax.legend(fontsize=7.2, loc='lower left', framealpha=0.95)

    fig.suptitle('Figure 3. The operating point is constrained, not chosen freely',
                 fontsize=10, y=1.04)
    fig.savefig(FIGS / "fig3-operating-point.png")
    plt.close(fig)
    print(f"  fig3: V_rest(K=10) = {izh_fixed_points(10.0)[0]:.1f} mV")


# ══════════════════════════════════════════════════════════════════════════════
# Fig. 4 — co ten warsztat dotąd ustalił (po jednej myśli na panel)
# ══════════════════════════════════════════════════════════════════════════════

def fig4_findings():
    e1 = np.load(REPO / "experiments/e1_regime_map/results/regime_map_full.npz")
    e1p = np.load(REPO / "experiments/e1_regime_map/results/matched_activity_full.npz")

    fig, axes = plt.subplots(1, 4, figsize=(15, 3.3),
                             gridspec_kw={'wspace': 0.42})

    # (a) E1 — dec jest monotoniczne, maksimum siedzi na podłodze maski
    ax = axes[0]
    v = e1['valid'].astype(bool)
    ax.scatter(e1['active_frac'][v], e1['dec'][v], s=9, color=BLUE, alpha=0.45)
    ax.axvline(0.02, color=VERM, ls='--', lw=1.4)
    ax.text(0.021, 0.05, 'analysis cut-off', color=VERM, fontsize=7.4, rotation=90)
    ax.set_xscale('log')
    ax.set_xlabel('fraction of active granule cells')
    ax.set_ylabel('separation  $r_{in}-r_{out}$')
    ax.set_title('(a) E1: "separation" simply\ngrows as the network falls silent')

    # (b) E1' — porównanie z nullem o dopasowanej rzadkości
    ax = axes[1]
    m = e1p['matched'].astype(bool)
    real = e1p['dec'][m].mean()
    null = e1p['dec_null_shuffle'][m].mean()
    ax.bar(['real\ncircuit', 'shuffled\ncontrol'], [real, null],
           color=[BLUE, GREY], width=0.6)
    # strzałka w przerwę między słupkami; etykieta nad niskim słupkiem, żeby
    # nie wychodziła poza oś i nie wchodziła na sąsiedni panel
    ax.annotate('', xy=(0.5, null), xytext=(0.5, real),
                arrowprops=dict(arrowstyle='<->', color=VERM, lw=1.6))
    ax.text(0.44, (real + null) / 2, f'{real - null:+.2f}\nthe circuit\nis WORSE',
            color=VERM, fontsize=7.8, va='center', ha='right', fontweight='bold')
    ax.set_ylabel('separation  $r_{in}-r_{out}$')
    ax.set_title('(b) E1′: shuffling the output\nseparates BETTER than the circuit')

    # (c) E2 — wkłady Shapleya (proweniencja w nagłówku pliku)
    ax = axes[2]
    phi = {'FF': 0.1998, 'FB': 0.1572, 'MC': -0.2257}
    cols = [BLUE, VERM, GREEN]
    ax.bar(list(phi), list(phi.values()), color=cols, width=0.6)
    ax.axhline(0, color='k', lw=1)
    ax.set_ylabel('Shapley contribution to separation')
    ax.set_title('(c) E2: mossy cells HURT alone\nbut help in combination')

    # (d) 1A — odczyt downstream
    ax = axes[3]
    acc = {'raw\ninput': 0.940, 'via\nDG': 0.885, 'DG no\ninhib.': 0.935,
           'random\nsparse': 0.885}
    ax.bar(list(acc), list(acc.values()),
           color=[VERM, BLUE, GREEN, PINK], width=0.65)
    ax.set_ylim(0.80, 0.98)
    ax.axhline(acc['raw\ninput'], color=VERM, ls='--', lw=1.2)
    ax.set_ylabel('classification accuracy')
    ax.set_title('(d) 1A: a decoder does NOT\nread DG output better')

    for a in axes:
        a.grid(axis='y', alpha=0.25, lw=0.6)
        a.set_axisbelow(True)

    fig.suptitle('Figure 4. What the framework has established so far — '
                 'each panel is one experiment, one message', fontsize=10, y=1.05)
    fig.savefig(FIGS / "fig4-findings.png")
    plt.close(fig)
    print(f"  fig4: E1' real={real:.3f} null={null:.3f} excess={real - null:+.3f}")


if __name__ == '__main__':
    FIGS.mkdir(parents=True, exist_ok=True)
    print("Generuję figury do artykułu:")
    fig1_concept()
    fig2_circuit()
    fig3_operating_point()
    fig4_findings()
    print(f"\nGotowe → {FIGS}")
