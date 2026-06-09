"""
Quick debug: verify FS fires when directly driven by PP→FS with g_ex >> G_crit
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from brian2 import *

prefs.codegen.target = 'numpy'

start_scope()
defaultclock.dt = 0.1 * ms

# ── FS parameters ─────────────────────────────────────────────────────────────
A_FS, B_FS, C_FS, D_FS = 0.10, 0.2, -65.0, 2.0
K_TONIC_FS = 5.0
TAU_EX_FS  = 3.0

FS_EQS = (
    f"dv/dt  = (0.04/mV/ms * v**2 + 5/ms * v + 140*mV/ms"
    f" - u/ms + g_ex/ms - {K_TONIC_FS}*mV/ms) : volt (unless refractory)\n"
    f"dg_ex/dt = -g_ex / ({TAU_EX_FS}*ms) : volt\n"
    f"du/dt  = {A_FS}/ms * ({B_FS} * v - u) : volt\n"
)

print("FS equations:")
print(FS_EQS)

# ── Single FS neuron ──────────────────────────────────────────────────────────
fs = NeuronGroup(1, FS_EQS,
                 threshold='v >= 30*mV',
                 reset=f'v = {C_FS}*mV; u = u + {D_FS}*mV',
                 refractory=1*ms, method='euler')
fs.v = -70*mV
fs.u = B_FS * (-70*mV)
fs.g_ex = 0*mV

# Monitor v, g_ex, u
state_mon = StateMonitor(fs, ['v', 'g_ex', 'u'], record=True)
spike_mon = SpikeMonitor(fs)

# ── PP input: 1 neuron firing at 600 Hz (aggregate) ──────────────────────────
T_MS = 200.0
DT_MS = 0.1
n_steps = int(T_MS / DT_MS)

rng = np.random.default_rng(42)
p = 600.0 * DT_MS * 1e-3  # prob per step
ts = np.where(rng.random(n_steps) < p)[0].astype(float) * DT_MS
ts = ts[(ts > 0) & (ts < T_MS)]
print(f"PP neuron fires {len(ts)} times in {T_MS} ms (expected ~{int(600*T_MS/1000)})")

pp = SpikeGeneratorGroup(1, np.zeros(len(ts), dtype=int), ts * ms)

# Connect PP → FS with W = 0.5 mV, delay = 4 ms
syn_pp_fs = Synapses(pp, fs, on_pre='g_ex_post += 0.5*mV', delay=4*ms)
syn_pp_fs.connect(i=0, j=0)

run(T_MS * ms)

print(f"\nFS spikes: {spike_mon.count[0]}")
print(f"FS mean FR: {spike_mon.count[0] / (T_MS/1000):.1f} Hz")
print(f"g_ex at t=50ms: {state_mon.g_ex[0, int(50/DT_MS)]/mV:.2f} mV")
print(f"g_ex at t=100ms: {state_mon.g_ex[0, int(100/DT_MS)]/mV:.2f} mV")
print(f"g_ex steady state (expected): {600 * 0.5e-3 * 3e-3 * 1e3:.2f} mV")
print(f"v at t=50ms: {state_mon.v[0, int(50/DT_MS)]/mV:.2f} mV")
print(f"v at t=100ms: {state_mon.v[0, int(100/DT_MS)]/mV:.2f} mV")

# ── Also test with STRONG direct current injection ────────────────────────────
print("\n--- Test 2: Direct g_ex injection (no synapse) ---")
start_scope()
defaultclock.dt = 0.1 * ms

fs2 = NeuronGroup(1, FS_EQS,
                  threshold='v >= 30*mV',
                  reset=f'v = {C_FS}*mV; u = u + {D_FS}*mV',
                  refractory=1*ms, method='euler')
fs2.v = -70*mV
fs2.u = B_FS * (-70*mV)
fs2.g_ex = 18*mV  # directly set to steady-state value

state2 = StateMonitor(fs2, ['v', 'g_ex'], record=True)
spike2 = SpikeMonitor(fs2)

run(50 * ms)

print(f"FS2 spikes in 50ms with g_ex=18mV constant: {spike2.count[0]}")
print(f"v at t=10ms: {state2.v[0, int(10/DT_MS)]/mV:.2f} mV")
print(f"v at t=20ms: {state2.v[0, int(20/DT_MS)]/mV:.2f} mV")
