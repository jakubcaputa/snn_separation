"""
Regresja i sanity-check zawodności synaptycznej („spike-wise noise").

Dwie rzeczy, które muszą być prawdą, żeby wprowadzenie `p_rel` nie było cichą
zmianą modelu:

1. Przy p_rel = 1.0 (domyślnie) obwód jest BIT-W-BIT identyczny z wersją sprzed
   wprowadzenia parametru. Realizowane przez osobną gałąź w `_on_pre`, która nie
   zużywa ani jednej liczby losowej.
2. Przy p_rel < 1.0 mechanizm działa zgodnie z opisem: obniżenie p_rel bez
   kompensacji zjeżdża z napędu, a kompensacja wagą W/p podnosi wariancję przy
   zachowanej średniej — czyli częstotliwość ROŚNIE, mimo tego samego napędu.

Uruchomienie:  python -m pytest tests/ -v
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))

from dg_core import DGConfig, make_connectivity, simulate  # noqa: E402
from dg_core.patterns import make_input_spikes, make_patterns  # noqa: E402


@pytest.fixture(scope="module")
def setup():
    """Jedna sieć i jedno wejście dla wszystkich testów — porównujemy obwód, nie losowanie."""
    cfg = DGConfig()
    pats, _ = make_patterns(cfg.N_GC, 3, 0.75, 0.25, seed=42)
    conn = make_connectivity(cfg, seed=0)
    idx, t = make_input_spikes(pats[0], cfg, seed=1042)
    return cfg, pats[0], conn, idx, t


def _run(cfg, conn, idx, t):
    return simulate(cfg, idx, t, conn)


def test_default_is_deterministic(setup):
    """p_rel = 1.0 → dwa przebiegi identyczne co do spajka (brak losowości w obwodzie)."""
    cfg, _, conn, idx, t = setup
    a = _run(cfg, conn, idx, t)
    b = _run(cfg, conn, idx, t)
    np.testing.assert_array_equal(a["gc_spikes"][0], b["gc_spikes"][0])
    np.testing.assert_array_equal(a["gc_spikes"][1], b["gc_spikes"][1])
    np.testing.assert_array_equal(a["fs_spikes"][1], b["fs_spikes"][1])


def test_explicit_one_equals_default(setup):
    """Jawne p_rel = 1.0 na każdej ścieżce daje dokładnie to samo, co domyślne."""
    cfg, _, conn, idx, t = setup
    explicit = cfg.with_reliability(gc=1.0, fs=1.0, hmc=1.0)
    a = _run(cfg, conn, idx, t)
    b = _run(explicit, conn, idx, t)
    np.testing.assert_array_equal(a["gc_spikes"][1], b["gc_spikes"][1])


def test_zero_jitter_equals_default(setup):
    """delay_jitter_ms = 0.0 nie może zmienić ani jednego spajka."""
    cfg, _, conn, idx, t = setup
    a = _run(cfg, conn, idx, t)
    b = _run(replace(cfg, delay_jitter_ms=0.0), conn, idx, t)
    np.testing.assert_array_equal(a["gc_spikes"][1], b["gc_spikes"][1])


def test_unreliability_reduces_drive(setup):
    """Obniżenie p_rel BEZ kompensacji wagą musi obniżyć częstotliwość GC."""
    cfg, mask, conn, idx, t = setup
    full = _run(cfg, conn, idx, t)["gc_rates"][mask].mean()
    half = _run(replace(cfg, P_REL_PP_GC=0.5), conn, idx, t)["gc_rates"][mask].mean()
    assert half < full, f"p_rel=0.5 dało {half:.2f} Hz, a pełne {full:.2f} Hz"


def test_compensated_unreliability_raises_rate(setup):
    """
    Kompensacja wagą W/p zachowuje ŚREDNI napęd, ale wariancja g_ex skaluje się
    jak 1/p — rzadsze, większe zdarzenia, więcej przebić progu. Częstotliwość
    powinna więc WZROSNĄĆ, mimo że średni napęd się nie zmienił.

    To jest mechanizm, dzięki któremu P(AP|puls) w ogóle staje się stopniowane,
    więc jeśli ten test padnie, cała kalibracja pod zadane P(AP) traci podstawę.
    """
    cfg, mask, conn, idx, t = setup
    base = _run(cfg, conn, idx, t)["gc_rates"][mask].mean()
    comp = _run(replace(cfg, P_REL_PP_GC=0.5, W_PP_GC=cfg.W_PP_GC * 2.0),
                conn, idx, t)["gc_rates"][mask].mean()
    assert comp > base, f"kompensowane {comp:.2f} Hz nie przekroczyło {base:.2f} Hz"


def test_p_rel_map_covers_every_pathway():
    """
    Każda ścieżka z `make_connectivity` musi mieć swoje p_rel — inaczej przy
    włączonej zawodności cicho ominęlibyśmy jedną synapsę i zostałaby ona
    deterministyczna bez śladu w konfiguracji.

    `p_rel_map` ma dokładnie jeden klucz więcej: `pp_gc`. To nie jest przeoczenie
    — łączność PP→GC nie przechodzi przez `make_connectivity`, bo jest budowana
    inline (1:1 albo per-fiber, zależnie od `cfg.per_fiber`).
    """
    cfg = DGConfig()
    conn_keys = set(make_connectivity(cfg, seed=0).keys())
    p_rel_keys = set(cfg.p_rel_map().keys())
    assert conn_keys <= p_rel_keys, f"ścieżki bez p_rel: {conn_keys - p_rel_keys}"
    assert p_rel_keys - conn_keys == {"pp_gc"}
