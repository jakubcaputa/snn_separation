# Stan projektu — model DG i separacja wzorców

*Aktualizacja: 2026-09-14. Ten plik odpowiada na jedno pytanie: **gdzie jestem
i co dalej**. Jest źródłem prawdy dla STANU prac — nie dla hipotez ani planów.*

> **Cztery dokumenty, cztery role** — jeśli szukasz czegoś innego, to jest gdzie indziej:
> | dokument | odpowiada na pytanie | czego tu NIE ma |
> |---|---|---|
> | `README.md` | gdzie co leży, jak uruchomić | stanu prac i planów |
> | `STATUS.md` | **gdzie jestem, co blokuje, co dalej** | uzasadnień naukowych |
> | `doktorat_plan.md` | dokąd to zmierza na poziomie doktoratu | szczegółów artykułu |
> | `PLAN_PUBLIKACJI.md` | plan artykułu do PLOS Comp Biol | bieżącego stanu prac |

---

## 1. Gdzie jesteś w tej chwili

Model działa i daje powtarzalne wyniki. **Blokadą nie jest kod, tylko trzy
decyzje biologiczne**, które wyszły w korespondencji z prof. Błasiak (mail
wysłany 2026-09-11, odpowiedź nie przyszła). Maszyneria kalibracyjna jest
gotowa i czeka na te trzy liczby.

| obszar | stan |
|---|---|
| Narzędzie `interactive_dg.py` | działa, rozbudowane o bilans hamowania i panel P(AP) |
| Rdzeń `dg_core` | działa, regresja bit-w-bit vs stan sprzed zmian |
| **E2** — atrybucja motywów (Shapley) | maszyneria gotowa, wynik wstępny stabilny |
| **E1** — mapa reżimów → testuje **H1, H2** | uruchamialne, wynik wstępny **ostrzegawczy** (§5) |
| **E4/E5** — kontroler → testują **H3, H4** | **niezbudowane** ← niosą ciężar publikacji |
| Kalibracja punktu pracy | maszyneria gotowa, **specyfikacja niedomknięta** (§3) |
| Właściwości błony z danych Madara | **wyciągnięte**, 91 komórek (§4) |
| Odczyt downstream 1A | zamknięte, wynik negatywny |
| Odczyt downstream 1B | odłożone, wymaga N_GC ≥ 2000 na HPC |

---

## 2. Co jest zrobione i nadal prawdziwe

**Reżim wejścia (skalibrowany, `dg_params.py` = jedyne źródło prawdy).**
40 włókien PP × 10 Hz = 400 Hz aggregate na aktywny GC. Przy 600 Hz GC dawały
16.6 Hz (za gęsto); 400 Hz daje ~6 Hz, czyli rzadkie kodowanie DG. Tryb
per-fiber i zagregowany są spójne.

**K_tonic = toniczne hamowanie, próg `G_crit = 4 + K`.** Wyprowadzone
analitycznie i potwierdzone symulacją co do 0.1 mV. GC/HMC (K=10, G_crit=14)
trudniej pobudliwe niż FS (K=5, G_crit=9). Napęd 400 Hz daje g_ex ≈ 8 mV, czyli
poniżej progu GC → reżim fluktuacyjny → separacja.

**Mossy cells są przy domyślnych wagach martwe (0.00 Hz).** Napęd GC→HMC
(1 mV) nie zbliża się do progu 14 mV. **Każdy wniosek o roli MC przy domyślnych
ustawieniach dotyczy obwodu BEZ nich.** Stąd dwa jawne reżimy w sweepach:
`mc_inert` i `mc_active`.

**Atrybucja motywów (preset quick, 576 symulacji, stabilne):**
```
[mc_inert]   FF 49.9%  FB 50.1%  MC  0.0%     dekorelacja +0.067 → +0.143
[mc_active]  FF 79.2%  FB 115.3% MC −94.5%    dekorelacja +0.067 → +0.244
```
φ_MC ujemne: mossy cells same korelują wzorce, ale w parze z hamowaniem
podnoszą separację najmocniej. **MC to motyw warunkowy.**

**Hamulec FS→HMC — najmocniejszy istniejący wynik.** Pętla GC→HMC→GC jest
czysto pobudzająca i bez hamulca nie ma reżimu pośredniego: dekorelacja −0.267
(obwód *koreluje* wzorce) przy `W_FS_HMC=0` vs **+0.247** przy `W_FS_HMC=2`.

**Wynik negatywny 1A.** „DG poprawia klasyfikację liniową" sprawdzone i obalone
(raw 0.940 vs dg 0.885). Uczciwe uzasadnienie przejścia na miary informacyjne.

---

## 3. ⛔ CO BLOKUJE — czeka na prof. Błasiak

Mail wysłany 2026-09-11. Bez tych odpowiedzi kalibracja nie domknie się,
bo każda próba trafia w jedno kryterium kosztem drugiego.

### B1. Jaki jest realny udział prądu tonicznego w hamowaniu GC?

Zmierzone w modelu (wkłady do `dv/dt`, te same jednostki):

| komórka | pobudzenie | hamowanie FAZOWE | hamowanie TONICZNE (K) | udział tonicznego |
|---|---|---|---|---|
| **GC** | PP 2.43 | FS→GC **3.59** | **10.0** | **74%** |
| **FS** | PP 7.32 + GC 1.85 | 0.0 (**kanał nie istniał**) | 5.0 | 100% |
| **HMC** | GC 0.20 | 0.0 (`W_FS_HMC=0`) | 10.0 | 100% |

74% to wartość **odziedziczona, nie wybrana**. Dotychczasowe zdania o
„hamowaniu tworzącym separację" mogą w większości dotyczyć składnika tonicznego,
a nie obwodu FS. Odpowiedź wymusza K — a przez to (patrz §6, pułapka 4) wymusza
też próg i potencjał spoczynkowy.

### B2. Czy ~46 Hz to fizjologiczna częstotliwość bazowa FS?

Prawdopodobnie zawyżona z przyczyny **strukturalnej**, nie doboru wag: FS nie
miały w modelu żadnego hamowania synaptycznego. Kanał FS→FS został dodany
(§4) i obniża FS z 46 do 28 Hz, ale jego siła wymaga zakotwiczenia.

### B3. Do którego reżimu wejścia kalibrujemy — in vitro czy in vivo?

**To jest pytanie najważniejsze i jedyne, którego wcześniej nie zadaliśmy wprost.**
Waga dobrana protokołem pulsowym Madara (tło 40 Hz) użyta w sieci przy napędzie
400 Hz daje GC **22 Hz zamiast 2–6 Hz**. Dziesięciokrotna różnica reżimu —
jedna waga nie obsłuży obu. Rzadka stymulacja w plastrze i gęsty napęd PP to
dwa różne punkty pracy i trzeba wybrać, który jest warunkiem kontrolnym.

---

## 4. ✅ CO MOŻNA ROBIĆ BEZ TYCH ODPOWIEDZI — i co już zrobione

### Zrobione 2026-09-14

**Właściwości błony z danych Madara** (`dg_core/madar_intrinsics.py`).
Madar opisał każdą komórkę wprost w swoich plikach MATLAB — bierzemy pomiar
eksperymentatora zamiast odtwarzać go z sygnału. Po deduplikacji po ID
(surowo 72 → faktycznie 42 komórki GC; **bez deduplikacji mediana wychodzi
−70 zamiast −76**):

| typ | n | V_rest [mV] mediana [IQR] | τ_m [ms] | Rm [MΩ] |
|---|---|---|---|---|
| GC | 53 | **−76 [−81…−70]** (n=42) | 3 [2–5] | 130 [94–198] |
| FS | 4 | −70 [−72…−65] | 1 | 51 |
| HMC | 19 | −67 [−74…−60] | — | — |
| CA3 | 15 | −72 [−76…−68] | — | — |

**To rozstrzyga spór o K.** Model przy `K_GC=10` daje V_rest = −78.7 mV, czyli
**wewnątrz IQR danych**; przy `K_GC=0` daje −70 mV, czyli na górnej krawędzi.
Wartość „około −70 mV" z maila odpowiada górnemu kwartylowi, nie medianie —
więc obecne `K_GC=10` jest przez dane **wspierane**, a nie podważane.

⚠️ Rozbieżność do opisania w Methods: **τ_m z danych to ~3 ms dla GC**, podczas
gdy w mailu mowa o 10–50 ms. Izhikevich i tak nie ma jawnego τ_m (szybka
składowa ~1 ms, całkowanie niosą stałe synaptyczne 5/8 ms). Warto zapytać, czy
rozbieżność bierze się z definicji (Rm wejściowe vs błonowe).

**Kanał FS→FS** (`W_FS_FS`, domyślnie 0.0 — obwód bez zmian). Wzajemne
hamowanie interneuronów, którego w modelu w ogóle nie było. Działa zgodnie
z oczekiwaniem:

| `W_FS_FS` | 0.0 | 0.5 | 1.0 | 2.0 | 4.0 |
|---|---|---|---|---|---|
| FR_FS [Hz] | 46.0 | 41.8 | 37.8 | 33.4 | 27.6 |
| FR_GC [Hz] | 3.12 | 3.09 | 3.37 | 3.65 | 4.08 |

**Mapa reżimów = eksperyment E1** (`experiments/e1_regime_map/`, testuje H1 i H2) — brakujący eksperyment.
Dotychczasowa siatka zmienia statystykę wejścia i odpowiada na pytanie o
ATRYBUCJĘ; nie ma w niej ani jednej osi hamowania, więc **nie mogła odpowiedzieć
na H1** (czy istnieje okno funkcjonalne). Nowy skrypt zamraża wejście i zmienia
`K_GC` × `W_FS_GC`, a główną osią jest **zmierzona frakcja aktywnych GC**.

### Do zrobienia dalej (kolejność wg wartości)

1. **Pełna mapa reżimów na HPC** — po wyniku wstępnym (§5) potrzebna szersza
   siatka i zaostrzona maska ważności. Bez tego H1 wisi w powietrzu.
2. **Skrypt analizy mapy reżimów** (`analyze_regime_map.py`) — figura
   „separacja vs aktywność" z panelem kontrolnym i przedziałami ufności.
3. **Kalibracja siły FS→FS** do docelowej częstotliwości FS (czeka na B2, ale
   maszyneria bisekcji już jest w `calibrate.py`).
4. **Krzywe f–I z CCIV.** Protokół prądowy JEST odzyskiwalny z adnotacji Axographu
   (`Pulse #1 … -100, 20` → start −100 pA, krok 20 pA, 30 epizodów, onset 100 ms,
   szerokość 500 ms). Dostępne: HMC 26 plików, GC+CA3 66. **FS nie mają ani
   jednego CCIV** — ich parametry tylko z adnotacji (4 komórki wyżej).
5. **Pełna siatka atrybucji na Aresie** z całą baterią metryk (~35 tys. symulacji,
   ~12 h CPU — obliczenia nie są ograniczeniem).

---

## 5. ⚠️ Wynik wstępny mapy reżimów — ostrzeżenie, nie potwierdzenie

Preset `quick` (12 punktów, 1 seed) **nie potwierdza H1**. Separacja rośnie
monotonicznie w miarę cichnięcia sieci, a maksimum leży na krańcu siatki:

```
maksimum separacji przy 8.0% aktywnych GC (dekorelacja 0.558)
⚠️ monotonicznie ku rzadszej aktywności, maksimum na KRAŃCU siatki
   → sygnatura artefaktu wyciszenia, nie okna funkcjonalnego
```

To jest dokładnie pułapka 3 z §6. Skrypt sam to wykrywa i mówi wprost. Zanim
z tego cokolwiek wyniknie, trzeba rozszerzyć siatkę i zaostrzyć maskę
(`MIN_ACTIVE_FRAC`, `MIN_FR_ACTIVE`) — i sprawdzić, czy maksimum przesunie się
do wnętrza. **Nie raportować tej liczby jako wyniku.**

---

## 6. Ustalenia, o których nie wolno zapomnieć

Cztery pułapki obowiązujące w każdym nowym sweepie (pełny opis: `doktorat_plan.md` §4):

1. **Skalowanie:** zawsze `DGConfig.scaled(N)`, nigdy gołe `N_GC=`. Inaczej obwód
   cicho umiera, a dekorelacja pokazuje +0.77, bo korelacja pustego wektora = 0.
2. **MC przy domyślnych wagach są martwe** — zawsze dwa reżimy `mc_inert`/`mc_active`.
3. **Separacja czy wyciszenie?** Dekorelacja przy FR→0 to artefakt. Każda analiza
   musi mieć maskę ważności i panel kontrolny FR/frakcji aktywnych.
4. **`K_GC` pełni TRZY role naraz** — ustala próg efektywny, potencjał spoczynkowy
   **i** cały budżet hamowania tonicznego. Nie da się ich wybrać niezależnie.
   Każde zdanie „zwiększyliśmy hamowanie, podnosząc K" jest jednocześnie zdaniem
   „zmieniliśmy właściwości błony". Przy raportowaniu manipulacji na K zawsze
   podawać wynikowe (V_rest, V_th_eff).

Dwie własności strukturalne modelu, wykryte przy kalibracji:

- **`b` ustawia SUMĘ `V_rest + V_th_eff`, `K` ich ODSTĘP.** Przy `b = 0.2` suma
  jest zablokowana na −120 mV: para (−70, −50) wychodzi przy `K = 0`, a (−70, −45)
  jest nieosiągalna żadnym K — wymaga `b = 0.4`, i wtedy K rośnie do 14.
- **P(AP|puls) nie jest sterowalne samą wagą.** Bez źródła zmienności krzywa jest
  skokowa (0.00 → 0.99). Stąd zawodność synaptyczna `P_REL_*`: przy kompensacji
  wagą `W/p` wariancja rośnie jak `1/p`, co daje stopniowane P(AP) przy
  niezmienionym średnim napędzie (zmierzone: FR 3.12 → 5.46 → 9.22 Hz dla
  p_rel 1.0 → 0.5 → 0.25). ⚠️ `p_rel` i wagę kalibrować RAZEM.

---

## 7. Jak co uruchomić

```bash
# narzędzie interaktywne
snn_sep_venv/Scripts/python.exe -m streamlit run interactive_dg.py

cd experiments

# kalibracja punktu pracy
python -m dg_core.calibrate --preset madar      # (−70, −50) — osiągalne przy b=0.2
python -m dg_core.calibrate --preset strict     # (−70, −45) — wymaga zmiany b
python -m dg_core.calibrate --tonic-share 0.5   # gdy B1 będzie znane

# właściwości błony z danych Madara
python -m dg_core.madar_intrinsics

# eksperymenty
cd e1_regime_map && python run_regime_map.py --preset quick     # E1 → H1, H2
cd ../e2_motif_attribution
python run_lesion_grid.py --preset quick                       # E2 → atrybucja
python analyze_motifs.py --in results/lesion_grid_quick.npz

# testy regresji
snn_sep_venv/Scripts/python.exe -m pytest tests/ -q     # 17 testów
```

**Gwarancja odtwarzalności:** wszystkie nowe parametry mają wartości neutralne
(`p_rel = 1.0`, `delay_jitter_ms = 0.0`, `W_FS_FS = 0.0`, `b_gc = 0.2`), a przy
`p_rel ≥ 1.0` kod bierze gałąź, która nie zużywa ani jednej liczby losowej.
Hash spajków jest identyczny ze stanem sprzed wszystkich zmian — **żaden
wcześniejszy wynik nie wymaga przeliczenia.**

---

## 8. Mapa plików

Pełna mapa i zasady repo: **`README.md`** (nowy, 2026-09-14).

```
README.md                  od czego zacząć — mapa kodu i pułapki
STATUS.md                 TEN plik — stan projektu i co blokuje
doktorat_plan.md           kierunki badawcze, hipotezy, plan publikacji
interactive_dg.py          narzędzie Streamlit — docelowy produkt
dg_params.py               jedyne źródło prawdy dla częstotliwości wejścia
experiments/README.md      ← mapa eksperyment→hipoteza→folder
experiments/dg_core/       rdzeń modelu (+ calibrate.py, madar_intrinsics.py)
experiments/e1_regime_map/        E1 → hipotezy H1, H2 (okno funkcjonalne)
experiments/e2_motif_attribution/ E2 → który motyw tworzy okno (Shapley)
experiments/readout_deferred/     1A zamknięte, 1B odłożone
experiments/hpc/           SLURM (Ares/PLGrid)
separation_parameters_sweep/    linia LIF + parameters.md (opis τ_m, V_th, V_reset)
tests/                     17 testów regresji i kalibracji
archive/                   skrypty, które zrobiły swoje — patrz archive/README.md
prezentacja/               materiały na spotkania
dataset/                   dane Madara (poza gitem)
```

**Sprzątanie 2026-09-14.** Usunięto 16 plików z korzenia: `debug_*.py` (7 roboczych),
`visualize_dg*.py` (4 generatory figur), jednorazowe eksploratory
(`dataset_overview.py`, `explore_gc1_r090.py`) oraz warianty zastąpione przez
`dg_core` (`dg_microcircuit_brian2.py`, `single_neuron_patsep_{brian2,nest}.py`).
Wszystko zostaje w historii gita. Do `archive/` przeniesiono cztery skrypty, które
wyprodukowały wnioski nadal obowiązujące (`bifurcation_K.py`, `freq_audit.py`,
`dg_module3_inh_comparison.py`, `explore_data.py`) — mają naprawione ścieżki
i uruchamiają się. Korzeń repo: z 25 plików do 5.
