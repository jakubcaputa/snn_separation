# Status — gdzie jesteśmy, co dalej

*Aktualizacja: 2026-10-31 (porządki w notatkach po E3.9h).*

Ten plik odpowiada na trzy pytania: **gdzie jesteśmy** (sek. 0–1), **co robimy dalej i w jakiej
kolejności** (sek. 4), **co zmierzyliśmy w E1–E2** (sek. 3 — numeracja 3.x jest stała, odwołuje
się do niej kod). Wyniki E3 i kalibracji mają własne foldery; tu są tylko werdykty i odsyłacze.

> **Kolejność czytania:** sek. 0 → sek. 4 → (szczegóły) README wątku, który ruszasz.
>
> | wątek | dokument wejściowy |
> |---|---|
> | separacja w DG (E1–E2, 1A) | sek. 3 tego pliku |
> | kalibracja ex vivo, gabazyna | [experiments/calib_exvivo/README.md](experiments/calib_exvivo/README.md) |
> | E3 — rzadkość jako trzeci czynnik | [experiments/e3_sparsity_third_factor/README.md](experiments/e3_sparsity_third_factor/README.md) |
> | artykuły, prezentacja | sek. 6, [article/prezentacja_notatki.md](article/prezentacja_notatki.md) |
> | hipotezy pierwotne (historyczne) | [PLAN_BADAWCZY.md](PLAN_BADAWCZY.md), [ml_paper.md](ml_paper.md) |

---

## 0. Gdzie jesteśmy — w jednej tabeli

| wątek | stan | wynik w jednym zdaniu |
|---|---|---|
| **A. Separacja w DG** (E1, E1′, E1″, E1‴, E2, 1A) | **zamknięty** | Teza „separacja ma optimum, a hamowanie nią steruje” obalona: dekorelacja rośnie sama, gdy sieć cichnie, a przy wyrównanej aktywności hamowanie fazowe jej nie zmienia. Wynik nośny jest metodologiczny: oba naturalne null-e zawodzą w przeciwne strony (sek. 3.5). Jedyny efekt obwodu — zapłon sieci przy aktywnych mossy cells — jest rzadki i nie przeszedł testu potwierdzającego (sek. 3.4). |
| **B. Kalibracja ex vivo** (dane Madara, gabazyna) | **policzone; czeka na wysłanie i na dane Oli i Kingi** | Model skrawka odtwarza kontrolę (GC 3 Hz, R_w, R_b, FS) i efekt gabazyny (×1.77 vs ×1.6), ale tylko gdy gabazyna obniża też hamowanie toniczne — co popiera uwagę B1. Przewidywanie zapisane 2026-10-27 (commit `75ccd60`). |
| **C. E3 — rzadkość jako trzeci czynnik** (Split-MNIST, zadanie separacji) | **wszystkie zaplanowane policzone (E3.0–E3.9h)** | „Nowość → rzadszy kod” pomaga przy regule tylko wzmacniającej i szkodzi przy regułach z osłabianiem (odporne na 6 architektur); przy osłabianiu działa przez przechylenie wyjść w stronę nowych klas, a na zadaniu separacji kierunek zależy też od podobieństwa wzorców. |
| **D. Artykuły** | **żaden nie jest w pisaniu** | Draft o narzędziu istnieje (nieskompilowany); wariant metodologiczny (a) ma komplet dowodów; artykuł ML (M1) ma wyniki E3, brakuje porównania ze standardową korektą przechylenia; wariant „padaczka” (d) czeka na siłę MC→GC (B4). |

**Infrastruktura:** nic się nie liczy. SLURM: konto `plgdyplomanci8-gpu-a100` (grant 7 wygasł
2026-10-27). Git: ostatni commit `75ccd60` (2026-10-27) — wszystko od E3.8 do porządków z
2026-10-31 jest niezacommitowane.

---

## 1. Stan prac — szczegółowo

| obszar | stan |
|---|---|
| Rdzeń `experiments/dg_core/` | działa; testy 20/20; nowe pola z kalibracji (`tau_in_gc`, `K_GC_sd`, `K_seed`) domyślnie nie zmieniają modelu |
| Narzędzie `interactive_dg.py` | działa; bilans hamowania, panel P(AP) |
| E1–E2, 1A | zamknięte (sek. 3) |
| Kalibracja ex vivo | v1–v4 zrobione, przewidywanie zapisane; wysłanie przewidywania i pytań — **do zrobienia** (sek. 2) |
| E3 | E3.0–E3.9h, E3.6x, fig. 1 do f = 90% — policzone i opisane; dalsze kroki w README E3 sek. 7 |
| Draft o narzędziu | `article/article_draft.tex` (2026-10-12: literatura, „Related tools”, MC vs Chavlis) — **nigdy nie skompilowany** (sek. 6) |
| Prezentacja | `article/prezentacja_stan_prac.pptx` — stan z 2026-10-07 (bez kalibracji ex vivo i E3) |
| Kontroler adaptacyjny E4/E5 (PLAN) | niezbudowany; zastąpiony w praktyce przez E3 (regulator nowość → `K`) |

---

## 2. Prof. Błasiak — co odpowiedziała, o co jeszcze pytamy

**Odpowiedź z 2026-10-22** ([korespondencja/2026-10-22_odpowiedz_blasiak.md](korespondencja/2026-10-22_odpowiedz_blasiak.md))
i co z nią zrobiliśmy:

| pytanie | odpowiedź | co zrobiliśmy |
|---|---|---|
| **B1** udział hamowania tonicznego (w modelu 74% hamowania GC) | za duży: −30% FS→GC ma dawać ~2× częstotliwość GC | kalibracja v1–v4: efekt gabazyny odtwarzamy tylko z blokiem tonicznym — model potwierdza uwagę, pytanie C1 niżej |
| **B2** częstotliwość FS (~46 Hz) | 10–28 Hz; FS→FS w porządku | w reżimie salw FS 9.6 Hz (dane 8.4 Hz), FS→FS 1 |
| **B3** reżim kalibracji | **ex vivo**: wejście = salwy z protokołu; 50% AP u Madara dotyczy zsumowanego EPSC salwy | `dg_core/io_madar.py`, `dg_core/exvivo.py`, kalibracja v1–v4 |
| nowe: R_w | mierzyć rzetelność odpowiedzi obok dekorelacji | R_w / R_b liczone jak u Madara, w kalibracji i przewidywaniu |

**Otwarte — do wysłania razem z przewidywaniem** (przed analizą danych Oli i Kingi):

- **C1.** Czy 100 nM gabazyny w skrawku obniża też prąd toniczny GC? Jeśli nie (Stell & Mody
  2002), w modelu hamowanie fazowe jest za słabe względem tonicznego.
- **C2.** Protokół Oli i Kingi: liczba powtórzeń (5?), R_in, stężenie gabazyny, czy te same
  pociągi P10Hz co u Madara — od tego zależy, którą tabelę przewidywania porównać.
- **B4.** Siła pętli mossy cells → GC (amplituda EPSP MC→GC, liczba MC na GC, częstotliwość MC
  in vivo). Warunek dla wariantu (d): przy obecnych wagach zapłon sieci w 2/20 przebiegów,
  przy wadze ×1.5 do 40%, bez MC nigdy (sek. 3.4).
- **τ_m.** Z danych Madara τ_m ≈ 3 ms dla GC (korespondencja: 10–50 ms) — różnica definicji?
  Potrzebne do Methods, symulacji nie zmienia.
- Drobne: czy wzrost burstów po gabazynie (Madar 2019, Fig. 7b) jest dla nich istotny — model
  burstów nie generuje.

Kontekst B1 (wkłady do `dv/dt` w dawnej kalibracji, te same jednostki): GC — pobudzenie PP 2.43,
hamowanie fazowe 3.59, toniczne `K` 10.0 (74%); FS — toniczne 100% (brak hamowania
synaptycznego); HMC — toniczne 100%. Wartości odziedziczone, nie wybrane.

---

## 3. Wyniki

Wątek A (zamknięty). Wyniki E3 i kalibracji ex vivo: ich README (tabela na górze pliku).
Sek. 3.3–3.7 to cztery eksperymenty **w kolejności powstawania** — każdy odpowiada
na pytanie otwarte przez poprzedni. Sek. 3.1 definiuje miary, sek. 3.8–3.9 to
materiał pomocniczy. Figury: proste (na slajdy) w `article/figures/`, analityczne
w `experiments/*/results/`.

### 3.1 Słownik — co dokładnie mierzymy

**`dec` — separacja.** `dec = r_in − r_out`: `r_in` to średnia korelacja Pearsona
między parami wzorców wejściowych (binarnych: który GC dostaje silny napęd), `r_out`
— to samo dla wektorów częstotliwości wyjściowych GC. Dodatnie = obwód oddalił
wzorce. ⚠️ Rośnie samo, gdy sieć cichnie.

**Frakcja aktywnych GC — rzadkość.** Odsetek komórek ziarnistych strzelających
powyżej 0.5 Hz. Okazała się **zmienną dominującą**: separacja, retencja
i dekodowalność są przede wszystkim jej funkcjami.

**`retention` — retencja informacji.** `MI(X;Y) / H(X)` — jaki ułamek entropii
wejścia przeżywa transformację. Liczona na poziomie pojedynczej komórki, binarnie:
`X` = czy GC dostaje silny napęd, `Y` = czy GC strzela > 0.5 Hz; rozkład łączny
estymowany po populacji 200 GC (plug-in, obciążenie ≈ 0.01 bita). `1` = z wyjścia
da się odtworzyć, które komórki były napędzane; `0` = nic. Kod:
`dg_core/metrics.py::binary_mi_io`. ⚠️ Binarna, więc nie widzi *jak szybko* komórka
strzela, tylko *czy*; i jest maksymalna, gdy rzadkość wyjścia ≈ rzadkość wejścia
(sek. 3.4) — użyteczna jako miara zachowania informacji, bezużyteczna jako
kryterium punktu pracy.

**`null` — punkt odniesienia.** Sztuczny kod o tej samej rzadkości co wyjście DG,
ale bez obwodu; ma odjąć tę część dekorelacji, którą daje sama rzadkość. Używamy
dwóch — **na figurach nazywają się `permuted DG output` i `random projection`**:

| | **null permutacyjny** — *permuted DG output* | **null projekcji losowej** — *random projection* |
|---|---|---|
| z czego powstaje | z **wyjścia DG** | z **wejścia** |
| jak | wektor częstotliwości GC przetasowany po komórkach, osobno dla każdego wzorca | wejście rzucone przez losową macierz gaussowską, zostawione `k` najsilniejszych jednostek (`k` = liczba aktywnych GC) |
| co zachowuje | dokładnie te same częstotliwości (ta sama rzadkość) | tę samą rzadkość i zależność od wejścia |
| co niszczy | **którą komórkę** napędza który wzorzec — całą informację o bodźcu | obwód: zamiast DG losowe połączenia |
| `r_out` (E1′) | 0.001 — **sufit**, osiągalny tylko przez wyrzucenie bodźca | 0.580 (78% `r_in`) — **słaba podłoga**: losowa projekcja z definicji zachowuje korelację |
| kod | `dg_core/nulls.py::shuffle_null_vectors` | `dg_core/nulls.py::kwta_random_projection` (to samo, co warunek „random" w 1A) |

Przykład dla intuicji: jeśli wzorce A i B napędzają w dużej części te same komórki,
DG odpowie w dużej części tymi samymi komórkami (`r_out` > 0). Permutacja losuje,
*które* komórki strzelają, więc A i B przestają się pokrywać (`r_out` ≈ 0) —
„separacja" jest idealna, ale z wyjścia nie da się już powiedzieć, który bodziec
padł. Projekcja losowa liczy wyjście z wejścia, więc pokrycie A i B w dużej części
przenosi dalej. DG leży pomiędzy (sek. 3.5).

**Dwie osie hamowania.** `K_GC` — **toniczne**: stały prąd w równaniu napięcia,
zawsze włączony. `W_FS_GC` — **fazowe**: synaptyczne, wyzwalane spajkami
interneuronów. W literaturze bywają zlewane w jedno „hamowanie".

**Motywy.** `FF` = PP→FS→GC (wyprzedzający), `FB` = GC→FS→GC (zwrotny),
`MC` = GC→HMC→GC/FS (pobudzająca pętla mossy cells).

### 3.2 Tabela zbiorcza

| eksperyment | pytanie | odpowiedź |
|---|---|---|
| **E1** mapa reżimów (sek. 3.3) | czy separacja ma optimum przy pośredniej aktywności? | **Nie.** Maksimum jedzie za progiem odrzucania cichych punktów |
| **E1′** wyrównana aktywność (sek. 3.4) | czy hamowanie fazowe zmienia separację przy tej samej aktywności? | **Nie.** Nachylenie −0.003, p = 0.60 |
| **null-e** (sek. 3.5) | z czym w ogóle porównywać obwód? | **Oba naturalne zawodzą**, w przeciwne strony |
| **E1″** szerszy sweep (sek. 3.4) | czy zależność pojawia się przy innym `R_in`, z aktywnymi MC albo w czasie? | **Nie** (kryterium zapisane z góry) |
| **E1‴** test potwierdzający (sek. 3.4) | czy aktywne MC + słabe hamowanie fazowe dają ucieczkę, na nowych seedach i przy różnej sile pętli MC? | **Nie przeszedł.** Zapłony całej sieci są, ale rzadkie (λ = 1: 2/20); bez MC — nigdy; przy `W` ≥ 3 — nigdy |
| **E2** motywy (sek. 3.6) | który motyw hamowania niesie separację? | **Zdominowane przez aktywność** (r = −0.97); wcześniejsza „kontrola nullem" była pusta |
| **1A** odczyt (sek. 3.7) | czy klasyfikator czyta DG lepiej niż wejście? | **Nie.** 0.885 vs 0.940 |
| **dane Madara** (sek. 3.8) | czy punkt pracy jest związany danymi? | **Zgodny, ale nie wyznaczony.** `K_GC=10` → `V_rest` −78.7 mV, wewnątrz IQR; dane dopuszczają `K` ≈ 0–13.6 |

### 3.3 E1 — mapa reżimów · wynik: H1 obalona

**Jak policzone.** Athena, job 3167903: 10 `K_GC` × 9 `W_FS_GC` × 5 seedów = 450
punktów, 1800 symulacji, 3.7 min na 16 CPU; 419/450 przeszło próg ważności.
Figury: `article/figures/slides/slide-e1.png`, `e1_regime_map/results/regime_map_full.png`.

**Wynik.** Separacja **nie ma optimum** — rośnie monotonicznie ku ciszy. Maksimum
`dec` siedzi zawsze na progu odrzucania cichych punktów albo tuż nad nim i przesuwa
się razem z progiem:

| próg odrzucania (frakcja aktywnych) | 2% | 3% | 5% | 8% | 10% | 15% | 20% |
|---|---|---|---|---|---|---|---|
| maksimum `dec` przy | 2.5% | 3.0% | 6.5% | 8.5% | 12.0% | 15.0% | 20.0% |

To podłoga analizy stawia maksimum, nie biologia. Szersza siatka tego nie naprawi.
Warunkowanie na retencji też nie — maksimum dalej wędruje (4% przy progu retencji
0.10 → 18% przy 0.60).

**Kurs wymiany separacja↔informacja jest gładki, bez wyróżnionego punktu:**

| retencja ≥ | 0.00 | 0.20 | 0.40 | 0.60 | 0.80 | 0.90 |
|---|---|---|---|---|---|---|
| osiągalne max `dec` | 0.785 | 0.623 | 0.533 | 0.352 | 0.257 | 0.232 |

Najlepszy kurs (separacja na jednostkę utraconej informacji) wypada przy **słabym**
hamowaniu: `dec` 0.173 za 1.3% utraconej informacji (`K_GC` 10, `W_FS_GC` 0.25).

⚠️ Wersja `run_regime_map.py` sprzed 2026-09-21 raportowała **fałszywe**
potwierdzenie H1 (test krańca sprawdzał równość z minimum siatki). Zastąpiona
testem kształtu; liczby z E1 sprzed tej daty są niewiarygodne.

### 3.4 E1′ — wyrównana aktywność · wynik: hamowanie fazowe bez efektu

**Po co.** W E1 aktywność była *wynikiem*, a separacja jest jej funkcją — oś sweepu
pokrywała się z confounderem. Tu aktywność jest **zadana**.

**Jak policzone.** `run_matched_activity.py`, job 3189473: aktywność ustawiona
bisekcją po `K_GC` na 6 poziomach × 9 `W_FS_GC` × 3 rzadkości wejścia × 5 seedów =
810 punktów; dostrojono 733 (reszta poza zasięgiem `K_GC` ∈ [0, 24]). Odtworzenie
bez liczenia: `python analyze_matched_activity.py`. Figury:
`article/figures/slides/slide-e1p.png`, `matched_activity_full.png`.

**Wynik: przy stałej aktywności separacja nie zależy od hamowania fazowego.**

| zadana aktywność | 2% | 5% | 10% | 15% | 20% | 30% |
|---|---|---|---|---|---|---|
| rozstęp `dec` po `W_FS_GC` 0–5 | 0.029 | 0.054 | 0.083 | 0.103 | 0.077 | 0.059 |
| 2 × SEM komórki | 0.061 | 0.087 | 0.126 | 0.099 | 0.081 | 0.062 |
| nachylenie (p) | −0.004 (0.48) | −0.011 (0.21) | −0.017 (0.17) | −0.021 (0.03) | −0.014 (0.13) | +0.001 (0.93) |

Łącznie: nachylenie **−0.003, p = 0.60**. Nachylenia są lekko ujemne; jedyne
nominalnie istotne (15%) nie przechodzi korekty na 6 porównań (próg 0.008). Brak
jakiegokolwiek dodatniego efektu: **cały efekt hamowania z E1 był efektem
wyciszania sieci**.

**Wynik: maksimum retencji idzie za rzadkością wejścia — tautologia, zamknięte.**

| rzadkość wejścia `P_active` | 0.10 | 0.25 | 0.40 |
|---|---|---|---|
| maksimum retencji przy frakcji aktywnych | 10% | 20% | 28% |

Własność estymatora, nie punkt pracy obwodu. **Nie raportować „optimum przy 25%".**

Separacja wobec nulli przy kolejnych poziomach aktywności — interpretacja w sek. 3.5:

| zadana aktywność | 2% | 5% | 10% | 15% | 20% | 30% |
|---|---|---|---|---|---|---|
| `dec` | 0.632 | 0.495 | 0.333 | 0.257 | 0.188 | 0.113 |
| nadwyżka nad null k-WTA | +0.324 | +0.274 | +0.172 | +0.133 | +0.100 | +0.078 |

> Korekta z 2026-10-06: pierwotnie odczytałem nadwyżkę nad nullem permutacyjnym
> (−0.389 ± 0.245) jako „obwód separuje gorzej niż null". **Wycofane** — ta nadwyżka
> to algebraicznie `−r_out` (sek. 3.5).

**E1″ — szerszy sweep (2026-10-07) · wynik: brak zależności; bliskie trafienie
to zapłon sieci.** E1′ trzymało na sztywno trzy rzeczy: `R_in` = 0.75,
mossy cells martwe, miarę ślepą na czas. E1″: `R_in` ∈ {0.5, 0.75, 0.9, 0.95} ×
reżim ∈ {mc_inert, mc_active} × `W_FS_GC` ∈ {0, 0.5, 1, 2, 3, 5, 8, 12} × aktywność
∈ {2, 5, 10, 20%} × 5 seedów = 1280 punktów, dostrojono 1267 (`--preset wide`;
3 shardy na `plgrid-now`). Drugi wynik obok `dec`: **dyskryminowalność czasowa**
`sep_t` = (korelacja wzorca z własnym powtórzeniem) − (korelacja z innym wzorcem),
okna 20 ms. Analiza: `python analyze_matched_activity_wide.py`; figury
`matched_activity_wide_{dec,sept,tuning}.png`.

*Kryterium zapisane przed liczeniem* (`prereg_test`): zależność tylko wtedy, gdy
nachylenie względem `W_FS_GC` jest istotne po korekcie Bonferroniego na wszystkie
testy **i** potwierdza się z tym samym znakiem w sąsiednim `R_in`. `sep_t` oceniane
tylko tam, gdzie korelacja z powtórzeniem ≥ 0.05 (próg dodany po pilocie, przed
głównym przebiegiem — przy 5% aktywności taktowanie się nie powtarza).

**Wynik zapisanego testu: brak zależności.** 40 testów, próg p < 1.25·10⁻³.
`dec`: 32 komórki, nominalnie p < 0.05 w 6 (z przypadku ~1.6), po korekcie w 2 —
obie w `mc_active` przy 20%: `R_in` 0.95 (zmiana −0.293, p = 1.4·10⁻⁴) i 0.75
(−0.192, p = 7.0·10⁻⁴). Nie są sąsiednie; komórka między nimi (0.90) ma ten sam
znak, ale p = 3.2·10⁻³, więc kryterium nie jest spełnione. `sep_t`: 8 ocenianych
komórek, po korekcie 0. Bez mossy cells wszystko jest płaskie do `W` = 12, w każdym
`R_in`.

**Bliskie trafienie to zapłon sieci, nie „szybsze komórki".** W komórce `mc_active` /
20% przy `W_FS_GC` = 0 większość punktów miała pozorną częstotliwość ~280 Hz na
aktywną komórkę (przy `W` ≥ 2: ~4 Hz). ⚠️ **Ta miara była błędna:** liczyła średnią
częstotliwość z 4 wzorców wejścia, a frakcję aktywnych — tylko z wzorca 0, na którym
bisekcja trzymała aktywność. Gdy inny wzorzec zapalał całą sieć, iloraz dawał
„280 Hz na aktywną komórkę". Pomiar per wzorzec (E1‴) pokazuje, że komórki nie
strzelają szybciej: wzorzec albo zostaje przy zadanej aktywności i 2–4 Hz, albo
zapala ~100% GC. **Wycofane (2026-10-07):** odczyt „toniczne ustala ile komórek
strzela, fazowe — jak szybko" i liczby 278.5 / 90.4 / 26.4 Hz z poprzedniej wersji.

**E1‴ — test potwierdzający (2026-10-07) · wynik: nie przeszedł.**
`run_runaway_confirm.py` (3 shardy na `plgrid-now`, jobs 3345806/09/13), figura
`article/figures/fig6-runaway.png`. Nowe seedy 10–19, oś siły pętli MC λ (0 =
`mc_inert`, 1 = `mc_active`, liniowo; też 0.5 / 0.75 / 1.5). Część A: aktywność
zadana (5 λ × {5, 10, 20%} × 7 `W` × 10 seedów = 1050 pkt). Część B: bez bisekcji,
`K_GC` ∈ {6…26} × `W` ∈ {0…5} × λ ∈ {0, 1} × 5 seedów = 360 pkt. Kryterium zapisane
w kodzie przed przebiegiem (`PREREG_RUNAWAY`; poprawka po pilocie — częstość
zapłonu jako wynik główny — też przed przebiegiem).

| kryterium | wynik |
|---|---|
| **R1b** (główne): więcej zapłonów przy `W` = 0 niż `W` = 2, λ = 1 i 1.5 | ✗ — λ = 1: 2/20 vs 0/20 (p = 0.24); λ = 1.5: 4/20 vs 0/20 (p = 0.053, próg 0.025) |
| R1a: średnia log-częstotliwość, `W` = 0 vs 2 | ✗ — w żadnej komórce |
| R2: bez MC (λ = 0) brak zapłonów | ✓ — 0/210 |
| R3: zapłon da się zatrzymać przy `W` ≤ 5 | ✓ — ale niemal trywialnie, bo zapłonów prawie nie ma |
| R4: bez bisekcji toniczne steruje liczbą aktywnych, fazowe częstotliwością (λ = 1) | ✗ — fazowe wyjaśnia 5% wariancji częstotliwości, toniczne 78% |

**Co widać eksploracyjnie** (zapłon = jeden z dwóch wzorców zapala ~całą sieć;
liczone na wszystkich aktywnościach, n = 30 na punkt):

| λ | `W` = 0 | 0.25 | 0.5 | 1 | 2 | 3 | 5 |
|---|---|---|---|---|---|---|---|
| 0 i 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0.75 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **1** (`mc_active`) | 2 | 2 | 1 | 0 | 0 | 0 | 0 |
| 1.5 | 6 | 8 | 12 | 7 | 1 | 0 | 0 |

Część B (λ = 1, bez wyrównywania aktywności): przy `K_GC` zgodnym z danymi (6, 10)
i `W` = 0 aktywnych jest **100%** komórek; `W` = 2 sprowadza to do 18–26%. `K_GC` = 14
(poza zakresem danych, sek. 3.8) zapobiega zapłonowi także bez hamowania fazowego.

**Odczyt:** z aktywnymi mossy cells sieć ma drugi, patologiczny stan — zapłon prawie
całej populacji — a hamowanie fazowe (`W` ≥ 3) zawsze mu zapobiega. To zjawisko
jakościowe i spójne, ale **jego częstość zależy od siły pętli MC, której nie znamy**
(przy wagach `mc_active` 2/20). Przy fizjologicznym hamowaniu tonicznym tylko
hamowanie fazowe chroni przed zapłonem. Wynik eksploracyjny; nie raportować jako
potwierdzonego. Rozbieżność z E1″ (tam zapłon w większości punktów przy 20%) to
częściowo liczba wzorców (4 zamiast 2 — więcej okazji do zapłonu), częściowo seedy.

### 3.5 ⭐ Null-e — z czym porównujemy obwód · wynik: oba zawodzą

**Metodologiczny rdzeń pracy i najmocniejszy kandydat na wynik publikowalny.**
Figura: `article/figures/fig5-nulls.png`.

**Wynik w jednej tabeli** (E1′, `r_in` = 0.748; niższe `r_out` = silniejsza dekorelacja):

| | `r_out` | % `r_in` | czym jest |
|---|---|---|---|
| null permutacyjny | 0.001 | 0% | **sufit** — osiąga zero, niszcząc całą informację |
| **DG** | **0.390** | **52%** | |
| null k-WTA | 0.580 | 78% | **prawie-izometria** — losowa projekcja zachowuje korelację |

**Oba null-e obejmują obwód zamiast wyznaczać poziom odniesienia.**

**Dlaczego permutacyjny zawodzi.** Przetasowanie niszczy odpowiedniość
wzorzec–komórka, więc jego `r_out` → 0 i wynik zbiega do `r_in`:

```
dec_null_perm ≈ r_in        (zmierzone: 0.5687 vs r_in 0.5682)
nadwyżka = (r_in − r_out) − r_in = −r_out
```

Zmierzone: `−r_out` = −0.4181, nadwyżka = −0.4186. Nadwyżka nad tym nullem nie
niesie nic ponad `r_out`, a sufit, który wyznacza, jest osiągalny tylko przez
wyrzucenie bodźca.

**Dlaczego k-WTA zawodzi w drugą stronę.** Losowa projekcja gaussowska zachowuje
iloczyny skalarne (Johnson–Lindenstrauss), więc z konstrukcji słabo dekoreluje.
„DG bije losową projekcję o +0.19" jest prawdą, ale to niska poprzeczka, a przewaga
maleje z aktywnością (tabela w sek. 3.4) — w tę samą stronę co confound rzadkości.

**Skąd ta przewaga: z progu spajkowania, nie z hamowania.** Na koalicjach E2
(`mc_active`, nadwyżka nad k-WTA): obwód **bez żadnego hamowania** daje **+0.094**
z +0.152 pełnego obwodu — ~61% przewagi to sam próg. Pozostałe +0.059 nie jest
kontrolowane aktywnością (frakcja spada 0.149 → 0.129), a pomiar kontrolowany
(sek. 3.4) nie wykrywa efektu hamowania fazowego. Zgodne z 1A, gdzie usunięcie
hamowania poprawiało odczyt.

**Uwaga dla E2:** odjęcie nulla permutacyjnego nie może zmienić wartości Shapleya
(null ≈ `r_in`, stałe między lezjami) — więc nie jest kontrolą dla E2. Sek. 3.6.

### 3.6 E2 — atrybucja motywów · wynik: zdominowany przez aktywność

**Jak policzone.** Trzy motywy można niezależnie wyłączać, więc wkład każdego to
wartość Shapleya po 2³ = 8 koalicjach lezji. Siatka `full`: 6 `R_in` × 6 `P_active`
× 3 poziomy napędu × 2 reżimy MC × 5 seedów (job 3167904; przeliczone z nullami
jako 3334385). Liczby: **kanoniczny napęd ×1.0**, 36 punktów × 5 seedów. Figury:
`article/figures/slides/slide-e2.png`, `e2_motif_attribution/results/fig1..4*.png`.

| reżim MC | φ_FF | φ_FB | φ_MC | interakcje | `dec`: bez hamowania → pełny obwód |
|---|---|---|---|---|---|
| `mc_inert` | +0.072 | +0.036 | 0.000 | FF×FB +0.025 | +0.065 → +0.173 |
| `mc_active` | +0.200 | +0.157 | −0.226 | FF×FB +0.126 · FF×MC +0.223 · FB×MC +0.210 | +0.065 → +0.197 |

**Wkłady są zdominowane przez aktywność.** Lezje zmieniają frakcję aktywnych GC
(`mc_active`, napęd ×1.0):

| koalicja | brak | FF | FB | **MC** | FF+FB | FF+MC | FB+MC | pełny |
|---|---|---|---|---|---|---|---|---|
| frakcja aktywnych | 0.20 | 0.15 | 0.20 | **0.94** | 0.13 | 0.70 | 0.60 | 0.18 |
| `dec` | 0.065 | 0.124 | 0.088 | **−0.343** | 0.173 | −0.162 | −0.211 | 0.197 |

Po koalicjach korelacja aktywności z `dec` wynosi **−0.97**. Same mossy cells, przy
wyłączonych motywach hamowania, rozpędzają sieć do 94% aktywnych komórek — to ta
sam zapłon sieci, który widać w E1″/E1‴. Ujemne φ_MC i dodatnie interakcje MC
z hamowaniem znaczą więc przede wszystkim: **MC rozpędzają sieć, hamowanie ją
trzyma** — to zdanie o regulacji aktywności, nie o separacji.

⚠️ **Wycofane:** twierdzenie, że ta atrybucja „przeżywa kontrolę nullem" (2026-10-06).
Null permutacyjny ≈ `r_in`, a `r_in` jest stałe między lezjami, więc jego odjęcie
nie może zmienić wartości Shapleya — test był pusty z konstrukcji. Niepusta kontrola
(null projekcji losowej, który zależy od liczby aktywnych komórek) zmniejsza wkłady
o 15–27% (φ_FF +0.170, φ_FB +0.131, φ_MC −0.164, FF×MC +0.191, FB×MC +0.166), ale
ich nie usuwa — i sama jest słaba (sek. 3.5).

**Zależność od napędu** (`mc_active`): przy ×0.5 φ_FF +0.024, φ_FB +0.034,
φ_MC −0.058, FF×MC +0.053; przy ×2.0 φ_FF +0.185, φ_FB +0.098, φ_MC −0.237,
FF×MC +0.285.

**Hamulec FS→HMC** (wcześniejsza, mała siatka, bez kontroli aktywności): `W_FS_HMC`
= 0 → `dec` −0.267 (FR_HMC 98 Hz); = 2 → +0.247; ≥ 5 → +0.15. W świetle powyższego
najpewniej też efekt aktywności.

**Skalowanie:** separacja rośnie z rozmiarem sieci (+0.149 → +0.231 → +0.296 dla
N_GC = 200 → 400 → 800) — bez kontroli aktywności.

### 3.7 1A — odczyt downstream · wynik: DG nie pomaga odbiorcy

**Jak policzone.** Ten sam klasyfikator liniowy na czterech wejściach: surowe,
przez DG, DG bez hamowania, losowy kod o dopasowanej rzadkości. Miara niezależna
od korelacji, więc nie podlega pułapce z sek. 3.3. Figura:
`article/figures/slides/slide-1a.png`.

```
surowe 0.940  ·  DG 0.885  ·  DG bez hamowania 0.935  ·  losowy rzadki 0.885
```

DG pogarsza odczyt o 0.054, losowy kod remisuje z DG, usunięcie hamowania poprawia
wynik. Hipoteza ratunkowa (krótkie okno odczytu) też obalona: skracanie T pogarsza
DG bardziej (−0.181 → −0.300 dla T = 600 → 60 ms przy R_in 0.90). Zamknięte.

**1B (pojemność pamięci skojarzeniowej) — odłożone.** Przy N_GC = 200 pojemność
kolapsuje do 2–4 wzorców we wszystkich warunkach naraz; prawdziwe DG→CA3 czerpie
z ekspansji, potrzeba N_GC ≥ 2000. Obecnych liczb nie traktować jako wyniku.
⚠️ Binaryzacja top-k na niemal binarnym wejściu wybiera spośród remisów i sztucznie
dekoreluje baseline — metryka główna używa progu w połowie zakresu.

### 3.8 Dane Madara — właściwości błony

`dg_core/madar_intrinsics.py` czyta pomiar eksperymentatora z adnotacji MATLAB.
Po deduplikacji po ID (72 rekordy → 42 komórki GC; **bez deduplikacji mediana
wychodzi −70 zamiast −76**):

| typ | n | V_rest [mV] mediana [IQR] | τ_m [ms] | Rm [MΩ] |
|---|---|---|---|---|
| GC | 53 | **−76 [−81…−70]** (n=42) | 3 [2–5] | 130 [94–198] |
| FS | 4 | −70 [−72…−65] | 1 | 51 |
| HMC | 19 | −67 [−74…−60] | — | — |
| CA3 | 15 | −72 [−76…−68] | — | — |

Model przy `K_GC = 10` ma V_rest = −78.7 mV — **wewnątrz IQR**. Dane **ograniczają**
`K`, ale go nie wyznaczają: IQR odpowiada `K` ≈ 0–13.6.

| `K_GC` | 0 | 5 | **10** | 13.6 | 15 | 20 |
|---|---|---|---|---|---|---|
| `V_rest` [mV] | −70.0 | −75.0 | **−78.7** | −81.0 | −81.8 | −84.5 |

⚠️ **Konsekwencja dla E1′/E1″:** bisekcja dobiera `K` sama. Przy celu 2–5% aktywności
wychodzi mediana `K` ≈ 14–17 (E1″: 99% punktów przy 2%, 89% przy 5% ma `K` > 13.6),
czyli komórki bardziej spolaryzowane niż ~75% zmierzonych GC. Przy 10% — 44%, przy
20% — 3%. Wyniki przy najniższych aktywnościach dotyczą więc obwodu na skraju
zakresu fizjologicznego.

**Skąd napęd 8 mV (panel a fig. 3) — to nie jest pomiar.** Średni napęd aktywnej GC =
częstotliwość wejścia × waga × stała czasowa synapsy = 400 Hz × 4 mV × 5 ms = 8 mV,
z fluktuacjami ok. ±4 mV (szum Poissona). 400 Hz = 40 włókien × 10 Hz (`dg_params.py`;
reprezentacja zagregowana, prawdziwa GC ma tysiące synaps PP). Waga 4 mV została
**dobrana** tak, żeby GC strzelały ~6 Hz. Panel (a) opisuje więc reżim pracy
(próg 14 mV leży ~1.5 odchylenia nad średnią → odpalają tylko fluktuacje), a
niezależnym ograniczeniem z danych jest wyłącznie panel (b). To samo pytanie, od
strony danych: B3 w sek. 2.
Rozbieżność τ_m: pytanie w sek. 2.

### 3.9 Kanał FS→FS (poboczne)

Wzajemne hamowanie interneuronów (`W_FS_FS`, domyślnie 0.0 — obwód bez zmian):

| `W_FS_FS` | 0.0 | 0.5 | 1.0 | 2.0 | 4.0 |
|---|---|---|---|---|---|
| FR_FS [Hz] | 46.0 | 41.8 | 37.8 | 33.4 | 27.6 |
| FR_GC [Hz] | 3.12 | 3.09 | 3.37 | 3.65 | 4.08 |

---

## 4. Co dalej — proponowana kolejność

### 4.0 Krok 1 — pilne, bez decyzji (1 dzień)

1. **Commit i push** obecnego stanu (E3.8–E3.9h, porządki w notatkach, zmiana konta SLURM).
2. **Mail do prof. Błasiak:** przewidywanie [PREDICTION_gabazine.md](experiments/calib_exvivo/PREDICTION_gabazine.md)
   z linkiem do commita `75ccd60` na GitHubie (dowód, że zapisane przed analizą) + pytania
   C1, C2, B4, τ_m z sek. 2. **Pilne, bo przewidywanie ma wartość tylko przed analizą ich danych.**

### 4.1 Krok 2 — decyzja o artykułach (blokuje pisanie)

Kandydaci i to, co ich podpiera:

| | artykuł | dowody | czego brakuje |
|---|---|---|---|
| **(a)** | metodologiczny: dekorelacja bez kontroli aktywności zwodzi, a oczywiste kontrole (null-e) same są pułapkami | **komplet**: E1, E1′, null-e, E2 (sek. 3.3–3.6) + funkcjonalne odpowiedniki z E3 (E3.1: optimum dla uczenia, którego dekorelacja nie widzi; E3.3: kontrola o tej samej średniej odwraca wniosek) | tylko pisanie |
| **(T)** | narzędzie + model skalibrowany do skrawka | draft, kalibracja v4, przewidywanie gabazyny | kompilacja draftu; dane Oli i Kingi — **potwierdzone przewidywanie byłoby najmocniejszym wynikiem tej części** |
| **(M1)** | ML: rzadkość sterowana nowością jako trzeci czynnik | E3.1–E3.9h | porównanie z korektą przechylenia (WA/BiC), potwierdzenia na nowych sieciach (README E3 sek. 7, kroki 1–2) |
| **(d)** | padaczka: utrata mossy cells / hamowania | maszyneria MC, zapłon w E1‴ (rzadki, eksploracyjny) | siła MC→GC z danych (B4) |
| (b) | mossy cells jako motyw warunkowy separacji | — | odpada: to regulacja aktywności (sek. 3.6) |

**Propozycja:** dwa artykuły zamiast czterech.
1. **Neuro: (a) + (T) razem** — model DG związany danymi skrawka i narzędzie, z wynikiem
   metodologicznym jako głównym przesłaniem i przewidywaniem gabazyny jako walidacją
   prospektywną. Pisanie można zacząć od razu od części (a); sekcja walidacji czeka na dane.
2. **ML: (M1)** — po krokach 1–2 z README E3 sek. 7; od wyniku porównania z korektą przechylenia
   zależy, czy teza brzmi „sterowanie rzadkością jako biologiczna korekta przechylenia”, czy
   jest wynikiem metodologicznym o kontroli dopasowanej rzadkości.
3. **(d)** tylko jeśli B4 wskaże silną pętlę MC (λ ≥ 1.5 w E1‴).

Do decyzji z promotorem: czy (a) i (T) w jednym artykule, czy osobno (draft (T) pozwala na obie drogi).

### 4.2 Krok 3 — obliczenia dla M1 (1–2 tygodnie, równolegle z pisaniem)

Szczegóły i uzasadnienie: README E3 sek. 7. W kolejności:
1. porównanie z korektą przechylenia wyjść (na gotowych kodach, tanie);
2. potwierdzenie E3.9 i E3.5 (architektura domyślna) na sieciach 5–9, z kryteriami zapisanymi z góry;
3. hamowanie zależne od aktywności zamiast globalnego `K`;
4. warstwa ukryta, która uczy się bez katastrofy (bramkowanie odgórne) — krok w stronę celu
   docelowego (DG jako mechanizm trójczynnikowy / odgórny w SNN).

### 4.3 Krok 4 — pisanie

1. Skompilować draft na Overleafie (nigdy nie kompilowany; na Athenie nie ma LaTeX-a).
2. Artykuł neuro wg decyzji z 4.1; zaktualizować prezentację o kalibrację i E3.

### 4.4 Czeka na innych

- Dane Oli i Kingi → porównanie z przewidywaniem (calib_exvivo README, „Dalej”).
- B4 → decyzja o (d).

### 4.5 Zaległe, niski priorytet

- R_w w porównaniach modelu (E1/E1′ w reżimie ex vivo) — może dać miarę separacji z optimum.
- Krzywe f–I z CCIV (HMC: 26 plików, GC+CA3: 66; FS brak) — protokół odzyskiwalny z adnotacji.
- Suwak `W_FS_HMC` w `interactive_dg.py` — przydatny tylko przy wariancie (d).
- Hipotezy w PLAN_BADAWCZY — przepisać dopiero po decyzji z 4.1 (świadomie nieruszane).

---

## 5. Ustalenia o modelu

Zmierzone, nadal obowiązujące.

**Wejście PP** (`dg_params.py` = jedyne źródło prawdy): 40 włókien × 10 Hz =
**400 Hz** na aktywny GC. Przy 600 Hz GC dawały 16.6 Hz (za gęsto); 400 Hz daje ~6 Hz.

**Próg `G_crit = 4 + K`.** Wyprowadzone analitycznie, potwierdzone symulacją co do
0.1 mV. GC/HMC (K=10, próg 14 mV) trudniej pobudliwe niż FS (K=5, próg 9 mV). Napęd
400 Hz daje g_ex ≈ 8 mV — poniżej progu GC, czyli reżim fluktuacyjny.

**Mossy cells przy domyślnych wagach są martwe (0.00 Hz).** Napęd GC→HMC (1 mV) nie
zbliża się do progu 14 mV. Każdy wniosek o MC przy domyślnych ustawieniach dotyczy
obwodu bez nich — stąd obowiązek dwóch reżimów `mc_inert`/`mc_active` w każdym
sweepie (PLAN sek. 3.3).

**`b` ustawia sumę `V_rest + V_th_eff`, `K` ich odstęp.** Przy `b = 0.2` suma jest
zablokowana na −120 mV: para (−70, −50) wychodzi przy `K = 0`, a (−70, −45) wymaga
`b = 0.4` i wtedy K rośnie do 14.

**P(AP|puls) nie jest sterowalne samą wagą** — bez źródła zmienności krzywa jest
skokowa (0.00 → 0.99). Stąd zawodność synaptyczna `P_REL_*`: przy kompensacji wagą
`W/p` wariancja rośnie jak `1/p` (FR 3.12 → 5.46 → 9.22 Hz dla p_rel 1.0 → 0.5 →
0.25). `p_rel` i wagę kalibrować razem.

Cztery pułapki obowiązujące w każdym nowym sweepie (skalowanie, dwa reżimy MC, próg
ważności, potrójna rola `K_GC`): PLAN sek. 3.5.

---

## 6. Zawartość `article/`

| plik | co to jest |
|---|---|
| `article_draft.tex` | draft artykułu o **narzędziu i mechanizmie** (ang., Overleaf; bez bibtexa) |
| `figures/fig1..fig6-*.png` | 6 figur artykułu |
| `figures/slides/*.png` | figury artykułu bez nagłówków „Figure N." + 4 figury jednopanelowe pod slajdy |
| `prezentacja_stan_prac.pptx` | prezentacja stanu prac z 2026-10-07; notatki slajd po slajdzie: `prezentacja_notatki.md` |
| `make_article_figures.py`, `build_presentation.py` | generatory — wszystko jest odtwarzalne |

**Przebudowa wszystkiego:**

```bash
python article/make_article_figures.py     # figury artykułu + figury slajdów
python article/build_presentation.py       # deck .pptx
```

**Draft** opisuje aplikację dla neurobiologów i mechanizm separacji; wyniki podaje
jako demonstracje możliwości warsztatu, nie jako tezę — więc nie przesądza sek. 4.1.
Ma jawne `\todo{}`: afiliacje i współautorzy, rozbieżność τ_m, kontener i depozyt
danych, URL repozytorium, finansowanie, brakująca bibliografia.

**Prezentacja** jest w python-pptx (precedens repo). Na Athenie nie ma LaTeX-a ani
LibreOffice, więc: draft sprawdzony statycznie (balans nawiasów i środowisk), deck —
walidatorem struktury OOXML i podglądem renderowanym w PIL z konserwatywną czcionką.
**Pierwsze otwarcie w PowerPoincie / pierwsza kompilacja na Overleafie są realną
kontrolą.**

---
