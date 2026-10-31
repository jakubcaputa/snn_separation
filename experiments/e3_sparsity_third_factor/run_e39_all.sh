#!/bin/bash
# E3.9 — rozbicie błędów: 2 neurony × sieci 0–4 × kolejności 0, 1 = 20 przebiegów, równolegle.
for n in izh lif; do for s in 0 1 2 3 4; do for o in 0 1; do [ -f "results/e39/${n}_s${s}_o${o}.json" ] || echo "$n $s $o"; done; done; done | \
  xargs -r -P "${1:-16}" -n 3 bash -c 'python run_errors.py --neuron $0 --seed $1 --order-seed $2 > results/logs/e39_$0_s$1_o$2.log 2>&1'
