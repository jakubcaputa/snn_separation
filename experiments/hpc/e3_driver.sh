#!/bin/bash
# E3 — sterownik łańcucha na plgrid-now (limit: jedno zadanie naraz, także w kolejce).
# Bierze pierwszą linię z e3_queue.txt (kroki rozdzielone ';'), wysyła athena_e3_now.sbatch,
# czeka na koniec, zapisuje stan w e3_driver.log i usuwa linię. Kolejkę można edytować w trakcie.
cd "$(dirname "$0")"
Q=e3_queue.txt
while [ -s "$Q" ]; do
  STEPS=$(head -n1 "$Q")
  JID=$(sbatch --parsable --export=ALL,STEPS="$STEPS" athena_e3_now.sbatch 2>>e3_driver.log)
  if [ -z "$JID" ]; then echo "$(date +%T) submit failed, retry in 60s" >> e3_driver.log; sleep 60; continue; fi
  echo "$(date +%T) submitted $JID: $STEPS" >> e3_driver.log
  sed -i '1d' "$Q"
  while squeue -j "$JID" -h 2>/dev/null | grep -q .; do sleep 30; done
  echo "$(date +%T) finished $JID: $(sacct -j "$JID" -n -X -o State,Elapsed | head -1)" >> e3_driver.log
done
echo "$(date +%T) queue empty" >> e3_driver.log
