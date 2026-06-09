# Parametry modelu LIF (Granule Cell) — opis

Każdy parametr jest zmieniany niezależnie przy zachowaniu pozostałych na wartościach domyślnych.
Miara efektu: **Pattern Separation Index = R_in − R_out** (im wyższy, tym lepsza separacja wzorców).

---

## Parametry neuronu

### `tau_m` — stała czasowa błony [ms]
**Domyślnie: 20 ms**

Opisuje jak szybko potencjał błony wraca do stanu spoczynkowego po zaburzeniu.
Wynika z iloczynu pojemności błony i rezystancji błony: τ_m = R_m · C_m.

- **Małe τ_m** → błona „zapomina" wejście szybko → neuron reaguje tylko na bieżące spiki → większa selektywność czasowa
- **Duże τ_m** → błona integruje wejście przez długi czas → neuron sumuje wiele kolejnych spików → mniejsza selektywność, wyższy FR

---

### `V_thr` — próg akcji [mV]
**Domyślnie: −55 mV** (15 mV powyżej V_rest = −70 mV)

Wartość potencjału, przy której neuron odpala potencjał czynnościowy.

- **Niski próg** (bliżej V_rest) → neuron odpala często, prawie na każde wejście → mała selektywność → słaba separacja
- **Wysoki próg** (daleko od V_rest) → neuron odpala rzadko, tylko przy dużych fluktuacjach → rzadki, rzadki kod → lepsza separacja, ale FR spada do zera przy zbyt wysokim progu

---

### `t_ref` — bezwzględny okres refrakcji [ms]
**Domyślnie: 3 ms**

Czas po każdym spiku, w którym neuron jest „zablokowany" i nie może odpalić ponownie niezależnie od wejścia.

- **Krótki t_ref** → neuron może odpalać bardzo gęsto → mała rzadkość kodu
- **Długi t_ref** → ogranicza maksymalne FR → wymusza rzadki kod → więcej separacji, ale przy bardzo długich wartościach FR staje się zbyt niski, by mierzyć korelację

---

### `V_reset` — potencjał resetu po spiku [mV]
**Domyślnie: −78 mV** (8 mV poniżej V_rest)

Wartość, do której potencjał błony jest natychmiast przywracany po odpaleniu spiku.
Odpowiada hyperpolaryzacji po potencjale czynnościowym (AHP — afterhyperpolarization).

- **Głęboki reset** (bardzo ujemny, np. −95 mV) → silna AHP → neuron potrzebuje dużo czasu, by ponownie naładować się do progu → mała częstość odpalania
- **Płytki reset** (bliski V_rest lub V_thr) → prawie brak AHP → neuron może natychmiast odpalić ponownie → bardzo wysokie FR przy V_reset → V_thr

---

## Parametry synaptyczne

### `tau_syn` — stała czasowa synapsy [ms]
**Domyślnie: 5 ms** (typowe dla receptorów AMPA)

Opisuje jak szybko zanika prąd synaptyczny po przybyciu spiku presynaptycznego.

- **Mała τ_syn** → prąd krótki, impulsowy → neuron widzi każdy prespike oddzielnie → większa rozdzielczość czasowa
- **Duża τ_syn** → prąd długi (jak receptory NMDA, ~50 ms) → wejścia są uśredniane w czasie → neuron reaguje na średni poziom aktywności, nie na poszczególne spiki → mniejsza selektywność

---

### `n_syn` — liczba synaps wejściowych
**Domyślnie: 40** (perforant path → granule cell)

Liczba niezależnych włókien wejściowych (perforant path) konwergujących na jeden neuron GC.

- **Mało synaps** → duże fluktuacje prądu wejściowego (mała liczba → duże odchylenia standardowe) → neuron jest bardziej „zaskakiwany" przez poszczególne spiki → potencjalnie więcej separacji, ale też większy szum
- **Dużo synaps** → prawo dużych liczb → prąd wejściowy jest gładki i przewidywalny → neuron strzela regularnie i podobnie dla podobnych wzorców → mniej separacji

---

### `W_SYN` — waga synaptyczna [mV]
**Domyślnie: 6 mV**

Amplituda skoku prądu synaptycznego wywołanego przez jeden prespike. Określa jak mocno jeden sygnał wejściowy depolaryzuje błonę.

- **Mała waga** → każdy prespike daje słaby sygnał → neuron odpala rzadko lub wcale (FR → 0)
- **Duża waga** → nawet jeden prespike silnie depolaryzuje błonę → neuron odpala bardzo często → saturacja, wszystkie wzorce dają podobny, gęsty output → separacja zanika

Istnieje optymalny przedział wag, w którym neuron pracuje w reżimie subprogowym z fluktuacjami — tu separacja jest największa.

---

### `r_input` — średnie tempo wejściowe [Hz]
**Domyślnie: 10 Hz**

Średnia częstotliwość odpalania każdego z `n_syn` włókien wejściowych (niezależne procesy Poissona).

- **Niski r_input** → mało spików wejściowych → mały prąd → neuron rzadko przekracza próg → separacja potencjalnie wysoka, ale FR wyjściowy bardzo niski
- **Wysoki r_input** → intensywne bombardowanie wejściowe → prąd wysoki → neuron odpala gęsto → podobne wzorce dają podobny gęsty output → separacja zanika

Wraz z `W_SYN` i `n_syn` wyznacza średni drive: `g_mean = n_syn × r_input × W_SYN × tau_syn`.

---

## Związki między parametrami

Średni prąd synaptyczny (drive) zależy od trzech parametrów jednocześnie:

```
g_mean = n_syn × r_input × W_SYN × tau_syn
```

Separacja wzorców jest największa gdy neuron pracuje **podprogowo z fluktuacjami** —
tzn. g_mean jest nieco poniżej progu, a spiki są generowane tylko przez odchylenia
statystyczne od średniej. Każdy parametr, który przesuwa neuron z tego reżimu
(zbyt niskie FR lub zbyt wysokie FR), pogarsza separację.
