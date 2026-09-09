"""
dg_core/metrics.py — metryki separacji, rzadkości i atrybucji motywów.

Atrybucja (kierunek 4) to sedno: mając dekorelację zmierzoną dla wszystkich 2^3
lezji (FF/FB/MC on-off), rozdzielamy ją między motywy wartością Shapleya. To
jedyny podział, który poprawnie rozlicza INTERAKCJE (np. FF i FB dzielą wspólną
drogę FS→GC, więc ich efekty NIE są addytywne — naiwne „on minus off" by kłamało).
"""

from __future__ import annotations

from itertools import combinations
from math import factorial

import numpy as np

from .params import MOTIFS


# ══════════════════════════════════════════════════════════════════════════════
# Separacja
# ══════════════════════════════════════════════════════════════════════════════

def mean_pairwise_r(vecs) -> float:
    """Średnia parami korelacja Pearsona listy wektorów (np. częstotliwości GC)."""
    vecs = list(vecs)
    rs = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            a, b = np.ravel(vecs[i]), np.ravel(vecs[j])
            if a.std() > 1e-9 and b.std() > 1e-9:
                r = float(np.corrcoef(a, b)[0, 1])
                if not np.isnan(r):
                    rs.append(r)
    return float(np.mean(rs)) if rs else 0.0


def decorrelation(r_in: float, r_out: float) -> float:
    """Dekorelacja = R_in − R_out. Dodatnia = obwód rozdzielił wzorce."""
    return r_in - r_out


# ══════════════════════════════════════════════════════════════════════════════
# Rzadkość (potrzebna, by odróżnić „separację" od zwykłego wyciszenia sieci)
# ══════════════════════════════════════════════════════════════════════════════

def population_sparseness(rates: np.ndarray) -> float:
    """
    Rzadkość populacyjna Trevesa–Rollsa: 1 − (Σr)²/(N·Σr²).
    0 = wszystkie komórki równo aktywne, →1 = aktywnych bardzo niewiele.
    """
    r = np.asarray(rates, dtype=float)
    if r.sum() <= 0:
        return 0.0
    num = r.sum() ** 2
    den = len(r) * (r ** 2).sum()
    return float(1.0 - num / den) if den > 0 else 0.0


def active_fraction(rates: np.ndarray, thr_hz: float = 0.5) -> float:
    """Ułamek komórek strzelających powyżej progu."""
    return float((np.asarray(rates) > thr_hz).mean())


# ══════════════════════════════════════════════════════════════════════════════
# Atrybucja motywów — wartość Shapleya
# ══════════════════════════════════════════════════════════════════════════════

def shapley_values(coalition_value: dict, players: tuple = MOTIFS) -> dict:
    """
    Dokładna wartość Shapleya dla n graczy (u nas n=3 → 8 koalicji, liczone wprost).

    `coalition_value`: {frozenset(podzbiór graczy) → wartość (np. dekorelacja)}
    musi zawierać WSZYSTKIE 2^n podzbiorów, łącznie z pustym (obwód bez hamowania).

    φ_i = Σ_{S ⊆ N\\{i}}  |S|!·(n−|S|−1)!/n!  ·  [v(S ∪ {i}) − v(S)]

    Własność, dla której to robimy: Σφ_i = v(pełny obwód) − v(brak hamowania),
    czyli wartości sumują się DOKŁADNIE do całej dekorelacji wniesionej przez
    hamowanie. Można więc mówić „FF odpowiada za X% separacji" bez oszukiwania.
    """
    n = len(players)
    phi = {p: 0.0 for p in players}

    for i in players:
        others = [p for p in players if p != i]
        for size in range(n):
            for S in combinations(others, size):
                S_set = frozenset(S)
                w = factorial(size) * factorial(n - size - 1) / factorial(n)
                marginal = coalition_value[S_set | {i}] - coalition_value[S_set]
                phi[i] += w * marginal

    return phi


def shapley_share(phi: dict) -> dict:
    """Udziały procentowe motywów w całkowitej separacji (znormalizowane |φ|)."""
    total = sum(abs(v) for v in phi.values())
    if total < 1e-12:
        return {k: 0.0 for k in phi}
    return {k: abs(v) / total for k, v in phi.items()}


def dominant_motif(phi: dict, min_effect: float = 0.01) -> str:
    """
    Motyw o największym wkładzie. Zwraca '—', gdy CAŁKOWITY efekt hamowania jest
    poniżej `min_effect` — bo wtedy „dominacja" byłaby szumem, a nie zjawiskiem.
    """
    if sum(phi.values()) < min_effect:
        return '—'
    return max(phi, key=lambda k: phi[k])


def interaction_2way(coalition_value: dict, a: str, b: str) -> float:
    """
    Interakcja dwuczynnikowa (efekt nie-addytywny) między motywami a i b, uśredniona
    po stanach trzeciego motywu:
        I(a,b) = v(ab) − v(a) − v(b) + v(∅)
    < 0 = redundancja / rywalizacja (np. FF i FB pchają ten sam FS→GC);
    > 0 = synergia (razem dają więcej niż suma osobnych wkładów).
    """
    others = [p for p in MOTIFS if p not in (a, b)]
    vals = []
    for size in range(len(others) + 1):
        for S in combinations(others, size):
            S = frozenset(S)
            vals.append(
                coalition_value[S | {a, b}]
                - coalition_value[S | {a}]
                - coalition_value[S | {b}]
                + coalition_value[S]
            )
    return float(np.mean(vals))


# ══════════════════════════════════════════════════════════════════════════════
# Bateria metryk aktywności i informacji — POZA dekorelację.
#
# Motywacja: (a) uwaga prof. Błasiak, że sama dekorelacja może być miarą
# niewystarczającą; (b) wynik negatywny kierunku 1A — dekorelacja nie przełożyła
# się na użyteczność liniową, więc trzeba mierzyć wprost dynamikę (FR, CV, Fano,
# synchronia), rozkład aktywności (entropia) i informację (MI wejście→wyjście).
# Definicje i interpretacje wszystkich metryk: doktorat_plan.md, §5.
#
# Konwencja: gdy metryka jest nieokreślona (za mało spajków, pusta populacja),
# zwracamy NaN — a NIE 0.0, żeby „brak danych" nie udawał wyniku. Agregować
# przez nanmean/nan_mean().
# ══════════════════════════════════════════════════════════════════════════════

def nan_mean(values) -> float:
    """Średnia z pominięciem NaN; NaN gdy nie został żaden element (bez warningów)."""
    v = np.asarray(list(values), dtype=float)
    v = v[np.isfinite(v)]
    return float(v.mean()) if v.size else float('nan')


def _per_neuron_trains(spikes, n_neurons: int) -> list:
    """(idx, t_ms) ze SpikeMonitora → lista czasów spajków każdego neuronu.

    SpikeMonitor zwraca spajki posortowane po czasie; stabilny sort po indeksie
    zachowuje więc rosnący czas wewnątrz każdego neuronu.
    """
    idx = np.asarray(spikes[0], dtype=np.int64)
    t = np.asarray(spikes[1], dtype=float)
    order = np.argsort(idx, kind='stable')
    idx_s, t_s = idx[order], t[order]
    bounds = np.searchsorted(idx_s, np.arange(n_neurons + 1))
    return [t_s[bounds[i]:bounds[i + 1]] for i in range(n_neurons)]


def _count_matrix(spikes, n_neurons: int, T_ms: float, bin_ms: float) -> np.ndarray:
    """Macierz zliczeń [n_neurons × n_bins] — wspólny półprodukt Fano i synchronii."""
    idx = np.asarray(spikes[0], dtype=np.int64)
    t = np.asarray(spikes[1], dtype=float)
    n_bins = max(1, int(T_ms // bin_ms))
    b = np.minimum((t / bin_ms).astype(np.int64), n_bins - 1)
    flat = np.bincount(idx * n_bins + b, minlength=n_neurons * n_bins)
    return flat.reshape(n_neurons, n_bins)


def isi_cv(spikes, n_neurons: int) -> float:
    """
    Średni współczynnik zmienności interwałów międzyspajkowych CV(ISI) = σ_ISI/μ_ISI,
    po neuronach z ≥ 3 spajkami (potrzeba ≥ 2 interwałów).
    ~1 = Poisson (nieregularnie), <1 = regularny zegar, >1 = bursty.
    """
    cvs = []
    for ts in _per_neuron_trains(spikes, n_neurons):
        if len(ts) >= 3:
            isi = np.diff(ts)
            m = isi.mean()
            if m > 0:
                cvs.append(isi.std() / m)
    return nan_mean(cvs)


def fano_factor(spikes, n_neurons: int, T_ms: float, bin_ms: float = 50.0) -> float:
    """
    Średni czynnik Fano zliczeń w oknach `bin_ms`: FF_i = var(n_i)/mean(n_i),
    po neuronach o niezerowej średniej. 1 = Poisson, <1 sub-, >1 nadpoissonowsko.
    Uwaga: niestacjonarność (transjent startowy, wolne modulacje) ZAWYŻA FF —
    to cecha metryki, nie błąd; porównywać między warunkami przy tym samym T i binie.
    """
    counts = _count_matrix(spikes, n_neurons, T_ms, bin_ms)
    mean = counts.mean(axis=1)
    mask = mean > 0
    if not mask.any():
        return float('nan')
    var = counts.var(axis=1)
    return float(np.mean(var[mask] / mean[mask]))


def synchrony_index(spikes, n_neurons: int, T_ms: float, bin_ms: float = 5.0) -> float:
    """
    Indeks synchronii χ (Golomb–Rinzel) na zliczeniach w binach `bin_ms`:
        χ = sqrt( var_t(sygnał populacyjny) / mean_i var_t(sygnał neuronu i) )
    liczony po neuronach AKTYWNYCH (nieaktywne sztucznie zaniżałyby synchronię).
    0 = asynchronicznie, →1 = pełna synchronizacja. Reżim runaway MC powinien
    być widoczny właśnie tutaj.
    """
    counts = _count_matrix(spikes, n_neurons, T_ms, bin_ms)
    active = counts[counts.sum(axis=1) > 0]
    if active.shape[0] < 2:
        return float('nan')
    var_pop = active.mean(axis=0).var()
    mean_var = active.var(axis=1).mean()
    if mean_var <= 0:
        return float('nan')
    return float(np.sqrt(var_pop / mean_var))


def activity_entropy(rates) -> float:
    """
    Znormalizowana entropia Shannona rozkładu aktywności po populacji:
        H = −Σ p_i log2 p_i / log2 N,   p_i = r_i / Σr.
    1 = aktywność rozłożona równo, →0 = skupiona w garstce jednostek.
    Dopełnia rzadkość Trevesa–Rollsa (inna czułość na ogony rozkładu).
    0.0 dla populacji całkiem niemej (świadomie, nie NaN — „brak kodu" to informacja).
    """
    r = np.asarray(rates, dtype=float)
    s = r.sum()
    if s <= 0 or len(r) < 2:
        return 0.0
    p = r / s
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum() / np.log2(len(r)))


def binary_mi_io(pattern, rates, thr_hz: float = 0.5) -> dict:
    """
    Informacja wzajemna wejście→wyjście na poziomie jednostki (bity/jednostkę):
    X = bit wejścia (czy GC dostaje silny napęd PP we wzorcu),
    Y = bit wyjścia (czy GC strzela > thr_hz), estymowana po N jednostkach populacji.

    Mierzy, ile tożsamości wzorca wejściowego przeżywa transformację DG —
    wprost kwantyfikuje „DG jest transformacją stratną" z kierunku 1A.

    Zwraca:
      mi_bits    — MI(X;Y) [bity]
      h_in       — entropia wejścia H(X) [bity] (górna granica MI)
      retention  — MI/H(X) ∈ [0,1]; 1 = pełna informacja o wejściu, 0 = nic
                   (info_loss = 1 − retention)

    Estymator plug-in; bias ≈ (|X||Y|−1)/(2N ln2) ≈ 0.01 bita przy N=200 — pomijalny
    przy porównaniach między warunkami o tym samym N.
    """
    x = np.asarray(pattern, dtype=bool)
    y = np.asarray(rates, dtype=float) > thr_hz
    n = len(x)
    if n == 0 or len(y) != n:
        return {'mi_bits': float('nan'), 'h_in': float('nan'), 'retention': float('nan')}

    def h(p):  # entropia binarna
        p = np.clip(p, 0.0, 1.0)
        terms = [q * np.log2(q) for q in (p, 1 - p) if q > 0]
        return -float(sum(terms))

    px, py = x.mean(), y.mean()
    h_in, h_out = h(px), h(py)

    # entropia łączna z tabeli 2×2
    joint = np.array([
        [np.mean(~x & ~y), np.mean(~x & y)],
        [np.mean(x & ~y),  np.mean(x & y)],
    ]).ravel()
    h_joint = -float(sum(p * np.log2(p) for p in joint if p > 0))

    mi = max(0.0, h_in + h_out - h_joint)
    retention = mi / h_in if h_in > 0 else float('nan')
    return {'mi_bits': mi, 'h_in': h_in, 'retention': retention}


def first_spike_latency(spikes, n_neurons: int) -> tuple[float, float]:
    """
    (średnia, SD) latencji pierwszego spajku po neuronach aktywnych [ms].
    SD to miara precyzji czasowej kodu latencyjnego: mała = neurony odpowiadają
    w wąskim oknie (istotne dla low-latency SNN), duża = odpowiedź rozmyta.
    """
    firsts = [ts[0] for ts in _per_neuron_trains(spikes, n_neurons) if len(ts)]
    if len(firsts) < 2:
        return float('nan'), float('nan')
    f = np.asarray(firsts)
    return float(f.mean()), float(f.std())


# ── Alternatywne miary separacji (kontrola dla dekorelacji Pearsona) ──────────

def mean_pairwise_cosine(vecs) -> float:
    """
    Średnie parami podobieństwo cosinusowe. W odróżnieniu od Pearsona nie centruje
    wektorów — na kodach rzadkich Pearson bywa zdominowany przez wspólne zera,
    cosinus patrzy tylko na część aktywną.
    """
    vecs = [np.ravel(v).astype(float) for v in vecs]
    sims = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            na, nb = np.linalg.norm(vecs[i]), np.linalg.norm(vecs[j])
            if na > 1e-12 and nb > 1e-12:
                sims.append(float(vecs[i] @ vecs[j] / (na * nb)))
    return nan_mean(sims)


def mean_pairwise_jaccard(vecs, thr_hz: float = 0.5) -> float:
    """
    Średni parami współczynnik Jaccarda ZBIORÓW aktywnych jednostek
    (|A∩B|/|A∪B| po binaryzacji rate > thr_hz) — miara nakładania się kodów
    z literatury remappingu/ortogonalizacji. 0 = kody rozłączne, 1 = identyczne.
    """
    bins = [np.ravel(np.asarray(v)) > thr_hz for v in vecs]
    js = []
    for i in range(len(bins)):
        for j in range(i + 1, len(bins)):
            union = (bins[i] | bins[j]).sum()
            if union > 0:
                js.append(float((bins[i] & bins[j]).sum() / union))
    return nan_mean(js)


# ── Komplet dla jednej próby ──────────────────────────────────────────────────

BATTERY_KEYS = ('cv_isi', 'fano', 'synchrony', 'entropy',
                'latency_mean', 'latency_sd', 'mi_io', 'info_retention')


def activity_battery(sim_out: dict, pattern, T_ms: float,
                     thr_hz: float = 0.5) -> dict:
    """
    Pełna bateria metryk aktywności/informacji populacji GC dla jednej próby
    (jednego wyniku `simulate()` + wzorca wejściowego, który ją napędzał).
    Klucze — patrz BATTERY_KEYS; skalary, NaN gdy nieokreślone.
    """
    rates = sim_out['gc_rates']
    spikes = sim_out['gc_spikes']
    n = len(rates)
    lat_mean, lat_sd = first_spike_latency(spikes, n)
    mi = binary_mi_io(pattern, rates, thr_hz)
    return {
        'cv_isi':         isi_cv(spikes, n),
        'fano':           fano_factor(spikes, n, T_ms),
        'synchrony':      synchrony_index(spikes, n, T_ms),
        'entropy':        activity_entropy(rates),
        'latency_mean':   lat_mean,
        'latency_sd':     lat_sd,
        'mi_io':          mi['mi_bits'],
        'info_retention': mi['retention'],
    }
