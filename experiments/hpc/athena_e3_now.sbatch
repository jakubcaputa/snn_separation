#!/bin/bash -l
## E3 — dowolny ciąg kroków na plgrid-now (16 CPU, 1 GPU, 1 h, jedno zadanie naraz).
## Kroki w zmiennej STEPS, rozdzielone ';', wykonywane w e3_sparsity_third_factor/:
##   sbatch --export=ALL,STEPS="python precompute_codes.py --neuron lif --seed 99 --batch 1000" athena_e3_now.sbatch
## Kolejne zadania łańcuchem: --dependency=afterany:<poprzedni>

#SBATCH --job-name=dg-e3now
#SBATCH --account=plgdyplomanci8-gpu-a100
#SBATCH --partition=plgrid-now
#SBATCH --gpus=1
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64GB
#SBATCH --output=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e3now_%j.out
#SBATCH --error=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e3now_%j.err

set -euo pipefail
REPO=/net/tscratch/people/plgjakubcaputa/snn_separation
VENV=/net/tscratch/people/plgjakubcaputa/venvs/snn_sep_venv
export PATH="${VENV}/bin:${PATH}"
export PYTHONIOENCODING=utf-8
export OMP_NUM_THREADS=1
cd "${REPO}/experiments/e3_sparsity_third_factor"
echo "=== E3 now | job ${SLURM_JOB_ID} | $(date) ==="
IFS=';' read -ra ARR <<< "${STEPS}"
for s in "${ARR[@]}"; do
  echo ">>> ${s}  ($(date +%T))"
  eval "${s}"
done
echo "=== done: $(date) ==="
