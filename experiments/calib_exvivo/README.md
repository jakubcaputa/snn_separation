# Kalibracja ex vivo, R_w i przewidywanie dla gabazyny

*Stan: 2026-10-31. Zrobione: kalibracja v1–v4 i przewidywanie zapisane 2026-10-27 (commit
`75ccd60`), przed analizą danych Oli i Kingi. Otwarte: wysłanie przewidywania i pytań do
prof. Błasiak (STATUS sek. 2 i 4).*

Skąd ten wątek: odpowiedź prof. Błasiak z 2026-10-22
([korespondencja](../../korespondencja/2026-10-22_odpowiedz_blasiak.md)) — kalibrować model
do skrawka (wejście = salwy z protokołu Madara, nie ciągłe tło 400 Hz), hamowanie toniczne
ma za dużą wagę względem fazowego (B1), obok dekorelacji mierzyć R_w.

## Stan w skrócie

| | dane Madara (GC, n = 7, bin 10 ms) | model (v4) |
|---|---|---|
| kontrola: częstotliwość GC | 3.0 Hz | 2.99 Hz |
| kontrola: R_w / R_b | 0.49 / 0.29 | 0.41 / 0.30 |
| kontrola: FS | 8.4 Hz | 9.6 Hz, FS odpalają przed GC |
| gabazyna 100 nM: ×częstotliwość GC | ×1.6 [1.3–11] | ×1.77 [1.36–2.76] |
| gabazyna: R_w / R_b | 0.80 / 0.55 | 0.71 / 0.54 |
| bursty GC | rosną po gabazynie | **brak** — GC modelu nie dają burstów |

**Warunek dopasowania:** w modelu gabazyna musi obniżać hamowanie fazowe FS→GC **i** toniczne
(o 30%). Gdy blokuje tylko fazowe, największy efekt w całej siatce v4 to ×1.41 (najlepsze
dopasowanie ×1.12). Albo więc 100 nM gabazyny w skrawku obniża też prąd toniczny GC, albo —
jeśli nie (Stell & Mody 2002: niskie stężenia go oszczędzają) — hamowanie fazowe w modelu
jest za słabe względem tonicznego, czyli dokładnie uwaga B1. To pytanie do prof. Błasiak.

**Przewidywanie** ([PREDICTION_gabazine.md](PREDICTION_gabazine.md); R_in 0.5 / 0.75 / 0.95,
5 i 10 powtórzeń): dla R_in 0.75 i 5 powtórzeń — częstotliwość GC ×1.82, R_w 0.42 → 0.75,
R_b 0.32 → 0.57, separacja R_in − R_b 0.44 → 0.19 (gorsza). Bursty: brak przewidywania.
Założenia do potwierdzenia z zespołem: protokół jak u Madara (P10Hz, 5 pociągów po 2 s),
100 nM gabazyny.

## Najlepszy punkt (`dg_core.exvivo.exvivo_best_config` + v4)

Salwa 20 mV (40 włókien/GC, każde z p_rel 0.6), PP→FS 0.5, FS→GC 2, GC→FS ≈ 0, FS→FS 1,
K_GC z V_rest = −76 mV (K = 6.24) ze zróżnicowaniem między GC (SD 2.5), τ IPSC 8 ms; bez tła.

## Czego nauczyła kalibracja (v1–v4)

1. **v1:** −30% FS→GC nie zmieniało częstotliwości GC (×1.01–1.05), bo **FS odpalały po GC**
   (10.4 vs 8–9 ms od salwy) — hamowanie fazowe było nie tylko za słabe, ale spóźnione.
   Mechanistyczna wersja uwagi B1.
2. **v2** (192 pkt): napęd PP→FS jako oś → FS przed GC, kontrola trafiona, ale gabazyna ×1.25
   i FS 19 Hz.
3. **v3** (162 pkt): GC→FS ≈ 0 i FS→FS 1–2 → kontrola zgodna we wszystkich miarach
   (strata 0.25); gabazyna dalej za słaba (najwyżej ×1.46).
4. **v4** (36 pkt): osie τ IPSC (8/15/25 ms), zróżnicowanie GC (SD 0/2.5/5), blok toniczny
   (0/0.3), FS→GC (2/4). Rozstrzyga blok toniczny; zróżnicowanie GC daje realistyczny rozrzut
   efektu między komórkami; dłuższe IPSC niewiele zmieniają (strata 0.043).

Model ex vivo jest używany w E3.6x (`run_dgtask.py --regime exvivo`).

## Cele z danych

Pełna tabela: `results/madar_targets.md` (bin 10 ms, 10 powtórzeń).

| | częstotliwość [Hz] | R_w | R_b |
|---|---|---|---|
| GC, wszystkie (n = 110) | 6.25 [1.87–8.41] | 0.38 [0.35–0.43] | 0.24 [0.17–0.31] |
| GC przed gabazyną (n = 7, R_in 0.76) | 3.04 [1.13–4.56] | 0.49 [0.37–0.54] | 0.29 [0.14–0.32] |
| GC po gabazynie 100 nM (te same 7) | 7.50 [4.29–8.98] | 0.80 [0.64–0.84] | 0.55 [0.32–0.58] |
| FS (n = 20) | 8.41 [7.09–9.19] | 0.35 [0.34–0.38] | 0.20 [0.15–0.25] |
| HMC (n = 18) | 8.42 [5.70–10.56] | 0.55 [0.36–0.69] | 0.23 [0.15–0.32] |

5 vs 10 powtórzeń (pytanie prof. Błasiak): na poziomie populacji różnice ≤ 0.03 w R_w i R_b,
więc 5 powtórzeń wystarcza do median; pojedyncze komórki — niesprawdzone.

## Kod i dane

| plik | rola |
|---|---|
| `dg_core/io_madar.py` | protokoły (`.prt.axgx`), nagrania (`.axgd`), impulsy (−20 mV), R_in / R_w / R_b wiernie wg `SimilarityAnalysis.m` / `SimMat_WandB.m` — ta sama funkcja dla danych i modelu |
| `dg_core/exvivo.py` | obwód napędzany salwami (tryb per włókno z p_rel), gabazyna (`gabazine_block`, `gabazine_tonic_block`), `EXVIVO_BEST` |
| `madar_targets.py` | cele z danych → `results/madar_targets.md` |
| `grid.py`, `grid_v4.py` | siatki kalibracyjne → `results/grid_v*_all.json` |
| `predict_gabazine.py` | przewidywanie → `PREDICTION_gabazine.md` |

Dane (`dataset/`, poza gitem): zip z BioStudies S-BSST219 i repo analiz Madara
(`PatSepSpikeTrains`, listy nagrań `NameFiles/*.m`); odczyt AxoGraph przez `neo`.
Jeden sweep `exvivo` ≈ 5.6 s (Brian2), punkt siatki ≈ 100 sweepów.

## Dalej

1. **Wysłać przewidywanie i pytania** (100 nM a prąd toniczny; protokół Oli i Kingi; B4 — siła
   MC → GC) — przed analizą ich danych.
2. Po ich danych: porównanie z przewidywaniem (kierunki i wielkości, per komórka).
3. R_w do porównań modelu: E1/E1′ w reżimie ex vivo, z R_w obok dekorelacji (hipoteza: przy
   bardzo niskiej aktywności R_w spada, więc miara z R_w może mieć optimum).
4. Bursty GC — wymagają zmiany neuronu (np. parametry Izhikevicha z burstami); tylko jeśli dane
   Oli i Kingi pokażą, że to istotne.
