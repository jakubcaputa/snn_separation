# Eksperymenty doktoratowe

Pełna dokumentacja (stan wyników, pułapki modelu, plan działań, HPC) została
scalona w jeden centralny dokument: **`../doktorat_plan.md`** (korzeń repo;
plik lokalny, poza gitem).

Mapa kodu:

```
experiments/
  dg_core/            ← wspólny rdzeń: obwód DG bez Streamlita (jedno źródło modelu)
  kierunek4_motifs/   ← lezje faktorialne + Shapley (run_lesion_grid.py, analyze_motifs.py)
  kierunek1_readout/  ← klasyfikator + pojemność (run_classification.py, run_capacity.py)
  hpc/                ← skrypty SLURM (Ares/Cyfronet, job array)
```

Zanim uruchomisz cokolwiek nowego, przeczytaj w `doktorat_plan.md` sekcję
**„⚠️ Trzy pułapki modelu"** — `DGConfig.scaled(N)` zamiast gołego `N_GC=`,
dwa reżimy mossy cells, kontrola „separacja czy wyciszenie".
