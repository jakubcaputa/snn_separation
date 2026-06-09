"""Quick smoke test: run 1 trial of each condition and verify FS fires."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch T_MS and number of patterns for speed
import dg_module3_inh_comparison as m
import numpy as np

m.T_MS = 200.0  # shorter trial
m.N_PATTERNS = 2
m.SEEDS = [42]
m.R_TARGETS = [0.75]

rng_conn = np.random.default_rng(0)
conn = m.make_connectivity(rng_conn)
print(f"PP→FS synapses: {len(conn['pp_fs'][0])}, GC→FS: {len(conn['gc_fs'][0])}")

for cname, ckw in m.CONDITIONS.items():
    rng_s   = np.random.default_rng(42)
    pats    = m.make_gc_patterns(m.N_PATTERNS, m.N_GC, 0.75, m.P_ACTIVE, rng_s)
    rng_inp = np.random.default_rng(1042)
    idx, t_ms = m.make_input_spikes(pats[0], m.R_EFF_HIGH, m.R_EFF_LOW, m.T_MS, m.DT_MS, rng_inp)
    gc_i, gc_t, fs_i, fs_t = m.simulate_dg(idx, t_ms, conn, **ckw)
    fr_gc = len(gc_t) / (m.T_MS * 1e-3 * m.N_GC)
    fr_fs = len(fs_t) / (m.T_MS * 1e-3 * m.N_FS)
    has_ff = ckw.get('enable_ff', True)
    has_fb = ckw.get('enable_fb', True)
    status = "✓" if (fr_fs > 0 or (not has_ff and not has_fb)) else "✗ FS SILENT"
    print(f"  {cname:10s}  FR_gc={fr_gc:.1f}Hz  FR_fs={fr_fs:.1f}Hz  {status}")
