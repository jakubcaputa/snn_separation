"""
Minimal repro: does a PP→FS Synapses object get included in Brian2 magic network
when PP also connects to GC (multiple Synapses from same source)?
"""
import numpy as np
from brian2 import *
from brian2.core.magic import collect

prefs.codegen.target = 'numpy'

N_GC  = 200
N_FS  = 20
DT_MS = 0.1
T_MS  = 100.0

A_FS, B_FS, C_FS, D_FS = 0.10, 0.2, -65.0, 2.0
K_TONIC_FS = 5.0
TAU_EX_FS  = 3.0

FS_EQS = (
    f"dv/dt  = (0.04/mV/ms * v**2 + 5/ms * v + 140*mV/ms"
    f" - u/ms + g_ex/ms - {K_TONIC_FS}*mV/ms) : volt (unless refractory)\n"
    f"dg_ex/dt = -g_ex / ({TAU_EX_FS}*ms) : volt\n"
    f"du/dt  = {A_FS}/ms * ({B_FS} * v - u) : volt\n"
)

A_GC, B_GC, C_GC, D_GC = 0.02, 0.2, -65.0, 6.0
K_TONIC_GC = 10.0
TAU_EX_GC  = 5.0
TAU_IN_GC  = 8.0

GC_EQS = (
    f"dv/dt  = (0.04/mV/ms * v**2 + 5/ms * v + 140*mV/ms"
    f" - u/ms + g_ex/ms - g_in/ms - {K_TONIC_GC}*mV/ms) : volt (unless refractory)\n"
    f"dg_ex/dt = -g_ex / ({TAU_EX_GC}*ms) : volt\n"
    f"dg_in/dt = -g_in / ({TAU_IN_GC}*ms) : volt\n"
    f"du/dt  = {A_GC}/ms * ({B_GC} * v - u) : volt\n"
)

# ── Generate spikes: 50 active PP neurons at 600 Hz, 150 inactive at 40 Hz ───
rng = np.random.default_rng(42)
n_steps = int(T_MS / DT_MS)

# Mark 50 as active
active_mask = np.zeros(N_GC, dtype=bool)
active_mask[:50] = True

all_idx, all_t = [], []
for i in range(N_GC):
    rate = 600.0 if active_mask[i] else 40.0
    p = rate * DT_MS * 1e-3
    ts = np.where(rng.random(n_steps) < p)[0].astype(float) * DT_MS
    ts = ts[(ts > 0) & (ts < T_MS)]
    if len(ts):
        all_idx.append(np.full(len(ts), i, dtype=np.int32))
        all_t.append(ts)
idx = np.concatenate(all_idx)
t_arr = np.concatenate(all_t)
order = np.argsort(t_arr)
idx, t_arr = idx[order], t_arr[order]

# ── Connectivity: 50 active PP → FS with P=0.40 ───────────────────────────────
rng2 = np.random.default_rng(0)
mask_pp_fs = rng2.random((N_GC, N_FS)) < 0.40
si_pp_fs, ti_pp_fs = np.where(mask_pp_fs)
si_pp_fs = si_pp_fs.astype(np.int32)
ti_pp_fs = ti_pp_fs.astype(np.int32)
print(f"PP→FS synapses: {len(si_pp_fs)}")
print(f"Active PP→FS per FS neuron (avg): {np.mean([np.sum(active_mask[si_pp_fs[ti_pp_fs==j]]) for j in range(N_FS)]):.1f}")

# ── Test A: PP→GC only (baseline) ────────────────────────────────────────────
print("\n=== Test A: PP→GC only ===")
start_scope()
defaultclock.dt = DT_MS * ms

pp = SpikeGeneratorGroup(N_GC, idx, t_arr * ms)
gc = NeuronGroup(N_GC, GC_EQS, threshold='v>=30*mV',
                 reset=f'v={C_GC}*mV; u=u+{D_GC}*mV',
                 refractory=2*ms, method='euler')
fs = NeuronGroup(N_FS, FS_EQS, threshold='v>=30*mV',
                 reset=f'v={C_FS}*mV; u=u+{D_FS}*mV',
                 refractory=1*ms, method='euler')
gc.v=-70*mV; gc.u=B_GC*(-70*mV); gc.g_ex=0*mV; gc.g_in=0*mV
fs.v=-70*mV; fs.u=B_FS*(-70*mV); fs.g_ex=0*mV

syn_pp_gc = Synapses(pp, gc, on_pre='g_ex_post += 4.0*mV', delay=4*ms)
syn_pp_gc.connect(i=np.arange(N_GC), j=np.arange(N_GC))

# NO PP→FS synapse
sp_gc = SpikeMonitor(gc)
sp_fs = SpikeMonitor(fs)
st_fs = StateMonitor(fs, ['v', 'g_ex'], record=True)

objs = collect()
print(f"Magic collects {len(objs)} objects before run()")
for o in objs:
    if isinstance(o, Synapses):
        print(f"  Synapse: {o.name}  source={o.source.name}  target={o.target.name}")

run(T_MS * ms)
print(f"FR_gc={sp_gc.num_spikes/(T_MS*1e-3*N_GC):.1f} Hz  FR_fs={sp_fs.num_spikes/(T_MS*1e-3*N_FS):.1f} Hz")
print(f"FS[0] max g_ex = {np.max(st_fs.g_ex[0])/mV:.3f} mV")


# ── Test B: PP→GC + PP→FS (magic network) ────────────────────────────────────
print("\n=== Test B: PP→GC + PP→FS (magic network) ===")
start_scope()
defaultclock.dt = DT_MS * ms

pp = SpikeGeneratorGroup(N_GC, idx, t_arr * ms)
gc = NeuronGroup(N_GC, GC_EQS, threshold='v>=30*mV',
                 reset=f'v={C_GC}*mV; u=u+{D_GC}*mV',
                 refractory=2*ms, method='euler')
fs = NeuronGroup(N_FS, FS_EQS, threshold='v>=30*mV',
                 reset=f'v={C_FS}*mV; u=u+{D_FS}*mV',
                 refractory=1*ms, method='euler')
gc.v=-70*mV; gc.u=B_GC*(-70*mV); gc.g_ex=0*mV; gc.g_in=0*mV
fs.v=-70*mV; fs.u=B_FS*(-70*mV); fs.g_ex=0*mV

_syns = []
syn_pp_gc = Synapses(pp, gc, on_pre='g_ex_post += 4.0*mV', delay=4*ms)
syn_pp_gc.connect(i=np.arange(N_GC), j=np.arange(N_GC))
_syns.append(syn_pp_gc)

syn_pp_fs = Synapses(pp, fs, on_pre='g_ex_post += 0.5*mV', delay=4*ms)
syn_pp_fs.connect(i=si_pp_fs, j=ti_pp_fs)
_syns.append(syn_pp_fs)

sp_gc = SpikeMonitor(gc)
sp_fs = SpikeMonitor(fs)
st_fs = StateMonitor(fs, ['v', 'g_ex'], record=True)

objs = collect()
print(f"Magic collects {len(objs)} objects before run()")
for o in objs:
    if isinstance(o, Synapses):
        print(f"  Synapse: {o.name}  source={o.source.name}  target={o.target.name}  N={len(o)}")

run(T_MS * ms)
print(f"FR_gc={sp_gc.num_spikes/(T_MS*1e-3*N_GC):.1f} Hz  FR_fs={sp_fs.num_spikes/(T_MS*1e-3*N_FS):.1f} Hz")
print(f"FS[0] max g_ex = {np.max(st_fs.g_ex[0])/mV:.3f} mV")
for t_check in [5, 10, 20, 50]:
    it = int(t_check / DT_MS)
    print(f"  t={t_check}ms: g_ex={st_fs.g_ex[0,it]/mV:.3f}mV  v={st_fs.v[0,it]/mV:.3f}mV")


# ── Test C: PP→GC + PP→FS (explicit Network) ─────────────────────────────────
print("\n=== Test C: PP→GC + PP→FS (explicit Network) ===")
start_scope()
defaultclock.dt = DT_MS * ms

pp = SpikeGeneratorGroup(N_GC, idx, t_arr * ms)
gc = NeuronGroup(N_GC, GC_EQS, threshold='v>=30*mV',
                 reset=f'v={C_GC}*mV; u=u+{D_GC}*mV',
                 refractory=2*ms, method='euler')
fs = NeuronGroup(N_FS, FS_EQS, threshold='v>=30*mV',
                 reset=f'v={C_FS}*mV; u=u+{D_FS}*mV',
                 refractory=1*ms, method='euler')
gc.v=-70*mV; gc.u=B_GC*(-70*mV); gc.g_ex=0*mV; gc.g_in=0*mV
fs.v=-70*mV; fs.u=B_FS*(-70*mV); fs.g_ex=0*mV

syn_pp_gc_c = Synapses(pp, gc, on_pre='g_ex_post += 4.0*mV', delay=4*ms)
syn_pp_gc_c.connect(i=np.arange(N_GC), j=np.arange(N_GC))

syn_pp_fs_c = Synapses(pp, fs, on_pre='g_ex_post += 0.5*mV', delay=4*ms)
syn_pp_fs_c.connect(i=si_pp_fs, j=ti_pp_fs)

sp_gc_c = SpikeMonitor(gc)
sp_fs_c = SpikeMonitor(fs)
st_fs_c = StateMonitor(fs, ['v', 'g_ex'], record=True)

net = Network(pp, gc, fs, syn_pp_gc_c, syn_pp_fs_c, sp_gc_c, sp_fs_c, st_fs_c)
net.run(T_MS * ms)
print(f"FR_gc={sp_gc_c.num_spikes/(T_MS*1e-3*N_GC):.1f} Hz  FR_fs={sp_fs_c.num_spikes/(T_MS*1e-3*N_FS):.1f} Hz")
print(f"FS[0] max g_ex = {np.max(st_fs_c.g_ex[0])/mV:.3f} mV")
for t_check in [5, 10, 20, 50]:
    it = int(t_check / DT_MS)
    print(f"  t={t_check}ms: g_ex={st_fs_c.g_ex[0,it]/mV:.3f}mV  v={st_fs_c.v[0,it]/mV:.3f}mV")
