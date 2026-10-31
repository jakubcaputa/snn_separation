# Prezentacja stanu prac (2026-10-07) — slajd po slajdzie

*Przeniesione 2026-10-31 ze STATUS.md (dawna sek. 7) bez zmian treści. Odwołania „sek. 3.x” dotyczą STATUS.md. Prezentacja nie obejmuje kalibracji ex vivo ani E3.*

`article/prezentacja_stan_prac.pptx`: 14 slajdów głównych (~22 min) + 3 zapasowe na
pytania. Każdy slajd ma notatki prelegenta. Figury po angielsku (spójnie
z artykułem), tekst po polsku. Pointa: slajd 8 (metodologia); slajd 10 pokazuje
jedyny efekt obwodu i to, że nie przeszedł testu potwierdzającego.

**1. Tytuł.** Tytuł i schemat obwodu. Do powiedzenia: model sieci spajkującej DG,
związany danymi patch-clamp; będzie o tym, co ustaliliśmy, co okazało się pułapką
pomiarową i jaka decyzja jest do podjęcia.

**2. W skrócie.** Trzy karty: *obalona* — H1 (sek. 3.3–3.4); *2 z 2* — oba naturalne
null-e zawodzą (sek. 3.5); *0 / 210* — bez mossy cells sieć nie zapala się nigdy; z nimi zapłon jest możliwy,
ale rzadki, a test potwierdzający nie przeszedł (sek. 3.4, E1‴). Na dole
odsyłacz do decyzji (slajd 13).

**3. Czym jest separacja wzorców** (`fig1-concept`). Lewo: dwa wzorce wejściowe
(czarne paski = komórki z silnym napędem; pokazane 80 z 200). Środek: częstotliwość
każdej komórki. Prawo: korelacja wejść 0.73 i wyjść 0.58, różnica +0.15. Jedna
symulacja domyślnej konfiguracji. Do powiedzenia: to definicja operacyjna całej
pracy — i ta liczba rośnie sama, gdy sieć cichnie.

**4. Model** (`fig2-circuit`). PP napędza GC i równolegle FS (FF); GC napędzają FS
(FB); FS hamują GC; HMC w pętli pobudzającej. Ramka: dwie osie hamowania. Do
powiedzenia: rozdzielenie tonicznego (`K_GC`) i fazowego (`W_FS_GC`) to sedno modelu.

**5. Punkt pracy jest zgodny z danymi** (`fig3-operating-point`). `K_GC` = hamowanie
toniczne, stały prąd odejmowany od każdej GC. (a) Niebieska linia: ile stałego napędu
potrzeba, żeby GC strzelała (`G_crit = 4 + K`); czerwona: średni napęd aktywnej GC,
8 mV (= 400 Hz × 4 mV × 5 ms, fluktuacje ±4 mV). Przy `K_GC = 10` próg 14 mV leży nad
średnią, więc odpalają tylko fluktuacje — stąd rzadki kod. (b) Ten sam `K` ustala
potencjał spoczynkowy; zielony pas = IQR z 42 GC Madara, szary pas = `K` zgodne z
danymi (0–13.6). Do powiedzenia: parametr, który robi z DG rzadki koder, daje też
spoczynek zgodny z pomiarem. Jeśli padnie pytanie: waga 4 mV jest dobrana, nie
zmierzona (panel a opisuje reżim, dowodem jest panel b), a dane ograniczają `K` do
zakresu, nie do jednej wartości. Szczegóły sek. 3.8.

**6. E1 — separacja rośnie, gdy sieć cichnie** (`slide-e1`). Szare punkty: 450
punktów siatki (separacja wobec frakcji aktywnych, oś log w %). Przerywane linie:
cztery progi odrzucania cichych punktów; gwiazdki: maksimum separacji przy każdym
progu. Do powiedzenia: każda gwiazdka siedzi przy swoim progu — gdyby istniało
biologiczne optimum, stałyby w jednym miejscu. Sek. 3.3.

**7. E1′ — hamowanie fazowe nic nie zmienia** (`slide-e1p`). Separacja wobec
hamowania fazowego, osobna linia dla każdego z 6 zadanych poziomów aktywności
(bisekcja po hamowaniu tonicznym, 733 punkty). Do powiedzenia: linie leżą na różnych
wysokościach (to robi aktywność), ale żadna nie rośnie z hamowaniem; nachylenie
−0.003, p = 0.60. Sek. 3.4.

**8. ⭐ Z czym w ogóle porównujemy obwód** (`fig5-nulls`). (a) korelacja wyjścia:
wejście 0.75, *random projection* 0.58, DG 0.39, *permuted DG output* 0.00 (oba
null-e objaśnione w sek. 3.1). (b) przewaga DG nad projekcją losową: obwód bez
motywów hamowania +0.094, z nimi +0.152. Do powiedzenia — pointa metodologiczna:
permutacja osiąga zero, bo niszczy informację (sufit); projekcja losowa z definicji
zachowuje korelację (trywialna podłoga); obejmują obwód z dwóch stron. A przewaga
nad projekcją to w ~60% sam próg spajkowania. Sek. 3.5.

**9. E2 — wkład motywów to głównie aktywność** (`slide-e2`). Trzy elementy obwodu:
FF (hamowanie wyprzedzające), FB (hamowanie zwrotne), MC (mossy cells, pętla
pobudzająca); każdy można wyłączyć, więc jest 8 wersji obwodu.
(a) Każda pomarańczowa kropka = jedna wersja (średnio po 36 zestawach wejść ×
5 seedów, `mc_active`, napęd ×1.0); szare punkty = pojedyncze pomiary. Oś x — ile
komórek ziarnistych strzela, oś y — separacja `r_in − r_out`. Wszystkie wersje leżą
na jednej malejącej linii (r = −0.97). (b) Wartość Shapleya = o ile średnio zmienia
się separacja, gdy element dołączamy, uśrednione po wszystkich kolejnościach
dołączania. Do powiedzenia: FF i FB „pomagają", bo wyciszają sieć; MC „szkodzi", bo
ją rozpędza (same MC: 94% aktywnych). Wkład mierzy więc wpływ na aktywność, nie
separację samą w sobie. Uczciwie: wcześniej pokazywałem tu „odporność na null" —
ta kontrola była pusta z konstrukcji. Interakcje i korekta projekcją losową: sek. 3.6.

**10. E1″ / E1‴ — zapłon sieci: jest, ale rzadki** (`fig6-runaway`). (a) Aktywność
wyrównana; oś x — hamowanie fazowe, oś y — odsetek przebiegów, w których jeden ze
wzorców zapalił prawie całą sieć; linie = siła pętli MC (λ = 0 bez MC, λ = 1 jak w
E1″). Bez MC zapłonów nie ma nigdy, przy λ = 1 są 2 na 30, przy λ = 1.5 do 40%; od
`W` = 3 — nigdy. (b) Bez wyrównywania aktywności, λ = 1: oś y — odsetek aktywnych
komórek; przy hamowaniu tonicznym zgodnym z danymi (`K` = 6, 10) bez hamowania
fazowego aktywne jest 100% komórek. Do powiedzenia: w E1″ wyglądało to na „szybsze
komórki" (~280 Hz) — to był artefakt miary mieszającej wzorce; test na nowych seedach
nie przeszedł kryterium zapisanego z góry. Zostaje zjawisko jakościowe, którego
częstość zależy od siły mossy cells — dlatego pytamy o nią prof. Błasiak. Sek. 3.4.

**11. 1A — odbiorca nie korzysta** (`slide-1a`). Dokładność klasyfikatora liniowego
dla czterech wejść. Miara niezależna od korelacji — i też nic: DG 0.885 wobec 0.940,
losowa projekcja remisuje z DG, bez hamowania lepiej. Sek. 3.7.

**12. Co upadło, co stoi, co jest nowe.** *Upadło:* optimum separacji, sterowanie
separacją przez hamowanie fazowe, mossy cells jako motyw separacji, pomoc dla
odbiorcy, „toniczne = ile, fazowe = jak szybko" (artefakt miary). *Stoi:* punkt
pracy zgodny z danymi; DG bije losową projekcję głównie dzięki progowi; z aktywnymi
MC możliwy zapłon sieci, któremu zapobiega hamowanie fazowe (eksploracyjnie).
*Metodologia:* oba null-e zawodzą; próg odrzucania przesuwa maksimum; retencja idzie
za rzadkością wejścia.

**13. Decyzja: czym jest teza pracy.** Cztery warianty; (d) wyróżniony. Do
powiedzenia: (d) przewidział sam plan (bramka G2), ale nasz własny wynik go nie
podpiera, dopóki nie znamy siły mossy cells; (b) odpada. Rekomendacja: najpierw (a),
(d) po zakotwiczeniu MC w danych. Sek. 4.1.

**14. Następne kroki.** Decyzja; siła mossy cells z danych (warunek dla (d)); pytania
do prof. Błasiak; bodźce Madara jako wejście; artykuły.

**15–17. Zapas.** Pełna mapa reżimów E1; pełna siatka E1″ (separacja wobec hamowania
fazowego w 8 panelach — płasko wszędzie poza 20% przy aktywnych MC); profile wkładów
motywów E2.

**Pytania, które padną:**

1. *„Czemu nie odrzucić cichych punktów?"* — Maksimum przenosi się dokładnie na
   próg, przy każdym progu (slajd 6).
2. *„Czemu permutacja nie jest dobrą kontrolą?"* — Jej wynik zbiega do `r_in`, więc
   nadwyżka nad nią to `−r_out` (slajd 8); a w E2 jej odjęcie nie może niczego
   zmienić (slajd 9).
3. *„Czy zapłon nie jest artefaktem ręcznie dobranych wag MC?"* — Jego częstość
   tak: zależy od siły pętli MC (slajd 10a). Samo zjawisko i to, że hamowanie fazowe
   mu zapobiega, powtarza się przy każdej sile, przy której występuje.
