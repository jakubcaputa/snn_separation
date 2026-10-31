#!/bin/bash -l
## Kalibracja ex vivo — fragment siatki na plgrid-gpu-a100 (równolegle z łańcuchem plgrid-now).
##   sbatch --export=ALL,CHUNK=0,NCHUNKS=8 athena_calib_grid.sbatch
## Punkty już policzone (results/grid/pt_*.json) są pomijane, więc fragmenty mogą się
## nakładać z zadaniami z e3_queue.txt bez szkody.
#SBATCH --job-name=dg-calib
#SBATCH --account=plgdyplomanci8-gpu-a100
#SBATCH --partition=plgrid-gpu-a100
#SBATCH --gpus=1
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32GB
#SBATCH --output=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/calib_%j.out
#SBATCH --error=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/calib_%j.err
set -euo pipefail
VENV=/net/tscratch/people/plgjakubcaputa/venvs/snn_sep_venv
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1
cd /net/tscratch/people/plgjakubcaputa/snn_separation/experiments
"${VENV}/bin/python" -m calib_exvivo.grid --chunk "${CHUNK}" --n-chunks "${NCHUNKS}" --jobs 16
