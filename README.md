# snn_separation — separacja wzorców w zakręcie zębatym (DG)

Model sieci spajkującej zakrętu zębatego (komórki ziarniste GC, interneurony FS,
mossy cells HMC) w Brian2, z interaktywnym narzędziem Streamlit. Służy do badania,
**co utrzymuje sieć w reżimie, w którym separuje wzorce** — i czy da się tym
sterować automatycznie.

Model jest ograniczany danymi patch-clamp Madara, Ewella i Jonesa (BioStudies
S-BSST219): te same bodźce wejściowe, cztery typy komórek, eksperyment
farmakologiczny przed/po gabazynie.

**Trzy pliki dokumentacji, każdy odpowiada na inne pytanie** — każdy fakt ma jedno
miejsce, pozostałe odsyłają:

| plik | pytanie |
|---|---|
| `README.md` | jak to zainstalować, uruchomić, gdzie co leży |
| [STATUS.md](STATUS.md) | gdzie jestem, co blokuje, jakie są zmierzone wyniki |
| [PLAN_BADAWCZY.md](PLAN_BADAWCZY.md) | hipotezy H1–H5 i plan eksperymentów E1–E7 |

---

## Instalacja

Wymagany Python 3.11+.

```bash
git clone <repo> snn_separation
cd snn_separation

python -m venv snn_sep_venv
snn_sep_venv/Scripts/activate        # Windows
# source snn_sep_venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

Główne zależności: Brian2 2.10, numpy 2.4, scipy, matplotlib 3.10, scikit-learn,
neo 0.14 (odczyt Axographu), streamlit 1.57, pytest.

Dane (`dataset/`) i PDF-y prac (`papers/`) są poza gitem. Dane pobierz
z BioStudies **S-BSST219** i rozpakuj do `dataset/`.

---

## Uruchamianie

```bash
# narzędzie interaktywne (główny produkt)
snn_sep_venv/Scripts/python.exe -m streamlit run interactive_dg.py

# kalibracja punktu pracy
cd experiments
python -m dg_core.calibrate --preset madar
python -m dg_core.madar_intrinsics          # wymaga dataset/

# eksperymenty — każdy ma --preset quick (minuty) i --preset full
cd e1_regime_map        && python run_regime_map.py --preset quick
python analyze_regime_map.py            # E1  — figura + werdykt H1
python run_matched_activity.py --preset quick   # E1′ — wersja poprawiona
python analyze_matched_activity.py      # E1′ — figura + werdykt H1′
cd ../e2_motif_attribution
python run_lesion_grid.py --preset quick
python analyze_motifs.py --in results/lesion_grid_quick.npz
```

Na HPC (Athena/PLGrid) — skrypty `hpc/athena_*.sbatch`:

```bash
cd experiments/hpc
sbatch athena_e1_matched_activity.sbatch        # E1′ — aktualny, ~40 min
sbatch athena_e1_regime_map.sbatch              # E1 stary (wynik negatywny, §3.2)
sbatch --array=0-7 athena_e2_attribution.sbatch
sbatch --array=0-7 athena_readout.sbatch classification
```

Venv na Athenie (raz, przed pierwszym sbatchem) — Brian2 2.10 i numpy 2.4
wymagają Pythona ≥3.11, a moduł `Python/3.10.4` jest za stary, więc interpreter
bierzemy z Miniconzy:

```bash
module load Miniconda3/25.7.0-2
python -m venv $SCRATCH/venvs/snn_sep_venv
$SCRATCH/venvs/snn_sep_venv/bin/pip install -r requirements.txt joblib scipy scikit-learn pytest
```

Każdy skrypt wspiera `--shard i --n-shards N` → job array SLURM; analiza scala
shardy po globie. Grant jest już wpisany (`plgdyplomanci7-gpu-a100`).

⚠️ **Athena nie ma partycji CPU-only.** `plgrid-gpu-a100` wymaga `--gpus`, więc
joby alokują 1 GPU, którego Brian2 nie używa, i **rozliczają się w godzinach GPU**
(`gpu=1`, `cpu=0.0625`). Dlatego liczba tasków w arrayu jest tu dobierana do
kosztu, a nie do dostępnych rdzeni: E1 (`full` = 450 punktów ≈ 2 h rdzenia) mieści
się w JEDNYM tasku na 16 CPU, a 20-taskowy array z wersji na Aresa kosztowałby
20 godzin GPU zamiast jednej. 16 CPU jest „darmowe" — mieści się w rozliczeniu
tego jednego GPU.

⚠️ O cache'u Brian2 dwie rzeczy, bo komentarze w skryptach na Aresa myliły w obie
strony. Po pierwsze **`BRIAN2_CACHE_DIR` nie istnieje** — Brian2 bierze katalog
z Cythona (`CYTHON_CACHE_DIR`, domyślnie `$HOME/.cython`), więc tamto ustawienie
było bezskuteczne. Po drugie **w tym projekcie i tak nic się nie kompiluje**:
`dg_core/circuit.py` ustawia `prefs.codegen.target = 'numpy'`, więc cache zostaje
pusty i ostrzeżenie o „losowo padającym jobie" nie dotyczy tej konfiguracji.
Skrypty ustawiają `CYTHON_CACHE_DIR` na task jako zabezpieczenie na wypadek
przełączenia targetu na `cython`.

### Testy

```bash
snn_sep_venv/Scripts/python.exe -m pytest tests/ -q
```

17 testów: regresja modelu (domyślna konfiguracja musi zostawać bit-w-bit
identyczna) i poprawność kalibracji.

---

## Struktura repozytorium

```
interactive_dg.py          narzędzie Streamlit — tryb pojedynczego neuronu (LIF)
                           i tryb sieci (Izhikevich)
dg_params.py               jedyne źródło prawdy dla częstotliwości wejścia PP
                           (40 włókien × 10 Hz = 400 Hz aggregate)

experiments/               łańcuch eksperymentalny bez GUI — z linii poleceń,
  dg_core/                 z shardingiem pod HPC
  e1_regime_map/
  e2_motif_attribution/
  readout_deferred/
  hpc/

separation_parameters_sweep/   linia LIF pojedynczego neuronu
single_neuron_patsep.py        (jej zależność)

tests/                     regresja modelu i kalibracji
archive/                   skrypty, które zrobiły swoje — patrz archive/README.md
prezentacja/               materiały na spotkania
dataset/                   dane Madara (poza gitem)
papers/                    literatura w PDF (poza gitem)
```

`interactive_dg.py` jest do **oglądania** obwodu (suwaki, wykresy); `experiments/`
do **liczenia**.

### `experiments/dg_core/` — jedno źródło modelu

Headless port obwodu z `interactive_dg.py`: te same równania Izhikevicza, te same
kanały synaptyczne, kanon częstotliwości z `dg_params.py`.

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

Dwa kanały istnieją, ale są **domyślnie wyłączone**, więc obwód bez nich jest
numerycznie identyczny z wersją sprzed ich dodania: `W_FS_HMC` — hamowanie mossy
cells (zmienna hipotezy H2), `W_FS_FS` — wzajemne hamowanie interneuronów, bez
którego FS nie mają żadnego hamowania synaptycznego.

### Foldery eksperymentów

Nazwy folderów odpowiadają eksperymentom E1–E7 z planu badawczego, żeby nie trzeba
było tłumaczyć numeracji. **Każdy folder odpowiada na jedno pytanie.**

| folder | pytanie | testuje |
|---|---|---|
| `e1_regime_map/` | **ile** hamowania jest optymalne — czy istnieje okno funkcjonalne | H1, H2 |
| `e2_motif_attribution/` | **który** motyw hamowania niesie separację | który motyw tworzy okno |
| `readout_deferred/` | czy DG pomaga odbiorcy downstream | 1A zamknięte, 1B odłożone |
| `hpc/` | skrypty SLURM na Ares/PLGrid | — |

Statusy i wyniki: [STATUS.md](STATUS.md) §3. Eksperymenty jeszcze niezbudowane
(E3–E7) i pełne brzmienie hipotez: [PLAN_BADAWCZY.md](PLAN_BADAWCZY.md).

---

## ⚠️ Zanim uruchomisz nowy sweep

Cztery pułapki, z których **każda już raz cicho zepsuła wynik**: skalowanie sieci
przez `scaled(N)` · dwa reżimy mossy cells · separacja czy wyciszenie · potrójna
rola `K_GC`. Opis i konsekwencje: [PLAN_BADAWCZY.md](PLAN_BADAWCZY.md) §3.5.
Przeczytaj, zanim dopiszesz nową siatkę — nie po tym, jak wyniki wyjdą dziwne.

---

## Odtwarzalność

Parametry dodane we wrześniu 2026 mają wartości neutralne (`p_rel = 1.0`,
`delay_jitter_ms = 0.0`, `W_FS_FS = 0.0`, `b_gc = 0.2`), a przy `p_rel ≥ 1.0` kod
bierze gałąź, która nie zużywa ani jednej liczby losowej. Hash spajków domyślnej
konfiguracji jest identyczny ze stanem sprzed tych zmian — **żaden wcześniejszy
wynik nie wymaga przeliczenia.** Pilnują tego testy w [tests/](tests/).

Standard odtwarzalności docelowy dla publikacji (determinizm przebiegów, YAML-e
konfiguracji, warstwy danych na Zenodo, kontener):
[PLAN_BADAWCZY.md](PLAN_BADAWCZY.md) §7.3.

---

## Licencja i atrybucja

Kod: BSD-3-Clause (planowane przy publikacji repo). Dane wejściowe pochodzą
z Madar, Ewell & Jones, *PLOS Computational Biology* 2019 — kod referencyjny na
licencji MIT, nagrania na BioStudies S-BSST219. Surowych nagrań nie
redystrybuujemy.
