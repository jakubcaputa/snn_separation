"""
readout_deferred/analyze_readout.py

Analiza kierunku 1: czy DG realnie pomaga odbiorcy downstream.

Figury (results/):
  fig1_accuracy.png     — dokładność w 4 warunkach vs R_in i vs szum
  fig2_delta_acc.png    — Δ accuracy (DG − raw) i (DG − random): mapy (R_in × szum)
  fig3_mechanism.png    — czy zysk idzie w parze ze spadkiem korelacji reprezentacji
  fig4_capacity.png     — pojemność pamięci vs siła hamowania (eksperyment 1B)

Uruchomienie:
  python analyze_readout.py --in classification_quick.npz
  python analyze_readout.py --in classification_full.npz --capacity capacity_full.npz
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

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from dg_core.viz import COND_COLORS, DIVERGING, diverging_norm, grid, use_style  # noqa: E402

RESULTS = Path(__file__).parent / "results"

COND_LABELS = {
    'raw':      'raw (bez DG)',
    'dg':       'DG (pełny obwód)',
    'dg_noinh': 'DG bez hamowania',
    'random':   'losowa rzadka proj. (k dopasowane)',
}


def load(pattern: str, concat_keys_prefix=('task_',)) -> dict:
    paths = sorted(glob.glob(str(RESULTS / pattern))) or sorted(glob.glob(pattern))
    if not paths:
        sys.exit(f"Brak plików pasujących do: {pattern}")
    parts = [dict(np.load(p, allow_pickle=True)) for p in paths]
    print(f"Wczytano {len(paths)} plik(ów): {', '.join(Path(p).name for p in paths)}")

    merged = {}
    n0 = len(parts[0]['task_seed'])
    for k in parts[0]:
        if parts[0][k].ndim >= 1 and parts[0][k].shape and parts[0][k].shape[0] == n0:
            merged[k] = np.concatenate([p[k] for p in parts], axis=0)
        else:
            merged[k] = parts[0][k]
    return merged


def agg(d: dict, key_fields: list[str], value_fields: list[str]) -> dict:
    """Uśrednia po seedach: {(pola kluczowe) → {pole → średnia}}."""
    acc = defaultdict(lambda: defaultdict(list))
    n = len(d['task_seed'])
    for i in range(n):
        key = tuple(float(d[f][i]) for f in key_fields)
        for v in value_fields:
            acc[key][v].append(float(d[v][i]))
    return {k: {v: float(np.mean(vals)) for v, vals in rec.items()}
            for k, rec in acc.items()}


# ══════════════════════════════════════════════════════════════════════════════
# Klasyfikacja (1A)
# ══════════════════════════════════════════════════════════════════════════════

def fig_accuracy(A, d):
    conds = [str(c) for c in d['conditions']]
    R_ins = [float(x) for x in d['grid_R_in']]
    noises = [float(x) for x in d['grid_noise']]
    chance = float(d['chance'])

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))

    # vs R_in (uśrednione po szumie)
    ax = axes[0]
    for c in conds:
        mu = [np.mean([A[(r, n)][f'acc_{c}'] for n in noises if (r, n) in A]) for r in R_ins]
        ax.plot(R_ins, mu, 'o-', color=COND_COLORS[c], label=COND_LABELS[c], zorder=3)
    ax.axhline(chance, color='#9A9A9A', ls='--', lw=1, zorder=1)
    ax.annotate(f'poziom przypadku ({chance:.2f})', (R_ins[0], chance), xytext=(0, 5),
                textcoords='offset points', fontsize=7, color='#6E6E6E')
    grid(ax)
    ax.set(xlabel='R_in (podobieństwo klas)', ylabel='dokładność klasyfikacji',
           title='Dokładność vs podobieństwo klas\n(im bardziej podobne klasy, tym trudniej)')
    ax.legend(loc='lower left')

    # vs szum (uśrednione po R_in)
    ax = axes[1]
    for c in conds:
        mu = [np.mean([A[(r, n)][f'acc_{c}'] for r in R_ins if (r, n) in A]) for n in noises]
        ax.plot(noises, mu, 'o-', color=COND_COLORS[c], label=COND_LABELS[c], zorder=3)
    ax.axhline(chance, color='#9A9A9A', ls='--', lw=1, zorder=1)
    grid(ax)
    ax.set(xlabel='poziom szumu (frakcja przerzuconych bitów)',
           ylabel='dokładność klasyfikacji',
           title='Dokładność vs szum wejścia')

    fig.suptitle('Kierunek 1 — czy warstwa DG pomaga klasyfikatorowi liniowemu?',
                 fontsize=12, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    p = RESULTS / 'fig1_accuracy.png'
    fig.savefig(p); plt.close(fig)
    return p


def fig_delta(A, d):
    R_ins = [float(x) for x in d['grid_R_in']]
    noises = [float(x) for x in d['grid_noise']]

    comps = [('dg', 'raw', 'Δ acc: DG − raw\n(czy DG w ogóle pomaga?)'),
             ('dg', 'random', 'Δ acc: DG − losowa rzadka\n(czy liczy się STRUKTURA DG, nie sama rzadkość?)'),
             ('dg', 'dg_noinh', 'Δ acc: DG − DG bez hamowania\n(czy pracę wykonuje OBWÓD, nie sam próg?)')]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3))
    for ax, (a, b, title) in zip(axes, comps):
        M = np.array([[A[(r, n)][f'acc_{a}'] - A[(r, n)][f'acc_{b}'] if (r, n) in A else np.nan
                       for r in R_ins] for n in noises])
        vmax = np.nanmax(np.abs(M)) if np.isfinite(M).any() else 1.0
        im = ax.imshow(M, origin='lower', aspect='auto', cmap=DIVERGING,
                       norm=diverging_norm(-vmax, vmax), interpolation='nearest')
        plt.colorbar(im, ax=ax, label='Δ dokładności')
        for i in range(len(noises)):
            for j in range(len(R_ins)):
                if np.isfinite(M[i, j]):
                    ax.text(j, i, f'{M[i, j]:+.3f}', ha='center', va='center',
                            fontsize=6.5, color='#1A1A1A')
        ax.set(xticks=range(len(R_ins)), xticklabels=[f'{r:.2f}' for r in R_ins],
               yticks=range(len(noises)), yticklabels=[f'{n:.2f}' for n in noises],
               xlabel='R_in', ylabel='szum', title=title)

    fig.suptitle('Kierunek 1 — zysk z DG  (niebieski = DG lepsze; brąz = DG SZKODZI)',
                 fontsize=12, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    p = RESULTS / 'fig2_delta_acc.png'
    fig.savefig(p); plt.close(fig)
    return p


def fig_mechanism(A, d):
    """
    Łącznik z kierunkiem 4: jeśli DG podnosi dokładność, powinno to iść w parze ze
    SPADKIEM korelacji reprezentacji między klasami. Jeśli punkty nie układają się
    wzdłuż tej zależności, zysk pochodzi z czegoś innego niż separacja — i lepiej
    o tym wiedzieć, niż to przemilczeć.
    """
    conds = [str(c) for c in d['conditions']]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))

    ax = axes[0]
    for c in conds:
        xs = [rec[f'r_repr_{c}'] for rec in A.values()]
        ys = [rec[f'acc_{c}'] for rec in A.values()]
        ax.scatter(xs, ys, s=34, color=COND_COLORS[c], label=COND_LABELS[c],
                   alpha=0.85, edgecolors='white', linewidths=1.2, zorder=3)
    grid(ax, axis='both')
    ax.set(xlabel='korelacja reprezentacji między klasami (R_repr)',
           ylabel='dokładność klasyfikacji',
           title='Mechanizm: niższa korelacja reprezentacji → wyższa dokładność')
    ax.legend(loc='best')

    ax = axes[1]
    xs = [rec['r_repr_raw'] - rec['r_repr_dg'] for rec in A.values()]
    ys = [rec['acc_dg'] - rec['acc_raw'] for rec in A.values()]
    ax.scatter(xs, ys, s=40, color=COND_COLORS['dg'], alpha=0.85,
               edgecolors='white', linewidths=1.2, zorder=3)
    if len(xs) > 2 and np.std(xs) > 1e-9:
        b, a0 = np.polyfit(xs, ys, 1)
        xr = np.linspace(min(xs), max(xs), 50)
        r = float(np.corrcoef(xs, ys)[0, 1])
        ax.plot(xr, a0 + b * xr, color='#5A5A5A', lw=1.5, ls='--', zorder=2,
                label=f'dopasowanie (r = {r:.2f})')
        ax.legend(loc='best')
    ax.axhline(0, color='#9A9A9A', lw=1, zorder=1)
    ax.axvline(0, color='#9A9A9A', lw=1, zorder=1)
    grid(ax, axis='both')
    ax.set(xlabel='dekorelacja wniesiona przez DG  (R_repr raw − R_repr DG)',
           ylabel='zysk dokładności  (acc DG − acc raw)',
           title='Czy zysk bierze się WŁAŚNIE z separacji?\n(to spina kierunek 1 z kierunkiem 4)')

    fig.suptitle('Kierunek 1 — mechanizm zysku', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    p = RESULTS / 'fig3_mechanism.png'
    fig.savefig(p); plt.close(fig)
    return p


def summary_classification(A, d):
    conds = [str(c) for c in d['conditions']]
    chance = float(d['chance'])
    print("\n" + "=" * 88)
    print(f"KIERUNEK 1A — klasyfikacja ({int(d['n_classes'])} klas, przypadek = {chance:.2f})")
    print("=" * 88)
    print(f"\n{'warunek':<36} {'średnia acc':>12} {'min':>8} {'max':>8}")
    for c in conds:
        vals = [rec[f'acc_{c}'] for rec in A.values()]
        print(f"{COND_LABELS[c]:<36} {np.mean(vals):>12.3f} {np.min(vals):>8.3f} {np.max(vals):>8.3f}")

    d_raw = np.mean([rec['acc_dg'] - rec['acc_raw'] for rec in A.values()])
    d_rnd = np.mean([rec['acc_dg'] - rec['acc_random'] for rec in A.values()])
    d_inh = np.mean([rec['acc_dg'] - rec['acc_dg_noinh'] for rec in A.values()])
    print(f"\n  Δ acc  DG − raw               : {d_raw:+.3f}   ← czy DG w ogóle pomaga")
    print(f"  Δ acc  DG − losowa rzadka     : {d_rnd:+.3f}   ← czy liczy się struktura DG")
    print(f"  Δ acc  DG − DG bez hamowania  : {d_inh:+.3f}   ← czy pracę wykonuje obwód")

    best = max(A.items(), key=lambda kv: kv[1]['acc_dg'] - kv[1]['acc_raw'])
    (r, n), rec = best
    print(f"\n  Największy zysk z DG przy R_in={r:.2f}, szum={n:.2f}: "
          f"{rec['acc_dg'] - rec['acc_raw']:+.3f} "
          f"(raw {rec['acc_raw']:.3f} → DG {rec['acc_dg']:.3f})")


# ══════════════════════════════════════════════════════════════════════════════
# Pojemność pamięci (1B)
# ══════════════════════════════════════════════════════════════════════════════

def _capacity(C, cond, w, Ns, thr, tag):
    """Największe P, przy którym jakość odtworzenia jeszcze trzyma próg."""
    cap = 0
    for n in Ns:
        key = (w, float(n))
        if key in C and C[key][f'recall{tag}_{cond}'] >= thr:
            cap = n
        else:
            break
    return cap


def fig_capacity(dc):
    conds = [str(c) for c in dc['conditions']]
    Ws = [float(x) for x in dc['grid_W_FS_GC']]
    Ns = [int(x) for x in dc['grid_n_store']]
    thr = float(dc['recall_thr'])

    tags = ['', '_matched'] if 'recall_matched_dg' in dc else ['']
    vals = []
    for t in tags:
        vals += [f'recall{t}_{c}' for c in conds] + [f'r_repr{t}_{c}' for c in conds]
        vals += [f'sparsity{t}_{c}' for c in conds if f'sparsity{t}_{c}' in dc]
    C = agg(dc, ['task_w_fs_gc', 'task_n_store'], vals)

    w_ref = 1.0 if 1.0 in Ws else Ws[len(Ws) // 2]
    fig, axes = plt.subplots(1, 1 + len(tags), figsize=(6.2 * (1 + len(tags)), 4.4),
                             squeeze=False)
    axes = axes[0]

    # krzywe degradacji (kod naturalny)
    ax = axes[0]
    for c in conds:
        ys = [C[(w_ref, float(n))][f'recall_{c}'] for n in Ns if (w_ref, float(n)) in C]
        ax.plot(Ns[:len(ys)], ys, 'o-', color=COND_COLORS[c], label=COND_LABELS[c], zorder=3)
    ax.axhline(thr, color='#9A9A9A', ls='--', lw=1, zorder=1)
    ax.annotate(f'próg ({thr:.2f})', (Ns[0], thr), xytext=(0, 5),
                textcoords='offset points', fontsize=7, color='#6E6E6E')
    grid(ax)
    ax.set(xlabel='liczba zapisanych wzorców P', ylabel='jakość odtworzenia (Jaccard)',
           title=f'Degradacja pamięci przy obciążeniu\n(kod naturalny, W FS→GC = {w_ref:g})')
    ax.legend(loc='best')

    titles = {
        '': 'Pojemność vs siła hamowania\n(kod naturalny — metryka główna)',
        '_matched': 'Kontrola: rzadkość WYRÓWNANA\n(czy przewaga to tylko rzadkość?)',
    }
    for ax, t in zip(axes[1:], tags):
        for c in conds:
            caps = [_capacity(C, c, w, Ns, thr, t) for w in Ws]
            ax.plot(Ws, caps, 'o-', color=COND_COLORS[c], label=COND_LABELS[c], zorder=3)
        grid(ax)
        ax.set(xlabel='siła hamowania  W FS→GC [mV]',
               ylabel=f'pojemność (max P, jakość ≥ {thr:.2f})', title=titles[t])
        ax.legend(loc='best')

    fig.suptitle('Kierunek 1B — pojemność pamięci skojarzeniowej (DG → CA3)',
                 fontsize=12, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    p = RESULTS / 'fig4_capacity.png'
    fig.savefig(p); plt.close(fig)

    print("\n" + "=" * 88)
    print(f"KIERUNEK 1B — pojemność pamięci (próg jakości ≥ {thr:.2f})")
    print("=" * 88)
    for t in tags:
        label = 'kod naturalny (metryka główna)' if t == '' else 'rzadkość wyrównana (kontrola)'
        print(f"\n[{label}]")
        sp = {c: np.mean([rec[f'sparsity{t}_{c}'] for rec in C.values()])
              for c in conds if f'sparsity{t}_{c}' in next(iter(C.values()))}
        if sp:
            print("  rzadkość kodu: " + ', '.join(f'{c}={v:.3f}' for c, v in sp.items()))
        print(f"\n  {'W FS→GC':>9} " + ' '.join(f'{COND_LABELS[c][:16]:>17}' for c in conds))
        for w in Ws:
            row = ' '.join(f'{_capacity(C, c, w, Ns, thr, t):>17d}' for c in conds)
            print(f"  {w:>9.2f} " + row)
    return p


# ══════════════════════════════════════════════════════════════════════════════

def fig_window(d):
    """
    Kluczowa figura wyniku negatywnego: zysk z DG jako funkcja OKNA ODCZYTU.

    Przy długim oknie odbiorca zlicza setki spajków PP → baseline 'raw' jest
    praktycznie bezszumowy i DG (transformacja stratna) może tylko szkodzić.
    Dopiero krótkie okno tworzy reżim, w którym separacja ma co poprawiać.
    Jeśli Δacc nie rośnie przy skracaniu okna, hipoteza „DG pomaga odbiorcy"
    nie broni się nawet w reżimie trudnym — i to też trzeba pokazać.
    """
    Ts = sorted({float(x) for x in d['grid_T_ms']})
    if len(Ts) < 2:
        return None
    conds = [str(c) for c in d['conditions']]
    B = agg(d, ['task_t_ms'], [f'acc_{c}' for c in conds])

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))

    ax = axes[0]
    for c in conds:
        ax.plot(Ts, [B[(T,)][f'acc_{c}'] for T in Ts], 'o-',
                color=COND_COLORS[c], label=COND_LABELS[c], zorder=3)
    ax.axhline(float(d['chance']), color='#9A9A9A', ls='--', lw=1, zorder=1)
    grid(ax)
    ax.set(xlabel='okno odczytu T [ms]', ylabel='dokładność klasyfikacji',
           title='Dokładność vs okno odczytu\n(krótkie okno = mniej spajków = trudniej)')
    ax.legend(loc='best')

    ax = axes[1]
    delta = [B[(T,)]['acc_dg'] - B[(T,)]['acc_raw'] for T in Ts]
    colors = ['#0072B2' if v >= 0 else '#D55E00' for v in delta]
    ax.bar([str(int(T)) for T in Ts], delta, color=colors, width=0.6, zorder=3)
    ax.axhline(0, color='#5A5A5A', lw=1.2, zorder=2)
    for i, v in enumerate(delta):
        ax.annotate(f'{v:+.3f}', (i, v), ha='center',
                    va='bottom' if v >= 0 else 'top',
                    xytext=(0, 3 if v >= 0 else -3), textcoords='offset points',
                    fontsize=8)
    grid(ax)
    ax.set(xlabel='okno odczytu T [ms]', ylabel='Δ acc (DG − raw)',
           title='Zysk z DG vs okno odczytu\n(niebieski = DG pomaga; brąz = DG szkodzi)')

    fig.suptitle('Kierunek 1 — czy DG pomaga zależy od OKNA ODCZYTU odbiorcy',
                 fontsize=12, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    p = RESULTS / 'fig5_readout_window.png'
    fig.savefig(p); plt.close(fig)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', default='classification_quick.npz')
    ap.add_argument('--capacity', dest='cap', default=None)
    ap.add_argument('--t-ms', type=float, default=None,
                    help='które okno odczytu pokazać na mapach (domyślnie najkrótsze)')
    args = ap.parse_args()

    use_style()
    RESULTS.mkdir(exist_ok=True)
    figs = []

    d = load(args.inp)
    conds = [str(c) for c in d['conditions']]
    vals = ([f'acc_{c}' for c in conds] + [f'r_repr_{c}' for c in conds]
            + [f'sparse_{c}' for c in conds])

    # Starsze pliki NPZ nie mają osi T — dołóż ją, żeby analiza była wstecznie zgodna.
    if 'task_t_ms' not in d:
        d['task_t_ms'] = np.full(len(d['task_seed']), 600.0)
        d['grid_T_ms'] = np.array([600.0])

    Ts = sorted({float(x) for x in d['grid_T_ms']})
    t_ref = args.t_ms if (args.t_ms in Ts) else min(Ts)
    if len(Ts) > 1:
        print(f"Okna odczytu: {Ts} ms — mapy pokazują T = {t_ref:.0f} ms "
              f"(zmień przez --t-ms)")

    A3 = agg(d, ['task_r_in', 'task_noise', 'task_t_ms'], vals)
    A = {(r, n): rec for (r, n, T), rec in A3.items() if T == t_ref}

    summary_classification(A, d)
    figs += [fig_accuracy(A, d), fig_delta(A, d), fig_mechanism(A, d)]

    w = fig_window(d)
    if w:
        figs.append(w)

    if args.cap:
        dc = load(args.cap)
        figs.append(fig_capacity(dc))

    print("\nFigury:")
    for f in figs:
        print(f"  {f}")


if __name__ == '__main__':
    main()
