#!/bin/bash
# E3.1 — wszystkie sieci (ziarna 0–4) dla jednego typu neuronu: ./run_e31_all.sh izh
for s in 0 1 2 3 4; do python run_static.py --exp e31 --neuron "$1" --seed "$s" --order-seed 0 --jobs 16; done
