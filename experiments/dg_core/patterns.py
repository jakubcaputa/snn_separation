"""
dg_core/patterns.py — generowanie wzorców wejściowych i spajków PP.

Dwa zastosowania:
  • kierunek 4 — N wzorców o kontrolowanym podobieństwie R_in (jak interactive_dg)
  • kierunek 1 — C klas (prototypy) × wiele zaszumionych prób na klasę,
                 czyli zbiór uczący dla klasyfikatora downstream
"""

from __future__ import annotations

import numpy as np

from .params import DGConfig, DT_MS


# ══════════════════════════════════════════════════════════════════════════════
# Wzorce binarne (które GC dostają silny napęd PP)
# ══════════════════════════════════════════════════════════════════════════════

def make_patterns(N_GC: int, n_patterns: int, R_in: float, p_active: float,
                  seed: int = 42) -> tuple[np.ndarray, float]:
    """
    N wzorców binarnych o zadanym parami podobieństwie R_in (schemat common+private).

    Zwraca (patterns[n_patterns, N_GC] bool, zmierzone R_in).
    Identyczny schemat jak `make_patterns_pop` w interactive_dg.py.
    """
    rng = np.random.default_rng(seed)
    common = rng.random(N_GC) < (p_active * R_in)
    pats = np.zeros((n_patterns, N_GC), dtype=bool)
    for k in range(n_patterns):
        pats[k] = common | (rng.random(N_GC) < p_active * (1.0 - R_in))
    return pats, mean_pairwise_r_binary(pats)


def mean_pairwise_r_binary(pats: np.ndarray) -> float:
    """Średnia parami korelacja Pearsona wektorów binarnych."""
    rs = []
    n = len(pats)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = pats[i].astype(float), pats[j].astype(float)
            if a.std() > 1e-9 and b.std() > 1e-9:
                rs.append(float(np.corrcoef(a, b)[0, 1]))
    return float(np.mean(rs)) if rs else 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Klasy + zaszumione próby (kierunek 1 — zadanie downstream)
# ══════════════════════════════════════════════════════════════════════════════

def make_class_trials(N_GC: int, n_classes: int, n_trials_per_class: int,
                      R_in: float, p_active: float, noise: float,
                      seed: int = 7) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Zadanie klasyfikacji: `n_classes` prototypów o wzajemnym podobieństwie R_in;
    każda próba = prototyp + szum bit-flip o sile `noise`.

    `noise` to prawdopodobieństwo, że dana jednostka zostanie przerzucona, przy
    zachowaniu oczekiwanej rzadkości p_active (flip 1→0 z p=noise, 0→1 z
    p=noise·p_active/(1-p_active)) — dzięki temu szum nie zmienia gęstości
    wejścia, więc różnica w dokładności nie bierze się ze zmiany sparsity.

    Zwraca (trials[n_classes*n_trials, N_GC] bool, labels, prototypes, R_in_zmierzone).
    """
    rng = np.random.default_rng(seed)

    protos, r_in_meas = make_patterns(N_GC, n_classes, R_in, p_active, seed=seed)

    p_off_on = noise * p_active / max(1e-9, (1.0 - p_active))  # 0→1
    p_on_off = noise                                            # 1→0

    trials, labels = [], []
    for c in range(n_classes):
        for _ in range(n_trials_per_class):
            x = protos[c].copy()
            flip_on = (~x) & (rng.random(N_GC) < p_off_on)
            flip_off = x & (rng.random(N_GC) < p_on_off)
            trials.append((x | flip_on) & ~flip_off)
            labels.append(c)

    return np.array(trials), np.array(labels), protos, r_in_meas


# ══════════════════════════════════════════════════════════════════════════════
# Spajki perforant path
# ══════════════════════════════════════════════════════════════════════════════

def make_input_spikes(pattern: np.ndarray, cfg: DGConfig,
                      seed: int = 1042) -> tuple[np.ndarray, np.ndarray]:
    """
    Poissonowskie wejście PP dla jednego wzorca.

    Tryb zagregowany: 1 generator na GC, r_high / r_low [Hz].
    Tryb per-fiber:   n_syn_pp niezależnych włókien na GC (indeks i*n_syn_pp + f),
                      każde r_high/n_syn_pp Hz — łączny napęd ten sam co zagregowany.

    Zwraca (indices, times_ms) posortowane po czasie — gotowe dla SpikeGeneratorGroup.
    """
    rng = np.random.default_rng(seed)
    n_steps = int(cfg.T_ms / DT_MS)

    if cfg.per_fiber:
        r_hi = cfg.r_high / cfg.n_syn_pp
        r_lo = cfg.r_low / cfg.n_syn_pp
        n_sub = cfg.n_syn_pp
    else:
        r_hi, r_lo, n_sub = cfg.r_high, cfg.r_low, 1

    all_idx, all_t = [], []
    for i, active in enumerate(pattern):
        p = (r_hi if active else r_lo) * DT_MS * 1e-3
        for f in range(n_sub):
            ts = np.where(rng.random(n_steps) < p)[0].astype(float) * DT_MS
            ts = ts[(ts > 0) & (ts < cfg.T_ms)]
            if len(ts):
                all_idx.append(np.full(len(ts), i * n_sub + f, dtype=np.int32))
                all_t.append(ts)

    if not all_idx:
        return np.array([], dtype=np.int32), np.array([])

    idx = np.concatenate(all_idx)
    t = np.concatenate(all_t)
    order = np.argsort(t)
    return idx[order], t[order]


def pp_rate_vector_empirical(idx: np.ndarray, cfg: DGConfig) -> np.ndarray:
    """
    Zmierzony wektor częstotliwości WEJŚCIA PP na GC [Hz] — baseline „bez DG".

    To sygnał, który odbiorca dostałby, gdyby warstwy DG nie było: te same
    spajki PP, ta sama wymiarowość (N_GC) i TEN SAM szum Poissona co widzi DG.
    Uczciwy baseline — nie wersja wyidealizowana.

    Uwaga: w trybie per-fiber indeksy to i*n_syn_pp + f, więc sumujemy po włóknach.
    """
    n_sub = cfg.n_syn_pp if cfg.per_fiber else 1
    counts = np.bincount(idx // n_sub, minlength=cfg.N_GC).astype(float)
    return counts / (cfg.T_ms * 1e-3)


def pp_rate_vector_expected(pattern: np.ndarray, cfg: DGConfig) -> np.ndarray:
    """Oczekiwany (bezszumowy) wektor częstotliwości PP — tylko do sanity-checków."""
    return np.where(pattern, cfg.r_high, cfg.r_low).astype(float)
