# Plan badawczy — DG, separacja wzorców i adaptacyjna regulacja aktywności

*Aktualizacja: 2026-09-14. Scalenie dawnych `doktorat_plan.md` i `PLAN_PUBLIKACJI.md`.*

**Ten plik odpowiada na dwa pytania: JAKIE SĄ HIPOTEZY i JAK JE TESTUJEMY.**
Zmierzone liczby, stan prac i blokady są w [STATUS.md](STATUS.md) — tutaj są do nich
odnośniki, nie kopie.

| § | zawartość |
|---|---|
| 1 | pytanie badawcze, luka, **hipotezy H1–H5** |
| 2 | fundament — trzy wyniki, na których stoi plan |
| 3 | **eksperymenty E1–E7**, architektura L0–L3, walidacja wewnętrzna, **cztery pułapki** |
| 4 | knockouty in silico K1–K7 |
| 5 | bateria metryk |
| 6 | walidacja biologiczna V1–V5 |
| 7 | oś czasu, plan figur, FAIR |
| 8 | ryzyka i pozycjonowanie wobec literatury |
| 9 | otwarte kwestie, role we współpracy |

---

## 1. Pytanie badawcze i hipotezy

### 1.1 Cel nadrzędny

Nie dwa niezależne wątki „biologia + ML", tylko **jeden projekt, w którym ML jest
narzędziem do odpowiedzi na pytanie neurobiologiczne, a SNN pomostem między nimi**:

> W jaki sposób biologicznie inspirowane mechanizmy regulacji aktywności
> neuronalnej wpływają na separację reprezentacji i efektywność przetwarzania
> informacji — i czy można wykorzystać te mechanizmy do projektowania
> adaptacyjnych SNN?

**Hipoteza robocza:** istnieje zakres aktywności neuronalnej, w którym separacja
reprezentacji jest optymalna, a mechanizmy homeostatyczne i hamujące mogą
automatycznie utrzymywać sieć w tym zakresie.

Jeden ciąg eksperymentalny:

```
biologicznie inspirowany mechanizm → dynamika aktywności →
separacja / informacja → model ML → adaptacyjny mechanizm w SNN
```

Kandydat publikacyjny: **PLOS Computational Biology** (pogranicze comp neuro i ML;
Madar et al. 2019 ukazał się tam, więc redakcja zna kontekst i metryki R/NDP/SF).

### 1.2 Luka biologiczna, nie obliczeniowa

Separacja wzorców w DG jest opisywana jako **statyczna własność architektury**:
ekspansja (10⁶ GC), rzadkie kodowanie, silne hamowanie. Trzy fakty tego nie domykają:

1. **Statystyka wejścia jest zmienna.** Kora śródwęchowa dostarcza wejście
   o zmiennym tempie, korelacji i burstiness; Madar pokazał, że separacja u tego
   samego neuronu zależy od skali czasowej i statystyki bodźca. Sieć strojona na
   jeden reżim nie ma powodu działać w innym.
2. **Sam obwód nie jest stabilny.** Pętla `GC→HMC→GC` bez hamulca nie ma reżimu
   pośredniego: MC są albo nieistotne, albo uciekają, a obwód zaczyna *korelować*
   wzorce. Biologia ma ten hamulec (interneurony hilusa hamują MC — Scharfman 2016).
3. **Regulacja bywa uszkodzona.** Utrata mossy cells jest znakiem rozpoznawczym
   padaczki skroniowej; spór „dormant basket cell" (Sloviter) vs „irritable mossy
   cell" dotyczy utraty REGULACJI, nie separacji per se.

**Luka:** nie wiemy, **jaka wielkość jest w DG regulowana** i **czy jej regulacja
czyni separację odporną**. Kandydaci: średnia częstotliwość GC, frakcja aktywnych GC
(rzadkość), lokalny bilans E/I. To trzy różne hipotezy o trzech różnych przewidywaniach.

Kierunek: przestać badać „czy DG separuje" (na to odpowiedziano), zacząć badać
**„co utrzymuje DG w reżimie, w którym separuje"**.

### 1.3 Hipotezy H1–H5 (falsyfikowalne, z warunkiem obalenia)

| ID | hipoteza | obala ją |
|---|---|---|
| **H1** | Separacja jest **niemonotoniczną** funkcją poziomu aktywności populacji GC — istnieje optimum przy pośredniej frakcji aktywnych komórek. | monotoniczny wzrost separacji przy spadku aktywności aż do reżimu ciszy (po odrzuceniu artefaktu pustego wektora) |
| **H2** | Hamowanie MC (`FS→HMC`) **tworzy** reżim pośredni — bez niego okno funkcjonalne znika (bistabilność: cisza albo runaway). | istnienie szerokiego reżimu pośredniego przy `W_FS_HMC = 0` w pełnej siatce, nie tylko w punkcie domyślnym |
| **H3** | Wielkością regulowaną, która najlepiej utrzymuje separację przy zmiennej statystyce wejścia, jest **frakcja aktywnych GC**, a nie średnia częstotliwość ani lokalny E/I. | kontroler na FR lub na E/I utrzymuje separację równie dobrze lub lepiej w teście uogólnienia poza reżim strojenia |
| **H4** | Prosta reguła homeostatyczna (plastyczność wewnętrzna progu + iSTDP na `FS→GC`) samodzielnie odnajduje punkt pracy zidentyfikowany offline i przywraca separację po dezinhibicji oraz po utracie 50% MC. | kontroler zbiega do punktu istotnie różnego od optimum offline albo nie odzyskuje separacji w żadnym z warunków |
| **H5** | Regulacja **przesuwa separację między kodami**: przy niskiej aktywności dominuje separacja wzorcowa (NDP), przy wysokiej częstotliwościowa (SF). | brak dysocjacji NDP/SF wzdłuż osi aktywności — w modelu I w danych Madara |

**Podział ciężaru:** H1 i H2 mają wyniki wstępne (§2). **H3–H5 są nowe i to one
niosą publikację** — a ich eksperymenty (E4, E5) jeszcze nie istnieją.

| hipoteza | eksperyment | kod |
|---|---|---|
| H1, H2 | E1 — mapa reżimów | `experiments/e1_regime_map/` ✅ |
| „który motyw tworzy okno" | E2 — atrybucja | `experiments/e2_motif_attribution/` ✅ |
| **H3, H4** | E4 — kontroler, E5 — uogólnienie | **niezbudowane** |
| H5 | wymaga metryk NDP/SF (§5.2) | niezbudowane |

---

## 2. Fundament — trzy wyniki, na których stoi plan

Liczby i warunki pomiaru: [STATUS.md](STATUS.md) §3. Tutaj tylko to, **co z nich
wynika dla hipotez**.

**2a. Hamulec FS→HMC tworzy reżim pośredni (→ H2).** Bez niego pętla GC→HMC→GC jest
czysto pobudzająca: mossy cells albo nie robią nic, albo uciekają, a obwód zaczyna
*korelować* wzorce zamiast je separować. Z hamulcem separacja przebija obwód
domyślny o kilkadziesiąt procent. To jest dosłownie „regulacja hamująca utrzymuje
sieć w funkcjonalnym reżimie, poza którym separacja się załamuje" — czyli teza
nośna pracy, pokazana na jednym motywie. Stąd `W_FS_HMC` jest **zmienną hipotezy
H2**, a nie parametrem technicznym.

**2b. Wynik negatywny 1A uzasadnia zmianę metryk.** „DG poprawia klasyfikację
liniową" zostało sprawdzone i obalone, razem z hipotezą ratunkową o krótkim oknie
odczytu. Separacja nie poprawia liniowej rozróżnialności, gdy wejście i tak jest
liniowo separowalne — DG kupuje coś innego (odporność odbiorcy o ograniczonej
pojemności, odporność na interferencję). Stąd przejście z samej dekorelacji na
baterię miar informacyjnych (§5) i oś **separacja↔informacja** jako właściwą
przestrzeń wyników.

**2c. Separacja rośnie z rozmiarem sieci.** Przy stałym in-degree i stałej frakcji
aktywnych GC separacja rośnie monotonicznie z N_GC — zgodnie z teorią kodowania
ekspansyjnego. Sam w sobie wynik nieodkrywczy, ale ustawia E6: pytanie brzmi nie
„czy rośnie", tylko **czy okno funkcjonalne przesuwa się z rozmiarem sieci**.

---

## 3. Plan eksperymentów E1–E7

### 3.1 Tabela zbiorcza

| # | eksperyment | plan | rozmiar | testuje | gdzie |
|---|---|---|---|---|---|
| **E1** | **Mapa reżimów** — separacja vs poziom aktywności | osie: napęd PP (×0.25…×4), `W_FS_GC`, `K_GC`, `R_in` ∈ {0.5…0.975}, `W_FS_HMC` ∈ {0,1,2,5}, reżim MC; 10 seedów sieci × 10 zestawów wzorców | ~30–50 tys. sym. | **H1, H2** | `e1_regime_map/` ✅ |
| **E2** | **Atrybucja motywów** — 2³ lezje FF/FB/MC + Shapley, pełna bateria metryk | ta sama sieć i te same wzorce we wszystkich lezjach | ~20 tys. | który motyw tworzy okno | `e2_motif_attribution/` ✅ |
| **E3** | **Sobol/LHS dla surrogatu ML** | sekwencja Sobola, NIE gęsta siatka (§3.4 leakage) | 20 tys. + 5 tys. spoza hipersześcianu | indeksy Sobola, sloppiness | niezbudowane |
| **E4** | **Kontroler** — 3 mechanizmy × 3 wielkości kontrolowane × ON/OFF | 60 s adaptacji → perturbacja → 60 s odzysku | ~3 tys. długich przebiegów | **H3, H4** ← nośne | niezbudowane |
| **E5** | **Uogólnienie kontrolera** — strojony w jednym reżimie, testowany w innych | strojenie 10 Hz / R=0.75; test 30 Hz, burstiness, inne `R_in` | ~2 tys. | **H3** (kluczowy test) | niezbudowane |
| **E6** | **Skalowanie** — `DGConfig.scaled(N)`, N_GC ∈ {200,400,800,2000,5000} | stały in-degree | ~1 tys. (drogie) | czy okno przesuwa się z rozmiarem | niezbudowane |
| **E7** | **Walidacja na bodźcach Madara** — wejście = rzeczywiste protokoły | patrz §6 | ~5 tys. | ground truth | niezbudowane |

Koszt: ~80–100 tys. symulacji × ~1.3 s; z E4 (długie przebiegi) i E6 (duże sieci)
realistycznie kilka tysięcy rdzenio-godzin. Na Aresie nieistotne — budżet
obliczeniowy nie jest ograniczeniem.

**E1 i E2 to dwa różne eksperymenty, nie warianty jednego.** E1 zamraża statystykę
wejścia i zmienia **siłę hamowania** (`K_GC` toniczne × `W_FS_GC` fazowe), a główną
osią wykresu jest **zmierzona** frakcja aktywnych GC — bo twierdzenie H1 dotyczy
aktywności, a nie parametrów. E2 zmienia statystykę wejścia i nie ma **ani jednej
osi hamowania**, więc nie może odpowiedzieć na pytanie, ile hamowania jest
optymalne. Stąd osobne E1; wcześniej tej osi w repo w ogóle nie było.

⚠️ E1 ma wynik wstępny, który **nie potwierdza H1** ([STATUS.md](STATUS.md) §3.2).
Zanim ruszy reszta planu, trzeba rozstrzygnąć: artefakt maski, za wąska siatka, czy
realne obalenie hipotezy nośnej.

### 3.2 Architektura obliczeniowa — cztery poziomy

Zasada nadrzędna: **jedno źródło prawdy modelu** = `experiments/dg_core/`.
Nie przepisujemy do NEST (to reset i drugie źródło prawdy) — NEST najwyżej jako
walidacja krzyżowa na końcu.

**L0 — pojedynczy neuron, ograniczony danymi.** Izhikevich (a, b, c, d, K)
dopasowywany per typ komórki (GC/FS/HMC/CA3) do nagrań `CCIV`. Metoda: różnicowa
ewolucja / CMA-ES, koszt = krzywa f–I + rheobase + adaptacja ISI + kształt AP
(największa waga na f–I). Produkt: `dg_core/fit_neurons.py` + rozkłady parametrów →
**heterogeniczna populacja** zamiast identycznych klonów. *Największy skok
wiarygodności modelu przy najmniejszym nakładzie.*

**L1 — obwód DG.** Istniejący `dg_core/circuit.py` (GC/FS/HMC, rozdzielone kanały
`g_ex`/`g_ex2`/`g_ex3`/`g_in` — obserwowalność za darmo). Rozszerzenia:
`W_FS_HMC` jako pełnoprawna oś; wejście PP z **rzeczywistych protokołów Madara**
(tryb `pp_source='madar'`); opcjonalna depresja Tsodyks–Markram na `PP→GC`
(jako parametr, nie domyślna zmiana modelu).

**L2 — kontroler adaptacyjny (rdzeń nowości).** Trzy mechanizmy, każdy włączalny
osobno, wszystkie wolne względem dynamiki obwodu (τ ≈ 1–10 s):

- **IP (intrinsic plasticity):** `dK_i/dt = η_K (r_i − ρ₀)`. W tym modelu `K` *jest*
  tonicznym GABA-A (`G_crit = 4 + K`), więc to biologicznie przesunięcie rheobase /
  tonic GABA, a nie abstrakcyjny próg.
- **iSTDP (Vogels–Sprekeler)** na `FS→GC`: `Δw = η(pre·post − α)`, `α = 2ρ₀τ_STDP`
  — biologicznie umocowany punkt nastawy E/I.
- **SS (synaptic scaling)** multiplikatywne na `W_PP_GC` — kontrola napędu.

Trzy warianty **wielkości kontrolowanej** (test H3): `r_i` = częstotliwość neuronu,
`a_i` = binarna aktywność (→ frakcja aktywnych), `b_i = g_ex/(g_ex+g_in)` = lokalny
bilans E/I. **To jest eksperyment, nie detal implementacyjny.**

**L3 — surrogat ML (narzędzie, nie wynik).** Gradient boosting / GP: parametry +
statystyki aktywności → metryki separacji i informacji. Trzy zastosowania:
(a) globalna analiza wrażliwości (indeksy Sobola); (b) przyspieszony **inverse
design** („maksymalna separacja przy budżecie spajków"); (c) **analiza sloppiness**
— czy 10-wymiarowa przestrzeń parametrów redukuje się do 2 sztywnych kombinacji
(przewidywanie: „poziom aktywności" i „netto E/I"). Punkt (c) jest wynikiem
biologicznym, nie ML-owym: mówi, *co* obwód musi regulować, żeby reszta przestała
mieć znaczenie.

### 3.3 Dwa reżimy mossy cells — obowiązkowe w każdym sweepie

Przy domyślnych wagach MC są sparametryzowane do nieistotności i nie strzelają
([STATUS.md](STATUS.md) §5), więc sweep przeprowadzony tylko w tym punkcie
odpowiada na pytanie postawione z góry. Każdy sweep leci w dwóch reżimach:

| reżim | drive (`W_GC_HMC`) | gain | brake (`W_FS_HMC`) | co reprezentuje |
|---|---|---|---|---|
| `mc_inert` | 1 | ×1 | 0 | domyślny `interactive_dg.py` — MC martwe |
| `mc_active` | 16 | ×20 | 2 | MC żywe i ustabilizowane |

**Różnica map dominacji między reżimami sama jest wynikiem:** ile „dominacji FF/FB"
bierze się z biologii, a ile z doboru wag. Wartości `drive`/`gain` w `mc_active` są
dziś arbitralne — procedura ich zakotwiczenia: §6.2 V5.

### 3.4 Walidacja wewnętrzna i statystyka

Sekcja, na której recenzenci PLOS CB koncentrują ogień.

1. **Leakage przez sąsiedztwo w siatce.** Losowe CV na gęstej siatce zawyża R²
   surrogatu (sąsiednie punkty to niemal duplikaty). Protokół: **blokowe CV
   w przestrzeni parametrów** + osobny **zbiór ekstrapolacyjny poza hipersześcianem
   treningowym**. Raportujemy oba R² — różnica sama jest informacją.
2. **Leakage przez seed sieci.** Ten sam seed łączności nie może być w treningu
   i w teście → **GroupKFold po seedzie**.
3. **Maska ważności.** Punkt siatki wchodzi do analizy tylko gdy frakcja aktywnych
   GC ∈ [0.005, 0.5] ORAZ `std(rates) > 0`. Poza maską `R_out` jest *nieokreślone*,
   nie zerowe. Każdy panel figury nosi obok panel z FR/aktywnością. To operacyjna
   postać pułapki 3 (§3.5).
4. **Statystyka:** wielkości efektu z **95% CI z bootstrapu po seedach**, nie same
   p-wartości; model mieszany (seed sieci i zestaw wzorców jako efekty losowe), bo
   próby nie są niezależne; korekcja **BH-FDR** przy porównaniach po siatce.
5. **Model zerowy** dla każdej metryki: (a) losowa sieć o dopasowanej rzadkości,
   (b) permutowane etykiety wzorców, (c) sieć bez hamowania. Bez tych trzech żaden
   wynik separacji nie jest raportowany.
6. **Preregistracja wewnętrzna** w `analysis_plan.md`: metryka pierwszorzędowa
   (propozycja: NDP przy binie 100 ms) i kryteria H1–H5 zapisane przed
   uruchomieniem pełnego E1. Data commita = dowód. Tanie, a bardzo dobrze wygląda
   w Methods.

### 3.5 ⚠️ Cztery pułapki modelu (obowiązują w KAŻDYM nowym sweepie)

Każda z nich już raz cicho zepsuła wynik. Podwójnie ważne przy generowaniu datasetu
dla ML (E3): model wytrenowany na artefaktach nauczy się artefaktów, a potem inverse
design zoptymalizuje pod artefakt.

1. **Skalowanie: `DGConfig.scaled(N)`, nigdy `N_GC=` wprost.** `DGConfig(N_GC=800)`
   cicho zabija obwód: wyjście PUSTE (0% aktywnych GC), a dekorelacja pokazuje
   +0.77, bo korelacja pustego wektora wynosi 0 — wynik-widmo. Skalować trzeba
   naraz proporcje populacji GC:FS:HMC **i** prawdopodobieństwa połączeń odwrotnie
   do rozmiaru populacji źródłowej (stały in-degree). `scaled()` robi jedno i drugie.
   Do CI: linter wykrywający gołe `N_GC=` w skryptach sweepów.
2. **MC przy domyślnych wagach są martwe** — każdy sweep w dwóch reżimach
   `mc_inert`/`mc_active` (§3.3), inaczej wniosek o roli MC dotyczy obwodu bez nich.
3. **Separacja czy wyciszenie?** Dekorelacja przy FR→0 jest artefaktem, nie
   obliczeniem. Każda analiza ma maskę ważności i panel kontrolny FR / frakcji
   aktywnych GC (progi: §3.4 pkt 3).
4. **`K_GC` pełni TRZY role naraz** — ustala próg efektywny, potencjał spoczynkowy
   **i** cały budżet hamowania tonicznego. Nie da się ich wybrać niezależnie, bo
   `b` ustawia sumę `V_rest + V_th_eff`, a `K` ich odstęp ([STATUS.md](STATUS.md)
   §5). Każde zdanie „zwiększyliśmy hamowanie, podnosząc K" jest jednocześnie
   zdaniem „zmieniliśmy właściwości błony", i recenzent to zobaczy. Przy
   raportowaniu manipulacji na K **zawsze podawać wynikowe (V_rest, V_th_eff)**.

---

## 4. Knockouty in silico K1–K7

Standard PLOS: perturbacja pokazuje mechanizm, nie tylko korelację.

| # | knockout | implementacja | przewidywanie |
|---|---|---|---|
| **K1** | lezje motywów FF/FB/MC (pełny 2³) | `cfg.with_motifs()` ✅ | Shapley: FB dominuje w `mc_inert`, MC warunkowo dominujący w `mc_active` (wstępnie potwierdzone) |
| **K2** | **utrata hamulca MC:** `W_FS_HMC → 0` | ✅ | zanik reżimu pośredniego → bistabilność (H2) |
| **K3** | **stopniowa utrata mossy cells** (padaczka skroniowa) | `N_HMC` × {1.0, 0.75, 0.5, 0.25, 0}, stały in-degree | rozstrzyga „dormant basket cell" vs „irritable mossy cell": mierzymy napęd FS (`g_ex3`) i separację równocześnie |
| **K4** | **symulowana gabazyna:** (a) tylko fazowa `W_FS_GC×(1−α)`, (b) tylko toniczna `K_GC×(1−α)`, (c) obie | nowy parametr `gaba_block` | dysocjacja toniczne/fazowe GABA-A; wersja (c) porównywana z danymi przed/po GZN (§6.2 V4) |
| **K5** | **pobudliwość GC** (proxy neurogenezy): obniżone `K_GC` dla 5–20% GC | `K_GC` per-neuron | młode, pobudliwe GC: poprawiają czy pogarszają separację? (spór w literaturze) |
| **K6** | **knockouty kontrolera:** IP/iSTDP/SS off | L2 | czy któryś mechanizm sam wystarcza (H4) |
| **K7** | **perturbacje wejścia:** skok tempa ×3, powolny dryf, utrata 30% włókien PP | tryb bodźca | odporność: czas odzysku, przeregulowanie, błąd ustalony |

Wszystkie knockouty na **tej samej sieci i tych samych wzorcach**
(deterministyczny `make_connectivity(seed)`) — zaimplementowane i jest to warunek
poprawności Shapleya.

**Dlaczego Shapley, a nie naiwne on/off:** FF i FB dzielą wspólną drogę wyjściową
`FS→GC`, więc ich efekty nie są addytywne — naiwne odejmowanie przypisałoby tę samą
separację dwa razy. Shapley jako jedyny podział spełnia
Σφ_i = v(pełny obwód) − v(brak hamowania), czyli zdanie „FF odpowiada za X%
separacji" jest dosłownie prawdziwe.

---

## 5. Bateria metryk

### 5.1 Zaimplementowane (`dg_core/metrics.py`, funkcja `activity_battery()`)

Liczone dla populacji GC per próba, uśredniane po wzorcach; w NPZ z siatki lezji
każda metryka ma kształt `[zadanie × koalicja]`, więc od razu służy jako
cecha/target dla ML. Konwencja: metryka nieokreślona = **NaN**, nie 0 — „brak
danych" nie udaje wyniku; agregacja przez `nan_mean()`.

**Dynamika spike trains** (na surowych czasach spajków):

- **CV(ISI)** — σ/μ odstępów międzyspajkowych, średnia po neuronach z ≥3 spajkami.
  ~1 = Poisson, <1 = regularny zegar, >1 = burstiness. Mówi, *jak* neuron strzela
  przy danym FR — dwa reżimy o tym samym FR mogą mieć inną regularność.
- **Fano factor** — wariancja/średnia liczby spajków w oknach 50 ms. 1 = Poisson.
  ⚠️ Niestacjonarność (transjent startowy) ZAWYŻA Fano — porównywać tylko między
  warunkami o tym samym T i binie, nie jako wartość absolutną.
- **Indeks synchronii χ** (Golomb–Rinzel) — na binach 5 ms, tylko po aktywnych
  neuronach. 0 = asynchronicznie, →1 = pełna synchronizacja. Tu powinien być
  widoczny reżim runaway MC; nadmierna synchronizacja to jedna z granic
  funkcjonalnego reżimu.
- **Precyzja czasowa** — średnia i SD latencji pierwszego spajku. Małe SD = kod
  latencyjny możliwy (istotne dla low-latency SNN).

**Rozkład aktywności po populacji** (na wektorze częstotliwości):

- **Entropia aktywności** — znormalizowana entropia Shannona p_i = r_i/Σr;
  1 = aktywność rozłożona równo, →0 = skupiona w garstce jednostek. Dopełnia
  rzadkość Trevesa–Rollsa (inna czułość na ogony rozkładu).

**Informacja:**

- **MI wejście→wyjście** [bity/jednostkę] między bitem wejścia (czy GC dostaje
  silny napęd PP) a bitem wyjścia (czy GC strzela > 0.5 Hz). Kwantyfikuje wprost
  „DG jest transformacją stratną" — mechanizm stojący za wynikiem negatywnym 1A (§2b).
- **Info retention** = MI/H(wejścia) ∈ [0,1]; information loss = 1 − retention.
  **To jest właściwa oś trade-offu:** separacja zwykle KOSZTUJE informację; pytanie
  brzmi, które motywy kupują dużo separacji za mało informacji.

**Alternatywne miary separacji** (główny wynik nie może wisieć na jednej definicji
podobieństwa):

- **Cosinus** — bez centrowania. Na kodach rzadkich Pearson bywa zdominowany przez
  wspólne ZERA; cosinus patrzy tylko na część aktywną.
- **Jaccard** — |A∩B|/|A∪B| zbiorów aktywnych jednostek; miara z literatury
  remappingu. 0 = pełna ortogonalizacja.
- Dekorelacja `R_in − R_out` zostaje metryką **główną** (ciągłość z dotychczasowymi
  wynikami), ale każdą mapę dominacji trzeba sprawdzić na wszystkich trzech —
  **jeśli wniosek się odwraca między miarami, sam ten fakt jest wynikiem.**

### 5.2 Do rozbudowy na potrzeby artykułu

| grupa | czego brakuje | po co |
|---|---|---|
| separacja | **`NDP`** (podobieństwo wzorca) i **`SF`** (scaling factor) Madara przy 7 szerokościach binów (5…500 ms) + SPIKE-distance (Kreuz) | zgodność 1:1 z Madarem; **rozdzielenie kodu wzorcowego od częstotliwościowego (H5)** |
| aktywność | rzadkość „lifetime" | kontrola artefaktu wyciszenia |
| dynamika | moc w paśmie gamma populacji FS (30–100 Hz) | fizjologiczna wiarygodność reżimu |
| informacja | MI z korekcją obciążenia + **dolne ograniczenie dekodera** | odpowiedź na zarzut „dekorelacja nie wystarczy" |
| koszt | liczba spajków, zdarzeń synaptycznych, **bity na spajk** | definiuje „optymalny reżim" nietrywialnie; łączy z wątkiem neuromorficznym |
| atrybucja | Shapley dla **każdej** metryki, nie tylko dekorelacji | mapa „który motyw odpowiada za który rodzaj separacji" |

**Krytyczne przy MI:** kody są rzadkie, więc naiwny estymator MI jest silnie
obciążony w górę. Protokół: (1) dyskretyzacja z ustaloną liczbą binów,
(2) korekcja shuffle + Panzeri–Treves, (3) **krzywa MI(liczba prób)** z ekstrapolacją,
(4) zawsze obok MI dolne ograniczenie dekodera. **Jeśli oba mówią co innego — wynik
nie idzie do artykułu.**

---

## 6. Walidacja biologiczna (ground truth)

### 6.1 Dane i ich integracja

| źródło | co daje | jak wchodzi |
|---|---|---|
| **Madar, Ewell & Jones** — patch-clamp DG/CA3, BioStudies **S-BSST219** (`dataset/`) | (a) dokładne zestawy bodźców (skorelowane Poissony R∈{0.05…1.0}, 10/30 Hz, warianty burstiness) w `Protocols/`; (b) odpowiedzi GC, FS, **HMC**, CA3 na te bodźce; (c) **GC przed/po gabazynie**; (d) `CCIV` — rampy prądowe | bodźce → wejście PP (koniec z syntetycznymi wzorcami); odpowiedzi → cel walidacji; CCIV → dopasowanie Izhikevicza per typ; gabazyna → walidacja knockoutu K4 |
| **Hippocampome.org** | prawdopodobieństwa połączeń, typy interneuronów hilusa, liczebności | priory dla `P_*`; uzasadnienie redukcji 3-typowej w Methods |
| **NeuroElectro** | rozkłady Rin, rheobase, τ_m per typ | zakresy przy dopasowaniu CCIV; heterogeniczność zamiast klonów |
| **Senzai & Buzsáki 2017** (CRCNS) | *in vivo* częstotliwości i rzadkość GC i MC | **kotwica dla punktu nastawy ρ₀** |
| **ModelDB** (Santhakumar 2005, Yim 2015, Braganza 2020) | referencyjne modele DG | pozycjonowanie; ew. walidacja krzyżowa |

Integracja: jeden format (Neo → NWB 2.x przez `neuroconv`; Axograph przez
`neo.io.AxographIO`, nie MATLAB); jeden algorytm detekcji spajków dla wszystkich
typów komórek (próg na dV/dt, weryfikacja ręczna na 5%); wspólna oś czasu 0.1 ms,
okno 2 s, odcięcie pierwszych 200 ms. **NIE z-score'ujemy** — zamiast tego
dopasowujemy *napęd* modelu tak, by rozkład FR GC odpowiadał rozkładowi in vitro
(mediana i IQR, nie średnia), a wszystkie metryki podobieństwa liczymy **jedną
funkcją o dwóch wejściach** (model i dane). To eliminuje najczęstszy zarzut
recenzenta przy porównaniach model–eksperyment.

### 6.2 Pięć poziomów walidacji

**V1 — dopasowanie pojedynczego neuronu (KALIBRACJA, nie walidacja).**
CCIV → f–I, rheobase, adaptacja per typ. Kryterium: model odtwarza f–I w granicach
1 SD danych dla ≥80% komórek. *Jawnie nazwane kalibracją w Methods.*

**V2 — odpowiedź na rzeczywiste bodźce (walidacja w domenie).** Bodźce z `Protocols/`
jako wejście PP. Porównanie krzywych `R_out(R_in)`, `NDP_out(NDP_in)`,
`SF_out(SF_in)` przy wszystkich binach + rozkłady FR i burstiness. Kryterium: krzywe
modelu w obrębie CI danych; **żaden parametr obwodu nie jest dostrajany do tych
krzywych po V1**, poza jednym globalnym mnożnikiem napędu.

**V3 — walidacja krzyżowa typów komórek (mocne ograniczenie).** Jeden zestaw
parametrów obwodu musi odtworzyć **uporządkowanie separacji między typami** GC vs FS
vs HMC — dane są dla wszystkich trzech, z tym samym bodźcem. Test, którego prawie
żaden model DG nie przechodzi, bo prawie żaden nie ma takich danych.
**Największy atut tego repo.**

**V4 — predykcja farmakologiczna (out-of-sample, główny cios).**
`GC_yo_BeforeAfterGZN_P10Hz` = te same komórki przed i po 100 nM gabazyny.
Procedura: (1) kalibracja WYŁĄCZNIE na „before"; (2) knockout K4 z α z krzywej
dawka–odpowiedź z literatury, **nie dopasowanym**; (3) predykcja zmiany R/NDP/SF
i FR; (4) porównanie z „after". Predykcję rejestrujemy przed odsłonięciem „after"
(hash pliku w repo).

**V5 — kotwica in vivo i literaturowa.** Punkt nastawy ρ₀ z E1 vs obserwowana
rzadkość GC in vivo (Senzai & Buzsáki) — zgodność = mocny argument, niezgodność =
też wynik (DG optymalizuje coś innego niż separacja). Reżim `mc_active` (§3.3)
zakotwiczony w Scharfman 2016: kalibrujemy `drive`/`gain`/`brake` tak, by **netto
wpływ MC na GC był hamujący w spoczynku**. Częstotliwości FS w paśmie gamma vs
literatura.

### 6.3 Falsyfikowalne przewidywania dla eksperymentatorów

1. Częściowe wyciszenie MC (chemogenetyka) powinno *poprawić* separację przy niskim
   R_in i *pogorszyć* przy wysokim — bo MC jest motywem **warunkowym**.
2. Blokada tonicznego GABA-A (δ-GABA_A) i fazowego powinny dawać **przeciwne**
   przesunięcia na osi NDP/SF, mimo podobnej zmiany FR.
3. Po utracie MC separacja powinna wracać w skali dziesiątek minut, jeśli homeostaza
   wewnętrzna działa — mierzalne jako powolny dryf rheobase GC.

---

## 7. Oś czasu, figury, odtwarzalność

### 7.1 Dwanaście miesięcy, bramki go/no-go

**Q1 (m. 1–3) — dane, metryki, kalibracja neuronów**
- M1.1 `io_madar.py`: Axograph → Neo → NWB; detekcja spajków; **eksport bodźców
  z `Protocols/`** jako wejście modelu.
- M1.2 `metrics.py`: R / NDP / SF / SPIKE + burstiness (§5.2); **test zgodności
  z MATLABem** Madara na 20 nagraniach (tolerancja < 1%).
- M1.3 `fit_neurons.py`: dopasowanie Izhikevicza do CCIV per typ, z rozkładami (L0).
- M1.4 `analysis_plan.md` — preregistracja H1–H5 i metryki pierwszorzędowej.
- **Bramka G1:** metryki zgodne z implementacją referencyjną ORAZ f–I w granicach
  danych dla ≥80% komórek. Bez tego nie ruszamy siatek.

**Q2 (m. 4–6) — mapa reżimów i atrybucja (rdzeń Wyników)**
- M2.1 E1 na Aresie z pełną baterią metryk + maska ważności.
- M2.2 E2 (Shapley dla wszystkich metryk).
- M2.3 E6 (skalowanie N_GC do 2000–5000).
- M2.4 E3 + surrogat L3: Sobol, blokowe CV, sloppiness.
- M2.5 Suwak `W FS→HMC` + panel obserwowalności w `interactive_dg.py`.
- **Bramka G2:** H1 potwierdzona (niemonotoniczność z CI, poza maską artefaktów)
  ORAZ H2 potwierdzona na pełnej siatce. **Jeśli nie — pivot na robustness/padaczkę
  z K3 jako wynikiem głównym.**

**Q3 (m. 7–9) — kontroler adaptacyjny i perturbacje**
- M3.1 `control.py`: IP + iSTDP + SS (L2); testy stabilności.
- M3.2 E4 + E5: porównanie wielkości kontrolowanych (H3), uogólnienie.
- M3.3 K3 + K4 + K5 + K7.
- M3.4 **V4 — predykcja gabazynowa** z zapieczętowaną predykcją.
- **Bramka G3:** kontroler odzyskuje separację po ≥2 z 3 perturbacji ORAZ zbiega do
  punktu zgodnego z optimum offline (H4).

**Q4 (m. 10–12) — walidacja, figury, manuskrypt**
- M4.1 V2/V3. M4.2 V5. M4.3 zamrożenie wyników (Zenodo, ModelDB, kontener).
- M4.4 figury (§7.2) + manuskrypt; preprint na bioRxiv **przed** submisją.
- M4.5 submisja + gotowy plan odpowiedzi na trzy najbardziej prawdopodobne zarzuty.

*Bufor:* Q1 i Q3 są najbardziej ryzykowne. 12 miesięcy wystarcza tylko przy
założeniu, że E1–E3 lecą na HPC bez babysittingu — sharding i kontener muszą
działać do końca Q1.

### 7.2 Plan figur — kontrakt na zakres

Jeśli figura nie ma miejsca, eksperyment nie ma priorytetu.

| Fig | treść |
|---|---|
| **1** | Model: schemat obwodu z rozdzielonymi kanałami + kalibracja L0 (f–I model vs CCIV, 4 typy) + rastry |
| **2** | **Okno funkcjonalne**: separacja (NDP/SF/R) vs poziom aktywności; niemonotoniczność; panel kontrolny FR; maska artefaktów |
| **3** | **Hamulec MC tworzy okno**: `W_FS_HMC` × napęd; bistabilność przy 0; reżim pośredni przy 2 |
| **4** | **Atrybucja**: Shapley per motyw dla każdej metryki; mapa dominacji (R_in × tempo); interakcja FB×MC |
| **5** | **Co jest regulowane**: 3 wielkości kontrolowane × 3 mechanizmy; uogólnienie poza reżim strojenia (H3) |
| **6** | **Odzysk po perturbacji**: dezinhibicja i utrata MC; trajektorie (aktywność × separacja) |
| **7** | **Walidacja**: (a) model vs dane na bodźcach Madara; (b) uporządkowanie typów; (c) predykcja gabazynowa out-of-sample |
| S1–S6 | sloppiness/Sobol, skalowanie N_GC, kontrola MI, modele zerowe, wrażliwość na L0, pełne siatki |

### 7.3 FAIR — wymóg PLOS CB

Bieżąca gwarancja odtwarzalności repo (neutralne wartości nowych parametrów, hash
spajków bit-w-bit) jest w [README.md](README.md). Do artykułu dochodzi:

- **Determinizm:** każdy przebieg zapisuje `{git_sha, config_hash, seed, wersje
  bibliotek}` w nagłówku pliku wynikowego. Brak tego = wynik nie idzie do artykułu.
- **Konfiguracja plikiem, nie flagami** — YAML w `configs/` jest jednocześnie
  dokumentacją eksperymentu i wpisem w Supplementary.
- **Dane w trzech warstwach na Zenodo** (wersjonowany DOI): L1 surowe wyniki
  (Parquet), L2 metryki zagregowane (CSV), L3 figury + dane do figur. Recenzent
  reprodukuje figury z L2 w minutę.
- **Model osobno w ModelDB** (i/lub Open Source Brain).
- **Nie redystrybuujemy surowych nagrań Madara** — publikujemy skrypt pobierający
  + nasze pochodne (wykryte spajki w NWB) z jawną atrybucją.
- **CI:** `pytest` + preset `quick` każdego eksperymentu + linter na pułapki modelu
  (gołe `N_GC=`, brak maski ważności, MI bez korekcji).
- **Kontener** (Docker + Apptainer): ten sam `.sif` na Aresie i lokalnie.

---

## 8. Ryzyka i pozycjonowanie wobec literatury

**Najbliższa literatura — trzeba się wobec niej jawnie ustawić w Intro:**

- **Yim, Hanuschkin, Wolfart (2015)** — *intrinsic rescaling* GC przywraca separację
  w warunkach epileptycznych. **Najbliższy prior art dla H4.** Nasza różnica:
  kontroler ONLINE (zamknięta pętla, nie jednorazowe przeskalowanie), porównanie
  *wielkości kontrolowanej* (H3), rola pętli MC jako mechanizmu okna, walidacja na
  danych z tym samym bodźcem. **Jeśli tego nie rozgraniczymy — desk reject.**
- **Braganza, Mueller-Komorowska, Beck (2020)** — obwód feedback i separacja zależna
  od częstotliwości. Nasza różnica: MC + regulacja adaptacyjna + kody NDP/SF.
- **Madar, Ewell & Jones (2019, PLOS CB)** — eksperymentalny towarzysz naszego
  modelu. Ustawiamy się jako **model wyjaśniający ich obserwacje**, nie konkurencja.
- **Santhakumar / Soltesz** — DG w padaczce; nasza różnica: nie liczymy napadów,
  tylko regulację punktu pracy separacji.

| ryzyko | prawdop. | mitygacja |
|---|---|---|
| Model 3-typowy (GC/FS/HMC) uznany za zbyt zredukowany | średnie | uzasadnienie z Hippocampome + analiza wrażliwości + argument, że redukcja jest warunkiem siatki 100 tys. symulacji |
| Izhikevich uznany za zbyt abstrakcyjny | średnie | **V1 (dopasowanie do CCIV) rozbraja to niemal całkowicie** — główny powód, by zrobić L0 |
| **H1 nie potwierdzona** (wynik wstępny E1 jej nie potwierdza) | **realizuje się** | szersza siatka + zaostrzona maska; jeśli obalona — pivot na robustness/padaczkę (bramka G2) |
| H4 „za łatwa" (homeostaza oczywiście stabilizuje) | wysokie | ciężar dowodu przenieść na **H3** (co jest regulowane) i na E5 (uogólnienie) |
| Predykcja gabazynowa nie trafi | średnie | to nadal wynik, o ile preregistrowany: mówi, że fazowe hamowanie GC nie tłumaczy efektu → wskazuje na toniczne/na sieć |
| Zbyt duży zakres na 12 miesięcy | wysokie | plan figur (§7.2) jest kontraktem; E6 i K5 pierwsze do wycięcia |

**Co uśmiercamy jawnie:** odczyt liniowy 1A — zamknięty, wchodzi do artykułu jako
jedno zdanie w Discussion („decorrelation does not imply linear decodability"),
ewentualnie panel suplementu; pojemność 1B — odłożona do po bramce G2, bo wymaga
N_GC ≥ 2000; catastrophic forgetting — poza zakresem tego artykułu; NEST — nie
ruszać (drugie źródło prawdy modelu).

**Odłożone kierunki doktoratu** (poza zakresem artykułu, ale w zakresie pracy):
neuromorfika (reguły strojenia rzadkich warstw SNN — naturalne przedłużenie inverse
design); DG → CA3, separacja vs completion (największy zakres, przyszłość);
three-factor learning (semestr 6).

> **Skąd dawne nazwy `kierunek1_readout` / `kierunek4_motifs`** w historii repo:
> z numeracji pięciu kierunków badawczych z początku doktoratu. Kierunek 4 =
> atrybucja motywów (dziś E2), kierunek 1 = odbiorca downstream (dziś
> `readout_deferred/`). Kierunki 2 (catastrophic forgetting), 3 (neuromorfika)
> i 5 (DG→CA3) nigdy nie dostały kodu. Numeracja E1–E7 zastąpiła tamtą, bo
> „kierunek" nie mówił, co dany kod właściwie testuje.

---

## 9. Otwarte kwestie i role

### 9.1 Blokujące — wysłane do prof. Błasiak 2026-09-11

Pełne brzmienie pytań i zmierzone liczby, które je motywują: [STATUS.md](STATUS.md) §2.
W skrócie: (B1) realny udział prądu tonicznego w hamowaniu GC — wymusza `K`, a przez
pułapkę §3.5.4 także próg i spoczynek; (B2) czy bazowa częstotliwość FS jest
fizjologiczna — kotwiczy siłę nowego kanału FS→FS; (B3) **do którego reżimu wejścia
kalibrujemy** — in vitro Madara czy gęsty napęd PP; jedna waga nie obsłuży obu.

B3 jest pytaniem badawczym, nie usterką: rzadka stymulacja w plastrze i gęsty napęd
PP to dwa różne punkty pracy, a wybór między nimi rzutuje na całą pracę —
w szczególności na to, czy predykcja gabazynowa (§6.2 V4) jest porównywalna z danymi.

### 9.2 Do decyzji po naszej stronie

1. **Wynik wstępny E1 nie potwierdza H1** — rozstrzygnąć, czy to artefakt maski, za
   wąska siatka, czy realne obalenie hipotezy nośnej. **Kwestia priorytetowa.**
2. Czy rozdzielić w modelu prąd toniczny od offsetu pobudliwości? Dziś to jeden
   parametr w trzech rolach (§3.5.4). Rozdzielenie usuwa pułapkę, ale jest zmianą
   modelu neuronu i wymaga opisu w Methods.
3. Kalibracja reżimu `mc_active` — §6.2 V5 daje procedurę, ale trzeba potwierdzić,
   czy „netto hamujący wpływ MC na GC w spoczynku" to właściwe kryterium
   (Scharfman 2016).
4. **Metryka pierwszorzędowa:** NDP przy 100 ms czy MI(klasa; kod)? Propozycja: NDP
   (porównywalna z Madarem), MI jako współrzędna druga. Do preregistracji (§3.4 pkt 6).
5. **Punkt nastawy ρ₀:** strojony jako wolny parametr czy wzięty z danych in vivo?
   Mocniejsza wersja: wzięty z danych i pokazany, że pokrywa się z optimum offline.
6. **Czy CA3 wchodzi do modelu?** Dane są. Za: zamyka łuk separacja→completion.
   Przeciw: podwaja zakres. Propozycja: **nie w tym artykule**, CA3 z danych jako
   punkt odniesienia w V3.
7. **Autorstwo** przy trójce (Błasiak / Wielgosz / Jakub) — ustalić przed Q2, bo
   Fig. 5–6 to naturalnie rdzeń doktoratu.

### 9.3 Role we współpracy

**prof. Anna Błasiak** — hipoteza biologiczna, uzasadnienie parametrów, interpretacja
dynamiki, homeostaza/E-I/neuromodulacja, ew. powiązanie z eksperymentami MEA.
**Maciej Wielgosz** — SNN/architektura/system, implementacja, efektywność,
neuromorphic implications. **Jakub** — warstwa computational/ML: formalizacja
hipotez, eksperymenty, analiza, adaptacyjne mechanizmy, doktorat.
