"""
e1_regime_map/analyze_matched_activity_wide.py

E1″ — szerszy sweep E1′: scalenie shardów, figury i werdykt.

Werdykt NIE jest liczony tutaj — pochodzi z `run_matched_activity.prereg_test`,
czyli z testu zapisanego PRZED liczeniem (STATUS sek. 3.4). Ten skrypt tylko
rysuje i wywołuje tamtą funkcję.

Figury (w results/):
  matched_activity_wide_dec.png     separacja vs W_FS_GC, siatka reżim × R_in
  matched_activity_wide_sept.png    dyskryminowalność czasowa, ta sama siatka
  matched_activity_wide_tuning.png  gdzie bisekcja trafiła w zadaną aktywność

Uruchomienie:
    python analyze_matched_activity_wide.py
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402

from run_matched_activity import PREREG, prereg_test   # noqa: E402

RESULTS = Path(__file__).parent / "results"


def load(pattern: str) -> dict:
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"Brak plików: {pattern}")
    parts = [dict(np.load(f, allow_pickle=True)) for f in files]
    keys = set(parts[0])
    for q in parts[1:]:
        keys &= set(q)
    p = {k: np.concatenate([q[k] for q in parts]) for k in keys}
    print(f"scalono {len(files)} plików → {len(p['dec'])} punktów")
    return p


def _grid_plot(p: dict, key: str, ylabel: str, title: str, out: Path,
               reliable_only: bool = False) -> None:
    m = p['matched'].astype(bool)
    regimes = list(dict.fromkeys(p['regime'].tolist()))
    rins = sorted(set(p['R_in_target'].tolist()))
    targets = sorted(set(p['target_af'].tolist()))
    cmap = plt.get_cmap('viridis')
    fig, axes = plt.subplots(len(regimes), len(rins), figsize=(3.4 * len(rins), 3.0 * len(regimes)),
                             sharex=True, sharey=True, squeeze=False)
    for i, reg in enumerate(regimes):
        for j, r in enumerate(rins):
            ax = axes[i, j]
            for k, a in enumerate(targets):
                s_ = m & (p['regime'] == reg) & (p['R_in_target'] == r) & (p['target_af'] == a)
                ws = np.unique(p['W_FS_GC'][s_])
                mu, se, ok_ws = [], [], []
                for w in ws:
                    y = p[key][s_ & (p['W_FS_GC'] == w)]
                    y = y[np.isfinite(y)]
                    if y.size < PREREG['min_points_per_w']:
                        continue
                    ok_ws.append(w); mu.append(y.mean())
                    se.append(y.std(ddof=1) / np.sqrt(y.size) if y.size > 1 else 0)
                if not ok_ws:
                    continue
                faded = reliable_only and \
                    np.nanmean(p['r_within_t'][s_]) < PREREG['min_r_within_t']
                col = cmap(k / max(1, len(targets) - 1))
                ax.errorbar(ok_ws, mu, yerr=se, fmt='-o', ms=3, lw=1.6, capsize=2,
                            color=col, alpha=(0.25 if faded else 1.0),
                            ls=(':' if faded else '-'),
                            label=f'{a:.0%}' + (' (nierzetelne)' if faded else ''))
            ax.axhline(0, color='0.6', lw=0.8)
            ax.grid(alpha=0.25, lw=0.5)
            if i == 0:
                ax.set_title(f'R_in = {r:.2f}')
            if j == 0:
                ax.set_ylabel(f'{reg}\n{ylabel}')
            if i == len(regimes) - 1:
                ax.set_xlabel('W_FS_GC — hamowanie fazowe')
    axes[0, -1].legend(title='aktywność', fontsize=7, title_fontsize=8, loc='best')
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"figura → {out}")


def _tuning_plot(p: dict, out: Path) -> None:
    """Odsetek dostrojonych punktów — luki pokazują, gdzie zadana aktywność jest
    nieosiągalna (np. możliwa bistabilność w mc_active)."""
    regimes = list(dict.fromkeys(p['regime'].tolist()))
    rins = sorted(set(p['R_in_target'].tolist()))
    targets = sorted(set(p['target_af'].tolist()))
    ws = sorted(set(p['W_FS_GC'].tolist()))
    fig, axes = plt.subplots(len(regimes), len(rins), figsize=(3.2 * len(rins), 2.6 * len(regimes)),
                             squeeze=False)
    for i, reg in enumerate(regimes):
        for j, r in enumerate(rins):
            M = np.full((len(targets), len(ws)), np.nan)
            for a_i, a in enumerate(targets):
                for w_i, w in enumerate(ws):
                    s_ = (p['regime'] == reg) & (p['R_in_target'] == r) & \
                        (p['target_af'] == a) & (p['W_FS_GC'] == w)
                    if s_.any():
                        M[a_i, w_i] = p['matched'][s_].mean()
            ax = axes[i, j]
            im = ax.imshow(M, origin='lower', aspect='auto', cmap='Greens', vmin=0, vmax=1)
            ax.set_xticks(range(len(ws))); ax.set_xticklabels([f'{w:g}' for w in ws], fontsize=7)
            ax.set_yticks(range(len(targets))); ax.set_yticklabels([f'{a:.0%}' for a in targets])
            if i == 0:
                ax.set_title(f'R_in = {r:.2f}')
            if j == 0:
                ax.set_ylabel(f'{reg}\nzadana aktywność')
            if i == len(regimes) - 1:
                ax.set_xlabel('W_FS_GC')
    fig.colorbar(im, ax=axes, label='odsetek dostrojonych', shrink=0.8)
    fig.suptitle('E1″ — gdzie bisekcja trafiła w zadaną aktywność', fontsize=11)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"figura → {out}")


def main():
    ap = argparse.ArgumentParser(description="E1″: scalenie + figury + werdykt z preregistracji")
    ap.add_argument('--in', dest='inp', default=str(RESULTS / "matched_activity_wide_shard*.npz"))
    args = ap.parse_args()
    p = load(args.inp)

    m = p['matched'].astype(bool)
    print(f"dostrojonych: {int(m.sum())}/{len(m)}")
    for reg in dict.fromkeys(p['regime'].tolist()):
        s_ = p['regime'] == reg
        print(f"  {reg}: {int(m[s_].sum())}/{int(s_.sum())}")

    _grid_plot(p, 'dec', 'separacja dec',
               'E1″ — separacja vs hamowanie fazowe przy zadanej aktywności',
               RESULTS / "matched_activity_wide_dec.png")
    if 'sep_t' in p:
        _grid_plot(p, 'sep_t', 'dyskrym. czasowa sep_t',
                   'E1″ — dyskryminowalność czasowa (okna 20 ms) vs hamowanie fazowe',
                   RESULTS / "matched_activity_wide_sept.png", reliable_only=True)
    _tuning_plot(p, RESULTS / "matched_activity_wide_tuning.png")

    prereg_test(p)


if __name__ == '__main__':
    main()
