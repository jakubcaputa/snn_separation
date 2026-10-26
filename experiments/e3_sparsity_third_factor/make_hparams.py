"""
E3 — składa hparams.json z wyników strojenia (ziarno pilotażowe 99), w dwóch krokach.

Krok 1 (po `run_static.py --exp tune`):
  η każdego czytnika = najlepsza średnia dokładność walidacyjna po wszystkich poziomach f;
  f_dense = poziom z najwyższą dokładnością walidacyjną przy tym η;
  f_sparse = poziom najbliższy f_dense / 4 (decyzja Q9).
Krok 2 (po `run_split.py --pilot`):
  sygnał nowości: 'unc', chyba że jego N̄ nie rośnie na granicach zadań
  (boundary_rise ≤ 0) — wtedy 'rpe' (reguła zapisana PRZED pilotażem);
  a, b = 5. i 95. percentyl N̄ wybranego sygnału.
Walidacja = ostatnie 10 000 obrazów zbioru treningowego; zbiór testowy nie jest używany.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HP = os.path.join(HERE, 'hparams.json')
RES = os.path.join(HERE, 'results')
PILOT_SEED = 99


def nearest(levels, f):
    return min(levels, key=lambda x: abs(math.log(x) - math.log(f)))


def step1(hp):
    for neuron in ('izh', 'lif'):
        fn = os.path.join(RES, 'tune', f'{neuron}_s{PILOT_SEED}.json')
        if not os.path.exists(fn):
            print('brak', fn)
            continue
        with open(fn) as f:
            tune = json.load(f)
        with open(os.path.join(RES, 'codes', f'{neuron}_s{PILOT_SEED}.json')) as f:
            meta = json.load(f)
        levels = meta['f_levels']
        hp.setdefault(neuron, {})
        for rule in ('rstdp', 'delta', 'rgate'):
            if rule not in tune['best_eta']:
                continue
            eta = tune['best_eta'][rule]
            recs = [r for r in tune['records'] if r['rule'] == rule and r['eta'] == eta]
            best = max(recs, key=lambda r: r['val_acc'])
            f_dense = levels[best['level']]
            hp[neuron][rule] = {'eta': eta, 'f_dense': f_dense,
                                'f_sparse': nearest(levels, f_dense / 4),
                                'val_acc_at_f_dense': best['val_acc']}
    return hp


def step2(hp):
    hp.setdefault('controller', {})
    for neuron in ('izh', 'lif'):
        for rule in ('rstdp', 'delta', 'rgate'):
            fn = os.path.join(RES, 'pilot', f'{neuron}_{rule}_s{PILOT_SEED}.json')
            if not os.path.exists(fn):
                print('brak', fn)
                continue
            with open(fn) as f:
                pil = json.load(f)
            sig = 'unc' if pil['unc']['boundary_rise'] > 0 else 'rpe'
            hp['controller'][f'{neuron}_{rule}'] = {
                'signal': sig, 'a': pil[sig]['a'], 'b': pil[sig]['b'],
                'boundary_rise_unc': pil['unc']['boundary_rise'],
                'boundary_rise_rpe': pil['rpe']['boundary_rise']}
    return hp


if __name__ == '__main__':
    hp = {}
    if os.path.exists(HP):
        with open(HP) as f:
            hp = json.load(f)
    hp.setdefault('eps', 0.02)
    hp.setdefault('tau', 50.0)
    hp.setdefault('c_lr', 3.0)
    hp.setdefault('oracle_M', 300)
    hp.setdefault('epochs_per_task', 1)
    hp.setdefault('fly_f', 0.05)
    hp.setdefault('fly_eta', 0.01)
    hp = step1(hp) if sys.argv[1:] == ['1'] else step2(hp)
    with open(HP, 'w') as f:
        json.dump(hp, f, indent=1)
    print(json.dumps(hp, indent=1))
