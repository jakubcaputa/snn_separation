"""
e2_motif_attribution/analyze_motifs.py

Analiza wyników `run_lesion_grid.py`: wartości Shapleya, mapa dominującego motywu,
interakcje FF×FB, panel kontrolny (czy to na pewno separacja, a nie wyciszenie).

Figury (results/):
  fig1_dominance_map.png   — mapa dominacji (R_in × P_active), oba reżimy MC
  fig2_shapley_profiles.png— udział motywów jako funkcja R_in i P_active
  fig3_interactions.png    — interakcja FF×FB (redundancja wspólnej drogi FS→GC)
  fig4_sanity.png          — FR, rzadkość, frakcja aktywnych — kontrola artefaktów

Uruchomienie:
  python analyze_motifs.py --in lesion_grid_quick.npz
  python analyze_motifs.py --in "lesion_grid_full_shard*.npz"   # scala shardy
"""

from __future__ import annotations

import argparse
import glob
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:  # konsola Windows domyślnie cp1250 — dławi się strzałkami/φ w logach
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from dg_core.metrics import shapley_values, shapley_share, dominant_motif, interaction_2way  # noqa: E402
from dg_core.params import MOTIFS, MOTIF_LABELS  # noqa: E402
from dg_core.viz import (  # noqa: E402
    DIVERGING, MOTIF_COLORS, NONE_COLOR, SEQ_CMAP, diverging_norm, grid, use_style,
)

RESULTS = Path(__file__).parent / "results"

# Poniżej tej dekorelacji „dominacja" jest szumem, nie zjawiskiem → pole '—'
MIN_EFFECT = 0.01


def load(pattern: str) -> dict:
    """Wczytuje jeden NPZ lub scala shardy z joba tablicowego SLURM."""
    paths = sorted(glob.glob(str(RESULTS / pattern))) or sorted(glob.glob(pattern))
    if not paths:
        sys.exit(f"Brak plików pasujących do: {pattern}")

    parts = [dict(np.load(p, allow_pickle=True)) for p in paths]
    print(f"Wczytano {len(paths)} plik(ów): {', '.join(Path(p).name for p in paths)}")

    merged = {}
    concat_keys = [k for k in parts[0] if k.startswith('task_')] + [
        'r_in_measured', 'dec', 'r_out', 'fr_gc', 'fr_gc_active',
        'sparseness', 'active_frac', 'fr_fs', 'fr_hmc']
    for k in concat_keys:
        merged[k] = np.concatenate([p[k] for p in parts], axis=0)
    for k in ['coalitions', 'motifs', 'grid_R_in', 'grid_P_active', 'grid_drive',
              'grid_regimes', 'n_patterns', 'N_GC', 'T_ms']:
        merged[k] = parts[0][k]
    return merged


def compute_shapley(d: dict) -> dict:
    """
    Dla każdego (reżim, R_in, P_active, drive) uśrednia po seedach:
      φ_FF, φ_FB, φ_MC, dekorelację pełnego obwodu, interakcję FF×FB, metryki kontrolne.
    """
    coals = [str(c) for c in d['coalitions']]
    key2i = {c: i for i, c in enumerate(coals)}

    def as_sets(row):
        # '' → frozenset(); 'FF+MC' → frozenset({'FF','MC'})
        return {frozenset(c.split('+')) - {''}: row[key2i[c]] for c in coals}

    acc = defaultdict(lambda: defaultdict(list))
    for i in range(len(d['task_seed'])):
        cell = (str(d['task_regime'][i]), float(d['task_r_in'][i]),
                float(d['task_p_active'][i]), float(d['task_drive'][i]))
        v = as_sets(d['dec'][i])

        phi = shapley_values(v, MOTIFS)
        full = frozenset(MOTIFS)
        none = frozenset()

        for m in MOTIFS:
            acc[cell][f'phi_{m}'].append(phi[m])
        acc[cell]['dec_full'].append(v[full])
        acc[cell]['dec_none'].append(v[none])
        acc[cell]['inter_FF_FB'].append(interaction_2way(v, 'FF', 'FB'))
        acc[cell]['inter_FF_MC'].append(interaction_2way(v, 'FF', 'MC'))
        acc[cell]['inter_FB_MC'].append(interaction_2way(v, 'FB', 'MC'))
        acc[cell]['r_in'].append(float(d['r_in_measured'][i]))
        for m in ['fr_gc_active', 'sparseness', 'active_frac', 'fr_fs', 'fr_hmc']:
            acc[cell][m].append(d[m][i][key2i['FF+FB+MC']])
            acc[cell][m + '_none'].append(d[m][i][key2i['']])

    out = {}
    for cell, vals in acc.items():
        rec = {k: float(np.mean(v)) for k, v in vals.items()}
        rec.update({k + '_sd': float(np.std(v)) for k, v in vals.items() if k.startswith('phi_')})
        rec['n_seeds'] = len(vals['dec_full'])
        phi = {m: rec[f'phi_{m}'] for m in MOTIFS}
        rec['dominant'] = dominant_motif(phi, MIN_EFFECT)
        rec.update({f'share_{m}': s for m, s in shapley_share(phi).items()})
        out[cell] = rec
    return out


def _axis_grids(d):
    return ([str(x) for x in d['grid_regimes']],
            [float(x) for x in d['grid_R_in']],
            [float(x) for x in d['grid_P_active']],
            [float(x) for x in d['grid_drive']])


# ══════════════════════════════════════════════════════════════════════════════
# FIG 1 — mapa dominującego motywu
# ══════════════════════════════════════════════════════════════════════════════

def fig_dominance(S, d, drive_ref):
    regimes, R_ins, P_acts, _ = _axis_grids(d)
    ncol = len(regimes)
    fig, axes = plt.subplots(2, ncol, figsize=(5.4 * ncol, 8.4), squeeze=False)

    for c, reg in enumerate(regimes):
        # ── góra: kto dominuje (kategoryczne — stała barwa na motyw) ──────────
        ax = axes[0][c]
        img = np.zeros((len(P_acts), len(R_ins), 3))
        for i, p in enumerate(P_acts):
            for j, r in enumerate(R_ins):
                rec = S.get((reg, r, p, drive_ref))
                dom = rec['dominant'] if rec else '—'
                hexc = MOTIF_COLORS.get(dom, NONE_COLOR)
                rgb = tuple(int(hexc[k:k + 2], 16) / 255 for k in (1, 3, 5))
                # Nasycenie ∝ pewność dominacji (przewaga nad drugim motywem):
                # blade pole = „dominacja słaba", nie chowamy tego przed czytelnikiem.
                if rec and dom != '—':
                    sh = sorted([rec[f'share_{m}'] for m in MOTIFS], reverse=True)
                    conf = np.clip((sh[0] - sh[1]) * 2.2, 0.18, 1.0)
                else:
                    conf = 0.10
                img[i, j] = 1 - (1 - np.array(rgb)) * conf

        ax.imshow(img, origin='lower', aspect='auto', interpolation='nearest')
        for i, p in enumerate(P_acts):
            for j, r in enumerate(R_ins):
                rec = S.get((reg, r, p, drive_ref))
                if rec:
                    ax.text(j, i, f"{rec['dominant']}\n{rec['dec_full']:+.2f}",
                            ha='center', va='center', fontsize=6.5, color='#1A1A1A')
        ax.set(xticks=range(len(R_ins)), xticklabels=[f'{r:.2f}' for r in R_ins],
               yticks=range(len(P_acts)), yticklabels=[f'{p:.2f}' for p in P_acts],
               xlabel='R_in (podobieństwo wzorców)', ylabel='P_active (rzadkość wejścia)',
               title=f'Dominujący motyw — {reg}\n(napęd ×{drive_ref:g}; liczba = dekorelacja pełnego obwodu)')

        # ── dół: ile w ogóle jest separacji (rozbieżna — bo bywa ujemna!) ─────
        ax = axes[1][c]
        M = np.array([[S[(reg, r, p, drive_ref)]['dec_full'] if (reg, r, p, drive_ref) in S else np.nan
                       for r in R_ins] for p in P_acts])
        vmax = np.nanmax(np.abs(M)) if np.isfinite(M).any() else 1.0
        im = ax.imshow(M, origin='lower', aspect='auto', cmap=DIVERGING,
                       norm=diverging_norm(-vmax, vmax), interpolation='nearest')
        plt.colorbar(im, ax=ax, label='dekorelacja (R_in − R_out)')
        ax.set(xticks=range(len(R_ins)), xticklabels=[f'{r:.2f}' for r in R_ins],
               yticks=range(len(P_acts)), yticklabels=[f'{p:.2f}' for p in P_acts],
               xlabel='R_in', ylabel='P_active',
               title=f'Siła separacji — {reg}\n(brąz = obwód KORELUJE wzorce, czyli szkodzi)')

    handles = [plt.Rectangle((0, 0), 1, 1, fc=MOTIF_COLORS[m], label=MOTIF_LABELS[m])
               for m in MOTIFS]
    handles.append(plt.Rectangle((0, 0), 1, 1, fc=NONE_COLOR,
                                 label=f'brak efektu (dek. < {MIN_EFFECT})'))
    fig.legend(handles=handles, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.015))
    fig.suptitle('Kierunek 4 — który motyw hamowania dominuje separację',
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=[0, 0.035, 1, 0.97])
    p = RESULTS / 'fig1_dominance_map.png'
    fig.savefig(p); plt.close(fig)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# FIG 2 — profile Shapleya wzdłuż osi statystyki wejścia
# ══════════════════════════════════════════════════════════════════════════════

def fig_profiles(S, d, drive_ref):
    regimes, R_ins, P_acts, _ = _axis_grids(d)
    fig, axes = plt.subplots(len(regimes), 2, figsize=(11, 3.6 * len(regimes)), squeeze=False)

    for ri, reg in enumerate(regimes):
        # vs R_in (uśrednione po P_active)
        ax = axes[ri][0]
        for m in MOTIFS:
            mu = [np.mean([S[(reg, r, p, drive_ref)][f'phi_{m}']
                           for p in P_acts if (reg, r, p, drive_ref) in S]) for r in R_ins]
            sd = [np.std([S[(reg, r, p, drive_ref)][f'phi_{m}']
                          for p in P_acts if (reg, r, p, drive_ref) in S]) for r in R_ins]
            mu, sd = np.array(mu), np.array(sd)
            ax.plot(R_ins, mu, 'o-', color=MOTIF_COLORS[m], label=m, zorder=3)
            ax.fill_between(R_ins, mu - sd, mu + sd, color=MOTIF_COLORS[m], alpha=0.13, lw=0)
            ax.annotate(m, (R_ins[-1], mu[-1]), xytext=(5, 0), textcoords='offset points',
                        color=MOTIF_COLORS[m], fontsize=8, fontweight='bold', va='center')
        ax.axhline(0, color='#9A9A9A', lw=1, ls='--', zorder=1)
        grid(ax)
        ax.set(xlabel='R_in (podobieństwo wzorców)', ylabel='wkład Shapleya w dekorelację',
               title=f'{reg} — wkład motywu vs podobieństwo wejścia')

        # vs P_active (uśrednione po R_in)
        ax = axes[ri][1]
        for m in MOTIFS:
            mu = np.array([np.mean([S[(reg, r, p, drive_ref)][f'phi_{m}']
                                    for r in R_ins if (reg, r, p, drive_ref) in S]) for p in P_acts])
            sd = np.array([np.std([S[(reg, r, p, drive_ref)][f'phi_{m}']
                                   for r in R_ins if (reg, r, p, drive_ref) in S]) for p in P_acts])
            ax.plot(P_acts, mu, 'o-', color=MOTIF_COLORS[m], label=m, zorder=3)
            ax.fill_between(P_acts, mu - sd, mu + sd, color=MOTIF_COLORS[m], alpha=0.13, lw=0)
            ax.annotate(m, (P_acts[-1], mu[-1]), xytext=(5, 0), textcoords='offset points',
                        color=MOTIF_COLORS[m], fontsize=8, fontweight='bold', va='center')
        ax.axhline(0, color='#9A9A9A', lw=1, ls='--', zorder=1)
        grid(ax)
        ax.set(xlabel='P_active (rzadkość wejścia)', ylabel='wkład Shapleya',
               title=f'{reg} — wkład motywu vs rzadkość wejścia')
        if ri == 0:
            ax.legend(title='motyw', loc='best')

    fig.suptitle('Kierunek 4 — profile wkładu motywów (Σφ = cała separacja z hamowania)',
                 fontsize=12, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.955])
    p = RESULTS / 'fig2_shapley_profiles.png'
    fig.savefig(p); plt.close(fig)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# FIG 3 — interakcje (czy motywy się sumują, czy dublują)
# ══════════════════════════════════════════════════════════════════════════════

def fig_interactions(S, d, drive_ref):
    regimes, R_ins, P_acts, _ = _axis_grids(d)
    pairs = [('FF', 'FB'), ('FF', 'MC'), ('FB', 'MC')]
    fig, axes = plt.subplots(len(regimes), 3, figsize=(13.5, 3.9 * len(regimes)), squeeze=False)

    for ri, reg in enumerate(regimes):
        for ci, (a, b) in enumerate(pairs):
            ax = axes[ri][ci]
            M = np.array([[S[(reg, r, p, drive_ref)][f'inter_{a}_{b}']
                           if (reg, r, p, drive_ref) in S else np.nan
                           for r in R_ins] for p in P_acts])
            vmax = np.nanmax(np.abs(M)) if np.isfinite(M).any() else 1.0
            im = ax.imshow(M, origin='lower', aspect='auto', cmap=DIVERGING,
                           norm=diverging_norm(-vmax, vmax), interpolation='nearest')
            plt.colorbar(im, ax=ax, label='interakcja')
            ax.set(xticks=range(len(R_ins)), xticklabels=[f'{r:.2f}' for r in R_ins],
                   yticks=range(len(P_acts)), yticklabels=[f'{p:.2f}' for p in P_acts],
                   xlabel='R_in', ylabel='P_active',
                   title=f'{reg}: {a} × {b}')

    fig.suptitle('Kierunek 4 — interakcje motywów\n'
                 'brąz = redundancja (dublują się, np. wspólna droga FS→GC)   ·   '
                 'niebieski = synergia (razem dają więcej niż osobno)',
                 fontsize=11, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    p = RESULTS / 'fig3_interactions.png'
    fig.savefig(p); plt.close(fig)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# FIG 4 — panel kontrolny: separacja czy zwykłe wyciszenie sieci?
# ══════════════════════════════════════════════════════════════════════════════

def fig_sanity(S, d, drive_ref):
    """
    Kontrola artefaktu, którego wymagałby każdy recenzent: obwód może „poprawić"
    R_out po prostu uciszając GC (mało spajków → korelacja spada z szumu, nie z
    obliczeń). Jeśli dekorelacja rośnie, a FR aktywnych GC leci do zera — to nie
    jest separacja. Te panele pozwalają to od razu zobaczyć.
    """
    regimes, R_ins, P_acts, _ = _axis_grids(d)
    fig, axes = plt.subplots(len(regimes), 3, figsize=(13.5, 3.9 * len(regimes)), squeeze=False)

    panels = [
        ('fr_gc_active', 'FR aktywnych GC [Hz]  (kanon DG ≈ 6 Hz)', SEQ_CMAP),
        ('active_frac', 'frakcja aktywnych GC', SEQ_CMAP),
        ('fr_hmc', 'FR mossy cells [Hz]', SEQ_CMAP),
    ]
    for ri, reg in enumerate(regimes):
        for ci, (key, title, cmap) in enumerate(panels):
            ax = axes[ri][ci]
            M = np.array([[S[(reg, r, p, drive_ref)][key] if (reg, r, p, drive_ref) in S else np.nan
                           for r in R_ins] for p in P_acts])
            im = ax.imshow(M, origin='lower', aspect='auto', cmap=cmap, interpolation='nearest')
            plt.colorbar(im, ax=ax)
            for i in range(len(P_acts)):
                for j in range(len(R_ins)):
                    if np.isfinite(M[i, j]):
                        ax.text(j, i, f'{M[i, j]:.1f}', ha='center', va='center',
                                fontsize=6, color='#2B2B2B')
            ax.set(xticks=range(len(R_ins)), xticklabels=[f'{r:.2f}' for r in R_ins],
                   yticks=range(len(P_acts)), yticklabels=[f'{p:.2f}' for p in P_acts],
                   xlabel='R_in', ylabel='P_active', title=f'{reg} — {title}')

    fig.suptitle('Kierunek 4 — kontrola: czy to separacja, czy tylko wyciszenie sieci?\n'
                 '(dekorelacja przy FR→0 byłaby artefaktem, nie obliczeniem)',
                 fontsize=11, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    p = RESULTS / 'fig4_sanity.png'
    fig.savefig(p); plt.close(fig)
    return p


# ══════════════════════════════════════════════════════════════════════════════

def print_summary(S, d, drive_ref):
    regimes, R_ins, P_acts, _ = _axis_grids(d)
    print("\n" + "=" * 92)
    print("PODSUMOWANIE — wkład Shapleya (uśredniony po siatce statystyk wejścia)")
    print("=" * 92)
    for reg in regimes:
        cells = [v for k, v in S.items() if k[0] == reg and k[3] == drive_ref]
        if not cells:
            continue
        phi = {m: np.mean([c[f'phi_{m}'] for c in cells]) for m in MOTIFS}
        tot = sum(phi.values())
        print(f"\n[{reg}]  n={len(cells)} punktów siatki × {cells[0]['n_seeds']} seedów")
        print(f"  dekorelacja: brak hamowania {np.mean([c['dec_none'] for c in cells]):+.3f}"
              f"  →  pełny obwód {np.mean([c['dec_full'] for c in cells]):+.3f}")
        # Σφ = v(pełny) − v(brak hamowania), więc udziały sumują się do 100%.
        # Udział UJEMNY jest sensowny: motyw sam z siebie POGARSZA separację
        # (np. MC są pobudzające → re-ekscytują GC → korelują wzorce), a zysk
        # przynosi dopiero w interakcji z hamowaniem — patrz wiersze poniżej.
        for m in MOTIFS:
            share = phi[m] / tot * 100 if abs(tot) > 1e-9 else 0.0
            n = min(25, int(round(abs(share) / 4)))
            bar = ('▓' if phi[m] < 0 else '█') * n
            sign = ' (POGARSZA sam)' if phi[m] < -1e-4 else ''
            print(f"    φ_{m:<3s} = {phi[m]:+.4f}   ({share:6.1f}%)  {bar}{sign}")
        for a, b in [('FF', 'FB'), ('FF', 'MC'), ('FB', 'MC')]:
            i = np.mean([c[f'inter_{a}_{b}'] for c in cells])
            tag = 'redundancja' if i < -0.005 else ('synergia' if i > 0.005 else 'addytywne')
            print(f"    {a}×{b}: {i:+.4f}  ({tag})")

        doms = [c['dominant'] for c in cells]
        counts = {x: doms.count(x) for x in set(doms)}
        print("    dominacja w polach siatki: " +
              ', '.join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])))
        print(f"    FR aktywnych GC: {np.mean([c['fr_gc_active'] for c in cells]):.1f} Hz"
              f"  |  FR MC: {np.mean([c['fr_hmc'] for c in cells]):.1f} Hz")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', default='lesion_grid_quick.npz')
    ap.add_argument('--drive', type=float, default=1.0,
                    help='który poziom napędu pokazać na mapach (domyślnie 1.0 = kanon)')
    args = ap.parse_args()

    use_style()
    RESULTS.mkdir(exist_ok=True)

    d = load(args.inp)
    S = compute_shapley(d)
    print(f"Punktów (reżim × R_in × P_active × drive): {len(S)}")

    drives = sorted({k[3] for k in S})
    drive_ref = args.drive if args.drive in drives else drives[0]
    if drive_ref != args.drive:
        print(f"Uwaga: napęd {args.drive} nieobecny; używam {drive_ref}")

    print_summary(S, d, drive_ref)

    print("\nFigury:")
    for f in (fig_dominance(S, d, drive_ref), fig_profiles(S, d, drive_ref),
              fig_interactions(S, d, drive_ref), fig_sanity(S, d, drive_ref)):
        print(f"  {f}")


if __name__ == '__main__':
    main()
