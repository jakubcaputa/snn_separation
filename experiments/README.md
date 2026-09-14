# experiments/ — właściwy łańcuch eksperymentalny

`interactive_dg.py` w korzeniu repo jest do **oglądania** obwodu (Streamlit,
suwaki, wykresy). Tutaj jest do **liczenia** — bez GUI, z linii poleceń,
z shardingiem pod HPC.

> Stan prac i co blokuje: **`../STATUS.md`**. Hipotezy i eksperymenty:
> `../PLAN_PUBLIKACJI.md` §2.3 i §3.4.

---

## Mapa: eksperyment → hipoteza → folder

Foldery nazywają się tak jak eksperymenty w planie publikacji, żeby nie trzeba
było tłumaczyć numeracji. **Każdy folder odpowiada na jedno pytanie.**

| # | folder | pytanie | testuje | status |
|---|---|---|---|---|
| **E1** | `e1_regime_map/` | **ile** hamowania jest optymalne — czy istnieje okno funkcjonalne | **H1, H2** | działa; wynik wstępny **nie potwierdza H1** (patrz niżej) |
| **E2** | `e2_motif_attribution/` | **który** motyw hamowania niesie separację | który motyw tworzy okno | maszyneria gotowa, wynik wstępny stabilny |
| E3 | — | surrogat ML, indeksy Sobola, sloppiness | — | niezbudowane |
| E4 | — | kontroler homeostatyczny | **H3, H4** | niezbudowane ← **to niesie ciężar publikacji** |
| E5 | — | uogólnienie kontrolera poza reżim strojenia | **H3** (kluczowy test) | niezbudowane |
| E6 | — | skalowanie `N_GC` (kodowanie ekspansyjne) | czy okno przesuwa się z rozmiarem | niezbudowane |
| E7 | — | walidacja na rzeczywistych bodźcach Madara | ground truth | niezbudowane |
| — | `readout_deferred/` | czy DG pomaga odbiorcy downstream | — | **1A zamknięte (negatywne), 1B odłożone** |

Hipotezy w skrócie (pełne brzmienie i warunki obalenia: `../PLAN_PUBLIKACJI.md` §2.3):

- **H1** — separacja ma **optimum przy pośredniej** frakcji aktywnych GC, nie rośnie monotonicznie z hamowaniem
- **H2** — hamowanie mossy cells (`W_FS_HMC`) tworzy reżim pośredni; bez niego okno znika
- **H3** — regulowaną wielkością jest **frakcja aktywnych GC**, a nie średnia częstotliwość ani lokalny E/I
- **H4** — prosta reguła homeostatyczna sama odnajduje punkt pracy znaleziony offline
- **H5** — regulacja przesuwa separację między kodem wzorcowym (NDP) a częstotliwościowym (SF)

H1 i H2 są testowane wstępnie; **H3–H5 są nowe i to one niosą publikację** — a ich
eksperymenty (E4, E5) jeszcze nie istnieją.

> **Skąd wzięły się dawne nazwy `kierunek1_readout` / `kierunek4_motifs`:** z numeracji
> pięciu kierunków badawczych z początku doktoratu. Kierunek 4 = atrybucja motywów
> (dziś E2), kierunek 1 = odbiorca downstream (dziś `readout_deferred/`). Kierunki 2
> (catastrophic forgetting), 3 (neuromorfika) i 5 (DG→CA3) nie mają kodu — ich status
> jest w `../doktorat_plan.md` §8.

---

## Foldery

### `dg_core/` — jedno źródło modelu

Headless port obwodu z `interactive_dg.py`: te same równania Izhikevicza, te same
kanały synaptyczne, kanon częstotliwości z `../dg_params.py`.

| plik | zawartość |
|---|---|
| `params.py` | `DGConfig` — pełna konfiguracja (zamrożona dataclass, nadaje się na klucz cache) |
| `circuit.py` | `simulate()` — jedna próba obwodu GC/FS/HMC |
| `patterns.py` | wzorce o zadanym R_in, klasy z zaszumionymi próbami, spajki PP |
| `metrics.py` | dekorelacja, rzadkość, Shapley, bateria metryk informacyjnych |
| `calibrate.py` | kalibracja do zadanego **punktu pracy** (błona, P(AP), bilans hamowania) |
| `madar_intrinsics.py` | właściwości błony wyciągnięte wprost z adnotacji Madara |
| `viz.py` | wspólna paleta (Okabe–Ito) i styl figur |

⚠️ **`dg_core/` i `interactive_dg.py` muszą trzymać ten sam model.** Zmiana
w obwodzie ma trafić w oba miejsca — inaczej powstaje drugie źródło prawdy
i wyniki eksperymentów przestają odpowiadać temu, co widać w narzędziu.

Kanały istniejące, ale **domyślnie wyłączone** (obwód bez nich jest numerycznie
identyczny z wersją sprzed ich dodania):

- `W_FS_HMC` — hamowanie mossy cells. Bez niego pętla GC→HMC→GC nie ma reżimu
  pośredniego: MC są albo nieistotne, albo uciekają. **To jest zmienna H2.**
- `W_FS_FS` — wzajemne hamowanie interneuronów. Bez niego FS nie mają **żadnego**
  hamowania synaptycznego i strzelają zawyżone ~46 Hz.

### `e1_regime_map/` — czy istnieje okno funkcjonalne (H1, H2)

`run_regime_map.py` zamraża statystykę wejścia i zmienia **siłę hamowania**:
`K_GC` (toniczne) × `W_FS_GC` (fazowe). Główną osią wykresu jest **zmierzona**
frakcja aktywnych GC, bo twierdzenie dotyczy aktywności, a nie parametrów.

⚠️ **Wynik wstępny NIE potwierdza H1.** Separacja rośnie monotonicznie ku ciszy,
maksimum leży na krańcu siatki — to sygnatura artefaktu wyciszenia (pułapka 3),
nie okna. Skrypt sam to wykrywa i mówi wprost. Przed wyciągnięciem wniosków:
szersza siatka i zaostrzona maska ważności.

### `e2_motif_attribution/` — który motyw niesie separację

`run_lesion_grid.py` liczy wszystkie 2³ = 8 lezji FF/FB/MC **na tych samych
wzorcach i tym samym okablowaniu**, więc jedyną zmienną jest obecność motywu.
Z ośmiu liczb wychodzą wartości Shapleya.

Shapley, a nie „włącz/wyłącz", bo FF i FB dzielą wspólne wyjście FS→GC — naiwne
odejmowanie przypisałoby tę samą separację dwa razy.

**E1 i E2 to dwa różne eksperymenty, nie warianty jednego.** E2 zmienia
statystykę wejścia i nie ma żadnej osi hamowania, więc nie może odpowiedzieć na
pytanie, ile hamowania jest optymalne — stąd osobne E1.

### `readout_deferred/` — zamknięte i odłożone

- `run_classification.py` (**1A — ZAMKNIĘTE, wynik negatywny**): „DG poprawia
  klasyfikację liniową" sprawdzone i obalone (raw 0.940 vs dg 0.885). To uczciwy
  wynik uzasadniający przejście na miary informacyjne, nie porażka. Do artykułu
  wchodzi jako jedno zdanie w Discussion. **Nie inwestować więcej.**
- `run_capacity.py` (**1B — ODŁOŻONE**): pojemność pamięci skojarzeniowej; przy
  N_GC=200 kolapsuje do 2–4 wzorców dla wszystkich warunków naraz (podłoga).
  Wymaga N_GC ≥ 2000 na HPC. **Nie traktować obecnych liczb jako wyniku.**

### `hpc/` — SLURM na Ares/PLGrid

`ares_e1_regime_map.sbatch` · `ares_e2_attribution.sbatch` · `ares_readout.sbatch`

Każdy skrypt wspiera `--shard i --n-shards N` → job array; analiza scala shardy
po globie. W `.sbatch` wpisz swój grant PLGrid (`--account`). Skrypty ustawiają
osobny `BRIAN2_CACHE_DIR` na task — bez tego równoległe taski nadpisują sobie
cache kompilacji Brian2 i job losowo pada.

---

## Uruchamianie

Każdy skrypt ma `--preset quick` (sanity check, minuty) i `--preset full`.

```bash
# kalibracja i dane
python -m dg_core.calibrate --preset madar
python -m dg_core.madar_intrinsics

# E1 — okno funkcjonalne (priorytet)
cd e1_regime_map && python run_regime_map.py --preset quick

# E2 — atrybucja motywów
cd e2_motif_attribution
python run_lesion_grid.py --preset quick
python analyze_motifs.py --in results/lesion_grid_quick.npz

# HPC
sbatch --array=0-19 hpc/ares_e1_regime_map.sbatch
sbatch --array=0-49 hpc/ares_e2_attribution.sbatch
```

---

## ⚠️ Zanim uruchomisz cokolwiek nowego

Cztery pułapki, z których każda już raz cicho zepsuła wynik (pełny opis:
`../doktorat_plan.md` §4):

1. **Skalowanie:** `DGConfig.scaled(N)`, nigdy gołe `N_GC=`. Inaczej obwód umiera,
   a dekorelacja pokazuje +0.77 — bo korelacja pustego wektora wynosi 0.
2. **Mossy cells przy domyślnych wagach są martwe** (0.00 Hz). Wniosek o ich roli
   dotyczy wtedy obwodu BEZ nich. Zawsze dwa reżimy: `mc_inert` / `mc_active`.
3. **Separacja czy wyciszenie?** Dekorelacja przy FR→0 to artefakt. Każda analiza
   musi mieć maskę ważności i panel kontrolny częstotliwości.
4. **`K_GC` pełni trzy role naraz** — próg efektywny, potencjał spoczynkowy
   *i* cały budżet hamowania tonicznego. „Zwiększyliśmy hamowanie, podnosząc K"
   znaczy jednocześnie „zmieniliśmy właściwości błony".

Testy regresji (`../tests/`, 17 sztuk) pilnują, żeby domyślna konfiguracja
pozostała bit-w-bit zgodna ze stanem sprzed wrześniowych zmian.
