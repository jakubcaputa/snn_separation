# Status — stan prac, wyniki, co dalej

*Aktualizacja: 2026-09-28.*

> **Gdzie zacząć (2026-09-28).** Obliczenia są skończone i nic nie czeka
> w kolejce. Teza „DG separuje wzorce, a hamowanie tym steruje" jest obalona
> trzema niezależnymi kontrolami — §3.2 (E1), §3.2b (E1′), §3.3 (1A).
> **Jedyna otwarta rzecz to decyzja o tezie pracy: §4 pkt 2.** Reszta tego pliku
> jest materiałem do tej decyzji. `PLAN_BADAWCZY.md` jest świadomie NIE
> przepisany — czeka na tę decyzję.

**Ten plik odpowiada na jedno pytanie: gdzie jestem i co dalej.** Jest jedynym
źródłem prawdy dla STANU prac i ZMIERZONYCH LICZB — wszędzie indziej są odnośniki
tutaj, nie kopie. Hipotezy i plan eksperymentów: [PLAN_BADAWCZY.md](PLAN_BADAWCZY.md).
Instalacja i uruchamianie: [README.md](README.md).

---

## 1. Gdzie jestem

Model działa i daje powtarzalne wyniki. **Blokadą nie jest kod, tylko trzy decyzje
biologiczne** (§2) — maszyneria kalibracyjna jest gotowa i czeka na te trzy liczby.

| obszar | stan |
|---|---|
| Narzędzie `interactive_dg.py` | działa, rozbudowane o bilans hamowania i panel P(AP) |
| Rdzeń `experiments/dg_core/` | działa; testy regresji 17/17, wyniki bit-w-bit jak przed zmianami |
| **E1** — mapa reżimów (→ H1, H2) | **policzone, H1 OBALONA** (§3.2); figura + analiza gotowe |
| **E1′** — separacja przy dopasowanej aktywności | **policzone, H1′ OBALONA** (§3.2b); nadwyżka ponad null ujemna |
| **E2** — atrybucja motywów (Shapley) | pełna siatka **policzona**, czeka na `analyze_motifs.py` (§3.1) |
| **E4/E5** — kontroler (→ H3, H4) | **niezbudowane** ← niosą ciężar publikacji |
| Kalibracja punktu pracy | maszyneria gotowa, **specyfikacja niedomknięta** (§2) |
| Właściwości błony z danych Madara | **wyciągnięte**, 91 komórek (§3.4) |
| Odczyt downstream | 1A zamknięte (wynik negatywny), 1B odłożone (§3.3) |

---

## 2. ⛔ Co blokuje — czeka na prof. Błasiak

Mail wysłany **2026-09-11**, odpowiedź jeszcze nie przyszła. Bez tych trzech liczb
kalibracja się nie domknie, bo każda próba trafia w jedno kryterium kosztem drugiego.

### B1. Jaki jest realny udział prądu tonicznego w hamowaniu GC?

Zmierzone w modelu (wkłady do `dv/dt`, te same jednostki):

| komórka | pobudzenie | hamowanie FAZOWE | hamowanie TONICZNE (K) | udział tonicznego |
|---|---|---|---|---|
| **GC** | PP 2.43 | FS→GC **3.59** | **10.0** | **74%** |
| **FS** | PP 7.32 + GC 1.85 | 0.0 (**kanał nie istniał**) | 5.0 | 100% |
| **HMC** | GC 0.20 | 0.0 (`W_FS_HMC=0`) | 10.0 | 100% |

74% to wartość **odziedziczona, nie wybrana**. Dotychczasowe zdania o „hamowaniu
tworzącym separację" mogą w większości dotyczyć składnika tonicznego, a nie obwodu
FS. Odpowiedź wymusza `K` — a przez jego potrójną rolę (pułapka 4) wymusza też próg
i potencjał spoczynkowy, więc nie jest to wybór jednej liczby.

### B2. Czy ~46 Hz to fizjologiczna częstotliwość bazowa FS?

Prawdopodobnie zawyżona z przyczyny **strukturalnej**, nie doboru wag: FS nie miały
w modelu żadnego hamowania synaptycznego. Dodany kanał FS→FS obniża je do 28 Hz
(§3.5), ale jego siła wymaga zakotwiczenia w biologii.

### B3. Do którego reżimu wejścia kalibrujemy — in vitro czy in vivo?

**Pytanie najważniejsze i jedyne, którego wcześniej nie zadaliśmy wprost.** Waga
dobrana protokołem pulsowym Madara (tło 40 Hz) użyta w sieci przy napędzie 400 Hz
daje GC **22 Hz zamiast 2–6 Hz**. Dziesięciokrotna różnica reżimu — jedna waga nie
obsłuży obu. Rzadka stymulacja w plastrze i gęsty napęd PP to dwa różne punkty pracy
i trzeba wybrać, który jest warunkiem kontrolnym.

---

## 3. Wyniki

### 3.1 E2 — atrybucja motywów (preset `full`, 216 punktów × 5 seedów)

Policzone na Athenie 2026-09-14 (job 3167904, 8 shardów po ~9 min). Figury:
`e2_motif_attribution/results/fig1..fig4*.png`.

```
[mc_inert]   FF  66.8%  FB  33.2%  MC    0.0%   dekorelacja +0.065 → +0.173
             FF×FB +0.025 (synergia)
[mc_active]  FF 152.1%  FB 119.7%  MC −171.8%   dekorelacja +0.065 → +0.197
             FF×FB +0.126   FF×MC +0.223   FB×MC +0.210  (wszystkie synergie)
             FR aktywnych GC 4.7 Hz | FR MC 5.9 Hz
```

⚠️ **Liczby różnią się od presetu `quick`, który tu wcześniej stał** (FF/FB było
50/50, teraz 67/33 w `mc_inert`; `mc_active` dawało +0.244, daje +0.197). Wniosek
JAKOŚCIOWY przeżył — φ_MC ujemne, MC w parach silnie synergiczne — ale **żadnej
liczby z presetu `quick` nie cytować**, bo siatka `full` je przesuwa.

φ_MC ujemne: mossy cells **same** korelują wzorce (re-ekscytują GC), ale w parze
z hamowaniem podnoszą separację najmocniej ze wszystkich motywów. **MC to motyw
warunkowy.** (Udziały >100% i ujemne są matematycznie poprawne — sumują się do 100%.)

Pełna bateria metryk, średnie „brak hamowania → pełny obwód"
(⚠️ ta tabela jest wciąż z presetu `quick` — `analyze_motifs.py` nie drukuje baterii
dla siatki `full`; przeliczyć, zanim pójdzie do tekstu):

| metryka | mc_inert | mc_active |
|---|---|---|
| dekorelacja | +0.067 → +0.143 | +0.067 → +0.244 |
| cosinus (podobieństwo) | 0.675 → 0.602 | 0.675 → 0.535 |
| Jaccard (overlap) | 0.633 → 0.593 | 0.633 → 0.403 |
| info retention | 1.000 → 0.915 | 1.000 → 0.733 |
| synchronia χ | 0.206 → 0.222 | 0.206 → 0.336 |
| Fano | 0.716 → 0.790 | 0.716 → 1.382 |

Trzy obserwacje (do potwierdzenia na pełnej siatce):

1. **Wszystkie trzy miary separacji zgadzają się co do kierunku** — wniosek nie
   wisi na Pearsonie.
2. **Trade-off separacja↔informacja jest mierzalny:** bez hamowania retention = 1.0
   (GC wiernie kopiują wejście, zero separacji); mc_inert kupuje +0.143 separacji za
   ~8% informacji, mc_active +0.244 za ~27%. To właściwa oś: nie „czy DG separuje",
   tylko **po jakim kursie wymienia informację na separację** (policzyć Shapleya na
   retention, nie tylko na dekorelacji).
3. **Aktywne MC przesuwają dynamikę ku synchronii i nadpoissonowskiej zmienności**
   (χ 0.22→0.34, Fano 0.79→1.38) — ślad reżimu, który bez hamulca FS→HMC kończy się
   runawayem.

**Hamulec FS→HMC — najmocniejszy istniejący wynik.** Pętla GC→HMC→GC jest czysto
pobudzająca i bez hamulca nie ma reżimu pośredniego:

| `W_FS_HMC` | dekorelacja |
|---|---|
| 0 (model domyślny) | **−0.267** (runaway, FR_HMC → 98 Hz — obwód *koreluje* wzorce) |
| **2** | **+0.247** ← najlepszy wynik w całym badaniu, o 66% lepiej niż obwód domyślny (+0.149) |
| ≥ 5 | +0.15 (MC znów wyciszone) |

**Separacja rośnie z rozmiarem sieci** (`DGConfig.scaled(N)`, stały in-degree,
stała frakcja aktywnych GC): +0.149 → +0.231 → **+0.296** dla N_GC = 200 → 400 → 800.
Zgodne z teorią kodowania ekspansyjnego; do policzenia porządnie na HPC (E6).

### 3.2 E1 — mapa reżimów: ROZSTRZYGNIĘTE. H1 w obecnym brzmieniu jest FAŁSZYWA

Pełna siatka policzona (Athena, job 3167903, 450 punktów = 10 `K_GC` × 9 `W_FS_GC`
× 5 seedów, 1800 symulacji, 3.7 min na 16 CPU; 419/450 przeszło maskę).
Figura: `e1_regime_map/results/regime_map_full.png`.

**Separacja NIE ma optimum przy pośredniej aktywności — jest MONOTONICZNA.**
Maksimum `dec` jedzie za progiem maski ważności przy każdym progu, jaki mu podstawić:

| `MIN_ACTIVE_FRAC` | 0.02 | 0.03 | 0.05 | 0.08 | 0.10 | 0.15 | 0.20 |
|---|---|---|---|---|---|---|---|
| maksimum przy | 0.025 | 0.030 | 0.065 | 0.085 | 0.120 | 0.150 | 0.200 |
| podłoga maski | 0.020 | 0.030 | 0.050 | 0.080 | 0.100 | 0.150 | 0.200 |

Maksimum siedzi zawsze na podłodze albo koszyk nad nią — to podłoga je stawia, nie
biologia. **Rozszerzanie siatki tego nie naprawi**: `dec = r_in − r_out` jest
strukturalnie monotoniczna względem rzadkości i nie odróżnia separacji od ciszy.
Warunkowanie na `retention` też nie ratuje H1 — maksimum dalej wędruje za progiem
(0.04 przy `MIN_RETENTION` 0.10 → 0.18 przy 0.60).

⚠️ Poprzednia wersja `run_regime_map.py` **raportowała fałszywe potwierdzenie H1**:
jej test krańca sprawdzał równość z minimum siatki, więc maksimum leżące jeden
koszyk nad podłogą przechodziło test. Zastąpiony testem KSZTAŁTU (przesuwamy próg
maski, patrzymy czy maksimum zostaje). Każda liczba z E1 sprzed 2026-09-21 jest
podejrzana.

**Kurs wymiany separacja↔informacja jest gładki i monotoniczny — nie ma kolana,**
czyli nie ma wyróżnionego punktu pracy (`retention` = MI/H, nowa kolumna w sweepie):

| retention ≥ | 0.00 | 0.20 | 0.40 | 0.50 | 0.60 | 0.70 | 0.80 | 0.90 |
|---|---|---|---|---|---|---|---|---|
| osiągalne max `dec` | 0.785 | 0.623 | 0.533 | 0.417 | 0.352 | 0.330 | 0.257 | 0.232 |

Najlepszy KURS (separacja na jednostkę utraconej informacji) wypada w reżimie
prawie bezstratnym, przy SŁABYM hamowaniu: `dec` 0.173 za 1.3% utraconej
informacji (`K_GC` 10, `W_FS_GC` 0.25). To jest wynik do sformułowania na nowo
zamiast H1: nie „istnieje okno", tylko „DG wymienia informację na separację po
kursie, który jest najkorzystniejszy przy słabym hamowaniu".

**`retention` MA maksimum wewnętrzne — przy ~25% aktywnych GC** (średnia po
koszykach: 0.08 przy <4% → 0.95 przy 24–32% → 0.16 powyżej 45%). ⚠️ Ale to jest
dokładnie `P_active` = 0.25 z siatki, więc **prawdopodobnie tautologia estymatora
MI** (informacja przechodzi najlepiej, gdy rzadkość wyjścia = rzadkość wejścia),
a nie własność obwodu. **Nie raportować tego jako wyniku, dopóki nie przejdzie
testu z §4 pkt 1.**

### 3.2b E1′ — separacja przy DOPASOWANEJ aktywności. Wynik negatywny, mocny

`run_matched_activity.py`, Athena job 3189473, 810 punktów (6 celów aktywności ×
9 `W_FS_GC` × 3 `P_active` × 5 seedów), 20.6 min. Dostrojono 733/810 — reszta
to kombinacje, dla których cel leży poza zasięgiem `K_GC` ∈ [0, 24].
Odtworzenie wszystkich liczb z tej sekcji **bez ponownego liczenia**:
`python analyze_matched_activity.py`. Figura:
`e1_regime_map/results/matched_activity_full.png`.

Konstrukcja naprawia trzy wady starego E1: aktywność jest **zadana** (bisekcja po
`K_GC`), mierzona jest **nadwyżka ponad null** o tej samej rzadkości, a `P_active`
jest osią, nie stałą.

**1. Obwód separuje GORZEJ niż przetasowanie własnego wyjścia.**

| cel aktywności | 0.02 | 0.05 | 0.10 | 0.15 | 0.20 | 0.30 |
|---|---|---|---|---|---|---|
| `dec` | 0.632 | 0.495 | 0.333 | 0.257 | 0.188 | 0.113 |
| nadwyżka − null permutacyjny | −0.116 | −0.252 | −0.413 | −0.490 | −0.561 | −0.633 |

Średnio **−0.389 ± 0.245** (SD), SEM 0.009, n=733 → **43 SEM od zera**. Ujemna
nadwyżka znaczy, że gdyby losowo poprzestawiać, KTÓRY GC strzela (zachowując
rozkład częstotliwości co do wartości), dekorelacja by WZROSŁA. Czyli tożsamość
strzelających GC jest dyktowana przez wejście: nakładające się wzorce pobudzają
nakładające się GC, a obwód **zachowuje** korelację względem losowego przypisania.
To jest mocniejszy wynik niż zero — DG tu nie „nie pomaga", tylko aktywnie trzyma
korelację wejścia.

**2. Hamowanie fazowe `W_FS_GC` nie kupuje NICZEGO przy wyrównanej aktywności.**
Nadwyżka jest płaska na całym zakresie 0.0–5.0 (rozstęp średnich 0.024 przy SEM
komórki 0.027). Sprawdzone też z osobna na każdym poziomie aktywności — płasko
wszędzie (jedna komórka z sześciu ledwo przekracza 2·SEM, czyli tyle, ile wypada
z przypadku przy sześciu porównaniach). **Cały efekt hamowania w starym E1 był
efektem wyciszania, nie obwodu.**

**3. Maksimum `retention` IDZIE za `P_active` — to tautologia, zamknięte.**

| `P_active` | 0.10 | 0.25 | 0.40 |
|---|---|---|---|
| maksimum retention przy AF | 0.100 | 0.200 | 0.280 |

Czyli własność estymatora MI (informacja przechodzi najlepiej, gdy rzadkość
wyjścia ≈ rzadkość wejścia), nie punkt pracy obwodu. **Nie raportować tych 25%.**
To domyka pytanie postawione w §4 pkt 1 — odpowiedź negatywna.

⚠️ Null k-WTA daje nadwyżkę DODATNIĄ (+0.32 przy AF 2% → +0.08 przy 30%), czyli DG
dekoreluje lepiej niż losowa projekcja o tej samej rzadkości. To NIE jest
sprzeczność z pkt 1 — to inne pytanie (losowa projekcja gaussowska jest słabym
dekorelatorem). Wniosek nośny opiera się na nullu permutacyjnym, bo tylko on
trzyma rozkład częstotliwości prawdziwego wyjścia co do wartości.

### 3.3 Odczyt downstream — 1A zamknięte, 1B odłożone

**1A: „DG poprawia klasyfikację liniową" — sprawdzone i OBALONE.** Cztery warunki
(`raw`/`dg`/`dg_noinh`/`random` z dopasowaną rzadkością):

```
raw 0.940  ·  dg 0.885  ·  dg_noinh 0.935  ·  random 0.885
Δ acc (DG − raw) = −0.054
```

Hipoteza ratunkowa (krótkie okno odczytu stworzy reżim, w którym DG wygrywa) też
obalona: skracanie T pogarsza DG jeszcze bardziej (−0.181 → −0.300 dla T=600→60 ms
przy R_in=0.90); przy R_in ≥ 0.95 wszystko siedzi na poziomie przypadku.
**To uczciwy wynik negatywny, który uzasadnia przejście na miary informacyjne, nie
porażka.** Nie inwestować więcej.

**1B: pojemność pamięci skojarzeniowej — ODŁOŻONE.** Sieć atraktorowa z regułą
kowariancyjną Tsodyksa–Feigelmana + k-WTA; pojemność = największe P przy
Jaccard ≥ 0.90; oś główna: siła hamowania `W FS→GC`. Przy N_GC = 200 pojemność
kolapsuje do 2–4 wzorców dla **wszystkich warunków naraz** (podłoga) — prawdziwe
DG→CA3 czerpie z ekspansji, więc potrzeba N_GC ≥ 2000 na HPC. **Nie traktować
obecnych liczb jako wyniku.**

⚠️ Pułapka, w którą już raz wpadłem: binaryzacja top-k na niemal binarnym wektorze
`raw` (400 Hz vs 40 Hz) wybiera spośród remisów rozstrzyganych jitterem Poissona →
sztuczna dekorelacja baseline'u. Metryka główna używa progu w połowie zakresu;
top-k został jako kontrola rzadkości.

### 3.4 Właściwości błony z danych Madara

`dg_core/madar_intrinsics.py` bierze pomiar eksperymentatora wprost z adnotacji
MATLAB, zamiast odtwarzać go z sygnału. Po deduplikacji po ID (surowo 72 →
faktycznie 42 komórki GC; **bez deduplikacji mediana wychodzi −70 zamiast −76**):

| typ | n | V_rest [mV] mediana [IQR] | τ_m [ms] | Rm [MΩ] |
|---|---|---|---|---|
| GC | 53 | **−76 [−81…−70]** (n=42) | 3 [2–5] | 130 [94–198] |
| FS | 4 | −70 [−72…−65] | 1 | 51 |
| HMC | 19 | −67 [−74…−60] | — | — |
| CA3 | 15 | −72 [−76…−68] | — | — |

**To rozstrzyga spór o K.** Model przy `K_GC=10` daje V_rest = −78.7 mV, czyli
**wewnątrz IQR danych**; przy `K_GC=0` daje −70 mV, na górnej krawędzi. Wartość
„około −70 mV" z maila odpowiada górnemu kwartylowi, nie medianie — **obecne
`K_GC=10` jest przez dane wspierane, a nie podważane.** Zamyka wątek, który
dwukrotnie zmieniał kierunek przy rozumowaniu bez danych.

⚠️ Rozbieżność do opisania w Methods: **τ_m z danych to ~3 ms dla GC**, a nie
10–50 ms jak w mailu. Izhikevich i tak nie ma jawnego τ_m (szybka składowa ~1 ms,
całkowanie niosą stałe synaptyczne 5/8 ms). Zapytać, czy rozbieżność bierze się
z definicji (Rm wejściowe vs błonowe).

### 3.5 Kanał FS→FS

Wzajemne hamowanie interneuronów, którego w modelu w ogóle nie było
(`W_FS_FS`, domyślnie 0.0 — obwód bez zmian). Działa zgodnie z oczekiwaniem:

| `W_FS_FS` | 0.0 | 0.5 | 1.0 | 2.0 | 4.0 |
|---|---|---|---|---|---|
| FR_FS [Hz] | 46.0 | 41.8 | 37.8 | 33.4 | 27.6 |
| FR_GC [Hz] | 3.12 | 3.09 | 3.37 | 3.65 | 4.08 |

---

## 4. Co dalej — kolejność wg wartości

**Bez odpowiedzi od prof. Błasiak (§2) można robić 1, 2, 4, 5 i 6.**
Stan na 2026-09-22: E1, E1′ i E2 policzone na Athenie. **Obliczenia przestały być
wąskim gardłem — wąskim gardłem jest decyzja z pkt 2.**

1. ~~Test tautologii `retention`~~ — **zrobione, wynik negatywny** (§3.2b pkt 3):
   maksimum idzie za `P_active`, więc to tautologia estymatora MI. Zamknięte.
2. **⛔ DECYZJA O TEZIE PRACY — to jest teraz pytanie nr 1 i nie jest techniczne.**
   Trzy niezależne eksperymenty mówią to samo: 1A (DG przegrywa z `random`
   o dopasowanej rzadkości, §3.3), E1 (separacja = wyciszenie, §3.2) i E1′
   (nadwyżka ponad null UJEMNA, hamowanie fazowe bez efektu, §3.2b). Wersja
   „DG separuje wzorce, a hamowanie tym steruje" jest **nie do obronienia
   na tym modelu**. Do wyboru:
   - **(a) opublikować wynik negatywny** — „separacja przypisywana DG jest
     rzadkością, nie obwodem", z trzema niezależnymi kontrolami. Uczciwe,
     spójne, i całe potrzebne liczenie JEST już zrobione.
   - **(b) zmienić model** — obecny obwód przy domyślnych wagach ma martwe MC
     (§5) i hamulec FS→HMC jako jedyny motyw o dużym efekcie (§3.1). Teza
     mogłaby dotyczyć REGULACJI aktywności (E4/E5), nie separacji.
   - **(c) zmienić miarę** — porzucić dekorelację na rzecz czegoś, czego
     rzadkość nie fałszuje. ⚠️ Ale `retention` już odpadło (§3.2b pkt 3),
     a decodability odpadła w 1A. Trzeciego kandydata nie widać.
   Bez tej decyzji nie ma sensu liczyć niczego dalej — każdy kolejny sweep
   odpowiada na pytanie, które właśnie straciło podstawę.
3. **Przeformułować H1 w `PLAN_BADAWCZY.md`** — dopiero po decyzji z pkt 2.
   „Separacja ma optimum przy pośredniej aktywności" jest obalone (§3.2, §3.2b)
   i nie da się tego naprawić ani siatką, ani miarą.
3. **Kalibracja siły FS→FS** do docelowej częstotliwości FS — czeka na B2,
   maszyneria bisekcji już jest w `calibrate.py`.
4. **Krzywe f–I z CCIV.** Protokół prądowy JEST odzyskiwalny z adnotacji Axographu
   (`Pulse #1 … -100, 20` → start −100 pA, krok 20 pA, 30 epizodów, onset 100 ms,
   szerokość 500 ms). Dostępne: HMC 26 plików, GC+CA3 66. **FS nie mają ani jednego
   CCIV** — ich parametry tylko z adnotacji (4 komórki, §3.4).
5. ~~Pełna siatka atrybucji (E2)~~ — **policzona** (Athena, job 3167904, 8 shardów
   po ~9 min; `e2_motif_attribution/results/lesion_grid_full_shard00*.npz`).
   Zostaje `analyze_motifs.py --in "lesion_grid_full_shard*.npz"` i wpisanie
   liczb do §3.1 w miejsce wyników z presetu `quick`.
6. **`io_madar.py`** — odczyt bodźców z `dataset/…/Protocols/` i podanie ich jako
   wejścia PP do `dg_core.circuit.simulate()`. Jeden dzień pracy, a zmienia status
   projektu z „model z syntetycznymi wzorcami" na „model napędzany tymi samymi
   bodźcami, co eksperyment" — odblokowuje walidacje V2, V3 i V4 naraz.
7. **Suwak `W FS→HMC` + panel obserwowalności w `interactive_dg.py`** — wisząca
   rekomendacja; ten suwak jest demonstracją tezy o regulacji aktywności w głównym
   narzędziu.
8. **E4/E5 — kontroler adaptacyjny** (`control.py`: IP + iSTDP + SS). Niosą ciężar
   publikacji, ale mają sens dopiero po domknięciu punktu pracy i rozstrzygnięciu E1.

---

## 5. Ustalenia o reżimie pracy modelu

Zmierzone, nadal obowiązujące, cytowane przez pozostałe dokumenty.

**Wejście PP (skalibrowane, `dg_params.py` = jedyne źródło prawdy).**
40 włókien × 10 Hz = **400 Hz aggregate** na aktywny GC. Przy 600 Hz GC dawały
16.6 Hz (za gęsto); 400 Hz daje ~6 Hz, czyli rzadkie kodowanie DG. Tryb per-fiber
i zagregowany są spójne.

**K_tonic = hamowanie toniczne, próg `G_crit = 4 + K`.** Wyprowadzone analitycznie
i potwierdzone symulacją co do 0.1 mV. GC/HMC (K=10, G_crit=14) trudniej pobudliwe
niż FS (K=5, G_crit=9). Napęd 400 Hz daje g_ex ≈ 8 mV, czyli poniżej progu GC →
reżim fluktuacyjny → separacja.

**Mossy cells przy domyślnych wagach są martwe (0.00 Hz).** Napęd GC→HMC (1 mV) nie
zbliża się do progu 14 mV; nawet zmuszone do strzelania dają 0.1 mV wobec 3.6 mV
z FS→GC. **Każdy wniosek o roli MC przy domyślnych ustawieniach dotyczy obwodu BEZ
nich** — stąd obowiązek dwóch reżimów `mc_inert`/`mc_active` w każdym sweepie
([PLAN_BADAWCZY.md](PLAN_BADAWCZY.md) §3.3).

**`b` ustawia SUMĘ `V_rest + V_th_eff`, `K` ich ODSTĘP.** Przy `b = 0.2` suma jest
zablokowana na −120 mV: para (−70, −50) wychodzi przy `K = 0`, a (−70, −45) jest
nieosiągalna żadnym K — wymaga `b = 0.4`, i wtedy K rośnie do 14.

**P(AP|puls) nie jest sterowalne samą wagą.** Bez źródła zmienności krzywa jest
skokowa (0.00 → 0.99). Stąd zawodność synaptyczna `P_REL_*`: przy kompensacji wagą
`W/p` wariancja rośnie jak `1/p`, co daje stopniowane P(AP) przy niezmienionym
średnim napędzie (zmierzone: FR 3.12 → 5.46 → 9.22 Hz dla p_rel 1.0 → 0.5 → 0.25).
⚠️ `p_rel` i wagę kalibrować RAZEM.

> Cztery pułapki obowiązujące w każdym nowym sweepie (skalowanie, dwa reżimy MC,
> maska ważności, potrójna rola `K_GC`) są opisane w
> [PLAN_BADAWCZY.md](PLAN_BADAWCZY.md) §3.5 — jedno miejsce, żeby nie rozjechały
> się dwie wersje.

---

## 6. Dziennik porządków

**2026-09-14 — scalenie dokumentacji, cztery pliki .md → trzy.**
`doktorat_plan.md` + `PLAN_PUBLIKACJI.md` → jeden
[PLAN_BADAWCZY.md](PLAN_BADAWCZY.md) (hipotezy + plan eksperymentów).
`README.md` przepisany na standardowy (instalacja, uruchamianie, struktura).
`experiments/README.md` rozpuszczony: mapa folderów i opis `dg_core` do README,
metodologia (E1 vs E2, historia numeracji) do PLAN_BADAWCZY, statusy i wyniki tutaj.
Ten plik odchudzony do: gdzie jestem → co blokuje → wyniki → co dalej → ustalenia.
Zasada: każda liczba i każdy fakt mają **jedno** miejsce, reszta odsyła.

**2026-09-14 — sprzątanie kodu.** Usunięto 16 plików z korzenia: `debug_*.py`
(7 roboczych), `visualize_dg*.py` (4 generatory figur), jednorazowe eksploratory
(`dataset_overview.py`, `explore_gc1_r090.py`) oraz warianty zastąpione przez
`dg_core` (`dg_microcircuit_brian2.py`, `single_neuron_patsep_{brian2,nest}.py`).
Wszystko zostaje w historii gita. Do `archive/` przeniesiono cztery skrypty, które
wyprodukowały nadal obowiązujące wnioski (`bifurcation_K.py`, `freq_audit.py`,
`dg_module3_inh_comparison.py`, `explore_data.py`) — mają naprawione ścieżki
i uruchamiają się. Korzeń repo: z 25 plików do 5.
