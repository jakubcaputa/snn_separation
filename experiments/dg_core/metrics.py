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
