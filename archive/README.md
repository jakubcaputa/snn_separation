# archive/ — skrypty, które zrobiły swoje

Nic tutaj nie jest częścią bieżącego łańcucha eksperymentów. Te skrypty
wyprodukowały wnioski, na których **nadal stoi model**, więc zostają — żeby dało
się pokazać wyprowadzenie, gdy ktoś o nie zapyta. Same wnioski są w `../STATUS.md` §2.

| plik | co udowodnił | gdzie wynik żyje dzisiaj |
|---|---|---|
| `bifurcation_K.py` | **G_crit = 4 + K** — analitycznie i numerycznie, zgodność co do 0.1 mV | fundament interpretacji K_tonic w całym projekcie |
| `freq_audit.py` | kalibracja wejścia **600 → 400 Hz** (przy 600 Hz GC dawały 16.6 Hz, za gęsto) | `dg_params.py` — jedyne źródło prawdy dla częstotliwości |
| `dg_module3_inh_comparison.py` | porównanie wariantów hamowania, rekalibracja pod 400 Hz | wchłonięte przez `experiments/dg_core/` |
| `explore_data.py` | jak czytać nagrania Axographu przez `neo` | wzorzec dla `dg_core/madar_intrinsics.py`; przyda się przy krzywych f–I |

## Uwagi

- Skrypty zostały przeniesione tutaj z korzenia repo (2026-09). Import `dg_params`
  dostał shim dopinający korzeń do `sys.path`, a `explore_data.py` — poprawkę
  martwej ścieżki bezwzględnej na `../dataset/`. **Wszystkie się uruchamiają.**
- Figury, które z nich powstały, są w `../prezentacja/` (`fig_bifurcation_en.png`,
  `fig_freq_en.png`).
- Czego tu NIE ma: usunięto `debug_*.py` (7 plików roboczych), `visualize_dg*.py`
  (4 generatory figur), jednorazowe eksploratory oraz warianty zastąpione przez
  `experiments/dg_core/` (`dg_microcircuit_brian2.py`, `single_neuron_patsep_nest.py`,
  `single_neuron_patsep_brian2.py`). Są w historii gita, gdyby okazały się potrzebne.
