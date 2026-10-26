"""
Cele kalibracji ex vivo z danych Madara (S-BSST219): częstotliwość, R_w, R_b, R_in
dla GC (kontrola), GC przed/po gabazynie (100 nM, pary), FS i HMC; biny 10/20/50/100 ms;
R_w i R_b z 5 i z 10 powtórzeń (pytanie prof. Błasiak: czy 5 vs 10 robi różnicę).

Wyjście: results/madar_targets.json (wszystkie nagrania) i results/madar_targets.md (tabela).
Użycie (z katalogu experiments/):  python -m calib_exvivo.madar_targets
"""
from __future__ import annotations

import json
import os

import numpy as np

from dg_core import io_madar as M

HERE = os.path.dirname(os.path.abspath(__file__))
BINS = [0.010, 0.020, 0.050, 0.100]
DATASETS = ['gc_all', 'gc_before_gzn', 'gc_after_gzn', 'fs', 'hmc']


def main():
    out = {}
    for key in DATASETS:
        out[key] = {}
        for b in BINS:
            for k in (5, 10):
                rows = M.dataset_table(key, b, n_repeats_used=k)
                out[key][f'bin{int(b * 1000)}ms_rep{k}'] = rows
        ok = [r for r in out[key]['bin10ms_rep10'] if 'R_w' in r]
        bad = [r for r in out[key]['bin10ms_rep10'] if 'R_w' not in r]
        print(f'{key}: {len(ok)} nagrań, pominięte {len(bad)}', flush=True)
    with open(os.path.join(HERE, 'results', 'madar_targets.json'), 'w') as f:
        json.dump(out, f)

    def summ(rows, field):
        v = np.array([r[field] for r in rows if field in r and np.isfinite(r[field])])
        if not len(v):
            return '—'
        q = np.percentile(v, [25, 50, 75])
        return f'{q[1]:.2f} [{q[0]:.2f}–{q[2]:.2f}] (n={len(v)})'
    lines = ['# Cele kalibracji ex vivo — dane Madara (S-BSST219)', '',
             'Mediana [IQR] po nagraniach. R_in = podobieństwo pociągów wejściowych, R_w = rzetelność '
             '(odpowiedzi na powtórzenia tego samego pociągu), R_b = podobieństwo odpowiedzi na różne pociągi. '
             'Impuls = przejście przez −20 mV. Sweep = 2 s.', '']
    for b in BINS:
        lines += [f'## bin {int(b * 1000)} ms', '',
                  '| zbiór | powt. | częstotliwość [Hz] | R_in | R_w | R_b |', '|---|---|---|---|---|---|']
        for key in DATASETS:
            for k in (10, 5):
                rows = [r for r in out[key][f'bin{int(b * 1000)}ms_rep{k}'] if 'R_w' in r]
                lines.append(f'| {key} | {k} | {summ(rows, "fr_hz")} | {summ(rows, "R_in")} | '
                             f'{summ(rows, "R_w")} | {summ(rows, "R_b")} |')
        lines.append('')
    # pary przed/po gabazynie
    bef = [r for r in out['gc_before_gzn']['bin10ms_rep10'] if 'R_w' in r]
    aft = [r for r in out['gc_after_gzn']['bin10ms_rep10'] if 'R_w' in r]
    if len(bef) == len(aft):
        ratio = [a['fr_hz'] / max(b_['fr_hz'], 1e-9) for b_, a in zip(bef, aft)]
        lines += ['## Gabazyna 100 nM — pary (ta sama komórka), bin 10 ms, 10 powtórzeń', '',
                  '| komórka | FR przed → po [Hz] | ×FR | R_w przed → po | R_b przed → po |', '|---|---|---|---|---|']
        for i, (b_, a) in enumerate(zip(bef, aft)):
            lines.append(f'| {i + 1} | {b_["fr_hz"]:.2f} → {a["fr_hz"]:.2f} | {ratio[i]:.2f} | '
                         f'{b_["R_w"]:.3f} → {a["R_w"]:.3f} | {b_["R_b"]:.3f} → {a["R_b"]:.3f} |')
        lines += ['', f'Mediana ×FR = {np.median(ratio):.2f} (zakres {min(ratio):.2f}–{max(ratio):.2f}).', '']
    with open(os.path.join(HERE, 'results', 'madar_targets.md'), 'w') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
