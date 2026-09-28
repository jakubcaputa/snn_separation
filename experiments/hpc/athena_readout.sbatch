#!/bin/bash -l
## Kierunek 1 — klasyfikator downstream + pojemność pamięci (Athena / Cyfronet)
##
## Wysłanie (dwa eksperymenty, ten sam skrypt):
##   sbatch --array=0-7 athena_readout.sbatch classification
##   sbatch --array=0-3 athena_readout.sbatch capacity
## Po zakończeniu:
##   python analyze_readout.py --in "classification_full_shard*.npz" \
##                             --capacity "capacity_full_shard*.npz"

#SBATCH --job-name=dg-k1
#SBATCH --account=plgdyplomanci7-gpu-a100
#SBATCH --partition=plgrid-gpu-a100
#SBATCH --gpus=1
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32GB
#SBATCH --output=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/k1_%A_%a.out
#SBATCH --error=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/k1_%A_%a.err

set -euo pipefail

EXPERIMENT="${1:-classification}"       # classification | capacity

REPO=/net/tscratch/people/plgjakubcaputa/snn_separation
VENV=/net/tscratch/people/plgjakubcaputa/venvs/snn_sep_venv

SHARD="${SLURM_ARRAY_TASK_ID:-0}"
N_SHARDS="${SLURM_ARRAY_TASK_COUNT:-1}"
JOBID="${SLURM_ARRAY_JOB_ID:-$SLURM_JOB_ID}"

case "${EXPERIMENT}" in
  classification) SCRIPT=run_classification.py ;;
  capacity)       SCRIPT=run_capacity.py ;;
  *) echo "Nieznany eksperyment: ${EXPERIMENT} (użyj: classification | capacity)"; exit 1 ;;
esac

module load Miniconda3/25.7.0-2

# Cache kompilacji Brian2 — osobny katalog na task, na wszelki wypadek.
# UWAGA na dwie rzeczy, bo komentarze w wersjach na Aresa myliły w obie strony:
#   1. Brian2 NIE czyta BRIAN2_CACHE_DIR — taka zmienna nie istnieje. Katalog
#      bierze z Cythona (CYTHON_CACHE_DIR, domyślnie $HOME/.cython).
#   2. W TYM projekcie i tak nic się nie kompiluje: dg_core/circuit.py ustawia
#      prefs.codegen.target = 'numpy', więc cache zostaje pusty. Ustawienie
#      poniżej jest zabezpieczeniem na wypadek zmiany targetu na 'cython',
#      a nie warunkiem poprawności — ostrzeżenie o „losowo padającym jobie"
#      dotyczyło konfiguracji, której tu nie ma.
export CYTHON_CACHE_DIR="/net/tscratch/people/plgjakubcaputa/brian_cache/${JOBID}_${SHARD}"
mkdir -p "${CYTHON_CACHE_DIR}"

export PYTHONIOENCODING=utf-8
export OMP_NUM_THREADS=1

cd "${REPO}/experiments/readout_deferred"

echo "=== ${EXPERIMENT} | $(date) | job ${JOBID} shard ${SHARD}/${N_SHARDS} ==="

"${VENV}/bin/python" "${SCRIPT}" \
    --preset full \
    --n-jobs "${SLURM_CPUS_PER_TASK}" \
    --shard "${SHARD}" \
    --n-shards "${N_SHARDS}"

echo "=== ${EXPERIMENT} shard ${SHARD} zakończony: $(date) ==="
