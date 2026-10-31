"""
E3 — analiza: łączy wyniki E3.1, E3.2, E3.3, liczy kryteria zapisane w prereg.md sek. 6
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
    """E3.5 — kryteria z prereg.md sek. 6b. Efekt Δ(g) = BWT(mod g) − BWT(stałe f g)."""
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
    """E3.6 — kryterium z prereg.md sek. 6c (zadanie separacji wzorców, dg_core);
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


def _wilc(d):
    d = np.asarray(d, float)
    try:
        p = float(stats.wilcoxon(d).pvalue) if len(d) > 1 and np.any(d != 0) else 1.0
    except ValueError:
        p = 1.0
    return {'mean': float(d.mean()), 'n_positive': int((d > 0).sum()), 'n': int(len(d)), 'p_wilcoxon': p}


def analyze_e38():
    """E3.8 — kryteria z prereg.md sek. 6f (mechanizm „rozcieńczać / izolować”)."""
    runs = _load('e38/*.json')
    out = {}
    for neuron in ('izh', 'lif'):
        rs = [r for r in runs if r['neuron'] == neuron]
        if not rs:
            continue
        s = {'n_runs': len(rs), 'A': {}, 'B': {}}
        for rule in ('rstdp', 'delta', 'rstdp_raw', 'delta_raw'):
            A = [r['A'][rule] for r in rs]
            s['A'][rule] = {
                'delta_plus1': _wilc([x['mod']['BWT'] - x['matched_mod']['BWT'] for x in A]),
                'delta_minus1': _wilc([x['inv']['BWT'] - x['matched_inv']['BWT'] for x in A]),
                'delta_minus1_evalrest': _wilc([x['inv']['BWT'] - x['matched_inv_evalrest']['BWT'] for x in A]),
                'damage_inv_minus_matched_evalrest': _wilc([x['inv']['damage_frac_novel'] - x['matched_inv_evalrest']['damage_frac_novel'] for x in A]),
                'damage_mod_minus_matched': _wilc([x['mod']['damage_frac_novel'] - x['matched_mod']['damage_frac_novel'] for x in A]),
                'damage_frac_novel': {k: float(np.mean([x[k]['damage_frac_novel'] for x in A]))
                                      for k in ('mod', 'inv', 'matched_mod', 'matched_inv', 'matched_inv_evalrest')}}
        for base in ('rstdp', 'delta'):
            d = [r['A'][f'{base}_raw']['inv']['BWT'] - r['A'][f'{base}_raw']['matched_inv']['BWT']
                 - (r['A'][base]['inv']['BWT'] - r['A'][base]['matched_inv']['BWT']) for r in rs]
            s['A'][f'H_M2_{base}_raw_minus_norm_delta_minus1'] = _wilc(d)
        for lam in ('0.0', '0.25', '0.5', '0.75', '1.0'):
            B = [r['B'][lam] for r in rs if lam in r['B']]
            s['B'][lam] = {'delta_plus1': _wilc([x['mod']['BWT'] - x['matched_mod']['BWT'] for x in B]),
                           'delta_minus1': _wilc([x['inv']['BWT'] - x['matched_inv']['BWT'] for x in B]),
                           'ACC_fixed': float(np.mean([x['matched_mod']['ACC'] for x in B]))}
        lam_means = [s['B'][l]['delta_plus1']['mean'] for l in ('0.0', '0.25', '0.5', '0.75', '1.0')]
        s['H_M4'] = {'spearman_lambda_delta_plus1': float(stats.spearmanr([0, .25, .5, .75, 1], lam_means).correlation),
                     'sign_change': bool(s['B']['0.0']['delta_plus1']['mean'] > 0 > s['B']['1.0']['delta_plus1']['mean']),
                     'pass': bool(s['B']['0.0']['delta_plus1']['mean'] > 0 and s['B']['0.0']['delta_plus1']['p_wilcoxon'] < 0.05
                                  and s['B']['1.0']['delta_plus1']['mean'] < 0 and s['B']['1.0']['delta_plus1']['p_wilcoxon'] < 0.05)}
        out[neuron] = s
    return out


def analyze_e37():
    """E3.7 — kryterium z prereg.md sek. 6g (sieć z warstwą ukrytą)."""
    runs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RES, 'e37', 'run_*.json')))]
    out = {}
    for variant, expect in (('agrel', -1), ('agrel_pos', +1)):
        for neuron in ('izh', 'lif'):
            rs = [r for r in runs if r['variant'] == variant and r['neuron'] == neuron]
            if not rs:
                continue
            get = lambda r, g, k: [x for x in r['results'] if x['g'] == g and x['kind'] == k][0]
            dp = _wilc([get(r, 1.0, 'mod')['BWT'] - get(r, 1.0, 'matched')['BWT'] for r in rs])
            dm = _wilc([get(r, -1.0, 'mod')['BWT'] - get(r, -1.0, 'matched')['BWT'] for r in rs])
            n_ok = dp['n_positive'] if expect > 0 else dp['n'] - dp['n_positive']
            out[f'{variant}_{neuron}'] = {'delta_plus1': dp, 'delta_minus1': dm,
                                          'ACC_fixed': float(np.mean([get(r, 0.0, 'fixed')['ACC'] for r in rs])),
                                          'BWT_fixed': float(np.mean([get(r, 0.0, 'fixed')['BWT'] for r in rs])),
                                          'expected_sign': expect,
                                          'pass': bool(np.sign(dp['mean']) == expect and dp['p_wilcoxon'] < 0.05
                                                       and n_ok >= int(np.ceil(0.8 * dp['n'])))}
    out['H_L1_pass'] = bool(out) and all(v['pass'] for v in out.values() if isinstance(v, dict))
    return out


def analyze_e37b():
    """E3.7b — kryterium H-L1b z prereg.md sek. 6i (warstwa ukryta bez osłabiania heterosynaptycznego)."""
    runs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RES, 'e37', 'run_*.json')))]
    get = lambda r, g, k: [x for x in r['results'] if x['g'] == g and x['kind'] == k][0]
    out = {}
    for variant, expect in (('pos_bound', +1), ('pos_pool', +1), ('agrel_bound', -1)):
        for neuron in ('izh', 'lif'):
            rs = [r for r in runs if r['variant'] == variant and r['neuron'] == neuron]
            if not rs:
                continue
            dp = _wilc([get(r, 1.0, 'mod')['BWT'] - get(r, 1.0, 'matched')['BWT'] for r in rs])
            dm = _wilc([get(r, -1.0, 'mod')['BWT'] - get(r, -1.0, 'matched')['BWT'] for r in rs])
            acc = float(np.mean([get(r, 0.0, 'fixed')['ACC'] for r in rs]))
            n_ok = dp['n_positive'] if expect > 0 else dp['n'] - dp['n_positive']
            out[f'{variant}_{neuron}'] = {
                'delta_plus1': dp, 'delta_minus1': dm, 'ACC_fixed': acc,
                'BWT_fixed': float(np.mean([get(r, 0.0, 'fixed')['BWT'] for r in rs])),
                'expected_sign': expect, 'decisive': acc > 0.25,
                'pass': bool(np.sign(dp['mean']) == expect and dp['p_wilcoxon'] < 0.05
                             and n_ok >= int(np.ceil(0.8 * dp['n'])))}
    dec = {k: v for k, v in out.items() if v['decisive']}
    pos_ok = any(all(out.get(f'{v}_{n}', {}).get('decisive') and out[f'{v}_{n}']['pass']
                     for v in ('pos_bound', 'pos_pool')) for n in ('izh', 'lif'))
    out['n_decisive'] = len(dec)
    out['H_L1b_pass'] = bool(len(dec) >= 4 and all(v['pass'] for v in dec.values()) and pos_ok)
    return out


def analyze_e39():
    """E3.9 — kryteria H-R1…H-R4 z prereg.md sek. 6h (przewaga nowych klas vs zniszczenie wag)."""
    runs = _load('e39/*.json')
    out = {}
    for neuron in ('izh', 'lif'):
        rs = [r for r in runs if r['neuron'] == neuron]
        if not rs:
            continue
        s = {'n_runs': len(rs)}
        for rule in ('rstdp', 'delta', 'rgate'):
            R = [r['rules'][rule] for r in rs]
            m = lambda c, k: np.array([x[c][k] for x in R])
            desc = {c: {k: float(m(c, k).mean()) for k in ('acc_class', 'acc_within', 'acc_debiased', 'err_newer',
                                                         'err_last', 'err_same_task', 'err_older')}
                    for c in ('mod', 'matched_mod', 'inv', 'matched_inv', 'matched_inv_evalrest')}
            gap = m('matched_mod', 'acc_within') - m('matched_mod', 'acc_class')
            gw = _wilc(gap)
            r1 = bool(desc['matched_mod']['acc_within'] >= 0.80 and gw['mean'] >= 0.30
                      and gw['p_wilcoxon'] < 0.05 and int((gap >= 0.30).sum()) >= 8)
            en = m('matched_mod', 'err_newer')
            r2 = bool(en.mean() >= 0.80 and int((en >= 0.80).sum()) >= 8)
            dl = _wilc(m('matched_inv_evalrest', 'err_last') - m('inv', 'err_last'))
            dwin = float((m('inv', 'acc_within') - m('matched_inv_evalrest', 'acc_within')).mean())
            r3 = bool(dl['mean'] > 0 and dl['p_wilcoxon'] < 0.05 and dl['n_positive'] >= 8 and abs(dwin) < 0.03)
            db = _wilc(m('matched_mod', 'acc_debiased') - m('matched_mod', 'acc_class'))
            r4 = bool(db['mean'] >= 0.20 and db['p_wilcoxon'] < 0.05)
            s[rule] = {'conditions': desc, 'H_R1': {'gap': gw, 'pass': r1},
                       'H_R2': {'err_newer_mean': float(en.mean()), 'n_ge_0.8': int((en >= 0.80).sum()), 'pass': r2},
                       'H_R3': {'err_last_evalrest_minus_inv': dl, 'acc_within_diff': dwin, 'pass': r3},
                       'H_R4': {'debias_gain': db, 'pass': r4}}
        out[neuron] = s
    out['recency_supported'] = bool(len(out) == 2 and all(
        out[n][r][h]['pass'] for n in ('izh', 'lif') for r in ('rstdp', 'delta') for h in ('H_R1', 'H_R2', 'H_R3')))
    return out


def analyze_e39h():
    """E3.9h — prereg.md sek. 6j: przewaga nowych klas czy zniszczenie reprezentacji w warstwie ukrytej."""
    runs = _load('e37/errors/*.json')
    out = {}
    keys = ('acc_class', 'acc_within', 'acc_debiased', 'err_newer', 'err_last', 'err_same_task', 'err_older')
    for variant in ('pos_bound', 'agrel_pos', 'pos_pool'):
        for neuron in ('izh', 'lif'):
            rs = [r['conditions'] for r in runs if r['variant'] == variant and r['neuron'] == neuron]
            if not rs:
                continue
            m = lambda c, k: np.array([x[c][k] for x in rs])
            desc = {c: {k: float(m(c, k).mean()) for k in keys} for c in rs[0]}
            gap = m('fixed', 'acc_within') - m('fixed', 'acc_class')
            gw = _wilc(gap)
            aw = desc['fixed']['acc_within']
            recency = bool(aw >= 0.80 and gw['mean'] >= 0.30 and gw['p_wilcoxon'] < 0.05
                           and int((gap >= 0.30).sum()) >= 8 and desc['fixed']['err_newer'] >= 0.80)
            verdict = 'recency' if recency else ('destruction' if aw < 0.65 else 'mixed')
            out[f'{variant}_{neuron}'] = {
                'n_runs': len(rs), 'conditions': desc, 'gap_within_minus_class': gw, 'verdict': verdict,
                'mod_vs_matched_acc_within': _wilc(m('mod', 'acc_within') - m('matched_mod', 'acc_within')),
                'mod_vs_matched_err_last': _wilc(m('mod', 'err_last') - m('matched_mod', 'err_last'))}
    return out


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    os.makedirs(FIG, exist_ok=True)
    summary = {'e31': analyze_e31(plt), 'e32': analyze_e32(plt), 'e33': analyze_e33(plt),
               'e34': analyze_e34(plt), 'e35': analyze_e35(), 'e36': analyze_e36(), 'e36x': analyze_e36('e36x'),
               'e37': analyze_e37(), 'e37b': analyze_e37b(), 'e38': analyze_e38(), 'e39': analyze_e39(), 'e39h': analyze_e39h()}
    with open(os.path.join(RES, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
