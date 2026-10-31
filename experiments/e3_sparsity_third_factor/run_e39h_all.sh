#!/bin/bash
# E3.9h — rozbicie błędów dla warstwy ukrytej: ./run_e39h_all.sh <wariant> [neuron]; sieci 0–4 × kolejności 0, 1.
for n in ${2:-izh lif}; do for s in 0 1 2 3 4; do for o in 0 1; do
  [ -f "results/e37/errors/$1_${n}_s${s}_o${o}.json" ] || echo "$n $s $o"
done; done; done | \
  xargs -r -P 16 -n 3 bash -c "python run_hidden_errors.py --variant $1 --neuron \$0 --seed \$1 --order-seed \$2 > results/logs/e39h_$1_\$0_s\$1_o\$2.log 2>&1"
