#!/bin/bash
# E3.7 — dolicza brakujące przebiegi (te, dla których nie ma pliku wyniku), równolegle.
for v in agrel agrel_pos; do for n in izh lif; do for s in 0 1 2 3 4; do for o in 0 1; do
  [ -f results/e37/run_${v}_${n}_s${s}_o${o}.json ] || echo "$v $n $s $o"
done; done; done; done | xargs -P "${1:-16}" -n 4 bash -c 'python run_hidden.py --phase run --variant $0 --neuron $1 --seed $2 --order-seed $3 > results/logs/e37_$0_$1_s$2_o$3.log 2>&1'
