"""
E3 — figury podsumowujące do README (results/figures/summary/).

Zapis: figures/ (w repo; results/ jest w .gitignore).

  fig1_e31_accuracy_vs_f.png   dokładność i dekorelacja vs f (H-E3a)
  fig2_e32_phasic.png          dokładność vs hamowanie fazowe przy stałym f (H-E3b)
  fig3_e33_contrasts.png       różnice w zapominaniu parami (H-E3c, H-E3d, H-E3e)
  fig4_e33_conditions.png      zapominanie i dokładność każdego warunku (R-STDP)
  fig5_e34_code_vs_rule.png    kod × reguła czytnika (E3.4)
  fig6_regulator_trace.png     jak regulator reaguje na granice zadań

Zasady: jedna oś Y na panel (dwie miary → dwa panele), stała kolejność kolorów,
etykiety w kolorze tekstu, legenda przy ≥ 2 seriach.
"""
from __future__ import annotations

import glob
import json
import os

import matplotlib
import matplotlib.ticker
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
OUT = os.path.join(HERE, 'figures')   # śledzone w gicie (wyjątek w .gitignore) — README się do nich odwołuje

# paleta referencyjna (skill dataviz, tryb jasny), kolejność stała
BLUE, ORANGE, AQUA, YELLOW, MAGENTA = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4'
GREY, INK, INK2, SURF = '#8a8985', '#0b0b0b', '#52514e', '#fcfcfb'

plt.rcParams.update({
    'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF,
    'axes.edgecolor': '#c9c8c3', 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
    'text.color': INK, 'axes.titlecolor': INK, 'axes.titlesize': 11, 'axes.titleweight': 'bold',
    'axes.labelsize': 9.5, 'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5, 'legend.fontsize': 8.5,
    'axes.grid': True, 'grid.color': '#e6e5e1', 'grid.linewidth': 0.8,
    'axes.spines.top': False, 'axes.spines.right': False, 'lines.linewidth': 2.0,
    'legend.frameon': False, 'font.family': 'DejaVu Sans',
})
NEUR = {'izh': 'Izhikevich', 'lif': 'LIF'}


def load(pattern):
    return [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RES, pattern))) if '_quick' not in f]


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name), dpi=160, bbox_inches='tight')
    plt.close(fig)
    print('saved', name)


# ── Fig. 1 — E3.1 ────────────────────────────────────────────────────────────
def fig1():
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.4), sharex=True, gridspec_kw={'height_ratios': [2.2, 1]})
    for ci, n in enumerate(('izh', 'lif')):
        R = load(f'e31/{n}_s*_o0.json')

        def curve(code, key):
            rows = []
            for r in R:
                rec = sorted([x for x in r['records'] if x['code'] == code], key=lambda x: x['level'])
                rows.append([x[key] for x in rec])
            return np.array(rows)
        F = curve('dg', 'f_train').mean(0)
        ax = axes[0, ci]
        series = [('dg', 'acc_rstdp', BLUE, '-', 'DG, czytnik R-STDP'),
                  ('dg', 'acc_delta', ORANGE, '-', 'DG, czytnik delta'),
                  ('random_projection', 'acc_rstdp', AQUA, '-', 'losowa projekcja, R-STDP'),
                  ('dg', 'acc_logistic', GREY, '--', 'DG, regresja logistyczna (sufit)')]
        for code, key, col, ls, lab in series:
            A = curve(code, key)
            ax.plot(F, A.mean(0), color=col, ls=ls, marker='o', ms=4, label=lab)
            ax.fill_between(F, A.mean(0) - A.std(0), A.mean(0) + A.std(0), color=col, alpha=0.12, lw=0)
        A = curve('dg', 'acc_rstdp').mean(0)
        k = int(np.argmax(A))
        ax.annotate(f'maksimum R-STDP\nf = {F[k]:.0%}', (F[k], A[k]), xytext=(F[k] * 1.25, 0.62),
                    fontsize=8, color=INK2, arrowprops=dict(arrowstyle='-', color=INK2, lw=0.8))
        ax.set_ylim(0.55, 0.97)
        ax.set_title(NEUR[n])
        ax.set_ylabel('dokładność (test, 1 epoka)' if ci == 0 else '')
        D = curve('dg', 'dec')
        axes[1, ci].plot(F, D.mean(0), color=MAGENTA, marker='s', ms=4)
        axes[1, ci].set_ylabel('dekorelacja dec\n= r_in − r_out' if ci == 0 else '')
        axes[1, ci].set_xscale('log')
        axes[1, ci].set_xlabel('odsetek aktywnych neuronów DG, f')
        axes[1, ci].set_xticks([0.01, 0.03, 0.1, 0.3, 0.5])
        axes[1, ci].set_xticklabels(['1%', '3%', '10%', '30%', '50%'])
    axes[0, 0].legend(loc='lower center', ncol=1)
    fig.suptitle('E3.1 · Optimum rzadkości dla uczenia istnieje, dekorelacja go nie widzi (H-E3a ✓)',
                 x=0.01, y=1.0, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, 0.945, 'Średnia ± SD po 5 sieciach. Dekorelacja rośnie monotonicznie, gdy kod rzednie; '
             'dokładność ma maksimum przy f ≈ 10–25%.', fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, 'fig1_e31_accuracy_vs_f.png')


# ── Fig. 2 — E3.2 ────────────────────────────────────────────────────────────
def fig2():
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ci, n in enumerate(('izh', 'lif')):
        R = load(f'e32/{n}_s*_o0.json')
        ax = axes[ci]
        for rule, ls, rl in (('rstdp', '-', 'R-STDP'), ('delta', '--', 'delta')):
            for f, col in ((0.05, BLUE), (0.20, ORANGE)):
                Ws = [0, 1, 2, 3, 5]
                M = [[x[f'acc_{rule}'] for r in R for x in r['records'] if x['W_FS_GC'] == W and abs(x['f_target'] - f) < 1e-9] for W in Ws]
                mu, sd = np.array([np.mean(m) for m in M]), np.array([np.std(m) for m in M])
                ax.errorbar(Ws, mu, sd, color=col, ls=ls, marker='o', ms=4, capsize=2, label=f'f = {f:.0%}, {rl}')
        ax.set_title(NEUR[n])
        ax.set_xlabel('siła hamowania fazowego W_FS_GC (K dobrane tak, by f było stałe)')
        ax.set_xticks([0, 1, 2, 3, 5])
    axes[0].set_ylabel('dokładność (test)')
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=BLUE, lw=2, label='f = 5%'), Line2D([], [], color=ORANGE, lw=2, label='f = 20%'),
         Line2D([], [], color=INK2, lw=2, ls='-', label='czytnik R-STDP'), Line2D([], [], color=INK2, lw=2, ls='--', label='czytnik delta')]
    axes[0].legend(handles=h, loc='lower left', ncol=2)
    fig.suptitle('E3.2 · Hamowanie fazowe przy stałym f obniża dokładność (H-E3b ✗)',
                 x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, 'fig2_e32_phasic.png')


# ── Fig. 3 — E3.3, kontrasty parami ─────────────────────────────────────────
def _e33_runs():
    out = {}
    for r in load('e33/*.json'):
        key = (r['neuron'], r['rule'])
        phase = 'główny (sieci 0–4)' if r['seed'] < 5 else 'potwierdzający (sieci 5–9)'
        out.setdefault(key, {}).setdefault(phase, []).append({x['condition']: x for x in r['results']})
    return out


def fig3():
    runs = _e33_runs()
    contrasts = [('mod_novelty', 'fixed_matched', 'H-E3c: nowość → RZADZIEJ\nvs stałe f o tej samej średniej'),
                 ('mod_novelty', '3f_lr', 'H-E3d: nowość → rzadkość\nvs nowość → tempo uczenia'),
                 ('mod_novelty_inv', 'fixed_matched_inv', 'H-E3e: nowość → GĘŚCIEJ\nvs stałe f o tej samej średniej')]
    combos = [('izh', 'rstdp'), ('lif', 'rstdp'), ('izh', 'delta'), ('lif', 'delta')]
    phases = ['główny (sieci 0–4)', 'potwierdzający (sieci 5–9)']
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.6), sharey=True)
    for ai, (a, b, title) in enumerate(contrasts):
        ax = axes[ai]
        ax.axvline(0, color=INK2, lw=1)
        for yi, (n, rule) in enumerate(combos):
            for pi, ph in enumerate(phases):
                rr = runs.get((n, rule), {}).get(ph, [])
                d = np.array([v[a]['BWT'] - v[b]['BWT'] for v in rr if a in v and b in v])
                if not len(d):
                    continue
                y = yi + (pi - 0.5) * 0.32
                col = BLUE if pi == 0 else ORANGE
                ax.scatter(d, np.full(len(d), y) + np.random.default_rng(yi * 10 + pi).uniform(-0.07, 0.07, len(d)),
                           s=12, color=col, alpha=0.55, lw=0)
                ax.plot([d.mean()], [y], marker='D', ms=7, color=col, mec=SURF, mew=1.2,
                        label=ph if (ai == 0 and yi == 0) else None)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('różnica zapominania ΔBWT\n(> 0 = pierwszy warunek zapomina MNIEJ)')
        ax.grid(axis='y', visible=False)
    axes[0].set_yticks(range(len(combos)))
    axes[0].set_yticklabels([f'{NEUR[n]} × {"R-STDP" if r == "rstdp" else "delta"}' for n, r in combos])
    axes[0].invert_yaxis()
    axes[0].legend(loc='lower left', title='przebieg', title_fontsize=8.5)
    fig.suptitle('E3.3 · Sterowanie rzadkością nowością: kierunek „rzadziej” szkodzi, „gęściej” pomaga, ale nie wszędzie',
                 x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, 0.90, 'Punkty: pojedyncze przebiegi (sieć × kolejność zadań), romby: średnie. '
             'H-E3e: kryterium (oba R-STDP w przebiegu potwierdzającym) niespełnione — Izhikevich × R-STDP p = 0.28.',
             fontsize=8.8, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    save(fig, 'fig3_e33_contrasts.png')


# ── Fig. 4 — E3.3, wszystkie warunki (R-STDP) ───────────────────────────────
def fig4():
    runs = _e33_runs()
    conds = [('kwta_fly', 'FlyModel (k-WTA 5%, własna reguła)'), ('mod_novelty_inv', 'nowość → gęściej'),
             ('fixed_sparse', 'stałe f rzadkie'), ('fixed_matched_inv', 'stałe f = średnia „gęściej”'),
             ('fixed_matched', 'stałe f = średnia „rzadziej”'), ('oracle_boundary', 'rzadziej na granicy (wyrocznia)'),
             ('fixed_dense', 'stałe f gęste'), ('3f_lr', 'nowość → tempo uczenia'),
             ('mod_novelty', 'nowość → rzadziej'), ('3f_both', 'nowość → rzadziej + tempo')]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for mi, metric in enumerate(('BWT', 'ACC')):
        ax = axes[mi]
        for ni, (n, col) in enumerate((('izh', BLUE), ('lif', ORANGE))):
            allr = [v for ph in runs.get((n, 'rstdp'), {}).values() for v in ph]
            for ci, (c, _) in enumerate(conds):
                vals = [v[c][metric] for v in allr if c in v]
                if vals:
                    y = ci + (ni - 0.5) * 0.3
                    ax.errorbar(np.mean(vals), y, xerr=np.std(vals), fmt='o', ms=6, color=col, capsize=2,
                                label=NEUR[n] if ci == 0 else None)
        ax.set_xlabel('zapominanie BWT (bliżej 0 = lepiej)' if metric == 'BWT' else 'końcowa dokładność ACC (10 klas)')
        ax.grid(axis='y', visible=False)
    axes[0].set_yticks(range(len(conds)))
    axes[0].set_yticklabels([l for _, l in conds])
    axes[0].invert_yaxis()
    fig.legend(*axes[0].get_legend_handles_labels(), loc='upper right', ncol=2, bbox_to_anchor=(0.99, 0.95))
    fig.suptitle('E3.3 · Split-MNIST, czytnik R-STDP: wszystkie warunki (średnia ± SD, 20 przebiegów)',
                 x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, 'fig4_e33_conditions.png')


# ── Fig. 5 — E3.4 ────────────────────────────────────────────────────────────
def fig5():
    R = load('e34/*.json')
    rules = [('fly', 'reguła FlyModel\n(tylko klasa docelowa)'), ('rstdp', 'R-STDP\n(R − R̄)'), ('delta', 'delta')]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.2), sharex=True)
    for ni, n in enumerate(('izh', 'lif')):
        rs = [r for r in R if r['neuron'] == n]
        for mi, metric in enumerate(('ACC', 'BWT')):
            ax = axes[mi, ni]
            for ci, (code, col, lab) in enumerate((('kwta', BLUE, 'k-WTA (FlyModel)'), ('dg5', ORANGE, 'DG, impulsy (globalny próg)'),
                                                   ('dg5n', AQUA, 'DG, znormalizowany per obraz'))):
                mu, sd = [], []
                for rule, _ in rules:
                    v = [x[metric] for r in rs for x in r['results'] if x['code'] == code and x['rule'] == rule]
                    mu.append(np.mean(v))
                    sd.append(np.std(v))
                if not np.isfinite(mu).all():
                    continue
                xs = np.arange(3) + (ci - 1) * 0.27
                ax.bar(xs, mu, 0.25, yerr=sd, color=col, capsize=2, label=lab, edgecolor=SURF, linewidth=1)
            ax.axhline(0, color=INK2, lw=0.8)
            ax.set_ylabel(('końcowa dokładność ACC' if metric == 'ACC' else 'zapominanie BWT') if ni == 0 else '')
            if mi == 0:
                ax.set_title(NEUR[n])
            ax.set_xticks(range(3))
            ax.set_xticklabels([l for _, l in rules])
            ax.grid(axis='x', visible=False)
    axes[0, 0].legend(loc='upper right')
    fig.suptitle('E3.4 · O zapominaniu decyduje reguła czytnika, nie kod (f = 5%, 20 przebiegów na neuron)',
                 x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, 0.925, 'Reguła FlyModelu na kodzie DG prawie się nie uczy (ACC ≈ 0.2): liczba aktywnych neuronów '
             'na obraz waha się 18–242, a reguła wymaga stałej (k-WTA: zawsze 100).', fontsize=8.8, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    save(fig, 'fig5_e34_code_vs_rule.png')


# ── Fig. 6 — przebieg regulatora ────────────────────────────────────────────
def fig6():
    import sys
    sys.path.insert(0, HERE)
    from tasks import load_mnist, task_stream
    _, ytr, _, _ = load_mnist(normalize=False)
    r = json.load(open(os.path.join(RES, 'e33', 'izh_rstdp_s0_o0.json')))
    st = task_stream(ytr, 1000 * r['seed'] + r['order_seed'])
    bounds = np.cumsum([0] + [len(s) for _, s in st])
    mod = [x for x in r['results'] if x['condition'] == 'mod_novelty'][0]['trace']
    inv = [x for x in r['results'] if x['condition'] == 'mod_novelty_inv'][0]['trace']
    x = np.arange(len(mod['n'])) * 50
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 4.6), sharex=True, gridspec_kw={'height_ratios': [1, 1.3]})
    axes[0].plot(x, mod['n'], color=INK2, lw=1)
    axes[0].set_ylabel('nowość n\n(wygładzona)')
    axes[1].plot(x, mod['level_f'], color=BLUE, lw=1.4, label='nowość → rzadziej (mod_novelty)')
    axes[1].plot(x, inv['level_f'], color=ORANGE, lw=1.4, label='nowość → gęściej (mod_novelty_inv)')
    axes[1].set_yscale('log')
    axes[1].set_yticks([0.03, 0.05, 0.1])
    axes[1].set_yticklabels(['3%', '5%', '10%'])
    axes[1].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axes[1].set_ylabel('f wybrane\nprzez regulator')
    axes[1].set_xlabel('obraz treningowy')
    axes[1].legend(loc='upper center', ncol=2, bbox_to_anchor=(0.5, -0.32))
    for ax in axes:
        for b in bounds[1:-1]:
            ax.axvline(b, color=GREY, lw=0.8, ls=':')
    for k, (t, _) in enumerate(st):
        axes[0].text((bounds[k] + bounds[k + 1]) / 2, 1.04, f'{2 * k}/{2 * k + 1}', ha='center', fontsize=8.5,
                     color=INK2, transform=axes[0].get_xaxis_transform())
    fig.suptitle('Regulator K reaguje na każdą granicę zadania (Izhikevich × R-STDP, sieć 0, przebieg główny)',
                 x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, 'fig6_regulator_trace.png')


# ── Fig. 7 — E3.5, dawka–odpowiedź ──────────────────────────────────────────
def fig7():
    R = load('e35/*.json')
    if not R:
        return
    archs = [(500, 30), (1000, 30), (2000, 30), (5000, 30), (2000, 10), (2000, 100)]
    cols = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, '#6250d6']
    gains = [-1.0, -0.5, 0.0, 0.5, 1.0]
    rules = [('rstdp', 'czytnik R-STDP (R − R̄)'), ('delta', 'czytnik delta'), ('rgate', 'czytnik bez osłabiania (rgate)')]
    fig, axes = plt.subplots(3, 2, figsize=(10.5, 9.5), sharex=True)
    for ri, (rule, rl) in enumerate(rules):
        for ni, n in enumerate(('izh', 'lif')):
            ax = axes[ri, ni]
            ax.axhline(0, color=INK2, lw=1)
            ax.axvline(0, color=GREY, lw=0.8, ls=':')
            for (N, k), col in zip(archs, cols):
                rs = [r for r in R if r['neuron'] == n and r['rule'] == rule and r['n_dg'] == N and r['fan_in'] == k]
                if not rs:
                    continue
                mu, sd = [], []
                for g in gains:
                    if g == 0:
                        mu.append(0.0)
                        sd.append(0.0)
                        continue
                    d = [[x for x in r['results'] if x['g'] == g and x['kind'] == 'mod'][0]['BWT']
                         - [x for x in r['results'] if x['g'] == g and x['kind'] == 'matched'][0]['BWT'] for r in rs]
                    mu.append(np.mean(d))
                    sd.append(np.std(d) / np.sqrt(len(d)))
                ax.errorbar(gains, mu, sd, color=col, marker='o', ms=4, capsize=2, lw=1.6,
                            label=f'N = {N}, fan-in {k}')
            if ri == 0:
                ax.set_title(NEUR[n])
            if ni == 0:
                ax.set_ylabel(f'{rl}\nΔ zapominania vs stałe f')
            if ri == 2:
                ax.set_xlabel('siła modulacji g  (− : nowość → gęściej,  + : nowość → rzadziej)')
            ax.set_xticks(gains)
    axes[0, 0].legend(loc='lower left', fontsize=7.5, ncol=2)
    fig.suptitle('E3.5 · Czy „nowość → rzadziej” zawsze zapomina więcej? Krzywa dawka–odpowiedź w 6 architekturach',
                 x=0.01, y=1.0, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, 0.965, 'Δ > 0: modulacja zapomina mniej niż stały kod o tej samej średniej rzadkości. '
             'Średnia ± błąd standardowy po przebiegach (sieć × kolejność).', fontsize=8.8, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    save(fig, 'fig7_e35_dose_response.png')


# ── Fig. 8 — E3.6, zadanie separacji wzorców (dg_core) ──────────────────────
def fig8(sub='e36', name='fig8_e36_dgcore_task.png',
         title='E3.6 · Zadanie separacji wzorców (dg_core, 200 GC): sterowanie K_GC nowością'):
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RES, sub, 'learn_*.json')))]
    if not R:
        return
    gains = [-1.0, -0.5, 0.0, 0.5, 1.0]
    rules = [('rstdp', 'R-STDP'), ('delta', 'delta'), ('rgate', 'rgate (bez osłabiania)')]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.9), sharey=True)
    for ri, (rule, rl) in enumerate(rules):
        ax = axes[ri]
        ax.axhline(0, color=INK2, lw=1)
        for rin, col in ((0.5, BLUE), (0.75, ORANGE), (0.9, AQUA)):
            rs = [r for r in R if r['rule'] == rule and abs(r['r_in'] - rin) < 1e-9]
            if not rs:
                continue
            mu, se = [], []
            for g in gains:
                if g == 0:
                    mu.append(0.0)
                    se.append(0.0)
                    continue
                d = [[x for x in r['results'] if x['g'] == g and x['kind'] == 'mod'][0]['BWT']
                     - [x for x in r['results'] if x['g'] == g and x['kind'] == 'matched'][0]['BWT'] for r in rs]
                mu.append(np.mean(d))
                se.append(np.std(d) / np.sqrt(len(d)))
            ax.errorbar(gains, mu, se, color=col, marker='o', ms=4, capsize=2, lw=1.6, label=f'R_in = {rin}')
        ax.set_title(f'czytnik {rl}')
        ax.set_xticks(gains)
        ax.set_xlabel('siła modulacji g (+ : nowość → rzadziej)')
    axes[0].set_ylabel('Δ zapominania vs stałe f\n(> 0 = modulacja zapomina mniej)')
    axes[0].legend(loc='lower left')
    fig.suptitle(title, x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, name)


def fig9():
    fig8('e36x', 'fig9_e36x_dgcore_exvivo.png',
         'E3.6x · To samo zadanie na modelu skalibrowanym do skrawka (salwy, dane Madara)')


# ── Fig. 10 — E3.8, mechanizm ───────────────────────────────────────────────
def fig10():
    R = load('e38/*.json')
    if not R:
        return
    lams = ['0.0', '0.25', '0.5', '0.75', '1.0']
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.9))
    ax = axes[0]
    ax.axhline(0, color=INK2, lw=1)
    for n, col in (('izh', BLUE), ('lif', ORANGE)):
        rs = [r for r in R if r['neuron'] == n]
        mu, se = [], []
        for l in lams:
            d = [r['B'][l]['mod']['BWT'] - r['B'][l]['matched_mod']['BWT'] for r in rs]
            mu.append(np.mean(d))
            se.append(np.std(d) / np.sqrt(len(d)))
        ax.errorbar([float(x) for x in lams], mu, se, color=col, marker='o', ms=4, capsize=2, label=NEUR[n])
    ax.set_xlabel('udział osłabiania w regule λ (0 = rgate, 1 = pełne)')
    ax.set_ylabel('Δ zapominania „nowość → rzadziej”\nvs stałe f (> 0 = pomaga)')
    ax.set_title('Znak efektu a osłabianie wag', fontsize=10)
    ax.legend()
    ax = axes[1]
    ax.axhline(0, color=INK2, lw=1)
    rules = [('rstdp', 'R-STDP'), ('rstdp_raw', 'R-STDP\nbez norm.'), ('delta', 'delta'), ('delta_raw', 'delta\nbez norm.')]
    for ni, (n, col) in enumerate((('izh', BLUE), ('lif', ORANGE))):
        rs = [r for r in R if r['neuron'] == n]
        for ri, (rule, _) in enumerate(rules):
            d = [r['A'][rule]['inv']['BWT'] - r['A'][rule]['matched_inv']['BWT'] for r in rs]
            ax.bar(ri + (ni - 0.5) * 0.38, np.mean(d), 0.36, yerr=np.std(d) / np.sqrt(len(d)), color=col, capsize=2,
                   edgecolor=SURF, label=NEUR[n] if ri == 0 else None)
    ax.set_xticks(range(len(rules)))
    ax.set_xticklabels([l for _, l in rules], fontsize=8)
    ax.set_ylabel('Δ zapominania „nowość → gęściej”\nvs stałe f')
    ax.set_title('Rola normalizacji (rozcieńczania)', fontsize=10)
    ax.grid(axis='x', visible=False)
    ax = axes[2]
    for ni, (n, col) in enumerate((('izh', BLUE), ('lif', ORANGE))):
        rs = [r for r in R if r['neuron'] == n]
        for ri, rule in enumerate(('rstdp', 'delta')):
            for ci, c in enumerate(('inv', 'matched_inv_evalrest')):
                v = [r['A'][rule][c]['damage_frac_novel'] for r in rs]
                x = ri * 2.4 + ci + (ni - 0.5) * 0.38
                ax.bar(x, np.mean(v), 0.36, yerr=np.std(v) / np.sqrt(len(v)), color=col, alpha=1.0 if ci == 0 else 0.45,
                       capsize=2, edgecolor=SURF)
    ax.set_xticks([0, 1, 2.4, 3.4])
    ax.set_xticklabels(['R-STDP\nnowość→gęściej', 'R-STDP\nstałe f', 'delta\nnowość→gęściej', 'delta\nstałe f'], fontsize=8)
    ax.set_ylabel('część zmian wag trafiająca w stare klasy\n(okna nowości)')
    ax.set_title('„Szkoda” na starcie nowego zadania', fontsize=10)
    ax.grid(axis='x', visible=False)
    fig.suptitle('E3.8 · Mechanizm: dlaczego kierunek modulacji zależy od reguły uczenia',
                 x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, 'fig10_e38_mechanism.png')


# ── Fig. 11 — E3.7, warstwa ukryta ──────────────────────────────────────────
def fig11():
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RES, 'e37', 'run_*.json')))]
    if not R:
        return
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ai, g in enumerate((1.0, -1.0)):
        ax = axes[ai]
        ax.axvline(0, color=INK2, lw=1)
        rows = [('agrel', 'izh'), ('agrel', 'lif'), ('agrel_pos', 'izh'), ('agrel_pos', 'lif')]
        for yi, (v, n) in enumerate(rows):
            rs = [r for r in R if r['variant'] == v and r['neuron'] == n]
            if not rs:
                continue
            d = np.array([[x for x in r['results'] if x['g'] == g and x['kind'] == 'mod'][0]['BWT']
                          - [x for x in r['results'] if x['g'] == g and x['kind'] == 'matched'][0]['BWT'] for r in rs])
            col = ORANGE if v == 'agrel' else BLUE
            ax.scatter(d, np.full(len(d), yi) + np.random.default_rng(yi).uniform(-0.12, 0.12, len(d)), s=12, color=col, alpha=0.5, lw=0)
            ax.plot([d.mean()], [yi], marker='D', ms=7, color=col, mec=SURF)
        ax.set_yticks(range(4))
        ax.set_yticklabels(['z osłabianiem · Izhikevich', 'z osłabianiem · LIF', 'bez osłabiania · Izhikevich', 'bez osłabiania · LIF'])
        ax.set_title('nowość → rzadziej (g = +1)' if g > 0 else 'nowość → gęściej (g = −1)', fontsize=10)
        ax.set_xlabel('Δ zapominania vs stałe f (> 0 = pomaga)')
        ax.grid(axis='y', visible=False)
    axes[0].invert_yaxis()
    fig.suptitle('E3.7 · Sieć z warstwą ukrytą uczoną trójczynnikowo (AGREL)',
                 x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, 'fig11_e37_hidden_layer.png')


if __name__ == '__main__':
    for fn in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11):
        fn()
