# Artykuł ML na bazie mechanizmu DG — pomysły

*Utworzono 2026-10-07. Status: **propozycja**, nie wyniki.*

> ⚠️ **Czytaj to jako nową linię pracy, nie jako przepakowanie tego, co mamy.**
> Z `snn_separation` nie ma ANI JEDNEGO wyniku uczenia maszynowego — to symulacja
> 200 neuronów w Brian2, bez zadania, bez uczenia, bez baseline'ów. Przenosimy
> stąd **mechanizm** i **metodologię oceny**, a nie liczby.

---

## 1. Co realnie mamy do przeniesienia

**Z `snn_separation` — mechanizm i metodologia:**

| aktyw | czym jest | dlaczego ważne dla ML |
|---|---|---|
| `K_GC` — hamowanie toniczne | globalny, skalarny, wewnątrzkomórkowy prąd wchodzący **wprost do równania napięcia**; próg odpalenia `G_crit = 4 + K` w formie zamkniętej | gotowy „pokrętło wzmocnienia": jeden skalar steruje tym, **kto** odpala |
| `solve_k_gc_for_active_fraction()` | bisekcja po `K` do **zadanej frakcji aktywnych** | to jest już kontroler rzadkości w pętli zamkniętej |
| wynik: aktywność dominuje wszystko | separacja, retencja informacji i dekodowalność są przede wszystkim funkcjami rzadkości, a nie obwodu (STATUS sek. 3.3, sek. 3.4) | uzasadnia, dlaczego sterować rzadkością, a nie wagami |
| wynik: ~61% przewagi to sam próg | obwód bez hamowania bije losową projekcję o +0.094 z +0.152 (STATUS sek. 3.5) | nieliniowość progowa jest głównym składnikiem — tanie w implementacji |
| **null-e o dopasowanej rzadkości** | dwa naturalne null-e zawodzą w przeciwne strony (STATUS sek. 3.5) | **protokół ewaluacji, którego ML nie stosuje** |

**Z `snn_stdp_vs_surrogate_gradient` — gotowa infrastruktura:**
`paper_experiments/exp2_dead_neurons/run_stdp_3factor.py` (R-STDP z nagrodą
**per-sample**, nie per-batch), `exp6_unified/mechanisms.py` (framework faktorialny
2^k warunków), k-WTA, hamowanie boczne, plastyczność wewnętrzna (IP), MNIST /
CIFAR / N-MNIST, SpikingJelly, sharding SLURM na Athenie. **To jest ~80% harnessu
treningowego gotowe i odpluskwione.**

---

## 2. Pomysł główny: **rzadkość jako trzeci czynnik**

Klasyczna reguła trójczynnikowa: `Δw = f(pre, post, M)`, gdzie `M` (nagroda,
dopamina, kontekst) moduluje **tempo uczenia** albo bramkuje ślad kwalifikowalności.

**Nasza propozycja:** `M` nie dotyka `Δw`. `M` ustawia **tonus `K`**, czyli
**frakcję aktywnych jednostek** — a więc to, **kto w ogóle jest kwalifikowalny**
do plastyczności.

```
klasycznie:   M  →  wielkość Δw            (ile się uczyć)
tutaj:        M  →  K  →  rzadkość  →  KTO się uczy
```

Biologicznie to jest wierne: toniczne GABA w DG jest neuromodulowane, działa
globalnie i zewnątrzsynaptycznie, i nie jest tym samym kanałem co hamowanie
fazowe — dokładnie ta dysocjacja, którą zmierzyliśmy.

**Dlaczego to miałoby działać w ML:** rzadkość steruje nakładaniem się
reprezentacji, nakładanie steruje interferencją między zadaniami, a interferencja
to katastroficzne zapominanie. Czyli skalar `M` o jednym wymiarze dostaje
bezpośredni uchwyt na interferencję — to jest „adaptive top-down encoding"
w najtańszej możliwej postaci.

---

## 3. Czym to się różni od tego, co już jest

| praca | co robi | czego NIE robi |
|---|---|---|
| **XdG** (Masse i in. 2018) | bramkuje **zakodowany na sztywno** podzbiór jednostek per zadanie | poziom rzadkości jest stały i z góry zadany; brak pętli zamkniętej |
| **Active Dendrites** (Iyer i in. 2022) | kontekst dendrytyczny + k-WTA | `k` ustalone; kontekst wybiera **które**, nie **ile** |
| **sparse distributed representations** (Ahmad & Scheinkman) | pokazuje, że rzadkość pomaga | nie steruje nią adaptacyjnie |
| k-WTA ze zmiennym progiem w SNN | próg zmienny w czasie | nie jest to trzeci czynnik, brak sygnału odgórnego |

**Luka, którą zajmujemy:** nie „które jednostki maskować", tylko **jaki ma być
poziom rzadkości — sterowany w pętli zamkniętej, sygnałem odgórnym, przez
pobudliwość wewnątrzkomórkową, a nie przez maskę.** Plus protokół ewaluacji
z sek. 4, którego ta literatura nie stosuje.

⚠️ **Uczciwie:** „zmienny próg w SNN" jest blisko mechanicznie. Nowość musi stać
na **pętli sterowania + ramie trójczynnikowej + ewaluacji**, a nie na samym
„próg się zmienia". To trzeba sprawdzić dokładniej, zanim się napisze abstrakt.

---

## 4. Drugi wkład, samodzielnie publikowalny: **null-e o dopasowanej rzadkości**

To jest nasz najmocniejszy, najlepiej udokumentowany wynik — i **podróżuje do ML
bez zmian**. Prace o reprezentacjach rutynowo twierdzą „nasza metoda uczy
bardziej zdekorelowanych / mniej redundantnych reprezentacji". Pokazaliśmy, że:

1. taka miara jest zdominowana przez rzadkość, nie przez metodę;
2. odrzucanie punktów o niskiej aktywności **nie ratuje** — maksimum przenosi się
   na próg odrzucania;
3. **dwa naturalne null-e zawodzą w przeciwne strony**: permutacyjny niszczy całą
   informację (sufit, `r_out`→0), losowa projekcja jest prawie-izometrią (podłoga,
   `r_out` = 78% `r_in`). Obejmują metodę, zamiast ją benchmarkować.

**Deliverable:** mały protokół + kod, zastosowany do istniejących reprezentacji
(SSL, continual learning), z pokazaniem, o ile kurczą się raportowane zyski
„dekorelacji" po kontroli rzadkości. To jest **warsztatowy paper albo sekcja
ewaluacyjna** w artykule głównym.

---

## 5. Trzy warianty, w kolejności rekomendacji

| | artykuł | koszt | ryzyko |
|---|---|---|---|
| **M1** ⭐ | **Rzadkość jako trzeci czynnik** — mechanizm (sek. 2) + ewaluacja (sek. 4) | średni: harness jest, trzeba dopisać kontroler `K` i pętlę | novelty vs „zmienny próg" — do sprawdzenia |
| **M2** | **Adaptacyjne kodowanie odgórne** — kontroler czyta kontekst, emituje docelową rzadkość; strumień NIESTACJONARNY | średni | trzeba zbudować benchmark niestacjonarny; mniej standardowy |
| **M3** | **Null-e dla reprezentacji** — sam protokół ewaluacji | **najniższy**, materiał prawie gotowy | warsztat, nie konferencja główna |

**Rekomendacja: M1 jako artykuł główny, z sek. 4 jako jego sekcją ewaluacyjną.**
M3 trzymać jako plan B — da się go napisać w tygodnie, gdyby M1 nie wyszedł.

---

## 6. Konkretny plan eksperymentów dla M1

**Architektura.** `wejście → warstwa ekspansji (spiking, z biasem tonicznym K) →
odczyt`. Uczenie w warstwie ekspansji: R-STDP (gotowe). Trzeci czynnik `M`
(nagroda / id zadania / wyjście małego kontrolera) → `K` → docelowa frakcja
aktywnych `a*`, realizowana homeostatycznie (online odpowiednik naszej bisekcji).

**Warunki (framework faktorialny z `mechanisms.py` to obsłuży):**

| warunek | `M` działa na | po co |
|---|---|---|
| `baseline` | — | k-WTA o stałym `k` |
| `3f_lr` | tempo uczenia | **klasyczny trzeci czynnik** — główny baseline |
| `3f_sparsity` | `K` → rzadkość | **nasza propozycja** |
| `3f_both` | oba | czy addytywne |
| `fixed_k_matched` | — | `k` ustawione na ŚREDNIĄ z `3f_sparsity` → **null o dopasowanej rzadkości** |

Ostatni wiersz jest nieoczywisty i najważniejszy: bez niego nie da się odróżnić
„adaptacyjna rzadkość pomaga" od „ta metoda po prostu trafiła lepsze `k`".

**Dane.** Split-MNIST i Split-CIFAR (continual), N-MNIST (natywnie spajkowe,
wyróżnik wobec prac na ANN). Wszystkie trzy są w repo STDP.

**Metryki.** Dokładność średnia i końcowa po zadaniach, miara zapominania,
**nakładanie reprezentacji między zadaniami kontrolowane rzadkością** (nasz null).

---

## 7. Ryzyka, uczciwie

1. **„Rzadkość pomaga" nie jest nowe.** Nowość = pętla sterowania + rama
   trójczynnikowa + ewaluacja. Jeśli recenzent odczyta to jako „XdG ze zmiennym
   k", artykuł pada. **Pozycjonowanie trzeba rozstrzygnąć przed pisaniem.**
2. **Może nie wygrać z `3f_lr`.** To realne. Wtedy wynik negatywny + sek. 4 nadal
   daje artykuł (M3), ale słabszy.
3. **Nasze wyniki DG są w większości negatywne.** Nie wolno ich sprzedawać jako
   motywacji w stylu „DG świetnie separuje, więc skopiujmy DG". Uczciwa motywacja
   brzmi: *zmierzyliśmy, że w tym obwodzie rzadkość jest zmienną dominującą — więc
   uczyńmy ją zmienną sterowaną.* To jest mocniejsze, bo oparte na pomiarze.
4. **Prior art do domknięcia.** Searche z 2026-10-07 nie wyczerpują tematu;
   przed abstraktem przejrzeć: neuromodulacja pobudliwości w SNN, homeostatyczna
   regulacja rzadkości, meta-uczenie progów.

---

## 8. Co zrobić najpierw (nie wymaga decyzji z STATUS sek. 4.1)

1. **Pół dnia:** przejrzeć prior art z sek. 3 i sek. 7 i rozstrzygnąć pozycjonowanie.
   To jest brama go/no-go dla M1 — przed jakimkolwiek kodem.
2. **Dzień:** prototyp `3f_sparsity` na Split-MNIST w repo STDP, jedno ziarno,
   bez tuningu. Pytanie: czy w ogóle się uczy i czy kontroler trafia w `a*`.
3. **Dzień:** dopisać warunek `fixed_k_matched`. Bez niego reszta nie ma wartości
   dowodowej.
4. Dopiero potem pełny sweep faktorialny na Athenie.

> **Uwaga rozliczeniowa:** Athena liczy godziny GPU i nie ma partycji CPU-only,
> ale w odróżnieniu od `snn_separation` **tu GPU jest faktycznie używane** —
> trening SNN. Sharding per warunek jak w `job_exp6_unified.sh` jest właściwy.
