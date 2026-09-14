# Status — stan prac, wyniki, co dalej

*Aktualizacja: 2026-09-14.*

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
| **E1** — mapa reżimów (→ H1, H2) | uruchamialne, wynik wstępny **ostrzegawczy** (§3.2) |
| **E2** — atrybucja motywów (Shapley) | maszyneria gotowa, wynik wstępny stabilny (§3.1) |
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

### 3.1 E2 — atrybucja motywów (preset `quick`, 576 symulacji, stabilne)

```
[mc_inert]   FF 49.9%  FB 50.1%  MC   0.0%    dekorelacja +0.067 → +0.143
[mc_active]  FF 79.2%  FB 115.3% MC −94.5%    dekorelacja +0.067 → +0.244
             FF×FB +0.148 (synergia)   FB×MC +0.301 (synergia)
```

φ_MC ujemne: mossy cells **same** korelują wzorce (re-ekscytują GC), ale w parze
z hamowaniem podnoszą separację najmocniej ze wszystkich motywów. **MC to motyw
warunkowy.** (Udziały >100% i ujemne są matematycznie poprawne — sumują się do 100%.)

Pełna bateria metryk, średnie „brak hamowania → pełny obwód":

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

### 3.2 ⚠️ E1 — mapa reżimów: wynik wstępny jest OSTRZEŻENIEM, nie potwierdzeniem

Preset `quick` (12 punktów, 1 seed) **nie potwierdza H1**:

```
maksimum separacji przy 8.0% aktywnych GC (dekorelacja 0.558)
⚠️ monotonicznie ku rzadszej aktywności, maksimum na KRAŃCU siatki
   → sygnatura artefaktu wyciszenia, nie okna funkcjonalnego
```

To dokładnie pułapka „separacja czy wyciszenie". Skrypt sam to wykrywa i mówi
wprost. Zanim cokolwiek z tego wyniknie, trzeba rozszerzyć siatkę i zaostrzyć maskę
ważności (`MIN_ACTIVE_FRAC`, `MIN_FR_ACTIVE`) i sprawdzić, czy maksimum przesunie
się do wnętrza. **Nie raportować tej liczby jako wyniku.**

H1 jest tezą nośną całej pracy, więc rozstrzygnięcie tego jest **priorytetem nr 1**
(§4 pkt 1).

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

1. **Rozstrzygnąć wynik E1** — pełna mapa reżimów na HPC: szersza siatka,
   zaostrzona maska ważności. Bez tego H1 wisi w powietrzu, a H1 jest tezą nośną.
2. **`analyze_regime_map.py`** — figura „separacja vs aktywność" z panelem
   kontrolnym FR i przedziałami ufności.
3. **Kalibracja siły FS→FS** do docelowej częstotliwości FS — czeka na B2,
   maszyneria bisekcji już jest w `calibrate.py`.
4. **Krzywe f–I z CCIV.** Protokół prądowy JEST odzyskiwalny z adnotacji Axographu
   (`Pulse #1 … -100, 20` → start −100 pA, krok 20 pA, 30 epizodów, onset 100 ms,
   szerokość 500 ms). Dostępne: HMC 26 plików, GC+CA3 66. **FS nie mają ani jednego
   CCIV** — ich parametry tylko z adnotacji (4 komórki, §3.4).
5. **Pełna siatka atrybucji (E2) na Aresie** z całą baterią metryk (~35 tys.
   symulacji, ~12 h CPU — obliczenia nie są ograniczeniem).
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
