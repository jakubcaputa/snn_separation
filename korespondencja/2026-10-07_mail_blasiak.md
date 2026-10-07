# Draft maila do prof. Anny Błasiak — 2026-10-07

*Ponowienie maila z 2026-09-11. Treść pytań: STATUS.md sek. 2 (B1–B3) i sek. 3.4.*
*⚠️ DRAFT — do przeczytania i poprawienia przed wysłaniem.*

---

**Temat:** Model DG — status, trzy pytania kalibracyjne i prośba o kierunek

Pani Profesor,

wracam do maila z 11 września. Poniżej krótko, gdzie jesteśmy, i te same trzy
pytania — bez nich nie domkniemy kalibracji punktu pracy modelu.

**Gdzie jesteśmy.** Model DG działa, pełne siatki policzone na klastrze. Wyniki
wyszły inaczej, niż zakładaliśmy: hipoteza, że separacja wzorców ma optimum przy
pośrednim poziomie aktywności i że steruje tym siła hamowania, **nie potwierdziła
się**. Powód okazał się pomiarowy — standardowa miara separacji (spadek korelacji
między wzorcami) rośnie sama z siebie, gdy sieć cichnie, więc każde wzmocnienie
hamowania „poprawia" wynik z przyczyny niezwiązanej z obwodem. Na plusie:
podział zasług między motywami hamowania jest realny, a **mossy cells wychodzą
jako motyw warunkowy** — same pogarszają separację, ale w parze z hamowaniem dają
największy wkład ze wszystkich motywów.

**Trzy pytania (te same co we wrześniu):**

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

Drobne, przy okazji: z adnotacji w danych Madara wychodzi τ_m ≈ 3 ms dla komórek
ziarnistych, a nie 10–50 ms. Czy to różnica definicji (opór wejściowy vs błonowy)?

**Jak Pani Profesor może nam najbardziej pomóc:** jedno–dwa zdania na każde
z trzech pytań w zupełności wystarczą, żeby odblokować kalibrację. Jeśli wygodniej
— chętnie umówimy krótką rozmowę.

**Dwa pytania otwarte, na których opinii bardzo nam zależy:**

- **Czy warto opublikować samo narzędzie?** Zbudowaliśmy interaktywną aplikację
  (przeglądarka, suwaki na wszystkich parametrach biofizycznych, podgląd macierzy
  korelacji wejście/wyjście i bilansu hamowania na żywo), z myślą o tym, żeby
  eksperymentator mógł sam zadawać modelowi pytania bez czytania kodu. Mamy
  gotowy draft artykułu opisującego narzędzie i mechanizm. Czy widzi Pani
  Profesor dla czegoś takiego odbiorców?

- **W którą stronę pchnąć dalszy research?** Skoro pierwotna hipoteza upadła,
  rozważamy trzy kierunki: (a) artykuł metodologiczny o tym, jak nie mierzyć
  separacji wzorców, (b) mossy cells jako motyw warunkowy, (c) **stopniowa utrata
  mossy cells jako model padaczki skroniowej** — co rozstrzygałoby spór „dormant
  basket cell" kontra „irritable mossy cell". Wariant (c) wydaje nam się
  najmocniejszy i maszyneria jest gotowa, ale to pytanie w całości biologiczne
  i Pani zdanie jest tu dla nas decydujące.

Z wyrazami szacunku,
Jakub Caputa
