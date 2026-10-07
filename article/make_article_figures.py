"""
article/make_article_figures.py — proste figury objaśniające do article_draft.tex.

Zasada: JEDNA figura = JEDNA myśl. To są figury do TŁUMACZENIA, nie do analizy —
analityczne (gęste) zostają w `experiments/*/results/`.

Proweniencja liczb — ważne, bo nie wszystko da się przeliczyć w tym skrypcie:
  • Fig. 1  — symulacja na żywo, domyślna konfiguracja `DGConfig`.
  • Fig. 2  — schemat, bez danych.
  • Fig. 3  — analitycznie (`calibrate.izh_fixed_points`, `g_crit`) + zmierzone
              właściwości błony z danych Madara, STATUS.md sek. 3.8 (GC n=42 po
              deduplikacji: mediana −76, IQR −81…−70). Dane `dataset/` są poza
              gitem, więc wartości są tu wpisane, a nie przeliczane.
  • Fig. 4a,b — liczone z `e1_regime_map/results/*.npz`.
  • Fig. 4c  — wartości Shapleya z `analyze_motifs.py --in "...shard*.npz"`
              (siatka `full`, 2026-09-14); nie przeliczamy ich tutaj, żeby nie
              mieć drugiej implementacji Shapleya.
  • Fig. 4d  — kierunek 1A, STATUS.md sek. 3.7 (eksperyment zamknięty, bez .npz).

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
SLIDES = FIGS / "slides"

# Tryb slajdu: te same figury, ale BEZ nagłówka „Figure N." — na slajdzie tytuł
# niesie sam slajd, a podwójny tytuł zabiera miejsce. Zapis do figures/slides/.
SLIDE = False


def _out(name: str) -> Path:
    return (SLIDES if SLIDE else FIGS) / name


def _fs(w: float, h: float, k_slide: float = 0.74) -> tuple[float, float]:
    """Rozmiar płótna. W trybie slajdu mniejsze płótno przy tych samych czcionkach:
    po rozciągnięciu na szerokość slajdu tekst wychodzi ~1.35× większy, czyli
    czytelny z sali (figury artykułowe mają 7–9 pt, pod druk)."""
    k = k_slide if SLIDE else 1.0
    return (w * k, h * k)
REPO = HERE.parent
sys.path.insert(0, str(REPO / "experiments"))

from dg_core import (                                 # noqa: E402
    DGConfig, make_connectivity, make_input_spikes, make_patterns,
    mean_pairwise_r, simulate,
)
from dg_core.calibrate import g_crit, izh_fixed_points  # noqa: E402
from dg_core.viz import pct_log_axis  # noqa: E402

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

    fig, axes = plt.subplots(1, 3, figsize=_fs(11.5, 3.1),
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

    if not SLIDE: fig.suptitle('Figure 1. Pattern separation: similar inputs should give less similar outputs',
                 fontsize=10, y=1.06)
    fig.savefig(_out("fig1-concept.png"))
    plt.close(fig)
    print(f"  fig1: r_in={r_in:.3f} r_out={r_out:.3f} sep={r_in - r_out:+.3f}")


# ══════════════════════════════════════════════════════════════════════════════
# Fig. 2 — obwód i dwie osie hamowania
# ══════════════════════════════════════════════════════════════════════════════

def fig2_circuit():
    """Schemat obwodu.

    Końce strzałek liczone GEOMETRYCZNIE w jednostkach danych, a nie przez
    `shrinkA/shrinkB` — tamte są w punktach, więc przy innej skali figury
    strzałki wchodziły pod koła węzłów.
    """
    fig, ax = plt.subplots(figsize=_fs(8.0, 5.2, 0.86))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.8)
    ax.set_aspect('equal'); ax.axis('off')

    GAP = 0.16          # odstęp między brzegiem koła a grotem

    def node(xy, r, label, color):
        ax.add_patch(Circle(xy, r, facecolor=color, edgecolor='k',
                            lw=1.3, zorder=3))
        ax.text(*xy, label, ha='center', va='center', fontsize=10,
                fontweight='bold', color='w', zorder=4)
        return (xy, r)

    def edge(src, tgt, color, kind='exc', lw=1.9, off=0.0):
        """Strzałka od brzegu `src` do brzegu `tgt`, z bocznym przesunięciem `off`."""
        (x0, y0), r0 = src
        (x1, y1), r1 = tgt
        dx, dy = x1 - x0, y1 - y0
        L = np.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        px, py = -uy, ux                      # wektor prostopadły — rozsuwa pary
        x0 += px * off; y0 += py * off
        x1 += px * off; y1 += py * off
        start = (x0 + ux * (r0 + GAP), y0 + uy * (r0 + GAP))
        end = (x1 - ux * (r1 + GAP), y1 - uy * (r1 + GAP))
        style = '-|>' if kind == 'exc' else '-['
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, color=color,
                                     lw=lw, mutation_scale=14 if kind == 'exc' else 10,
                                     shrinkA=0, shrinkB=0, zorder=2))

    PP = node((1.45, 3.3), 0.58, 'PP', GREY)
    GC = node((5.00, 3.3), 0.78, 'GC', BLUE)
    FS = node((5.00, 5.75), 0.60, 'FS', VERM)
    HM = node((5.00, 0.95), 0.66, 'HMC', GREEN)

    edge(PP, GC, GREY)                        # PP -> GC
    edge(PP, FS, VERM)                        # PP -> FS   (feedforward)
    edge(GC, FS, VERM, off=+0.30)             # GC -> FS   (feedback)
    edge(FS, GC, VERM, kind='inh', off=+0.30)  # FS -| GC
    edge(GC, HM, GREEN, off=+0.26)            # GC -> HMC
    edge(HM, GC, GREEN, off=+0.26)            # HMC -> GC

    ax.text(2.55, 5.05, 'FF  feedforward', color=VERM, fontsize=8.8,
            ha='center', rotation=31)
    ax.text(4.25, 4.52, 'FB', color=VERM, fontsize=8.8, ha='right')
    ax.text(5.78, 4.52, 'FS $\\dashv$ GC', color=VERM, fontsize=8.8, ha='left')
    ax.text(5.80, 2.05, 'MC loop', color=GREEN, fontsize=8.8, ha='left')
    ax.text(3.20, 3.52, 'perforant path', color=GREY, fontsize=8, ha='center')

    ax.text(7.95, 6.25, '$\\to$  excitatory', fontsize=8.4, ha='left')
    ax.text(7.95, 5.85, '$\\dashv$  inhibitory', fontsize=8.4, ha='left')

    ax.add_patch(Rectangle((0.05, 0.08), 3.95, 1.95, facecolor='#F3F3F3',
                           edgecolor=GREY, lw=1, zorder=1))
    ax.text(2.02, 1.72, 'two inhibition axes', fontsize=9, fontweight='bold',
            ha='center', zorder=2)
    ax.text(2.02, 1.16, '$K_{GC}$ — TONIC\ncell-intrinsic, always on', fontsize=7.6,
            ha='center', color=BLUE, zorder=2)
    ax.text(2.02, 0.50, '$W_{FS\\to GC}$ — PHASIC\nsynaptic, spike-driven', fontsize=7.6,
            ha='center', color=VERM, zorder=2)

    if not SLIDE: ax.set_title('Figure 2. The dentate gyrus microcircuit as modelled\n'
                 '(200 GC / 20 FS / 10 HMC, Izhikevich neurons, Brian2)',
                 fontsize=10)
    fig.savefig(_out("fig2-circuit.png"))
    plt.close(fig)
    print("  fig2: schemat zapisany")


# ══════════════════════════════════════════════════════════════════════════════
# Fig. 3 — punkt pracy związany danymi
# ══════════════════════════════════════════════════════════════════════════════

def fig3_operating_point():
    # Madar et al. 2019 (S-BSST219), GC po deduplikacji — STATUS.md sek. 3.8
    MADAR_MED, MADAR_LO, MADAR_HI, MADAR_N = -76.0, -81.0, -70.0, 42

    Ks = np.linspace(0, 20, 201)
    fig, axes = plt.subplots(1, 2, figsize=_fs(9.2, 3.4, 0.84),
                             gridspec_kw={'wspace': 0.32})

    ax = axes[0]
    ax.plot(Ks, [g_crit(k) for k in Ks], color=BLUE, lw=2,
            label='threshold $G_{crit} = 4 + K$')
    ax.axhline(8.0, color=VERM, lw=1.8, ls='--',
               label='PP drive $g_{ex}=8$ mV')
    ax.axvline(10.0, color='k', lw=1, ls=':')
    ax.plot([10.0], [g_crit(10.0)], 'o', color=BLUE, ms=7, zorder=5)
    ax.annotate('$K_{GC}=10$: drive < threshold\n'
                '$\\Rightarrow$ fluctuation-driven,\n    sparse firing',
                xy=(10.0, g_crit(10.0)), xytext=(10.4, 9.0), ha='left', va='bottom',
                fontsize=7.6, arrowprops=dict(arrowstyle='->', color='k', lw=1))
    ax.set_xlabel('$K_{GC}$ — tonic inhibition')
    ax.set_ylabel('synaptic drive [mV]')
    ax.set_title('(a) Why granule cells\nstay sparse')
    ax.legend(fontsize=7.4, loc='upper left')

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
    ax.set_title('(b) The same knob is pinned\nby patch-clamp data')
    ax.legend(fontsize=7.2, loc='lower left', framealpha=0.95)

    if not SLIDE: fig.suptitle('Figure 3. The operating point is constrained, not chosen freely',
                 fontsize=10, y=1.04)
    fig.savefig(_out("fig3-operating-point.png"))
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
    pct_log_axis(ax)
    ax.set_xlabel('fraction of active granule cells')
    ax.set_ylabel('separation  $r_{in}-r_{out}$')
    ax.set_title('(a) E1: "separation" simply\ngrows as the network falls silent')

    # (b) E1' — porównanie z DWOMA nullami. Permutacyjny jest zdegenerowany
    # (równa się r_in, bo niszczy całą informację), więc sam w sobie nie jest
    # kontrolą rzadkości — pokazujemy oba, żeby to było widać. Patrz STATUS sek. 3.5.
    ax = axes[1]
    m = e1p['matched'].astype(bool)
    real = e1p['dec'][m].mean()
    n_shuf = e1p['dec_null_shuffle'][m].mean()
    n_kwta = e1p['dec_null_kwta'][m].mean()
    ax.bar(['DG', 'random\nsparse', 'scrambled'],
           [real, n_kwta, n_shuf], color=[BLUE, PINK, GREY], width=0.62)
    ax.text(2, n_shuf + 0.03, 'discards\nthe input', ha='center', color=GREY,
            fontsize=7.2, style='italic')
    ax.set_ylim(0, 0.92)
    ax.set_ylabel('separation  $r_{in}-r_{out}$')
    ax.set_title('(b) E1$^\\prime$: DG beats a random sparse code,\n'
                 'but not a code that discards the input')
    ax.annotate(f'+{real - n_kwta:.2f}', xy=(0.5, max(real, n_kwta) + 0.03),
                ha='center', color=GREEN, fontsize=8.5, fontweight='bold')

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

    if not SLIDE: fig.suptitle('Figure 4. What the framework has established so far — '
                 'each panel is one experiment, one message', fontsize=10, y=1.05)
    fig.savefig(_out("fig4-findings.png"))
    plt.close(fig)
    print(f"  fig4: E1' DG={real:.3f}  kWTA={n_kwta:.3f} (nadwyzka {real - n_kwta:+.3f})"
          f"  scrambled={n_shuf:.3f}")


def fig5_nulls():
    """Dlaczego oba null-e nie są poziomem szansy, i skąd bierze się przewaga DG."""
    e1p = np.load(REPO / "experiments/e1_regime_map/results/matched_activity_full.npz")
    m = e1p['matched'].astype(bool)
    r_in = float(e1p['r_in'][m].mean())
    ro = lambda key: r_in - float(e1p[key][m].mean())

    fig, axes = plt.subplots(1, 2, figsize=_fs(11.5, 3.6, 0.82),
                             gridspec_kw={'wspace': 0.42, 'width_ratios': [1.15, 1]})

    # (a) oba null-e OBEJMUJĄ DG — żaden nie jest poziomem szansy
    ax = axes[0]
    names = ['input', 'k-WTA\nnull', 'DG', 'permutation\nnull']
    vals = [r_in, ro('dec_null_kwta'), ro('dec'), ro('dec_null_shuffle')]
    cols = [GREY, PINK, BLUE, '#4D4D4D']
    ax.bar(names, vals, color=cols, width=0.62)
    for x, v in enumerate(vals):
        ax.text(x, v + 0.018, f'{v:.2f}', ha='center', fontsize=8.5, fontweight='bold')
    ax.axhline(r_in, color=GREY, ls=':', lw=1.2)
    ax.set_ylabel('output correlation  $r_{out}$')
    ax.set_ylim(0, r_in * 1.22)
    ax.set_title('(a) Neither null is a chance level — they BRACKET the circuit\n'
                 'lower $r_{out}$ = more decorrelation', fontsize=9.5)
    ax.annotate('preserves almost\neverything\n(near-isometry)', xy=(1, vals[1]),
                xytext=(1, r_in * 1.02), ha='center', fontsize=7, color=PINK)
    ax.annotate('destroys everything\n(unreachable ceiling)', xy=(3, vals[3]),
                xytext=(3, r_in * 0.42), ha='center', fontsize=7, color='#4D4D4D')

    # (b) rozkład przewagi: nieliniowość vs hamowanie
    ax = axes[1]
    import glob as _g
    ek, reg, coal = [], [], None
    for f in sorted(_g.glob(str(REPO / "experiments/e2_motif_attribution/results/lesion_grid_full_shard*.npz"))):
        d = np.load(f, allow_pickle=True)
        coal = [str(c) for c in d['coalitions']]
        ek.append(d['dec_excess_kwta']); reg.append(d['task_regime'])
    EK = np.concatenate(ek); R = np.concatenate(reg)
    mm = (R == 'mc_active')
    none_v = float(EK[mm, coal.index('')].mean())
    full_v = float(EK[mm, coal.index('FF+FB+MC')].mean())

    ax.bar(['spiking\nnonlinearity alone', 'full circuit\n(+ inhibition)'],
           [none_v, full_v], color=[BLUE, VERM], width=0.55)
    ax.bar(['full circuit\n(+ inhibition)'], [full_v - none_v], bottom=[none_v],
           color=VERM, width=0.55, hatch='//', edgecolor='w')
    ax.text(0, none_v / 2, f'{none_v:.3f}\n({none_v / full_v:.0%})', ha='center',
            va='center', color='w', fontsize=9, fontweight='bold')
    ax.text(1, none_v + (full_v - none_v) / 2, f'+{full_v - none_v:.3f}', ha='center',
            va='center', color='w', fontsize=9, fontweight='bold')
    ax.set_ylabel('advantage over the random sparse code')
    ax.set_title('(b) Most of the advantage is the threshold,\n'
                 'not the inhibitory circuit', fontsize=9.5)
    ax.grid(axis='y', alpha=0.25, lw=0.6); ax.set_axisbelow(True)

    if not SLIDE: fig.suptitle('Figure 5. What the circuit is actually compared against',
                 fontsize=10, y=1.04)
    fig.savefig(_out("fig5-nulls.png"))
    plt.close(fig)
    print(f"  fig5: r_in={r_in:.3f} kWTA={vals[1]:.3f} DG={vals[2]:.3f} perm={vals[3]:.3f}"
          f" | nieliniowosc {none_v:+.3f} -> pelny {full_v:+.3f}")


# ══════════════════════════════════════════════════════════════════════════════
# Figury TYLKO pod slajdy — jeden panel, jedna myśl, większa czcionka.
# Na slajdzie figura ma pokazać DOWÓD, nie tylko wynik.
# ══════════════════════════════════════════════════════════════════════════════

SLIDE_RC = {'font.size': 13, 'axes.titlesize': 14, 'axes.labelsize': 13,
            'xtick.labelsize': 12, 'ytick.labelsize': 12, 'legend.fontsize': 11}


def slide_e1():
    """E1: maksimum separacji siedzi zawsze tuż przy progu odrzucania."""
    e1 = np.load(REPO / "experiments/e1_regime_map/results/regime_map_full.npz")
    act, dec = e1['active_frac'], e1['dec']
    ok = act > 0
    with plt.rc_context(SLIDE_RC):
        fig, ax = plt.subplots(figsize=(7.4, 4.9))
        ax.scatter(act[ok], dec[ok], s=12, color=GREY, alpha=0.45, zorder=1,
                   label='grid points')
        cols = [VERM, PINK, GREEN, BLUE]
        for thr, c in zip([0.02, 0.05, 0.10, 0.20], cols):
            v = act >= thr
            i = int(np.argmax(np.where(v, dec, -np.inf)))
            ax.axvline(thr, color=c, ls='--', lw=1.4, zorder=2)
            ax.plot(act[i], dec[i], marker='*', ms=17, color=c, mec='k', mew=0.7,
                    zorder=3, label=f'cut-off {thr:.0%} → max at {act[i]:.1%}')
        pct_log_axis(ax)
        ax.set_xlabel('fraction of active granule cells')
        ax.set_ylabel('separation  $r_{in} - r_{out}$')
        ax.legend(loc='lower left', frameon=True, framealpha=0.95, edgecolor='0.8')
        ax.grid(alpha=0.25, lw=0.6); ax.set_axisbelow(True)
        fig.savefig(SLIDES / "slide-e1.png", dpi=200)
        plt.close(fig)
    print("  slide-e1 zapisany")


def slide_e1p():
    """E1′: przy ZADANEJ aktywności separacja nie zależy od hamowania fazowego."""
    d = np.load(REPO / "experiments/e1_regime_map/results/matched_activity_full.npz")
    m = d['matched'].astype(bool)
    targets = np.unique(d['target_af'][m])
    ws = np.unique(d['W_FS_GC'][m])
    cmap = plt.get_cmap('viridis')
    with plt.rc_context(SLIDE_RC):
        fig, ax = plt.subplots(figsize=(7.4, 4.9))
        spans = []
        for k, a in enumerate(targets):
            s_ = m & (d['target_af'] == a)
            mu = [d['dec'][s_ & (d['W_FS_GC'] == w)].mean() for w in ws]
            spans.append(max(mu) - min(mu))
            ax.plot(ws, mu, '-o', lw=2.2, ms=5, color=cmap(k / max(1, len(targets) - 1)),
                    label=f'activity held at {a:.0%}')
        ax.set_xlabel('phasic inhibition  $W_{FS \\to GC}$')
        ax.set_ylabel('separation  $r_{in} - r_{out}$')
        ax.set_ylim(0, 0.92)
        ax.legend(loc='upper center', frameon=False, ncol=3, fontsize=10.5,
                  columnspacing=1.2, handlelength=1.6)
        ax.grid(alpha=0.25, lw=0.6); ax.set_axisbelow(True)
        fig.savefig(SLIDES / "slide-e1p.png", dpi=200)
        plt.close(fig)
    print(f"  slide-e1p: rozstep separacji po W_FS_GC przy stalej aktywnosci: "
          f"max {max(spans):.3f}, sredni {np.mean(spans):.3f}")


def slide_e2():
    """E2: wkłady Shapleya na surowej separacji i po korekcie nullem — prawie identyczne.

    Przy KANONICZNYM napędzie PP (×1.0), tak jak raportuje `analyze_motifs.py`.
    Uśrednianie po wszystkich napędach (×0.5, ×1, ×2) rozmywa efekt — przy ×0.5
    wkłady są kilkukrotnie mniejsze (STATUS sek. 3.6)."""
    import glob as _g
    from dg_core.metrics import interaction_2way, shapley_values
    from dg_core import MOTIFS
    acc = {'dec': [], 'dec_excess_shuffle': []}
    reg, drv, coal = [], [], None
    for f in sorted(_g.glob(str(REPO / "experiments/e2_motif_attribution/results/"
                                      "lesion_grid_full_shard*.npz"))):
        z = np.load(f, allow_pickle=True)
        coal = [str(c) for c in z['coalitions']]
        for k in acc:
            acc[k].append(z[k])
        reg.append(z['task_regime'])
        drv.append(z['task_drive'])
    R = np.concatenate(reg)
    keep = (R == 'mc_active') & (np.concatenate(drv) == 1.0)
    labels = ['FF', 'FB', 'MC', 'FF×FB', 'FF×MC', 'FB×MC']
    out = {}
    for metric, arrs in acc.items():
        A = np.concatenate(arrs)[keep]
        rows = []
        for row in A:
            v = {frozenset(c.split('+')) - {''}: row[i] for i, c in enumerate(coal)}
            phi = shapley_values(v, MOTIFS)
            rows.append([phi['FF'], phi['FB'], phi['MC'],
                         interaction_2way(v, 'FF', 'FB'),
                         interaction_2way(v, 'FF', 'MC'),
                         interaction_2way(v, 'FB', 'MC')])
        out[metric] = np.mean(rows, axis=0)
    with plt.rc_context(SLIDE_RC):
        fig, ax = plt.subplots(figsize=(7.4, 4.9))
        x = np.arange(len(labels)); w = 0.38
        base = [BLUE, VERM, GREEN, GREY, GREY, GREY]
        ax.bar(x - w / 2, out['dec'], w, color=base, label='raw separation')
        ax.bar(x + w / 2, out['dec_excess_shuffle'], w, color=base, alpha=0.45,
               hatch='//', edgecolor='w', label='after null correction')
        ax.axhline(0, color='k', lw=1)
        ax.axvline(2.5, color='k', lw=0.8, ls=':')
        ax.text(1.0, 0.30, 'single motifs', ha='center', fontsize=12, color='0.3')
        ax.text(4.0, 0.30, 'pairs (interaction)', ha='center', fontsize=12, color='0.3')
        ax.set_xticks(x); ax.set_xticklabels(labels)
        ax.set_ylabel('Shapley contribution to separation')
        ax.set_ylim(-0.30, 0.34)
        ax.legend(loc='lower left', frameon=False)
        ax.grid(axis='y', alpha=0.25, lw=0.6); ax.set_axisbelow(True)
        fig.savefig(SLIDES / "slide-e2.png", dpi=200)
        plt.close(fig)
    print("  slide-e2: " + "  ".join(f"{l} {a:+.3f}/{b:+.3f}" for l, a, b in
                                      zip(labels, out['dec'], out['dec_excess_shuffle'])))


def slide_1a():
    """1A: dokładność klasyfikatora liniowego (STATUS sek. 3.7 — eksperyment zamknięty)."""
    acc = {'raw input': 0.940, 'via DG': 0.885, 'DG without\ninhibition': 0.935,
           'random sparse\ncode': 0.885}
    with plt.rc_context(SLIDE_RC):
        fig, ax = plt.subplots(figsize=(7.4, 4.9))
        ax.bar(list(acc), list(acc.values()), color=[VERM, BLUE, GREEN, PINK], width=0.6)
        for i, v in enumerate(acc.values()):
            ax.text(i, v - 0.006, f'{v:.3f}', ha='center', va='top', fontsize=13,
                    fontweight='bold', color='w')
        ax.axhline(acc['raw input'], color=VERM, ls='--', lw=1.3)
        ax.set_ylim(0.85, 0.96)
        ax.set_ylabel('linear classifier accuracy')
        ax.grid(axis='y', alpha=0.25, lw=0.6); ax.set_axisbelow(True)
        fig.savefig(SLIDES / "slide-1a.png", dpi=200)
        plt.close(fig)
    print("  slide-1a zapisany")


if __name__ == '__main__':
    FIGS.mkdir(parents=True, exist_ok=True)
    print("Generuję figury do artykułu:")
    fig1_concept()
    fig2_circuit()
    fig3_operating_point()
    fig4_findings()
    fig5_nulls()

    # te same figury pod slajdy (bez nagłówków „Figure N.") + figury jednopanelowe
    print("Figury pod slajdy:")
    SLIDES.mkdir(parents=True, exist_ok=True)
    SLIDE = True
    fig1_concept()
    fig2_circuit()
    fig3_operating_point()
    fig5_nulls()
    slide_e1()
    slide_e1p()
    slide_e2()
    slide_1a()
    print(f"\nGotowe → {FIGS}")
