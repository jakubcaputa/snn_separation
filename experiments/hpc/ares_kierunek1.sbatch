#!/bin/bash -l
## Kierunek 1 — klasyfikator downstream + pojemność pamięci (Ares / Cyfronet)
##
## Wysłanie (dwa eksperymenty, ten sam skrypt):
##   sbatch --array=0-39 ares_kierunek1.sbatch classification
##   sbatch --array=0-19 ares_kierunek1.sbatch capacity
## Po zakończeniu:
##   python analyze_readout.py --in "classification_full_shard*.npz" \
##                             --capacity "capacity_full_shard*.npz"

#SBATCH --job-name=dg-k1
#SBATCH --account=CHANGEME-cpu          # <-- wpisz swój grant PLGrid
#SBATCH --partition=plgrid
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --mem=16G
#SBATCH --output=logs/k1_%A_%a.out
#SBATCH --error=logs/k1_%A_%a.err

set -euo pipefail
mkdir -p logs

EXPERIMENT="${1:-classification}"       # classification | capacity

module load python/3.11
cd "${SLURM_SUBMIT_DIR}/../kierunek1_readout"
source "${SCRATCH}/dgvenv/bin/activate"

export BRIAN2_CACHE_DIR="${SCRATCH}/brian_cache/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
mkdir -p "${BRIAN2_CACHE_DIR}"
export PYTHONIOENCODING=utf-8
export OMP_NUM_THREADS=1

case "${EXPERIMENT}" in
  classification) SCRIPT=run_classification.py ;;
  capacity)       SCRIPT=run_capacity.py ;;
  *) echo "Nieznany eksperyment: ${EXPERIMENT} (użyj: classification | capacity)"; exit 1 ;;
esac

python "${SCRIPT}" \
    --preset full \
    --n-jobs "${SLURM_CPUS_PER_TASK}" \
    --shard "${SLURM_ARRAY_TASK_ID}" \
    --n-shards "${SLURM_ARRAY_TASK_COUNT}"

echo "${EXPERIMENT} shard ${SLURM_ARRAY_TASK_ID} zakończony"
