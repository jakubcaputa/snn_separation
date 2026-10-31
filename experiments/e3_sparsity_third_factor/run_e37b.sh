#!/bin/bash
# E3.7b — warstwa ukryta bez osłabiania heterosynaptycznego (README sek. 6i).
#   ./run_e37b.sh prep                 — strojenie η, potem pilotaż (oba neurony × 3 warianty, równolegle)
#   ./run_e37b.sh run <wariant> [neuron] — przebiegi: sieci 0–4 × kolejności 0, 1 (brak pliku wyniku → licz)
V="pos_bound pos_pool agrel_bound"
if [ "$1" = prep ]; then
  for n in izh lif; do for v in $V; do echo "$n $v"; done; done | \
    xargs -r -P 6 -n 2 bash -c 'python run_hidden.py --phase tune --neuron $0 --variants $1 > results/logs/e37b_tune_$0_$1.log 2>&1 && python run_hidden.py --phase pilot --neuron $0 --variants $1 > results/logs/e37b_pilot_$0_$1.log 2>&1'
  exit
fi
for n in ${3:-izh lif}; do for s in 0 1 2 3 4; do for o in 0 1; do
  [ -f "results/e37/run_$2_${n}_s${s}_o${o}.json" ] || echo "$n $s $o"
done; done; done | \
  xargs -r -P 16 -n 3 bash -c "python run_hidden.py --phase run --variant $2 --neuron \$0 --seed \$1 --order-seed \$2 > results/logs/e37b_$2_\$0_s\$1_o\$2.log 2>&1"
