# Status — gdzie jesteśmy, wyniki, decyzje

*Aktualizacja: 2026-10-07.*

Jedyne źródło prawdy dla **stanu prac** i **zmierzonych liczb**. Każda liczba ma tu
jedno miejsce; inne dokumenty odsyłają tutaj. Hipotezy i plan:
[PLAN_BADAWCZY.md](PLAN_BADAWCZY.md). Instalacja i uruchamianie: [README.md](README.md).

> **Mapa.** `0` w dwóch minutach · `1` stan prac · `2` pytania do prof. Błasiak ·
> **`3` wyniki** · **`4` decyzje** · `5` ustalenia o modelu · `6` zawartość `article/` ·
> **`7` prezentacja slajd po slajdzie**
>
> **Kolejność czytania:** sek. 0 → tabela w sek. 3.2 → decyzja w sek. 4.1.
> Pod prezentację: sek. 7.

---

## 0. W dwóch minutach

**Co badaliśmy.** Zakręt zębaty (DG) ma „separować wzorce": z podobnych wejść robić
mniej podobne wyjścia. Mierzy się to spadkiem korelacji, `dec = r_in − r_out`.
Teza projektu: *separacja ma optimum przy pośrednim poziomie aktywności, a steruje
nim siła hamowania* (H1 w planie).

**Co wyszło.** Teza jest **obalona** i nie da się jej uratować większą siatką ani
inną miarą. `dec` rośnie samo, gdy sieć cichnie — korelacja dwóch prawie pustych
wektorów dąży do zera. Każde wzmocnienie hamowania wycisza sieć, więc „poprawia
separację" z przyczyny niezwiązanej z obwodem. Przy wyrównanej aktywności hamowanie
fazowe nie zmienia separacji wcale.

**Najciekawszy wynik jest metodologiczny.** Żeby odróżnić separację od wyciszenia,
porównuje się obwód z *nullem* — sztucznym kodem o tej samej rzadkości, ale bez
obwodu (definicja: sek. 3.1). Oba naturalne null-e **zawodzą, w przeciwne strony**:
jeden niszczy całą informację, drugi prawie nic nie zmienia. Zamiast wyznaczać
poziom odniesienia, obejmują obwód z dwóch stron (sek. 3.5).

**Co zostaje na plusie.** Podział zasług między motywami hamowania jest realny
i przeżywa kontrolę nullem: mossy cells **same pogarszają** separację, a w parze
z hamowaniem dają największy wkład (sek. 3.6).

**Co dalej.** Jedna decyzja: **czym jest teza pracy** — cztery warianty
z rekomendacją w sek. 4.1. Nic nie zostało do policzenia, co zmieniłoby ten obraz.

---

## 1. Stan prac

| obszar | stan |
|---|---|
| Narzędzie `interactive_dg.py` | działa; bilans hamowania, panel P(AP) |
| Rdzeń `experiments/dg_core/` | działa; testy regresji 17/17, domyślna konfiguracja bit w bit jak przed zmianami |
| Eksperymenty E1, E1′, E2, 1A | **policzone i przeanalizowane** — wyniki w sek. 3.2 |
| Kontroler adaptacyjny (E4/E5) | **niezbudowany**; to wariant (c) w sek. 4.1, nie domyślny kierunek |
| Kalibracja punktu pracy | maszyneria gotowa, **specyfikacja czeka na odpowiedzi z sek. 2** |
| Draft artykułu o narzędziu | `article/article_draft.tex` — gotowy do przeczytania, **nieskompilowany** (sek. 6) |
| Prezentacja stanu prac | `article/prezentacja_stan_prac.pptx`, 13 + 3 zapasowe slajdy (sek. 7) |
| Pomysł na artykuł ML | [`ml_paper.md`](ml_paper.md) — propozycja, zero wyników (sek. 4.2) |

---

## 2. Pytania do prof. Błasiak — blokują tylko kalibrację

Nie blokują ani decyzji z sek. 4.1, ani pisania. Blokują domknięcie punktu pracy:
bez tych liczb każda próba kalibracji trafia w jedno kryterium kosztem drugiego.
Mail z 2026-09-11 bez odpowiedzi; draft ponowienia:
[`korespondencja/2026-10-07_mail_blasiak.md`](korespondencja/2026-10-07_mail_blasiak.md).

**B1. Jaki jest realny udział hamowania tonicznego w GC?** W modelu (wkłady do
`dv/dt`, te same jednostki):

| komórka | pobudzenie | hamowanie fazowe | hamowanie toniczne (K) | udział tonicznego |
|---|---|---|---|---|
| **GC** | PP 2.43 | FS→GC **3.59** | **10.0** | **74%** |
| **FS** | PP 7.32 + GC 1.85 | 0.0 (kanał nie istniał) | 5.0 | 100% |
| **HMC** | GC 0.20 | 0.0 (`W_FS_HMC=0`) | 10.0 | 100% |

74% jest **odziedziczone, nie wybrane**. Odpowiedź wymusza `K`, a przez jego potrójną
rolę (PLAN sek. 3.5, pułapka 4) także próg i potencjał spoczynkowy.

**B2. Czy ~46 Hz to fizjologiczna częstotliwość bazowa FS?** Prawdopodobnie zawyżona
z przyczyny strukturalnej: FS nie miały żadnego hamowania synaptycznego. Dodany kanał
FS→FS obniża ją do ~28 Hz (sek. 3.9), ale jego siła wymaga zakotwiczenia w biologii.

**B3. Do którego reżimu wejścia kalibrujemy — in vitro czy in vivo?** Pytanie
najważniejsze. Waga dobrana protokołem pulsowym Madara (tło 40 Hz), użyta w sieci
przy napędzie 400 Hz, daje GC **22 Hz zamiast 2–6 Hz**. Jedna waga nie obsłuży obu
reżimów — trzeba wybrać warunek kontrolny.

**Drobne: τ_m.** Z danych Madara τ_m ≈ 3 ms dla GC, a nie 10–50 ms z korespondencji.
Izhikevich nie ma jawnego τ_m, więc symulacji to nie zmienia, ale do Methods trzeba
wiedzieć, czy to różnica definicji (opór wejściowy vs błonowy).

---

## 3. Wyniki

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
ale bez obwodu; odejmuje tę część dekorelacji, którą daje sama rzadkość.
*Permutacyjny*: wektor częstotliwości przetasowany po komórkach. *k-WTA*: losowa
projekcja wejścia, zostawione tyle najsilniejszych jednostek, ile aktywnych GC.

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
| **E2** motywy (sek. 3.6) | który motyw hamowania niesie separację? | **Mossy cells warunkowo:** same −0.23, w parach +0.21…+0.22; odporne na null |
| **1A** odczyt (sek. 3.7) | czy klasyfikator czyta DG lepiej niż wejście? | **Nie.** 0.885 vs 0.940 |
| **dane Madara** (sek. 3.8) | czy punkt pracy jest związany danymi? | **Tak.** `K_GC=10` → `V_rest` −78.7 mV, wewnątrz IQR [−81, −70] |

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
„DG bije losowy kod rzadki o +0.19" jest prawdą, ale to niska poprzeczka, a przewaga
maleje z aktywnością (tabela w sek. 3.4) — w tę samą stronę co confound rzadkości.

**Skąd ta przewaga: z progu spajkowania, nie z hamowania.** Na koalicjach E2
(`mc_active`, nadwyżka nad k-WTA): obwód **bez żadnego hamowania** daje **+0.094**
z +0.152 pełnego obwodu — ~61% przewagi to sam próg. Pozostałe +0.059 nie jest
kontrolowane aktywnością (frakcja spada 0.149 → 0.129), a pomiar kontrolowany
(sek. 3.4) nie wykrywa efektu hamowania fazowego. Zgodne z 1A, gdzie usunięcie
hamowania poprawiało odczyt.

**Co przeżywa:** atrybucja motywów — szczegóły w sek. 3.6.

### 3.6 E2 — atrybucja motywów · wynik: jedyny pozytywny, odporny na kontrolę

**Jak policzone.** Trzy motywy można niezależnie wyłączać, więc wkład każdego to
wartość Shapleya po 2³ = 8 koalicjach lezji. Siatka `full`: 6 `R_in` × 6 `P_active`
× 3 poziomy napędu × 2 reżimy MC × 5 seedów (job 3167904; przeliczone z nullami jako
3334385, `dec` odtworzone bit w bit). Liczby poniżej: **kanoniczny napęd ×1.0**,
36 punktów × 5 seedów. Figury: `article/figures/slides/slide-e2.png`,
`e2_motif_attribution/results/fig1..4*.png`.

| reżim MC | φ_FF | φ_FB | φ_MC | interakcje | `dec`: bez hamowania → pełny obwód |
|---|---|---|---|---|---|
| `mc_inert` | +0.072 | +0.036 | 0.000 | FF×FB +0.025 | +0.065 → +0.173 |
| `mc_active` | +0.200 | +0.157 | **−0.226** | FF×FB +0.126 · FF×MC +0.223 · FB×MC +0.210 | +0.065 → +0.197 |

**Co znaczy.** Mossy cells **same** korelują wzorce (re-ekscytują GC), ale w parze
z każdym motywem hamowania dają największy wkład ze wszystkich. **MC to motyw
warunkowy.** W `mc_inert` są martwe (sek. 5), stąd φ_MC = 0.

**Odporne na null.** Null jest praktycznie stały po koalicjach (rozstęp 0.0051 przy
rozstępie `dec` 0.3774), bo zależy od `r_in`, którego lezja nie zmienia, a Shapley
jest niewrażliwy na stałą: φ_FF +0.1998 → +0.1999, φ_FB +0.1572 → +0.1555,
φ_MC −0.2257 → −0.2245, FF×MC +0.2227 → +0.2217, FB×MC +0.2096 → +0.2085.

⚠️ **Zależność od napędu** (`mc_active`) — przy słabszym wejściu efekty są kilkukrotnie
mniejsze:

| napęd PP | φ_FF | φ_FB | φ_MC | FF×MC |
|---|---|---|---|---|
| ×0.5 | +0.024 | +0.034 | −0.058 | +0.053 |
| **×1.0** | **+0.200** | **+0.157** | **−0.226** | **+0.223** |
| ×2.0 | +0.185 | +0.098 | −0.237 | +0.285 |

**Hamulec FS→HMC.** Pętla GC→HMC→GC jest czysto pobudzająca i bez hamulca ucieka:
`W_FS_HMC` = 0 → `dec` −0.267 (FR_HMC → 98 Hz, obwód *koreluje* wzorce); = 2 →
+0.247; ≥ 5 → +0.15 (MC znów wyciszone). ⚠️ Z mniejszej, wcześniejszej siatki,
bez nulla — do powtórzenia przed cytowaniem.

**Skalowanie.** Separacja rośnie z rozmiarem sieci (`scaled(N)`, stały in-degree):
+0.149 → +0.231 → +0.296 dla N_GC = 200 → 400 → 800. ⚠️ Bez nulla — może być
efektem samej rzadkości.

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

Model przy `K_GC = 10` ma V_rest = −78.7 mV — **wewnątrz IQR**; przy `K_GC = 0` ma
−70 mV, na górnej krawędzi. **Obecne `K_GC = 10` jest wspierane przez dane.**
Rozbieżność τ_m: pytanie w sek. 2.

### 3.9 Kanał FS→FS (poboczne)

Wzajemne hamowanie interneuronów (`W_FS_FS`, domyślnie 0.0 — obwód bez zmian):

| `W_FS_FS` | 0.0 | 0.5 | 1.0 | 2.0 | 4.0 |
|---|---|---|---|---|---|
| FR_FS [Hz] | 46.0 | 41.8 | 37.8 | 33.4 | 27.6 |
| FR_GC [Hz] | 3.12 | 3.09 | 3.37 | 3.65 | 4.08 |

---

## 4. Decyzje

### 4.1 ⛔ Jedna decyzja blokująca: czym jest teza pracy

Pierwotna teza („separacja ma optimum przy pośredniej aktywności, a hamowanie nią
steruje") jest obalona (sek. 3.3, 3.4). Następcę trzeba wybrać z tego, co dane
faktycznie podpierają.

| | teza | dowód, który mamy | koszt | główne ryzyko |
|---|---|---|---|---|
| **(a)** | metodologiczna: dekorelacja bez kontroli jest zwodnicza, a oczywiste kontrole same są pułapkami | **komplet** (sek. 3.3, 3.5) | samo pisanie | praca metodyczna — niższy prestiż, ale wynik nowy |
| **(b)** | mossy cells jako motyw warunkowy | Shapley odporny na null (sek. 3.6) | niski | efekt **zależy od napędu** i nie jest kontrolowany aktywnością |
| **(c)** | regulacja zamiast separacji (kontroler E4/E5) | brak | najwyższy: nowy moduł | wynik nieznany, miesiące pracy |
| **(d)** ⭐ | **padaczka: utrata mossy cells** (K3) | maszyneria MC gotowa | **jeden sweep** | — |

**Wariant (d) przepisuje sam plan.** PLAN sek. 7.1, **bramka G2**: „H1 potwierdzona
ORAZ H2 potwierdzona na pełnej siatce. Jeśli nie — pivot na robustness/padaczkę z K3
jako wynikiem głównym." H1 jest obalona od 2026-09-21, więc bramka jest otwarta. K3
(PLAN sek. 4): `N_HMC` × {1.0, 0.75, 0.5, 0.25, 0} przy stałym in-degree; rozstrzyga
spór „dormant basket cell" vs „irritable mossy cell", mierząc napęd FS i separację
naraz. Mocny, bo nie zakłada, że DG dobrze separuje; MC to jedyny motyw o dużych
efektach w naszych danych; spór jest kliniczny i otwarty, więc wynik jest publikowalny
niezależnie od znaku.

**Rekomendacja: (d) jako teza nośna + (a) jako osobny, krótszy artykuł.** Nie robić
(c) przed (d). W każdym wariancie przy K3 mierzyć **przy wyrównanej aktywności**
i w kilku napędach — to są dwie słabości (b), których (d) nie powinno odziedziczyć.

### 4.2 Osobna ścieżka: artykuł ML

[`ml_paper.md`](ml_paper.md): **rzadkość jako trzeci czynnik** uczenia oraz null-e
o dopasowanej rzadkości jako protokół ewaluacji. Nie koliduje z sek. 4.1 — inna
publikacja, inne repo wykonawcze (`snn_stdp_vs_surrogate_gradient`, ~80% harnessu
gotowe). Zero wyników ML na dziś.

### 4.3 Po decyzji z 4.1

1. Przepisać hipotezy w PLAN (świadomie nieprzepisane; oznaczone jako historyczne).
2. Kolejność artykułów — (a) da się pisać od zaraz, (d) wymaga sweepu; można równolegle.
3. Czy draft o narzędziu zostaje osobnym artykułem, czy wstępem do (d) — draft
   pozwala na obie drogi.

### 4.4 Niezależne od decyzji — można robić od zaraz

1. **Skompilować draft na Overleafie** — nigdy nie był kompilowany (na Athenie nie ma
   LaTeX-a), sprawdzony tylko statycznie.
2. **`io_madar.py`** — bodźce z `dataset/…/Protocols/` jako wejście PP do
   `dg_core.circuit.simulate()`. Dzień pracy; zmienia „model z syntetycznymi
   wzorcami" w „model napędzany bodźcami z eksperymentu". Wartościowe w każdym
   wariancie.
3. **Krzywe f–I z CCIV.** Protokół odzyskiwalny z adnotacji Axographu (start −100 pA,
   krok 20 pA, 30 epizodów, onset 100 ms, szerokość 500 ms). HMC: 26 plików,
   GC+CA3: 66; FS nie mają żadnego CCIV.
4. **Kalibracja FS→FS** do docelowej częstotliwości FS — czeka na B2.
5. **Suwak `W_FS_HMC` w `interactive_dg.py`** — przy wariancie (d) staje się
   demonstracją tezy.

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
| `figures/fig1..fig5-*.png` | 5 figur artykułu |
| `figures/slides/*.png` | te same figury bez nagłówków „Figure N." + 4 figury jednopanelowe pod slajdy |
| `prezentacja_stan_prac.pptx` | prezentacja stanu prac (sek. 7) |
| `make_article_figures.py`, `build_presentation.py` | generatory — wszystko jest odtwarzalne |

**Przebudowa wszystkiego:**

```bash
python article/make_article_figures.py     # figury artykułu + figury slajdów
python article/build_presentation.py       # deck .pptx
```

**Draft** opisuje aplikację dla neurobiologów i mechanizm separacji; wyniki podaje
jako demonstracje możliwości warsztatu, nie jako tezę — więc nie przesądza sek. 4.1.
Ma jawne `\todo{}`: afiliacje, rozbieżność τ_m, brakująca bibliografia, uwaga do
Methods o 2.2 Hz.

**Prezentacja** jest w python-pptx (precedens repo). Na Athenie nie ma LaTeX-a ani
LibreOffice, więc: draft sprawdzony statycznie (balans nawiasów i środowisk), deck —
walidatorem struktury OOXML i podglądem renderowanym w PIL z konserwatywną czcionką.
**Pierwsze otwarcie w PowerPoincie / pierwsza kompilacja na Overleafie są realną
kontrolą.**

---

## 7. Prezentacja — slajd po slajdzie

`article/prezentacja_stan_prac.pptx`: 13 slajdów głównych (~20 min) + 3 zapasowe na
pytania. Każdy slajd ma notatki prelegenta. Figury na slajdach są po angielsku
(spójnie z artykułem), tekst po polsku. Pointą jest slajd 8; reszta do niego prowadzi.

**1. Tytuł.** Na slajdzie: tytuł i schemat obwodu. Do powiedzenia: model sieci
spajkującej DG, związany danymi patch-clamp; będzie o tym, co ustaliliśmy, co okazało
się pułapką pomiarową i jaka decyzja jest do podjęcia.

**2. W skrócie.** Na slajdzie: trzy karty z liczbami. *obalona* — H1, separacja nie
ma optimum (sek. 3.3–3.4). *2 z 2* — oba naturalne null-e zawodzą (sek. 3.5).
*−0.23 / +0.22* — wkład mossy cells samych i w parze z hamowaniem (sek. 3.6). Na dole
odsyłacz do decyzji. Do powiedzenia: trzy rzeczy do zapamiętania, reszta prezentacji
je rozwija.

**3. Czym jest separacja wzorców** (`fig1-concept`). Na slajdzie: lewo — dwa wzorce
wejściowe, czarne paski to komórki z silnym napędem (pokazane 80 z 200); środek —
częstotliwość każdej komórki na wyjściu; prawo — korelacja wejść 0.73 i wyjść 0.58,
różnica +0.15. Jak policzone: jedna symulacja domyślnej konfiguracji (200 GC,
podobieństwo wejść 0.75, 25% napędzanych, 600 ms). Do powiedzenia: to definicja
operacyjna całej pracy — i ta liczba rośnie sama, gdy sieć cichnie.

**4. Model** (`fig2-circuit`). Na slajdzie: PP napędza GC i równolegle FS
(wyprzedzająco, FF); GC też pobudzają FS (zwrotnie, FB); FS hamują GC; HMC w pętli
pobudzającej. Ramka: dwie osie hamowania. Do powiedzenia: rozdzielenie hamowania
tonicznego (`K_GC`, stały prąd) i fazowego (`W_FS_GC`, synaptyczne) to sedno modelu;
trzy motywy można wyłączać niezależnie.

**5. Punkt pracy jest przypięty danymi** (`fig3-operating-point`). Na slajdzie:
(a) próg odpalenia `G_crit = 4 + K` i realny napęd 8 mV; przy `K_GC = 10` napęd jest
poniżej progu 14 mV. (b) `V_rest(K)` modelu na tle mediany i IQR z 42 komórek
Madara. Jak policzone: analitycznie, z punktów stałych równania Izhikevicza,
zweryfikowane symulacją. Do powiedzenia: komórki strzelają tylko na fluktuacjach —
stąd rzadki kod; ten sam parametr trafia w środek danych. Model nie jest dostrojony
pod wynik.

**6. E1 — separacja rośnie, gdy sieć cichnie** (`slide-e1`). Na slajdzie: szare
punkty to 450 punktów siatki (separacja wobec zmierzonej frakcji aktywnych, oś log
w %). Przerywane linie to cztery progi odrzucania cichych punktów (2, 5, 10, 20%),
gwiazdki — maksimum separacji przy każdym progu. Do powiedzenia: każda gwiazdka
siedzi tuż przy swoim progu; gdyby istniało biologiczne optimum, stałyby w jednym
miejscu. Liczby: sek. 3.3.

**7. E1′ — hamowanie fazowe nic nie zmienia** (`slide-e1p`). Na slajdzie: separacja
wobec siły hamowania fazowego, osobna linia dla każdego z 6 zadanych poziomów
aktywności. Jak policzone: aktywność ustawiana bisekcją po hamowaniu tonicznym,
733 dostrojone punkty. Do powiedzenia: linie leżą na różnych wysokościach (to robi
aktywność), ale żadna nie rośnie z hamowaniem; łączne nachylenie −0.003 (p = 0.60).
Efekt hamowania z E1 był efektem wyciszenia. Liczby: sek. 3.4.

**8. ⭐ Z czym w ogóle porównujemy obwód** (`fig5-nulls`). Na slajdzie: (a) korelacja
wyjścia dla: wejścia bez transformacji 0.75, nulla k-WTA 0.58, DG 0.39, nulla
permutacyjnego 0.00. (b) przewaga DG nad losowym kodem rozbita na obwód bez hamowania
(+0.094, 61%) i dodatek hamowania (+0.059). Jak policzone: (a) z E1′, `r_out` = `r_in`
− `dec`; (b) z koalicji lezji E2. Do powiedzenia — **pointa**: żeby powiedzieć „DG
separuje", trzeba punktu odniesienia o tej samej rzadkości. Oba naturalne zawodzą:
permutacja osiąga zero, bo niszczy całą informację (sufit), losowa projekcja z
definicji zachowuje korelację (trywialna podłoga). Obejmują obwód z dwóch stron.
A przewaga nad losowym kodem to w większości sam próg spajkowania. Szczegóły: sek. 3.5.

**9. E2 — mossy cells: motyw warunkowy** (`slide-e2`). Na slajdzie: wartości Shapleya
trzech motywów i trzech par; pełne słupki — na surowej separacji, kreskowane — po
korekcie nullem. Jak policzone: 8 koalicji lezji, 36 punktów statystyki wejścia
× 5 seedów, kanoniczny napęd. Do powiedzenia: MC same szkodzą (−0.23), w parach
pomagają najbardziej (+0.21…+0.22); korekta nullem nic nie zmienia, bo null nie
zależy od lezji. Zastrzeżenie: przy napędzie ×0.5 efekty ~4× mniejsze. Sek. 3.6.

**10. 1A — odbiorca nie korzysta** (`slide-1a`). Na slajdzie: dokładność klasyfikatora
liniowego dla czterech wejść; linia przerywana = surowe wejście. Do powiedzenia: miara
niezależna od korelacji, więc nie podlega pułapce z E1 — i też nic: DG 0.885 wobec
0.940, losowy kod remisuje z DG, bez hamowania lepiej. Sek. 3.7.

**11. Co upadło, co stoi, co jest nowe.** Na slajdzie: trzy kolumny. *Upadło* —
optimum separacji, sterowanie hamowaniem fazowym, pomoc dla odbiorcy. *Stoi* — punkt
pracy zgodny z danymi, MC jako motyw warunkowy, przewaga nad losowym kodem (głównie
dzięki progowi). *Metodologia* — oba null-e zawodzą, próg odrzucania przesuwa
maksimum, retencja idzie za rzadkością wejścia.

**12. Decyzja: czym jest teza pracy.** Na slajdzie: cztery warianty (a)–(d),
rekomendowany (d) wyróżniony. Do powiedzenia: (d) nie jest naszym pomysłem — plan
przewidywał ten pivot, jeśli H1 nie przejdzie (bramka G2). Rekomendacja: (d) jako teza
nośna + (a) jako osobny artykuł. Sek. 4.1.

**13. Następne kroki.** Na slajdzie: pięć kroków; pierwszy (decyzja) blokuje resztę.
Drugi to trzy pytania kalibracyjne do prof. Błasiak (sek. 2).

**14–16. Zapas.** Gęste figury analityczne na pytania z sali: pełna mapa reżimów E1
(panel c: separacja zmienia się prawie wyłącznie wzdłuż osi hamowania tonicznego),
kontrola dostrojenia E1′ (panel d: czy bisekcja trafiła; panel c: tautologia retencji),
profile wkładów motywów E2 w funkcji statystyki wejścia.

**Trzy pytania, które padną:**

1. *„Czemu nie odrzucić cichych punktów?"* — Próbowaliśmy; maksimum przenosi się
   dokładnie na próg, przy każdym progu (slajd 6).
2. *„Czemu permutacja nie jest dobrą kontrolą?"* — Jej wynik zbiega do `r_in`
   (0.5687 vs 0.5682), więc nadwyżka nad nią to algebraicznie `−r_out` (slajd 8).
3. *„To co zostaje na plusie?"* — Atrybucja motywów: odporna na null, bo null jest
   stały po lezjach, a Shapley ignoruje stałą (slajd 9).
