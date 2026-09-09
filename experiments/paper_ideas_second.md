# Paper ideas — wersja druga: adaptacyjna regulacja aktywności a separacja wzorców

*Dokument roboczy, stan 2026-08-24. Cel: plan projektu publikacyjnego pod
**PLOS Computational Biology**, osadzony w faktycznym stanie tego repo
(`doktorat_plan.md`, `experiments/`, `dataset/`). Nacisk na METODOLOGIĘ
i EKSPERYMENTY, nie na tekst manuskryptu.*

---

## 0. Rekomendacja w trzech zdaniach (przeczytaj, nawet jeśli reszty nie)

1. **Masz już fundament, którego zwykle brakuje**: wynik `FS→HMC` (brak reżimu
   pośredniego → hamulec przywraca separację, +0.247 vs −0.267) jest gotowym
   dowodem tezy „regulacja hamująca wyznacza okno funkcjonalne", a negatywny wynik
   1A jest uczciwym uzasadnieniem przejścia na miary informacyjne.
2. **Masz coś jeszcze lepszego, a nie używasz tego**: `dataset/` to komplet danych
   patch-clamp Madara, Ewella i Jonesa — *tych samych bodźców wejściowych*, czterech
   typów komórek (GC, FS, HMC, CA3) i **eksperymentu farmakologicznego przed/po
   gabazynie**. To jest gotowy ground truth dla in-silico knockoutów, a artykuł
   towarzyszący ukazał się w PLOS Comp Biol — czyli redakcja i recenzenci znają
   kontekst i metryki (R / NDP / SF).
3. **Kierunek**: przestań badać „czy DG separuje" (na to odpowiedziano), zacznij
   badać **„co utrzymuje DG w reżimie, w którym separuje"** — z jawnym
   kontrolerem homeostatycznym, walidowanym na danych gabazynowych i na utracie
   mossy cells (model padaczki). To jest pytanie biologiczne, a nie metodologiczne,
   więc przechodzi filtr PLOS Comp Biol („no methods-only papers").

---

## 1. Tytuł i Author Summary

### 1.1 Kandydaci na tytuł

| # | tytuł | co eksponuje |
|---|---|---|
| **A** ★ | **Inhibitory control of the hilar mossy cell loop defines a narrow activity window for pattern separation, and homeostatic regulation keeps the dentate gyrus inside it** | mechanizm + odkrycie; długi, ale w duchu PLOS CB |
| B | *Pattern separation has an activity set point: adaptive inhibition maintains it in a data-constrained spiking model of the dentate gyrus* | „set point" jako haczyk pojęciowy |
| C | *Robustness without tuning: homeostatic regulation of excitability recovers the pattern-separation regime after disinhibition and mossy cell loss* | eksponuje robustness + trafność kliniczną |

Rekomendacja: **A** jako roboczy (mechanizm→odkrycie), **C** trzymać w zanadrzu,
jeśli wynik z utratą MC okaże się mocniejszy niż wynik z oknem aktywności.

### 1.2 Draft Author Summary (~190 słów, bez żargonu)

> - Every day we form memories of places and events that are almost identical to
>   ones we already have. The brain avoids confusing them in a small region called
>   the dentate gyrus, which turns similar inputs into dissimilar patterns of
>   activity — a process called pattern separation.
> - Textbook explanations say this works because the region is sparsely active and
>   heavily inhibited. But its inputs are not constant: their rate, timing and
>   similarity change with behaviour, and the circuit itself changes with disease.
>   How separation survives that variability is not understood.
> - We built a spiking network model of the dentate gyrus, constrained by
>   electrical recordings from four cell types stimulated with the same input
>   patterns, and mapped how well it separates inputs across a wide range of
>   activity levels.
> - Separation works only inside a narrow window of activity. Outside it, the
>   circuit either falls silent or starts making patterns *more* similar. We show
>   that inhibition of hilar mossy cells is what creates this window, and that a
>   simple homeostatic rule — cells adjusting their own excitability — is enough
>   to keep the network inside it after disinhibition or after mossy cell loss,
>   the hallmark of temporal lobe epilepsy.
> - This turns pattern separation from a fixed property of wiring into a
>   *regulated* one, and predicts which measurements should change when the
>   regulation fails.

*Uwaga redakcyjna:* PLOS chce Author Summary prozą; powyższe punkty scalimy
w 3 akapity na etapie pisania. Test poprawności: nie ma tu słów „decorrelation",
„Shapley", „mutual information", „Izhikevich".

---

## 2. Problem biologiczny, luka w wiedzy, hipotezy

### 2.1 Luka BIOLOGICZNA (nie obliczeniowa)

Separacja wzorców w DG jest opisywana jako **statyczna własność architektury**:
ekspansja (10⁶ GC), rzadkie kodowanie, silne hamowanie. Trzy fakty tego nie
domykają:

1. **Statystyka wejścia jest zmienna.** Kora śródwęchowa dostarcza wejście
   o zmiennym tempie, korelacji i „burstiness"; Madar i wsp. pokazali, że
   separacja u tego samego neuronu zależy od skali czasowej i statystyki bodźca.
   Sieć strojona na jeden reżim nie ma powodu działać w innym.
2. **Sam obwód nie jest stabilny.** W naszym modelu pętla `GC→HMC→GC` bez
   hamulca nie ma reżimu pośredniego: mossy cells są albo nieistotne, albo
   uciekają, a obwód zaczyna *korelować* wzorce (dekorelacja −0.267). Biologia ma
   ten hamulec (interneurony hilusa hamują MC — Scharfman 2016) — pytanie, po co.
3. **Regulacja bywa uszkodzona.** Utrata mossy cells jest znakiem rozpoznawczym
   padaczki skroniowej, a spór „dormant basket cell" (Sloviter) vs „irritable
   mossy cell" trwa. Obie hipotezy mówią o tym samym: o utracie REGULACJI, nie
   o utracie separacji per se.

**Luka:** nie wiemy, **jaka wielkość jest w DG regulowana** i **czy jej regulacja
jest tym, co czyni separację odporną**. Kandydaci na wielkość kontrolowaną:
średnia częstotliwość GC, frakcja aktywnych GC (rzadkość), lokalny bilans E/I na
neuronie. To są trzy różne hipotezy biologiczne o trzech różnych przewidywaniach.

### 2.2 Nowe spojrzenie, które daje ten model

Model przenosi separację z kategorii „własność" do kategorii „**punkt pracy
utrzymywany przez sprzężenie zwrotne**". Konkretnie dostarcza:

- **mapę reżimów** — separacja jako funkcja poziomu aktywności, z jawną
  demonstracją niemonotoniczności (optimum, a nie monotoniczny wzrost z hamowaniem);
- **przypisanie ról** — który motyw hamowania (FF / FB / MC) tworzy okno, a który
  je przesuwa (wartości Shapleya, już policzone dla dekorelacji);
- **rozdzielenie kodów** — czy regulacja przenosi separację między kodem
  „wzorcowym" (NDP) a „częstotliwościowym" (SF); to bezpośrednie rozwinięcie
  tezy Madara o multipleksowaniu kodów;
- **falsyfikowalne przewidywania** dla eksperymentu in vitro (kierunek i wielkość
  efektu gabazyny; efekt stopniowej utraty MC; efekt zmiany pobudliwości GC
  odpowiadający neurogenezie).

### 2.3 Hipotezy (falsyfikowalne, z warunkiem obalenia)

| ID | hipoteza | obala ją |
|---|---|---|
| **H1** | Separacja jest niemonotoniczną funkcją poziomu aktywności populacji GC — istnieje optimum przy pośredniej frakcji aktywnych komórek. | monotoniczny wzrost separacji przy spadku aktywności aż do reżimu ciszy (po odrzuceniu artefaktu „pustego wektora") |
| **H2** | Hamowanie MC (`FS→HMC`) tworzy reżim pośredni — bez niego okno funkcjonalne znika (bistabilność: cisza albo runaway). | istnienie szerokiego reżimu pośredniego przy `W_FS_HMC = 0` w pełnej siatce, nie tylko w punkcie domyślnym |
| **H3** | Wielkością regulowaną, która najlepiej utrzymuje separację przy zmiennej statystyce wejścia, jest **frakcja aktywnych GC**, a nie średnia częstotliwość ani lokalny E/I. | kontroler na FR lub na E/I utrzymuje separację równie dobrze lub lepiej w teście uogólnienia poza reżim strojenia |
| **H4** | Prosta reguła homeostatyczna (plastyczność wewnętrzna progu + iSTDP na `FS→GC`) samodzielnie odnajduje punkt pracy zidentyfikowany offline i przywraca separację po dezinhibicji oraz po utracie 50% MC. | kontroler zbiega do punktu istotnie różnego od optimum offline albo nie odzyskuje separacji w żadnym z warunków |
| **H5** | Regulacja przesuwa separację między kodami: przy niskiej aktywności dominuje separacja „wzorcowa" (NDP), przy wysokiej „częstotliwościowa" (SF). | brak dysocjacji NDP/SF wzdłuż osi aktywności — w modelu I w danych Madara |

**Ważne:** H1 i H2 są w dużej mierze przetestowane wstępnie (§2 `doktorat_plan.md`);
H3–H5 są nowe i to one niosą ciężar publikacji.

---

## 3. Metodologia i eksperymenty obliczeniowe

### 3.1 Dane publiczne i ich integracja

| źródło | co daje | jak wchodzi do projektu |
|---|---|---|
| **Madar, Ewell & Jones** — patch-clamp DG/CA3, BioStudies **S-BSST219** (lokalnie: `dataset/PatchPatSep2s_Public/`, kod `dataset/PatSepSpikeTrains/`, MIT) | (a) *dokładne zestawy bodźców* (skorelowane Poissony R∈{0.05…1.0}, 10/30 Hz, warianty burstiness) w `Protocols/`; (b) odpowiedzi GC, FS, **HMC**, CA3 na te bodźce; (c) **GC przed/po gabazynie**; (d) `CCIV` — rampy prądowe do charakterystyki f–I | bodźce → wejście PP modelu (koniec z syntetycznymi wzorcami); odpowiedzi → cel walidacji; CCIV → dopasowanie parametrów Izhikevicza per typ komórki; gabazyna → walidacja knockoutu hamowania |
| **Hippocampome.org** | prawdopodobieństwa połączeń, typy interneuronów hilusa, liczebności populacji | priory dla `P_*` w `DGConfig`; uzasadnienie 3-typowej redukcji (GC/FS/HMC) w Methods |
| **NeuroElectro** | rozkłady właściwości elektrofizjologicznych per typ (Rin, rheobase, τ_m) | zakresy dopuszczalne przy dopasowaniu CCIV; heterogeniczność populacji zamiast klonów |
| **Senzai & Buzsáki 2017** (databank Buzsáki lab / CRCNS) | *in vivo* częstotliwości i rzadkość GC oraz MC u zachowującego się zwierzęcia | **kotwica dla punktu nastawy** kontrolera: czy ρ₀ maksymalizujące separację odpowiada obserwowanej rzadkości |
| **ModelDB** (Santhakumar 2005, Yim 2015, Braganza 2020) | referencyjne modele DG | pozycjonowanie; ewentualna walidacja krzyżowa architektury |

**Integracja i normalizacja (konkretnie):**

1. **Jeden format**: wszystkie nagrania i bodźce → **Neo** → eksport do **NWB 2.x**
   (`neuroconv`). Axograph czytamy przez `neo.io.AxographIO` (działa już
   w `explore_data.py`) — nie przez MATLAB.
2. **Detekcja spajków** jednym algorytmem dla wszystkich typów komórek (próg na
   dV/dt, weryfikacja ręczna na losowej próbce 5%), bo porównujemy typy między sobą.
3. **Wspólna oś czasu**: wszystko na siatce 0.1 ms (`DT_MS`), okno analizy 2 s
   zgodnie z protokołem, odcięcie pierwszych 200 ms (transjent).
4. **Normalizacja skali**: NIE z-score'ujemy. Zamiast tego (a) dopasowujemy
   *napęd* modelu tak, by rozkład FR GC odpowiadał rozkładowi in vitro
   (dopasowanie mediany i IQR, nie średniej), (b) wszystkie metryki podobieństwa
   liczymy w tej samej implementacji dla modelu i dla danych — **jedna funkcja,
   dwa wejścia**. To eliminuje najczęstszy zarzut recenzenta przy porównaniach
   model–eksperyment.
5. **Metryki jak u Madara**: `R` (Pearson na binowanych spike-trainach),
   **`NDP`** (znormalizowany iloczyn skalarny — podobieństwo „wzorca"),
   **`SF`** (scaling factor — podobieństwo „skali/tempa"), przy zestawie szerokości
   binów (5, 10, 20, 50, 100, 250, 500 ms) + **SPIKE-distance** (Kreuz).
   Reimplementacja w Pythonie z **testem zgodności do MATLABa** z
   `dataset/PatSepSpikeTrains/SimilarityAnalysis/` na 20 losowych nagraniach
   (osobny kamień milowy, §6 Q1).

### 3.2 Architektura obliczeniowa — cztery poziomy

Zasada nadrzędna: **jedno źródło prawdy modelu** = `experiments/dg_core/`.
Nie przepisujemy do NEST (`doktorat_plan.md` §5) — NEST najwyżej jako walidacja
krzyżowa na końcu.

**L0 — pojedynczy neuron, ograniczony danymi.**
Izhikevich (a, b, c, d, K) dopasowywany per typ komórki (GC / FS / HMC / CA3)
do nagrań `CCIV` z `dataset/`. Metoda: różnicowa ewolucja / CMA-ES na funkcji
kosztu = krzywa f–I + rheobase + adaptacja ISI + kształt AP (największa waga na f–I).
Produkt: `dg_core/fit_neurons.py` + rozkłady parametrów → **heterogeniczna
populacja** (losowanie z dopasowanego rozkładu zamiast identycznych klonów).
*To jest największy skok wiarygodności modelu przy najmniejszym nakładzie* —
i zamyka jednocześnie postulat „poziom 1" z ramy współpracy.

**L1 — obwód DG.** Istniejący `dg_core/circuit.py` (GC/FS/HMC, rozdzielone kanały
`g_ex`/`g_ex2`/`g_ex3`/`g_in` — obserwowalność za darmo). Rozszerzenia:
- `W_FS_HMC` jako pełnoprawny parametr osi (istnieje, domyślnie 0);
- wejście PP z **rzeczywistych protokołów Madara** (nowy tryb `pp_source='madar'`
  obok `per_fiber`/aggregate);
- opcjonalna depresja krótkoterminowa Tsodyks–Markram na `PP→GC` (backlog
  z `Changes.md`) — jako parametr, nie jako domyślna zmiana modelu.

**L2 — kontroler adaptacyjny (rdzeń nowości).** Trzy mechanizmy, każdy włączalny
osobno, wszystkie wolne względem dynamiki obwodu (τ ≈ 1–10 s):
- **IP (intrinsic plasticity)**: `dK_i/dt = η_K (r_i − ρ₀)` — regulacja tonicznego
  prądu hamującego. W tym modelu `K` *jest* tonicznym GABA-A (`G_crit = 4 + K`),
  więc to jest biologicznie przesunięcie rheobase / tonic GABA, a nie abstrakcyjny
  próg;
- **iSTDP (Vogels–Sprekeler)** na `FS→GC`: `Δw = η(pre·post − α)`, `α = 2ρ₀τ_STDP`
  — biologicznie umocowana implementacja punktu nastawy E/I;
- **SS (synaptic scaling)** multiplikatywne na `W_PP_GC` — kontrola napędu.

Trzy warianty *wielkości kontrolowanej* (test H3): `r_i` = częstotliwość neuronu,
`a_i` = binarna aktywność (→ frakcja aktywnych), `b_i = g_ex/(g_ex+g_in)` = lokalny
bilans E/I. **To jest eksperyment, nie detal implementacyjny.**

**L3 — surrogat ML (narzędzie, nie wynik).** Gradient boosting / GP na danych
z siatki: parametry + statystyki aktywności → metryki separacji i informacji.
Trzy zastosowania: (a) globalna analiza wrażliwości (indeksy Sobola),
(b) przyspieszony inverse design („maksymalna separacja przy budżecie spajków"),
(c) **analiza „sloppiness"** — widmo Hessianu / PCA wrażliwości: czy 10-wymiarowa
przestrzeń parametrów redukuje się do 2 sztywnych kombinacji (przewidywanie:
„poziom aktywności" i „netto E/I"). Punkt (c) jest wynikiem biologicznym, nie
ML-owym: mówi, *co* obwód musi regulować, żeby wszystko inne przestało mieć
znaczenie.

### 3.3 Bateria metryk (`dg_core/metrics.py` — rozbudowa)

| grupa | metryki | po co |
|---|---|---|
| separacja | `R`, **`NDP`**, **`SF`** przy 7 szerokościach binów; SPIKE-distance; dekorelacja `R_in − R_out` | zgodność 1:1 z Madarem; **rozdzielenie kodu wzorcowego od częstotliwościowego** (H5) |
| aktywność (kontrola artefaktów) | FR per typ, frakcja aktywnych, rzadkość Trevesa–Rollsa (jest), rzadkość „lifetime" | pułapka #3: separacja czy wyciszenie |
| dynamika | CV(ISI), Fano, indeks synchronii, **moc w paśmie gamma populacji FS (30–100 Hz)** | fizjologiczna wiarygodność reżimu; realizacja obietnicy obserwowalności |
| informacja | MI(klasa wzorca; kod wyjściowy) z korekcją obciążenia, entropia kodu, information loss, **dolne ograniczenie dekodera** | odpowiedź na zarzut „dekorelacja nie wystarczy" (wynik 1A) |
| koszt | liczba spajków, liczba zdarzeń synaptycznych, **bity na spajk** | definiuje „optymalny reżim" nietrywialnie; łączy z wątkiem neuromorficznym |
| atrybucja | Shapley per motyw (jest), interakcje 2-czynnikowe (jest) — teraz dla **każdej** metryki, nie tylko dekorelacji | mapa „który motyw odpowiada za który rodzaj separacji" |

**Krytyczne przy MI:** kody są rzadkie, więc naiwny estymator MI jest silnie
obciążony w górę. Protokół: (1) dyskretyzacja z ustaloną liczbą binów,
(2) korekcja shuffle + Panzeri–Treves, (3) **krzywa MI(liczba prób)** z ekstrapolacją,
(4) zawsze raportować obok MI dolne ograniczenie dekodera (prosty klasyfikator na
trzymanej części). Jeśli oba mówią co innego — wynik nie idzie do artykułu.

### 3.4 Eksperymenty obliczeniowe (E1–E7)

| # | eksperyment | plan | rozmiar | testuje |
|---|---|---|---|---|
| **E1** | **Mapa reżimów** — separacja vs poziom aktywności | osie: napęd PP (×0.25…×4), `W_FS_GC`, `K_GC`, `R_in` ∈ {0.5…0.975}, `W_FS_HMC` ∈ {0, 1, 2, 5}, reżim MC (`mc_inert`/`mc_active`); 10 seedów sieci × 10 zestawów wzorców | ~30–50 tys. symulacji | H1, H2 |
| **E2** | **Atrybucja motywów** — 2³ lezje FF/FB/MC + Shapley, z pełną baterią metryk | istniejący `run_lesion_grid.py`, ta sama sieć i te same wzorce we wszystkich lezjach | 8 × podsiatka E1 ≈ 20 tys. | który motyw tworzy okno |
| **E3** | **Sobol/LHS dla surrogatu ML** — quasi-losowe próbkowanie 10-wym. przestrzeni | sekwencja Sobola, NIE gęsta siatka (§3.5, leakage) | 20 tys. + 5 tys. testowych spoza hipersześcianu | L3, indeksy Sobola, sloppiness |
| **E4** | **Kontroler** — 3 mechanizmy × 3 wielkości kontrolowane × ON/OFF | protokół: 60 s adaptacji → perturbacja → 60 s odzysku | ~3 tys. długich przebiegów | H3, H4 |
| **E5** | **Uogólnienie kontrolera** — strojony w jednym reżimie, testowany w innych | strojenie przy 10 Hz / R=0.75; test na 30 Hz, na wariantach burstiness, na innych `R_in` | ~2 tys. | H3 (kluczowy test) |
| **E6** | **Skalowanie** — `DGConfig.scaled(N)` dla N_GC ∈ {200, 400, 800, 2000, 5000} | test kodowania ekspansyjnego, stały in-degree | ~1 tys. (drogie) | czy okno przesuwa się z rozmiarem |
| **E7** | **Walidacja na bodźcach Madara** — wejście = rzeczywiste protokoły | patrz §4 | ~5 tys. | ground truth |

Koszt: ~80–100 tys. symulacji × ~1.3 s dla najkrótszych; z E4 (długie przebiegi
adaptacji) i E6 (duże sieci) realistycznie **kilka tysięcy rdzenio-godzin** — na
Aresie nieistotne (`experiments/hpc/`, sharding `--shard/--n-shards`, osobny
`BRIAN2_CACHE_DIR` per task).

### 3.5 Walidacja wewnętrzna, kontrola przeuczenia, statystyka

**To sekcja, na której recenzenci PLOS CB koncentrują ogień. Cztery pułapki:**

1. **Leakage przez sąsiedztwo w siatce.** Losowe CV na gęstej siatce parametrów
   zawyża R² surrogatu, bo sąsiednie punkty są niemal duplikatami. Protokół:
   **blokowe CV w przestrzeni parametrów** (podział na hipersześcienne bloki,
   trzymany blok w całości) + osobny **zbiór ekstrapolacyjny poza hipersześcianem
   treningowym**. Raportujemy oba R² — różnica między nimi sama jest informacją
   (mówi, czy surrogat uchwycił mechanizm, czy tylko interpoluje).
2. **Leakage przez seed sieci.** Ten sam seed łączności nie może występować
   w treningu i w teście → **GroupKFold po seedzie**.
3. **Artefakt „separacja przez wyciszenie".** Formalna **maska ważności**: punkt
   siatki wchodzi do analizy tylko gdy frakcja aktywnych GC ∈ [0.005, 0.5] ORAZ
   `std(rates) > 0`. Poza maską `R_out` jest *nieokreślone*, nie zerowe. Każdy
   panel figury nosi obok panel z FR/aktywnością (pułapka #3).
4. **Skalowanie.** Wyłącznie `DGConfig.scaled(N)`, nigdy `DGConfig(N_GC=...)`.
   Dodać **test w CI**, który wykrywa gołe `N_GC=` w skryptach sweepów.

**Statystyka:**
- efekty raportowane jako **wielkości efektu z 95% CI z bootstrapu po seedach**,
  nie jako same p-wartości;
- model mieszany (seed sieci i zestaw wzorców jako efekty losowe) dla porównań
  między warunkami — bo próby nie są niezależne;
- korekcja **BH-FDR** przy porównaniach po siatce;
- **model zerowy** dla każdej metryki: (a) losowa sieć o dopasowanej rzadkości,
  (b) permutowane etykiety wzorców, (c) sieć bez hamowania. Bez tych trzech żaden
  wynik separacji nie jest raportowany;
- **preregistracja wewnętrzna**: przed uruchomieniem E1 zapisujemy w repo
  `analysis_plan.md` z metryką pierwszorzędową (propozycja: separacja `NDP` przy
  binie 100 ms) i kryteriami H1–H5. Data commita = dowód. Tanie, a bardzo dobrze
  wygląda w Methods.

### 3.6 Eksperymenty perturbacyjne (in silico knockouts) — K1–K7

Standard PLOS: perturbacja pokazuje mechanizm, nie tylko korelację.

| # | knockout | implementacja | przewidywanie |
|---|---|---|---|
| **K1** | lezje motywów FF / FB / MC (pełny 2³) | `cfg.with_motifs()` (jest) | Shapley: FB dominuje w reżimie `mc_inert`, MC staje się warunkowo dominujący w `mc_active` (wstępnie potwierdzone) |
| **K2** | **utrata hamulca MC**: `W_FS_HMC → 0` | jest | zanik reżimu pośredniego → bistabilność (H2) |
| **K3** | **stopniowa utrata mossy cells** (model padaczki skroniowej) | `N_HMC` × {1.0, 0.75, 0.5, 0.25, 0} przy zachowanym in-degree | rozstrzyga „dormant basket cell" vs „irritable mossy cell": mierzymy napęd FS (`g_ex3`) i separację równocześnie — model mówi, który mechanizm dominuje przy jakim stopniu utraty |
| **K4** | **symulowana gabazyna**: (a) tylko fazowa `W_FS_GC × (1−α)`, (b) tylko toniczna `K_GC × (1−α)`, (c) obie | nowy parametr `gaba_block` | dysocjacja toniczne/fazowe GABA-A; wersja (c) porównywana ilościowo z danymi przed/po GZN (§4 V4) |
| **K5** | **pobudliwość GC** (proxy neurogenezy): obniżone `K_GC` dla podpopulacji 5–20% GC | `K_GC` per-neuron zamiast globalnego | młode, pobudliwe GC: pogarszają czy poprawiają separację? (spór w literaturze — model podaje warunek) |
| **K6** | **knockouty kontrolera**: IP off / iSTDP off / SS off / wszystkie off | L2 | czy któryś mechanizm sam wystarcza (H4) |
| **K7** | **perturbacje wejścia**: skok tempa ×3, powolny dryf, utrata 30% włókien PP | tryb bodźca | odporność: czas odzysku, przeregulowanie, błąd ustalony |

Wszystkie knockouty na **tej samej sieci i tych samych wzorcach**
(deterministyczny `make_connectivity(seed)`) — jest zaimplementowane i jest to
warunek poprawności Shapleya.

---

## 4. Weryfikacja biologiczna (ground truth)

Pięć poziomów, od najtańszego do najmocniejszego. **V4 jest kluczowy** — to
predykcja out-of-sample, nie dopasowanie.

**V1 — dopasowanie pojedynczego neuronu (kalibracja).**
CCIV z `dataset/` → f–I, rheobase, adaptacja per typ (GC/FS/HMC/CA3).
Kryterium: model odtwarza f–I w granicach 1 SD danych dla ≥80% komórek.
*To jest kalibracja, nie walidacja — jawnie tak nazwane w Methods.*

**V2 — odpowiedź na rzeczywiste bodźce (walidacja w domenie).**
Bodźce z `Protocols/` (te same, których użyto in vitro) podawane jako wejście PP.
Porównanie: krzywe `R_out(R_in)`, `NDP_out(NDP_in)`, `SF_out(SF_in)` przy
wszystkich szerokościach binów, rozkłady FR, burstiness (compactness/occupancy,
KLD ISI — jest w `NoiseFitFtestBurst/`).
Kryterium: krzywe modelu w obrębie CI danych; **żaden parametr obwodu nie jest
dostrajany do tych krzywych po V1**, poza jednym globalnym mnożnikiem napędu.

**V3 — walidacja krzyżowa typów komórek (mocne ograniczenie).**
Jeden zestaw parametrów obwodu musi jednocześnie odtworzyć **uporządkowanie
separacji między typami komórek** GC vs FS vs HMC — dane są dla wszystkich trzech,
z tym samym bodźcem. To test, którego prawie żaden model DG nie przechodzi, bo
prawie żaden nie ma takich danych. **Największy atut tego repo.**

**V4 — predykcja farmakologiczna (out-of-sample, główny cios).**
Dane `GC_yo_BeforeAfterGZN_P10Hz` = te same komórki przed i po 100 nM gabazyny.
Procedura: (1) kalibracja WYŁĄCZNIE na warunku „before"; (2) knockout K4 z α
odpowiadającym 100 nM GZN wziętym z krzywej dawka–odpowiedź z literatury, a nie
dopasowanym; (3) **predykcja** zmiany R/NDP/SF i FR; (4) porównanie z „after".
Predykcję rejestrujemy przed odsłonięciem „after" (hash pliku w repo). To dokładnie
ten rodzaj testu, za który PLOS CB przyjmuje prace modelowe.

**V5 — kotwica in vivo i literaturowa.**
- Punkt nastawy ρ₀ znaleziony offline (E1) vs obserwowana rzadkość GC in vivo
  (Senzai & Buzsáki 2017). Zgodność = mocny argument, że regulacja w modelu trafia
  w biologię; niezgodność = też wynik (mówi, że DG optymalizuje coś innego niż
  separacja — ciekawe samo w sobie).
- Reżim `mc_active` zakotwiczony w Scharfman 2016 (netto wpływ MC na GC przeważnie
  hamujący, przez napędzanie interneuronów). **To jest otwarta kwestia #1
  z `doktorat_plan.md` — tutaj dostaje procedurę**: kalibrujemy `drive`/`gain`/
  `brake` tak, by netto wpływ MC na GC był hamujący w spoczynku, zgodnie z danymi HMC.
- Częstotliwości FS w paśmie gamma vs literatura (obietnica obserwowalności).

**Falsyfikowalne przewidywania do zaproponowania eksperymentatorom** (sekcja
Discussion, bardzo lubiana przez PLOS CB):
1. Częściowe wyciszenie MC (chemogenetyka) powinno *poprawić* separację przy
   niskim R_in i *pogorszyć* przy wysokim — bo MC jest motywem warunkowym.
2. Blokada tonicznego GABA-A (δ-GABA_A) i blokada fazowego powinny dawać
   przeciwne przesunięcia na osi NDP/SF, mimo podobnej zmiany FR.
3. Po utracie MC separacja powinna wracać w skali dziesiątek minut, jeśli
   homeostaza wewnętrzna działa — mierzalne jako powolny dryf rheobase GC.

---

## 5. Open Science i reprodukowalność (FAIR)

PLOS CB egzekwuje to twardo (Data Availability + Code Availability jako warunek
przyjęcia). Plan:

```
snn-dg-regulation/                     # publiczne repo (wydzielone z tego)
├── CITATION.cff, codemeta.json        # metadane maszynowo czytelne (F)
├── LICENSE                            # kod: BSD-3-Clause
├── LICENSE-DATA                       # dane/figury: CC-BY-4.0
├── README.md                          # + badge DOI Zenodo
├── analysis_plan.md                   # preregistracja (data commita = dowód)
├── env/
│   ├── environment.yml, conda-lock.yml
│   ├── Dockerfile                     # obraz z Brian2 + zależnościami
│   └── apptainer.def                  # Apptainer/Singularity pod HPC
├── configs/                           # KAŻDY przebieg opisany plikiem YAML
│   └── e1_regime_map.yaml, ...
├── dgnet/                             # pakiet instalowalny (dawne dg_core)
│   ├── params.py circuit.py patterns.py metrics.py control.py fit_neurons.py
│   └── io_madar.py                    # wczytanie danych + eksport NWB
├── experiments/  e1_… e7_…            # skrypty, każdy z --preset quick|full
├── analysis/                          # skrypty analityczne, jeden na figurę
├── tests/                             # pytest: regresja modelu, metryki, pułapki
└── Makefile / Snakefile               # `make figures` odtwarza CAŁY artykuł
```

**Zasady operacyjne:**
- **Determinizm**: każdy przebieg zapisuje `{git_sha, config_hash, seed, wersje
  bibliotek}` w nagłówku pliku wynikowego. Brak tego = wynik nie idzie do artykułu.
- **Konfiguracja plikiem, nie flagami** — YAML w `configs/` jest jednocześnie
  dokumentacją eksperymentu i wpisem w Supplementary.
- **Dane w trzech warstwach na Zenodo** (osobny, wersjonowany DOI): L1 surowe
  wyniki symulacji (Parquet, kilka GB), L2 metryki zagregowane (CSV, MB), L3
  figury + dane do figur. Recenzent reprodukuje figury z L2 w minutę.
- **Model osobno**: depozyt w **ModelDB** (i/lub Open Source Brain) — recenzenci
  comp-neuro tego szukają; eksport przez PyNN/NeuroML jako opcja.
- **Dane pochodne z `dataset/`**: kod Madara jest na MIT (sprawdzone lokalnie:
  `dataset/PatSepSpikeTrains/LICENSE`), dane na BioStudies S-BSST219 — **nie
  redystrybuujemy surowych nagrań**, publikujemy skrypt pobierający + nasze
  pochodne (wykryte spajki w NWB) z jawną atrybucją, po sprawdzeniu warunków
  licencji BioStudies.
- **CI (GitHub Actions)**: `pytest` + preset `quick` każdego eksperymentu + linter
  na pułapki modelu (gołe `N_GC=`, brak maski ważności, MI bez korekcji).
- **Kontener na HPC**: ten sam `.sif` na Aresie i lokalnie → koniec z „u mnie
  działa". Osobny `BRIAN2_CACHE_DIR` per task SLURM (znany problem, §7
  `doktorat_plan.md`).

---

## 6. Oś czasu 12 miesięcy (kwartały, z bramkami go/no-go)

### Q1 (m. 1–3) — dane, metryki, kalibracja neuronów
- **M1.1** `io_madar.py`: Axograph → Neo → NWB; detekcja spajków; **eksport
  bodźców z `Protocols/`** jako wejście modelu.
- **M1.2** `metrics.py`: R / NDP / SF / SPIKE + burstiness; **test zgodności
  z MATLABem** Madara na 20 nagraniach (tolerancja < 1%).
- **M1.3** `fit_neurons.py`: dopasowanie Izhikevicza do CCIV, per typ komórki,
  z rozkładami (heterogeniczność).
- **M1.4** `analysis_plan.md` — preregistracja H1–H5 i metryki pierwszorzędowej.
- **Bramka G1:** metryki zgodne z implementacją referencyjną ORAZ f–I w granicach
  danych dla ≥80% komórek. Bez tego nie ruszamy siatek — inaczej policzymy 100 tys.
  symulacji nieporównywalnych z danymi.

### Q2 (m. 4–6) — mapa reżimów i atrybucja (rdzeń Wyników)
- **M2.1** E1 na Aresie (mapa reżimów, pełna bateria metryk) + maska ważności.
- **M2.2** E2 (Shapley dla wszystkich metryk) — figura „który motyw tworzy okno".
- **M2.3** E6 (skalowanie N_GC do 2000–5000) — test kodowania ekspansyjnego.
- **M2.4** E3 + surrogat L3: indeksy Sobola, blokowe CV, analiza sloppiness.
- **M2.5** Suwak `W FS→HMC` + panel obserwowalności w `interactive_dg.py`
  (deliverable narzędziowy).
- **Bramka G2:** H1 potwierdzona (niemonotoniczność z CI, poza maską artefaktów)
  ORAZ H2 potwierdzona na pełnej siatce. Jeśli nie — pivot na wariant „C" tytułu
  (robustness/padaczka) z K3 jako wynikiem głównym.

### Q3 (m. 7–9) — kontroler adaptacyjny i perturbacje
- **M3.1** `control.py`: IP + iSTDP + SS; testy jednostkowe stabilności.
- **M3.2** E4 + E5: porównanie wielkości kontrolowanych (H3), uogólnienie poza
  reżim strojenia.
- **M3.3** K3 (utrata MC) + K4 (gabazyna) + K5 (neurogeneza) + K7 (perturbacje
  wejścia).
- **M3.4** **V4 — predykcja gabazynowa** z zapieczętowaną predykcją przed
  odsłonięciem „after".
- **Bramka G3:** kontroler odzyskuje separację po ≥2 z 3 perturbacji ORAZ zbiega
  do punktu zgodnego z optimum offline (H4).

### Q4 (m. 10–12) — walidacja, figury, manuskrypt
- **M4.1** V2/V3 (odpowiedzi na rzeczywiste bodźce, uporządkowanie typów komórek).
- **M4.2** V5 (kotwica in vivo, kalibracja `mc_active` do Scharfmana).
- **M4.3** Zamrożenie wyników: Zenodo (kod + dane L1–L3), ModelDB, kontener.
- **M4.4** Figury (§7) + manuskrypt; preprint na bioRxiv **przed** submisją.
- **M4.5** Submisja do PLOS Comp Biol + gotowy plan odpowiedzi na trzy
  najbardziej prawdopodobne zarzuty (§8).

*Bufor:* Q1 i Q3 są najbardziej ryzykowne (dane + nowy kod wolnej dynamiki).
12 miesięcy wystarcza tylko przy założeniu, że E1–E3 lecą na HPC bez babysittingu —
czyli sharding i kontener muszą działać do końca Q1.

---

## 7. Plan figur (kotwica dla zakresu — jeśli figura nie ma miejsca, eksperyment nie ma priorytetu)

| Fig | treść |
|---|---|
| **1** | Model: schemat obwodu z rozdzielonymi kanałami + kalibracja L0 (f–I model vs CCIV, 4 typy komórek) + przykładowe rastry |
| **2** | **Okno funkcjonalne**: separacja (NDP/SF/R) vs poziom aktywności; niemonotoniczność; panel kontrolny FR/frakcja aktywnych; maska artefaktów |
| **3** | **Hamulec MC tworzy okno**: `W_FS_HMC` × napęd; bistabilność przy 0; reżim pośredni przy 2 |
| **4** | **Atrybucja**: Shapley per motyw dla każdej metryki; mapa dominacji w płaszczyźnie (R_in × tempo); interakcja FB×MC |
| **5** | **Co jest regulowane**: 3 wielkości kontrolowane × 3 mechanizmy; uogólnienie poza reżim strojenia (H3) |
| **6** | **Odzysk po perturbacji**: dezinhibicja i utrata MC; trajektorie w płaszczyźnie (aktywność × separacja); kontroler odnajduje optimum offline |
| **7** | **Walidacja**: (a) model vs dane na bodźcach Madara; (b) uporządkowanie typów komórek; (c) **predykcja gabazynowa out-of-sample** |
| S1–S6 | sloppiness/Sobol, skalowanie N_GC, kontrola MI, modele zerowe, wrażliwość na dopasowanie L0, pełne siatki |

---

## 8. Ryzyka, pozycjonowanie wobec literatury, kontrargumenty

**Najbliższa literatura — trzeba się wobec niej jawnie ustawić w Intro:**
- **Yim, Hanuschkin, Wolfart (2015)** — *intrinsic rescaling* GC przywraca separację
  w warunkach epileptycznych. **To jest najbliższe prior art dla H4.** Nasza
  różnica: kontroler ONLINE (zamknięta pętla, nie jednorazowe przeskalowanie),
  porównanie *wielkości kontrolowanej* (H3), rola pętli MC jako mechanizmu okna,
  walidacja na danych z tym samym bodźcem. Jeśli tego nie rozgraniczymy — desk reject.
- **Braganza, Mueller-Komorowska, Beck (2020)** — obwód feedback i separacja
  zależna od częstotliwości. Nasza różnica: MC + regulacja adaptacyjna + kody NDP/SF.
- **Madar, Ewell & Jones (2019, PLOS CB)** — eksperymentalny towarzysz naszego
  modelu. Ustawiamy się jako **model wyjaśniający ich obserwacje**, nie jako
  konkurencja. Bardzo dobra pozycja dla tego samego czasopisma.
- **Santhakumar / Soltesz** — model DG w padaczce; nasza różnica: nie liczymy
  napadów, tylko regulację punktu pracy separacji.

**Ryzyka i mitygacje:**

| ryzyko | prawdopodobieństwo | mitygacja |
|---|---|---|
| Model 3-typowy (GC/FS/HMC) uznany za zbyt zredukowany | średnie | jawne uzasadnienie z Hippocampome + analiza wrażliwości + argument, że redukcja jest warunkiem siatki 100 tys. symulacji |
| Izhikevich uznany za zbyt abstrakcyjny | średnie | **V1 (dopasowanie do CCIV) rozbraja to niemal całkowicie** — to główny powód, by zrobić L0 |
| H4 „za łatwa" (homeostaza oczywiście stabilizuje) | **wysokie** | ciężar dowodu przenieść na **H3** (co jest regulowane) i na E5 (uogólnienie) — to jest niebanalne |
| Predykcja gabazynowa nie trafi | średnie | to nadal wynik, o ile preregistrowany: mówi, że fazowe hamowanie GC nie tłumaczy efektu → wskazuje na toniczne/na sieć. Preregistracja zamienia porażkę w wynik |
| Zbyt duży zakres na 12 miesięcy | **wysokie** | plan figur (§7) jest kontraktem; E6 i K5 są pierwsze do wycięcia |

---

## 9. Co to znaczy dla TEGO repo — konkretne decyzje

### 9.1 Promować
- **Wynik `FS→HMC`** → Figura 3, a nie „detal kierunku 4".
- **Kierunek 4 (Shapley)** → Figura 4; maszyneria gotowa, brakuje tylko baterii metryk.
- **Skalowanie N_GC** → Suplement S2 (nie główny wątek — sam w sobie nie jest nowy).

### 9.2 Uśmiercić / odłożyć jawnie
- **Kierunek 1A** (klasyfikator liniowy) — zamknięty; wchodzi do artykułu jako
  jedno zdanie w Discussion („decorrelation does not imply linear decodability"),
  ewentualnie panel suplementu. Nie inwestować więcej.
- **Kierunek 1B** (pojemność) — odłożyć do po G2; wymaga N_GC ≥ 2000, a wtedy
  i tak lepiej wpiąć go jako Fig. S „downstream consequence".
- **Kierunek 2** (forgetting) — poza zakresem tego artykułu.
- **NEST** — nie ruszać (drugie źródło prawdy modelu).

### 9.3 Zbudować (kolejność wykonania, pierwsze 3 miesiące)

```
experiments/dg_core/io_madar.py      # NOWY  — Axograph→Neo→NWB; bodźce z Protocols/
experiments/dg_core/metrics.py       # ROZBUDOWA — NDP, SF, SPIKE, MI+korekcja, gamma, koszt
experiments/dg_core/fit_neurons.py   # NOWY  — Izhikevich ← CCIV, per typ, rozkłady
experiments/dg_core/control.py       # NOWY  — IP / iSTDP / synaptic scaling
experiments/dg_core/circuit.py       # ZMIANA — pp_source='madar'; K_GC per-neuron; gaba_block
experiments/analysis_plan.md         # NOWY  — preregistracja H1–H5
tests/                               # NOWY  — regresja modelu + linter pułapek
interactive_dg.py                    # ZMIANA — suwak W FS→HMC + panel obserwowalności
```

**Pierwszy krok, który zrobiłbym jutro:** `io_madar.py` + odczyt jednego pliku
`dataset/PatchPatSep2s_Public/PatchPatSep2s_Public/Protocols/10Hz/10Hz_R0.750_CorrelatedPoisson.prt.axgx`
i podanie go jako wejścia PP do `dg_core.circuit.simulate()`. To jeden dzień pracy,
a zmienia status projektu z „model z syntetycznymi wzorcami" na „model napędzany
tymi samymi bodźcami, co eksperyment" — czyli odblokowuje V2, V3 i V4 naraz.

### 9.4 Trzy pułapki modelu — nadal obowiązują
`DGConfig.scaled(N)` zamiast gołego `N_GC=`; dwa reżimy MC (`mc_inert`/`mc_active`);
maska „separacja czy wyciszenie" na każdym panelu. Przy generowaniu datasetu dla
surrogatu ML (E3) złamanie którejkolwiek z nich oznacza, że model ML nauczy się
artefaktu — a potem inverse design zoptymalizuje pod ten artefakt.

---

## 10. Otwarte pytania do rozstrzygnięcia przed startem Q1

1. **Metryka pierwszorzędowa**: NDP przy 100 ms czy MI(klasa; kod)? Propozycja:
   NDP (porównywalna z Madarem), MI jako współrzędna druga. Do preregistracji.
2. **Punkt nastawy ρ₀**: strojony jako wolny parametr czy wzięty z danych in vivo?
   Mocniejsza wersja: wzięty z danych i pokazany, że pokrywa się z optimum offline.
3. **Czy CA3 wchodzi do modelu?** Dane są. Za: zamyka łuk „separacja→completion".
   Przeciw: podwaja zakres. Propozycja: **nie w tym artykule**, ale CA3 z danych
   używamy jako punkt odniesienia w V3.
4. **Autorstwo** — przy trójce (Błasiak / Wielgosz / Jakub) ustalić przed Q2, bo
   Fig. 5–6 to naturalnie rdzeń doktoratu.
5. **Kalibracja `mc_active`** (drive=16, gain=×20 są dziś arbitralne) — §4 V5 daje
   procedurę, ale trzeba potwierdzić z prof. Błasiak, czy „netto hamujący wpływ MC
   na GC w spoczynku" to właściwe kryterium.
