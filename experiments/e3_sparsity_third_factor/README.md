# E3 — rzadkość kodu DG jako trzeci czynnik uczenia

*Stan: 2026-10-31. Wszystkie zaplanowane eksperymenty (E3.0–E3.9h) są policzone
i przeanalizowane; w tle nic się nie liczy. Kolejność prac w całym projekcie:
[STATUS.md](../../STATUS.md) sek. 4.*

| plik | co zawiera | kiedy czytać |
|---|---|---|
| **README.md** (ten) | pytanie, odpowiedź, werdykty, mechanizm, dalsze kroki, model w skrócie | najpierw |
| [results.md](results.md) | każdy wykres z objaśnieniem, słowniczek (czytniki, ACC, BWT) | przed spotkaniem, przy pisaniu |
| [wyniki_szczegolowe.md](wyniki_szczegolowe.md) | wszystkie tabele liczb (sek. 12–12k) | gdy potrzebna konkretna liczba |
| [prereg.md](prereg.md) | hipotezy i kryteria zapisane przed uruchomieniem (sek. 2, 6–6k) | przy ocenie werdyktu |
| [literatura.md](literatura.md) | przegląd literatury i zderzenie z wynikami | przy pisaniu |
| [archiwum_plan.md](archiwum_plan.md) | plan z 2026-10-12, decyzje Q1–Q9, implementacja E3.0 | rzadko |

Kod powstaje tylko w `snn_separation`; repo `snn_stdp_vs_surrogate_gradient` jest co
najwyżej źródłem danych (MNIST) i nie jest modyfikowane. W PLAN_BADAWCZY „E3” oznaczało
niezbudowany eksperyment Sobol/LHS — on nazywa się teraz „E3-S”.

---

## 1. Pytanie

Hamowanie toniczne `K` ustawia jednym skalarem, jaki odsetek **f** neuronów warstwy DG
odpala na bodziec (STATUS sek. 3.3–3.4). E3 zamienia tę zmienną w zmienną sterowaną:

> **Czy sterowanie gęstością kodu sygnałem nowości zmniejsza zapominanie przy uczeniu
> kolejnych zadań bardziej niż ta sama średnia gęstość ustawiona na stałe?**

Nowość to drugi trzeci czynnik obok nagrody: nagroda decyduje, *czy* zmienić wagi, nowość
— *ile neuronów* koduje bodziec, czyli gdzie nauka zostawia ślad. Zadanie główne:
Split-MNIST class-incremental (5 zadań po 2 cyfry, jeden czytnik 10-klasowy, bez
informacji o granicach zadań); drugie: separacja wzorców w modelu `dg_core`.

## 2. Odpowiedź

1. **Kierunek zależy od reguły uczenia.** Przy regułach osłabiających wagi (R-STDP z R − R̄,
   delta) „nowość → rzadziej” zwiększa zapominanie, a „nowość → gęściej” je zmniejsza.
   Przy regule tylko wzmacniającej (`rgate`) jest odwrotnie. Wynik jest odporny na
   6 architektur × 2 neurony (E3.5), a znak odwraca już niewielkie osłabianie (λ = 0.25, E3.8).
2. **Przy osłabianiu zapominanie to głównie przewaga nowych klas.** Wiedza o starych klasach
   zostaje w czytniku (wybór „0 czy 1?” trafny w 83–92%), ale na starych obrazach wygrywają
   wyjścia nowszych klas (96–100% błędów). „Nowość → gęściej” ogranicza to przejmowanie
   (E3.9). Hipoteza „gęsty kod rozcieńcza szkodę” jest sprzeczna z pomiarem (E3.8).
3. **Na zadaniu separacji wzorców kierunek zależy też od podobieństwa wzorców.** W modelu
   skalibrowanym do skrawka: przy R_in = 0.5 pomaga „rzadziej”, przy R_in = 0.9 — „gęściej”,
   zgodnie z Pérez-Montoyo i in. 2026 (E3.6x).
4. **Warstwa ukryta:** gdy jednostki ukryte są przypisane klasom, zasada z pkt 1 obowiązuje
   (20/20); wspólna warstwa ukryta zapomina prawie wszystko przy każdej regule i — inaczej niż
   czytnik liniowy — naprawdę niszczy wiedzę (E3.7b, E3.9h).
5. **Metodologia:** optimum rzadkości dla uczenia leży przy f ≈ 10–25%, a dekorelacja go
   nie widzi (E3.1, sprawdzone do f = 90%); kontrola „stałe f o tej samej średniej” zmienia
   wnioski o modulacji — opublikowane prace jej nie mają (E3.3, Nm-SNN). O zapominaniu
   bardziej niż rzadkość decyduje reguła czytnika, a globalny próg (samo hamowanie
   toniczne) nie wyrównuje aktywności między wzorcami (E3.0, E3.4).

**Wspólny mianownik** (we wszystkich przypadkach, które zmierzyliśmy w E3.9/E3.9h):
korzystne sterowanie rzadkością zmniejsza to, ile obrazów starych klas „przejmuje” ostatnie
zadanie, a dokładność w obrębie zadania prawie się nie zmienia (≤ 0.03). Sterowanie
rzadkością działa więc głównie jako regulacja przechylenia między starymi a nowymi
wyjściami, nie jako ochrona śladów pamięci.

## 3. Werdykty

Kryteria: [prereg.md](prereg.md); liczby: [wyniki_szczegolowe.md](wyniki_szczegolowe.md);
wykresy: [results.md](results.md). „Δ” = BWT(modulacja) − BWT(stałe f o tej samej średniej);
> 0 znaczy, że modulacja zapomina mniej.

| exp. | pytanie | wynik | fig. |
|---|---|---|---|
| E3.1 | czy dokładność ma optimum w f, a dekorelacja rośnie do ciszy? (H-E3a) | ✅ 4/4 kombinacje, 5/5 sieci; optimum 10–25%, spadek trwa do f = 90% | 1 |
| E3.2 | czy hamowanie fazowe przy stałym f nie zmienia dokładności? (H-E3b) | ❌ obniża ją (6/8 testów) | 2 |
| E3.3 | czy „nowość → rzadziej” zapomina mniej niż stałe f? (H-E3c) | ❌ zapomina **więcej** (R-STDP, delta; dwa zestawy sieci) | 3, 4 |
| E3.3 | rzadkość vs tempo uczenia (H-E3d) | ❌ bez różnicy | 3 |
| E3.3 | czy „nowość → gęściej” zapomina mniej? (H-E3e, potwierdzenie na sieciach 5–9) | ⚠️ kierunek 8/8, kryterium niespełnione dla Izhikevich × R-STDP | 3 |
| E3.4 | kod czy reguła decyduje o zapominaniu? | reguła; DG bez wyrównania aktywności przegrywa z k-WTA | 5 |
| E3.5 | czy obalenie H-E3c jest ogólne? | ❌ nie — przy `rgate` „rzadziej” pomaga w 12/12 komórkach, przy R-STDP/delcie szkodzi w 24/24 | 7 |
| E3.6 | to samo na zadaniu separacji (`dg_core`, stara kalibracja) | kierunek zależy od reguły i R_in (3/9 zgodnych z obaleniem) | 8 |
| E3.6x | to samo na modelu skalibrowanym do skrawka | R_in 0.5: „rzadziej” pomaga; R_in 0.9: „gęściej” pomaga | 9 |
| E3.8 | dlaczego reguła? („rozcieńczanie szkody”) | ❌ rozcieńczania nie ma; λ = 0.25 osłabiania już odwraca znak | 10 |
| E3.7 | czy zasada przenosi się na warstwę ukrytą (AGREL)? | ⚠️ nierozstrzygające — obie wersje zapominają całkowicie | 11 |
| E3.9 | przy osłabianiu: zniszczenie wag czy przewaga nowych klas? | ✅ przewaga nowych klas; „gęściej” ogranicza przejmowanie (delta ✅, R-STDP: kierunek zgodny, p = 0.16) | 12 |
| E3.7b | warstwa ukryta bez osłabiania heterosynaptycznego | ⚠️ formalnie nierozstrzygające (uczą się 2/6 wariantów); w uczącym się (pule na klasę) zasada obowiązuje 20/20 | 13 |
| E3.9h | wspólna warstwa ukryta: przewaga czy zniszczenie? | zniszczenie (w obrębie zadania 0.61–0.67, losowo 0.50) | — |

## 4. Mechanizm — obraz na dziś

| sieć / reguła | jak zapomina | korzystny kierunek przy nowości | przez co działa (E3.9, E3.9h) |
|---|---|---|---|
| czytnik liniowy z osłabianiem (R-STDP, delta) | przewaga nowych klas; wiedza zostaje | gęściej | mniej obrazów przejmuje ostatnie zadanie (delta: −0.03…−0.07, 10/10) |
| czytnik liniowy bez osłabiania (`rgate`), pule na klasę | mało (BWT −0.03…−0.08), błędy bez przechylenia | rzadziej | to samo (`rgate` Izh.: przejmowanie 0.34 → 0.11) |
| wspólna warstwa ukryta | zniszczenie reprezentacji + przejmowanie | rzadziej, ale sieć i tak nie pamięta | mniej przejmowania (−0.39), wiedza +0.03 |
| zadanie separacji, model skrawka | — | zależy od podobieństwa wzorców | niezbadane |

Otwarte: **dlaczego** kierunek odwraca się z regułą — wiemy, że oba kierunki działają przez
przejmowanie, ale nie, czemu przy osłabianiu przejmowanie ogranicza gęsty, a bez osłabiania
rzadki kod.

## 5. Ograniczenia

- Czytnik nie jest impulsowy (10 integratorów, decyzja = maksimum); impulsowa jest tylko
  warstwa DG. Jedna zamrożona realizacja szumu na obraz, jedna epoka na zadanie.
- Normalizacja wejścia per obraz jest założeniem modelu (bez niej globalny próg niszczy kod — E3.0).
- Część twierdzeń stoi tylko na sieciach 0–4 (E3.5 dla architektury domyślnej, E3.8, E3.9);
  potwierdzenie na nowych sieciach zrobiono tylko dla E3.3 (sieci 5–9).
- `rgate`: η i f_gęsty (Izh. 50%) na brzegu siatki strojenia.
- E3.6x: przy R_in ≥ 0.75 dokładności niskie (0.15–0.30), więc te komórki rozstrzygają słabo.
- E3.1: przy LIF i f = 90% hamowanie toniczne K ≈ −4 (próg ≈ 0, strzelanie bez wejścia).
- Nie porównaliśmy ze standardowymi metodami korekcji przechylenia (BiC, WA) — patrz sek. 7.

## 6. Model i metody w skrócie

**Warstwa DG** (`model.py`): 2000 neuronów Izhikevicha (parametry GC z `dg_core`) albo LIF;
każdy widzi 30 losowych pikseli; wejście Poisson 200 Hz × 1 mV, 100 ms, obraz znormalizowany
do stałej sumy jasności. `K` w równaniu napięcia, jeden skalar dla warstwy. Warstwa się
nie uczy, więc **kody liczymy raz** (`precompute_codes.py`, GPU): 70 000 obrazów × 17 poziomów
f (1–50%, tablica `K(f)` z bisekcji); f = 70/90% w osobnych plikach `*_hi`. Zgodność z
Brian2: `tests/test_e3_layer.py`.

**Czytniki** (`learning.py`; wejście ĉ = c/‖c‖, chyba że `_raw`):

| reguła | Δw | osłabia? |
|---|---|---|
| `rstdp` | η (R − R̄)(post − p) ĉ, wyjście losowane z softmax (REINFORCE) | tak |
| `delta` | NLMS z etykietą | tak |
| `rgate` | tylko przy nagrodzie: wagi do wybranego wyjścia + η ĉ, normalizacja kolumny; ε = 0.1, β = 20 | nie |
| `rmix` | `rgate` + przy pomyłce − λ η ĉ | λ |
| `fly` | FlyModel: + η c do klasy docelowej | nie |
| `rstdp_raw`, `delta_raw` | jak wyżej, bez normalizacji per obraz | tak |

**Regulator:** nowość = niepewność czytnika (`unc`), wygładzona (τ = 50 obrazów),
przeskalowana percentylami 5–95 z pilotażu; f przesuwa się w skali log między f_spoczynek
a f_nowość. **Dawka g ∈ [−1, 1]:** f_spoczynek = f_c·r^{g/2}, f_nowość = f_c·r^{−g/2},
f_c = √(f_gęsty·f_rzadki), r = f_gęsty/f_rzadki; g = +1 to „nowość → rzadziej”.
**Kontrola:** stałe f równe średniemu f zrealizowanemu przez modulację, ten sam przebieg
danych; wariant `matched_inv_evalrest` ocenia na tym samym poziomie co modulacja.

**Miary:** ACC (końcowa dokładność, średnia po 5 zadaniach), BWT (średni spadek dokładności
zadań 1–4 od chwili nauki do końca; 0 = nic nie zapomniano, −1 = wszystko). E3.9: dokładność
w obrębie zadania (wybór z 2 klas), część błędów → nowsze / ostatnie zadanie, dokładność po
wyrównaniu wyjść.

**Hiperparametry** (`hparams.json`, strojone na sieci 99, walidacja = ostatnie 10k obrazów
treningowych):

| | η (izh / lif) | f_gęsty / f_rzadki (izh) | (lif) |
|---|---|---|---|
| `rstdp` | 0.25 / 0.5 | 10% / 3% | 10% / 3% |
| `delta` | 0.05 / 0.05 | 20% / 5% | 25% / 6% |
| `rgate` | 0.01 / 0.01 | 50% / 12% | 12% / 3% |

**Warstwa ukryta** (`run_hidden.py`): 500 jednostek ReLU, AGREL (nagroda × sprzężenie od
wybranego wyjścia); warianty `agrel`, `agrel_pos` (E3.7), `pos_bound`, `pos_pool`,
`agrel_bound` (E3.7b) — opis w docstringu.

**Zadanie separacji** (`run_dgtask.py`): `dg_core` (200 GC + FS + HMC, Brian2), 10 prototypów
o podobieństwie R_in, uczone parami; `--regime exvivo` = model skalibrowany do skrawka
([../calib_exvivo/README.md](../calib_exvivo/README.md)).

## 7. Dalsze kroki E3 (propozycja, w kolejności)

1. **Porównanie z korekcją przechylenia wyjść** (tanie, na gotowych kodach, ~1 dzień).
   Skoro przy osłabianiu sterowanie działa przez przechylenie, trzeba sprawdzić, czy daje coś
   ponad standardową korektę bez dostępu do starych danych (np. WA — wyrównanie norm wag
   wyjść, Zhao i in. 2020) i czy oba się sumują. Od tego zależy, czy artykuł ML ma tezę
   „sterowanie rzadkością jako biologiczna korekta przechylenia”, czy tylko wynik metodologiczny.
2. **Potwierdzenie na nowych sieciach (5–9)** dla E3.9 (zwłaszcza R-STDP, gdzie H-R3 nie
   przeszło) i E3.5 w architekturze domyślnej, z kryteriami zapisanymi przed uruchomieniem.
3. **Hamowanie zależne od aktywności zamiast globalnego `K`** (zwrotne FS albo k-WTA) — E3.4
   pokazało, że wyrównanie aktywności między wzorcami waży więcej niż poziom rzadkości.
4. **Warstwa ukryta, która się uczy bez katastrofy** — w stronę celu docelowego (DG jako
   mechanizm trójczynnikowy / odgórny w SNN): bramkowanie odgórne od wybranego wyjścia, które
   jednostki ukryte się uczą (pule `pos_pool` to wersja sztywna); tu sterowanie rzadkością
   staje się kodowaniem odgórnym.
5. **E3.6x dokładniej:** więcej poziomów R_in, czytnik z wyższą dokładnością przy R_in ≥ 0.75.

## 8. Pliki i uruchamianie

| plik | rola |
|---|---|
| `model.py`, `calibrate.py`, `tasks.py`, `learning.py` | warstwa DG, tablica K(f), MNIST/Split-MNIST, czytniki i regulator |
| `precompute_codes.py` | kody DG (GPU) → `results/codes/` |
| `run_static.py` | E3.1, E3.2, strojenie η |
| `run_split.py` | E3.3 (wszystkie warunki), pilotaż regulatora |
| `run_factorial.py` | E3.4 |
| `run_dose.py` | E3.5 (dawka–odpowiedź) |
| `run_dgtask.py` | E3.6, E3.6x |
| `run_mechanism.py` | E3.8 |
| `run_hidden.py`, `run_hidden_errors.py` | E3.7, E3.7b, E3.9h |
| `run_errors.py` | E3.9 |
| `make_hparams.py`, `hparams.json` | hiperparametry |
| `analyze.py` → `results/summary.json` | wszystkie kryteria |
| `make_summary_figures.py` → `figures/` | fig. 1–13 (śledzone w gicie) |
| `run_e3*_all.sh`, `run_e37b.sh`, `run_e31_hi.sh` | partie na klaster |

Klaster: `../hpc/e3_driver.sh` wysyła kolejne linie `../hpc/e3_queue.txt` na `plgrid-now`
(jedno zadanie naraz, 1 h, 16 CPU + 1 GPU, konto `plgdyplomanci8-gpu-a100`); kroki w linii
rozdzielone `;`, więc pętle tylko w skryptach `run_*.sh` (z `xargs -r`). Driver:
`pgrep -f "^/bin/bash ./e3_driver.sh"`; start: `nohup ./e3_driver.sh >/dev/null 2>&1 &`
z `experiments/hpc`.
