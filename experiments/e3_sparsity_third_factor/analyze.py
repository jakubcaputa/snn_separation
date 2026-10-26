"""
E3 — analiza: łączy wyniki E3.1, E3.2, E3.3, liczy kryteria zapisane w README sek. 6
i rysuje figury. Wyjście: results/summary.json, results/figures/*.png.

Kryteria (ustalone przed uruchomieniem pełnych przebiegów):
  H-E3a  maksimum dokładności (kod DG) w punkcie WEWNĘTRZNYM siatki f w ≥ 4/5 ziaren,
         osobno dla każdego czytnika i typu neuronu; dodatkowo: dec maleje z f
         (ujemna korelacja Spearmana f–dec) — „dekorelacja rośnie do ciszy”.
  H-E3b  brak zależności dokładności od W_FS_GC: nachylenie OLS (punkty ze wszystkich
         ziaren) nieistotne po korekcie Bonferroniego (2 poziomy f × 2 czytniki).
  H-E3c  BWT(mod_novelty) − BWT(fixed_matched) > 0, Wilcoxon (parowany po ziarnach)
         p < 0.05 i ten sam znak w ≥ 8/10 ziaren.
  H-E3d  BWT(mod_novelty) − BWT(3f_lr) > 0, to samo kryterium.
"""
from __future__ import annotations

import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
FIG = os.path.join(RES, 'figures')
OKABE = ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#000000']


def _load(pattern):
    out = []
    for fn in sorted(glob.glob(os.path.join(RES, pattern))):
        if '_quick' in fn:
            continue
        with open(fn) as f:
            out.append(json.load(f))
    return out


def analyze_e31(plt):
    runs = _load('e31/*.json')
    summary = {}
    for neuron in ('izh', 'lif'):
        rs = [r for r in runs if r['neuron'] == neuron]
        if not rs:
            continue
        s = {}
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        for ai, rule in enumerate(('rstdp', 'delta')):
            interior, spear = [], []
            curves = []
            for r in rs:
                dg = sorted([x for x in r['records'] if x['code'] == 'dg'], key=lambda x: x['level'])
                f = np.array([x['f_train'] for x in dg])
                acc = np.array([x[f'acc_{rule}'] for x in dg])
                dec = np.array([x['dec'] for x in dg])
                k = int(np.argmax(acc))
                interior.append(0 < k < len(acc) - 1)
                spear.append(stats.spearmanr(f, dec).correlation)
                curves.append((f, acc, dec, r))
            s[rule] = {'interior_max_seeds': int(sum(interior)), 'n_seeds': len(interior),
                       'H_E3a_pass': bool(sum(interior) >= max(4, int(0.8 * len(interior)))),
                       'spearman_f_dec_mean': float(np.mean(spear)),
                       'f_at_max_acc': [float(c[0][int(np.argmax(c[1]))]) for c in curves],
                       'max_acc': [float(np.max(c[1])) for c in curves]}
            ax = axes[ai]
            F = np.mean([c[0] for c in curves], 0)
            for key, col, lab in (('dg', OKABE[4], 'DG (impulsy)'),
                                  ('random_projection', OKABE[0], 'losowa projekcja')):
                A = np.array([[x[f'acc_{rule}'] for x in sorted([y for y in c[3]['records'] if y['code'] == key],
                                                                key=lambda y: y['level'])] for c in curves])
                ax.errorbar(F, A.mean(0), A.std(0), color=col, marker='o', ms=3, label=f'{lab} — {rule}')
            L = np.array([[x['acc_logistic'] for x in sorted([y for y in c[3]['records'] if y['code'] == 'dg'],
                                                             key=lambda y: y['level'])] for c in curves])
            ax.plot(F, L.mean(0), color=OKABE[7], ls='--', label='DG — regresja logistyczna (sufit)')
            pix = [x for x in curves[0][3]['records'] if x['code'] == 'pixels'][0]
            ax.axhline(pix[f'acc_{rule}'], color='grey', ls=':', label=f'piksele — {rule}')
            ax.set_xscale('log')
            ax.set_xlabel('odsetek aktywnych neuronów DG, f')
            ax.set_ylabel('dokładność (test)')
            ax2 = ax.twinx()
            D = np.array([c[2] for c in curves])
            ax2.plot(F, D.mean(0), color=OKABE[5], marker='s', ms=3)
            ax2.set_ylabel('dec = r_in − r_out', color=OKABE[5])
            ax.set_title(f'{neuron.upper()} · czytnik {rule}')
            ax.legend(fontsize=7, loc='lower center')
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, f'e31_{neuron}.png'), dpi=150)
        plt.close(fig)
        summary[neuron] = s
    return summary


def analyze_e32(plt):
    runs = _load('e32/*.json')
    summary = {}
    for neuron in ('izh', 'lif'):
        rs = [r for r in runs if r['neuron'] == neuron]
        if not rs:
            continue
        s = {}
        n_tests = 4
        fig, ax = plt.subplots(figsize=(6, 4))
        for ci, rule in enumerate(('rstdp', 'delta')):
            for fi, f in enumerate((0.05, 0.20)):
                W, A = [], []
                for r in rs:
                    for x in r['records']:
                        if abs(x['f_target'] - f) < 1e-9:
                            W.append(x['W_FS_GC'])
                            A.append(x[f'acc_{rule}'])
                res = stats.linregress(W, A)
                s[f'{rule}_f{f}'] = {'slope': float(res.slope), 'p': float(res.pvalue),
                                     'significant_bonferroni': bool(res.pvalue < 0.05 / n_tests)}
                Wu = sorted(set(W))
                means = [np.mean([a for w, a in zip(W, A) if w == u]) for u in Wu]
                ax.plot(Wu, means, marker='o', color=OKABE[ci * 2 + fi], label=f'{rule}, f={f:.0%}')
        s['H_E3b_pass'] = not any(v['significant_bonferroni'] for k, v in s.items() if isinstance(v, dict))
        ax.set_xlabel('hamowanie fazowe W_FS_GC (przy stałym f)')
        ax.set_ylabel('dokładność (test)')
        ax.set_title(f'E3.2 · {neuron.upper()}')
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, f'e32_{neuron}.png'), dpi=150)
        plt.close(fig)
        summary[neuron] = s
    return summary


def _contrast(by_seed, a, b, metric='BWT'):
    d = np.array([v[a][metric] - v[b][metric] for v in by_seed.values() if a in v and b in v])
    if len(d) < 2:
        return {'n': int(len(d))}
    try:
        p = float(stats.wilcoxon(d).pvalue)
    except ValueError:
        p = 1.0
    same_sign = int((d > 0).sum())
    return {'n': int(len(d)), 'mean_diff': float(d.mean()), 'sd_diff': float(d.std(ddof=1)),
            'p_wilcoxon': p, 'n_positive': same_sign,
            'pass': bool(d.mean() > 0 and p < 0.05 and same_sign >= int(np.ceil(0.8 * len(d))))}


def analyze_e33(plt):
    runs = _load('e33/*.json')
    summary = {}
    groups = defaultdict(dict)
    for r in runs:
        # sieci 0–4 = przebieg główny; 5–9 = test potwierdzający H-E3e (nowe sieci)
        phase = 'main' if r['seed'] < 5 else 'confirm'
        key = f"{phase}_{r['neuron']}_{r['rule']}"
        groups[key][(r['seed'], r['order_seed'])] = {x['condition']: x for x in r['results']}
    conds = ['fixed_dense', 'fixed_sparse', 'mod_novelty', 'fixed_matched', '3f_lr', '3f_both',
             'mod_novelty_inv', 'fixed_matched_inv', 'oracle_boundary', 'kwta_fly']
    for key, by_seed in groups.items():
        s = {'n_runs': len(by_seed), 'conditions': {}}
        for c in conds:
            vals = [v[c] for v in by_seed.values() if c in v]
            if vals:
                s['conditions'][c] = {m: [float(np.mean([x[m] for x in vals])), float(np.std([x[m] for x in vals]))]
                                      for m in ('ACC', 'BWT', 'mean_level_f')}
        s['H_E3c'] = _contrast(by_seed, 'mod_novelty', 'fixed_matched')
        s['H_E3d'] = _contrast(by_seed, 'mod_novelty', '3f_lr')
        s['inv_vs_matched'] = _contrast(by_seed, 'mod_novelty_inv', 'fixed_matched')
        s['H_E3e_inv_vs_matched_inv'] = _contrast(by_seed, 'mod_novelty_inv', 'fixed_matched_inv')
        s['ACC_mod_vs_matched'] = _contrast(by_seed, 'mod_novelty', 'fixed_matched', 'ACC')
        summary[key] = s
        # figura: ACC i BWT per warunek
        present = [c for c in conds if c in s['conditions']]
        fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
        for ax, m in zip(axes, ('ACC', 'BWT')):
            mu = [s['conditions'][c][m][0] for c in present]
            sd = [s['conditions'][c][m][1] for c in present]
            cols = [OKABE[5] if c == 'mod_novelty' else OKABE[4] if c == 'fixed_matched' else 'grey' for c in present]
            ax.bar(range(len(present)), mu, yerr=sd, color=cols)
            ax.set_xticks(range(len(present)))
            ax.set_xticklabels(present, rotation=40, ha='right', fontsize=8)
            ax.set_ylabel(m)
        axes[0].set_title(f'E3.3 · {key} · {len(by_seed)} przebiegów')
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, f'e33_{key}.png'), dpi=150)
        plt.close(fig)
        # przebieg regulatora (pierwszy przebieg)
        first = next(iter(by_seed.values()))
        if 'trace' in first.get('mod_novelty', {}):
            tr = first['mod_novelty']['trace']
            fig, ax = plt.subplots(figsize=(9, 3))
            x = np.arange(len(tr['f'])) * 50
            ax.plot(x, tr['level_f'], color=OKABE[5], lw=1, label='f wybrane przez regulator')
            ax.set_yscale('log')
            ax.set_xlabel('obraz treningowy (zadania 0/1 → 8/9)')
            ax.set_ylabel('f')
            ax2 = ax.twinx()
            ax2.plot(x, tr['n'], color=OKABE[1], lw=0.8, alpha=0.7)
            ax2.set_ylabel('nowość n', color=OKABE[1])
            ax.set_title(f'Regulator K · {key}')
            fig.tight_layout()
            fig.savefig(os.path.join(FIG, f'e33_trace_{key}.png'), dpi=150)
            plt.close(fig)
    return summary


def analyze_e34(plt):
    """E3.4 (eksploracyjnie): kod {kwta, dg5} × reguła {fly, rstdp, delta}, f = 5%.
    Kontrasty parowane po przebiegach (10 sieci × 2 kolejności): efekt reguły przy
    stałym kodzie i efekt kodu przy stałej regule."""
    runs = _load('e34/*.json')
    summary = {}
    for neuron in ('izh', 'lif'):
        rs = [r for r in runs if r['neuron'] == neuron]
        if not rs:
            continue
        cell = defaultdict(list)
        by_run = {}
        for r in rs:
            d = {(x['code'], x['rule']): x for x in r['results']}
            by_run[(r['seed'], r['order_seed'])] = d
            for k, x in d.items():
                cell[k].append(x)
        s = {'n_runs': len(rs), 'cells': {f'{c}_{ru}': {m: [float(np.mean([x[m] for x in v])), float(np.std([x[m] for x in v]))]
                                                        for m in ('ACC', 'BWT')} for (c, ru), v in cell.items()}}

        def contrast(a, b, metric='BWT'):
            d = np.array([v[a][metric] - v[b][metric] for v in by_run.values() if a in v and b in v])
            try:
                p = float(stats.wilcoxon(d).pvalue)
            except ValueError:
                p = 1.0
            return {'n': int(len(d)), 'mean_diff': float(d.mean()), 'n_positive': int((d > 0).sum()), 'p_wilcoxon': p}
        s['rule_effect_fly_minus_rstdp'] = {c: contrast((c, 'fly'), (c, 'rstdp')) for c in ('kwta', 'dg5', 'dg5n')}
        s['rule_effect_fly_minus_delta'] = {c: contrast((c, 'fly'), (c, 'delta')) for c in ('kwta', 'dg5', 'dg5n')}
        s['code_effect_kwta_minus_dg5'] = {ru: contrast(('kwta', ru), ('dg5', ru)) for ru in ('fly', 'rstdp', 'delta')}
        s['code_effect_dg5n_minus_dg5'] = {ru: contrast(('dg5n', ru), ('dg5', ru)) for ru in ('fly', 'rstdp', 'delta')}
        s['code_effect_kwta_minus_dg5n'] = {ru: contrast(('kwta', ru), ('dg5n', ru)) for ru in ('fly', 'rstdp', 'delta')}
        summary[neuron] = s
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
        for ax, m in zip(axes, ('ACC', 'BWT')):
            for ci, code in enumerate(('kwta', 'dg5', 'dg5n')):
                if f'{code}_fly' not in s['cells']:
                    continue
                mu = [s['cells'][f'{code}_{ru}'][m][0] for ru in ('fly', 'rstdp', 'delta')]
                sd = [s['cells'][f'{code}_{ru}'][m][1] for ru in ('fly', 'rstdp', 'delta')]
                ax.bar(np.arange(3) + 0.26 * ci, mu, 0.24, yerr=sd, color=OKABE[[4, 0, 2][ci]],
                       label=['k-WTA (FlyModel)', 'DG, impulsy', 'DG, znormalizowany per obraz'][ci])
            ax.set_xticks(np.arange(3) + 0.19)
            ax.set_xticklabels(['reguła FlyModel', 'R-STDP (R − R̄)', 'delta'])
            ax.set_ylabel(m)
        axes[0].legend(fontsize=8)
        axes[0].set_title(f'E3.4 · {neuron.upper()} · f = 5%')
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, f'e34_{neuron}.png'), dpi=150)
        plt.close(fig)
    return summary


def analyze_e35():
    """E3.5 — kryteria z README sek. 6b. Efekt Δ(g) = BWT(mod g) − BWT(stałe f g)."""
    runs = _load('e35/*.json')
    cells = defaultdict(list)
    for r in runs:
        cells[(r['n_dg'], r['fan_in'], r['neuron'], r['rule'])].append(r)
    out = {'cells': {}}
    neg, sig_pos, tot = 0, 0, 0
    neg_rg, sig_pos_rg, tot_rg = 0, 0, 0
    mono = 0
    for (N, k, n, rule), rs in sorted(cells.items()):
        c = {'n_runs': len(rs)}
        for g in (-1.0, -0.5, 0.5, 1.0):
            d = []
            for r in rs:
                m = [x for x in r['results'] if x['g'] == g and x['kind'] == 'mod'][0]
                f = [x for x in r['results'] if x['g'] == g and x['kind'] == 'matched'][0]
                d.append(m['BWT'] - f['BWT'])
            d = np.array(d)
            try:
                p = float(stats.wilcoxon(d).pvalue) if len(d) > 1 and np.any(d != 0) else 1.0
            except ValueError:
                p = 1.0
            c[f'delta_g{g:+.1f}'] = {'mean': float(d.mean()), 'sd': float(d.std()), 'n_positive': int((d > 0).sum()),
                                     'n': int(len(d)), 'p_wilcoxon': p, 'values': d.tolist()}
        d1 = c['delta_g+1.0']
        tot += 1
        neg += d1['mean'] < 0
        sig_pos += (d1['mean'] > 0 and d1['p_wilcoxon'] < 0.05)
        if rule == 'rgate':
            tot_rg += 1
            neg_rg += d1['mean'] < 0
            sig_pos_rg += (d1['mean'] > 0 and d1['p_wilcoxon'] < 0.05)
        mono += d1['mean'] <= c['delta_g+0.5']['mean'] <= 0
        out['cells'][f'N{N}_k{k}_{n}_{rule}'] = c
    out['criterion1'] = {'cells': tot, 'mean_delta_plus1_negative': int(neg), 'significantly_positive': int(sig_pos),
                         'pass': bool(tot and neg >= int(np.ceil(0.9 * tot)) and sig_pos == 0)}
    out['criterion2_rgate'] = {'cells': tot_rg, 'mean_delta_plus1_negative': int(neg_rg),
                               'significantly_positive': int(sig_pos_rg),
                               'pass': bool(tot_rg and neg_rg >= tot_rg - 1 and sig_pos_rg == 0)}
    out['monotone_cells'] = int(mono)
    return out


def analyze_e36(sub: str = 'e36'):
    """E3.6 — kryterium z README sek. 6c (zadanie separacji wzorców, dg_core);
    sub='e36x' — wariant na modelu skalibrowanym do skrawka (sek. 6e)."""
    runs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RES, sub, 'learn_*.json')))]
    cells = defaultdict(list)
    for r in runs:
        cells[(r['r_in'], r['rule'])].append(r)
    out = {'cells': {}}
    neg = sig_pos = 0
    for (rin, rule), rs in sorted(cells.items()):
        c = {'n_runs': len(rs)}
        for g in (-1.0, -0.5, 0.5, 1.0):
            d = np.array([[x for x in r['results'] if x['g'] == g and x['kind'] == 'mod'][0]['BWT']
                          - [x for x in r['results'] if x['g'] == g and x['kind'] == 'matched'][0]['BWT'] for r in rs])
            try:
                p = float(stats.wilcoxon(d).pvalue) if len(d) > 1 and np.any(d != 0) else 1.0
            except ValueError:
                p = 1.0
            c[f'delta_g{g:+.1f}'] = {'mean': float(d.mean()), 'n_positive': int((d > 0).sum()), 'n': int(len(d)),
                                     'p_wilcoxon': p}
        c['ACC_fixed'] = float(np.mean([[x for x in r['results'] if x['kind'] == 'fixed'][0]['ACC'] for r in rs]))
        neg += c['delta_g+1.0']['mean'] < 0
        sig_pos += c['delta_g+1.0']['mean'] > 0 and c['delta_g+1.0']['p_wilcoxon'] < 0.05
        out['cells'][f'rin{rin:.2f}_{rule}'] = c
    n = len(out['cells'])
    out['criterion'] = {'cells': n, 'mean_delta_plus1_negative': int(neg), 'significantly_positive': int(sig_pos),
                        'pass': bool(n and neg >= n - 1 and sig_pos == 0)}
    return out


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    os.makedirs(FIG, exist_ok=True)
    summary = {'e31': analyze_e31(plt), 'e32': analyze_e32(plt), 'e33': analyze_e33(plt),
               'e34': analyze_e34(plt), 'e35': analyze_e35(), 'e36': analyze_e36(), 'e36x': analyze_e36('e36x')}
    with open(os.path.join(RES, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
