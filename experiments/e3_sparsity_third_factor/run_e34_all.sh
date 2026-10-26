#!/bin/bash
# E3.4 — kod × reguła czytnika: 2 neurony × 10 sieci × 2 kolejności = 40 przebiegów, równolegle.
for n in izh lif; do for s in 0 1 2 3 4 5 6 7 8 9; do for o in 0 1; do
  echo "$n $s $o"
done; done; done | xargs -P "${1:-16}" -n 3 bash -c 'python run_factorial.py --neuron $0 --seed $1 --order-seed $2 > results/logs/e34_$0_s$1_o$2.log 2>&1'
