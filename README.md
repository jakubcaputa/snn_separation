# Separacja wzorców w zakręcie zębatym (DG) — model sieci spajkującej

Model obwodu DG (komórki ziarniste, interneurony FS, mossy cells) służący do
badania, **co utrzymuje sieć w reżimie, w którym separuje wzorce** — i czy da się
tym sterować automatycznie. Brian2 + Streamlit.

---

## Od czego zacząć czytać

**Cztery dokumenty, cztery role.** Każdy temat ma jedno miejsce kanoniczne —
pozostałe wskazują, zamiast powtarzać (bo powtórzone treści się rozjeżdżają).

| dokument | odpowiada na pytanie | co jest tu kanoniczne |
|---|---|---|
| `README.md` | gdzie co leży, jak uruchomić | mapa kodu, komendy |
| **`STATUS.md`** ← **zacznij tutaj** | **gdzie jestem, co blokuje, co dalej** | stan prac, zmierzone liczby |
| `doktorat_plan.md` | dokąd to zmierza na poziomie doktoratu | §4 pułapki · §5a metryki · §8 kierunki · §9 otwarte kwestie |
| `PLAN_PUBLIKACJI.md` | plan artykułu do PLOS Comp Biol | §2.3 hipotezy H1–H5 · §3.4 E1–E7 · §6 oś czasu · §7 figury |

Model klikalnie: uruchom `interactive_dg.py` (komendy niżej).

⚠️ `doktorat_plan.md` jest **poza gitem** (`.gitignore`), a kod się do niego
odwołuje w komentarzach. Po sklonowaniu repo tych odnośników nie da się otworzyć.

---

## Mapa kodu

```
README.md                 ten plik — mapa i komendy
STATUS.md                 stan prac: co blokuje, co dalej
doktorat_plan.md          plan doktoratu (⚠ poza gitem)
PLAN_PUBLIKACJI.md        plan artykułu do PLOS Comp Biol

interactive_dg.py         ⭐ narzędzie Streamlit — DOCELOWY PRODUKT
                             dwa tryby: pojedynczy neuron (LIF) i sieć (Izhikevich)
dg_params.py              jedyne źródło prawdy dla częstotliwości wejścia PP
                             (40 włókien × 10 Hz = 400 Hz aggregate)

experiments/              ← ma własny README.md (numeracja „kierunków", pułapki)
  dg_core/                rdzeń obwodu bez Streamlita — JEDNO ŹRÓDŁO MODELU
    params.py             DGConfig: pełna konfiguracja (zamrożona dataclass)
    circuit.py            simulate(): jedna próba obwodu GC/FS/HMC
    patterns.py           wzorce wejściowe o zadanej korelacji
    metrics.py            dekorelacja, Shapley, bateria metryk informacyjnych
    calibrate.py          kalibracja do zadanego PUNKTU PRACY
    madar_intrinsics.py   właściwości błony wyciągnięte z danych Madara
    viz.py                wspólna paleta i styl figur

  e1_regime_map/          E1 — ile hamowania jest optymalne   → hipotezy H1, H2
  e2_motif_attribution/   E2 — który motyw niesie separację    → Shapley
  readout_deferred/       1A zamknięte (negatywne), 1B odłożone
  hpc/                    skrypty SLURM (Ares / PLGrid)

  (E3–E7 z planu publikacji jeszcze nie istnieją; E4 i E5 testują H3/H4,
   czyli hipotezy niosące ciężar artykułu — patrz experiments/README.md)

separation_parameters_sweep/   linia LIF pojedynczego neuronu
                                 parameters.md = opis τ_m, V_th, V_reset
single_neuron_patsep.py        (jej zależność)

tests/                    regresja modelu i kalibracji — 17 testów
archive/                  skrypty, które zrobiły swoje (patrz archive/README.md)
prezentacja/              materiały na spotkania
papers/                   prace Madara w PDF (poza gitem)
dataset/                  dane Madara (poza gitem — BioStudies S-BSST219)
```

**Zasada, która obowiązuje w tym repo:** `experiments/dg_core/` i `interactive_dg.py`
mają trzymać ten sam model. Zmiana w obwodzie musi trafić w oba miejsca, inaczej
powstaje drugie źródło prawdy i wyniki eksperymentów przestają odpowiadać temu,
co widać w narzędziu.

---

## Uruchamianie

```bash
# narzędzie interaktywne
snn_sep_venv/Scripts/python.exe -m streamlit run interactive_dg.py

cd experiments

# kalibracja punktu pracy
python -m dg_core.calibrate --preset madar      # (−70, −50) — osiągalne przy b=0.2
python -m dg_core.calibrate --preset strict     # (−70, −45) — wymaga zmiany b
python -m dg_core.madar_intrinsics              # właściwości błony z danych

# eksperymenty  (każdy ma --preset quick do sanity checku)
cd e1_regime_map && python run_regime_map.py --preset quick     # E1 → H1, H2
cd ../e2_motif_attribution
python run_lesion_grid.py --preset quick                       # E2 → atrybucja
python analyze_motifs.py --in results/lesion_grid_quick.npz

# testy
snn_sep_venv/Scripts/python.exe -m pytest tests/ -q
```

Środowisko: `snn_sep_venv` (Brian2 2.10.1, numpy 2.4, matplotlib 3.10, neo 0.14,
streamlit 1.57, pytest). Pełna siatka leci na Aresie — patrz `experiments/hpc/`.

---

## ⚠️ Cztery pułapki, które cicho psują wyniki

Pełny opis w `doktorat_plan.md` §4. Skrót, bo każda z nich już raz uderzyła:

1. **Skalowanie sieci:** zawsze `DGConfig.scaled(N)`, nigdy gołe `N_GC=`.
   Inaczej obwód umiera, a dekorelacja pokazuje +0.77 — bo korelacja pustego
   wektora wynosi 0.
2. **Mossy cells przy domyślnych wagach są martwe** (0.00 Hz). Każdy wniosek
   o ich roli dotyczy wtedy obwodu BEZ nich. Zawsze dwa reżimy: `mc_inert` / `mc_active`.
3. **Separacja czy wyciszenie?** Dekorelacja przy FR→0 to artefakt. Każda analiza
   musi mieć maskę ważności i panel kontrolny częstotliwości.
4. **`K_GC` pełni trzy role naraz** — ustala próg efektywny, potencjał spoczynkowy
   *i* cały budżet hamowania tonicznego. „Zwiększyliśmy hamowanie, podnosząc K"
   znaczy jednocześnie „zmieniliśmy właściwości błony".

---

## Odtwarzalność

Wszystkie parametry dodane we wrześniu 2026 mają wartości neutralne
(`p_rel = 1.0`, `delay_jitter_ms = 0.0`, `W_FS_FS = 0.0`, `b_gc = 0.2`), a przy
`p_rel ≥ 1.0` kod bierze gałąź, która nie zużywa ani jednej liczby losowej.
Hash spajków domyślnej konfiguracji jest identyczny ze stanem sprzed tych zmian —
**żaden wcześniejszy wynik nie wymaga przeliczenia.** Pilnują tego testy w `tests/`.
