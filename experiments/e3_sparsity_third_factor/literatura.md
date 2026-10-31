# E3 — literatura

*Przeniesione 2026-10-31 z README.md (sek. 10 bez zmian; sek. 13 zaktualizowana o E3.5–E3.9h).*

## 10. Przegląd literatury (krok 0, 2026-10-12)

Szybki przegląd (kilkanaście wyszukiwań, nie przegląd systematyczny). **Nie
znaleźliśmy pracy, która robi dokładnie E3**: jeden globalny skalar pobudliwości
(analog tonicznego GABA) ustawiający *poziom* rzadkości w pętli zamkniętej, sterowany
nowością, w SNN z lokalną regułą trójczynnikową czytnika i z kontrolą
`fixed_matched`. Każdy składnik osobno ma jednak bliskie odpowiedniki.

| praca | co robi | czym się różni od E3 | wpływ na plan |
|---|---|---|---|
| **FlyModel** — Shen, Dasgupta & Navlakha, *Neural Comput.* 2023 ([arXiv 2107.07617](https://arxiv.org/abs/2107.07617)) | losowa ekspansja + **stałe** k-WTA (~5%) + uczenie tylko synaps aktywnych KC do klasy docelowej; class-incremental MNIST-20 (0.86) i CIFAR-100; bije EWC/GEM | nie-spajkowa, wejście = cechy z LeNet/ResNet, nie piksele; **rzadkość stała i niebadana systematycznie**; brak nowości | nasze warunki ze stałym `f` to w praktyce „spajkowy FlyModel” — dodany warunek `kwta_fly`; E3.1 (przemiatanie `f`) uzupełnia lukę, której nie zbadali |
| **Nm-SNN** — Hammouamri, Masquelier & Wilson, *TMLR* 2022 ([link](https://mlanthology.org/tmlr/2022/hammouamri2022tmlr-mitigating)) | **ewoluowana** sieć neuromodulacyjna ustawia **progi poszczególnych neuronów** SNN na podstawie aktywności poprzedniej warstwy; class-incremental; mniej zapominania niż przy stałym progu | per-neuron (wybiera *które*), ewoluowana, nie nowość; brak kontroli dopasowanej rzadkości | **najbliższy konkurent.** Sprawdzone w kodzie ([github.com/Thvnvtos/Nm-SNN](https://github.com/Thvnvtos/Nm-SNN), `network.py`, `nm.py`): konwolucyjna SNN uczona **surrogate gradient** (SpikingJelly); sieć neuromodulacyjna (2 warstwy LIF + tanh, ewoluowana) czyta mapy cech i w każdym kroku czasu dodaje **osobny przyrost progu dla każdego z 256 neuronów warstwy FC**; zbiór DVS128 Gesture; porównanie: stały próg, Nm-SNN, EWC. W kodzie **nie ma kontroli ani raportu średniej aktywności**. Różni się od E3: per-neuron, ewoluowane, backprop, sygnał z wejścia, nie z nowości/nagrody |
| CATFormer — *PMLR* 2026 ([link](https://proceedings.mlr.press/v308/nagabhushana26a.html)) | progi zależne od kontekstu w spajkowym transformerze | uczone, per-neuron, backprop | cytować jako kierunek „pobudliwość zamiast wag” |
| Lässig i in., *Biol. Cybern.* 2023 ([arXiv 2212.04316](https://arxiv.org/abs/2212.04316)) | WTA z rzadkością narastającą w trakcie ustalania, sprzężenie zwrotne odgórne, task-free Split-MNIST | rzadkość docelowa stała; nie nowość | cytować; ich wynik class-incremental jako punkt odniesienia |
| Controlled Forgetting — Allred & Roy, *Front. Neurosci.* 2020 ([PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6999159/)) | nowość wyzwala „dopaminową” modulację **plastyczności** w STDP SNN | moduluje plastyczność, nie rzadkość | to biologiczny odpowiednik naszego `3f_lr` — cytować przy H-E3d |
| Dynamic gain neuromodulation — Rodriguez-Garcia i in., arXiv 2025 ([2507.14056](https://arxiv.org/abs/2507.14056)) | globalne „noradrenergiczne” wzmocnienie przy zmianie zadania, ANN | wzmocnienie, nie rzadkość; ANN | cytować; bliskie ideowo czynnikowi A |
| Sparse Distributed Memory is a Continual Learner — Bricken i in., *ICLR* 2023 ([arXiv 2303.11934](https://arxiv.org/abs/2303.11934)) | top-k jako mechanizm uczenia ciągłego | stałe k | cytować |
| **Pérez-Montoyo i in., *PLoS Biol.* 2026** ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13506102/)) | myszy + model (rate, k%-WTA): **słabsze hamowanie w DG przy kodowaniu poprawia późniejszą dyskryminację, ale zwiększa interferencję; silniejsze stabilizuje kosztem czułości** | biologia; poziom hamowania stały w warunku, nie sterowany nowością; brak ML | **mocna motywacja biologiczna**, ale też **pytanie o kierunek** — patrz niżej |
| Noradrenalina rzadkuje kod GC (*Commun. Biol.* 2026); nowo narodzone GC zwiększają rzadkość przy nowości (*Nat. Neurosci.* 2022, [link](https://www.nature.com/articles/s41593-022-01176-5)) | biologia: nowość → rzadszy kod | — | wspiera kierunek „nowość → rzadziej” |
| Meeter, Murre & Talamini, *Hippocampus* 2004 | nowość → ACh → przełączenie zapis/przywoływanie | model hipokampa, nie ML | cytować przy wariancie dwufazowym |

### Wnioski dla E3

1. **Nowość pomysłu stoi na połączeniu, nie na składnikach.** Trzy elementy, których
   w tej literaturze nie znaleźliśmy: (i) systematyczne przemiatanie `f` z miarą
   funkcjonalną obok dekorelacji (E3.1), (ii) **kontrola `fixed_matched`** —
   żadna z prac nie odróżnia „modulacja pomaga” od „trafiono lepszą średnią
   rzadkość”, (iii) bezpośrednie porównanie „nowość → rzadkość” z „nowość →
   plastyczność” (`3f_lr`, odpowiednik Allred & Roy) w tym samym modelu.
2. **Kierunek modulacji nie jest oczywisty.** Pérez-Montoyo 2026 pokazuje, że
   *słabsze* hamowanie przy kodowaniu podobnych doświadczeń poprawia ich późniejsze
   rozróżnianie (kosztem interferencji), a noradrenalina i nowe GC rzadkują kod przy
   nowości. Dlatego E3.3 testuje oba kierunki: `mod_novelty` (nowość → rzadziej)
   i `mod_novelty_inv` (nowość → gęściej). Hipoteza H-E3c dotyczy pierwszego;
   wynik odwrotny też jest informatywny.
3. **FlyModel to obowiązkowy punkt odniesienia** (`kwta_fly`). Jego wynik (0.86 na
   MNIST-20) dotyczy cech z LeNet, nie pikseli — przy surowych pikselach należy
   spodziewać się niższych liczb, więc porównujemy warunki między sobą, nie z ich
   tabelą.
4. **Brama przed kodem — przeszła.** Mechanizm Nm-SNN jest inny (per-neuron,
   ewoluowany, backprop, bez nowości i bez kontroli aktywności), więc E3 nie wymaga
   przepozycjonowania.

### Szczegóły z pełnych tekstów (PDF w `similiar_papers/`, dodane 2026-10-12)

- **Nm-SNN** (`184_Mitigating_Catastrophic_Fo-sim2.pdf`): konwolucyjna SNN
  wstępnie wytrenowana i zamrożona; uczona (surrogate gradient) jest tylko warstwa
  FC i wyjście. Sieć neuromodulacyjna (ewoluowana, ~600 generacji) czyta impulsy
  ostatniej warstwy konwolucyjnej i co krok zmienia progi neuronów FC. Każde
  zadanie = **jedna klasa**, 20 lub 50 kroków SGD; zbiory DVS128 Gesture, EMNIST
  letters, MNIST; porównanie: stały próg, Nm-SNN, EWC. **Sami raportują, że Nm-SNN
  ma ~54% mniej impulsów niż SNN ze stałym progiem i równiej rozłożoną
  aktywność** — i interpretują to jako mechanizm. Nie mają warunku ze stałym progiem
  dobranym do tej samej średniej aktywności, więc nie da się odróżnić „modulacja
  pomaga” od „niższa aktywność pomaga”. To jest dokładnie pytanie `fixed_matched`.
- **FlyModel** (`SDN23-sim1.pdf`): MNIST-20 = MNIST + Fashion-MNIST, 10 zadań po
  2 klasy, wejście = 84 cechy z LeNet5, m = 3200 KC (40×), k-WTA z `l = m/20`
  aktywnymi (5%), reguła `w[target] += β·φ` (β = 0.01), bez osłabiania; ablacja
  porównuje m.in. wariant z `w[predict] −= β·φ` (perceptron). Rzadkości nie przemiatają.
- **Allred & Roy 2020** (`fnins-14-00007.pdf`): nienadzorowane STDP w jednej
  warstwie; nowość wyzwala wymuszone odpalenie i lokalnie zwiększoną plastyczność
  („dopamina”); MNIST z rozłącznymi klasami, 95.24%. Odpowiednik `3f_lr`, ale
  nienadzorowany.
- **Pérez-Montoyo i in. 2026** (`journal.pbio.3003956.pdf`): hamowanie w modelu
  to E%-max WTA (de Almeida, Idiart & Lisman) — aktywne są neurony w k% od maksimum;
  poziom k% stały w obrębie warunku. Słabsze hamowanie przy kodowaniu → lepsza
  późniejsza dyskryminacja podobnych wejść (zwłaszcza przy podobieństwie 0.8),
  silniejsze → stabilniejsze reprezentacje.

---

---

## 13. Zderzenie z literaturą (sek. 10)

| praca | co twierdzi | co pokazuje E3 |
|---|---|---|
| **FlyModel** (Shen, Dasgupta, Navlakha 2023) | rzadka losowa ekspansja + reguła „tylko klasa docelowa” daje uczenie ciągłe bez zapominania | potwierdzamy na impulsowej wersji z pikseli (k-WTA 5%: ACC 0.65, BWT −0.06 na Split-MNIST 5×2). Dodajemy to, czego nie zbadali: przemiatanie rzadkości (E3.1) — przy uczeniu statycznym optimum jest przy f ≈ 10–25%, nie przy 5% — i to, że **przy czytniku, który osłabia wagi, rzadkość sama nie chroni przed zapominaniem** (BWT −0.43 … −0.97) |
| **Nm-SNN** (Hammouamri i in. 2022) | ewoluowana modulacja progów zmniejsza zapominanie; ich sieć ma ~54% mniej impulsów | **nasz wynik ostrzega przed ich interpretacją:** stałe f dobrane do średniej (`fixed_matched`) było lepsze od modulacji w kierunku „rzadziej” (H-E3c). Bez takiej kontroli zysk z modulacji nie odróżnia się od zysku z niższej aktywności. Ich mechanizm jest inny (progi per neuron, ewoluowane, bez sygnału nowości), więc ich wyniku nie obalamy — pokazujemy tylko, że brakująca kontrola może odwrócić wniosek |
| **Allred & Roy 2020** | nowość → silniejsza plastyczność („dopamina”) pomaga w uczeniu ciągłym STDP | w naszym modelu `3f_lr` (nowość → tempo uczenia) **nie pomaga** względem `fixed_matched` (izh × R-STDP: BWT −0.64 vs −0.42); ich układ jest nienadzorowany i z innym mechanizmem rekrutacji neuronów, więc to nie jest bezpośrednie obalenie |
| **Pérez-Montoyo i in. 2026** | słabsze hamowanie w DG przy kodowaniu podobnych doświadczeń poprawia ich późniejsze rozróżnianie; silniejsze stabilizuje kosztem czułości | **kierunek zgodny z naszym wynikiem:** nowość → słabsze hamowanie (gęstszy kod) zapomina mniej niż nowość → silniejsze, we wszystkich 8 porównaniach; ale test potwierdzający względem stałego f o tej samej średniej przeszedł tylko w części konfiguracji (sek. 12a). **Uzupełnienie (E3.6x):** na zadaniu separacji w modelu skrawka „nowość → gęściej” pomaga właśnie przy podobnych wzorcach (R_in 0.9), a przy mało podobnych (0.5) pomaga kierunek odwrotny — zgodnie z ich tezą, że słabsze hamowanie służy rozróżnianiu podobnych doświadczeń |
| Noradrenalina / nowe GC rzadkują kod przy nowości (2022, 2026) | biologiczne „nowość → rzadziej” | przy czytnikach z osłabianiem taki kierunek **szkodzi**; przy czytniku bez osłabiania (rgate, E3.5) i przy mało podobnych wzorcach (E3.6x) **pomaga** — czyli „rzadziej przy nowości” jest korzystne, gdy plastyczność jest tylko wzmacniająca |

**Co z tego wynika dla pozycjonowania (zaktualizowane 2026-10-31, po E3.5–E3.9h):**
wcześniejszy wniosek „pomysł nowość → rzadszy kod nie działa” (2026-10-13) jest nieaktualny.
Teza w wersji warunkowej jest poparta: kierunek korzystnej modulacji wyznacza reguła uczenia
(osłabianie tak/nie, E3.5, E3.8) i podobieństwo wzorców (E3.6x), a przy regułach z osłabianiem
działa przez ograniczanie przewagi nowych klas (E3.9) — co łączy E3 z literaturą o korekcji
przechylenia w class-incremental (BiC — Wu i in. 2019; LUCIR — Hou i in. 2019; WA — Zhao i in.
2020), której tu jeszcze nie porównaliśmy. Wyniki metodologiczne bez zmian: (1) optimum
rzadkości dla uczenia istnieje, a dekorelacja go nie widzi (H-E3a, do f = 90%); (2) kontrola
o dopasowanej średniej rzadkości zmienia wniosek o modulacji, czego brakuje w opublikowanych
pracach (Nm-SNN); (3) reguła czytnika waży więcej niż rzadkość (E3.4).
