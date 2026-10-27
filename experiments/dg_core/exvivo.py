"""
dg_core/exvivo.py — obwód DG napędzany protokołem stymulacji Madara (reżim skrawka).

Po co (odpowiedź prof. Błasiak, B3, 2026-10-22)
-----------------------------------------------
Dane są ze skrawków, a w skrawku wejściem nie jest ciągłe tło z kory śródwęchowej,
tylko stymulacja drogi przeszywającej: salwy w chwilach z pociągu wejściowego (protokół
`.prt.axgx`, 5 pociągów po 2 s, ok. 10 Hz). „~50% AP po pulsie” u Madara dotyczy
ZSUMOWANEGO EPSP salwy — wielu synaps naraz. Wcześniej tę wagę (6.98 mV) dawaliśmy
każdemu z 40 niezależnych włókien po 10 Hz, stąd GC strzelały 11–22 Hz zamiast 2–6 Hz.

Model salwy
-----------
Tryb `per_fiber`: każdy GC ma `n_fibers` włókien PP; w chwili impulsu z protokołu
odpalają WSZYSTKIE, każde uwalnia z prawdopodobieństwem `p_rel`. Waga włókna =
W_volley / (n_fibers · p_rel), więc średni zsumowany EPSP = W_volley, a jego zmienność
między powtórzeniami (dwumianowa) jest jedynym źródłem szumu — to ona ustala R_w.
FS dostają tę samą salwę przez połączenia PP→FS (pierwsze włókno każdego źródła).
Gabazyna 100 nM: niskie stężenie blokuje głównie hamowanie FAZOWE (Stell & Mody 2002),
więc modelujemy ją jako W_FS_GC × (1 − blok), domyślnie blok = 0.3 (jak u Madara
wg prof. Błasiak); hamowania tonicznego (K_GC) nie zmieniamy.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from .circuit import make_connectivity, simulate
from .params import DGConfig, PP_DELAY

T_SWEEP_MS = 2000.0


def exvivo_config(base: DGConfig, W_volley: float, p_rel: float, n_fibers: int = 40,
                  gabazine_block: float = 0.0, gabazine_tonic_block: float = 0.0, **overrides) -> DGConfig:
    """Konfiguracja skrawka: salwy zamiast tła, zawodność włókien PP, opcjonalnie gabazyna.
    gabazine_tonic_block (2026-10-27): hipoteza alternatywna — gabazyna obniża też hamowanie
    toniczne (K_GC × (1 − blok)); domyślnie 0 = tylko hamowanie fazowe."""
    cfg = replace(base, per_fiber=True, n_syn_pp=n_fibers, T_ms=T_SWEEP_MS,
                  W_PP_GC=W_volley / (n_fibers * p_rel), P_REL_PP_GC=p_rel, **overrides)
    if gabazine_block:
        cfg = replace(cfg, W_FS_GC=cfg.W_FS_GC * (1.0 - gabazine_block))
    if gabazine_tonic_block:
        cfg = replace(cfg, K_GC=cfg.K_GC * (1.0 - gabazine_tonic_block))
    return cfg


def volley_input(cfg: DGConfig, pulse_times_s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Wszystkie włókna wszystkich GC odpalają w każdej chwili z protokołu.
    (Opóźnienie PP_DELAY dodaje synapsa w `simulate`.)"""
    n_src = cfg.N_GC * cfg.n_syn_pp
    t_ms = np.asarray(pulse_times_s, float) * 1000.0
    t_ms = t_ms[(t_ms > 0) & (t_ms < cfg.T_ms - PP_DELAY)]
    idx = np.tile(np.arange(n_src, dtype=np.int32), len(t_ms))
    ts = np.repeat(t_ms, n_src)
    return idx, ts


def _one_sweep(args):
    cfg, conn, pulses, seed = args
    from brian2 import seed as bseed
    bseed(int(seed))
    np.random.seed(int(seed) % (2 ** 32 - 1))
    idx, ts = volley_input(cfg, pulses)
    out = simulate(cfg, idx, ts, conn)
    gi, gt = out['gc_spikes']
    fi, ft = out['fs_spikes']
    return (np.asarray(gi), np.asarray(gt) / 1000.0, np.asarray(fi), np.asarray(ft) / 1000.0)


def run_protocol(cfg: DGConfig, conn: dict, stim_trains: list, n_repeats: int = 10,
                 seed: int = 0, jobs: int = 1) -> dict:
    """
    Sweepy przeplatane jak u Madara (sweep k ↔ pociąg k mod n_stims), n_repeats powtórzeń.
    Zwraca czasy impulsów [s] każdego GC i każdego FS w każdym sweepie:
      gc[c][k], fs[c][k] — lista tablic (komórka c, sweep k).
    """
    n_st = len(stim_trains)
    jobs_l = [(cfg, conn, stim_trains[k % n_st], 1_000_003 * (seed + 1) + k) for k in range(n_st * n_repeats)]
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs) as p:
            res = p.map(_one_sweep, jobs_l)
    else:
        res = [_one_sweep(j) for j in jobs_l]
    gc = [[r[1][r[0] == c] for r in res] for c in range(cfg.N_GC)]
    fs = [[r[3][r[2] == c] for r in res] for c in range(cfg.N_FS)]
    return {'gc': gc, 'fs': fs, 'n_stims': n_st, 'n_repeats': n_repeats}


def population_similarity(run: dict, stim_trains: list, binsize_s: float = 0.010,
                          n_repeats_used: int | None = None, cells: str = 'gc') -> list[dict]:
    """Każda komórka modelu traktowana jak jedno nagranie Madara (te same miary)."""
    from .io_madar import similarity
    return [similarity(stim_trains, resp, binsize_s, n_repeats_used) for resp in run[cells]]


# ── punkt kalibracyjny i wejście dla zadań wzorcowych (E3.6 ex vivo, 2026-10-24) ──
# Najlepszy punkt siatki v3 (calib_exvivo/README.md): kontrola zgodna z danymi Madara
# (GC 3.0 Hz, R_w 0.37, R_b 0.28, FS 9.6 Hz, FS przed GC); efekt gabazyny za słaby (×1.25).
EXVIVO_BEST = dict(W_volley=20.0, p_rel=0.6, W_FS_GC=2.0, W_GC_FS=1e-4, W_PP_FS=0.5, W_FS_FS=1.0)
K_GC_VREST76 = 6.24          # V_rest = −76 mV (mediana GC w danych)


def exvivo_best_config(K_GC: float = K_GC_VREST76, T_ms: float = 600.0) -> DGConfig:
    b = dict(EXVIVO_BEST)
    cfg = exvivo_config(DGConfig(K_GC=K_GC), b.pop('W_volley'), b.pop('p_rel'), **b)
    return replace(cfg, T_ms=T_ms)


def poisson_train(rate_hz: float, T_ms: float, rng) -> np.ndarray:
    """Czasy salw [s] — pociąg Poissona jak w protokołach Madara (10 Hz)."""
    n = rng.poisson(rate_hz * T_ms / 1000.0)
    return np.sort(rng.uniform(0.0, T_ms / 1000.0, n))


def pattern_volley_input(cfg: DGConfig, pattern: np.ndarray, pulse_times_s: np.ndarray):
    """Salwy tylko we włóknach GC wskazanych przez wzorzec (zadanie przestrzenne);
    wszystkie włókna aktywnego GC odpalają w każdej salwie."""
    active = np.where(np.asarray(pattern, bool))[0]
    fib = (active[:, None] * cfg.n_syn_pp + np.arange(cfg.n_syn_pp)[None, :]).ravel().astype(np.int32)
    t_ms = np.asarray(pulse_times_s, float) * 1000.0
    t_ms = t_ms[(t_ms > 0) & (t_ms < cfg.T_ms - PP_DELAY)]
    return np.tile(fib, len(t_ms)), np.repeat(t_ms, len(fib))
