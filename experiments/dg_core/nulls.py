"""
dg_core/nulls.py — modele zerowe o DOPASOWANEJ RZADKOŚCI.

Po co to istnieje
-----------------
`dec = r_in − r_out` miesza dwie rzeczy, których nie wolno mylić:

  1. dekorelację, którą robi OBWÓD (to, o co pytamy),
  2. dekorelację, którą gwarantuje sama RZADKOŚĆ (to, co dostajemy za darmo,
     bo korelacja prawie pustych wektorów dąży do zera).

Dopóki mierzy się samo `dec`, składnik 2 rośnie przy wyciszaniu sieci i udaje
wynik. E1 w wersji z siatką `K_GC × W_FS_GC` przewrócił się dokładnie na tym:
maksimum separacji jechało za progiem maski ważności przy każdym progu, jaki mu
podstawić (STATUS sek. 3.3). Maska tego nie leczy — tylko ucina zdegenerowany obszar,
a maksimum siada na linii cięcia.

Lekarstwo: policzyć, ile dekorelacji miałby kod o TEJ SAMEJ rzadkości, ale bez
obwodu, i odjąć. Nadwyżka `dec − dec_null` znika przy wyciszeniu **z konstrukcji**,
bo null wycisza się razem z siecią. Artefakt się skraca, zamiast być maskowany.

Dwa null-e, bo odpowiadają na różne pytania
-------------------------------------------
`shuffle`  — permutacja wektora wyjściowego po neuronach, osobno dla każdego
             wzorca. Rozkład częstotliwości zostaje CO DO WARTOŚCI, znika
             odpowiedniość wzorzec→neuron. Pyta: „czy separacja jest w tym,
             KTÓRY neuron strzela, czy tylko w tym, ILU ich strzela?"

`kwta`     — losowa rzadka projekcja wejścia z liczbą aktywnych dopasowaną do
             wyjścia DG. Pyta mocniej: „czy DOWOLNY rzadki kod o tej rzadkości
             nie zrobiłby tego samego?" To ta sama kontrola, którą kierunek 1A
             nazywa `random` i na której DG tam przegrało (STATUS sek. 3.7).
"""

from __future__ import annotations

import numpy as np

from .metrics import mean_pairwise_r

__all__ = ['shuffle_null_vectors', 'kwta_random_projection', 'separation_vs_null']


def shuffle_null_vectors(vecs, rng: np.random.Generator) -> list:
    """Permutuje każdy wektor po neuronach — rozkład zostaje, struktura znika."""
    return [rng.permutation(np.asarray(v)) for v in vecs]


def kwta_random_projection(X: np.ndarray, k: int,
                           rng: np.random.Generator) -> np.ndarray:
    """
    Losowa rzadka ekspansja: X @ W, potem k-WTA (zostaw k najsilniejszych, reszta 0).

    To jest kontrola „rzadkość bez DG": ta sama wymiarowość i ta sama liczba
    aktywnych jednostek co w wyjściu GC, ale selekcja losowa, nie przez obwód.
    """
    n_feat = X.shape[1]
    W = rng.normal(0, 1 / np.sqrt(n_feat), size=(n_feat, n_feat))
    H = X @ W
    if k <= 0 or k >= n_feat:
        return H
    thr = np.partition(H, -k, axis=1)[:, -k][:, None]
    return np.where(H >= thr, H, 0.0)


def separation_vs_null(gc_vecs, pats, r_in: float, rng: np.random.Generator,
                       thr_hz: float = 0.5, n_rep: int = 20) -> dict:
    """
    Separacja obwodu i separacja null-i o dopasowanej rzadkości.

    Zwraca `dec` (jak dotąd) oraz NADWYŻKI ponad oba null-e. Nadwyżka jest tym,
    co wolno przypisać obwodowi; samo `dec` nie jest.

    `n_rep` losowań uśredniamy, bo pojedyncza permutacja ma własny rozrzut —
    przy 4 wzorcach szum null-a byłby porównywalny z mierzonym efektem.
    """
    dec = r_in - mean_pairwise_r(gc_vecs)

    # ile jednostek jest aktywnych w wyjściu DG — tyle samo dostanie null k-WTA
    k_active = int(round(float(np.mean([(np.asarray(v) > thr_hz).sum() for v in gc_vecs]))))

    dec_shuf = float(np.mean([
        r_in - mean_pairwise_r(shuffle_null_vectors(gc_vecs, rng)) for _ in range(n_rep)]))

    X = np.asarray(pats, dtype=float)
    dec_kwta = float(np.mean([
        r_in - mean_pairwise_r(list(kwta_random_projection(X, k_active, rng)))
        for _ in range(n_rep)]))

    return {
        'dec': float(dec),
        'dec_null_shuffle': dec_shuf,
        'dec_null_kwta': dec_kwta,
        # to są liczby, na których wolno budować twierdzenie
        'dec_excess_shuffle': float(dec - dec_shuf),
        'dec_excess_kwta': float(dec - dec_kwta),
        'k_active_null': k_active,
    }
