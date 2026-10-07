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
obwodu (sek. 3.1). Oba naturalne null-e **zawodzą, w przeciwne strony**: jeden
niszczy całą informację, drugi prawie nic nie zmienia. Obejmują obwód z dwóch stron
zamiast wyznaczać poziom odniesienia (sek. 3.5).

**Jedyny efekt obwodu, jaki widzimy, dotyczy regulacji, nie separacji — i jest
słaby.** Przy aktywnych mossy cells sieć bywa **bistabilna**: dla części wejść
zapala się prawie cała populacja komórek ziarnistych (stan przypominający napad),
a hamowanie fazowe (`W_FS_GC` ≥ 3) temu zapobiega. Test potwierdzający na nowych
seedach (E1‴) **nie przeszedł** kryterium zapisanego z góry: przy wagach `mc_active`
zapłony są rzadkie (2/20). Wcześniejsza interpretacja „toniczne ustala ile,
fazowe — jak szybko" (~280 Hz na aktywną komórkę) była artefaktem miary i jest
**wycofana** (sek. 3.4).

**Co upadło po drodze.** Atrybucja motywów E2 wyglądała na wynik pozytywny
(„mossy cells jako motyw warunkowy"). Jest zdominowana przez aktywność, a jej
„kontrola nullem" była pusta z konstrukcji (sek. 3.6).

**Co dalej.** Decyzja o tezie pracy — warianty z rekomendacją w sek. 4.1. Test
potwierdzający dla E1″ jest zrobiony (E1‴, sek. 3.4) i osłabia wariant (d).

---

## 1. Stan prac

| obszar | stan |
|---|---|
| Narzędzie `interactive_dg.py` | działa; bilans hamowania, panel P(AP) |
| Rdzeń `experiments/dg_core/` | działa; testy regresji 17/17, domyślna konfiguracja bit w bit jak przed zmianami |
| Eksperymenty E1, E1′, E1″, E1‴, E2, 1A | **policzone i przeanalizowane** — wyniki w sek. 3.2 |
| Kontroler adaptacyjny (E4/E5) | **niezbudowany**; to wariant (c) w sek. 4.1, nie domyślny kierunek |
| Kalibracja punktu pracy | maszyneria gotowa, **specyfikacja czeka na odpowiedzi z sek. 2** |
| Draft artykułu o narzędziu | `article/article_draft.tex` — gotowy do przeczytania, **nieskompilowany** (sek. 6) |
| Prezentacja stanu prac | `article/prezentacja_stan_prac.pptx`, 14 + 3 zapasowe slajdy (sek. 7) |
| Pomysł na artykuł ML | [`ml_paper.md`](ml_paper.md) — propozycja, zero wyników (sek. 4.2) |

---

## 2. Pytania do prof. Błasiak — kalibracja i warunek dla wariantu (d)

B1–B3 nie blokują decyzji z sek. 4.1 ani pisania, tylko domknięcie punktu pracy:
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

**B4. Jak silna jest pętla mossy cells → komórki ziarniste?** Od tego zależy, czy
zapłon sieci z E1‴ jest realistyczny: przy obecnych wagach `mc_active` zdarza się
w 2 na 30 przebiegów, przy wadze o połowę większej — do 40%, bez MC — nigdy
(sek. 3.4). To warunek dla wariantu (d) w sek. 4.1. Szukamy dowolnej liczby z
literatury lub danych: amplituda EPSP MC→GC, liczba MC na GC, częstotliwość MC in vivo.

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

## 4. Decyzje

### 4.1 ⛔ Jedna decyzja blokująca: czym jest teza pracy

Pierwotna teza („separacja ma optimum przy pośredniej aktywności, a hamowanie nią
steruje") jest obalona (sek. 3.3, 3.4), także w szerszym sweepie E1″. Następcę
trzeba wybrać z tego, co dane faktycznie podpierają.

| | teza | dowód, który mamy | koszt | główne ryzyko |
|---|---|---|---|---|
| **(a)** | metodologiczna: dekorelacja bez kontroli aktywności jest zwodnicza, a oczywiste kontrole same są pułapkami | **komplet** (sek. 3.3, 3.5, 3.6) | samo pisanie | praca metodyczna — niższy prestiż, ale wynik nowy |
| **(b)** | mossy cells jako motyw warunkowy separacji | Shapley — **zdominowany przez aktywność** (sek. 3.6) | — | **praktycznie odpada** |
| **(c)** | regulacja aktywności (kontroler E4/E5) | tylko pośredni: E2 (aktywność dominuje), zapłon z E1‴ | nowy moduł, miesiące | wynik kontrolera nieznany |
| **(d)** ⭐ | **padaczka: utrata mossy cells / hamowania** (K3) | maszyneria MC gotowa; zapłon sieci przy aktywnych MC (E1‴, eksploracyjnie, rzadki przy obecnych wagach) | **jeden–dwa sweepy** | częstość zapłonu zależy od nieznanej siły pętli MC — trzeba ją zakotwiczyć w danych |

**Wariant (d) przepisuje sam plan** — PLAN sek. 7.1, bramka G2: „H1 potwierdzona
ORAZ H2 potwierdzona. Jeśli nie — pivot na robustness/padaczkę z K3 jako wynikiem
głównym." H1 jest obalona, więc bramka jest otwarta. **Test E1‴ osłabił
uzasadnienie z E1″:** zjawisko jest (zapłon prawie całej sieci przy aktywnych MC,
któremu zapobiega hamowanie fazowe — dokładnie spór „dormant basket cell" vs
„irritable mossy cell"), ale przy obecnych wagach jest rzadkie i nie przeszło testu
zapisanego z góry. (d) stoi więc na planie (bramka G2), nie na naszym wyniku; bez
zakotwiczenia siły MC→GC w danych nie powiemy, czy zapłon jest realistyczny.
(b) odpada: „warunkowa rola MC" okazała się regulacją aktywności.

**Rekomendacja (zaktualizowana po E1‴): (a) jako pierwszy artykuł — ma komplet
dowodów; (d) dopiero po zakotwiczeniu siły pętli MC w danych** (pytanie do prof.
Błasiak, sek. 2). Jeśli dane wskażą siłę bliską λ ≥ 1.5, (d) ma gotowy punkt
startu (tabela E1‴); jeśli słabszą — zapłonu w modelu praktycznie nie ma. Mierzyć
zawsze przy wyrównanej aktywności — to lekcja z E2; i liczyć wynik per wzorzec —
to lekcja z E1″.

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

0. ~~Test potwierdzający dla E1″~~ — **zrobione (E1‴), nie przeszedł**; wyniki
   i kryterium w sek. 3.4. Następny krok w tym wątku zależy od siły pętli MC
   z danych, nie od kolejnego sweepu.
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
| `figures/fig1..fig6-*.png` | 6 figur artykułu |
| `figures/slides/*.png` | figury artykułu bez nagłówków „Figure N." + 4 figury jednopanelowe pod slajdy |
| `prezentacja_stan_prac.pptx` | prezentacja stanu prac (sek. 7) |
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

## 7. Prezentacja — slajd po slajdzie

`article/prezentacja_stan_prac.pptx`: 14 slajdów głównych (~22 min) + 3 zapasowe na
pytania. Każdy slajd ma notatki prelegenta. Figury po angielsku (spójnie
z artykułem), tekst po polsku. Pointa: slajd 8 (metodologia); slajd 10 pokazuje
jedyny efekt obwodu i to, że nie przeszedł testu potwierdzającego.

**1. Tytuł.** Tytuł i schemat obwodu. Do powiedzenia: model sieci spajkującej DG,
związany danymi patch-clamp; będzie o tym, co ustaliliśmy, co okazało się pułapką
pomiarową i jaka decyzja jest do podjęcia.

**2. W skrócie.** Trzy karty: *obalona* — H1 (sek. 3.3–3.4); *2 z 2* — oba naturalne
null-e zawodzą (sek. 3.5); *0 / 210* — bez mossy cells sieć nie zapala się nigdy; z nimi zapłon jest możliwy,
ale rzadki, a test potwierdzający nie przeszedł (sek. 3.4, E1‴). Na dole
odsyłacz do decyzji (slajd 13).

**3. Czym jest separacja wzorców** (`fig1-concept`). Lewo: dwa wzorce wejściowe
(czarne paski = komórki z silnym napędem; pokazane 80 z 200). Środek: częstotliwość
każdej komórki. Prawo: korelacja wejść 0.73 i wyjść 0.58, różnica +0.15. Jedna
symulacja domyślnej konfiguracji. Do powiedzenia: to definicja operacyjna całej
pracy — i ta liczba rośnie sama, gdy sieć cichnie.

**4. Model** (`fig2-circuit`). PP napędza GC i równolegle FS (FF); GC napędzają FS
(FB); FS hamują GC; HMC w pętli pobudzającej. Ramka: dwie osie hamowania. Do
powiedzenia: rozdzielenie tonicznego (`K_GC`) i fazowego (`W_FS_GC`) to sedno modelu.

**5. Punkt pracy jest zgodny z danymi** (`fig3-operating-point`). `K_GC` = hamowanie
toniczne, stały prąd odejmowany od każdej GC. (a) Niebieska linia: ile stałego napędu
potrzeba, żeby GC strzelała (`G_crit = 4 + K`); czerwona: średni napęd aktywnej GC,
8 mV (= 400 Hz × 4 mV × 5 ms, fluktuacje ±4 mV). Przy `K_GC = 10` próg 14 mV leży nad
średnią, więc odpalają tylko fluktuacje — stąd rzadki kod. (b) Ten sam `K` ustala
potencjał spoczynkowy; zielony pas = IQR z 42 GC Madara, szary pas = `K` zgodne z
danymi (0–13.6). Do powiedzenia: parametr, który robi z DG rzadki koder, daje też
spoczynek zgodny z pomiarem. Jeśli padnie pytanie: waga 4 mV jest dobrana, nie
zmierzona (panel a opisuje reżim, dowodem jest panel b), a dane ograniczają `K` do
zakresu, nie do jednej wartości. Szczegóły sek. 3.8.

**6. E1 — separacja rośnie, gdy sieć cichnie** (`slide-e1`). Szare punkty: 450
punktów siatki (separacja wobec frakcji aktywnych, oś log w %). Przerywane linie:
cztery progi odrzucania cichych punktów; gwiazdki: maksimum separacji przy każdym
progu. Do powiedzenia: każda gwiazdka siedzi przy swoim progu — gdyby istniało
biologiczne optimum, stałyby w jednym miejscu. Sek. 3.3.

**7. E1′ — hamowanie fazowe nic nie zmienia** (`slide-e1p`). Separacja wobec
hamowania fazowego, osobna linia dla każdego z 6 zadanych poziomów aktywności
(bisekcja po hamowaniu tonicznym, 733 punkty). Do powiedzenia: linie leżą na różnych
wysokościach (to robi aktywność), ale żadna nie rośnie z hamowaniem; nachylenie
−0.003, p = 0.60. Sek. 3.4.

**8. ⭐ Z czym w ogóle porównujemy obwód** (`fig5-nulls`). (a) korelacja wyjścia:
wejście 0.75, *random projection* 0.58, DG 0.39, *permuted DG output* 0.00 (oba
null-e objaśnione w sek. 3.1). (b) przewaga DG nad projekcją losową: obwód bez
motywów hamowania +0.094, z nimi +0.152. Do powiedzenia — pointa metodologiczna:
permutacja osiąga zero, bo niszczy informację (sufit); projekcja losowa z definicji
zachowuje korelację (trywialna podłoga); obejmują obwód z dwóch stron. A przewaga
nad projekcją to w ~60% sam próg spajkowania. Sek. 3.5.

**9. E2 — wkład motywów to głównie aktywność** (`slide-e2`). Trzy elementy obwodu:
FF (hamowanie wyprzedzające), FB (hamowanie zwrotne), MC (mossy cells, pętla
pobudzająca); każdy można wyłączyć, więc jest 8 wersji obwodu.
(a) Każda pomarańczowa kropka = jedna wersja (średnio po 36 zestawach wejść ×
5 seedów, `mc_active`, napęd ×1.0); szare punkty = pojedyncze pomiary. Oś x — ile
komórek ziarnistych strzela, oś y — separacja `r_in − r_out`. Wszystkie wersje leżą
na jednej malejącej linii (r = −0.97). (b) Wartość Shapleya = o ile średnio zmienia
się separacja, gdy element dołączamy, uśrednione po wszystkich kolejnościach
dołączania. Do powiedzenia: FF i FB „pomagają", bo wyciszają sieć; MC „szkodzi", bo
ją rozpędza (same MC: 94% aktywnych). Wkład mierzy więc wpływ na aktywność, nie
separację samą w sobie. Uczciwie: wcześniej pokazywałem tu „odporność na null" —
ta kontrola była pusta z konstrukcji. Interakcje i korekta projekcją losową: sek. 3.6.

**10. E1″ / E1‴ — zapłon sieci: jest, ale rzadki** (`fig6-runaway`). (a) Aktywność
wyrównana; oś x — hamowanie fazowe, oś y — odsetek przebiegów, w których jeden ze
wzorców zapalił prawie całą sieć; linie = siła pętli MC (λ = 0 bez MC, λ = 1 jak w
E1″). Bez MC zapłonów nie ma nigdy, przy λ = 1 są 2 na 30, przy λ = 1.5 do 40%; od
`W` = 3 — nigdy. (b) Bez wyrównywania aktywności, λ = 1: oś y — odsetek aktywnych
komórek; przy hamowaniu tonicznym zgodnym z danymi (`K` = 6, 10) bez hamowania
fazowego aktywne jest 100% komórek. Do powiedzenia: w E1″ wyglądało to na „szybsze
komórki" (~280 Hz) — to był artefakt miary mieszającej wzorce; test na nowych seedach
nie przeszedł kryterium zapisanego z góry. Zostaje zjawisko jakościowe, którego
częstość zależy od siły mossy cells — dlatego pytamy o nią prof. Błasiak. Sek. 3.4.

**11. 1A — odbiorca nie korzysta** (`slide-1a`). Dokładność klasyfikatora liniowego
dla czterech wejść. Miara niezależna od korelacji — i też nic: DG 0.885 wobec 0.940,
losowa projekcja remisuje z DG, bez hamowania lepiej. Sek. 3.7.

**12. Co upadło, co stoi, co jest nowe.** *Upadło:* optimum separacji, sterowanie
separacją przez hamowanie fazowe, mossy cells jako motyw separacji, pomoc dla
odbiorcy, „toniczne = ile, fazowe = jak szybko" (artefakt miary). *Stoi:* punkt
pracy zgodny z danymi; DG bije losową projekcję głównie dzięki progowi; z aktywnymi
MC możliwy zapłon sieci, któremu zapobiega hamowanie fazowe (eksploracyjnie).
*Metodologia:* oba null-e zawodzą; próg odrzucania przesuwa maksimum; retencja idzie
za rzadkością wejścia.

**13. Decyzja: czym jest teza pracy.** Cztery warianty; (d) wyróżniony. Do
powiedzenia: (d) przewidział sam plan (bramka G2), ale nasz własny wynik go nie
podpiera, dopóki nie znamy siły mossy cells; (b) odpada. Rekomendacja: najpierw (a),
(d) po zakotwiczeniu MC w danych. Sek. 4.1.

**14. Następne kroki.** Decyzja; siła mossy cells z danych (warunek dla (d)); pytania
do prof. Błasiak; bodźce Madara jako wejście; artykuły.

**15–17. Zapas.** Pełna mapa reżimów E1; pełna siatka E1″ (separacja wobec hamowania
fazowego w 8 panelach — płasko wszędzie poza 20% przy aktywnych MC); profile wkładów
motywów E2.

**Pytania, które padną:**

1. *„Czemu nie odrzucić cichych punktów?"* — Maksimum przenosi się dokładnie na
   próg, przy każdym progu (slajd 6).
2. *„Czemu permutacja nie jest dobrą kontrolą?"* — Jej wynik zbiega do `r_in`, więc
   nadwyżka nad nią to `−r_out` (slajd 8); a w E2 jej odjęcie nie może niczego
   zmienić (slajd 9).
3. *„Czy zapłon nie jest artefaktem ręcznie dobranych wag MC?"* — Jego częstość
   tak: zależy od siły pętli MC (slajd 10a). Samo zjawisko i to, że hamowanie fazowe
   mu zapobiega, powtarza się przy każdej sile, przy której występuje.
