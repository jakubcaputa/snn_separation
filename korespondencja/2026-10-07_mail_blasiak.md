# Draft maila do prof. Anny Błasiak — 2026-10-07

*Ponowienie maila z 2026-09-11. Treść pytań: STATUS.md sek. 2 (B1–B4) i sek. 3.4.*
*⚠️ DRAFT — do przeczytania i poprawienia przed wysłaniem.*

---

**Temat:** Model DG — status, pytania kalibracyjne i prośba o kierunek

Pani Profesor,

wracam do maila z 11 września. Poniżej krótko, gdzie jesteśmy, te same trzy
pytania — bez nich nie domkniemy kalibracji punktu pracy modelu — i jedno nowe.

**Gdzie jesteśmy.** Model DG działa, pełne siatki policzone na klastrze. Wyniki
wyszły inaczej, niż zakładaliśmy: hipoteza, że separacja wzorców ma optimum przy
pośrednim poziomie aktywności i że steruje tym siła hamowania, **nie potwierdziła
się**. Powód okazał się pomiarowy — standardowa miara separacji (spadek korelacji
między wzorcami) rośnie sama z siebie, gdy sieć cichnie, więc każde wzmocnienie
hamowania „poprawia" wynik z przyczyny niezwiązanej z obwodem. Gdy aktywność
trzymamy stałą, hamowanie fazowe nie zmienia separacji wcale.

Jedyny efekt samego obwodu, jaki widzimy, dotyczy regulacji aktywności: przy
aktywnych mossy cells sieć potrafi przejść w drugi stan, w którym strzela prawie
cała populacja komórek ziarnistych (przypomina to napad), a silniejsze hamowanie
fazowe temu zapobiega. Bez mossy cells to się nie zdarza. Test na nowych danych
pokazał jednak, że przy naszych obecnych wagach jest to rzadkie, a jak często
się zdarza, zależy od siły pobudzenia mossy cells → komórki ziarniste, którą
dobraliśmy sami, nie z danych.

**Trzy pytania z września i jedno nowe:**

1. **Udział hamowania tonicznego w GC.** W modelu toniczne odpowiada za ~74%
   hamowania komórek ziarnistych, fazowe FS→GC za resztę. Ta proporcja jest
   odziedziczona po wcześniejszych ustawieniach, nie dobrana świadomie. Czy ~74%
   jest realistyczne? To nie jest wybór jednej liczby — ten sam parametr ustala
   jednocześnie próg pobudliwości i potencjał spoczynkowy.

2. **Częstotliwość bazowa FS.** Model daje ~46 Hz, co wydaje się nam zawyżone.
   Przyczyna jest strukturalna: interneurony nie miały w modelu żadnego hamowania
   synaptycznego. Dodanie wzajemnego hamowania FS→FS obniża wynik do ~28 Hz.
   Jaka wartość jest fizjologiczna i jak silna powinna być ta pętla?

3. **Do którego reżimu wejścia kalibrujemy — in vitro czy in vivo?** To pytanie
   uważamy za najważniejsze. Waga dobrana protokołem pulsowym z danych Madara
   (tło 40 Hz), użyta w sieci przy napędzie 400 Hz, daje komórki ziarniste
   strzelające 22 Hz zamiast oczekiwanych 2–6 Hz. Dziesięciokrotna różnica
   reżimu — jedna waga nie obsłuży obu. Który ma być warunkiem kontrolnym?

4. **Siła pętli mossy cells → komórki ziarniste (nowe).** Od niej zależy, czy
   opisany wyżej stan „zapłonu" jest realistyczny: przy naszych wagach zdarza się
   w kilku procentach symulacji, przy wadze o połowę większej — w do 40%. Czy jest
   jakakolwiek liczba, na której można to oprzeć (amplituda EPSP MC→GC, liczba
   mossy cells kontaktujących jedną komórkę ziarnistą, częstotliwość MC in vivo)?

Drobne, przy okazji: z adnotacji w danych Madara wychodzi τ_m ≈ 3 ms dla komórek
ziarnistych, a nie 10–50 ms. Czy to różnica definicji (opór wejściowy vs błonowy)?

**Jak Pani Profesor może nam najbardziej pomóc:** jedno–dwa zdania na każde
z czterech pytań w zupełności wystarczą, żeby odblokować kalibrację. Jeśli wygodniej
— chętnie umówimy krótką rozmowę.

**Dwa pytania otwarte, na których opinii bardzo nam zależy:**

- **Czy warto opublikować samo narzędzie?** Zbudowaliśmy interaktywną aplikację
  (przeglądarka, suwaki na wszystkich parametrach biofizycznych, podgląd macierzy
  korelacji wejście/wyjście i bilansu hamowania na żywo), z myślą o tym, żeby
  eksperymentator mógł sam zadawać modelowi pytania bez czytania kodu. Mamy
  gotowy draft artykułu opisującego narzędzie i mechanizm. Czy widzi Pani
  Profesor dla czegoś takiego odbiorców?

- **W którą stronę pchnąć dalszy research?** Skoro pierwotna hipoteza upadła,
  rozważamy dwa kierunki: (a) artykuł metodologiczny o tym, jak nie mierzyć
  separacji wzorców, oraz (b) **regulacja aktywności i padaczka skroniowa** —
  stopniowa utrata mossy cells albo hamowania koszykowego, czyli spór „dormant
  basket cell" kontra „irritable mossy cell". Maszyneria do (b) jest gotowa, ale
  to, czy ma sens, zależy od pytania 4 — i to pytanie w całości biologiczne, więc
  Pani zdanie jest tu dla nas decydujące. Na razie skłaniamy się, żeby najpierw
  napisać (a).

Z wyrazami szacunku,
Jakub Caputa
