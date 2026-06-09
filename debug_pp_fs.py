"""
Directly test PP→FS in isolation with 20 active neurons at 600 Hz.
Mirrors the exact structure of simulate_dg().
"""
import numpy as np
from brian2 import *

prefs.codegen.target = 'numpy'

A_FS, B_FS, C_FS, D_FS = 0.10, 0.2, -65.0, 2.0
K_TONIC_FS = 5.0
TAU_EX_FS  = 3.0

FS_EQS = (
    f"dv/dt  = (0.04/mV/ms * v**2 + 5/ms * v + 140*mV/ms"
    f" - u/ms + g_ex/ms - {K_TONIC_FS}*mV/ms) : volt (unless refractory)\n"
    f"dg_ex/dt = -g_ex / ({TAU_EX_FS}*ms) : volt\n"
    f"du/dt  = {A_FS}/ms * ({B_FS} * v - u) : volt\n"
)

N_PP = 20   # 20 active PP neurons at 600 Hz each
N_FS = 1

start_scope()
defaultclock.dt = 0.1 * ms

# Generate Poisson spikes for 20 PP neurons at 600 Hz
T_MS, DT_MS = 200.0, 0.1
n_steps = int(T_MS / DT_MS)
rng = np.random.default_rng(42)
p = 600.0 * DT_MS * 1e-3

all_idx, all_t = [], []
for i in range(N_PP):
    ts = np.where(rng.random(n_steps) < p)[0].astype(float) * DT_MS
    ts = ts[(ts > 0) & (ts < T_MS)]
    if len(ts):
        all_idx.append(np.full(len(ts), i, dtype=np.int32))
        all_t.append(ts)

idx = np.concatenate(all_idx)
t_arr = np.concatenate(all_t)
order = np.argsort(t_arr)
idx, t_arr = idx[order], t_arr[order]

print(f"PP total spikes: {len(idx)} from {N_PP} neurons over {T_MS} ms")
print(f"Expected: {N_PP * 600 * T_MS/1000:.0f} spikes")

pp = SpikeGeneratorGroup(N_PP, idx, t_arr * ms)

fs = NeuronGroup(N_FS, FS_EQS,
                 threshold='v >= 30*mV',
                 reset=f'v = {C_FS}*mV; u = u + {D_FS}*mV',
                 refractory=1*ms, method='euler')
fs.v = -70 * mV
fs.u = B_FS * (-70 * mV)
fs.g_ex = 0 * mV

# Connect ALL 20 PP neurons to the single FS neuron (all-to-one)
syn_pp_fs = Synapses(pp, fs, on_pre='g_ex_post += 0.5*mV', delay=4*ms)
syn_pp_fs.connect()   # all-to-all = all 20 PP to 1 FS

sm = StateMonitor(fs, ['v', 'g_ex'], record=True)
sp = SpikeMonitor(fs)

run(T_MS * ms)

print(f"\nFS spikes in {T_MS} ms: {sp.count[0]}  (FR = {sp.count[0]/(T_MS/1000):.1f} Hz)")
print(f"Expected g_ex_ss = {N_PP * 600 * 0.5e-3 * 3e-3 * 1e3:.1f} mV  (G_crit = {4+K_TONIC_FS:.0f} mV)")

# Sample g_ex at a few time points
for t_ms in [5, 10, 20, 50, 100, 150]:
    idx_t = int(t_ms / DT_MS)
    if idx_t < len(sm.g_ex[0]):
        print(f"  g_ex at t={t_ms:3d}ms = {sm.g_ex[0, idx_t]/mV:.2f} mV   "
              f"v = {sm.v[0, idx_t]/mV:.2f} mV")

print("\n--- Same test but using _syns list (mimic simulate_dg fix) ---")
start_scope()
defaultclock.dt = 0.1 * ms

pp2 = SpikeGeneratorGroup(N_PP, idx, t_arr * ms)
fs2 = NeuronGroup(N_FS, FS_EQS,
                  threshold='v >= 30*mV',
                  reset=f'v = {C_FS}*mV; u = u + {D_FS}*mV',
                  refractory=1*ms, method='euler')
fs2.v = -70*mV; fs2.u = B_FS*(-70*mV); fs2.g_ex = 0*mV

_syns = []
s = Synapses(pp2, fs2, on_pre='g_ex_post += 0.5*mV', delay=4*ms)
s.connect()
_syns.append(s)

sm2 = StateMonitor(fs2, ['v', 'g_ex'], record=True)
sp2 = SpikeMonitor(fs2)

run(T_MS * ms)

print(f"FS spikes: {sp2.count[0]}  FR = {sp2.count[0]/(T_MS/1000):.1f} Hz")
for t_ms in [5, 10, 20, 50]:
    idx_t = int(t_ms / DT_MS)
    if idx_t < len(sm2.g_ex[0]):
        print(f"  g_ex at t={t_ms:3d}ms = {sm2.g_ex[0, idx_t]/mV:.2f} mV   "
              f"v = {sm2.v[0, idx_t]/mV:.2f} mV")

print(f"\nIs syn in _syns? {s in _syns}")
print(f"syn id: {id(s)}, _syns[0] id: {id(_syns[0])}")
