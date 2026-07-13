# Eksperymenty doktoratowe — ścieżka aplikacyjna / ML

Wydzielona baza kodowa dla dwóch kierunków z `prezentacja/doktorat_kierunki.md`.
Nic tutaj nie modyfikuje istniejących skryptów w korzeniu repo — `interactive_dg.py`
i `separation_parameters_sweep/` działają bez zmian.

```
experiments/
  dg_core/            ← wspólny rdzeń: obwód DG bez Streamlita (jedno źródło modelu)
  kierunek4_motifs/   ← który motyw hamowania dominuje separację (lezje + Shapley)
  kierunek1_readout/  ← czy DG realnie pomaga odbiorcy downstream (klasyfikator, pamięć)
  hpc/                ← skrypty SLURM (Ares/Cyfronet, job array)
```

Kolejność zgodna z rekomendacją z `doktorat_kierunki.md`: **najpierw 4** (domyka etap
obserwowalności, szybki publikowalny wynik), **potem 1** (daje narrację „po co to jest").

---

## Rdzeń: `dg_core/`

Headless port obwodu z `interactive_dg.py` — te same równania Izhikevicza, ten sam
podział na kanały synaptyczne, ten sam kanon częstotliwości PP (importowany z
`dg_params.py`, żeby nie powstało drugie źródło prawdy). Dzięki temu wyniki sweepów
odpowiadają temu, co użytkownik widzi w narzędziu, zamiast pochodzić z „innego modelu".

| plik | zawartość |
|---|---|
| `params.py`   | `DGConfig` — pełna konfiguracja obwodu (zamrożona dataclass) |
| `circuit.py`  | `simulate()` — jedna próba obwodu GC/FS/HMC |
| `patterns.py` | wzorce o zadanym R_in; klasy + zaszumione próby; spajki PP |
| `metrics.py`  | dekorelacja, rzadkość, **wartości Shapleya**, interakcje |
| `viz.py`      | wspólna paleta (Okabe–Ito, zwalidowana pod kątem daltonizmu) i styl figur |

**Jedna zmiana względem modelu z `interactive_dg.py`:** dodany kanał `FS→HMC`
(hamowanie NA mossy cells), **domyślnie wyłączony** (`W_FS_HMC = 0.0`). Przy zerowej
wadze synapsa nie powstaje, kanał zostaje na zerze i obwód jest numerycznie
identyczny z oryginałem (zweryfikowane regresyjnie). Po co istnieje — patrz niżej.

---

## Kierunek 4 — który motyw hamowania dominuje

**Pytanie:** przy jakiej statystyce wejścia (R_in, rzadkość, tempo) za separację
odpowiada feedforward, feedback, czy mossy cells?

### Metoda: lezje faktorialne + wartość Shapleya

Dla każdego punktu siatki uruchamiamy **wszystkie 2³ = 8 lezji** (FF/FB/MC on-off) na
**tych samych wzorcach i tej samej sieci** — jedyną zmienną jest obecność motywu.
Z ośmiu wartości dekorelacji liczymy wartość Shapleya każdego motywu.

**Dlaczego Shapley, a nie naiwne „włącz/wyłącz":** FF i FB dzielą wspólną drogę
wyjściową FS→GC, więc ich efekty **nie są addytywne** — proste porównanie „on minus
off" przypisałoby tę samą separację dwa razy. Shapley uśrednia wkład krańcowy po
wszystkich kolejnościach wejścia motywów i jako jedyny podział spełnia

> Σφ_i = v(pełny obwód) − v(brak hamowania)

czyli udziały sumują się **dokładnie** do całej separacji wniesionej przez hamowanie.
Zdanie „FF odpowiada za X% separacji" jest wtedy dosłownie prawdziwe.

### ⚠️ Dlaczego sweep leci w DWÓCH reżimach mossy cells

Przy **domyślnych wagach `interactive_dg.py` mossy cells są sparametryzowane do
nieistotności** — i to trzeba wiedzieć, zanim spojrzy się na jakikolwiek wynik:

1. **Nie strzelają.** `W_GC_HMC = 1 mV` przy `G_crit = 4 + K_HMC = 14 mV` → FR_HMC = 0 Hz.
2. **Nawet zmuszone do strzelania nic nie wnoszą.** Przy `N_HMC=10`, `W_HMC_GC=0.5`,
   `P=0.4` każdy GC dostaje ~4 synapsy MC → przepływ **0.1 mV** wobec **3.6 mV** z FS→GC.

Sweep wyłącznie w tym punkcie odpowiadałby na pytanie z góry ustawione: MC nie mogłyby
wygrać, bo są *odłączone*, a nie dlatego, że statystyka wejścia im nie sprzyja. Dlatego
siatka liczy się w dwóch reżimach:

| reżim | drive (`W_GC_HMC`) | gain (wyjście MC) | brake (`W_FS_HMC`) | co reprezentuje |
|---|---|---|---|---|
| `mc_inert`  | 1  | ×1  | 0 | domyślny `interactive_dg.py` — MC martwe |
| `mc_active` | 16 | ×20 | 2 | MC żywe i ustabilizowane |

**Różnica między mapami dominacji w tych reżimach sama jest wynikiem:** pokazuje, ile
z „dominacji FF/FB" bierze się z biologii, a ile z doboru wag.

### ⚠️ Ścieżka MC jest bistabilna — i dlatego dodano hamulec

Pętla `GC → HMC → GC` jest **czysto pobudzająca** i w obecnym modelu **nie ma hamulca**
(równania HMC nie miały kanału hamującego). Skutek — brak reżimu pośredniego:

| siła ścieżki MC | zachowanie |
|---|---|
| gain ≤ ×10 | MC nieistotne (przepływ < 0.5 mV) |
| gain ≥ ×20 | **runaway**: FR_HMC → 98 Hz, dekorelacja **−0.267** (obwód zaczyna *korelować* wzorce) |
| `N_HMC` = 30 | całkowita ucieczka, 95% GC aktywnych |

W biologii mossy cells dostają silne hamowanie z interneuronów hilusa. Dodanie
`FS→HMC` przywraca reżim fizjologiczny — i **poprawia separację powyżej wartości
domyślnej**:

| `W_FS_HMC` | dekorelacja |
|---|---|
| 0 (obecny model) | **−0.267** (runaway) |
| **2** | **+0.247** ← najlepszy wynik, o **66% lepszy** niż obwód domyślny (+0.149) |
| ≥ 5 | +0.15 (MC znów wyciszone) |

To jest samodzielny, publikowalny wynik: **hamowanie mossy cells nie jest detalem — jest
warunkiem, żeby MC w ogóle mogły wnosić coś do separacji.** Rekomendacja: dodać suwak
`W FS→HMC` do `interactive_dg.py`.

### Wynik wstępny (preset `quick`, do potwierdzenia na pełnej siatce)

```
[mc_inert]   FF 49.9%  ·  FB 50.1%  ·  MC 0.0%        dekorelacja +0.067 → +0.143
[mc_active]  FF 79.2%  ·  FB 115.3% ·  MC −94.5%      dekorelacja +0.067 → +0.244
             FF×FB +0.148 (synergia)  FB×MC +0.301 (synergia)
```

Odczyt: **φ_MC jest ujemne** — mossy cells *same z siebie korelują* wzorce (są
pobudzające, re-ekscytują GC). Ale ich interakcje z hamowaniem są silnie **synergiczne**.
MC to motyw **warunkowy**: szkodzą samotnie, a w parze z hamowaniem podnoszą separację
najbardziej ze wszystkich motywów. (Udziały > 100% i ujemne są matematycznie poprawne —
sumują się do 100%, bo Σφ = v(pełny) − v(brak).)

### Uruchomienie

```bash
python run_lesion_grid.py --preset quick          # ~2 min, sanity check
python run_lesion_grid.py --preset full -j 14     # pełna siatka lokalnie
python analyze_motifs.py  --in lesion_grid_full.npz
```

Figury: mapa dominacji, profile Shapleya, interakcje, **panel kontrolny** (czy to na
pewno separacja, a nie zwykłe wyciszenie sieci — dekorelacja przy FR→0 byłaby
artefaktem, nie obliczeniem).

---

## Kierunek 1 — czy DG realnie pomaga odbiorcy downstream

**Pytanie:** czy separacja typu DG poprawia rozróżnianie skorelowanych/zaszumionych
wejść w zadaniu downstream? To jest „hak ML" i najmocniejsza narracja doktoratu:
mechanizm biologiczny → **mierzalna korzyść**.

### 1A — klasyfikator liniowy (`run_classification.py`)

Cztery warunki. Trzy z nich to **kontrole, bez których wynik byłby niepublikowalny**:

| warunek | co testuje |
|---|---|
| `raw` | baseline „bez DG" — te same spajki PP, ten sam szum Poissona, ta sama wymiarowość. **Uczciwy, nie wyidealizowany.** |
| `dg` | pełny obwód |
| `dg_noinh` | GC z wyłączonym hamowaniem → czy pracę wykonuje **obwód**, czy sama nieliniowość progowa neuronu? |
| `random` | losowa projekcja + k-WTA, **rzadkość dopasowana do DG** → czy liczy się **struktura DG**, czy wystarczy dowolne rzadkie kodowanie? |

### ⚠️ Wynik jest NEGATYWNY i ODPORNY — to informacja, nie porażka

```
raw 0.940  ·  dg 0.885  ·  dg_noinh 0.935  ·  random 0.885
Δ acc (DG − raw) = −0.054
```

**DG pogarsza dokładność klasyfikatora liniowego.** Powód jest strukturalny: przy
`T=600 ms` aktywny GC dostaje ~240 spajków PP, więc wektor `raw` jest praktycznie
**bezszumowy** — klasyfikator czyta z niego klasę bez trudu (0.94). Nie ma zapasu, a DG
jako transformacja **stratna** może tylko odjąć informację.

**Hipoteza ratunkowa została sprawdzona i OBALONA.** Zakładałem, że krótkie okno odczytu
(mało spajków → `raw` przestaje być bezszumowe) stworzy reżim, w którym DG wygrywa.
Sonda po siatce trudności (8 klas, poziom przypadku 0.125):

| T [ms] | R_in | szum | raw | DG | Δ(DG−raw) |
|---|---|---|---|---|---|
| 600 | 0.90 | 0.30 | 0.544 | 0.362 | **−0.181** |
| 150 | 0.90 | 0.30 | 0.559 | 0.284 | **−0.275** |
| 60  | 0.90 | 0.30 | 0.466 | 0.166 | **−0.300** |
| 600 | 0.98 | 0.60 | 0.116 | 0.122 | +0.006 (obie na poziomie przypadku) |

Skracanie okna **nie pomaga DG — szkodzi mu jeszcze bardziej**. Tam gdzie baseline ma
zapas (R_in=0.90), DG wyraźnie przegrywa; tam gdzie zadanie jest trudne (R_in≥0.95),
wszystko siedzi na poziomie przypadku i nie ma czego mierzyć.

**Uczciwy wniosek: w tym modelu i przy tych punktach pracy hipoteza „DG poprawia odczyt
liniowy" NIE broni się.** To jest zgodne ze znanym, choć często przemilczanym faktem:
separacja wzorców nie poprawia liniowej rozróżnialności, gdy wejście i tak jest liniowo
separowalne. DG kupuje coś innego — odporność odbiorcy **ograniczonego pojemnością**
(pamięć skojarzeniowa, 1B) — i tam należy szukać metryki, nie w accuracy.

**Co to znaczy dla doktoratu.** Narracja „DG jako warstwa wstępna poprawia klasyfikację"
w obecnej formie się nie obroni i lepiej wiedzieć to teraz niż po napisaniu rozdziału.
Do rozważenia, zanim uzna się kierunek 1 za zamknięty:
1. **Metryka pojemnościowa zamiast accuracy** (1B) — to tam DG ma teoretyczną przewagę.
2. **Odbiorca uczony lokalnie / o ograniczonej pojemności**, nie regresja logistyczna
   o pełnym rzędzie, która sama nadrabia brak separacji.
3. **Kierunek 2 (catastrophic forgetting)** — dekorelacja pomaga przy *interferencji
   sekwencyjnej*, a nie przy jednorazowej klasyfikacji. To może być właściwy hak ML.

### 1B — pojemność pamięci skojarzeniowej (`run_capacity.py`)

Sieć atraktorowa z regułą **kowariancyjną Tsodyksa–Feigelmana** (klasyczna reguła Hebba
±1 załamuje się dla rzadkich wzorców — wszystko zbiega do jednego atraktora) i dynamiką
**k-WTA** (utrzymuje stałą rzadkość; bez tego trzeba by stroić próg osobno w każdym
warunku, co samo zaburzyłoby porównanie).

**Pojemność** = największe P, przy którym średnia jakość odtworzenia (Jaccard) ≥ 0.90.
Oś główna: **siła hamowania `W FS→GC`** — czyli metryka odpowiadająca wprost na pytanie
„po co jest hamowanie".

**Pułapka, w którą wpadłem i którą warto znać.** Pierwsza wersja binaryzowała wzorce
przez top-k. Wektor `raw` jest niemal binarny (400 Hz aktywne vs 40 Hz tło), więc
wszystkie ~50 aktywnych jednostek ma tę samą częstotliwość nominalną — wymuszenie
top-k=20 kazało wybrać 20 z 50 **remisów**, a rozstrzygał je czysty jitter Poissona.
To losowo przetasowywało wzorce, **sztucznie dekorelowało baseline** i dawało `raw`
przewagę, której nie ma. Metryka główna używa teraz progu w połowie zakresu („kod
naturalny", własna rzadkość reprezentacji), a top-k został jako *kontrola* rzadkości.

**Status: punkt pracy wymaga kalibracji — nie traktować obecnych liczb jako wyniku.**
Przy `N_GC=200` rzadki kod DG ma tylko ~15 aktywnych jednostek, wzorce są z założenia
skorelowane, i pojemność Hopfielda kolapsuje do 2–4 wzorców dla **wszystkich** warunków
naraz — czyli siedzimy na podłodze i niczego nie różnicujemy. Prawdziwe DG→CA3 czerpie
przewagę z ogromnej ekspansji (10⁶ GC). Do zrobienia na HPC: większe `N_GC` (≥ 2000,
patrz niżej o skalowaniu) i dopiero wtedy odczyt krzywych degradacji.

### Uruchomienie

```bash
python run_classification.py --preset quick
python run_capacity.py       --preset quick
python analyze_readout.py --in classification_quick.npz --capacity capacity_quick.npz
```

---

## ⚠️ Skalowanie sieci — `DGConfig.scaled(N_GC)`, nigdy `N_GC=` wprost

Zanim odpali się cokolwiek dużego na HPC: **`DGConfig(N_GC=800)` cicho zabija obwód.**
Wyjście DG jest wtedy PUSTE (0% aktywnych GC), a metryki wyglądają na policzone —
dekorelacja pokazuje nawet `+0.77`, bo korelacja pustego wektora wynosi 0. Klasyczny
wynik-widmo.

Dwie rzeczy muszą się zgadzać naraz:

1. **Proporcje populacji** GC:FS:HMC — inaczej garstka interneuronów wchodzi w saturację.
2. **Liczba wejść na neuron (in-degree)** — każdy GC dostaje `P_FS_GC × N_FS` synaps
   hamujących, więc przy 4× większej populacji FS hamowanie na GC rośnie **4×**, podczas
   gdy pobudzenie PP (1:1) zostaje bez zmian. Prawdopodobieństwa połączeń trzeba więc
   skalować **odwrotnie** do rozmiaru populacji źródłowej.

`DGConfig.scaled(N)` robi jedno i drugie. Zweryfikowane:

| N_GC | N_FS | P_FS→GC | in-degree | aktywnych GC | dekorelacja |
|---|---|---|---|---|---|
| 200 | 20 | 0.500 | 10.0 | 0.220 | +0.149 |
| 400 | 40 | 0.250 | 10.0 | 0.200 | +0.231 |
| 800 | 80 | 0.125 | 10.0 | 0.203 | **+0.296** |

Efekt uboczny wart uwagi: **separacja rośnie z rozmiarem sieci** (+0.149 → +0.296), czyli
dokładnie tak, jak przewiduje teoria kodowania ekspansyjnego. To jest samodzielny wynik
do policzenia porządnie na HPC — i najmocniejszy argument, żeby liczyć duże `N_GC`.

---

## HPC (Cyfronet / Ares)

Wszystkie skrypty wspierają sharding (`--shard i --n-shards N`) → job array SLURM.
Wyniki lecą do osobnych plików NPZ, a skrypty analizy **scalają shardy po glob-ie**.

```bash
# jednorazowo:
python -m venv $SCRATCH/dgvenv
$SCRATCH/dgvenv/bin/pip install brian2 numpy scipy matplotlib scikit-learn joblib

cd experiments/hpc
sbatch --array=0-49 ares_kierunek4.sbatch
sbatch --array=0-39 ares_kierunek1.sbatch classification
sbatch --array=0-19 ares_kierunek1.sbatch capacity

# po zakończeniu:
cd ../kierunek4_motifs && python analyze_motifs.py --in "lesion_grid_full_shard*.npz"
```

W `.sbatch` trzeba wpisać **swój grant PLGrid** (`--account`). Skrypty ustawiają osobny
`BRIAN2_CACHE_DIR` na task — bez tego równoległe taski nadpisują sobie cache kompilacji
Brian2 i job losowo pada.

Koszt: ~1.3 s na symulację Brian2 (N_GC=200, T=600 ms, target `numpy`).
Pełna siatka kierunku 4 to ~35 000 symulacji.

---

## Otwarte kwestie

**Kierunek 4 (mocny — do domknięcia):**
1. **Suwak `W FS→HMC` w `interactive_dg.py`** — bez hamowania na MC ich ścieżka jest
   bezużyteczna albo niestabilna; z nim daje najlepszą separację w całym badaniu (+0.247).
2. **Kalibracja reżimu MC do danych.** Wybór `mc_active` (drive=16, gain=×20) jest na
   razie arbitralny — trzeba go zakotwiczyć w literaturze (Scharfman 2016: netto wpływ
   MC na GC jest przeważnie *hamujący*, przez napędzanie interneuronów).
3. **Porównanie z danymi Madar et al.** — w repo jest `dataset/`; kierunek 4 obiecuje
   falsyfikowalne przewidywania i to naturalny następny krok.
4. **Separacja vs rozmiar sieci** — zależność +0.149 → +0.296 (N=200→800) policzyć
   porządnie; to test teorii kodowania ekspansyjnego.

**Kierunek 1 (wymaga decyzji — obecna forma się nie broni):**
5. Hipoteza „DG poprawia klasyfikację liniową" została **sprawdzona i obalona** (patrz
   wyżej). Zanim pójdzie do rozdziału, trzeba wybrać jedno:
   - przenieść ciężar na **metrykę pojemnościową** (1B) przy dużym `N_GC`,
   - albo zmienić odbiorcę na **ograniczony pojemnością / uczony lokalnie**,
   - albo przejść na **kierunek 2 (catastrophic forgetting)**, gdzie dekorelacja działa
     przeciw *interferencji sekwencyjnej* — to prawdopodobnie właściwszy hak ML.
6. **Punkt pracy pamięci wymaga kalibracji** — przy `N_GC=200` pojemność siedzi na
   podłodze (2–4 wzorce) dla wszystkich warunków naraz, więc nic nie różnicuje.
