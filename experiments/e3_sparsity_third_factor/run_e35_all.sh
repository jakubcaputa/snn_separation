#!/bin/bash
# E3.5 — dawka–odpowiedź dla jednej architektury: ./run_e35_all.sh <procesy> <n_dg> <fan_in> "<sieci>"
for n in izh lif; do for r in rstdp delta rgate; do for s in $4; do for o in 0 1; do
  echo "$n $r $s $o"
done; done; done; done | xargs -P "$1" -n 4 bash -c "python run_dose.py --neuron \$0 --rule \$1 --seed \$2 --order-seed \$3 --n-dg $2 --fan-in $3 > results/logs/e35_\$0_\$1_n$2_k$3_s\$2_o\$3.log 2>&1"
