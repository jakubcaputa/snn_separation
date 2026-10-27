# Przewidywanie modelu: gabazyna (zapisane 2026-10-27, przed analizą danych Oli i Kingi)

Model: `dg_core` w reżimie skrawka (salwy, `exvivo_best_config` + najlepszy punkt siatki v4: τ_IPSC 8 ms, zróżnicowanie K_GC (SD) 2.5, blok tonicznego 0.3, W_FS_GC 2.0). Gabazyna = −30% hamowania fazowego FS→GC i −30% tonicznego.
Komórki: GC modelu odpowiadające na salwy, 3 sieci; pary kontrola/gabazyna = ta sama komórka.
Założenia do potwierdzenia: protokół wejściowy jak u Madara (P10Hz, 5 pociągów po 2 s); stężenie i działanie gabazyny jak u Madara (100 nM).

Mediana [IQR] po komórkach; „zmiana” = różnica parami (gabazyna − kontrola), ×FR = iloraz parami.

## R_in = 0.5, 5 powtórzeń

| miara | kontrola | gabazyna | zmiana parami |
|---|---|---|---|
| częstotliwość [Hz] | 3.06 [1.50–4.95] | 5.81 [4.25–7.06] | +2.360 [+1.785–+2.710] (×1.89) |
| skłonność do burstów | 0.00 [0.00–0.00] | 0.00 [0.00–0.00] | +0.000 [+0.000–+0.003] |
| R_w (10 ms) | 0.45 [0.31–0.64] | 0.69 [0.50–0.80] | +0.218 [+0.103–+0.286] |
| R_b (10 ms) | 0.18 [0.12–0.26] | 0.29 [0.21–0.35] | +0.101 [+0.069–+0.125] |
| separacja R_in − R_b (10 ms) | 0.30 [0.22–0.37] | 0.20 [0.14–0.28] | -0.101 [-0.125–-0.069] |
| R_w (20 ms) | 0.45 [0.30–0.65] | 0.70 [0.51–0.82] | +0.231 [+0.104–+0.304] |
| R_b (20 ms) | 0.18 [0.11–0.27] | 0.30 [0.21–0.37] | +0.111 [+0.071–+0.136] |
| R_w (50 ms) | 0.46 [0.32–0.67] | 0.74 [0.52–0.88] | +0.253 [+0.108–+0.326] |
| R_b (50 ms) | 0.19 [0.12–0.27] | 0.31 [0.21–0.39] | +0.112 [+0.062–+0.145] |

## R_in = 0.5, 10 powtórzeń

| miara | kontrola | gabazyna | zmiana parami |
|---|---|---|---|
| częstotliwość [Hz] | 3.06 [1.50–4.95] | 5.81 [4.25–7.06] | +2.360 [+1.785–+2.710] (×1.89) |
| skłonność do burstów | 0.00 [0.00–0.00] | 0.00 [0.00–0.00] | +0.000 [+0.000–+0.003] |
| R_w (10 ms) | 0.46 [0.30–0.63] | 0.69 [0.51–0.80] | +0.218 [+0.107–+0.281] |
| R_b (10 ms) | 0.18 [0.12–0.26] | 0.29 [0.21–0.35] | +0.104 [+0.074–+0.122] |
| separacja R_in − R_b (10 ms) | 0.30 [0.23–0.37] | 0.20 [0.14–0.28] | -0.104 [-0.122–-0.074] |
| R_w (20 ms) | 0.46 [0.30–0.64] | 0.70 [0.51–0.82] | +0.231 [+0.107–+0.301] |
| R_b (20 ms) | 0.18 [0.11–0.26] | 0.29 [0.21–0.36] | +0.113 [+0.076–+0.133] |
| R_w (50 ms) | 0.46 [0.31–0.66] | 0.74 [0.53–0.88] | +0.257 [+0.110–+0.328] |
| R_b (50 ms) | 0.18 [0.13–0.27] | 0.31 [0.21–0.39] | +0.116 [+0.062–+0.144] |

## R_in = 0.75, 5 powtórzeń

| miara | kontrola | gabazyna | zmiana parami |
|---|---|---|---|
| częstotliwość [Hz] | 3.21 [1.56–5.05] | 5.87 [4.47–6.87] | +2.330 [+1.750–+2.720] (×1.82) |
| skłonność do burstów | 0.00 [0.00–0.00] | 0.00 [0.00–0.00] | +0.000 [+0.000–+0.000] |
| R_w (10 ms) | 0.42 [0.22–0.65] | 0.75 [0.54–0.87] | +0.274 [+0.165–+0.341] |
| R_b (10 ms) | 0.32 [0.16–0.49] | 0.57 [0.42–0.64] | +0.209 [+0.124–+0.254] |
| separacja R_in − R_b (10 ms) | 0.44 [0.27–0.60] | 0.19 [0.11–0.34] | -0.209 [-0.254–-0.124] |
| R_w (20 ms) | 0.41 [0.21–0.63] | 0.75 [0.53–0.86] | +0.280 [+0.171–+0.344] |
| R_b (20 ms) | 0.30 [0.15–0.47] | 0.54 [0.40–0.62] | +0.205 [+0.122–+0.250] |
| R_w (50 ms) | 0.37 [0.18–0.59] | 0.73 [0.50–0.85] | +0.295 [+0.184–+0.359] |
| R_b (50 ms) | 0.27 [0.12–0.45] | 0.55 [0.38–0.64] | +0.227 [+0.144–+0.275] |

## R_in = 0.75, 10 powtórzeń

| miara | kontrola | gabazyna | zmiana parami |
|---|---|---|---|
| częstotliwość [Hz] | 3.21 [1.56–5.05] | 5.87 [4.47–6.87] | +2.330 [+1.750–+2.720] (×1.82) |
| skłonność do burstów | 0.00 [0.00–0.00] | 0.00 [0.00–0.00] | +0.000 [+0.000–+0.000] |
| R_w (10 ms) | 0.41 [0.22–0.65] | 0.75 [0.56–0.87] | +0.277 [+0.172–+0.341] |
| R_b (10 ms) | 0.32 [0.16–0.49] | 0.56 [0.42–0.64] | +0.210 [+0.128–+0.255] |
| separacja R_in − R_b (10 ms) | 0.44 [0.26–0.60] | 0.19 [0.12–0.33] | -0.210 [-0.255–-0.128] |
| R_w (20 ms) | 0.39 [0.20–0.64] | 0.74 [0.54–0.86] | +0.282 [+0.176–+0.340] |
| R_b (20 ms) | 0.30 [0.15–0.47] | 0.55 [0.40–0.62] | +0.210 [+0.128–+0.252] |
| R_w (50 ms) | 0.35 [0.18–0.60] | 0.72 [0.51–0.85] | +0.297 [+0.182–+0.360] |
| R_b (50 ms) | 0.26 [0.12–0.46] | 0.55 [0.38–0.64] | +0.228 [+0.141–+0.275] |

## R_in = 0.95, 5 powtórzeń

| miara | kontrola | gabazyna | zmiana parami |
|---|---|---|---|
| częstotliwość [Hz] | 3.14 [1.56–4.95] | 5.86 [4.36–6.92] | +2.410 [+1.860–+2.720] (×1.87) |
| skłonność do burstów | 0.00 [0.00–0.00] | 0.00 [0.00–0.00] | +0.000 [+0.000–+0.000] |
| R_w (10 ms) | 0.41 [0.20–0.63] | 0.76 [0.54–0.90] | +0.290 [+0.201–+0.352] |
| R_b (10 ms) | 0.37 [0.19–0.59] | 0.71 [0.50–0.85] | +0.277 [+0.194–+0.329] |
| separacja R_in − R_b (10 ms) | 0.58 [0.36–0.76] | 0.24 [0.10–0.45] | -0.277 [-0.329–-0.194] |
| R_w (20 ms) | 0.39 [0.19–0.62] | 0.77 [0.53–0.91] | +0.304 [+0.205–+0.368] |
| R_b (20 ms) | 0.35 [0.18–0.58] | 0.71 [0.50–0.85] | +0.287 [+0.200–+0.340] |
| R_w (50 ms) | 0.41 [0.21–0.62] | 0.77 [0.55–0.91] | +0.304 [+0.209–+0.361] |
| R_b (50 ms) | 0.38 [0.20–0.58] | 0.72 [0.52–0.86] | +0.291 [+0.202–+0.341] |

## R_in = 0.95, 10 powtórzeń

| miara | kontrola | gabazyna | zmiana parami |
|---|---|---|---|
| częstotliwość [Hz] | 3.14 [1.56–4.95] | 5.86 [4.36–6.92] | +2.410 [+1.860–+2.720] (×1.87) |
| skłonność do burstów | 0.00 [0.00–0.00] | 0.00 [0.00–0.00] | +0.000 [+0.000–+0.000] |
| R_w (10 ms) | 0.39 [0.20–0.64] | 0.75 [0.55–0.90] | +0.299 [+0.197–+0.348] |
| R_b (10 ms) | 0.36 [0.19–0.60] | 0.71 [0.51–0.85] | +0.277 [+0.185–+0.327] |
| separacja R_in − R_b (10 ms) | 0.59 [0.35–0.76] | 0.24 [0.10–0.44] | -0.277 [-0.327–-0.185] |
| R_w (20 ms) | 0.38 [0.19–0.63] | 0.76 [0.54–0.91] | +0.311 [+0.205–+0.364] |
| R_b (20 ms) | 0.35 [0.18–0.59] | 0.71 [0.51–0.85] | +0.290 [+0.192–+0.338] |
| R_w (50 ms) | 0.40 [0.21–0.64] | 0.76 [0.55–0.91] | +0.313 [+0.211–+0.357] |
| R_b (50 ms) | 0.37 [0.20–0.60] | 0.72 [0.52–0.87] | +0.293 [+0.206–+0.339] |

## Przewidywania do sprawdzenia (R_in = 0.75, 5 powtórzeń, bin 10 ms)

Uwaga o modelu: żeby odtworzyć wielkość efektu gabazyny, w modelu gabazyna musi obniżać także
hamowanie toniczne (−30%); przy blokowaniu wyłącznie hamowania fazowego największy efekt w całej
siatce to ×1.41 (najlepsze dopasowanie ×1.12). Jeśli w skrawku 100 nM gabazyny nie zmienia prądu
tonicznego (Stell & Mody 2002: niskie stężenia oszczędzają prąd toniczny), to w modelu hamowanie
fazowe jest za słabe względem tonicznego — dokładnie uwaga B1 prof. Błasiak.

1. Częstotliwość GC rośnie (mediana ×1.82).
2. Skłonność do burstów — **brak przewidywania**: GC modelu nie dają burstów (≥ 2 impulsy na salwę) ani w kontroli, ani po gabazynie; Madar 2019 (Fig. 7b) obserwuje ich wzrost — tego model nie odtwarza.
3. R_w rośnie (0.42 → 0.75).
4. R_b rośnie (0.32 → 0.57).
5. Separacja R_in − R_b maleje — gorsza separacja po gabazynie, jak u Madara.

Dane Madara dla porównania (100 nM, n = 7, bin 10 ms): ×FR 1.6 [1.3–11], R_w 0.49 → 0.80, R_b 0.29 → 0.55 (`results/madar_targets.md`).

Ograniczenie: kalibracja v4 — patrz `README.md`; jeśli model nie odtwarza wielkości efektu, przewidywania dotyczą kierunków, nie wartości.