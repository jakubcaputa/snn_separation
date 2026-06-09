"""
Trace FS voltage trajectory step by step with g_ex=18mV
to diagnose why FS doesn't fire.
"""
import numpy as np
from brian2 import *

prefs.codegen.target = 'numpy'
start_scope()
defaultclock.dt = 0.1 * ms

A_FS, B_FS, C_FS, D_FS = 0.10, 0.2, -65.0, 2.0
K_TONIC_FS = 5.0
TAU_EX_FS  = 3.0

FS_EQS = (
    f"dv/dt  = (0.04/mV/ms * v**2 + 5/ms * v + 140*mV/ms"
    f" - u/ms + g_ex/ms - {K_TONIC_FS}*mV/ms) : volt (unless refractory)\n"
    f"dg_ex/dt = -g_ex / ({TAU_EX_FS}*ms) : volt\n"
    f"du/dt  = {A_FS}/ms * ({B_FS} * v - u) : volt\n"
)

fs = NeuronGroup(1, FS_EQS,
                 threshold='v >= 30*mV',
                 reset=f'v = {C_FS}*mV; u = u + {D_FS}*mV',
                 refractory=1*ms, method='euler')
fs.v = -70 * mV
fs.u = B_FS * (-70 * mV)
fs.g_ex = 18 * mV

sm = StateMonitor(fs, ['v', 'g_ex', 'u'], record=True)
sp = SpikeMonitor(fs)

run(5 * ms)

print("Step-by-step trajectory (first 50 steps = 5ms):")
print(f"{'t(ms)':>8}  {'v(mV)':>10}  {'g_ex(mV)':>10}  {'u(mV)':>10}  dv/dt(mV/ms)")
for i in range(50):
    t_i = i * 0.1
    v_i = sm.v[0, i] / mV
    g_i = sm.g_ex[0, i] / mV
    u_i = sm.u[0, i] / mV
    # Compute expected dv/dt
    dvdt = 0.04 * v_i**2 + 5 * v_i + 140 - u_i + g_i - K_TONIC_FS
    print(f"{t_i:>8.1f}  {v_i:>10.4f}  {g_i:>10.4f}  {u_i:>10.4f}  {dvdt:>12.4f}")

print(f"\nTotal FS spikes in 5ms: {sp.count[0]}")

# ── Manual Euler for comparison ───────────────────────────────────────────────
print("\n--- Manual Euler comparison ---")
v, g, u_val = -70.0, 18.0, -14.0
dt = 0.1
for i in range(50):
    dvdt = 0.04*v**2 + 5*v + 140 - u_val + g - K_TONIC_FS
    dgdt = -g / 3.0
    dudt = A_FS * (B_FS * v - u_val)
    if i < 5 or i % 10 == 0:
        print(f"t={i*dt:.1f}ms: v={v:.4f}mV, g={g:.4f}mV, u={u_val:.4f}mV, dv/dt={dvdt:.4f}mV/ms")
    v += dt * dvdt
    g += dt * dgdt
    u_val += dt * dudt
    if v >= 30:
        print(f"  → SPIKE at t={(i+1)*dt:.1f}ms, resetting to {C_FS}mV, u+={D_FS}mV")
        v = C_FS
        u_val += D_FS

print(f"Manual Euler final v={v:.4f}mV, g={g:.4f}mV")
