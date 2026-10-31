# E3 — hipotezy i kryteria zapisane przed uruchomieniem

*Przeniesione 2026-10-31 z README.md bez zmian treści; numeracja sekcji (2, 6, 6a–6k) zachowana, bo odwołuje się do niej kod. Każda podsekcja ma datę zapisu — kryteria nie były zmieniane po uruchomieniu. Werdykty: README.md sek. 3, liczby: wyniki_szczegolowe.md.*

## 2. Hipotezy (falsyfikowalne)

| # | hipoteza | eksperyment | obalona, jeśli |
|---|---|---|---|
| **H-E3a** | dokładność czytnika ma maksimum przy pośrednim `f`, a dekorelacja rośnie monotonicznie do ciszy | E3.1 | dokładność monotoniczna w `f` (maksimum na brzegu siatki) |
| **H-E3b** | przy wyrównanym `f` hamowanie fazowe nie zmienia dokładności (funkcjonalna wersja E1′) | E3.2 | istotne nachylenie po korekcji |
| **H-E3c** ⭐ | `f` sterowane nowością daje mniejsze zapominanie niż stałe `f` równe jego średniej | E3.3 | brak istotnej różnicy `mod_novelty` vs `fixed_matched` |
| **H-E3d** | sterowanie rzadkością pomaga bardziej niż sterowanie tempem uczenia tym samym sygnałem | E3.3 | `3f_lr` ≥ `mod_novelty` |

H-E3c jest hipotezą nośną. H-E3d decyduje o pozycjonowaniu względem klasycznej
reguły trójczynnikowej. H-E3a ma wartość sama w sobie (łączy się z artykułem
metodologicznym — wariant (a) w STATUS sek. 4.1).

---

---

## 6. Statystyka — zapisać w kodzie przed uruchomieniem

Lekcja z E1‴: kryterium ustalone z góry, potwierdzenie na nowych ziarnach.

- **Kontrast główny (H-E3c):** `BWT(mod_novelty) − BWT(fixed_matched)`, parowany po
  ziarnach; test Wilcoxona, α = 0.05. Kryterium: istotny i ten sam znak w ≥ 8/10 ziaren.
- **H-E3d:** analogicznie `mod_novelty` vs `3f_lr`.
- **H-E3a:** maksimum dokładności w punkcie wewnętrznym siatki `f` w ≥ 4/5 ziaren.
- **H-E3b:** nachylenie dokładność(`W_FS_GC`), korekta Bonferroniego po poziomach `f`.
- **Potwierdzenie:** jeśli H-E3c przejdzie, powtórka na 10 **nowych** ziarnach
  z niezmienionymi hiperparametrami, zanim cokolwiek napiszemy.
- Hiperparametry (`η`, `T`, `τ_N`, `f_gęsty`, `f_rzadki`) stroimy na osobnych ziarnach
  i zamrażamy przed E3.3.

---

### 6a. Test potwierdzający H-E3e (zapisane 2026-10-13, PRZED uruchomieniem)

Przebieg główny (sieci 0–4) obalił H-E3c, a wariant odwrócony `mod_novelty_inv`
(nowość → gęstszy kod) zapominał mniej niż `fixed_matched` — ale był to warunek
dodatkowy, a `fixed_matched` dopasowano do średniego f **innego** warunku. Stąd:

- **H-E3e:** `mod_novelty_inv` zapomina mniej niż stałe f równe **jego własnemu**
  średniemu f (`fixed_matched_inv`).
- **Dane:** nowe sieci, ziarna 5–9 × kolejności 0, 1 (10 przebiegów na kombinację);
  hiperparametry bez zmian (`hparams.json` z 2026-10-12).
- **Kryterium (per kombinacja neuron × czytnik):** BWT(`mod_novelty_inv`) −
  BWT(`fixed_matched_inv`) > 0, Wilcoxon parowany p < 0.05, dodatni w ≥ 8/10.
- **Werdykt:** H-E3e potwierdzona, jeśli kryterium spełniają **obie kombinacje z
  czytnikiem R-STDP** (izh, lif) — to jest czytnik trójczynnikowy, o który chodzi
  w E3. Kombinacje z regułą delta raportujemy, ale nie wchodzą do werdyktu (reguła
  delta zapomina prawie całkowicie w każdym warunku, BWT ≈ −0.9).

### 6b. E3.5 — odporność obalenia H-E3c (zapisane 2026-10-22, PRZED uruchomieniem)

**Cel:** sprawdzić, czy „nowość → rzadszy kod zapomina więcej niż stały kod o tej samej
średniej” zachodzi także w innych architekturach i przy innej regule czytnika, a nie
tylko w konfiguracji z E3.3. Skrypt `run_dose.py`, figura i kryteria w `analyze.py`.

- **Siła modulacji g** ∈ {−1, −0.5, 0, +0.5, +1}: f_spoczynek = f_c·r^{g/2}, f_nowość =
  f_c·r^{−g/2}, f_c = √(f_gęsty·f_rzadki), r = f_gęsty/f_rzadki (g = +1 ≡ `mod_novelty`,
  g = −1 ≡ `mod_novelty_inv`). Dla każdego g ≠ 0 kontrola: stałe f = średnie f
  zrealizowane przez modulację. **Efekt Δ(g) = BWT(mod g) − BWT(stałe f g).**
- **Osie (komórki):** architektura warstwy DG {N = 500, 1000, 2000, 5000 przy fan-in 30;
  fan-in 10 i 100 przy N = 2000} × neuron {Izhikevich, LIF} × czytnik {R-STDP, delta,
  **rgate**} = 36 komórek. `rgate` = trójczynnikowa bez osłabiania (nagroda bramkuje tylko
  wzmacnianie wybranego, poprawnego wyjścia; skalowanie synaptyczne) — czytnik, który sam
  prawie nie zapomina, więc efekt rzadkości nie jest maskowany regułą (E3.4).
- **Przebiegi:** sieci 0–4 dla N = 2000 / fan-in 30, sieci 0–2 dla pozostałych;
  kolejności 0, 1 (10 lub 6 przebiegów na komórkę).
- **Hiperparametry:** η i regulator z ziarna 99 (architektura domyślna) dla wszystkich
  architektur, bez ponownego strojenia; η i f_gęsty/f_rzadki dla `rgate` strojone tak samo
  jak dla pozostałych czytników (walidacja, ziarno 99) przed przebiegiem.

**Kryteria:**
1. **Obalenie H-E3c jest odporne**, jeśli średnie Δ(+1) < 0 w ≥ 90% komórek (≥ 33/36)
   **i** w żadnej komórce Δ(+1) nie jest istotnie dodatnie (Wilcoxon p < 0.05).
   Jeśli w którejś komórce Δ(+1) jest istotnie dodatnie — H-E3c działa w tej
   konfiguracji, a obalenie nie jest ogólne.
2. **Czytnik bez osłabiania:** to samo kryterium osobno dla 12 komórek z `rgate`
   (≥ 11/12, żadna istotnie dodatnia). To jest najważniejszy test — tu pytanie jest
   najczystsze.
3. **Dawka–odpowiedź (opisowo):** w ilu komórkach Δ(+1) ≤ Δ(+0.5) ≤ 0 (monotonicznie);
   oraz znak Δ(−1) (kierunek odwrócony) — raportujemy bez kryterium.

### 6c. E3.6 — H-E3c na zadaniu separacji wzorców z `dg_core` (zapisane 2026-10-22, PRZED uruchomieniem)

**Cel:** sprawdzić tę samą hipotezę na zadaniu, dla którego model DG został zbudowany,
z modelem `dg_core` bez zmian (Brian2, 200 GC + FS + HMC, parametry domyślne). Skrypt
`run_dgtask.py`.

- **Zadanie** jak w 1A (`readout_deferred/run_classification.py`): 10 prototypów
  o wzajemnym podobieństwie R_in ∈ {0.5, 0.75, 0.9}, p_active = 0.25, szum bit-flip 0.2;
  100 prób uczących i 50 testowych na klasę; uczone sekwencyjnie parami
  (0/1 → … → 8/9), 3 epoki na zadanie, czytnik 10-klasowy na częstotliwościach GC.
- **Poziomy K_GC:** bisekcja (`solve_k_gc_for_active_fraction`, średnia z 3
  prototypów) do f ∈ {3, 5, 7, 10, 14, 20, 30%}; f_c = 10%, r = 4 (ustalone z góry,
  bez strojenia na tym zadaniu).
- **Dawka–odpowiedź** g ∈ {−1, −0.5, 0, +0.5, +1} z kontrolą stałego f o tej samej
  średniej, jak w E3.5; czytniki R-STDP, delta, rgate z η jak dla MNIST (Izhikevich).
  Regulator: a, b z pilotażu na sieci 99 (dla każdego R_in i czytnika osobno), τ = 20.
- **Przebiegi:** sieci 0–2 × kolejności 0, 1 (6 na komórkę), 3 R_in × 3 czytniki =
  9 komórek.
- **Kryterium:** jak w sek. 6b, pkt 1: obalenie H-E3c przenosi się na zadanie
  separacji, jeśli Δ(+1) < 0 w ≥ 8/9 komórek i w żadnej nie jest istotnie dodatnie
  (Wilcoxon p < 0.05). Dodatkowo raportujemy, czy przy najwyższym podobieństwie
  (R_in = 0.9) — gdzie separacja powinna być najważniejsza — kierunek jest inny.

> ⚠️ **Zastrzeżenie (2026-10-22, po odpowiedzi prof. Błasiak):** E3.6 liczy się na
> obecnej kalibracji `dg_core` — gęste tło wejściowe 400 Hz i hamowanie toniczne ~74%.
> Według odpowiedzi kalibrować trzeba do ex vivo (wejście = salwy protokołu Madara),
> hamowanie toniczne jest za silne względem fazowego, a separację trzeba oceniać razem
> z R_w (`korespondencja/2026-10-22_odpowiedz_blasiak.md`). E3.6 odpowiada więc na pytanie
> „czy H-E3c przenosi się na zadanie separacji w obecnym modelu”, a nie „w modelu
> skalibrowanym do skrawka” — to drugie dopiero po rekalibracji.

### 6e. E3.6x — to samo zadanie na modelu skalibrowanym do skrawka (zapisane 2026-10-24, PRZED uruchomieniem)

Model: `dg_core.exvivo.exvivo_best_config()` — najlepszy punkt siatki v3 kalibracji ex vivo
(salwa 20 mV, p_rel 0.6, PP→FS 0.5, FS→GC 2, GC→FS ≈ 0, FS→FS 1, K_GC przez bisekcję).
Wejście: wzorzec wskazuje, które GC dostają salwy (p_active 0.25, szum 0.2 jak wyżej);
salwy w pociągu Poissona 10 Hz (jak protokoły Madara), osobnym dla każdej próby, wspólnym dla
wszystkich poziomów K; bez tła (skrawek). Poziomy f: 3–20% (ok. 25% GC dostaje wejście, więc
30% jest nieosiągalne); f_c = 10%, r = 4 bez zmian. Wszystko inne (zadanie, czytniki, η,
dawka–odpowiedź, pilotaż na sieci 99, sieci 0–2 × 2 kolejności) **jak w sek. 6c**.
Skrypt: `run_dgtask.py --regime exvivo`, wyniki `results/e36x/`.
Uwaga z testu (2026-10-24): K skalibrowane na 3 prototypach daje na rzeczywistych próbach
f ≈ 4–6% dla poziomów 3% i 5% (kilka GC odpala zawsze), więc dolny koniec zakresu jest
płytszy niż zakładano. Regulator i kontrola wybierają poziomy po ZMIERZONYM f, więc
porównanie modulacja vs stałe f pozostaje uczciwe, ale efektywna rozpiętość r < 4.

**Kryterium — identyczne jak w sek. 6c** (obalenie H-E3c przenosi się, jeśli Δ(+1) < 0
w ≥ 8/9 komórek i w żadnej nie jest istotnie dodatnie). Dodatkowo porównujemy komórka po
komórce z E3.6 (stara kalibracja): czy kierunek Δ(+1) się zgadza.

### 6f. E3.8 — test mechanizmu „rozcieńczać przy osłabianiu, izolować przy wzmacnianiu” (zapisane 2026-10-27, PRZED uruchomieniem)

**Hipoteza** (z dyskusji 2026-10-26): reguły znormalizowane per obraz zmieniają odpowiedź
czytnika o tyle samo niezależnie od gęstości kodu, więc gęsty kod rozkłada każdą poprawkę
na więcej synaps. Przy regułach z osłabianiem duże, szkodliwe poprawki na starcie nowego zadania
są przy „nowość → gęściej” rozcieńczone, a przy „nowość → rzadziej” skoncentrowane na
najsilniej pobudzonych neuronach, z których czytane są stare klasy. Przy regule bez osłabiania
nie ma czego rozcieńczać i lepsza jest izolacja (rzadki kod). Skrypt `run_mechanism.py`,
Split-MNIST, architektura domyślna, sieci 0–4 × kolejności 0, 1, oba neurony.

Nowe reguły (`learning.py`): `rstdp_raw`, `delta_raw` — bez normalizacji per obraz (stała skala
dobrana przy f_c, żeby średnia wielkość zmian była porównywalna); `rmix` — `rgate` z udziałem
osłabiania λ (przy pomyłce wagi do wybranego wyjścia maleją o λ·η·ĉ).

**Kryteria** (każde osobno dla Izhikevicha i LIF, Wilcoxon parowany po 10 przebiegach):
- **H-M1 (rozcieńczanie):** w oknach nowości (pierwsze 300 obrazów zadań 2–5) część zmian wag
  trafiająca w wagi starych klas na ich neuronach jest **mniejsza** przy „nowość → gęściej” niż
  przy stałym f o tej samej średniej ocenianym na tym samym poziomie (`matched_inv_evalrest`);
  p < 0.05, ≥ 8/10, dla R-STDP i delta.
- **H-M2 (rola normalizacji):** przewaga „nowość → gęściej” (Δ(−1)) jest **mniejsza** bez
  normalizacji niż z nią (Δ(−1)_raw − Δ(−1)_norm < 0, p < 0.05), dla R-STDP i delta.
- **H-M3 (kontrola oceny):** „nowość → gęściej” zapomina mniej niż stałe f o tej samej średniej
  oceniane na tym samym (rzadkim) poziomie — Δ(−1)_evalrest > 0, p < 0.05, ≥ 8/10, dla R-STDP
  i delta. Jeśli nie — wcześniejsza przewaga była artefaktem poziomu oceny.
- **H-M4 (udział osłabiania):** Δ(+1) zmienia znak z λ: Δ(+1) > 0 przy λ = 0 i Δ(+1) < 0 przy
  λ = 1, oba p < 0.05.

**Mechanizm uznajemy za poparty**, jeśli H-M3 i H-M4 przechodzą dla obu neuronów, a H-M1 lub
H-M2 dla co najmniej jednego czytnika z osłabianiem.

### 6g. E3.7 — sieć z warstwą ukrytą uczoną trójczynnikowo (zapisane 2026-10-27, PRZED uruchomieniem)

Skrypt `run_hidden.py`: kod DG → warstwa ukryta (500 jednostek ReLU) → 10 wyjść; obie warstwy
uczone regułą typu AGREL (Roelfsema & van Ooyen 2005; nagroda × sprzężenie zwrotne od
wybranego wyjścia × aktywność). Warianty: `agrel` (błąd predykcji nagrody może być ujemny →
osłabianie) i `agrel_pos` (tylko nagroda zmienia wagi → bez osłabiania); skalowanie synaptyczne
w obu. η strojone na sieci 99 (MNIST statycznie, walidacja), regulator z pilotażu na sieci 99;
f_gęsty/f_rzadki = 10%/3%. Jednostki warstwy ukrytej są „częstotliwościowe” (nie impulsowe).

**Kryterium (H-L1):** przewidywanie zasady z E3.5/E3.8 — Δ(+1) („nowość → rzadziej” vs stałe f
o tej samej średniej) **ujemne** dla `agrel` i **dodatnie** dla `agrel_pos`; w każdej z 4 komórek
(wariant × neuron) Wilcoxon p < 0.05 i właściwy znak w ≥ 8/10 przebiegach. Zasada przenosi się
na sieć z warstwą ukrytą, jeśli przechodzą wszystkie 4 komórki.

### 6h. E3.9 — zapominanie: przewaga nowych klas czy zniszczenie starych wag? (zapisane 2026-10-28, PRZED uruchomieniem)

**Hipoteza** (z E3.8, sek. 12f): przy czytnikach z osłabianiem (R-STDP, delta) zapominanie na
Split-MNIST class-incremental to głównie **przewaga nowych klas** — wiedza o starych klasach
zostaje w wagach, ale wyjścia nowszych klas wygrywają na obrazach starych klas. „Nowość →
gęściej” zapomina mniej, bo ogranicza tę przewagę. Skrypt `run_errors.py`: te same warunki
i ziarna co w E3.8 (mod, inv, stałe f o tej samej średniej, `matched_inv_evalrest`), czytniki
rstdp, delta, rgate, sieci 0–4 × kolejności 0, 1, oba neurony. Po nauce wszystkich zadań, na
obrazach testowych zadań 1–4 (cyfry 0–7):

- `acc_class` — dokładność 10-klasowa; `acc_within` — wybór ograniczony do 2 klas prawdziwego
  zadania; `acc_debiased` — po standaryzacji każdego wyjścia na zbalansowanej próbce obrazów
  treningowych wszystkich klas (korekta „z wyrocznią”, jak BiC);
- `err_newer` / `err_last` — część błędów wskazujących klasę nowszego / ostatniego zadania.

**Kryteria** (każde osobno dla neuronu × czytnika z osłabianiem, Wilcoxon parowany, 10 przebiegów):
- **H-R1 (wiedza zostaje):** przy stałym f (`matched_mod`) `acc_within` ≥ 0.80 (średnio) i
  `acc_within − acc_class` ≥ 0.30, p < 0.05, ≥ 8/10.
- **H-R2 (błędy idą w nowe klasy):** przy stałym f `err_newer` ≥ 0.80 (średnio, ≥ 8/10 przebiegów).
- **H-R3 (gęściej = mniej przejmowania):** `err_last` mniejsze przy „nowość → gęściej” niż
  przy `matched_inv_evalrest` (ta sama ocena), p < 0.05, ≥ 8/10; oraz `acc_within` różni się
  o mniej niż 0.03 (różnica dokładności wynika z przechylenia, nie z wiedzy).
- **H-R4 (korekta odzyskuje):** `acc_debiased − acc_class` ≥ 0.20 przy stałym f, p < 0.05.

**Mechanizm „przewagi nowych klas” uznajemy za poparty**, jeśli H-R1, H-R2 i H-R3 przechodzą
dla delty i R-STDP u obu neuronów (H-R4 — pomocniczo). Jeśli H-R1 nie przechodzi
(`acc_within` niskie), zapominanie to zniszczenie starych wag. rgate raportujemy opisowo
(oczekiwanie: mała przewaga nowych klas, bo prawie nie zapomina).

### 6i. E3.7b — warstwa ukryta bez osłabiania heterosynaptycznego (zapisane 2026-10-28, PRZED uruchomieniem)

Powód: w E3.7 (sek. 12g) normalizacja wag jednostki ukrytej wspólnej dla klas działała jak
osłabianie, więc `agrel_pos` nie był wariantem „bez osłabiania”. `run_hidden.py`, trzy nowe
warianty (szczegóły w docstringu): `pos_bound` (tylko nagroda, W1 bez normalizacji, wagi
przycięte do ±4/√n_in), `pos_pool` (tylko nagroda, 10 pul po 50 jednostek przypisanych
wyjściom — normalizacja tylko w obrębie klasy), `agrel_bound` (z osłabianiem, W1 ograniczone
jak w `pos_bound` — kontrola kierunku). Procedura jak w 6g: η z {0.01, 0.03, 0.1, 0.3} na sieci 99,
regulator z pilotażu na sieci 99, f_gęsty/f_rzadki = 10%/3%, sieci 0–4 × kolejności 0, 1.

**Kryterium (H-L1b):** Δ(+1) **dodatnie** dla `pos_bound` i `pos_pool`, **ujemne** dla
`agrel_bound`; w każdej komórce (wariant × neuron) Wilcoxon p < 0.05 i właściwy znak w ≥ 8/10.
**Warunek sensowności:** komórka jest rozstrzygająca tylko, jeśli ACC przy stałym f > 0.25
(czyli więcej niż „pamięta tylko ostatnie zadanie” ≈ 0.20); w przeciwnym razie raportujemy ją
jako nierozstrzygającą, a nie jako obalenie. Zasada przenosi się na warstwę ukrytą, jeśli
przechodzą wszystkie rozstrzygające komórki i jest ich co najmniej 4 z 6, w tym oba warianty
„tylko nagroda” dla co najmniej jednego neuronu.

### 6j. E3.9h — rozbicie błędów dla sieci z warstwą ukrytą (zapisane 2026-10-29, PRZED uruchomieniem)

Pytanie: czy prawie całkowite zapominanie **wspólnej** warstwy ukrytej (E3.7 `agrel_pos`, E3.7b
`pos_bound`; BWT ≈ −0.7…−0.9) to też przewaga nowych klas, jak przy czytnikach liniowych z
osłabianiem (E3.9), czy zniszczenie reprezentacji starych klas? Kontrola: `pos_pool`. Skrypt
`run_hidden_errors.py`: te same sieci, ziarna, η i regulator co E3.7/E3.7b; miary jak w 6h.
Warunki: stałe f przy f_c (`fixed`), g = +1 i jego stałe f, g = −1 i stałe f o jego średniej
oceniane na tym samym poziomie (`matched_inv_evalrest`).

**Kryteria** (osobno dla wariantu wspólnego × neuron, warunek `fixed`, 10 przebiegów):
- **przewaga nowych klas**, jeśli `acc_within` ≥ 0.80 (średnio), `acc_within − acc_class` ≥ 0.30
  (p < 0.05, ≥ 8/10) i `err_newer` ≥ 0.80 (średnio);
- **zniszczenie reprezentacji**, jeśli `acc_within` < 0.65 (losowo = 0.50);
- w pozostałych przypadkach — mieszane (raportujemy liczby).
Pomocniczo: czy „nowość → rzadziej” (które w `pos_bound` zmniejsza zapominanie o 0.18) podnosi
`acc_within` (ochrona wiedzy) czy tylko obniża `err_last` (mniej przejmowania) — porównanie
`mod` z `matched_mod`, Wilcoxon.

### 6k. Fig. 1 — poziomy f 70% i 90% (2026-10-29, opisowo)

Uzupełnienie E3.1 bez zmiany istniejących kodów: osobne kody dla f ∈ {0.70, 0.90}
(`precompute_codes.py --levels 0.7 0.9 --tag hi` → `results/codes/{neuron}_s{seed}_hi.npy`)
i E3.1 na nich (`run_static.py --exp e31 --codes-tag hi` → `results/e31_hi/`); te same sieci 0–4,
te same η. Bez kryterium — pytanie opisowe: czy po maksimum przy 10–25% dokładność dalej spada
i czy losowa projekcja zachowuje się tak samo. Uwaga: przy f = 90% K może spaść poniżej −4
(G_crit < 0), czyli neurony strzelają bez wejścia — zapisujemy K w meta.

### 6d. E3.7 — sieć uczona R-STDP z warstwą ukrytą (plan pierwotny; zrealizowany jako 6g)

Uwaga z 2026-10-22: wynik może zależeć od tego, *jaka sieć* uczy się regułą
trójczynnikową — dotąd uczył się tylko czytnik liniowy na stałym kodzie. E3.7: warstwa
ukryta między DG a czytnikiem (albo plastyczne połączenia PP→DG), uczona trójczynnikowo
z sygnałem zwrotnym od wybranego wyjścia (typu AGREL, Roelfsema & van Ooyen 2005).
Kodów nie da się wtedy liczyć z góry — wymaga symulacji w pętli na GPU. Rozpocząć po
wynikach E3.5 i E3.6.
