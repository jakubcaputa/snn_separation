#!/bin/bash -l
## Kierunek 4 — sweep lezji + Shapley (Ares / Cyfronet, PLGrid)
## Job array: każdy task liczy swój shard siatki, wyniki scala analyze_regime_map.py  # TODO: skrypt jeszcze nie istnieje.
##
## Wysłanie:
##   sbatch --array=0-19 ares_e1_regime_map.sbatch
## Po zakończeniu:
##   python analyze_regime_map.py  # TODO: skrypt jeszcze nie istnieje --in "regime_map_full_shard*.npz"

#SBATCH --job-name=dg-k4
#SBATCH --account=CHANGEME-cpu          # <-- wpisz swój grant PLGrid
#SBATCH --partition=plgrid
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --mem=16G
#SBATCH --output=logs/k4_%A_%a.out
#SBATCH --error=logs/k4_%A_%a.err

set -euo pipefail
mkdir -p logs

module load python/3.11

REPO="${SLURM_SUBMIT_DIR}/../.."
cd "${SLURM_SUBMIT_DIR}/../e1_regime_map"

# venv przygotuj RAZ przed wysłaniem joba:
#   python -m venv $SCRATCH/dgvenv
#   $SCRATCH/dgvenv/bin/pip install brian2 numpy scipy matplotlib scikit-learn joblib
source "${SCRATCH}/dgvenv/bin/activate"

# Brian2 kompiluje kod w cache — osobny katalog na task, inaczej równoległe
# taski nadpisują sobie cache i job losowo pada.
export BRIAN2_CACHE_DIR="${SCRATCH}/brian_cache/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
mkdir -p "${BRIAN2_CACHE_DIR}"
export PYTHONIOENCODING=utf-8
export OMP_NUM_THREADS=1                # joblib zarządza równoległością, nie BLAS

python run_regime_map.py \
    --preset full \
    --n-jobs "${SLURM_CPUS_PER_TASK}" \
    --shard "${SLURM_ARRAY_TASK_ID}" \
    --n-shards "${SLURM_ARRAY_TASK_COUNT}"

echo "shard ${SLURM_ARRAY_TASK_ID} zakończony"
