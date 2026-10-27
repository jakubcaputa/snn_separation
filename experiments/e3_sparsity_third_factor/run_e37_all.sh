#!/bin/bash
# E3.7 — sieć z warstwą ukrytą: ./run_e37_all.sh <procesy> <agrel|agrel_pos>; 2 neurony × sieci 0–4 × kolejności 0, 1.
for n in izh lif; do for s in 0 1 2 3 4; do for o in 0 1; do echo "$n $s $o"; done; done; done | \
  xargs -P "$1" -n 3 bash -c "python run_hidden.py --phase run --variant $2 --neuron \$0 --seed \$1 --order-seed \$2 > results/logs/e37_$2_\$0_s\$1_o\$2.log 2>&1"
