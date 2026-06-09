"""
Add HMC + full synapse set from simulate_dg() incrementally to find what breaks FS.
"""
import numpy as np
from brian2 import *
from brian2.core.magic import collect
from builtins import sum as builtins_sum

prefs.codegen.target = 'numpy'

N_GC  = 200; N_FS  = 20; N_HMC = 10
DT_MS = 0.1; T_MS  = 100.0

A_FS, B_FS, C_FS, D_FS   = 0.10, 0.2, -65.0, 2.0
A_GC, B_GC, C_GC, D_GC   = 0.02, 0.2, -65.0, 6.0
A_HMC, B_HMC, C_HMC, D_HMC = 0.02, 0.2, -65.0, 4.0
K_TONIC_GC=10.0; K_TONIC_FS=5.0; K_TONIC_HMC=10.0
TAU_EX_GC=5.0; TAU_IN_GC=8.0; TAU_EX_FS=3.0; TAU_EX_HMC=5.0
W_PP_GC=4.0; W_PP_FS=0.5; W_GC_FS=10.0; W_FS_GC=2.0
W_GC_HMC=1.0; W_HMC_FS=1.0; W_HMC_GC=0.5
PP_DELAY=4.0; SYN_DELAY=1.0
P_PP_FS=0.40; P_GC_FS=0.40; P_FS_GC=0.50; P_GC_HMC=0.25; P_HMC_FS=0.40; P_HMC_GC=0.40

def _izh_eqs(a, b, tau_ex, tau_in=None, K_tonic=0.0):
    inh_eq   = f"\ndg_in/dt = -g_in / ({tau_in}*ms) : volt" if tau_in else ""
    inh_term = "- g_in/ms " if tau_in else ""
    K_term   = f"- {K_tonic}*mV/ms" if K_tonic != 0.0 else ""
    return (
        f"dv/dt  = (0.04/mV/ms * v**2 + 5/ms * v + 140*mV/ms"
        f" - u/ms + g_ex/ms {inh_term}{K_term}) : volt (unless refractory)\n"
        f"dg_ex/dt = -g_ex / ({tau_ex}*ms) : volt{inh_eq}\n"
        f"du/dt  = {a}/ms * ({b} * v - u) : volt\n"
    )

GC_EQS  = _izh_eqs(A_GC,  B_GC,  TAU_EX_GC,  tau_in=TAU_IN_GC, K_tonic=K_TONIC_GC)
FS_EQS  = _izh_eqs(A_FS,  B_FS,  TAU_EX_FS,  tau_in=None,       K_tonic=K_TONIC_FS)
HMC_EQS = _izh_eqs(A_HMC, B_HMC, TAU_EX_HMC, tau_in=None,       K_tonic=K_TONIC_HMC)

# ── Generate spikes: 50 active at 600 Hz, 150 inactive at 40 Hz ──────────────
rng = np.random.default_rng(42)
n_steps = int(T_MS / DT_MS)
active_mask = np.zeros(N_GC, dtype=bool); active_mask[:50] = True

all_idx, all_t = [], []
for i in range(N_GC):
    rate = 600.0 if active_mask[i] else 40.0
    p = rate * DT_MS * 1e-3
    ts = np.where(rng.random(n_steps) < p)[0].astype(float) * DT_MS
    ts = ts[(ts > 0) & (ts < T_MS)]
    if len(ts):
        all_idx.append(np.full(len(ts), i, dtype=np.int32))
        all_t.append(ts)
idx_in = np.concatenate(all_idx)
t_in = np.concatenate(all_t)
order = np.argsort(t_in); idx_in, t_in = idx_in[order], t_in[order]

# ── Connectivity ──────────────────────────────────────────────────────────────
rng2 = np.random.default_rng(0)
def _pairs(Nr, Nc, p):
    mask = rng2.random((Nr, Nc)) < p
    s, t = np.where(mask)
    return s.astype(np.int32), t.astype(np.int32)

conn = {
    'pp_fs' : _pairs(N_GC,  N_FS,  P_PP_FS),
    'gc_fs' : _pairs(N_GC,  N_FS,  P_GC_FS),
    'fs_gc' : _pairs(N_FS,  N_GC,  P_FS_GC),
    'gc_hmc': _pairs(N_GC,  N_HMC, P_GC_HMC),
    'hmc_fs': _pairs(N_HMC, N_FS,  P_HMC_FS),
    'hmc_gc': _pairs(N_HMC, N_GC,  P_HMC_GC),
}

def _syn(src, tgt, si, ti, w_mV, var, delay_ms):
    if len(si) == 0: return None
    syn = Synapses(src, tgt, on_pre=f'{var}_post += {w_mV}*mV', delay=delay_ms*ms)
    syn.connect(i=si, j=ti)
    return syn

def make_groups():
    pp  = SpikeGeneratorGroup(N_GC, idx_in, t_in * ms)
    gc  = NeuronGroup(N_GC, GC_EQS,  threshold='v>=30*mV', reset=f'v={C_GC}*mV; u=u+{D_GC}*mV',  refractory=2*ms, method='euler')
    fs  = NeuronGroup(N_FS, FS_EQS,  threshold='v>=30*mV', reset=f'v={C_FS}*mV; u=u+{D_FS}*mV',  refractory=1*ms, method='euler')
    hmc = NeuronGroup(N_HMC, HMC_EQS, threshold='v>=30*mV', reset=f'v={C_HMC}*mV; u=u+{D_HMC}*mV', refractory=2*ms, method='euler')
    gc.v=-70*mV; gc.u=B_GC*(-70*mV); gc.g_ex=0*mV; gc.g_in=0*mV
    fs.v=-70*mV; fs.u=B_FS*(-70*mV); fs.g_ex=0*mV
    hmc.v=-70*mV; hmc.u=B_HMC*(-70*mV); hmc.g_ex=0*mV
    return pp, gc, fs, hmc

def run_test(label, extra_syns=None):
    start_scope()
    defaultclock.dt = DT_MS * ms
    pp, gc, fs, hmc = make_groups()
    _syns = []
    syn_pp_gc = Synapses(pp, gc, on_pre=f'g_ex_post += {W_PP_GC}*mV', delay=PP_DELAY*ms)
    syn_pp_gc.connect(i=np.arange(N_GC), j=np.arange(N_GC))
    _syns.append(syn_pp_gc)
    # PP→FS (always)
    s = _syn(pp, fs, conn['pp_fs'][0], conn['pp_fs'][1], W_PP_FS, 'g_ex', PP_DELAY)
    if s is not None: _syns.append(s)
    pp_fs_syn = s
    # Extra synapses (passed in)
    if extra_syns:
        for fn in extra_syns:
            s = fn(pp, gc, fs, hmc)
            if s is not None: _syns.append(s)
    sp_gc = SpikeMonitor(gc); sp_fs = SpikeMonitor(fs)
    st_fs = StateMonitor(fs, ['v', 'g_ex'], record=[0])
    objs = collect()
    syn_count = builtins_sum(1 for o in objs if isinstance(o, Synapses))
    run(T_MS * ms)
    fr_gc = sp_gc.num_spikes/(T_MS*1e-3*N_GC)
    fr_fs = sp_fs.num_spikes/(T_MS*1e-3*N_FS)
    max_gex = np.max(st_fs.g_ex[0])/mV
    print(f"{label:50s}  syns={syn_count}  FR_gc={fr_gc:.1f}Hz  FR_fs={fr_fs:.1f}Hz  max_gex={max_gex:.2f}mV")

print(f"{'Test':50s}  {'syns':5}  {'FR_gc':8}  {'FR_fs':8}  {'max_gex'}")

# Test 1: Just PP→GC + PP→FS
run_test("1: PP→GC + PP→FS")

# Test 2: + FS→GC
run_test("2: + FS→GC", [
    lambda pp,gc,fs,hmc: _syn(fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', SYN_DELAY)
])

# Test 3: + GC→HMC
run_test("3: + FS→GC + GC→HMC", [
    lambda pp,gc,fs,hmc: _syn(fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', SYN_DELAY),
    lambda pp,gc,fs,hmc: _syn(gc, hmc, conn['gc_hmc'][0], conn['gc_hmc'][1], W_GC_HMC, 'g_ex', SYN_DELAY),
])

# Test 4: + HMC→FS
run_test("4: + FS→GC + GC→HMC + HMC→FS", [
    lambda pp,gc,fs,hmc: _syn(fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', SYN_DELAY),
    lambda pp,gc,fs,hmc: _syn(gc, hmc, conn['gc_hmc'][0], conn['gc_hmc'][1], W_GC_HMC, 'g_ex', SYN_DELAY),
    lambda pp,gc,fs,hmc: _syn(hmc, fs, conn['hmc_fs'][0], conn['hmc_fs'][1], W_HMC_FS, 'g_ex', SYN_DELAY),
])

# Test 5: full (+ HMC→GC)
run_test("5: full circuit", [
    lambda pp,gc,fs,hmc: _syn(fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', SYN_DELAY),
    lambda pp,gc,fs,hmc: _syn(gc, hmc, conn['gc_hmc'][0], conn['gc_hmc'][1], W_GC_HMC, 'g_ex', SYN_DELAY),
    lambda pp,gc,fs,hmc: _syn(hmc, fs, conn['hmc_fs'][0], conn['hmc_fs'][1], W_HMC_FS, 'g_ex', SYN_DELAY),
    lambda pp,gc,fs,hmc: _syn(hmc, gc, conn['hmc_gc'][0], conn['hmc_gc'][1], W_HMC_GC, 'g_ex', SYN_DELAY),
])

# Test 6: Same as 5 but FS→GC BEFORE PP→FS to isolate ordering effect
print("\n=== Ordering tests: does _syn order matter? ===")
def run_test_order(label):
    start_scope()
    defaultclock.dt = DT_MS * ms
    pp, gc, fs, hmc = make_groups()
    _syns = []
    syn_pp_gc = Synapses(pp, gc, on_pre=f'g_ex_post += {W_PP_GC}*mV', delay=PP_DELAY*ms)
    syn_pp_gc.connect(i=np.arange(N_GC), j=np.arange(N_GC))
    _syns.append(syn_pp_gc)

    if label == 'FS→GC_first':
        # FS→GC created BEFORE PP→FS
        s = _syn(fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', SYN_DELAY)
        if s is not None: _syns.append(s)

    s = _syn(pp, fs, conn['pp_fs'][0], conn['pp_fs'][1], W_PP_FS, 'g_ex', PP_DELAY)
    if s is not None: _syns.append(s)

    if label == 'FS→GC_after':
        s = _syn(fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', SYN_DELAY)
        if s is not None: _syns.append(s)

    sp_gc = SpikeMonitor(gc); sp_fs = SpikeMonitor(fs)
    st_fs = StateMonitor(fs, ['v', 'g_ex'], record=[0])
    run(T_MS * ms)
    fr_fs = sp_fs.num_spikes/(T_MS*1e-3*N_FS)
    max_gex = np.max(st_fs.g_ex[0])/mV
    print(f"  {label}: FR_fs={fr_fs:.1f}Hz  max_gex={max_gex:.2f}mV")

run_test_order('FS→GC_first')
run_test_order('FS→GC_after')

# Test 7: Exact replicate of simulate_dg() ff_only with collect() inspection
print("\n=== Exact simulate_dg() replication with collect() ===")
start_scope()
defaultclock.dt = DT_MS * ms
pp, gc, fs, hmc = make_groups()
_syns = []
syn_pp_gc = Synapses(pp, gc, on_pre=f'g_ex_post += {W_PP_GC}*mV', delay=PP_DELAY*ms)
syn_pp_gc.connect(i=np.arange(N_GC), j=np.arange(N_GC))
_syns.append(syn_pp_gc)

s = _syn(pp, fs, conn['pp_fs'][0], conn['pp_fs'][1], W_PP_FS, 'g_ex', PP_DELAY)
if s is not None: _syns.append(s)

s = _syn(fs, gc, conn['fs_gc'][0], conn['fs_gc'][1], W_FS_GC, 'g_in', SYN_DELAY)
if s is not None: _syns.append(s)

s = _syn(gc,  hmc, conn['gc_hmc'][0], conn['gc_hmc'][1], W_GC_HMC, 'g_ex', SYN_DELAY)
if s is not None: _syns.append(s)

s = _syn(hmc, fs,  conn['hmc_fs'][0], conn['hmc_fs'][1], W_HMC_FS, 'g_ex', SYN_DELAY)
if s is not None: _syns.append(s)

s = _syn(hmc, gc,  conn['hmc_gc'][0], conn['hmc_gc'][1], W_HMC_GC, 'g_ex', SYN_DELAY)
if s is not None: _syns.append(s)

sp_gc = SpikeMonitor(gc); sp_fs = SpikeMonitor(fs)
st_fs = StateMonitor(fs, ['v', 'g_ex'], record=[0])

print(f"_syns has {len(_syns)} objects: {[type(x).__name__ for x in _syns]}")
objs = collect()
print(f"Magic network collects {len(objs)} objects")
for o in objs:
    if isinstance(o, Synapses):
        print(f"  {o.name}: {o.source.name} → {o.target.name}  N={len(o)}")

run(T_MS * ms)
fr_gc = sp_gc.num_spikes/(T_MS*1e-3*N_GC)
fr_fs = sp_fs.num_spikes/(T_MS*1e-3*N_FS)
max_gex = np.max(st_fs.g_ex[0])/mV
print(f"FR_gc={fr_gc:.1f}Hz  FR_fs={fr_fs:.1f}Hz  max_gex={max_gex:.2f}mV")
