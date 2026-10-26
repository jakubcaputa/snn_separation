#!/bin/bash
# E3.3 (użycie: ./run_e33_all.sh <procesy> [neuron] ["ziarna sieci"]) — wszystkie przebiegi Split-MNIST równolegle: 2 neurony × 2 czytniki × 5 sieci × 2 kolejności.
# kwta_fly (FlyModel) liczony raz na (sieć, kolejność), przy przebiegach rstdp.
for n in ${2:-izh lif}; do for r in rstdp delta; do for s in ${3:-0 1 2 3 4}; do for o in 0 1; do
  extra=""; [ "$r" = "rstdp" ] && extra="--with-fly"
  echo "python run_split.py --neuron $n --rule $r --seed $s --order-seed $o $extra"
done; done; done; done | xargs -P "${1:-16}" -I{} bash -c "{} > results/logs/e33_\$(echo '{}' | tr ' -' '__' | cut -c20-90).log 2>&1"
