"""
Testy harnessa kalibracyjnego.

Nacisk jest na krok 1 (wzory zamknięte), bo to jedyna część, którą da się
sprawdzić dokładnie i szybko — kroki 2–4 wymagają symulacji, więc weryfikujemy
je tylko na poziomie własności (monotoniczność, spójność), nie konkretnych liczb.

Uruchomienie:  python -m pytest tests/ -v
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))

from dg_core import DGConfig  # noqa: E402
from dg_core.calibrate import (  # noqa: E402
    OperatingPoint, g_crit, izh_fixed_points, solve_b_K,
)
from dg_core.params import B_GC  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# Krok 1 — wzory zamknięte
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("K,b,want_rest,want_th", [
    (0.0,  0.2, -70.0, -50.0),     # domyślne b, zerowy prąd toniczny
    (10.0, 0.2, -78.7, -41.3),     # obecne ustawienie GC w modelu
    (14.0, 0.4, -70.0, -45.0),     # para żądana przez stronę biologiczną
])
def test_fixed_points_known_values(K, b, want_rest, want_th):
    vr, vt = izh_fixed_points(K, b)
    assert vr == pytest.approx(want_rest, abs=0.1)
    assert vt == pytest.approx(want_th, abs=0.1)


def test_sum_of_voltages_depends_only_on_b():
    """
    Własność strukturalna modelu: V_rest + V_th_eff = −(5−b)/0.04, więc jest
    NIEZALEŻNA od K. To dlatego pary (−70, −45) nie da się uzyskać samym prądem
    tonicznym — i dlatego kalibracja musi móc ruszyć b.
    """
    for b in (0.2, 0.3, 0.4):
        expected = -(5.0 - b) / 0.04
        checked = 0
        for K in (0.0, 5.0, 10.0, 20.0):
            vr, vt = izh_fixed_points(K, b)
            if np.isnan(vr):
                # Przy większym b i małym K punkty stałe NIE ISTNIEJĄ — neuron
                # odpala samoistnie. To poprawne zachowanie modelu, nie błąd,
                # więc taki przypadek pomijamy zamiast go wymuszać.
                continue
            assert vr + vt == pytest.approx(expected, abs=1e-6)
            checked += 1
        assert checked >= 2, f"b={b}: za mało przypadków z istniejącymi punktami stałymi"


def test_solve_b_K_is_inverse_of_fixed_points():
    """Round-trip: cel → (b, K) → punkty stałe musi wrócić do celu."""
    for v_rest, v_th in [(-70, -50), (-70, -45), (-75, -48), (-68, -52)]:
        b, K = solve_b_K(v_rest, v_th)
        vr, vt = izh_fixed_points(K, b)
        assert vr == pytest.approx(v_rest, abs=1e-6)
        assert vt == pytest.approx(v_th, abs=1e-6)


def test_default_pair_needs_no_model_change():
    """Para (−70, −50) jest osiągalna przy domyślnym b — i wymaga K = 0."""
    b, K = solve_b_K(-70.0, -50.0)
    assert b == pytest.approx(B_GC, abs=1e-9)
    assert K == pytest.approx(0.0, abs=1e-9)


def test_strict_pair_requires_changing_b():
    """Para (−70, −45) NIE jest osiągalna przy domyślnym b i podnosi K powyżej obecnych 10."""
    b, K = solve_b_K(-70.0, -45.0)
    assert b > B_GC
    assert K > 10.0


def test_threshold_above_rest_is_required():
    with pytest.raises(ValueError):
        solve_b_K(-50.0, -70.0)


def test_g_crit_matches_fixed_point_collapse():
    """
    G_crit = 4 + K to minimalny napęd, przy którym punkty stałe znikają (neuron
    odpala). Sprawdzamy wprost: tuż poniżej istnieją, tuż powyżej nie.
    """
    for K in (0.0, 5.0, 10.0):
        gc_thr = g_crit(K)
        # napęd g wchodzi do równania jak zmniejszenie K o g
        below = izh_fixed_points(K - (gc_thr - 0.05))
        above = izh_fixed_points(K - (gc_thr + 0.05))
        assert not np.isnan(below[0]), f"K={K}: tuż poniżej progu punkty mają istnieć"
        assert np.isnan(above[0]), f"K={K}: tuż powyżej progu punktów ma nie być"


# ══════════════════════════════════════════════════════════════════════════════
# Specyfikacja punktu pracy
# ══════════════════════════════════════════════════════════════════════════════

def test_b_gc_is_config_field_and_defaults_to_module_constant():
    """
    b musi być polem konfiguracji, inaczej krok 4 mierzyłby częstotliwości
    neuronu innego niż ten, dla którego kroki 1–2 wyliczyły próg.
    """
    assert DGConfig().b_gc == pytest.approx(B_GC)
    assert replace(DGConfig(), b_gc=0.4).b_gc == pytest.approx(0.4)


def test_open_questions_flag_unresolved_spec():
    """Nierozstrzygnięty bilans hamowania musi być JAWNIE zgłoszony, a nie cicho przyjęty."""
    spec = OperatingPoint()
    assert spec.tonic_share is None
    qs = " ".join(spec.open_questions())
    assert "tonic_share" in qs
    assert "in vitro" in qs

    resolved = replace(spec, tonic_share=0.5)
    assert "tonic_share" not in " ".join(resolved.open_questions())
