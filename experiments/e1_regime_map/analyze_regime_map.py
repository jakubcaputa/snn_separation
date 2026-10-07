"""
e1_regime_map/analyze_regime_map.py

E1 — scalenie shardów mapy reżimów i figura „separacja vs aktywność".

Co ta analiza ma rozstrzygnąć
-----------------------------
Czy istnieje OKNO FUNKCJONALNE separacji (H1), czy też „separacja" w tym modelu
jest tylko cieniem wyciszenia sieci. To nie jest pytanie kosmetyczne: `dec`
(= r_in − r_out) rośnie, gdy sieć milknie, bo korelacja prawie pustego wektora
dąży do zera. Dlatego każda figura tutaj ma obok siebie PANEL KONTROLNY
aktywności i retention — bez nich wykres separacji jest nieuczciwy.

Werdykt (test kształtu maski) NIE jest tu liczony po raz drugi — pochodzi
z `run_regime_map.diagnose`, żeby istniała jedna definicja tego, co uznajemy
za artefakt.

Uruchomienie
------------
    python analyze_regime_map.py
    python analyze_regime_map.py --in "results/regime_map_full*.npz"
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

# dg_core leży w experiments/ — ścieżkę trzeba dodać PRZED importem z dg_core
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use('Agg')                    # HPC: brak DISPLAY
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

from dg_core.viz import PCT_TICKS, pct_formatter, pct_log_axis   # noqa: E402
from run_regime_map import (              # noqa: E402  — jedna definicja werdyktu
    MIN_ACTIVE_FRAC, MIN_FR_ACTIVE, MIN_RETENTION, diagnose,
)

HERE = Path(__file__).parent
RESULTS = HERE / "results"

SCALAR_KEYS = ('K_GC', 'W_FS_GC', 'seed', 'r_in', 'r_out', 'dec', 'r_out_cos',
               'overlap_jac', 'active_frac', 'fr_gc', 'fr_gc_active', 'sparseness',
               'fr_fs', 'fr_hmc', 'v_rest', 'v_th_eff', 'valid', 'retention')


def load_shards(pattern: str) -> dict:
    """Scala shardy po globie. Shardy są rozłączne, więc wystarczy konkatenacja."""
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"Brak plików pasujących do: {pattern}")

    out: dict[str, list] = {}
    grids: dict[str, np.ndarray] = {}
    for f in files:
        d = np.load(f)
        for k in d.files:
            if k.startswith('grid_'):
                grids[k] = d[k]
            elif k in SCALAR_KEYS:
                out.setdefault(k, []).append(d[k])

    merged = {k: np.concatenate(v) for k, v in out.items()}
    merged.update(grids)
    print(f"scalono {len(files)} plików → {len(merged['K_GC'])} punktów")
    if 'retention' not in merged:
        print("  ⚠️ brak kolumny 'retention' — to wynik ze starej wersji run_regime_map.py.")
        print("     Test informacyjny zostanie pominięty; przelicz sweep, żeby go dostać.")
    return merged


def aggregate_over_seeds(d: dict) -> dict:
    """Średnia i błąd standardowy po seedach dla każdej komórki (K, W).

    Przedziały ufności liczymy PO SEEDACH, bo to jedyne powtórzenia, jakie tu
    są — rozrzut między komórkami siatki to sygnał, nie szum.
    """
    keys = [k for k in ('dec', 'active_frac', 'fr_gc_active', 'retention', 'r_out')
            if k in d]
    cells = {}
    for i, (k, w) in enumerate(zip(d['K_GC'], d['W_FS_GC'])):
        cells.setdefault((float(k), float(w)), []).append(i)

    agg: dict[str, list] = {'K_GC': [], 'W_FS_GC': [], 'n_seeds': [], 'n_valid': []}
    for key in keys:
        agg[key], agg[key + '_sem'] = [], []

    for (k, w), idx in sorted(cells.items()):
        idx = np.array(idx)
        v = d['valid'][idx].astype(bool)
        agg['K_GC'].append(k)
        agg['W_FS_GC'].append(w)
        agg['n_seeds'].append(len(idx))
        agg['n_valid'].append(int(v.sum()))
        use = idx[v] if v.any() else idx          # gdy cała komórka odrzucona — bez maski
        for key in keys:
            vals = np.asarray(d[key][use], dtype=float)
            vals = vals[np.isfinite(vals)]
            agg[key].append(float(np.mean(vals)) if vals.size else np.nan)
            agg[key + '_sem'].append(
                float(np.std(vals, ddof=1) / np.sqrt(vals.size)) if vals.size > 1 else 0.0)

    return {k: np.asarray(v) for k, v in agg.items()}


def make_figure(d: dict, a: dict, out_png: Path) -> None:
    has_ret = 'retention' in a
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("E1 — mapa reżimów: czy separacja to okno funkcjonalne, czy cisza",
                 fontsize=13)

    cell_valid = a['n_valid'] > 0

    # (a) GŁÓWNA FIGURA: separacja vs ZMIERZONA aktywność, z CI po seedach.
    ax = axes[0, 0]
    m = cell_valid
    c = a['retention'][m] if has_ret else None
    ax.errorbar(a['active_frac'][m], a['dec'][m],
                yerr=a['dec_sem'][m], xerr=a['active_frac_sem'][m],
                fmt='none', ecolor='0.75', lw=0.8, zorder=1)
    kw = dict(c=c, cmap='viridis', vmin=0, vmax=1) if has_ret else dict(color='tab:blue')
    sc = ax.scatter(a['active_frac'][m], a['dec'][m], s=34, zorder=2, **kw)
    ax.axvline(MIN_ACTIVE_FRAC, color='crimson', ls='--', lw=1.2)
    ax.annotate(f"podłoga maski\n({MIN_ACTIVE_FRAC:.0%} aktywnych GC)",
                xy=(MIN_ACTIVE_FRAC, ax.get_ylim()[1]), xytext=(6, -30),
                textcoords='offset points', color='crimson', fontsize=8)
    pct_log_axis(ax)
    ax.set_xlabel("frakcja aktywnych GC (zmierzona)")
    ax.set_ylabel("separacja  dec = r_in − r_out")
    ax.set_title("(a) separacja vs aktywność — twierdzenie dotyczy TEJ osi")
    if has_ret:
        fig.colorbar(sc, ax=ax, label="retention (MI/H) — ile informacji przeżyło")

    # (b) PANEL KONTROLNY: co się dzieje z informacją tam, gdzie dec rośnie.
    ax = axes[0, 1]
    if has_ret:
        ax.errorbar(a['active_frac'][m], a['retention'][m], yerr=a['retention_sem'][m],
                    fmt='o', ms=4, color='tab:purple', ecolor='0.8', lw=0.8)
        ax.axhline(MIN_RETENTION, color='crimson', ls='--', lw=1.2,
                   label=f"próg informacyjny {MIN_RETENTION}")
        ax.axvline(MIN_ACTIVE_FRAC, color='crimson', ls=':', lw=1.0)
        pct_log_axis(ax)
        ax.set_ylabel("retention (MI/H)")
        ax.legend(fontsize=8)
    else:
        ax.text(0.5, 0.5, "brak kolumny 'retention'\n— przelicz sweep",
                ha='center', va='center', transform=ax.transAxes, color='crimson')
    ax.set_xlabel("frakcja aktywnych GC")
    ax.set_title("(b) panel kontrolny: informacja znika tam, gdzie dec rośnie")

    # (c) Mapa separacji na siatce parametrów — dla orientacji, nie dla tezy.
    ax = axes[1, 0]
    ks, ws = np.unique(a['K_GC']), np.unique(a['W_FS_GC'])
    grid = np.full((len(ks), len(ws)), np.nan)
    for k, w, val, ok in zip(a['K_GC'], a['W_FS_GC'], a['dec'], cell_valid):
        if ok:
            grid[np.searchsorted(ks, k), np.searchsorted(ws, w)] = val
    im = ax.imshow(grid, origin='lower', aspect='auto', cmap='magma',
                   extent=(ws[0], ws[-1], ks[0], ks[-1]))
    ax.set_xlabel("W_FS_GC — hamowanie FAZOWE")
    ax.set_ylabel("K_GC — hamowanie TONICZNE")
    ax.set_title("(c) separacja na siatce parametrów (szare = odrzucone maską)")
    fig.colorbar(im, ax=ax, label="dec")

    # (d) KURS WYMIANY — uczciwa oś: ile separacji za ile utraconej informacji.
    ax = axes[1, 1]
    if has_ret:
        keep = cell_valid & np.isfinite(a['retention'])
        sc2 = ax.scatter(a['retention'][keep], a['dec'][keep],
                         c=a['active_frac'][keep], cmap='cividis',
                         norm=matplotlib.colors.LogNorm(), s=34)
        ax.axvline(MIN_RETENTION, color='crimson', ls='--', lw=1.2)
        cb2 = fig.colorbar(sc2, ax=ax, label="frakcja aktywnych GC")
        # LogNorm domyślnie stawia znaczniki tylko na dekadach — przy zakresie
        # 0.02–0.97 zostawia to JEDNĄ etykietę. Wymuszamy te same progi co na osiach.
        lo, hi = a['active_frac'][keep].min(), a['active_frac'][keep].max()
        cb2.set_ticks([t for t in PCT_TICKS if lo <= t <= hi])
        cb2.ax.yaxis.set_major_formatter(pct_formatter())
        ax.set_xlabel("retention (MI/H) — ile informacji o wejściu przeżyło")
        ax.set_ylabel("separacja  dec")
    else:
        ax.text(0.5, 0.5, "brak kolumny 'retention'", ha='center', va='center',
                transform=ax.transAxes, color='crimson')
    ax.set_title("(d) kurs wymiany separacja ↔ informacja")

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out_png, dpi=150)
    print(f"figura → {out_png}")


def main():
    ap = argparse.ArgumentParser(description="E1: scalenie shardów + figura")
    ap.add_argument('--in', dest='inp', default=str(RESULTS / "regime_map_full*.npz"))
    ap.add_argument('--out', default=str(RESULTS / "regime_map_full.png"))
    args = ap.parse_args()

    d = load_shards(args.inp)
    a = aggregate_over_seeds(d)
    print(f"komórek siatki (K × W_FS_GC): {len(a['K_GC'])}  "
          f"| w pełni odrzuconych maską: {int((a['n_valid'] == 0).sum())}")

    make_figure(d, a, Path(args.out))

    # Werdykt — ta sama funkcja, której używa run_regime_map.py.
    diagnose(d)


if __name__ == '__main__':
    main()
