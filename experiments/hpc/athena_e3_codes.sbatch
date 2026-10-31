#!/bin/bash -l
## E3 — kody warstwy DG (precompute) na GPU.
##   sbatch --export=ALL,NEURON=izh,SEED=0 athena_e3_codes.sbatch
##   sbatch --export=ALL,NEURON=izh,SEED=0,PHASIC=1 athena_e3_codes.sbatch   # E3.2
## Wyjście: experiments/e3_sparsity_third_factor/results/codes/

#SBATCH --job-name=dg-e3codes
#SBATCH --account=plgdyplomanci8-gpu-a100
#SBATCH --partition=plgrid-gpu-a100
#SBATCH --gpus=1
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24GB
#SBATCH --output=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e3codes_%j.out
#SBATCH --error=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e3codes_%j.err

set -euo pipefail
REPO=/net/tscratch/people/plgjakubcaputa/snn_separation
VENV=/net/tscratch/people/plgjakubcaputa/venvs/snn_sep_venv
NEURON="${NEURON:-izh}"
SEED="${SEED:-0}"
PRESET="${PRESET:-full}"
EXTRA=""
if [ "${PHASIC:-0}" = "1" ]; then EXTRA="--phasic"; fi

export PYTHONIOENCODING=utf-8
cd "${REPO}/experiments/e3_sparsity_third_factor"
echo "=== E3 codes | ${NEURON} seed ${SEED} ${EXTRA} | $(date) | job ${SLURM_JOB_ID} ==="
nvidia-smi -L || true
"${VENV}/bin/python" precompute_codes.py --neuron "${NEURON}" --seed "${SEED}" \
    --preset "${PRESET}" --batch 1000 ${EXTRA}
echo "=== done: $(date) ==="
