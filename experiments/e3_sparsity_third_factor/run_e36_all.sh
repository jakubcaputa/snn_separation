#!/bin/bash
# E3.6 — faza learn: 3 R_in × 3 czytniki × sieci 0–2 × kolejności 0, 1 = 54 przebiegi.
# REGIME=exvivo ./run_e36_all.sh 16  → model skalibrowany do skrawka (results/e36x/)
for rin in 0.5 0.75 0.9; do for r in rstdp delta rgate; do for s in 0 1 2; do for o in 0 1; do
  echo "$rin $r $s $o"
done; done; done; done | xargs -P "${1:-16}" -n 4 bash -c 'python run_dgtask.py --phase learn --regime ${REGIME:-invivo} --r-in $0 --rule $1 --seed $2 --order-seed $3 > results/logs/e36${REGIME:-invivo}_rin$0_$1_s$2_o$3.log 2>&1'
