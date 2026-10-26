# Odpowiedź prof. Błasiak na pytania B1–B3 (otrzymana 2026-10-22)

Pytania: STATUS sek. 2 (mail z 2026-09-11, ponowienie z 2026-10-07).
B4 (siła pętli MC→GC) i τ_m — **bez odpowiedzi**.

## Treść (streszczenie wierne, kolejność jak w mailu)

**Separacja i hamowanie.** Hamowanie GC przez interneurony utrzymuje bardzo niską
aktywność GC i sprzyja separacji: Madar (PLoS CB 2019) — po częściowym odhamowaniu
(gabazyna) aktywność GC rosła, a separacja była gorsza. Ola i Kinga zrobiły podobne
eksperymenty z gabazyną; analiza w toku. Ale: przy bardzo niskiej aktywności
korelacja spada do zera, więc „separacja” rośnie — to własność korelacji, nie sieci.
Liczy się też, KIEDY neuron odpala: po przetasowaniu impulsów (spike shuffling,
Madar Sci Rep, szare pole; Madar 2019 Fig. 7c–d) liczba impulsów jest ta sama
i „separacja” wygląda na lepszą niż w prawdziwej GC, ale komórka na ten sam pociąg
wejściowy odpowiada za każdym razem inaczej. **Wniosek: obok dekorelacji patrzeć na
R_w — korelację między odpowiedziami na powtórzenia tego samego wzorca** (Madar:
10 powtórzeń; w ich preparacie 5, bo komórki umierają — w modelu sprawdzić, czy
5 vs 10 powtórzeń coś zmienia).

**B1 — udział hamowania tonicznego (74% w modelu).** Obniżenie FS→GC o 30% (jak
u Madara z gabazyną) w modelu nie zmienia częstości GC; w preparacie zmienia — ok. 2×
(Madar 2019 PLoS CB: „partial disinhibition of GCs led to higher FR and a higher
propensity to fire small bursts of spikes riding on the same EPSP”, Fig. 7b).
**Hamowanie toniczne ma w modelu za dużą wagę względem fazowego.**

**B2 — częstotliwość FS.** Perisomatyczne PV+ (odpowiednik naszych FS): in vivo
10–20 Hz (tabela w załączonym przeglądzie). Skrawek: Madar Sci Rep, suplement Fig. S7.
**28 Hz (z FS→FS) mieści się w zakresie, 46 Hz nie** (wysokie wartości na wykresie to
częstotliwość w burstach). Suwaka FS→FS nie znalazła.

**B3 — in vitro czy in vivo.** **Kalibrować do ex vivo (skrawki)** — wszystkie dane
(literatura i nasze) są ze skrawków. Uwaga do wagi: u Madara 50% AP dotyczy
**zsumowanego EPSC po jednym pulsie, czyli wielu synaps naraz**; jeśli 50% przypisać
pojedynczej synapsie i dać 40 takich po 10 Hz, wychodzi kilkanaście Hz.

Załączniki (do zapisania w `papers/`, poza repo): przegląd z tabelą częstotliwości
interneuronów in vivo; suplement Madar et al. Sci Rep (Fig. S7).

## Co z tego wynika (nasza interpretacja, 2026-10-22)

1. **B3 rozwiązuje sprzeczność z kalibracji.** `calibrate.measure_p_spike` modeluje
   puls jako JEDNO zdarzenie o wadze W_pulse = 6.98 mV — czyli dokładnie zsumowany
   EPSP salwy, jak u Madara. Błąd był w użyciu tej wagi w sieci jako wagi każdego
   z 40 niezależnych włókien po 10 Hz. W reżimie ex vivo wejściem nie jest ciągłe tło
   400 Hz, tylko **protokół stymulacji: salwy (pociągi pulsów Madara), każda o wadze
   W_pulse**. To jest zadanie `io_madar.py` (STATUS sek. 4.4 pkt 2) — teraz główna
   ścieżka kalibracji, nie dodatek.
2. **B1 daje cel kalibracji:** −30% FS→GC → ok. 2× częstotliwość GC (+ skłonność do
   małych burstów). Kalibrować `W_FS_GC` i `K_GC` razem tak, by ten test przechodził.
   Wyniki E1′ / E3.2 („hamowanie fazowe przy stałej aktywności nie zmienia separacji /
   obniża użyteczność kodu”) były liczone w reżimie z dominującym hamowaniem tonicznym
   — trzeba je powtórzyć po rekalibracji.
3. **B2:** FS→FS włączone jako domyślne (~28 Hz); cel 10–28 Hz.
4. **R_w zmienia metrykę.** Porównywać korelację między wzorcami (r_out) z korelacją
   między powtórzeniami tego samego wzorca (R_w). Model jest deterministyczny przy
   ustalonym wejściu, więc R_w wymaga źródła zmienności — zawodności synaps (`P_REL_*`,
   już w `dg_core`) albo szumu błonowego; jego siłę można dopasować do R_w z danych
   Madara (S-BSST219 ma powtórzenia). Hipoteza warta sprawdzenia: przy bardzo niskiej
   aktywności R_w też spada, więc miara uwzględniająca rzetelność (np. R_w − r_out)
   może mieć optimum — czyli H1 w poprawnej postaci.
5. **Eksperyment Oli i Kingi** to okazja na przewidywanie zapisane przed analizą
   ich danych: co model mówi o częstotliwości, burstach, r_out i R_w po −30% FS→GC.
