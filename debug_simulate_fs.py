"""
Replicate exactly one simulate_dg() trial (ff_only) with a FS StateMonitor
to see why FS fires 0 Hz in the full simulation.
"""
import numpy as np
from brian2 import *

prefs.codegen.target = 'numpy'

# ── Copy parameters from dg_module3_inh_comparison.py ────────────────────────
N_GC  = 200
N_FS  = 20
N_HMC = 10
T_MS  = 200.0   # shorter for debugging
DT_MS = 0.1

R_EFF_HIGH = 600.0
R_EFF_LOW  =  40.0
P_ACTIVE   = 0.25
N_PATTERNS = 5
R_target   = 0.75

A_GC, B_GC, C_GC, D_GC = 0.02, 0.2, -65.0, 6.0
A_FS, B_FS, C_FS, D_FS = 0.10, 0.2, -65.0, 2.0
A_HMC, B_HMC, C_HMC, D_HMC = 0.02, 0.2, -65.0, 4.0

K_TONIC_GC  = 10.0
K_TONIC_FS  =  5.0
K_TONIC_HMC = 10.0

TAU_EX_GC  =  5.0
TAU_IN_GC  =  8.0
TAU_EX_FS  =  3.0
TAU_EX_HMC =  5.0

W_PP_GC  =  4.0
W_PP_FS  =  0.5
W_GC_FS  = 10.0
W_FS_GC  =  2.0
W_GC_HMC =  1.0
W_HMC_FS =  1.0
W_HMC_GC =  0.5

PP_DELAY  = 4.0
SYN_DELAY = 1.0

P_PP_FS   = 0.40
P_GC_FS   = 0.40
P_FS_GC   = 0.50
P_GC_HMC  = 0.25
P_HMC_FS  = 0.40
P_HMC_GC  = 0.40

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

print("FS_EQS:\n", FS_EQS)

def make_gc_patterns(N_pat, N_GC, R, p_active, rng):
    common = rng.random(N_GC) < (p_active * R)
    pats = np.zeros((N_pat, N_GC), dtype=bool)
    for k in range(N_pat):
        pats[k] = common | (rng.random(N_GC) < p_active * (1.0 - R))
    return pats

def make_input_spikes(pattern_active, r_high, r_low, T_ms, dt_ms, rng):
    n_steps = int(T_ms / dt_ms)
    all_idx, all_t = [], []
    for i, active in enumerate(pattern_active):
        rate = r_high if active else r_low
        p    = rate * dt_ms * 1e-3
        ts   = np.where(rng.random(n_steps) < p)[0].astype(float) * dt_ms
        ts   = ts[(ts > 0) & (ts < T_ms)]
        if len(ts):
            all_idx.append(np.full(len(ts), i, dtype=np.int32))
            all_t.append(ts)
    if all_idx:
        idx = np.concatenate(all_idx)
        t   = np.concatenate(all_t)
        order = np.argsort(t)
        return idx[order], t[order]
    return np.array([], dtype=np.int32), np.array([])

def _syn(src, tgt, si, ti, w_mV, var, delay_ms):
    if len(si) == 0:
        return None
    syn = Synapses(src, tgt,
                   on_pre=f'{var}_post += {w_mV}*mV',
                   delay=delay_ms * ms)
    syn.connect(i=si, j=ti)
    return syn

# ── Build connectivity ────────────────────────────────────────────────────────
rng_conn = np.random.default_rng(0)
def _pairs(N_src, N_tgt, p):
    mask = rng_conn.random((N_src, N_tgt)) < p
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
print(f"PP→FS synapses: {len(conn['pp_fs'][0])} (expected ~{int(N_GC*N_FS*P_PP_FS)})")

# ── Generate one pattern ──────────────────────────────────────────────────────
rng_s = np.random.default_rng(42)
pats  = make_gc_patterns(N_PATTERNS, N_GC, R_target, P_ACTIVE, rng_s)
pat   = pats[0]
n_active = pat.sum()
print(f"Active GCs in pattern 0: {n_active}")
print(f"Active PP indices connected to FS neuron 0: "
      f"{(conn['pp_fs'][1] == 0).sum()} total connections to FS[0]")
active_to_fs0 = np.sum((conn['pp_fs'][1] == 0) & pat[conn['pp_fs'][0]])
print(f"  ...of which {active_to_fs0} come from ACTIVE PP neurons")

rng_inp = np.random.default_rng(1042)
idx, t_ms = make_input_spikes(pat, R_EFF_HIGH, R_EFF_LOW, T_MS, DT_MS, rng_inp)
n_active_spikes = np.sum(pat[idx])
n_inactive_spikes = np.sum(~pat[idx])
print(f"\nTotal PP spikes: {len(idx)}")
print(f"  from active GCs: {n_active_spikes}  (expected ~{int(n_active * R_EFF_HIGH * T_MS/1000)})")
print(f"  from inactive GCs: {n_inactive_spikes}  (expected ~{int((N_GC-n_active)*R_EFF_LOW*T_MS/1000)})")

# ── Run simulate_dg-equivalent with StateMonitor ──────────────────────────────
print("\n=== Simulating ff_only with StateMonitor on FS ===")
start_scope()
defaultclock.dt = DT_MS * ms

pp = SpikeGeneratorGroup(N_GC, idx, t_ms * ms)

gc = NeuronGroup(N_GC, GC_EQS, threshold='v >= 30*mV',
                 reset=f'v = {C_GC}*mV; u = u + {D_GC}*mV',
                 refractory=2*ms, method='euler')
fs = NeuronGroup(N_FS, FS_EQS, threshold='v >= 30*mV',
                 reset=f'v = {C_FS}*mV; u = u + {D_FS}*mV',
                 refractory=1*ms, method='euler')
hmc = NeuronGroup(N_HMC, HMC_EQS, threshold='v >= 30*mV',
                  reset=f'v = {C_HMC}*mV; u = u + {D_HMC}*mV',
                  refractory=2*ms, method='euler')

gc.v  = -70*mV;  gc.u  = B_GC  * (-70*mV);  gc.g_ex  = 0*mV;  gc.g_in = 0*mV
fs.v  = -70*mV;  fs.u  = B_FS  * (-70*mV);  fs.g_ex  = 0*mV
hmc.v = -70*mV;  hmc.u = B_HMC * (-70*mV);  hmc.g_ex = 0*mV

_syns = []

syn_pp_gc = Synapses(pp, gc, on_pre=f'g_ex_post += {W_PP_GC}*mV', delay=PP_DELAY*ms)
syn_pp_gc.connect(i=np.arange(N_GC), j=np.arange(N_GC))
_syns.append(syn_pp_gc)

# ff_only: enable_ff=True, enable_fb=False, enable_hmc=True
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

sm_gc  = SpikeMonitor(gc)
sm_fs  = SpikeMonitor(fs)
st_fs  = StateMonitor(fs, ['v', 'g_ex'], record=True)  # Monitor ALL FS neurons

run(T_MS * ms)

print(f"\nGC spikes: {sm_gc.num_spikes}  FR_gc = {sm_gc.num_spikes/(T_MS*1e-3*N_GC):.1f} Hz")
print(f"FS spikes: {sm_fs.num_spikes}  FR_fs = {sm_fs.num_spikes/(T_MS*1e-3*N_FS):.1f} Hz")

# Print per-FS-neuron max g_ex
print("\nPer-FS-neuron max g_ex and max v (first 5):")
for j in range(min(5, N_FS)):
    max_gex = np.max(st_fs.g_ex[j]) / mV
    max_v   = np.max(st_fs.v[j]) / mV
    n_syn = np.sum(conn['pp_fs'][1] == j)
    n_active_syn = np.sum((conn['pp_fs'][1] == j) & pat[conn['pp_fs'][0]])
    print(f"  FS[{j}]: {n_syn} PP connections ({n_active_syn} from active), "
          f"max g_ex={max_gex:.2f} mV, max v={max_v:.2f} mV, "
          f"spikes={np.sum(sm_fs.i == j)}")

# Overall max g_ex across all FS neurons
all_max_gex = np.array([np.max(st_fs.g_ex[j])/mV for j in range(N_FS)])
print(f"\nMax g_ex across all FS: {np.max(all_max_gex):.2f} mV (median={np.median(all_max_gex):.2f} mV)")
print(f"G_crit_FS = {4 + K_TONIC_FS:.0f} mV")

# Check g_ex at specific times
print("\ng_ex[FS neuron 0] at key time points:")
for t_check in [5, 10, 20, 50, 100]:
    if t_check < T_MS:
        i_t = int(t_check / DT_MS)
        print(f"  t={t_check}ms: g_ex={st_fs.g_ex[0,i_t]/mV:.3f} mV  v={st_fs.v[0,i_t]/mV:.3f} mV")
