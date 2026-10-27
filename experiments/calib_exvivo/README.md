# Kalibracja ex vivo i R_w (po odpowiedzi prof. Błasiak, 2026-10-22)

Odpowiedź: [`korespondencja/2026-10-22_odpowiedz_blasiak.md`](../../korespondencja/2026-10-22_odpowiedz_blasiak.md).
Dwa kroki: (1) `io_madar` + kalibracja do skrawka, (2) R_w obok dekorelacji.

## Dane

`dataset/` (poza gitem): `PatchPatSep2s_Public/` — zip z BioStudies S-BSST219
(pobrany 2026-10-22, 542 MB, rozpakowany bez `__MACOSX`); `PatSepSpikeTrains/` — repo
analiz Madara z GitHuba (listy nagrań `NameFiles/*.m`, ścieżki bezwzględne autora →
dopasowanie po nazwie pliku). Odczyt AxoGraph: pakiet `neo` (doinstalowany do venv).

## Kod

| plik | co robi |
|---|---|
| `dg_core/io_madar.py` | protokoły (`.prt.axgx`: 5 pociągów × 2 s), nagrania (`.axgd`: 50 sweepów = 5 pociągów × 10 powtórzeń, przeplatane), impulsy (−20 mV), **R_in, R_w, R_b** wiernie wg `SimilarityAnalysis.m` / `SimMat_WandB.m`; ta sama funkcja dla danych i modelu |
| `dg_core/exvivo.py` | obwód `dg_core` napędzany salwami z protokołu: tryb `per_fiber`, 40 włókien/GC odpala w każdej salwie, każde z p_rel; waga włókna = W_salwy/(40·p_rel) ⇒ średni zsumowany EPSP = W_salwy, zmienność dwumianowa = źródło R_w < 1. Gabazyna = W_FS_GC × 0.7 (niskie stężenie blokuje głównie hamowanie fazowe) |
| `calib_exvivo/madar_targets.py` | cele z danych → `results/madar_targets.md` |
| `calib_exvivo/grid.py` | siatka: W_salwy × W_FS_GC × p_rel × W_GC_FS (144 punkty), kontrola + gabazyna, K_GC z V_rest = −76 mV (K = 6.24) |

## Cele z danych (bin 10 ms, 10 powtórzeń; pełna tabela: `results/madar_targets.md`)

| | częstotliwość [Hz] | R_w | R_b |
|---|---|---|---|
| GC, wszystkie (n = 110, różne R_in) | 6.25 [1.87–8.41] | 0.38 [0.35–0.43] | 0.24 [0.17–0.31] |
| GC przed gabazyną (n = 7, R_in = 0.76) | 3.04 [1.13–4.56] | 0.49 [0.37–0.54] | 0.29 [0.14–0.32] |
| GC po gabazynie 100 nM (te same 7) | 7.50 [4.29–8.98] | 0.80 [0.64–0.84] | 0.55 [0.32–0.58] |
| FS (n = 20) | 8.41 [7.09–9.19] | 0.35 [0.34–0.38] | 0.20 [0.15–0.25] |
| HMC (n = 18) | 8.42 [5.70–10.56] | 0.55 [0.36–0.69] | 0.23 [0.15–0.32] |

- **Gabazyna (pary):** mediana ×1.6 częstotliwości (1.3–11×); R_w i R_b rosną — wyjścia
  rzetelniejsze, ale bardziej do siebie podobne (separacja gorsza), zgodnie z Madarem.
- **5 vs 10 powtórzeń:** na poziomie populacji różnice ≤ 0.03 w R_w i R_b
  (np. GC R_w 0.38 vs 0.38, R_b 0.24 vs 0.26). Na pytanie prof. Błasiak: w tych danych
  5 powtórzeń wystarcza do oszacowania median; różnice dla pojedynczych komórek —
  do sprawdzenia.
- **FS w skrawku pod protokołem: ~8.4 Hz** — to cel dla modelu w reżimie salw
  (wartości 28/46 Hz z wcześniejszych notatek dotyczyły ciągłego tła 400 Hz).

## Stan (2026-10-22)

- Jeden sweep `exvivo` = 5.6 s (Brian2); punkt siatki ≈ 100 sweepów.
- Pierwsze testy: przy W_salwy 6.98 mV (dawna kalibracja pojedynczej komórki) GC w sieci
  milczą — salwa pobudza też FS i hamowanie feedforward wycisza GC. Przy W_salwy 16 mV,
  W_FS_GC 2: GC 2.6 Hz, R_w 0.43, R_b 0.36 (cele 3.0 / 0.49 / 0.29), ale FS 39 Hz
  (cel 8.4) — stąd oś W_GC_FS w siatce.
- **Siatka v1** (48 ze 144 punktów, `results/grid_v1/`): w ŻADNYM punkcie „gabazyna”
  (−30% FS→GC) nie zmienia częstotliwości GC (×1.01–1.05; dane ×1.6). Diagnoza: **FS
  odpalają po GC** — mediana opóźnienia od salwy FS 10.4 ms, GC 8–9 ms — więc hamowanie
  fazowe przychodzi, gdy GC już strzeliły; nawet W_FS_GC = 60 mV prawie nic nie zmienia
  (GC 3.35 → 2.33 Hz). W skrawku interneurony koszyczkowe odpowiadają na salwę szybciej
  niż GC (hamowanie feedforward) i dlatego gabazyna działa. To mechanistyczna wersja
  uwagi B1: w modelu hamowanie fazowe jest nie tylko za słabe, ale przede wszystkim
  **spóźnione**.
- Test: silniejszy napęd PP→FS (1.5–3) → FS przed GC (6.6 vs 7.7 ms), ale GC milkną
  całkowicie, a FS strzelają 28–43 Hz (cel 8.4). Właściwy reżim jest pomiędzy.
- **Siatka v2** (192 punkty: W_salwy 16/20/25 × W_PP_FS 0.5–1.5 × W_FS_GC 0.5–5 ×
  p_rel 0.3/0.6 × W_GC_FS 1/2.5; w wynikach także opóźnienia GC i FS) — w kolejce
  plgrid-now (4 zadania) i równolegle na plgrid-gpu-a100 (8 zadań; punkty policzone
  przez jedną ścieżkę druga pomija). Wynik: `results/grid_all.json`.
- **Wynik v2 (2026-10-23, 192/192, plgrid-now; zadania GPU nigdy nie ruszyły — ReqNodeNotAvail).**
  Najlepszy punkt: W_salwy 20, W_PP_FS 0.5, W_FS_GC 2, p_rel 0.6, W_GC_FS 1 →
  **kontrola trafiona**: GC 2.92 Hz / R_w 0.38 / R_b 0.29 (cele 3.0 / 0.38–0.49 / 0.29),
  FS przed GC (6.3 vs 7.6 ms). **Gabazyna za słaba**: ×1.25 (cel 1.6), R_w 0.38 → 0.47
  (dane 0.49 → 0.80), R_b 0.29 → 0.37 (0.29 → 0.55); **FS za szybkie**: 19 Hz (cel 8.4).
  Strukturalna różnica do zbadania: w danych odhamowanie silnie podnosi rzetelność (R_w),
  w modelu słabo — szum (zawodność PP) nie zależy od hamowania.
- **Siatka v3** (162/162, 2026-10-23): W_PP_FS 0.3–0.5, W_FS_GC 2–10, W_GC_FS 0–1,
  W_FS_FS 0–2, p_rel 0.6, W_salwy 20/25. **Najlepszy punkt (strata 0.25):** W_salwy 20,
  W_PP_FS 0.5, W_FS_GC 2, p_rel 0.6, **W_GC_FS ≈ 0**, W_FS_FS 1–2 →
  **GC 2.99 Hz, R_w 0.37, R_b 0.28, FS 9.6 Hz, FS przed GC (5.9 vs 7.6 ms)** — kontrola
  zgodna z danymi we wszystkich miarach (cele 3.0 Hz / 0.38–0.49 / 0.29 / 8.4 Hz).
  FS→FS prawie nie zmienia wyniku (W_FS_FS 0, 1, 2 → strata 0.27 / 0.25 / 0.25); FS
  w reżimie salw ogranicza przede wszystkim brak sprzężenia GC→FS.
- **Nierozwiązane: gabazyna.** W całej v3 największy efekt −30% FS→GC to ×1.46, w najlepszym
  punkcie ×1.25 (dane ×1.6); R_w po gabazynie 0.46 (dane 0.80), R_b 0.36 (0.55). Model
  odtwarza kierunek (więcej impulsów, wyższe R_w i R_b), ale nie wielkość. Kandydaci:
  (a) za krótkie IPSC (τ_in = 8 ms) albo zbyt mała liczba połączeń FS→GC; (b) w danych
  gabazyna działa też na hamowanie toniczne lub dendrytyczne (HIPP), którego model nie ma;
  (c) zmienność między komórkami (w danych ×1.3–11) — model ma identyczne GC.

## Dalej

1. Wybór punktu z siatki; zawężenie siatki wokół niego; sprawdzenie na drugim
   protokole (inne R_in) i na danych GC z wszystkich zestawów.
2. R_w do porównań modelu: E1/E1′ w nowym reżimie, z R_w obok dekorelacji (hipoteza:
   przy bardzo niskiej aktywności R_w też spada → miara z R_w może mieć optimum).
3. Przewidywanie dla eksperymentu z gabazyną (Ola, Kinga) — zapisać przed ich analizą.

## Krok 2 (2026-10-27): efekt gabazyny i przewidywanie

**Siatka v4** (`grid_v4.py`, 36 punktów wokół najlepszego punktu v3) — trzy kandydackie
wyjaśnienia słabego efektu gabazyny (×1.25 vs ×1.6), jako osie:
- `tau_in_gc` — stała czasowa IPSC na GC: 8 / 15 / 25 ms (nowe pole `DGConfig.tau_in_gc`);
- `K_GC_sd` — zróżnicowanie pobudliwości GC: K per neuron ~ N(K, sd²), sd 0 / 2.5 / 5 (nowe pola
  `DGConfig.K_GC_sd`, `K_seed`; w danych V_rest −81…−70 mV ⇔ K ≈ 0…13.6);
- `gabazine_tonic` — gabazyna obniża też hamowanie toniczne: 0 / 0.3 (`exvivo_config`);
- `W_FS_GC` 2 / 4.
Domyślne wartości nowych pól nie zmieniają modelu (testy regresji 20/20). ×FR liczony per
komórka (para kontrola/gabazyna tej samej GC), jak w danych.
Znane ograniczenie z testu: GC modelu nie dają burstów (≥ 2 impulsy na salwę) — model nie
odtworzy „skłonności do małych burstów” z Madar 2019 Fig. 7b.

**Przewidywanie** (`predict_gabazine.py` → `PREDICTION_gabazine.md`, zapisywane z datą PRZED
analizą danych Oli i Kingi): najlepszy punkt v4; protokoły P10Hz R_in 0.5 / 0.75 / 0.95;
3 sieci; 5 powtórzeń (ich protokół) i 10 (Madar); per komórka: częstotliwość, bursty, R_w, R_b,
R_in − R_b (biny 10/20/50 ms). Założenia do potwierdzenia z zespołem: protokół wejściowy jak
u Madara, 100 nM gabazyny.

### Wynik v4 i przewidywanie (2026-10-27)

**Najlepszy punkt v4 (strata 0.043):** τ_IPSC 8 ms, zróżnicowanie K_GC (SD) 2.5, W_FS_GC 2,
**gabazyna obniża też hamowanie toniczne o 30%** →
kontrola: GC 2.99 Hz, R_w 0.41, R_b 0.30, FS 9.6 Hz; gabazyna: **×1.77 [1.36–2.76]**,
R_w 0.71, R_b 0.54 — zgodnie z danymi (×1.6 [1.3–11], R_w 0.80, R_b 0.55).
- **Kluczowe:** bez działania na hamowanie toniczne największy efekt w całej siatce to ×1.41
  (najlepsze dopasowanie ×1.12). Wszystkie najlepsze punkty mają blok toniczny 0.3. Zróżnicowanie
  GC daje realistyczny rozrzut efektu między komórkami; dłuższe IPSC niewiele zmieniają.
- **Interpretacja / pytanie do prof. Błasiak:** albo 100 nM gabazyny w skrawku obniża też prąd
  toniczny GC, albo (jeśli nie — Stell & Mody 2002: niskie stężenia go oszczędzają) w modelu
  hamowanie fazowe jest za słabe względem tonicznego, czyli dokładnie jej uwaga B1.
- **Przewidywanie zapisane:** [`PREDICTION_gabazine.md`](PREDICTION_gabazine.md) (R_in 0.5/0.75/0.95,
  5 i 10 powtórzeń). Dla R_in 0.75, 5 powtórzeń: częstotliwość ×1.82, R_w 0.42 → 0.75,
  R_b 0.32 → 0.57, separacja R_in − R_b 0.44 → 0.19 (gorsza). Bursty: brak przewidywania
  (GC modelu ich nie generują).
