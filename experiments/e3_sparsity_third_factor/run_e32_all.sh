#!/bin/bash
# E3.2 — hamowanie fazowe przy stałym f, oba neurony, ziarna 0–4.
for n in izh lif; do for s in 0 1 2 3 4; do python run_static.py --exp e32 --neuron "$n" --seed "$s" --order-seed 0 --jobs 10; done; done
