"""
dg_core — wspólny rdzeń obwodu DG dla eksperymentów doktoratowych.

Headless (bez Streamlita) port modelu z `interactive_dg.py`. Ten sam obwód
GC/FS/HMC, te same równania Izhikevicza, ten sam kanon częstotliwości PP
(`dg_params.py`) — po to, by wyniki sweepów były porównywalne z narzędziem
interaktywnym, a nie pochodziły z „innego modelu".

Używany przez:
  • kierunek4_motifs — który motyw hamowania dominuje separację (lezje + Shapley)
  • kierunek1_readout — czy DG poprawia odbiorcę downstream (klasyfikator, pamięć)
"""

from .params import (
    DGConfig, MOTIFS, MOTIF_LABELS, config_from_motif_set, DT_MS, T_MS,
)
from .circuit import make_connectivity, simulate
from .patterns import (
    make_patterns, make_class_trials, make_input_spikes,
    pp_rate_vector_empirical, pp_rate_vector_expected, mean_pairwise_r_binary,
)
from .metrics import (
    mean_pairwise_r, decorrelation, population_sparseness, active_fraction,
    shapley_values, shapley_share, dominant_motif, interaction_2way,
    isi_cv, fano_factor, synchrony_index, activity_entropy, binary_mi_io,
    first_spike_latency, mean_pairwise_cosine, mean_pairwise_jaccard,
    activity_battery, BATTERY_KEYS, nan_mean,
)

__all__ = [
    'DGConfig', 'MOTIFS', 'MOTIF_LABELS', 'config_from_motif_set', 'DT_MS', 'T_MS',
    'make_connectivity', 'simulate',
    'make_patterns', 'make_class_trials', 'make_input_spikes',
    'pp_rate_vector_empirical', 'pp_rate_vector_expected', 'mean_pairwise_r_binary',
    'mean_pairwise_r', 'decorrelation', 'population_sparseness', 'active_fraction',
    'shapley_values', 'shapley_share', 'dominant_motif', 'interaction_2way',
    'isi_cv', 'fano_factor', 'synchrony_index', 'activity_entropy', 'binary_mi_io',
    'first_spike_latency', 'mean_pairwise_cosine', 'mean_pairwise_jaccard',
    'activity_battery', 'BATTERY_KEYS', 'nan_mean',
]
