"""
e1_regime_map/analyze_matched_activity.py

E1′ — scalenie shardów, figura i werdykt dla H1′.

Po co osobno od `analyze_regime_map.py`
---------------------------------------
Tamten analizuje STARY eksperyment (`run_regime_map.py`), w którym aktywność była
wynikiem, a nie zmienną zadaną. Tu dane mają inną strukturę: aktywność jest
dostrojona bisekcją, a wielkością nośną jest NADWYŻKA ponad null o dopasowanej
rzadkości, nie samo `dec`.

Werdykt NIE jest liczony po raz drugi — pochodzi z `run_matched_activity.report`,
żeby istniała jedna definicja tego, co uznajemy za potwierdzenie H1′.

Uruchomienie
------------
    python analyze_matched_activity.py
    python analyze_matched_activity.py --in "results/matched_activity_full*.npz"
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402

from run_matched_activity import AF_TOL, report   # noqa: E402  — jeden werdykt

HERE = Path(__file__).parent
RESULTS = HERE / "results"


def load_shards(pattern: str) -> dict:
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"Brak plików pasujących do: {pattern}")
    out: dict[str, list] = {}
    for f in files:
        d = np.load(f)
        for k in d.files:
            out.setdefault(k, []).append(d[k])
    merged = {k: np.concatenate(v) for k, v in out.items()}
    print(f"scalono {len(files)} plików → {len(merged['W_FS_GC'])} punktów")
    return merged


def cells(p: dict, key: str, by: str, m: np.ndarray):
    """Średnia i SEM `key` w grupach po `by`, tylko na dopasowanych punktach."""
    xs = np.unique(p[by][m])
    mu = np.array([p[key][m & (p[by] == x)].mean() for x in xs])
    sem = np.array([p[key][m & (p[by] == x)].std(ddof=1)
                    / max(1, np.sqrt((m & (p[by] == x)).sum())) for x in xs])
    return xs, mu, sem


def make_figure(p: dict, out_png: Path) -> None:
    m = p['matched'].astype(bool)
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("E1′ — separacja ponad null o dopasowanej rzadkości "
                 f"(n={int(m.sum())} dostrojonych punktów)", fontsize=13)

    # (a) Sedno: surowe dec vs nadwyżka, w funkcji zadanej aktywności.
    ax = axes[0, 0]
    for key, lab, col in (('dec', 'surowe dec (mylące)', 'tab:gray'),
                          ('dec_excess_shuffle', 'nadwyżka − null permutacyjny', 'tab:red'),
                          ('dec_excess_kwta', 'nadwyżka − null k-WTA', 'tab:blue')):
        x, mu, sem = cells(p, key, 'target_af', m)
        ax.errorbar(x, mu, yerr=sem, fmt='o-', color=col, label=lab, capsize=3)
    ax.axhline(0, color='k', lw=1, ls='--')
    ax.set_xlabel("zadana frakcja aktywnych GC")
    ax.set_ylabel("separacja")
    ax.set_title("(a) surowe `dec` i nadwyżki nad dwoma nullami\n(permutacyjny jest zdegenerowany: nadwyżka = −r_out, STATUS sek. 3.5)")
    ax.legend(fontsize=8)

    # (b) Test H1': czy hamowanie fazowe cokolwiek kupuje przy wyrównanej ciszy.
    ax = axes[0, 1]
    x, mu, sem = cells(p, 'dec_excess_shuffle', 'W_FS_GC', m)
    ax.errorbar(x, mu, yerr=sem, fmt='o-', color='tab:red', capsize=3)
    ax.axhline(0, color='k', lw=1, ls='--')
    span = mu.max() - mu.min()
    ax.set_xlabel("W_FS_GC — hamowanie FAZOWE")
    ax.set_ylabel("nadwyżka − null permutacyjny")
    ax.set_title(f"(b) TEST H1′: płasko (rozstęp {span:.3f} ≈ SEM {sem.mean():.3f})")

    # (c) Tautologia retention: czy szczyt idzie za rzadkością wejścia.
    ax = axes[1, 0]
    for pa in np.unique(p['P_active'][m]):
        s = m & (p['P_active'] == pa)
        order = np.argsort(p['af_measured'][s])
        ax.plot(p['af_measured'][s][order], p['retention'][s][order], 'o', ms=4,
                alpha=0.6, label=f"P_active {pa:.2f}")
        pk = p['af_measured'][s][np.argmax(p['retention'][s])]
        ax.axvline(pk, ls=':', lw=1.2, color=ax.lines[-1].get_color())
    ax.set_xlabel("zmierzona frakcja aktywnych GC")
    ax.set_ylabel("retention (MI/H)")
    ax.set_title("(c) szczyt retention IDZIE za P_active → tautologia MI")
    ax.legend(fontsize=8)

    # (d) Kontrola dostrojenia — czy bisekcja faktycznie trafiła w cel.
    ax = axes[1, 1]
    ok, bad = p['matched'].astype(bool), ~p['matched'].astype(bool)
    ax.scatter(p['target_af'][ok], p['af_hit'][ok], s=18, c='tab:green', label='dostrojone')
    if bad.any():
        ax.scatter(p['target_af'][bad], p['af_hit'][bad], s=18, c='tab:orange',
                   label=f'poza zasięgiem K_GC (n={int(bad.sum())})')
    lim = [0, max(p['target_af'].max(), p['af_hit'].max()) * 1.05]
    ax.plot(lim, lim, 'k--', lw=1)
    ax.set_xlabel("cel aktywności")
    ax.set_ylabel("osiągnięta aktywność")
    ax.set_title(f"(d) kontrola bisekcji (tolerancja ±{AF_TOL})")
    ax.legend(fontsize=8)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out_png, dpi=150)
    print(f"figura → {out_png}")


def main():
    ap = argparse.ArgumentParser(description="E1′: scalenie + figura + werdykt")
    ap.add_argument('--in', dest='inp',
                    default=str(RESULTS / "matched_activity_full*.npz"))
    ap.add_argument('--out', default=str(RESULTS / "matched_activity_full.png"))
    args = ap.parse_args()

    p = load_shards(args.inp)
    n_match = int(p['matched'].sum())
    print(f"dostrojonych: {n_match}/{len(p['matched'])} (tol ±{AF_TOL})")
    make_figure(p, Path(args.out))
    report(p)


if __name__ == '__main__':
    main()
