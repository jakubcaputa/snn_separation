# Changes — usprawnienia narzędzia separacji wzorców DG

Dziennik zmian po spotkaniu z promotor (2026-06-09). Plan podzielony na 4 priorytety:
**1) częstotliwości → 2) parametry K → 3) obwód/obserwowalność → 4) mossy cells.**

> ⚠️ **Jest nowsza runda.** Wszystko poniżej dotyczy rundy 1 (czerwiec 2026).
> Runda 2 (wrzesień 2026, kalibracja pod dane Madara) — **patrz sekcja
> „RUNDA 2" na końcu pliku**. Koryguje ona m.in. wniosek o doborze K
> i ujawnia, że 74% hamowania GC jest toniczne, a nie synaptyczne.

Plik docelowy wszystkich usprawnień: **`interactive_dg.py`** (Streamlit).
Skrypty pomocnicze (`freq_audit.py`, `dg_module3_inh_comparison.py`, …) to
poligon doświadczalny — ich wnioski wędrują do narzędzia interaktywnego.

---

# 📋 STRESZCZENIE DLA PROMOTOR (do wytłumaczenia)

**W jednym zdaniu:** obniżyliśmy zbyt wysoką częstotliwość wejścia (żeby GC kodowały
rzadko, jak w prawdziwym DG), matematycznie wyjaśniliśmy parametr K, i przebudowaliśmy
narzędzie tak, by było widać firing każdego typu komórek oraz to, co pobudza, a co hamuje GC.

### Mapowanie pytań ze spotkania → co zrobione → wniosek

| Pytanie/uwaga promotor | Co zrobiliśmy | Wniosek / wynik |
|---|---|---|
| Czy częstotliwość wejścia (600 Hz) nie jest za duża? | Audyt `freq_audit.py`: zmierzyliśmy output GC dla różnych wejść | 600 Hz dawało GC ~16.6 Hz (za dużo). **Obniżone do 400 Hz → GC ~6 Hz** (rzadkie kodowanie ✓). Sam „lumping" 40×10 Hz=400 Hz jest poprawny (superpozycja Poissona) |
| 10 Hz to wszystko co komórka rejestruje? | Rozdzielono pojęcia: **per-włókno** (~10 Hz, fizjologiczne) vs **zagregowane** (suma 40 włókien) | Pojedyncze włókno PP ~10 Hz; do GC wpada suma 40 włókien. Oba tryby w aplikacji, teraz spójne |
| Czym są współczynniki K? | Analiza bifurkacji `bifurcation_K.py` | **K = toniczne hamowanie GABA; podnosi próg pobudzenia: G_crit = 4 + K.** Potwierdzone i teorią, i symulacją (co do 0.1 mV) |
| Wkład każdej synapsy w napięcie? | Nowy panel „budżet napięcia" — rozbicie na PP, HMC, FS | Widać ile mV **dokłada** pobudzenie (PP, HMC) i ile **zabiera** hamowanie (FS) w czasie |
| Większy nacisk na rolę neuronów hamujących i schemat | Metryki firing per typ, żywy schemat (grubość strzałek = przepływ), budżet napięcia | Widać że FS strzela w gamma (~52 Hz), dociska GC; po wyłączeniu hamowania GC robią się gęstsze |
| Rola mossy cells (MC/HMC)? | Diagnoza + suwaki + panel „Rola Mossy Cells" | **Domyślnie MC milczą** (0 Hz): rzadkie GC nie dają im dość napędu (próg 14 mV). Można je ożywić suwakiem `W GC→HMC` |
| PP→GC nie mnożymy (bez depresji TM) | Udokumentowane | Przy 600/400 Hz aggregate depresja TM byłaby przesterowana; PP→GC zostaje prostą synapsą AMPA |

### Co pokazać w aplikacji (tryb 🌐 Populacja DG)
1. **Metryki na górze** — firing GC / FS / HMC z flagą czy są w zakresie fizjologicznym.
2. **Schemat obwodu** — grubość strzałek pokazuje, które połączenia realnie pracują.
3. **Panel „Co pobudza, a co hamuje GC?"** — zielone=PP, pomarańcz=HMC, fiolet=hamowanie FS.
4. **Demo roli hamowania:** odznacz Feedforward/Feedback → znika fioletowe pole, GC gęstsze, R_out rośnie.
5. **Demo roli MC:** podnieś `W GC→HMC` do ~14 → HMC zaczynają strzelać, rośnie pomarańczowe pole.

### Nowe / zmienione pliki
- **`interactive_dg.py`** (główne narzędzie) — rekalibracja częstotliwości, 2 kanały
  pobudzenia GC, budżet napięcia, żywy schemat, metryki per typ, suwaki MC, naprawa osi rastrów.
- **`dg_params.py`** (NOWY) — jedno źródło prawdy dla częstotliwości wejścia.
- **`freq_audit.py`** (NOWY) — audyt: dowód, że 400 Hz jest właściwe (figura `freq_audit.png`).
- **`bifurcation_K.py`** (NOWY) — wyjaśnienie K = 4 + G_crit (figura `bifurcation_K.png`).
- **`dg_module3_inh_comparison.py`** — rekalibracja wejścia 600→400 Hz.

> Szczegóły techniczne każdej zmiany — w sekcjach „Priorytet 1–4" poniżej.

---

## Priorytet 1 — Częstotliwości sygnału

### ✅ Krok 1 — Audyt częstotliwości (`freq_audit.py`, NOWY)
Skrypt diagnostyczny odpowiadający na pytanie „czy 600 Hz aggregate to za dużo?".
Mierzy (nic nie zmieniając w modelach):
- **A) Superpozycja Poissona** — 40 włókien × 15 Hz ≡ 1 proces 600 Hz (tożsamość
  matematyczna; sam lumping NIE jest błędem).
- **B) Stan ustalony g_ex** = r·W·τ vs próg bifurkacji G_crit ≈ 14 mV (K=10).
- **C) Empiryczny output GC** (prawdziwy neuron Izhikevich) dla zakresu wejść.
- **D) Niespójność** między skryptami (single_neuron 10 Hz/wł., reszta 15 Hz/wł.).

**Kluczowy wynik:**

| r_agg wejście | output GC | ocena |
|---|---|---|
| 300 Hz | 2.6 Hz | ✓ fizjologiczne |
| **400 Hz** | **5.9 Hz** | ✓ **cel DG** |
| 600 Hz (poprzednie) | 16.6 Hz | ✗ za wysoko |

**Wniosek:** błąd nie leży w „600 Hz na wejściu", lecz w tym, że taki napęd
wypycha output GC poza reżim rzadkiego kodowania DG (aktywne GC ~1–10 Hz).
Wyjście: `freq_audit.png`.

### ✅ Krok 2 — Rekalibracja w `interactive_dg.py`
- `R_EFF_HIGH`: **600 → 400 Hz** (= 40 włókien × 10 Hz). Output GC ~6 Hz ✓.
- `R_EFF_LOW` pozostaje 40 Hz (= 40 włókien × 1 Hz).
- Efekt uboczny: tryb zagregowany jest teraz **spójny** z domyślnym trybem
  per-fiber (10 / 1 Hz na włókno) — koniec niespójności z audytu (sekcja D).

### ✅ Krok 3 — Wspólny moduł parametrów wejścia (`dg_params.py`, NOWY)
Jedyne źródło prawdy dla reżimu częstotliwości wejścia PP — koniec niespójności
10 vs 15 Hz/włókno. Definiuje: `N_FIBERS_PER_GC=40`, `R_FIBER_ACTIVE=10`,
`R_FIBER_BG=1`, pochodne `R_EFF_HIGH=400`, `R_EFF_LOW=40`, `W_PP_GC_IZH=4`.
Podłączone do:
- `interactive_dg.py` — import stałych + domyślne wartości suwaków per-fiber,
- `dg_module3_inh_comparison.py` — import `R_EFF_HIGH/LOW` (rekalibracja 600→400).

Skrypty LIF (`single_neuron_patsep_brian2.py` — już 10 Hz; `dg_microcircuit_brian2.py`
— LIF z W=6) mają osobną kalibrację wag i NIE są zmieniane, by nie zepsuć ich
dostrojenia; ich reżim wejścia opisuje komentarz / kanon w `dg_params.py`.

---

## Priorytet 2 — Czym jest parametr K_tonic (`bifurcation_K.py`, NOWY)

K_tonic to **toniczny prąd hamujący** (tło GABA-A) w równaniu Izhikevicza:
wchodzi jako „− K·mV/ms" i podnosi rheobazę (próg pobudzenia).

**Wynik analityczny** (wyprowadzony w nagłówku skryptu): punkty stałe spełniają
`0.04v² + (5−b)v + (140 + g_ex − K) = 0`; bifurkacja siodło-węzeł przy zerowym
wyróżniku daje próg pobudzenia w jednostkach g_ex:

> **G_crit(K) = (5−b)²/0.16 − 140 + K = 4 + K**  (dla b=0.2)

| K | G_crit analit. | G_crit zmierzony (Brian2) |
|---|---|---|
| 0 | 4 mV | 4.0 mV |
| 5 (FS) | 9 mV | 9.0 mV |
| 10 (GC, HMC) | 14 mV | 14.0 mV |
| 15 | 19 mV | 19.0 mV |

**Empiria dokładnie potwierdza teorię.** Stąd: GC/HMC (K=10) są trudniej
pobudliwe (G_crit=14) niż FS (K=5, G_crit=9) — dlatego FS odpalają łatwo
(interneurony), a GC pozostają rzadkie. Kanoniczny napęd 400 Hz daje g_ex≈8 mV,
poniżej G_crit_GC=14 → GC w reżimie fluktuacyjnym → separacja wzorców.

Figura `bifurcation_K.png`: A) krzywe f–I przesuwane przez K, B) G_crit(K)
liniowy z punktami pracy GC/FS, C) płaszczyzna fazowa (nullcliny) poniżej/powyżej
bifurkacji.

---

## Priorytet 3 — Obserwowalność (podbity na życzenie: „pokazać co się dzieje")

Wszystko w `interactive_dg.py`, tryb Populacja DG.

### Metryki dla KAŻDEGO typu komórek (z flagą zakresu fizjologicznego)
- FR GC + „rzadkie ✓ / za gęste ✗" (cel 1–10 Hz),
- FR FS + „gamma ✓ / za wolno / za szybko" (cel 30–100 Hz),
- FR HMC + „aktywne / ~ciche".

### Panel „Co pobudza, a co hamuje GC? (budżet napięcia)" — z ROZBICIEM NA ŹRÓDŁA
GC ma teraz DWA kanały pobudzające (`_izh_eqs(..., second_ex_tau=)`):
- `g_ex`  = PP→GC,
- `g_ex2` = HMC→GC,
oraz `g_in` = FS→GC (hamowanie). `simulate_brian` nagrywa wszystkie trzy dla
reprezentatywnych aktywnych/nieaktywnych GC. Wykres warstwowy pokazuje wprost:
- **zielone** = ile mV dokłada PP→GC,
- **pomarańczowe** = ile dokłada re-ekscytacja HMC→GC (cienkie ⟹ MC nie działają),
- **fioletowe** = ile zabiera hamowanie FS→GC,
- czarna linia = napęd netto vs próg G_crit; pod spodem V_m aktywne vs nieaktywne GC.

### Żywy schemat obwodu
- **Każde połączenie to osobna strzałka jednokierunkowa** (→ pobudza, ⊣ hamuje);
  pary dwukierunkowe (GC↔FS, GC↔HMC) rysowane jako **dwie osobne strzałki** na
  równoległych pasach (offset prostopadły) — koniec mylących „dwugłowych" strzałek.
- **Grubość ORAZ liczba [mV]** na każdej strzałce = przepływ ładunku **ZMIERZONY
  z symulacji** (nie ze wzoru): średnia przewodności dostarczonej przez daną
  ścieżkę w czasie. Aby rozdzielić źródła, FS ma teraz 3 osobne kanały pobudzające
  (g_ex=PP→FS, g_ex2=GC→FS, g_ex3=HMC→FS); `StateMonitor` zapisuje przewodności na
  GC/FS/HMC, a `simulate_brian` zwraca `flow_meas`. Ścieżki→GC liczone po aktywnych
  GC (spójnie z budżetem napięcia), →FS/HMC po całej populacji. Znak +/− = pobudza/hamuje.
- Usunięto etykiety „AMPA"/„GABA-A" ze schematu (zostały nazwy połączeń + wartości).

Zmiany techniczne: `simulate_brian()` zwraca `budget` z kluczami
`gpp_act / ghmc_act / gin_act / v_act / v_inact`; wyniki przechowują `weights`,
`r_drive`, `K_GC/K_FS/K_HMC`.

---

## Priorytet 4 — Mossy Cells (HMC)

- **Diagnoza (uwidoczniona):** przy domyślnych ustawieniach HMC są prawie ciche —
  rzadkie GC (~6 Hz) dają napęd GC→HMC dużo poniżej progu G_crit=4+K_HMC=14.
  Widać to teraz wprost: cienka szara strzałka HMC→GC na schemacie + cienkie
  pomarańczowe pole w budżecie napięcia + panel „Rola Mossy Cells".
- **Ablacja:** checkbox „Hilar Mossy Cells (HMC)" włącza/wyłącza całą pętlę MC —
  porównanie R_out z/bez HMC dostępne od ręki.
- **Sterowalność:** wagi MC wystawione jako suwaki (były zaszyte na sztywno):
  `W GC→HMC` (napęd MC), `W HMC→FS` (MC wzmacnia hamowanie), `W HMC→GC`
  (re-ekscytacja). Zwiększenie `W GC→HMC` (≈10–16) lub zmniejszenie `K_HMC`
  aktywuje MC — wtedy rośnie pomarańczowe pole (re-ekscytacja) i FR FS (wzmocnione
  hamowanie). Panel „Rola Mossy Cells" interpretuje stan liczbowo.

> **Do review w Streamlicie:** sprawdź scenariusze — (a) domyślny (MC ciche),
> (b) `W GC→HMC=14` (MC aktywne, rośnie pomarańczowe pole), (c) HMC off vs on
> i porównaj R_out. To pokazuje netto rolę MC: re-ekscytacja (HMC→GC) kontra
> wzmocnienie hamowania (HMC→FS→GC).

---

## Poprawki UX rastrów (po pierwszym review)

- **Oś Y rastrów była myląca:** N_patterns wzorców rysowanych z offsetem pionowym
  ⟹ oś sięgała N_patterns × N_neuronów (np. GC: 3×(200+6)=618), choć etykieta brzmiała
  „GC neuron". Teraz oś Y pokazuje **pasma wzorców** (Wz.1/Wz.2/Wz.3, każde 0–N) z
  liniami rozdzielającymi; tytuł podaje N. To samo dla FS i HMC.
- **Pusty panel HMC** dostaje adnotację „HMC nieaktywne (0 Hz)", by nie mylił.

## Diagnoza ciszy HMC (zweryfikowana liczbowo, ustawienia domyślne)

Reprodukcja domyślnego biegu (N_GC=200, P_active=0.25, R_in=0.75, pełny obwód):
`FR GC ≈ 0.75 Hz` (bardzo rzadko — pełne hamowanie FS@52 Hz dociska GC),
`FR FS ≈ 52 Hz` (gamma ✓), **`FR HMC = 0.0 Hz` (0 spików)**.
Powód: HMC napędzane tylko przez GC→HMC; przy tak rzadkich GC
`g_ex_HMC ≈ 0.5–0.7 mV` ≪ próg `G_crit = 4+K_HMC = 14 mV` (ok. 20× za mało).
Aktywacja: ↑`W GC→HMC` (≈14–16), ↓`K_HMC`, lub (fizjologicznie) dodać PP→HMC.

---

# RUNDA 2 (2026-09) — kalibracja pod dane Madara

Kontekst: wymiana maili z prof. Błasiak po rundzie 1. Cztery pytania z jej strony
(V_reset i parametry błony, spiking probability, czym dokładnie jest K_tonic,
czy K_tonic + FS→GC to podwójne hamowanie) wymusiły przejście od „ustaw suwaki
i zobacz" do **jawnej specyfikacji punktu pracy**.

## Co zmierzono (odpowiedzi na pytania z maila)

### Bilans hamowania wg typu komórki — to był ślepy punkt narzędzia

Wkłady do `dv/dt` w tych samych jednostkach, konfiguracja domyślna:

| komórka | pobudzenie | hamowanie FAZOWE | hamowanie TONICZNE (K) | udział tonicznego |
|---|---|---|---|---|
| **GC** | PP 2.43 + HMC 0.00 | FS→GC **3.59** | **10.0** | **74%** |
| **FS** | PP 7.32 + GC 1.85 | **0.0 — kanał nie istnieje** | 5.0 | 100% |
| **HMC** | GC 0.20 | 0.0 (`W_FS_HMC=0`) | 10.0 | 100% |

Dwa wnioski, które trzeba mieć z tyłu głowy przy każdej analizie hamowania:
1. **Trzy czwarte hamowania GC jest toniczne**, nie synaptyczne. Wcześniejsze
   wnioski o „hamowaniu tworzącym separację" mogą w dużej części dotyczyć
   składnika tonicznego, a nie obwodu FS. Ile powinno być — pytanie otwarte.
2. **FS i HMC nie mają w modelu żadnego hamowania synaptycznego.** To nie jest
   kwestia doboru wag: kanał `g_in` nie istnieje w ich równaniach. Brakuje
   w szczególności wzajemnego hamowania FS→FS.

### P(AP | puls) — nie da się ustawić samą wagą

Protokół pulsowy jak u Madara (dyskretne pulsy, okno 15 ms):

- **Bez źródła zmienności krzywa jest SKOKOWA** (0.00 → 0.99). Deterministyczny
  neuron albo zawsze odpala, albo nigdy — zakresu Madara 20–80% nie da się trafić.
- Z tłem 40 Hz i `K_GC=10`: P(AP) ≈ 0 aż do wagi 16 mV, przy 20 mV dopiero 0.24.
  **Obecny punkt pracy modelu nie odpowiada protokołowi Madara** — nie o korektę
  chodzi, tylko o czynnik pięciu (`W PP→GC` = 4 mV vs potrzebne ~22 mV).

### b ustawia SUMĘ napięć, K ich ODSTĘP

Punkty stałe to pierwiastki `0.04v² + (5−b)v + (140−K) = 0`, więc:

> `V_rest + V_th_eff = −(5−b)/0.04` — **zależy wyłącznie od b, nie od K**

Przy domyślnym `b = 0.2` suma jest zablokowana na **−120 mV**:

| cel (V_rest, V_th) | wymagane b | wymagane K | uwaga |
|---|---|---|---|
| (−70, −50) | 0.2 | **0** | osiągalne bez zmiany modelu |
| (−70, −47.5) | 0.3 | 7 | wymaga zmiany b |
| (−70, −45) | 0.4 | **14** | K **rośnie** powyżej obecnych 10 |

To koryguje wcześniejszą intuicję „obniżyć K". Kierunek zależy od tego, który
koniec zakresu podanego przez prof. Błasiak weźmiemy — przy −45 jest odwrotny.

### K_GC pełni TRZY role naraz

Jeden parametr ustala jednocześnie próg efektywny, potencjał spoczynkowy **i**
cały budżet hamowania tonicznego. Nie da się ich wybrać niezależnie: podanie
docelowej proporcji toniczne:fazowe wymusza K, a więc wymusza też próg i spoczynek.
Przy punkcie spełniającym właściwości błony (`K_GC = 0`) hamowanie toniczne znika
zupełnie — odwrotność obecnych 74%.

*To jest argument za rozdzieleniem w modelu prądu tonicznego od offsetu
pobudliwości, ale to zmiana modelu neuronu, nie kalibracja — decyzja do podjęcia.*

## Co dodano do kodu

### Zawodność synaptyczna („spike-wise noise" Madara)
`DGConfig`: osiem pól `P_REL_*` (per ścieżka) + `delay_jitter_ms`, metoda
`with_reliability(gc=, fs=, hmc=)` ustawiająca zawodność **wg typu komórki
docelowej** — tak, jak formułuje to biologia.

Mechanizm nie jest przebraniem wagi: przerzedzenie Poissona z prawdopodobieństwem
`p` przy kompensacji wagą `W/p` daje wariancję `g_ex ∝ 1/p`, czyli **większe
fluktuacje przy tym samym średnim napędzie**. Zmierzone: FR aktywnych GC rośnie
**3.12 → 5.46 → 9.22 Hz** dla `p_rel` = 1.0 → 0.5 → 0.25. To właśnie ta wariancja
wytwarza stopniowane P(AP).

⚠️ Efektywny napęd = `rate × W × p_rel × τ` — `p_rel` i wagę trzeba kalibrować RAZEM.

### Harness kalibracyjny (`experiments/dg_core/calibrate.py`, NOWY)
Odwraca kierunek: podajesz `OperatingPoint` (specyfikację), kod dobiera parametry
i **raportuje, czego nie da się spełnić**. Nie jest to ślepy optymalizator:

| krok | metoda |
|---|---|
| (b, K) ← właściwości błony | wzór zamknięty |
| `W PP→GC` ← docelowe P(AP\|puls) | bisekcja 1D |
| `W FS→GC` ← docelowy bilans toniczne:fazowe | bisekcja 1D |
| częstotliwości w pełnym obwodzie | pomiar, nie strojenie |

Nierozstrzygnięte pola (`tonic_share=None`) to jawne znaki zapytania — metoda
`open_questions()` wypisuje je przy każdym przebiegu.

```bash
cd experiments
python -m dg_core.calibrate --preset madar     # (−70, −50), osiągalne przy b=0.2
python -m dg_core.calibrate --preset strict    # (−70, −45), wymaga zmiany b
python -m dg_core.calibrate --tonic-share 0.5  # gdy proporcja będzie znana
```

### Panel budżetu napięcia — K_tonic wreszcie widoczne
Do rundy 1 panel rysował PP, HMC→GC i FS→GC, ale **K_tonic nie występowało tam
jako hamowanie** — siedziało schowane w podniesionej linii `G_crit = 4 + K`.
Dlatego dominacja składnika tonicznego była niewidoczna aż do pomiaru.

Teraz: czwarte, turkusowe pasmo (−K) układane pod fazowym, napęd netto liczony
jako `PP + HMC − FS − K`, a linia progu stoi na **stałych 4 mV**. Gdy kręcisz
`K_GC`, rośnie pasmo tonicznego i opada czarna linia — zamiast przesuwać się próg.
Pod spodem tabela „Bilans hamowania" z udziałem procentowym per typ komórki.

### Panel kalibracji P(AP)
Protokół pulsowy w narzędziu: wykres P(AP) względem wagi pulsu, z pasmem 20–80%
i pozycją obecnego `W PP→GC`. Gdy żadna waga nie trafia w pasmo, panel mówi wprost,
że brakuje źródła zmienności, i wskazuje, który suwak ruszyć.

## GŁÓWNY WYNIK: specyfikacja jest wewnętrznie sprzeczna

```
V_rest GC          -70.0 mV    →  -70.0 mV    OK
V_th_eff GC        -50.0 mV    →  -50.0 mV    OK
P(AP | puls)       0.45        →   0.46       OK
W PP→GC            (wynikowe)  →   7.13 mV
FR GC (we wzorcu)  2–6 Hz      →  21.74 Hz    NIE
FR FS              10–40 Hz    →  181.92 Hz   NIE
napęd ustalony     < 4.0 mV    →  14.3 mV     NIE
```

Właściwości błony i P(AP) trafiają idealnie, częstotliwości rozjeżdżają się
o rząd wielkości. Przyczyna jest policzalna: **wagę dobiera się protokołem
pulsowym przy tle 40 Hz, a używa w sieci przy napędzie 400 Hz.** Dziesięciokrotna
różnica reżimu wejścia — jedna waga nie obsłuży obu.

To nie jest usterka, tylko **pytanie „in vitro czy in vivo" przeliczone na liczby**:
rzadka stymulacja u Madara i gęsty napęd PP to dwa różne punkty pracy i trzeba
wybrać, który jest warunkiem kontrolnym.

## Regresja — stare wyniki są nietknięte

| sprawdzenie | wynik |
|---|---|
| hash spajków `dg_core` vs baza sprzed rundy 2 | **identyczne bit w bit** |
| `pytest tests/` (17 testów) | 17/17 |
| kierunek 4, preset quick (576 symulacji) | FF 49.9% / FB 50.1% / MC 0.0%, dekorelacja +0.067 → +0.143 — zgodne z dokumentacją |

Wszystkie nowe parametry mają wartości domyślne neutralne (`p_rel = 1.0`,
`delay_jitter_ms = 0.0`, `b_gc = B_GC`), a `_on_pre` przy `p_rel >= 1.0` bierze
osobną gałąź, która **nie zużywa ani jednej liczby losowej**. Dlatego domyślna
konfiguracja jest odtwarzalna co do spajka.

## Pytania otwarte (blokują domknięcie kalibracji)

1. **Jaki jest realny udział prądu tonicznego w całkowitym hamowaniu GC?**
   (model daje 74%, ale to wartość odziedziczona, nie wybrana)
2. **Czy ~46 Hz to fizjologiczna częstotliwość bazowa FS?** (w modelu FS nie mają
   żadnego hamowania synaptycznego, więc wartość jest prawdopodobnie zawyżona)
3. **Do którego reżimu wejścia kalibrujemy** — rzadka stymulacja in vitro (Madar)
   czy gęsty napęd PP? Bez tego każda kalibracja trafi w jedno kryterium kosztem drugiego.
4. Czy rozdzielić w modelu prąd toniczny od offsetu pobudliwości (dziś to jeden
   parametr pełniący trzy role)?

---

## Do zrobienia (kolejne kroki)

**Zablokowane do odpowiedzi prof. Błasiak** (pytania 1–3 powyżej):
- domknięcie punktu pracy: `K` per typ komórki, `tonic_share`, wybór reżimu wejścia.

**Odblokowane, można robić teraz:**
- **Dopasowanie do CCIV** (`fit_neurons.py`, do napisania) — rampy prądowe
  z `dataset/`, per typ komórki. Dostępne: HMC 26 nagrań, GC+CA3 66.
  ⚠️ **FS nie mają CCIV w ogóle** (folder `GCandFS_yo_P10Hz_1`: 64 nagrania, zero ramp),
  więc parametry FS trzeba wziąć z literatury albo estymować ze spike trainów.
- **Kanał FS→FS** jako parametr z domyślnym zerem (wzorzec `W_FS_HMC`).
- **Oś hamowania w siatce** (`K_GC` × `W_FS_GC`) — obecna siatka ma tylko osie
  statystyki wejścia, więc odpowiada na pytanie o ATRYBUCJĘ, ale **nie o okno
  funkcjonalne** (H1). To dwa różne eksperymenty, dziś zlepione w jeden.

**Backlog (bez zmian):** TM na PP→GC, Hodgkin-Huxley, multi-trial R_out,
twardy test pasma gamma FS, fizjologiczny napęd MC (bezpośrednie PP→HMC),
wykres bifurkacji K w `interactive_dg.py`.

---

## Uwagi techniczne
- Konsola Windows (cp1250) nie obsługuje Unicode — `freq_audit.py` wymusza UTF-8 na stdout.
- Środowisko: `snn_sep_venv` (Brian2 2.10.1, numpy 2.4, matplotlib 3.10; bez scipy → `np.corrcoef`).
