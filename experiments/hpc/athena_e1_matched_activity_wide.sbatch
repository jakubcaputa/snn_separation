#!/bin/bash -l
## E1″ — SZERSZY SWEEP E1′: R_in × reżim MC × W_FS_GC do 12 + miara czasowa (Athena)
##
## Uruchamiane na plgrid-now (limit: 16 CPU, 1 GPU, 1 h, JEDNO zadanie naraz),
## bo plgrid-gpu-a100 jest zablokowane oknem serwisowym do 2026-10-11. Pełny
## sweep (~45 min) dzielony na 3 shardy wysyłane po kolei:
##   sbatch --export=ALL,SHARD=0,N_SHARDS=3 athena_e1_matched_activity_wide.sbatch
## Następca mapy reżimów: aktywność jest ZADANA (bisekcja po K_GC), a mierzymy
## NADWYŻKĘ separacji ponad null o tej samej rzadkości. Patrz nagłówek
## run_matched_activity.py — tam jest, dlaczego stary E1 nie wystarczył.
##
## Wysłanie — domyślnie JEDEN task, bez job-array:
##   sbatch athena_e1_regime_map.sbatch
##
## Preset `full` to 810 punktów, a każdy to bisekcja (do 14 symulacji) + 4
## pomiarowe — rząd 15 tys. symulacji. Na 16 CPU ~40 min, więc dzielenie
## tego na job-array NIE MA SENSU: Athena rozlicza się w GODZINACH GPU
## (TRESBillingWeights: gpu=1, cpu=0.0625), a każdy dodatkowy task arraya to
## kolejna pełna godzina GPU zapłacona za obliczenie, które GPU nie używa.
## Sharding nadal działa, gdyby siatka kiedyś urosła:
##   sbatch --array=0-3 athena_e1_regime_map.sbatch
##
## Po zakończeniu (scala shardy po globie, rysuje figurę, drukuje werdykt):
##   python analyze_regime_map.py

#SBATCH --job-name=dg-e1pp
#SBATCH --account=plgdyplomanci7-gpu-a100
#SBATCH --partition=plgrid-now
#SBATCH --gpus=1
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32GB
#SBATCH --output=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e1pp_%A_%a.out
#SBATCH --error=/net/tscratch/people/plgjakubcaputa/snn_separation/experiments/hpc/logs/e1pp_%A_%a.err

## Athena nie ma partycji czysto CPU — `plgrid-gpu-a100` wymaga --gpus, więc
## GPU jest tu alokowane wyłącznie dlatego, że kolejka tego żąda. Brian2 liczy
## na CPU i GPU zostanie bezczynne. 16 CPU mieści się w rozliczeniu tego jednego
## GPU (16 × 0.0625 = 1), więc szersze CPU nic by nie kosztowało dopiero powyżej.

set -euo pipefail

REPO=/net/tscratch/people/plgjakubcaputa/snn_separation
VENV=/net/tscratch/people/plgjakubcaputa/venvs/snn_sep_venv

# Skrypt działa i jako pojedynczy job, i jako array — pod `set -u` zmienne
# arraya nie istnieją w tym pierwszym przypadku, więc muszą mieć wartości domyślne.
SHARD="${SHARD:-${SLURM_ARRAY_TASK_ID:-0}}"
N_SHARDS="${N_SHARDS:-${SLURM_ARRAY_TASK_COUNT:-1}}"
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
export OMP_NUM_THREADS=1                # joblib zarządza równoległością, nie BLAS

cd "${REPO}/experiments/e1_regime_map"

echo "=== E1 regime map | $(date) | job ${JOBID} shard ${SHARD}/${N_SHARDS} ==="

# UWAGA: skrypt przyjmuje --jobs / -j, NIE --n-jobs (argparse odrzuciłby --n-jobs).
"${VENV}/bin/python" run_matched_activity.py \
    --preset wide \
    --jobs "${SLURM_CPUS_PER_TASK}" \
    --shard "${SHARD}" \
    --n-shards "${N_SHARDS}"

echo "=== shard ${SHARD} zakończony: $(date) ==="
