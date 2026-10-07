#!/bin/bash -l
## E1‴ — TEST POTWIERDZAJĄCY ucieczki częstotliwości z E1″ (STATUS sek. 4.4 pkt 0)
##
## plgrid-now (16 CPU, 1 h, jedno zadanie naraz), bo plgrid-gpu-a100 ma okno
## serwisowe do 2026-10-11. Preset `full` = 1410 punktów w 3 shardach, po kolei:
##   sbatch --export=ALL,SHARD=0,N_SHARDS=3 athena_e1_runaway_confirm.sbatch
##   (kolejne z --dependency=afterany:<poprzedni>)
## Po zakończeniu (scala shardy, figura, werdykt zapisanego testu):
##   python run_runaway_confirm.py --preset full --analyze

#SBATCH --job-name=dg-e1ppp
#SBATCH --account=plgdyplomanci7-gpu-a100
#SBATCH --partition=plgrid-now
#SBATCH --gpus=1
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32GB
#SBATCH --output=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e1ppp_%j.out
#SBATCH --error=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e1ppp_%j.err

## GPU tylko dlatego, że partycja go wymaga — Brian2 liczy na CPU (numpy codegen).

set -euo pipefail

REPO=/net/tscratch/people/plgjakubcaputa/snn_separation
VENV=/net/tscratch/people/plgjakubcaputa/venvs/snn_sep_venv
SHARD="${SHARD:-0}"
N_SHARDS="${N_SHARDS:-1}"

module load Miniconda3/25.7.0-2
export PYTHONIOENCODING=utf-8
export OMP_NUM_THREADS=1

cd "${REPO}/experiments/e1_regime_map"
echo "=== E1‴ runaway confirm | $(date) | job ${SLURM_JOB_ID} shard ${SHARD}/${N_SHARDS} ==="
"${VENV}/bin/python" run_runaway_confirm.py --preset full \
    --jobs "${SLURM_CPUS_PER_TASK}" --shard "${SHARD}" --n-shards "${N_SHARDS}"
echo "=== shard ${SHARD} zakończony: $(date) ==="
