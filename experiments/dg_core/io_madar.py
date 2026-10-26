"""
dg_core/io_madar.py — dane Madara (S-BSST219) i miary podobieństwa ciągów impulsów.

Po co
-----
Odpowiedź prof. Błasiak (2026-10-22, korespondencja/): kalibrujemy do skrawka (ex vivo),
a wejściem modelu ma być protokół stymulacji Madara — salwy, nie ciągłe tło 400 Hz.
Separację oceniamy razem z R_w (podobieństwo odpowiedzi na powtórzenia tego samego
wejścia). Ten moduł daje jedno i drugie, dla danych i dla modelu tą samą funkcją.

Dane
----
`dataset/PatchPatSep2s_Public/` — zip z BioStudies S-BSST219 (rozpakowany, poza gitem).
`dataset/PatSepSpikeTrains/NameFiles/*.m` — listy nagrań z repo Madara
(github.com/antoinemadar/PatSepSpikeTrains). Ścieżki w nich są bezwzględne (komputer
autora), więc pliki dopasowujemy po nazwie.

Protokół: plik .axgx, 5 kolumn = 5 pociągów wejściowych po 2 s (10 kHz), impuls = próbka > 0.
Nagranie: plik .axgd, 50 sweepów po 2 s = 5 pociągów × 10 powtórzeń, PRZEPLATANE
(sweep k odpowiada pociągowi k mod 5) — jak w SimilarityAnalysis.m.

Miary (wierne SimilarityAnalysis.m + SimMat_WandB.m):
  rastry: liczby impulsów w binach `binsize` na odcinku 0–2 s;
  R_in  = średnia korelacja Pearsona par pociągów wejściowych;
  R_w   = średnia korelacja odpowiedzi na RÓŻNE powtórzenia TEGO SAMEGO pociągu
          (rzetelność, „Sw” u Madara);
  R_b   = średnia korelacja odpowiedzi na RÓŻNE pociągi (podobieństwo wyjść, „Sb”);
  impuls = przejście napięcia w górę przez −20 mV (threshtype 'direct', −20e-3 V).
Pary z rastrem bez żadnego impulsu dają NaN (jak corrcoef w MATLAB-ie); uśredniamy
z pominięciem NaN i raportujemy ich liczbę.
"""
from __future__ import annotations

import glob
import os
import re
from functools import lru_cache

import numpy as np

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(_REPO, 'dataset', 'PatchPatSep2s_Public')
NAMEFILES_DIR = os.path.join(_REPO, 'dataset', 'PatSepSpikeTrains', 'NameFiles')
T_SWEEP_S = 2.0
SPIKE_THRESH_MV = -20.0

NAMEFILES = {
    'gc_all': 'PatSepFileListAllGC_2010toDec2015.m',
    'gc_before_gzn': 'PatSepFilesBeforeGabazine.m',
    'gc_after_gzn': 'PatSepFilesAfterGabazine.m',
    'fs': 'PatSepFilesListFS.m',
    'hmc': 'PatSepHilarMossyCells.m',
}


# ── pliki ────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _index() -> dict:
    idx = {}
    for p in glob.glob(os.path.join(DATA_DIR, '**', '*.ax*'), recursive=True):
        idx.setdefault(os.path.basename(p), p)
    return idx


def local_path(original: str) -> str | None:
    return _index().get(os.path.basename(original.replace('\\', '/')))


def parse_namefile(key_or_path: str) -> list[dict]:
    """Lista {stim, resp: [...]} z pliku NameFiles (tylko linie niezakomentowane)."""
    path = key_or_path if key_or_path.endswith('.m') else os.path.join(NAMEFILES_DIR, NAMEFILES[key_or_path])
    stims, resps = {}, {}
    for line in open(path, encoding='latin-1'):
        line = line.split('%')[0]
        m = re.search(r"Files\.Stim\.File\{(\d+)\}\s*=\s*'([^']+)'", line)
        if m:
            stims[int(m.group(1))] = m.group(2)
        m = re.search(r"Files\.Resp\.File\{(\d+)\}\{(\d+)\}\s*=\s*'([^']+)'", line)
        if m:
            resps.setdefault(int(m.group(1)), {})[int(m.group(2))] = m.group(3)
    out = []
    for k in sorted(stims):
        out.append({'stim': local_path(stims[k]), 'stim_orig': stims[k],
                    'resp': [local_path(v) for _, v in sorted(resps.get(k, {}).items())],
                    'resp_orig': [v for _, v in sorted(resps.get(k, {}).items())]})
    return out


def _raw(path):
    from neo.rawio import AxographRawIO
    r = AxographRawIO(path)
    r.parse_header()
    return r


def read_protocol(path: str) -> list[np.ndarray]:
    """Pociągi wejściowe: lista tablic czasów impulsów [s] (jeden element na kolumnę)."""
    r = _raw(path)
    fs = r.get_signal_sampling_rate(0)
    x = r.rescale_signal_raw_to_float(r.get_analogsignal_chunk(0, 0, stream_index=0), dtype='float64', stream_index=0)
    return [np.where(x[:, i] > 0)[0] / fs for i in range(x.shape[1])]


def read_sweeps(path: str) -> tuple[np.ndarray, float]:
    """Napięcie [mV], kształt [n_sweeps, n_samples], oraz krok czasu [s]."""
    r = _raw(path)
    fs = r.get_signal_sampling_rate(0)
    sw = []
    for seg in range(r.segment_count(0)):
        raw = r.get_analogsignal_chunk(0, seg, stream_index=0)
        v = r.rescale_signal_raw_to_float(raw, dtype='float64', stream_index=0)[:, 0]
        sw.append(v)
    n = min(len(v) for v in sw)
    V = np.stack([v[:n] for v in sw])
    units = str(r.header['signal_channels'][0]['units'])
    if units.strip().lower() == 'v':
        V = V * 1e3
    return V, 1.0 / fs


def detect_spikes(v_mv: np.ndarray, dt_s: float, thresh_mv: float = SPIKE_THRESH_MV) -> np.ndarray:
    """Czasy [s] przejść w górę przez próg."""
    above = v_mv >= thresh_mv
    return (np.where(above[1:] & ~above[:-1])[0] + 1) * dt_s


# ── miary ────────────────────────────────────────────────────────────────────
def raster(times_list, binsize_s: float, T_s: float = T_SWEEP_S) -> np.ndarray:
    """Liczby impulsów [n_trains, n_bins]."""
    edges = np.arange(0.0, T_s + 1e-9, binsize_s)
    return np.stack([np.histogram(np.asarray(t), edges)[0] for t in times_list]).astype(float)


def _corr_matrix(R: np.ndarray) -> np.ndarray:
    Z = R - R.mean(1, keepdims=True)
    nrm = np.sqrt((Z * Z).sum(1))
    with np.errstate(invalid='ignore', divide='ignore'):
        C = (Z @ Z.T) / np.outer(nrm, nrm)
    C[np.outer(nrm, nrm) == 0] = np.nan
    return C


def similarity(stim_times: list, resp_times: list, binsize_s: float = 0.010,
               n_repeats_used: int | None = None) -> dict:
    """
    stim_times: n_stims pociągów wejściowych; resp_times: odpowiedzi w kolejności sweepów
    (przeplatane: sweep k ↔ pociąg k mod n_stims). n_repeats_used: użyj tylko pierwszych
    k powtórzeń (test 5 vs 10 powtórzeń).
    """
    n_st = len(stim_times)
    n_rep = len(resp_times) // n_st
    k = n_rep if n_repeats_used is None else min(n_repeats_used, n_rep)
    grouped = [[resp_times[st + n_st * r] for r in range(k)] for st in range(n_st)]
    Rs = raster(stim_times, binsize_s)
    Cin = _corr_matrix(Rs)
    iu = np.triu_indices(n_st, 1)
    Ro = raster([t for g in grouped for t in g], binsize_s)
    C = _corr_matrix(Ro)
    lab = np.repeat(np.arange(n_st), k)
    same = lab[:, None] == lab[None, :]
    upper = np.triu(np.ones_like(C, dtype=bool), 1)
    w = C[same & upper]
    b = C[~same & upper]
    n_spk = np.array([len(t) for g in grouped for t in g])
    return {
        'binsize_s': binsize_s, 'n_stims': n_st, 'n_repeats': k,
        'R_in': float(np.nanmean(Cin[iu])),
        'R_w': float(np.nanmean(w)) if np.isfinite(w).any() else np.nan,
        'R_b': float(np.nanmean(b)) if np.isfinite(b).any() else np.nan,
        'nan_frac_w': float(np.isnan(w).mean()), 'nan_frac_b': float(np.isnan(b).mean()),
        'fr_hz': float(n_spk.mean() / T_SWEEP_S),
        'frac_silent_sweeps': float((n_spk == 0).mean()),
    }


def recording_similarity(stim_path: str, resp_path: str, binsize_s: float = 0.010,
                         n_repeats_used: int | None = None) -> dict:
    stim = read_protocol(stim_path)
    V, dt = read_sweeps(resp_path)
    resp = [detect_spikes(v, dt) for v in V]
    out = similarity(stim, resp, binsize_s, n_repeats_used)
    out.update(stim=os.path.basename(stim_path), resp=os.path.basename(resp_path), n_sweeps=len(resp))
    return out


def dataset_table(key: str, binsize_s: float = 0.010, n_repeats_used: int | None = None) -> list[dict]:
    """Wszystkie nagrania z listy NameFiles (pomija brakujące pliki, zgłaszając je)."""
    rows = []
    for grp in parse_namefile(key):
        for resp, orig in zip(grp['resp'], grp['resp_orig']):
            if grp['stim'] is None or resp is None:
                rows.append({'missing': os.path.basename(orig if resp is None else grp['stim_orig'])})
                continue
            try:
                rows.append(recording_similarity(grp['stim'], resp, binsize_s, n_repeats_used))
            except Exception as e:      # uszkodzony / nietypowy plik — zgłaszamy, nie przerywamy
                rows.append({'error': f'{os.path.basename(resp)}: {e}'})
    return rows
