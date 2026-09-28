#!/bin/bash -l
## E2 — sweep lezji + atrybucja Shapleya (Athena / Cyfronet, PLGrid)
##
## Wysłanie:
##   sbatch --array=0-7 athena_e2_attribution.sbatch
## Po zakończeniu:
##   python analyze_motifs.py --in "lesion_grid_full_shard*.npz"
##
## Dlaczego 8 shardów, a nie 50 jak w wersji na Aresa: siatka `full` to
## 540 punktów × 2 reżimy × wszystkie koalicje motywów × 4 wzorce, czyli rząd
## 10^4-10^5 symulacji Brian2 (~80 godzin RDZENIA). Na 8 × 16 CPU schodzi to
## w ~40 min na task. Athena rozlicza GODZINY GPU (gpu=1, cpu=0.0625), więc
## 50 tasków kosztowałoby 50 godzin GPU zamiast 8 — za tę samą pracę na CPU.

#SBATCH --job-name=dg-e2
#SBATCH --account=plgdyplomanci7-gpu-a100
#SBATCH --partition=plgrid-gpu-a100
#SBATCH --gpus=1
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32GB
#SBATCH --output=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e2_%A_%a.out
#SBATCH --error=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e2_%A_%a.err

set -euo pipefail

REPO=/net/tscratch/people/plgjakubcaputa/snn_separation
VENV=/net/tscratch/people/plgjakubcaputa/venvs/snn_sep_venv

SHARD="${SLURM_ARRAY_TASK_ID:-0}"
N_SHARDS="${SLURM_ARRAY_TASK_COUNT:-1}"
JOBID="${SLURM_ARRAY_JOB_ID:-$SLURM_JOB_ID}"

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

cd "${REPO}/experiments/e2_motif_attribution"

echo "=== E2 lesion grid | $(date) | job ${JOBID} shard ${SHARD}/${N_SHARDS} ==="

"${VENV}/bin/python" run_lesion_grid.py \
    --preset full \
    --n-jobs "${SLURM_CPUS_PER_TASK}" \
    --shard "${SHARD}" \
    --n-shards "${N_SHARDS}"

echo "=== shard ${SHARD} zakończony: $(date) ==="
