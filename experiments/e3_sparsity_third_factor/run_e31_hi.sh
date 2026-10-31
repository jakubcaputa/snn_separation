#!/bin/bash
# Fig. 1 — poziomy f 70% i 90% (README sek. 6k): ./run_e31_hi.sh <neuron>; kody (GPU) i E3.1 dla sieci 0–4.
for s in 0 1 2 3 4; do
  [ -f "results/codes/$1_s${s}_hi.json" ] || python precompute_codes.py --neuron "$1" --seed "$s" --levels 0.7 0.9 --tag hi > "results/logs/codes_hi_$1_s$s.log" 2>&1
  [ -f "results/e31_hi/$1_s${s}_o0_hi.json" ] || python run_static.py --exp e31 --neuron "$1" --seed "$s" --order-seed 0 --jobs 3 --codes-tag hi > "results/logs/e31_hi_$1_s$s.log" 2>&1
done
