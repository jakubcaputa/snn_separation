# Draft maila do prof. Anny Błasiak — 2026-10-07

*Ponowienie maila z 2026-09-11. ⚠️ DRAFT — do przeczytania przed wysłaniem.*
*Pod podpisem: notatki dla mnie (nie wysyłać) — skąd każde pytanie i sprawdzenie liczb.*

---

**Temat:** Model DG — status i cztery krótkie pytania

Pani Profesor,

wracam do maila z 11 września, z krótkim statusem i pytaniami, bez których nie
domkniemy kalibracji modelu.

**Gdzie jesteśmy.** Hipoteza, że separacja wzorców ma optimum przy pośredniej
aktywności sterowanej hamowaniem, się nie potwierdziła. Standardowa miara
separacji rośnie sama, gdy sieć cichnie, a przy stałej aktywności hamowanie
fazowe nie zmienia jej wcale. Jedyny efekt samego obwodu, jaki widzimy: przy
aktywnych mossy cells sieć potrafi „zapalić się" niemal w całości (stan
przypominający napad), a hamowanie fazowe temu zapobiega. Jak często — zależy
od siły mossy cells, którą dobraliśmy sami.

**Pytania:**

1. **Hamowanie toniczne.** W modelu odpowiada za ~74% hamowania komórek
   ziarnistych (reszta to FS→GC). Czy to realistyczne?
2. **Częstotliwość FS.** Model daje ~46 Hz; po dodaniu wzajemnego hamowania
   FS→FS ~28 Hz. Jaka wartość bazowa jest fizjologiczna?
3. **In vitro czy in vivo?** Waga dobrana do protokołu pulsowego z danych
   Madara (~50% szans na AP) jest w sieci o gęstym wejściu za silna: komórki
   ziarniste strzelają ~11–22 Hz zamiast 2–6 Hz. Do którego reżimu kalibrować?
4. **Mossy cells → komórki ziarniste (nowe).** Przy naszych wagach „zapłon"
   zdarza się w kilku procentach symulacji, przy pętli ~50% silniejszej —
   w 20–40%. Czy jest liczba, na której można oprzeć siłę tej drogi (amplituda
   EPSP, liczba kontaktów, częstotliwość MC in vivo)?

Przy okazji: z adnotacji w danych Madara wychodzi τ_m ≈ 3 ms dla komórek
ziarnistych, a nie 10–50 ms. Czy to kwestia definicji?

Wystarczy po zdaniu na pytanie — chętnie też umówię krótką rozmowę.

I prośba o opinię w dwóch sprawach: czy widzi Pani odbiorców dla samego
narzędzia (interaktywna aplikacja do modelu, mamy draft artykułu) i w którą
stronę pchnąć dalszą pracę — artykuł metodologiczny o mierzeniu separacji
czy model padaczki (utrata mossy cells / hamowania). Drugi kierunek zależy
od pytania 4.

Z wyrazami szacunku,
Jakub Caputa

---
---

## Notatki dla mnie — nie wysyłać

Liczby sprawdzone ponownie 2026-10-07 (symulacja domyślnej konfiguracji,
`calibrate.measure_inhibition_balance`, `python -m dg_core.calibrate`).
✓ = potwierdzone, ⚠️ = z zastrzeżeniem.

### Pytanie 1 — hamowanie toniczne (~74%)

**Skąd.** Komórka ziarnista ma w modelu dwa hamulce: stały prąd `K_GC` = 10
(toniczny, odpowiednik pozasynaptycznego GABA_A) i impulsy od interneuronów FS
(fazowy, `W_FS_GC`). Oba wchodzą do tego samego równania napięcia, więc można je
porównać wprost: toniczne 10.0, fazowe średnio 3.59 → udział tonicznego
10 / 13.59 = **73.6% ✓**.

**Dlaczego pytamy.** 74% nikt nie wybrał — wyszło z wcześniejszych ustawień. A
`K_GC` robi trzy rzeczy naraz: ustala próg (14 mV), potencjał spoczynkowy
(−78.7 mV) i to, ile komórek strzela (STATUS sek. 3.8). Jeśli prof. powie np.
„toniczne to ~30%", trzeba będzie zmniejszyć `K` albo wzmocnić fazowe — i to
przesunie cały punkt pracy.

**Powiązanie.** Dane Madara dopuszczają `K` ≈ 0–13.6 (STATUS sek. 3.8), więc
odpowiedź zawęzi ten zakres.

### Pytanie 2 — częstotliwość FS (~46 → ~28 Hz)

**Skąd.** W domyślnym modelu FS strzelają **46.0 Hz ✓**. Interneurony nie miały
żadnego hamowania synaptycznego (tylko toniczne `K_FS` = 5), co jest
nierealistyczne. Dodany kanał FS→FS obniża to: `W_FS_FS` = 0.5 / 1 / 2 / 4 →
41.8 / 37.8 / 33.4 / **27.6 Hz ✓** (komórki ziarniste 3.1 → 4.1 Hz, bo słabsze FS
mniej je hamują).

**Dlaczego pytamy.** Nie wiemy, jaka siła FS→FS jest realna, więc nie wiemy, którą
wartość wybrać. Znajomość docelowej częstotliwości FS wyznaczy `W_FS_FS`.

### Pytanie 3 — in vitro czy in vivo (~11–22 Hz zamiast 2–6 Hz)

**Skąd.** Są dwa sposoby dobrania wagi wejścia PP→GC:
- **nasz obecny:** waga 4 mV, dobrana tak, żeby w sieci (400 Hz wejścia na aktywną
  komórkę) komórki strzelały ~3–6 Hz — czyli „pod wynik", nie z pomiaru;
- **z protokołu Madara:** pojedynczy impuls przy słabym tle (40 Hz) ma dawać
  ~50% szans na AP. Kalibracja (`python -m dg_core.calibrate`) daje wagę
  **6.98 mV**.

Waga z protokołu, wstawiona do sieci z gęstym wejściem, daje za dużo aktywności.

⚠️ **Korekta liczby z poprzedniej wersji maila.** „22 Hz" (dokładnie 21.5 Hz ✓)
wychodzi z dwóch zmian NARAZ: wagi 6.98 mV i `K_GC` = 0. To drugie bierze się
z tego, że preset kalibracji celuje w V_rest = −70 mV, a przy b = 0.2 daje to `K`
= 0, czyli zero hamowania tonicznego. Rozdzielone:

| zmiana względem domyślnego modelu | GC we wzorcu | FS |
|---|---|---|
| nic (waga 4, `K` = 10) | 3.1 Hz | 46 Hz |
| tylko waga 6.98 mV | **11.5 Hz** | 117 Hz |
| tylko `K` = 0 (V_rest −70) | 12.7 Hz | 121 Hz |
| obie | 21.6 Hz | 178 Hz |

Dlatego w mailu jest teraz „~11–22 Hz". Uczciwe zdanie: sama waga z protokołu
daje ~4× za dużo; razem z celem V_rest −70 mV — ~7× za dużo.

**Uwaga przy okazji:** cel −70 mV w presecie pochodzi z wcześniejszej
korespondencji, a dane Madara dają medianę **−76 mV** (STATUS sek. 3.8). Przy
−76 mV `K` byłoby ~6, nie 0 — czyli część problemu „22 Hz" wynika z celu −70 mV,
który same dane podważają. Warto to mieć w głowie przy odpowiedzi prof.

**Dlaczego pytamy.** Jedna waga nie spełni obu warunków (50% AP in vitro i rzadkie
strzelanie w sieci). Trzeba wybrać, który warunek jest kontrolny — to decyzja
biologiczna, nie obliczeniowa.

### Pytanie 4 — siła mossy cells (nowe)

**Skąd.** Przy domyślnych wagach mossy cells w ogóle nie strzelają (**0.00 Hz ✓**):
napęd od komórek ziarnistych (1 mV) jest daleko pod ich progiem 14 mV. Żeby
zbadać ich rolę, ustawiliśmy ręcznie reżim `mc_active` (napęd GC→MC 16, wyjście
MC ×20, hamowanie FS→MC 2). Test E1‴ (STATUS sek. 3.4) przesuwał całą pętlę
współczynnikiem λ (1 = `mc_active`).

**Liczby ✓** (zapłon = prawie cała sieć strzela dla jednego z wzorców, n = 30 na
punkt):
- λ = 1, słabe hamowanie fazowe (`W` = 0–0.5): 2, 2, 1 na 30 → **„kilka procent"**;
- λ = 1.5 (wszystkie wagi pętli ~1.5×; ściśle +47–50%): 6, 8, 12 na 30 →
  **20–40%**;
- bez mossy cells: 0 na 210; przy `W` ≥ 3: zawsze 0.

**Dlaczego pytamy.** Od tej jednej liczby zależy, czy wariant (d) — model padaczki —
ma sens: przy słabej pętli zapłonu praktycznie nie ma, przy silnej jest częsty.
Wystarczy cokolwiek z literatury: amplituda EPSP MC→GC, ile MC kontaktuje jedną
GC, jak często MC strzelają in vivo.

### τ_m (drobne)

**Skąd.** Z adnotacji Madara (pola Rm, Cm) τ_m = Rm·Cm ≈ **3 ms** [IQR 2–5],
n = 42 GC (STATUS sek. 3.8). ⚠️ Nie zweryfikowałem tego ponownie — katalogu
`dataset/` z plikami Madara nie ma na Athenie; liczba jest z wcześniejszej analizy.
„10–50 ms" pochodzi z wcześniejszej korespondencji z prof.

**Moje podejrzenie (do sprawdzenia, nie pisać jako fakt):** Cm odczytane ze
wzmacniacza w trybie whole-cell to głównie pojemność somy i proksymalnych dendrytów
(szybka kompensacja), więc Rm·Cm zaniża τ_m. Klasyczne τ_m z zaniku napięcia po
impulsie prądowym wychodzi dla GC rzędu dziesiątek ms. Jeśli tak, to różnica jest
w definicji pomiaru, nie w komórkach. Model Izhikevicza nie ma jawnego τ_m, więc
na symulacje to nie wpływa — potrzebne tylko do Methods.

### Dwie sprawy otwarte na końcu maila

- **Narzędzie:** `interactive_dg.py` + `article/article_draft.tex` (nieskompilowany).
- **Kierunek:** STATUS sek. 4.1 — rekomendacja: najpierw (a) artykuł metodologiczny;
  (d) padaczka dopiero, gdy pytanie 4 da liczbę.
