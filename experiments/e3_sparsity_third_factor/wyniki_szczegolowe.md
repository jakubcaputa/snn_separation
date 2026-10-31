# E3 — wyniki szczegółowe (wszystkie tabele liczb)

*Przeniesione 2026-10-31 z README.md bez zmian treści (sek. 12–12k). Kryteria, do których odnoszą się werdykty: prereg.md. Objaśnienia wykresów: results.md. Szczegóły implementacji i zmian po E3.0: archiwum_plan.md sek. 11.*

## 12. Wyniki — przebieg główny (sieci 0–4; 2026-10-13)

Figury podsumowujące: `figures/` (w repo). Figury robocze: `results/figures/` (poza repo).
Liczby: `results/summary.json`.

### E3.1 — H-E3a: **przechodzi** (4/4 kombinacje)

Dokładność ma maksimum w punkcie wewnętrznym siatki f w 5/5 sieciach dla każdej
kombinacji, a dekorelacja `dec` maleje z f monotonicznie (Spearman = −1.0 w każdej
sieci). Średnie po 5 sieciach (Izhikevich):

| f | R-STDP | delta | sufit (logist.) | losowa projekcja, R-STDP | dec |
|---|---|---|---|---|---|
| 1% | 0.640 | 0.630 | 0.701 | 0.680 | 0.295 |
| 5% | 0.858 | 0.853 | 0.895 | 0.888 | 0.273 |
| 10% | **0.886** | 0.897 | 0.926 | 0.911 | 0.258 |
| 20% | 0.858 | **0.909** | 0.936 | 0.898 | 0.241 |
| 30% | 0.804 | 0.907 | 0.938 | 0.850 | 0.230 |
| 50% | 0.728 | 0.888 | 0.931 | 0.782 | 0.217 |
| piksele | 0.816 | 0.865 | 0.924 | — | — |

Maksimum: R-STDP przy f ≈ 10–20%, delta przy 17–25% (LIF podobnie, R-STDP
0.909–0.914, delta 0.923–0.926). **Najrzadszy kod ma najwyższą dekorelację
i najgorszą dokładność** — funkcjonalny odpowiednik wyniku E1. Uwaga: kod DG
nie jest lepszy od losowej projekcji o tym samym f (przy R-STDP nawet nieco gorszy),
zgodnie z wynikiem 1A (STATUS sek. 3.7).

### E3.2 — H-E3b: **obalona** (w przeciwnym kierunku niż E1′)

Przy wyrównanym f hamowanie fazowe **obniża** dokładność; nachylenia istotne po
korekcie Bonferroniego w 6 z 8 testów. Średnie po 5 sieciach (R-STDP / delta):

| | W_FS_GC = 0 | 1 | 2 | 3 | 5 |
|---|---|---|---|---|---|
| izh, f = 5% | 0.858 / 0.853 | 0.868 / 0.884 | 0.867 / 0.882 | 0.865 / 0.878 | 0.857 / 0.869 |
| izh, f = 20% | 0.858 / 0.909 | 0.797 / 0.891 | 0.764 / 0.879 | 0.773 / 0.870 | 0.734 / 0.855 |
| lif, f = 5% | 0.883 / 0.853 | 0.872 / 0.895 | 0.730 / 0.869 | 0.694 / 0.853 | 0.657 / 0.838 |
| lif, f = 20% | 0.878 / 0.924 | 0.625 / 0.875 | 0.626 / 0.845 | 0.597 / 0.831 | 0.517 / 0.811 |

Wyjątek: słabe hamowanie fazowe (W = 1) przy f = 5% lekko pomaga czytnikowi delta.
W E1′ hamowanie fazowe nie zmieniało *separacji*; tutaj szkodzi *użyteczności* kodu.
Mechanizmu nie badaliśmy (kandydaci: zwrotne hamowanie ucina impulsy najsilniej
pobudzonych neuronów albo dodaje zmienność czasową, której czytnik liczący impulsy
nie wykorzystuje).

### E3.3 — H-E3c: **obalona** (w przeciwnym kierunku), H-E3d: **obalona**

Średnie po 10 przebiegach (5 sieci × 2 kolejności). BWT = zapominanie (bliżej 0 = lepiej).

| warunek | izh × R-STDP: ACC / BWT | lif × R-STDP | izh × delta | lif × delta |
|---|---|---|---|---|
| fixed_dense | 0.285 / −0.469 | 0.266 / −0.641 | 0.207 / −0.975 | 0.215 / −0.967 |
| fixed_sparse | 0.426 / −0.426 | 0.406 / −0.507 | 0.247 / −0.908 | 0.292 / −0.851 |
| **mod_novelty** | 0.270 / −0.688 | 0.283 / −0.715 | 0.206 / −0.975 | 0.215 / −0.964 |
| **fixed_matched** | 0.355 / −0.418 | 0.352 / −0.512 | 0.222 / −0.953 | 0.254 / −0.917 |
| 3f_lr | 0.281 / −0.638 | 0.267 / −0.665 | 0.205 / −0.977 | 0.220 / −0.961 |
| 3f_both | 0.212 / −0.823 | 0.249 / −0.791 | 0.198 / −0.986 | 0.200 / −0.981 |
| mod_novelty_inv | **0.389 / −0.279** | **0.412 / −0.389** | **0.283 / −0.865** | **0.344 / −0.768** |
| oracle_boundary | 0.290 / −0.486 | 0.294 / −0.640 | 0.210 / −0.972 | 0.224 / −0.956 |
| kwta_fly (FlyModel) | **0.653 / −0.057** | (ten sam) | — | — |

- **H-E3c:** `mod_novelty` zapomina **więcej** niż `fixed_matched` we wszystkich 4
  kombinacjach (różnica BWT −0.02 … −0.27, 0/10 dodatnich, p = 0.002). Rzadszy kod
  przy nowości szkodzi.
- **H-E3d:** `mod_novelty` vs `3f_lr` — brak istotnej różnicy (p = 0.13–0.56).
- **Regulator działa zgodnie z założeniem:** na granicy zadania n rośnie
  (np. 0.01 → 0.90) i f spada z 10% do ~3.6%; nie jest to więc wynik źle
  działającej pętli.
- **Eksploracyjnie:** `mod_novelty_inv` (nowość → gęstszy kod) zapomina mniej niż
  `fixed_matched` we wszystkich 4 kombinacjach (+0.09 … +0.15, 8–10/10 dodatnich) i
  mniej niż `fixed_sparse`. Ale `fixed_matched` był dopasowany do średniego f
  `mod_novelty`, nie `mod_novelty_inv` (dla lif × R-STDP: 5.4% vs 7.0%), więc część
  efektu może wynikać z rzadkości. Stąd test potwierdzający z własną kontrolą (sek. 6a).
- **Nakładanie neuronów używanych przez kolejne zadania** (neurony aktywne w ≥ 1%
  obrazów zadania) jest wysokie we wszystkich warunkach (0.6–1.0) i nie tłumaczy
  przewagi `mod_novelty_inv` (izh × R-STDP: 0.84 vs 0.85 dla `fixed_matched`).
- **Reguła delta zapomina prawie całkowicie** w każdym warunku (BWT ≈ −0.9): przy
  wspólnym czytniku 10-klasowym aktywnie obniża wyjścia klas nieobecnych w zadaniu.
- **FlyModel jest daleko najlepszy** (ACC 0.65, BWT −0.06). Jego reguła tylko
  wzmacnia wagi klasy docelowej i z konstrukcji niczego nie osłabia; nasze czytniki
  (R-STDP z R − R̄, delta) osłabiają wagi innych klas. Sposób uczenia czytnika waży
  tu więcej niż poziom rzadkości.

### 12a. Test potwierdzający H-E3e (sieci 5–9, kryterium z sek. 6a) — **nie przeszedł**

BWT(`mod_novelty_inv`) − BWT(`fixed_matched_inv`), 10 przebiegów na kombinację:

| kombinacja | sieci 0–4 (eksploracyjnie) | **sieci 5–9 (potwierdzenie)** |
|---|---|---|
| izh × R-STDP | +0.139, 8/10, p = 0.010 | **+0.066, 7/10, p = 0.275 — nie spełnia** |
| lif × R-STDP | +0.172, 9/10, p = 0.014 | **+0.108, 9/10, p = 0.010 — spełnia** |
| izh × delta (poza werdyktem) | +0.088, 10/10, p = 0.002 | +0.086, 10/10, p = 0.002 |
| lif × delta (poza werdyktem) | +0.166, 10/10, p = 0.002 | +0.162, 10/10, p = 0.002 |

**Werdykt według zapisanego kryterium: H-E3e niepotwierdzona** — wymagało spełnienia
w obu kombinacjach z R-STDP, a przy Izhikevichu efekt ma ten sam znak, ale jest
mniejszy i zmienny (SD różnicy 0.17); `mod_novelty_inv` jest tam praktycznie równy
`fixed_sparse` (BWT −0.424 vs −0.427). Kierunek jest jednak spójny we wszystkich 8
porównaniach (efekt dodatni), a przy czytniku delta i przy LIF + R-STDP efekt jest
duży i powtarzalny. Uczciwy opis: **„nowość → gęstszy kod” zmniejsza zapominanie
względem stałego f o tej samej średniej w większości konfiguracji, ale nie we
wszystkich; przy Izhikevichu z R-STDP nie odróżnia się od stałego rzadkiego kodu.**

**H-E3c powtarza się na nowych sieciach:** `mod_novelty` zapomina więcej niż
`fixed_matched` we wszystkich 4 kombinacjach (0–2/10 dodatnich, p ≤ 0.027).
FlyModel: ACC 0.662, BWT −0.063 (jak w przebiegu głównym).

### 12b. E3.4 — kod × reguła czytnika (eksploracyjnie, f = 5%, 20 przebiegów na neuron)

ACC / BWT, średnie po 10 sieciach × 2 kolejnościach (izh; lif w nawiasie, gdy inny):

| kod \ reguła | FlyModel (tylko klasa docelowa) | R-STDP (R − R̄) | delta |
|---|---|---|---|
| k-WTA (FlyModel) | **0.658 / −0.060** | 0.379 / −0.574 (lif 0.312 / −0.649) | 0.204 / −0.984 |
| DG, impulsy | 0.203 / −0.008 (lif 0.224 / −0.011) | 0.381 / −0.450 (lif 0.355 / −0.541) | 0.244 / −0.911 (lif 0.292 / −0.841) |

- **Zapominanie wyznacza reguła, nie kod.** Przy obu kodach reguła FlyModelu
  zapomina o 0.44–0.59 mniej niż R-STDP i o 0.83–0.92 mniej niż delta (20/20
  przebiegów, p < 0.001). Reguły, które osłabiają wagi innych klas, zapominają
  niezależnie od kodu.
- **Reguła FlyModelu na kodzie DG prawie się nie uczy** (ACC 0.20; BWT ≈ 0 tylko
  dlatego, że nie ma czego zapominać — dokładność na bieżącym zadaniu 0.0–0.57).
  Przyczyna (sprawdzone na izh, sieć 0): nawet po normalizacji wejścia liczba
  aktywnych neuronów DG na obraz waha się od 18 do 242 (5.–95. percentyl, mediana 88),
  podczas gdy k-WTA ma zawsze 100. Reguła „dodaj kod do wag klasy” robi z wag sumę
  kodów, a iloczyn skalarny faworyzuje klasy o „szerokich” kodach. Po normalizacji
  kodu per obraz (‖c‖ = 1): ACC 0.502, BWT −0.059 (dokładność na bieżących
  zadaniach 0.22–0.91) — blisko braku zapominania FlyModelu, ale niższa dokładność.
- To ten sam problem co w E3.0, tylko słabszy: **hamowanie toniczne (globalny próg)
  nie wyrównuje aktywności między wzorcami**, a k-WTA — czyli hamowanie zależne od
  aktywności — tak. Reguła FlyModelu tego wymaga; R-STDP z normalizacją wejścia
  (ĉ = c/‖c‖, sek. 11) jest na to odporna (DG ≈ k-WTA: 0.38 vs 0.38).

**Normalizacja kodu DG per obraz na wszystkich 40 przebiegach** (`dg5n`, dodane
2026-10-22; ACC / BWT):

| reguła FlyModelu | k-WTA | DG (globalny próg) | DG znormalizowany (‖c‖ = 1) |
|---|---|---|---|
| Izhikevich | 0.658 / −0.060 | 0.203 / −0.008 | 0.498 / −0.055 |
| LIF | 0.658 / −0.060 | 0.224 / −0.011 | 0.551 / −0.061 |

Normalizacja odzyskuje większość dokładności i przywraca zapominanie FlyModelu, ale
k-WTA jest nadal lepszy o 0.11–0.16 (20/20, p < 0.001): normalizacja wyrównuje skalę
kodu, a k-WTA także *liczbę* aktywnych neuronów. Dla R-STDP `dg5n` ≡ `dg5` (0.380 vs
0.381) — zgodnie z oczekiwaniem, bo ta reguła już normalizuje wejście (test poprawności).

**Wniosek dla kierunku pracy:** jeśli celem jest uczenie bez zapominania, ważniejsze
od sterowania rzadkością są (1) reguła czytnika, która nie osłabia innych klas,
oraz (2) normalizacja aktywności per wzorzec (k-WTA albo hamowanie zwrotne
zależne od aktywności), a nie tylko globalny próg.

### 12c. E3.5 — wyniki (2026-10-23)

**Werdykt wg sek. 6b: kryterium 1 NIE przeszło** (Δ(+1) < 0 w 24/36 komórkach, **12 istotnie
dodatnich**), kryterium 2 (rgate) — wszystkie 12/12 komórek istotnie dodatnie. 12 komórek
przeciwnych to dokładnie **wszystkie** komórki z czytnikiem `rgate`, w każdej z 6 architektur
(N = 500, 1000, 2000, 5000; fan-in 10, 30, 100) i przy obu neuronach: Δ(+1) od +0.021 do +0.047
(6/6 albo 10/10 dodatnich). Przy R-STDP i delta Δ(+1) jest ujemne we wszystkich 24 komórkach
(od −0.015 do −0.272). **Kierunek efektu „nowość → rzadziej” wyznacza reguła uczenia czytnika,
nie rozmiar warstwy DG ani fan-in.** Δ(−1) („nowość → gęściej”) dodatnie przy R-STDP/delta,
bliskie zera przy rgate. Figura: `figures/fig7_e35_dose_response.png`.

Architektura domyślna, szczegółowo (Δ(g) = BWT(mod g) − BWT(stałe f o tej samej średniej), 10 przebiegów na komórkę:

| neuron × czytnik | ACC (g = 0) | Δ(−1) | Δ(+0.5) | **Δ(+1)** |
|---|---|---|---|---|
| izh × R-STDP | 0.381 | +0.088 (9/10) | −0.118 (2/10) | **−0.263 (0/10, p = 0.002)** |
| izh × delta | 0.229 | +0.088 (10/10) | −0.019 (0/10) | **−0.021 (0/10, p = 0.002)** |
| izh × **rgate** | 0.766 | +0.007 (10/10) | +0.022 (10/10) | **+0.047 (10/10, p = 0.002)** |
| lif × R-STDP | 0.371 | +0.174 (9/10) | −0.146 (0/10) | **−0.249 (0/10, p = 0.002)** |
| lif × delta | 0.263 | +0.165 (10/10) | −0.039 (0/10) | **−0.047 (0/10, p = 0.002)** |
| lif × **rgate** | 0.743 | −0.005 (0/10) | +0.008 (10/10) | **+0.023 (10/10, p = 0.002)** |

**Przy czytniku bez osłabiania (`rgate`) „nowość → rzadziej” zmniejsza zapominanie**
(10/10 w obu neuronach) — kierunek H-E3c. Według kryterium z sek. 6b obalenie H-E3c
**nie jest więc ogólne**: zależy od reguły, którą uczy się sieć. Efekt jest mały, bo
`rgate` i tak prawie nie zapomina (BWT −0.08 → −0.03 przy izh), i ma koszt: przy
Izhikevichu końcowa dokładność spada (ACC 0.731 vs 0.766, 0/10), przy LIF bez zmian
(0.752 vs 0.750). To kompromis stabilność–czułość, ten sam, który dla hamowania w DG
opisują Pérez-Montoyo i in. 2026. Zastrzeżenia: η `rgate` wyszło na brzegu siatki
strojenia (0.01), a f_gęsty dla izh × rgate = 50% (też brzeg).

### 12d. E3.6 — zadanie separacji wzorców z `dg_core` (2026-10-24)

**Werdykt wg sek. 6c: kryterium NIE przeszło** — Δ(+1) < 0 tylko w 3/9 komórkach, 5 istotnie
dodatnich. 6 przebiegów na komórkę (sieci 0–2 × 2 kolejności), Wilcoxon (min. p = 0.031):

| R_in \ czytnik | R-STDP | delta | rgate |
|---|---|---|---|
| 0.5 (ACC przy g = 0: 0.44 / 0.47 / 0.88) | **+0.076 (6/6)** | **+0.343 (6/6)** | **+0.037 (6/6)** |
| 0.75 (0.23 / 0.24 / 0.40) | −0.095 (3/6) | +0.035 (2/6) | **+0.035 (6/6)** |
| 0.9 (0.15 / 0.16 / 0.18) | −0.022 (2/6) | −0.042 (2/6) | **+0.030 (6/6)** |

- **Przy czytniku `rgate` „nowość → rzadziej” zmniejsza zapominanie przy każdym podobieństwie
  wzorców** — jak na MNIST (E3.5).
- Przy małym podobieństwie (R_in = 0.5) pomaga także przy R-STDP i delta.
- Przy dużym podobieństwie (0.75, 0.9) i czytnikach R-STDP/delta efekt Δ(+1) jest nieistotny,
  a wyraźnie pomaga kierunek odwrotny (Δ(−1) = +0.08 … +0.18, 5–6/6) — jak w E3.3.
- Zastrzeżenia: przy R_in = 0.9 dokładności są blisko losowych (0.15–0.18 przy 10 klasach),
  więc te komórki mało rozstrzygają; E3.6 liczone na STAREJ kalibracji `dg_core` (sek. 6c).

### 12e. E3.6x — zadanie separacji wzorców na modelu skalibrowanym do skrawka (2026-10-25)

**Werdykt wg sek. 6e: kryterium NIE przeszło** (Δ(+1) < 0 w 6/9 komórkach, 2 istotnie dodatnie).
Δ(+1) („nowość → rzadziej” vs stałe f o tej samej średniej), w nawiasie stara kalibracja (E3.6):

| R_in \ czytnik | R-STDP | delta | rgate |
|---|---|---|---|
| 0.5 | **+0.127 (6/6)** (+0.076) | −0.333 (0/6) (**+0.343**) | **+0.023 (6/6)** (+0.037) |
| 0.75 | −0.032 (4/6, n.i.) (−0.095) | −0.617 (0/6) (+0.035) | +0.012 (5/6, n.i.) (+0.035) |
| 0.9 | −0.133 (0/6) (−0.022) | −0.483 (0/6) (−0.042) | −0.015 (0/6, n.i.) (+0.030) |

- **Zgodny kierunek z E3.6 w 6/9 komórkach.** Zmiana znaku: delta przy R_in 0.5 i 0.75 (w modelu
  ex vivo reguła delta zapomina dużo silniej przy modulacji — efekty ±0.3–0.6) oraz rgate przy
  R_in 0.9 (tam dokładność ≈ poziom losowy, 0.16, więc komórka nie rozstrzyga).
- **Nowy wzór: kierunek zależy od podobieństwa wzorców.** Przy mało podobnych wzorcach
  (R_in 0.5) „nowość → rzadziej” pomaga dla R-STDP i rgate; przy bardzo podobnych (0.9)
  szkodzi dla R-STDP i delta, a pomaga „nowość → gęściej” (Δ(−1) = +0.08 … +0.60). To zgadza
  się z Pérez-Montoyo i in. 2026: słabsze hamowanie przy kodowaniu podobnych doświadczeń
  poprawia ich późniejsze rozróżnianie.
- Przy rgate efekty są małe w liczbach bezwzględnych (≤ 0.03), jak na MNIST.
- Zastrzeżenia: przy R_in 0.75–0.9 dokładności są niskie (0.15–0.30); najniższe poziomy f
  w praktyce 4–6% (sek. 6e); kalibracja ex vivo nie odtwarza efektu gabazyny (×1.25 vs ×1.6).

### 12f. E3.8 — test mechanizmu (2026-10-27)

**Werdykt wg sek. 6f: mechanizm „rozcieńczania” NIE jest poparty** (H-M1 odwrotnie, H-M4 nie
przeszło); rola osłabiania wag jest jednak widoczna. 10 przebiegów na neuron:

| kryterium | Izhikevich | LIF | wynik |
|---|---|---|---|
| **H-M1** szkoda w oknach nowości: „gęściej” < stałe f (ta sama ocena) | R-STDP +0.016 (n.i.), delta **+0.153 (10/10)** | R-STDP +0.016 (n.i.), delta **+0.152 (10/10)** | ❌ **odwrotnie**: przy „nowość → gęściej” *więcej* zmian trafia w wagi starych klas, a mimo to zapominanie jest mniejsze |
| **H-M2** bez normalizacji przewaga „gęściej” maleje | R-STDP −0.105 (n.i.), delta **−0.055 (0/10, p = 0.002)** | R-STDP −0.064 (n.i.), delta **−0.107 (0/10, p = 0.002)** | ✅ dla delty, ❌ dla R-STDP |
| **H-M3** „gęściej” lepsze od stałego f ocenianego na tym samym poziomie | R-STDP +0.050 (9/10, p = 0.084), delta **+0.054 (10/10)** | R-STDP +0.132 (7/10, p = 0.027), delta **+0.089 (10/10)** | ✅ dla delty, ⚠️ R-STDP (kierunek zgodny, kryterium niespełnione) |
| **H-M4** znak Δ(+1) zmienia się z udziałem osłabiania λ | λ = 0: **+0.047 (10/10)**; λ = 0.25: **−0.032 (0/10)**; λ ≥ 0.5: ≈ 0 | λ = 0: **+0.023 (10/10)**; λ = 0.25: **−0.006 (1/10)**; λ ≥ 0.75: +0.011 | ❌ wg kryterium (przy λ = 1 nie ujemne), ale znak odwraca się już przy λ = 0.25 |

Co z tego wynika:
- **Osłabianie odwraca kierunek — i to już niewielkie.** Wystarczy λ = 0.25 (przy pomyłce wagi
  maleją o ćwierć tego, o ile rosną przy trafieniu), by „nowość → rzadziej” z pomocnego stało się
  szkodliwe (10/10 → 0/10 i 1/10). Przy λ ≥ 0.5 reguła przestaje się uczyć (ACC przy stałym f:
  0.21 → 0.19 dla Izhikevicha), więc różnice znikają — dlatego kryterium przy λ = 1 nie przeszło.
- **Przewaga „nowość → gęściej” przy osłabianiu nie jest artefaktem poziomu oceny** (H-M3:
  przetrwała kontrolę dla delty, kierunek zgodny dla R-STDP), ale **nie wynika z rozcieńczania
  szkody** (H-M1 odwrotnie). Nowa hipoteza do sprawdzenia: przy regułach z osłabianiem
  zapominanie w scenariuszu class-incremental to głównie *przewaga nowych klas* (ich wyjścia
  wygrywają na obrazach starych klas), a nie zniszczenie starych wag; gęsty kod przy nauce nowych
  klas rozkłada ich wagi na wiele neuronów, więc przy ocenie na rzadkim kodzie nowe klasy mają
  słabsze wyjścia i mniej „przejmują” stare obrazy.
- Normalizacja per obraz ma znaczenie dla delty (bez niej przewaga „gęściej” maleje o połowę),
  nie dla R-STDP.

### 12g. E3.7 — sieć z warstwą ukrytą uczoną trójczynnikowo (2026-10-27)

**Werdykt wg sek. 6g: H-L1 nie przeszło — test nierozstrzygający.** 10 przebiegów na komórkę:

| wariant × neuron | ACC (stałe f) | BWT (stałe f) | Δ(+1) | Δ(−1) |
|---|---|---|---|---|
| agrel (z osłabianiem) × Izhikevich | 0.185 | −0.947 | +0.004 (5/10, n.i.) | +0.007 (8/10) |
| agrel × LIF | 0.175 | −0.957 | +0.006 (5/10, n.i.) | +0.018 (10/10) |
| agrel_pos (bez osłabiania) × Izhikevich | 0.162 | −0.919 | −0.016 (1/10, p = 0.004) | +0.032 (10/10) |
| agrel_pos × LIF | 0.167 | −0.922 | −0.020 (0/10, p = 0.002) | +0.044 (10/10) |

- **Obie wersje zapominają prawie całkowicie** (ACC ≈ 0.17, czyli „pamięta tylko ostatnie
  zadanie”), więc pytanie o kierunek modulacji jest tu słabo postawione.
- **Wariant „bez osłabiania” nie jest w praktyce bez osłabiania.** Skalowanie synaptyczne
  normalizuje wagi każdej jednostki ukrytej, a te jednostki są wspólne dla wszystkich klas:
  wzmocnienie wejść dla nowej klasy obniża (po normalizacji) wejścia używane przez stare klasy —
  to osłabianie heterosynaptyczne. W czytniku `rgate` tego nie było, bo każda kolumna wag
  należy do jednej klasy. Zgodnie z tym w obu wariantach zachowanie przypomina reguły
  z osłabianiem (Δ(−1) > 0, Δ(+1) ≤ 0).
- **Następny krok dla tej osi:** warstwa ukryta bez normalizacji wspólnej dla klas (np. ograniczenie
  wag zamiast normalizacji, albo pule jednostek przypisane wyjściom), żeby rzeczywiście mieć
  wariant bez osłabiania.

### 12h. E3.9 — przewaga nowych klas czy zniszczenie starych wag? (2026-10-29)

**Werdykt wg sek. 6h: mechanizm „przewagi nowych klas” poparty dla delty, dla R-STDP częściowo**
(H-R1, H-R2, H-R4 ✅ wszędzie; H-R3 ✅ dla delty, ❌ dla R-STDP). 10 przebiegów na komórkę,
obrazy testowe cyfr 0–7 po nauce wszystkich zadań, stałe f (`matched_mod`):

| czytnik × neuron | dokładność 10-klasowa | w obrębie zadania | po wyrównaniu wyjść | błędy → nowsze klasy | błędy → ostatnie zadanie |
|---|---|---|---|---|---|
| R-STDP × Izhikevich | 0.36 | **0.91** | 0.73 | 0.96 | 0.55 |
| R-STDP × LIF | 0.32 | **0.92** | 0.76 | 0.99 | 0.92 |
| delta × Izhikevich | 0.04 | **0.85** | 0.53 | 1.00 | 0.99 |
| delta × LIF | 0.08 | **0.83** | 0.54 | 1.00 | 0.99 |
| rgate × Izhikevich | 0.79 | 0.96 | 0.79 | 0.52 | 0.34 |
| rgate × LIF | 0.78 | 0.95 | 0.77 | 0.51 | 0.30 |

H-R3 („nowość → gęściej” vs stałe f o tej samej średniej i tej samej ocenie): część błędów
wskazujących ostatnie zadanie mniejsza o 0.025 (Izh.) i 0.070 (LIF) dla delty, 10/10, p = 0.002,
przy niezmienionej dokładności w obrębie zadania (−0.002, −0.008) ✅. Dla R-STDP różnica jest
większa (−0.26, −0.21), ale niespójna (5/10, 7/10; p = 0.16), a dokładność w obrębie zadania
spada o 0.04–0.05 (próg 0.03) ❌.

Co z tego wynika:
- **Przy regułach z osłabianiem stara wiedza w większości przetrwa.** Gdy wybór ogranicza się do
  2 klas właściwego zadania, czytnik nadal rozpoznaje 83–92% starych obrazów; prawie wszystkie
  błędy to obrazy „przejęte” przez klasy nowszych zadań (dla delty — niemal wyłącznie ostatniego).
  Zwykła dokładność (0.04–0.36) mierzy więc głównie przechylenie wyjść, nie utratę wiedzy.
- **Samo wyrównanie skali wyjść odzyskuje 0.36–0.49 dokładności** (H-R4); korekta „z wyrocznią”
  korzysta z danych starych klas, więc to miara ukrytej wiedzy, nie metoda.
- **„Nowość → gęściej” pomaga, bo zmniejsza przejmowanie, nie dlatego, że chroni wiedzę** —
  dla delty wiedza w obrębie zadania jest ta sama, mniej obrazów wygrywa ostatnia klasa.
  „Nowość → rzadziej” robi odwrotnie: R-STDP 96–97% błędów → ostatnie zadanie.
- **rgate nie ma tego wzorca:** błędy rozkładają się po równo na klasy starsze i nowsze, a korekta
  nic nie daje — to zapominanie innego rodzaju (mniejsze i bez przechylenia). Tu „nowość →
  rzadziej” zmniejsza część błędów → ostatnie zadanie (0.34 → 0.11 u Izh.).
- W sumie: przy regułach z osłabianiem wybór kierunku modulacji to w praktyce sterowanie
  przechyleniem między starymi a nowymi wyjściami. To łączy E3 z literaturą o korekcji
  przechylenia w class-incremental (Wu i in. 2019 BiC, Hou i in. 2019) — gęsty kod przy nowości
  działa jak biologiczny odpowiednik takiej korekty.

### 12i. E3.7b — warstwa ukryta bez osłabiania heterosynaptycznego (2026-10-29)

**Werdykt wg sek. 6i: H-L1b nierozstrzygające** — rozstrzygające są tylko 2 z 6 komórek (wymagano
≥ 4). 10 przebiegów na komórkę:

| wariant × neuron | ACC (stałe f) | BWT (stałe f) | Δ(+1) | Δ(−1) | rozstrzyga? |
|---|---|---|---|---|---|
| `pos_pool` (pule na klasę, tylko nagroda) × Izh. | **0.71** | −0.07 | **+0.022 (10/10, p = 0.002)** | −0.019 (1/10) | ✅ tak, zgodne z przewidywaniem |
| `pos_pool` × LIF | **0.73** | −0.07 | **+0.020 (10/10, p = 0.002)** | −0.017 (0/10) | ✅ tak, zgodne |
| `pos_bound` (wspólne, ograniczone, tylko nagroda) × Izh. | 0.18 | −0.73 | +0.184 (10/10) | +0.001 | ❌ nie (ACC ≤ 0.25) |
| `pos_bound` × LIF | 0.19 | −0.71 | +0.189 (10/10) | +0.014 | ❌ nie |
| `agrel_bound` (wspólne, ograniczone, z osłabianiem) × Izh. | 0.12 | −0.64 | +0.051 (8/10, n.i.) | −0.015 | ❌ nie |
| `agrel_bound` × LIF | 0.12 | −0.71 | −0.040 (4/10, n.i.) | +0.114 (8/10) | ❌ nie |

- **Gdy jednostki ukryte należą do jednej klasy, zasada przenosi się na warstwę ukrytą**:
  `pos_pool` uczy się dobrze (ACC 0.71–0.73, mało zapomina, jak `rgate`), a „nowość → rzadziej”
  pomaga w 20/20 przebiegach, „nowość → gęściej” szkodzi — ten sam wzorzec co `rgate` (E3.5).
- **Wspólna warstwa ukryta bez normalizacji nadal zapomina prawie całkowicie** (`pos_bound`,
  BWT ≈ −0.72) mimo braku jakiegokolwiek osłabiania. Interferencja nie wymaga więc osłabiania:
  wzmacnianie wejść jednostek wspólnych dla klas zmienia też to, co czytają stare klasy.
  W tym wariancie „nowość → rzadziej” pomaga mocno (+0.18, 10/10), ale przy ACC 0.18 to raczej
  „mniej katastrofalnie” niż ochrona.
- **`agrel_bound` się nie uczy** (ACC 0.12, czyli poniżej „pamięta tylko ostatnie zadanie”) —
  osłabianie bez normalizacji destabilizuje sieć; nic z tego nie wnioskujemy.
- Wniosek ostrożny: zasada „bez osłabiania → rzadziej przy nowości” obowiązuje też dla sieci
  z warstwą ukrytą, *o ile* jej reprezentacje nie są wspólne dla klas. Uczciwy test wspólnej warstwy
  wymaga reguły, która w ogóle uczy się bez katastrofy (np. modulacja plastyczności warstwy ukrytej
  nowością zamiast samej rzadkości).

---


### 12j. E3.9h — rozbicie błędów dla warstwy ukrytej (2026-10-29)

**Werdykt wg sek. 6j: zniszczenie reprezentacji** w 3 z 4 komórek wspólnej warstwy (`agrel_pos`
× LIF — mieszane, `acc_within` 0.67, tuż powyżej progu 0.65). 10 przebiegów, warunek `fixed`:

| wariant × neuron | acc 10 klas | w obrębie zadania | po wyrównaniu | błędy → nowsze | → ostatnie | werdykt |
|---|---|---|---|---|---|---|
| `pos_bound` × Izh. | 0.08 | 0.61 | 0.15 | 0.97 | 0.59 | zniszczenie |
| `pos_bound` × LIF | 0.09 | 0.62 | 0.16 | 0.97 | 0.56 | zniszczenie |
| `agrel_pos` × Izh. | 0.00 | 0.62 | 0.23 | 1.00 | 1.00 | zniszczenie |
| `agrel_pos` × LIF | 0.00 | 0.67 | 0.25 | 1.00 | 1.00 | mieszane |
| `pos_pool` × Izh. | 0.75 | 0.90 | 0.74 | 0.47 | 0.29 | mieszane (mało zapomina) |
| `pos_pool` × LIF | 0.77 | 0.94 | 0.76 | 0.47 | 0.28 | mieszane (mało zapomina) |

- Wspólna warstwa ukryta **niszczy** wiedzę o starych klasach (w obrębie zadania 0.61–0.67 vs
  0.83–0.92 dla czytników liniowych w E3.9), a wyrównanie wyjść prawie nic nie odzyskuje
  (+0.07–0.25). Mechanizm zapominania jest więc inny niż w czytniku liniowym: nie tylko przechylenie
  wyjść, ale przepisanie reprezentacji ukrytej.
- „Nowość → rzadziej” w `pos_bound` (Δ BWT +0.18 w E3.7b) działa głównie przez **mniej przejmowania**
  (błędy → ostatnie zadanie −0.39, 10/10, p = 0.002), a wiedzę chroni słabo (`acc_within` +0.025;
  Izh. 9/10, p = 0.02; LIF 6/10, n.i.). W `pos_pool` to samo w mniejszej skali (−0.10…−0.11, 10/10;
  `acc_within` +0.018).
- `pos_pool` (i rgate w E3.9): błędy rozłożone równo na klasy starsze i nowsze — brak przechylenia.

### 12k. Fig. 1 do f = 90% (2026-10-29, opisowo, sek. 6k)

| f | DG + R-STDP (Izh. / LIF) | DG + delta | sufit (logistyczna) | los. projekcja + R-STDP | dekorelacja | K (Izh. / LIF) |
|---|---|---|---|---|---|---|
| 50% | 0.73 / 0.78 | 0.89 / 0.91 | 0.93 / 0.95 | 0.78 / 0.76 | 0.22 / 0.21 | 8.3 / −0.9 |
| 70% | 0.76 / 0.67 | 0.86 / 0.87 | 0.92 / 0.93 | 0.72 / 0.75 | 0.21 / 0.20 | 6.7 / −2.2 |
| 90% | 0.55 / 0.55 | 0.84 / 0.85 | 0.90 / 0.91 | 0.59 / 0.57 | 0.20 / 0.19 | 4.5 / −4.0 |

Po maksimum dokładność dalej spada; dla R-STDP gwałtownie i z dużym rozrzutem między sieciami
(przy 90%: 0.38–0.68), przy czym losowa projekcja spada tak samo — to własność czytnika przy gęstym
kodzie. Dekorelacja maleje monotonicznie do końca. Przy LIF i f = 90% próg G_crit = 4 + K ≈ 0
(neurony na granicy strzelania bez wejścia).
