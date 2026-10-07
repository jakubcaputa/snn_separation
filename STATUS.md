# Status — stan prac, wyniki, co dalej

*Aktualizacja: 2026-10-08.*

> ### Gdzie zacząć (2026-10-08)
>
> **Trzy ekrany, w tej kolejności:**
> 1. **§3.0** — wszystkie eksperymenty i wyniki w jednej tabeli, z indeksem figur.
> 2. **§3.2c** — null-e. Metodologiczny rdzeń i najmocniejszy kandydat na wynik
>    publikowalny. Figura `article/figures/fig5-nulls.png`.
> 3. **§4.1** — **jedyna decyzja blokująca**: czym jest teza pracy. Cztery
>    warianty w tabeli, z rekomendacją.
>
> **Stan w jednym zdaniu.** Teza „separacja ma optimum przy pośredniej
> aktywności, a hamowanie fazowe tym steruje" jest obalona i nie da się jej
> uratować. Obraz NIE jest jednak czysto negatywny: podział zasług między
> motywami jest realny i odporny na kontrolę (§3.1), a najciekawszy wynik jest
> metodologiczny — **oba naturalne null-e zawodzą, w przeciwne strony** (§3.2c).
>
> Obliczenia są skończone; nic nie czeka w kolejce i **nic nie zostało do
> policzenia, co zmieniłoby obraz**. `PLAN_BADAWCZY.md` jest świadomie NIE
> przepisany — czeka na decyzję z §4.1 i ma na wejściu ramkę mówiącą, że jest
> dokumentem historycznym.

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
| **Draft artykułu** | `article/` — tekst + **5** figur objaśniających, **do przeczytania** (§6) |
| **Pomysł na artykuł ML** | [`ml_paper.md`](ml_paper.md) — rzadkość jako trzeci czynnik; propozycja, zero wyników (§4.1b) |

---

## 2. Co blokuje KALIBRACJĘ — czeka na prof. Błasiak

> Uwaga: to NIE jest blokada całej pracy. Blokadą jest decyzja z §4.1;
> poniższe trzy pytania blokują domknięcie punktu pracy modelu.

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

### 3.0 Wszystko na jednym ekranie

| # | eksperyment | pytanie | odpowiedź | figura |
|---|---|---|---|---|
| **E1** | mapa reżimów (§3.2) | czy separacja ma optimum przy pośredniej aktywności? | **NIE.** `dec` rośnie monotonicznie ku ciszy; maksimum jedzie za progiem maski (0.02→0.025, 0.20→0.200) | `article/figures/fig4-findings.png` (a)<br>`e1_regime_map/results/regime_map_full.png` |
| **E1′** | dopasowana aktywność (§3.2b) | czy hamowanie FAZOWE coś kupuje, gdy cisza jest wyrównana? | **NIE.** Płasko na całym `W_FS_GC` 0–5 (rozstęp 0.024 przy SEM 0.027) | `fig4-findings.png` (b)<br>`matched_activity_full.png` |
| **—** | null-e (§3.2c) | z czym w ogóle porównujemy obwód? | **Oba null-e zawodzą, w przeciwne strony.** Permutacyjny = sufit (`r_out`→0), k-WTA = prawie-izometria (`r_out` = 78% `r_in`) | **`fig5-nulls.png`** ← kluczowa |
| **E2** | atrybucja motywów (§3.1) | który motyw hamowania niesie separację? | **FF 152%, FB 120%, MC −172% z silnymi synergiami.** Odporne na null | `e2_motif_attribution/results/fig1..fig4*.png` |
| **1A** | odczyt downstream (§3.3) | czy klasyfikator czyta DG lepiej niż wejście? | **NIE.** 0.885 vs 0.940; losowy kod rzadki remisuje z DG | `fig4-findings.png` (d) |
| **—** | dane Madara (§3.4) | czy punkt pracy jest związany danymi? | **TAK.** `K_GC=10` → `V_rest` −78.7 mV, wewnątrz IQR [−81,−70] | `fig3-operating-point.png` |

**Jedno zdanie podsumowania.** Obwód nie separuje w sensie absolutnym i nie pomaga
odbiorcy; przewaga nad losowym kodem rzadkim istnieje (+0.19), ale w ~61% pochodzi
z samego progu spajkowania, a nie z architektury hamowania. Natomiast **podział
zasług między motywami jest realny i odporny na kontrolę** — i to jest jedyny
kawałek, na którym da się budować wynik pozytywny.

**Figury „do tłumaczenia" vs „do analizy".** `article/figures/fig1`–`fig5` są
proste, po angielsku, jedna myśl na panel — do pokazania komuś. Figury w
`experiments/*/results/` są gęste i analityczne — do pracy własnej.


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

✅ **Zweryfikowane nullem (2026-10-06, §3.2c):** Shapley policzony na nadwyżce
ponad null daje te same wkłady co na surowej dekorelacji (φ_FF +0.1999 vs +0.1998,
φ_MC −0.2245 vs −0.2257). Atrybucja motywów NIE jest artefaktem rzadkości —
te liczby można cytować.

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

### 3.2b E1′ — separacja przy DOPASOWANEJ aktywności

> **Co z tego zostaje (wersja po korekcie):** przy wyrównanej aktywności
> **hamowanie fazowe `W_FS_GC` nie kupuje nic** na całym zakresie 0–5 — i to jest
> trwały wynik tej sekcji. Natomiast liczba −0.389 „nadwyżki ponad null" NIE
> znaczy tego, co pierwotnie napisałem: null permutacyjny okazał się równy `r_in`,
> więc ta nadwyżka to po prostu `−r_out` (wyprowadzenie: §3.2c pkt 1).
> Sformułowanie „obwód separuje gorzej niż null o dopasowanej rzadkości" jest
> **wycofane**; poprzedni nagłówek sekcji brzmiał „Wynik negatywny, mocny" i był
> nadinterpretacją.

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

### 3.2c ⭐ NULL-E: z czym naprawdę porównujemy obwód

**To jest metodologiczny rdzeń całej pracy i najmocniejszy kandydat na wynik
publikowalny.** Figura: `article/figures/fig5-nulls.png`.

Przeliczenie E2 z nullami (job 3334385, 4 shardy × ~17 min) wymusiło korektę
interpretacji §3.2b. **Dec nie zmieniło się ani o jotę** względem przebiegu bez
nulli (max |różnica| = 0.0e+00 na 1080 zadaniach mimo innego shardowania), więc
zmienia się wyłącznie odczyt, nie liczby.

**1. Null permutacyjny mierzy `r_in`, a nie poziom szansy dla danej rzadkości.**
Przetasowanie wektora częstotliwości po komórkach niszczy CAŁĄ odpowiedniość
wzorzec–komórka, więc korelacja wyjścia nulla dąży do zera, a zatem

```
dec_null_shuffle ≈ r_in                    (zmierzone: 0.5687 vs r_in 0.5682,
                                            max |różnica| 0.045)
nadwyżka = dec − dec_null = (r_in − r_out) − r_in = −r_out
```

Zmierzone: średnie `−r_out` = −0.4181, średnia nadwyżka = −0.4186. To ta sama
liczba. **Nadwyżka ponad null permutacyjny nie niesie żadnej informacji ponad
samo `r_out`.**

⚠️ **Dlatego sformułowanie z §3.2b („obwód separuje gorzej niż null o dopasowanej
rzadkości") jest za mocne i trzeba je wycofać.** Prawdziwa treść tamtego pomiaru
jest słabsza: `r_out > 0`, czyli wyjście zachowuje część korelacji wejścia.
Null permutacyjny osiąga `r_out = 0` przez **wyrzucenie całej informacji**
o wzorcu, więc jest nieosiągalnym sufitem, a nie poziomem szansy. Liczba
−0.389 ± 0.245 z §3.2b pozostaje poprawna; błędna była jej interpretacja.

**2. Null k-WTA jest tym, który faktycznie coś porównuje** — buduje rzadki kod
z tego samego wejścia, o dopasowanej liczbie aktywnych. Na nim nadwyżka jest
**DODATNIA** (E1′: +0.32 przy 2% aktywnych → +0.08 przy 30%; E2: +0.118).
Czyli DG dekoreluje **lepiej** niż ogólny losowy kod rzadki o tej samej rzadkości.

**3. Atrybucja motywów (E2) przeżywa kontrolę — i to z dobrego powodu.**
Null jest praktycznie STAŁY po koalicjach (rozstęp 0.0051 przy rozstępie `dec`
0.3774), bo zależy od `r_in`, które lezja nie zmienia. Shapley jest niewrażliwy
na stałą, więc wkłady są niemal identyczne:

| | φ_FF | φ_FB | φ_MC | FF×MC | FB×MC |
|---|---|---|---|---|---|
| na `dec` | +0.1998 | +0.1572 | −0.2257 | +0.2227 | +0.2096 |
| na nadwyżce | +0.1999 | +0.1555 | −0.2245 | +0.2217 | +0.2085 |

**Wniosek: wyniki E2 z §3.1 NIE były obciążone tym confounderem** i można je
cytować. Zastrzeżenie dopisane do §3.1 i do draftu artykułu jest zdjęte.

**4. ⚠️ Drugi null też NIE jest poziomem szansy — i to osłabia jedyny wynik
dodatni.** Skoro null permutacyjny okazał się zdegenerowany, ta sama ostrożność
należy się k-WTA. Zmierzone (E1′, przy `r_in` = 0.748):

| | `r_out` | % `r_in` | czym to jest |
|---|---|---|---|
| null permutacyjny | 0.001 | 0% | **sufit** — niszczy całą informację |
| **DG** | **0.390** | **52%** | |
| null k-WTA | 0.580 | 78% | **prawie-izometria** — projekcja losowa z definicji ZACHOWUJE korelację |

Dwa null-e **obejmują** DG z obu stron, ale żaden nie jest poziomem szansy.
„DG bije losowy kod rzadki o +0.19" jest prawdą, ale słabszą, niż brzmi: losowa
projekcja gaussowska jest z konstrukcji kiepskim dekorelatorem (Johnson–
Lindenstrauss), więc bicie jej nie jest wysoką poprzeczką. Przewaga maleje
monotonicznie z aktywnością (+0.324 przy 2% aktywnych → +0.078 przy 30%),
czyli w tę samą stronę co confound rzadkości.

**5. Skąd bierze się ta przewaga: z nieliniowości, nie z obwodu hamowania.**
Rozkład na koalicjach E2 (reżim `mc_active`, nadwyżka nad k-WTA):

| obwód | nadwyżka nad k-WTA |
|---|---|
| **bez żadnego hamowania** | **+0.094** |
| pełny obwód (FF+FB+MC) | +0.152 |
| różnica = wkład hamowania | +0.059 |

Czyli ~62% przewagi daje sam próg/spajkowanie, zanim w ogóle włączymy hamowanie.
⚠️ I te +0.059 **nie jest kontrolowane aktywnością** (frakcja aktywnych GC spada
0.149 → 0.129 między tymi warunkami), więc może być tym samym efektem rzadkości.
Pomiar, który JEST kontrolowany aktywnością — §3.2b pkt 2 — mówi, że hamowanie
fazowe nie daje nic. **Spójna lektura: DG dekoreluje lepiej niż losowy kod rzadki
dzięki nieliniowości progowej, a nie dzięki charakterystycznej architekturze
hamowania DG.** Zgodne z 1A, gdzie usunięcie hamowania POPRAWIAŁO odczyt
(dg_noinh 0.935 vs dg 0.885).

**Czego to NIE unieważnia.** Confound z §3.2 (maksimum `dec` jedzie za progiem
maski) był pokazany niezależnie, testem przesuwania progu, i nadal obowiązuje.
Płaskość `W_FS_GC` przy wyrównanej aktywności (§3.2b pkt 2) też — to pomiar na
`dec`, nie na nadwyżce.

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

## 4. Decyzje do podjęcia

Obliczenia są skończone. **Nie ma już nic do policzenia, co zmieniłoby obraz** —
oba ostatnie wnioski (§3.2c pkt 4 i 5) wzięły się z ponownej analizy danych, które
już leżą na dysku. Wąskim gardłem jest decyzja z §4.1.

### 4.1 ⛔ JEDNA decyzja blokująca: czym jest teza pracy

Projekt startował z tezą „DG separuje wzorce, a hamowanie tym steruje". Ta teza
jest **obalona** (§3.2, §3.2b). Nie ma domyślnego następcy — trzeba go wybrać
z tego, co dane faktycznie podpierają.

| | teza | dowód, który JUŻ mamy | koszt | główne ryzyko |
|---|---|---|---|---|
| **(a)** | metodologiczna: dekorelacja bez kontroli jest zwodnicza, a oczywiste kontrole same są pułapkami | **komplet** (§3.2, §3.2c) | zero liczenia, samo pisanie | praca metodyczna — niższy prestiż, ale wynik jest nowy i nietrywialny |
| **(b)** | mossy cells jako motyw warunkowy | Shapley odporny na null (§3.1) | niski | **osłabiony** — efekt mały, nie kontrolowany aktywnością; recenzent to wytknie |
| **(c)** | regulacja zamiast separacji (kontroler E4/E5) | **brak** — nie zbudowane | najwyższy: nowy moduł `control.py` | wynik nieznany, miesiące pracy |
| **(d)** ⭐ | **padaczka: utrata mossy cells** (K3) | maszyneria MC gotowa i przetestowana | **jeden sweep** | — |

**Wariant (d) przepisuje sam plan.** `PLAN_BADAWCZY.md` §7.1, **bramka G2**:
„H1 potwierdzona ORAZ H2 potwierdzona na pełnej siatce. **Jeśli nie — pivot na
robustness/padaczkę z K3 jako wynikiem głównym.**" H1 jest obalona od 2026-09-21,
więc **bramka G2 jest otwarta od trzech tygodni i nikt jej nie przeszedł
formalnie.** K3 (`PLAN_BADAWCZY.md` §4): `N_HMC` × {1.0, 0.75, 0.5, 0.25, 0} przy
stałym in-degree, rozstrzyga spór „dormant basket cell" vs „irritable mossy cell",
mierząc jednocześnie napęd FS i separację.

**Dlaczego (d) jest teraz najmocniejszy:** nie zakłada, że DG dobrze separuje —
pyta, co się dzieje przy utracie MC; MC to **jedyny motyw o dużych efektach**
w naszych danych (φ_MC −0.22, synergie +0.22), czyli jedyna oś, na której model
faktycznie coś robi; pytanie jest kliniczne i ma żywy spór w literaturze, więc
wynik jest publikowalny niezależnie od znaku.

**Rekomendacja:** **(d) jako teza nośna + (a) jako osobny, krótszy artykuł
metodologiczny.** Materiał na (a) jest kompletny i leży odłogiem. Nie robić (c)
przed (d) — kontroler to miesiące pod pytanie, którego nikt nie zadał.

⚠️ Czego NIE da się już obronić w żadnym wariancie: „separacja ma optimum przy
pośredniej aktywności" (§3.2) i „hamowanie fazowe steruje separacją" (§3.2b).

### 4.1b Osobna, NIEZALEŻNA ścieżka: artykuł ML

[`ml_paper.md`](ml_paper.md) — propozycja wykorzystania mechanizmu DG
w uczeniu maszynowym: **rzadkość jako trzeci czynnik** (zamiast modulacji tempa
uczenia) oraz **null-e o dopasowanej rzadkości jako protokół ewaluacji**.

**Nie koliduje z decyzją z §4.1** — to inna publikacja, inna literatura i inne
repo wykonawcze (`snn_stdp_vs_surrogate_gradient`, gdzie ~80% harnessu
treningowego jest gotowe: R-STDP per-sample, k-WTA, IP, MNIST/CIFAR/N-MNIST).
⚠️ Zero wyników ML na dziś — to propozycja, nie przepakowanie.

### 4.2 Decyzje drugiego rzędu — dopiero PO 4.1

1. **Przeformułować H1 w `PLAN_BADAWCZY.md`.** Plik jest świadomie nieprzepisany,
   oznaczony jako historyczny. Przepisywanie przed 4.1 to robota do wyrzucenia.
2. **Który artykuł pierwszy** — (a) jest gotowy do pisania od zaraz, (d) wymaga
   sweepu. Można równolegle.
3. **Czy `article_draft.tex` zostaje osobnym artykułem o narzędziu**, czy wtapia
   się we wstęp do (d). Draft jest napisany tak, że obie drogi są otwarte (§6).

### 4.3 Zadania niezależne od decyzji — można robić od zaraz

1. **Skompilować draft na Overleafie.** Nigdy nie był kompilowany — na Athenie nie
   ma LaTeX-a. Sprawdzony tylko statycznie.
2. **`io_madar.py`** — odczyt bodźców z `dataset/…/Protocols/` i podanie ich jako
   wejścia PP do `dg_core.circuit.simulate()`. Jeden dzień pracy, a zmienia status
   projektu z „model z syntetycznymi wzorcami" na „model napędzany tymi samymi
   bodźcami, co eksperyment" — odblokowuje walidacje V2, V3 i V4 naraz.
   **Wartościowe w KAŻDYM wariancie z 4.1.**
3. **Krzywe f–I z CCIV.** Protokół prądowy JEST odzyskiwalny z adnotacji Axographu
   (`Pulse #1 … -100, 20` → start −100 pA, krok 20 pA, 30 epizodów, onset 100 ms,
   szerokość 500 ms). Dostępne: HMC 26 plików, GC+CA3 66. **FS nie mają ani jednego
   CCIV** — ich parametry tylko z adnotacji (4 komórki, §3.4).
4. **Przypomnieć się prof. Błasiakowi** (§2, mail z 2026-09-11, ~4 tygodnie bez
   odpowiedzi). Konkretny pretekst: rozbieżność τ_m z §3.4 — dane dają ~3 ms dla
   GC, nie 10–50 ms; pytanie, czy to różnica definicji (Rm wejściowe vs błonowe).
5. **Kalibracja siły FS→FS** do docelowej częstotliwości FS — czeka na B2,
   maszyneria bisekcji jest w `calibrate.py`.
6. **Suwak `W FS→HMC` + panel obserwowalności w `interactive_dg.py`** — wisząca
   rekomendacja; przy wariancie (d) staje się wprost demonstracją tezy.

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

## 6. Draft artykułu — co w nim jest i czego świadomie nie ma

`article/article_draft.tex` (ang., Overleaf-ready) + `article/figures/*.png`
+ `article/make_article_figures.py` (figury są ODTWARZALNE, nie wklejone).

**Zakres ustalony 2026-10-05:** artykuł opisuje **aplikację zbudowaną dla
neurobiologów** i **mechanizm separacji wzorców**. NIE przesądza tezy pracy —
§4 pkt 2 zostaje otwarte. Dlatego wyniki z §3 są tam podane jako demonstracje
tego, co warsztat rozstrzyga, a nie jako teza nośna.

| sekcja draftu | treść |
|---|---|
| §1 Introduction | po co DG, po co model, czego brakuje (narzędzie dla eksperymentatora) |
| §2 Mechanism | definicja operacyjna separacji + **pułapka pomiarowa** (Fig. 1) |
| §3 Model | równania, parametry, kanon PP, `G_crit = 4 + K`, dane Madara (Fig. 2, 3) |
| §4 Application | `interactive_dg.py`, warstwa headless, kalibracja przez bisekcję |
| §5 Experiments | E1, E1′, E2, 1A jako demonstracje (Fig. 4) |
| §6 Outlook | co ustalone, **co otwarte**, plany (kontroler, bodźce Madara, ekspansja) |

**Pięć figur objaśniających** (`article/figures/`) — jedna figura = jedna myśl,
po angielsku, do tłumaczenia komuś, a nie do analizy:

1. `fig1-concept` — czym JEST separacja wzorców (wejście → wyjście → spadek korelacji)
2. `fig2-circuit` — obwód i dwie osie hamowania (toniczna vs fazowa)
3. `fig3-operating-point` — dlaczego GC są rzadkie + jak dane Madara przypinają `K_GC`
4. `fig4-findings` — po jednym panelu na eksperyment, jedna myśl na panel
5. **`fig5-nulls`** — z czym naprawdę porównujemy obwód: oba null-e obejmują DG
   zamiast go benchmarkować, a przewaga nad losowym kodem rzadkim w ~61% pochodzi
   z progu spajkowania, nie z hamowania. **Najważniejsza figura w komplecie.**

⚠️ **W drafcie są jawne `\todo{}`** — m.in. afiliacje, rozbieżność τ_m (§3.4)
i brakujące pozycje bibliografii. To są miejsca do Twojej decyzji, nie
przeoczenia. ✅ Zastrzeżenie o Shapleyu na surowej dekorelacji **zostało zdjęte**
po przeliczeniu z nullami (§3.2c).

⚠️ Na Athenie **nie ma LaTeX-a**, więc draft nie został skompilowany lokalnie —
sprawdzony statycznie (balans środowisk i nawiasów, brak pustych jednostek
`\SI`, nazwy figur bez podkreślników). Pierwsza kompilacja na Overleafie.

---

## 7. Dziennik porządków

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
