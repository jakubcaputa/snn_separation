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
cd ../e2_motif_attribution
python run_lesion_grid.py --preset quick
python analyze_motifs.py --in results/lesion_grid_quick.npz
```

Na HPC (Ares/PLGrid):

```bash
cd experiments
sbatch --array=0-19 hpc/ares_e1_regime_map.sbatch
sbatch --array=0-49 hpc/ares_e2_attribution.sbatch
```

Każdy skrypt wspiera `--shard i --n-shards N` → job array SLURM; analiza scala
shardy po globie. W `.sbatch` wpisz swój grant PLGrid (`--account`).
⚠️ Skrypty ustawiają osobny `BRIAN2_CACHE_DIR` na task — bez tego równoległe taski
nadpisują sobie cache kompilacji Brian2 i job losowo pada.

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
