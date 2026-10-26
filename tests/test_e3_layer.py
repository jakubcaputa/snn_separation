"""E3: warstwa DG w torch liczy to samo co neuron GC z dg_core (Brian2)."""
import os
import sys

import numpy as np
import pytest

torch = pytest.importorskip('torch')

HERE = os.path.dirname(os.path.abspath(__file__))
E3 = os.path.join(HERE, '..', 'experiments', 'e3_sparsity_third_factor')
sys.path.insert(0, E3)
sys.path.insert(0, os.path.join(HERE, '..', 'experiments'))

from model import DGLayer, LayerCfg  # noqa: E402


def _brian_counts(spike_steps, K, T_ms, w_pp):
    from brian2 import (NeuronGroup, SpikeGeneratorGroup, Synapses, defaultclock, ms, mV,
                        start_scope, run, SpikeMonitor, prefs)
    from dg_core.circuit import _gc_eqs
    from dg_core.params import B_GC, C_GC, D_GC
    prefs.codegen.target = 'numpy'
    start_scope()
    defaultclock.dt = 0.1 * ms
    times = np.asarray(spike_steps, float) * 0.1
    pp = SpikeGeneratorGroup(1, np.zeros(len(times), int), times * ms)
    gc = NeuronGroup(1, _gc_eqs(K), threshold='v >= 30*mV',
                     reset=f'v = {C_GC}*mV; u = u + {D_GC}*mV', refractory=2 * ms, method='euler')
    gc.v = -70 * mV
    gc.u = B_GC * (-70 * mV)
    s = Synapses(pp, gc, on_pre=f'g_ex_post += {w_pp}*mV')
    s.connect(i=0, j=0)
    mon = SpikeMonitor(gc)
    run(T_ms * ms)
    return int(mon.num_spikes)


@pytest.mark.parametrize('K', [0.0, 5.0, 10.0])
def test_izh_layer_matches_dg_core(K):
    cfg = LayerCfg(neuron='izh', n_dg=1, fan_in=1, T_ms=200.0)
    steps = int(cfg.T_ms / cfg.dt)
    rng = np.random.default_rng(1)
    spike_steps = np.sort(rng.choice(np.arange(1, steps - 1), size=120, replace=False))
    conn = {'M': np.zeros((784, 1), np.float32), 'C_gc_fs': np.zeros((1, 20), np.float32),
            'C_fs_gc': np.zeros((20, 1), np.float32)}
    conn['M'][0, 0] = 1.0
    inp = torch.zeros(steps, 1, 784)
    # Brian2 dostarcza impuls z kroku s do g_ex po aktualizacji stanu w kroku s;
    # w torch wejście kroku t też dodajemy po aktualizacji stanu.
    inp[spike_steps, 0, 0] = 1.0
    c_torch = int(DGLayer(cfg, conn).run(torch.zeros(1, 784), [K], input_spikes=inp)[0, 0, 0])
    c_brian = _brian_counts(spike_steps, K, cfg.T_ms, cfg.w_pp)
    assert c_brian > 0 or K > 0
    assert abs(c_torch - c_brian) <= max(1, int(0.05 * c_brian)), (c_torch, c_brian)
