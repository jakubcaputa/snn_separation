# E3 — plan z 2026-10-12 i implementacja E3.0 (archiwum)

*Przeniesione 2026-10-31 z README.md bez zmian treści. Historyczne: pierwotna motywacja, plan modelu i eksperymentów, decyzje Q1–Q9, implementacja i zmiany po E3.0. Aktualny opis modelu: README.md sek. 6.*

## 1. Pytanie i motywacja

W `snn_separation` zmierzyliśmy, że w obwodzie DG zmienną dominującą jest
**odsetek aktywnych komórek ziarnistych** `f`, a hamowanie toniczne `K_GC` ustawia go
jednym skalarem (próg `G_crit = 4 + K`). Hamowanie fazowe przy wyrównanym `f`
nie zmienia separacji (STATUS sek. 3.4), a miara dekorelacji rośnie aż do ciszy
(sek. 3.3), więc nie mówi, ile rzadkości jest *użyteczne*.

E3 zamienia to w pytanie o funkcję:

> **Czy sterowanie gęstością kodu (`K`) sygnałem nowości zmniejsza zapominanie
> bardziej niż ta sama średnia gęstość ustawiona na stałe?**

Uczciwa motywacja (za `ml_paper.md` sek. 7.3): nie „DG świetnie separuje, więc go
skopiujmy”, tylko *„zmierzyliśmy, że rzadkość jest tu zmienną dominującą — uczyńmy
ją zmienną sterowaną i sprawdźmy, czy to pomaga w uczeniu”*.

### Dwa czynniki trzecie

| | **B — nagroda** | **A — nowość** |
|---|---|---|
| sygnał | `R = ±1` po odpowiedzi czytnika | nowość `N` (błąd / niepewność czytnika) |
| działa na | **czy** zmienić wagi czytnika | **ile** neuronów warstwy DG koduje obraz, czyli **gdzie** nauka zostawia ślad |
| biologia | dopamina (DAN → KC–MBON u muszki) | noradrenalina / ACh → toniczne GABA w DG |
| w kodzie | reguła czytnika `Δw = η·R·e` | regulator `N → f_cel → K` |

---

---

## 3. Model

```
 obraz 28×28            warstwa „DG” (stała, losowa)          czytnik (uczony)
 784 wejścia   ──────►  N_DG = 2000 neuronów            ────►  10 neuronów
 Poisson, 0–50 Hz       każdy widzi FAN = 30 losowych          Δw = η · R · e
 T kroków               pikseli (połączenia stałe)             R = ±1 (czynnik B)
                        dv/dt = … + I_in − K                    odpowiedź = argmax
                        K: jeden skalar dla całej warstwy        liczby impulsów
                        (opcj.) pula FS: hamowanie fazowe
                                ▲
                 regulator: N → f_cel → K   (czynnik A)
```

**Warstwa DG się nie uczy.** Uczy się tylko czytnik. Tak działa ciało grzybkowate
muszki (Kenyon → MBON) i tak najłatwiej oddzielić rolę kodu od roli reguły uczenia.
Plastyczna warstwa DG (R-STDP w warstwie ekspansji, jak w `ml_paper.md` sek. 6) to
osobny, późniejszy etap (sek. 7, pytanie Q3).

| element | ustawienie wyjściowe | uwagi |
|---|---|---|
| wejście | Poisson, jasność × 50 Hz, `T` = 100 kroków po 1 ms | `T` do potwierdzenia na danych |
| neuron DG | **Izhikevich jak w `dg_core`** (GC: a,b,c,d = 0.02, 0.2, −65, 6), `K` w równaniu napięcia | ciągłość z `snn_separation`: próg `4 + K` w formie zamkniętej; alternatywa LIF — Q1 |
| fan-in | 30 losowych pikseli, wagi dodatnie, stałe | odpowiednik PP→GC; normalizacja wag do ustalenia w E3.0 |
| hamowanie fazowe | pula 20 FS, GC→FS→GC, waga `W_FS_GC` | tylko w E3.2; domyślnie wyłączone |
| czytnik | 10 neuronów LIF, wagi 2000×10, start losowy mały | wyjście = neuron z największą liczbą impulsów |
| reguła czytnika | R-STDP per-sample: ślad `e_ij` z koincydencji pre×post w oknie `T`, aktualizacja na końcu prezentacji | ślad jest zerem dla cichego neuronu DG, więc jego wagi się nie zmieniają |
| odniesienie górne | regresja logistyczna / reguła delta na tych samych kodach DG | oddziela jakość kodu od słabości R-STDP |

**Implementacja: PyTorch na GPU, nie Brian2.** 60 000 obrazów × dziesiątki warunków ×
ziarna jest poza zasięgiem Brian2. `dg_core` zostaje źródłem prawdy dla parametrów
neuronu i dla procedury bisekcji; E3 ma własny, wektoryzowany symulator warstwy.
Test zgodności: przy tym samym wejściu i `K` neuron Izhikevicha w torch odpala tak
samo jak w `dg_core` (tolerancja do ustalenia).

⚠️ Venv `snn_sep_venv` **nie ma torch** — trzeba go doinstalować albo użyć osobnego
środowiska (Q6).

### Definicja `f`

`f` = odsetek z `N_DG` neuronów, które wysłały **co najmniej jeden impuls podczas
prezentacji jednego obrazu**. Raportujemy rozkład po obrazach (średnia, kwartyle),
nie tylko średnią: lekcja z E1″ — iloraz wielkości z różnych prób kłamie, więc `f`
liczymy per obraz.

---

## 4. Kalibracja i regulator `K`

### 4.1 Tablica `K(f)` (przed treningiem)

Bisekcja po `K` (ta sama logika co `dg_core.calibrate.solve_k_gc_for_active_fraction`)
dla `f ∈ {1, 2, 5, 10, 20, 50%}`, uśredniona po 1000 obrazach kalibracyjnych
spoza zbioru testowego. Wynik: monotoniczna tablica `K_tab(f_tab)`, zapisana w
`results/` i używana przez wszystkie warunki.

### 4.2 Sygnał nowości `N` (per obraz)

| wariant | wzór | uwagi |
|---|---|---|
| `err` | `N = 1` gdy `R = −1`, inaczej 0 | najprostszy |
| `unc` ⭐ | `N = 1 − (s₁ − s₂)/(s₁ + ε)`, `s₁, s₂` = liczby impulsów dwóch najaktywniejszych wyjść | działa też przy trafieniu „na styk” |
| `rpe` | `N = |R − R̄|`, `R̄` = średnia krocząca nagrody | standard RL |

Wygładzanie: `N̄ ← N̄ + (N − N̄)/τ_N`, `τ_N` ∈ {20, 50, 100} obrazów.
**Regulator nie dostaje informacji o granicach zadań** — sam wykrywa zmianę po
wzroście nowości.

### 4.3 Od nowości do `K`

```
f_cel = f_gęsty − (f_gęsty − f_rzadki) · N̄          np. f_gęsty = 20%, f_rzadki = 5%
K     = interp(f_cel, f_tab, K_tab)  [+ K_corr]
K_corr ← K_corr + η_K · (f_zmierzone − f_cel)        (opcjonalnie, wariant całkujący)
```

`K` jest stałe w trakcie jednego obrazu i zmienia się przed następnym (przyczynowo).
Granice: `K ∈ [K(50%), K(1%)]`.

**Czego nie robimy:** progu ustawianego osobno dla każdego obrazu tak, żeby `f`
było dokładnie równe `f_cel` — to globalne k-WTA, inny mechanizm, który nie zachowuje
własności „rzadki kod ⊂ gęsty kod” między obrazami. Może być co najwyżej warunkiem
porównawczym (`kwta_matched`).

### 4.4 `K` przy teście

Stałe `K = K(f_gęsty)` we wszystkich warunkach. Test sprawdza wtedy, czy wagi
nauczone na rzadkim kodzie działają na gęstym — przy hamowaniu tonicznym rzadki kod
obrazu jest podzbiorem gęstego (globalny próg odcina najsłabiej pobudzone neurony).

---

## 5. Eksperymenty

### E3.0 — sanity (brama do reszty)

1. Zgodność neuronu torch z `dg_core` (to samo wejście → te same impulsy w tolerancji).
2. Kalibracja trafia w `f` (błąd < 1 pp dla każdego poziomu).
3. Czytnik R-STDP uczy się na pełnym MNIST przy `f = 10%` wyraźnie powyżej losowości;
   odniesienie górne (regresja logistyczna na kodach) podaje sufit.

**Brama:** jeśli 3. nie przechodzi po rozsądnym strojeniu `η` i `T`, nie idziemy
dalej — najpierw naprawić regułę czytnika.

### E3.1 — statyczne `f` (tylko czynnik B) → H-E3a

| oś | wartości |
|---|---|
| `f` | 1, 2, 5, 10, 20, 50% (przez `K_tab`) |
| kod | DG (próg + `K`), losowa projekcja o tym samym `f` (null z STATUS sek. 3.5), surowe piksele |
| czytnik | R-STDP; regresja logistyczna jako sufit |
| ziarna | 5 (sieć + kolejność danych) |

Mierzymy dokładność testową i — na tych samych kodach — `dec = r_in − r_out`.
**Kluczowa figura:** dokładność(`f`) i `dec`(`f`) na jednej osi `f`.

### E3.2 — hamowanie fazowe przy wyrównanym `f` → H-E3b

`f` ∈ {5, 20%} ustawione bisekcją po `K` przy każdym `W_FS_GC` ∈ {0, 1, 2, 3, 5};
5 ziaren. Dokładność vs `W_FS_GC`. Funkcjonalny odpowiednik E1′ (STATUS sek. 3.4).

### E3.3 — Split-MNIST, sterowanie nowością → H-E3c, H-E3d ⭐

Zadania po kolei: 0/1 → 2/3 → 4/5 → 6/7 → 8/9, wspólny czytnik 10-klasowy
(scenariusz class-incremental — Q5), każde zadanie przez ustaloną liczbę epok.

| warunek | `K` | `η` czytnika | po co |
|---|---|---|---|
| `fixed_dense` | stałe, `f = 20%` | stałe | odniesienie |
| `fixed_sparse` | stałe, `f = 5%` | stałe | odniesienie |
| `mod_novelty` ⭐ | z regulatora (sek. 4) | stałe | **nasza propozycja** |
| `fixed_matched` ⭐ | stałe, `f` = **średnie zrealizowane `f`** z `mod_novelty` tego samego ziarna | stałe | **null o dopasowanej rzadkości** — bez niego reszta nie ma wartości dowodowej |
| `3f_lr` | stałe, `f` jak w `fixed_matched` | `η · (1 + c·N̄)` | klasyczny trzeci czynnik na tempo uczenia (H-E3d) |
| `3f_both` | z regulatora | `η · (1 + c·N̄)` | czy efekty się sumują |
| `oracle_boundary` | podnoszone na znanej granicy zadania | stałe | górna granica dla detekcji nowości |
| `mod_novelty_inv` | z regulatora, **odwrócony kierunek**: nowość → gęstszy kod | stałe | test kierunku (sek. 10, Pérez-Montoyo 2026) |
| `kwta_fly` | stałe k-WTA (top-`f` neuronów per obraz), reguła jak w FlyModel | — | odniesienie do najbliższej pracy (FlyModel) |
| `fixed_matched_inv` | stałe, `f` = średnie zrealizowane `f` z `mod_novelty_inv` | stałe | null dla wariantu odwróconego (dodane 2026-10-13, sek. 6a) |

10 ziaren. `fixed_matched` i `3f_lr` liczone **po** `mod_novelty`, bo potrzebują
jego średniego `f` (to samo ziarno sieci i kolejności danych).

**Metryki** (wszystkie per ziarno):
- `ACC` — średnia dokładność na wszystkich zadaniach po ostatnim zadaniu;
- `BWT` — zapominanie: średni spadek dokładności zadania *i* od chwili jego nauki do końca;
- krzywe uczenia (dokładność po każdym zadaniu);
- **nakładanie kodów między zadaniami** przy tym samym `f` (część wspólnych aktywnych neuronów) — sprawdza mechanizm, nie tylko wynik;
- przebieg `N̄`, `f`, `K` w czasie (czy regulator reaguje na granice zadań).

---

---

## 7. Kolejność, bramki i koszt

| krok | zakres | brama |
|---|---|---|
| 0 | prior art: neuromodulacja pobudliwości w SNN, homeostaza rzadkości, XdG / Active Dendrites (`ml_paper.md` sek. 3, 7) | jeśli pomysł już jest opublikowany — przepozycjonować przed kodem |
| 1 | E3.0 sanity | czytnik uczy się na pełnym MNIST |
| 2 | E3.1 + E3.2 | — (wynik wartościowy niezależnie od E3.3) |
| 3 | E3.3, jedno ziarno, prototyp | regulator reaguje na granice zadań |
| 4 | E3.3 pełne (10 ziaren) | kryterium z sek. 6 |
| 5 | potwierdzenie na nowych ziarnach | — |
| później | plastyczna warstwa DG; N-MNIST / Split-CIFAR; wariant dwufazowy (zapis/przywoływanie, Hasselmo) | — |

Koszt orientacyjny (do weryfikacji w E3.0): warstwa 2000 neuronów × `T` = 100 kroków
na GPU, wsadowo — minuty na epokę MNIST. E3.3: 7 warunków × 10 ziaren × 5 zadań.
Athena: rozliczenie w godzinach GPU; tu GPU jest faktycznie wykorzystywane.

---

## 8. Planowana struktura folderu

```
e3_sparsity_third_factor/
  README.md            ten plan
  model.py             warstwa DG (Izhikevich/LIF w torch, K, opcj. FS), czytnik, R-STDP
  calibrate.py         bisekcja K → tablica K(f); test zgodności z dg_core
  controller.py        nowość (err / unc / rpe), N → f_cel → K, wariant całkujący
  tasks.py             MNIST, Split-MNIST, kolejność danych per ziarno
  run_static.py        E3.0, E3.1, E3.2 (--preset quick / full, sharding)
  run_split.py         E3.3 (warunki z sek. 5, sharding per warunek × ziarno)
  analyze.py           ACC, BWT, nakładanie kodów, kryteria z sek. 6
  results/
experiments/hpc/athena_e3_*.sbatch
tests/test_e3_*.py     zgodność neuronu z dg_core, kalibracja, regulator
```

Importy z `snn_stdp_vs_surrogate_gradient` — tylko jeśli to oszczędzi pracę i tylko
do odczytu (Q7). Dane MNIST: własny loader (`torchvision`) wskazujący na istniejący
katalog z danymi albo nowa kopia.

---

## 9. Decyzje (2026-10-12)

| # | pytanie | decyzja |
|---|---|---|
| Q1 | neuron warstwy DG | **oba typy**: Izhikevich (jak `dg_core`) i LIF — dodatkowa oś we wszystkich eksperymentach |
| Q2 | czytnik | **oba**: R-STDP jako główny, reguła delta jako drugi czytnik; regresja logistyczna jako sufit |
| Q3 | warstwa DG | **stała** w E3; plastyczna jako następny etap |
| Q4 | sygnał nowości | `unc` główny, `rpe` wariant |
| Q5 | scenariusz | **class-incremental** |
| Q6 | środowisko | **doinstalować torch** do `snn_sep_venv` (testy regresji `dg_core` uruchomić po instalacji) |
| Q7 | kod | **własny** (koder Poissona, R-STDP, reguła delta) — bez importów z repo STDP |
| Q8 | publikacja | odłożone — najpierw eksperymenty |
| Q9 | `f_gęsty` / `f_rzadki` | po E3.1 (domyślnie: maksimum dokładności i ~4× mniej) |

Przed kodem: przegląd literatury (krok 0, sek. 7) — wynik w sek. 10.

## 9a. Pytania w pierwotnym brzmieniu (archiwalnie)

| # | pytanie | moja rekomendacja |
|---|---|---|
| **Q1** | Neuron warstwy DG: Izhikevich jak w `dg_core` czy LIF? | **Izhikevich** — ciągłość z wynikami i próg `4 + K`; LIF tylko jeśli okaże się za drogi |
| **Q2** | Czytnik: tylko R-STDP, czy też reguła delta jako drugi czytnik? | R-STDP jako główny, regresja logistyczna jako sufit (bez uczenia ciągłego); reguła delta tylko jeśli R-STDP nie zadziała |
| **Q3** | Warstwa DG stała czy plastyczna (`ml_paper.md` sek. 6 zakładał R-STDP w ekspansji)? | **stała** w E3; plastyczna jako następny etap |
| **Q4** | Sygnał nowości: `err`, `unc` czy `rpe`? | `unc` jako główny, `rpe` jako wariant |
| **Q5** | Split-MNIST class-incremental (wspólny czytnik 10-klasowy) czy task-incremental (osobne głowice)? | **class-incremental** — trudniejszy i bliższy biologii (brak id zadania) |
| **Q6** | Środowisko: doinstalować torch do `snn_sep_venv` czy osobny venv dla E3? | osobny venv `snn_sep_e3_venv`, żeby nie ruszać środowiska testów regresji |
| **Q7** | Importować `datasets` / `PoissonEncoderT` / `STDPUpdaterPerSample3F` z repo STDP czy napisać własne? | **własne** — koder Poissona i R-STDP czytnika to kilkadziesiąt linii; import tworzy zależność między repo |
| **Q8** | Czy E3 to osobny artykuł (M1), a draft o narzędziu i wariant (a) idą niezależnie? | tak; H-E3a może trafić też do artykułu metodologicznego jako przykład funkcjonalny |
| **Q9** | Zakres `f_gęsty` / `f_rzadki` (20% / 5%) — ustalić z góry czy wybrać po E3.1? | po E3.1: `f_gęsty` = maksimum dokładności, `f_rzadki` = poziom o ~4× mniejszy |

---

---

## 11. Implementacja i zmiany względem planu (E3.0)

### Pliki

| plik | co robi |
|---|---|
| `model.py` | warstwa DG w PyTorch: Izhikevich (parametry GC z `dg_core`) i LIF, `K` w równaniu napięcia, opcjonalna pula 20 FS (GC→FS→GC); wiele poziomów `K` naraz na tych samych impulsach wejściowych |
| `calibrate.py` | bisekcja tablicy `K(f)` dla 17 poziomów naraz (1000 obrazów kalibracyjnych) |
| `precompute_codes.py` | kody DG (liczby impulsów) dla 70 000 obrazów × 17 poziomów; `--phasic` dla E3.2 |
| `learning.py` | czytniki `rstdp`, `delta`, `fly`; regulator nowości; k-WTA FlyModelu; sufit (regresja logistyczna) |
| `tasks.py` | MNIST z plików idx, normalizacja wejścia, Split-MNIST |
| `run_static.py` | E3.1, E3.2 i strojenie (`--exp tune`) |
| `run_split.py` | E3.3 (wszystkie warunki) i pilotaż regulatora (`--pilot`) |
| `make_hparams.py` | `hparams.json` ze strojenia i pilotażu (ziarno 99, walidacja = ostatnie 10k obrazów treningowych) |
| `analyze.py` | kryteria z sek. 6 / 6a, `results/summary.json`, `results/figures/` |
| `run_e31_all.sh`, `run_e32_all.sh`, `run_e33_all.sh`, `diag_input.py` | uruchamianie partiami; diagnostyka wejścia |
| `../hpc/athena_e3_now.sbatch`, `../hpc/e3_driver.sh`, `../hpc/e3_queue.txt` | łańcuch zadań na `plgrid-now` (limit: jedno zadanie naraz) |
| `../../tests/test_e3_layer.py` | zgodność neuronu z `dg_core` |

**Kody DG liczone raz.** Warstwa DG jest stała i nie dostaje sygnału z czytnika, więc
jej odpowiedź zależy tylko od obrazu, `K` i szumu. Kody dla 17 poziomów liczymy na
GPU (~9 min na komplet na A100), a uczenie sekwencyjne z regulatorem czyta gotowy
kod wybranego poziomu. Szum Poissona: jedna zamrożona realizacja na obraz, wspólna
dla wszystkich poziomów. Regulator wybiera najbliższy poziom z siatki
(1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 17, 20, 25, 30, 40, 50%).

**Zgodność z `dg_core`.** Ten sam ciąg impulsów wejściowych podany do jednego GC
w Brian2 (równania `dg_core`) i w torch daje identyczną liczbę impulsów dla
K = −5, 0, 5, 10, 15 (12, 9, 6, 3, 1). Test regresji 17/17 po instalacji torch.

### Zmiany wynikające z E3.0 (diagnostyka przed przebiegiem głównym)

1. **Normalizacja wejścia per obraz** (`tasks.normalize_images`: każdy obraz
   przeskalowany do tej samej sumy jasności). Przy samym hamowaniu tonicznym —
   jednym progu dla wszystkich obrazów — odsetek aktywnych neuronów zależał od
   „masy” cyfry: przy średnim f = 5% cyfra 1 aktywowała ~0.1% neuronów, cyfra 0
   ~18.5%, a regresja logistyczna na takim kodzie dawała 46% (k-WTA na tej samej
   ekspansji: 91%). Po normalizacji wejścia: 88–91%. **To osobny wynik:** hamowanie
   toniczne ustala próg, ale nie normalizuje aktywności między wzorcami o różnej
   sile wejścia; w `dg_core` wzorce mają z konstrukcji stałą gęstość wejścia, więc
   problem tam nie wystąpił.
2. **Wejście 200 Hz × 1 mV** zamiast 50 Hz × 4 mV (ten sam średni napęd). Dzięki temu
   `K` dla Izhikevicha wynosi 8.3 (f = 50%) … 16.9 (f = 1%), blisko zakresu
   zgodnego z danymi Madara (0–13.6); dla LIF −0.9 … 6.3. (Samo zmniejszenie szumu
   nie poprawiło informacji w kodzie — przyczyną słabego kodu był punkt 1.)
3. **Reguła R-STDP** zmieniona na trójczynnikową z wartością odniesienia nagrody
   (REINFORCE; Williams 1992, Florian 2007): wyjście losowane z softmax,
   Δw = η (R − R̄)(post − p) pre. Pierwsza wersja (wzmacnianie zwycięzcy, bez R̄)
   dawała 29–45% na czystych kodach; nowa ~90% po jednej epoce.
4. **`kwta_codes` przez mnożenie macierzy** (pierwsza wersja tworzyła tablicę 14 GB).

### Strojenie (ziarno 99, walidacja, bez zbioru testowego) — `hparams.json`

| neuron × czytnik | η | f_gęsty | f_rzadki | dokładność walid. przy f_gęstym |
|---|---|---|---|---|
| izh × rstdp | 0.25 | 10% | 3% | 0.890 |
| izh × delta | 0.05 | 20% | 5% | 0.918 |
| lif × rstdp | 0.5 | 10% | 3% | 0.914 |
| lif × delta | 0.05 | 25% | 6% | 0.931 |

Sygnał nowości: `unc` we wszystkich czterech kombinacjach (jego N̄ rośnie na
granicach zadań: +0.17 … +0.43); a, b = 5. i 95. percentyl N̄ z pilotażu.

---
