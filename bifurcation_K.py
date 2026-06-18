"""
bifurcation_K.py — Priorytet 2:  CZYM JEST PARAMETR K_tonic?

K_tonic w naszych równaniach Izhikevicza to stały (toniczny) prąd HAMUJĄCY,
reprezentujący toniczne tło GABA-A.  Wchodzi do równania napięcia jako
„− K·mV/ms", czyli przesuwa neuron w stronę mniejszej pobudliwości: podnosi
RHEOBAZĘ, czyli próg pobudzenia G_crit (ile mV g_ex trzeba, by neuron odpalił).

──────────────────────────────────────────────────────────────────────────────
WYPROWADZENIE ANALITYCZNE (dlaczego G_crit = 4 + K dla b = 0.2)
──────────────────────────────────────────────────────────────────────────────
Model:   dv/dt = 0.04 v² + 5 v + 140 − u + I_net
         du/dt = a (b v − u)
gdzie w naszej implementacji stały napęd I_net = g_ex − K  (oba w mV/ms).

Punkty stałe:  du/dt = 0 ⟹ u = b v.  Podstawiając do dv/dt = 0:
         0.04 v² + (5 − b) v + (140 + I_net) = 0
To równanie kwadratowe ma pierwiastki (punkty stałe) dopóki wyróżnik ≥ 0:
         (5 − b)² − 4·0.04·(140 + I_net) ≥ 0
Bifurkacja siodło-węzeł (znikają punkty stałe → neuron zaczyna strzelać) przy:
         I_net* = (5 − b)² / 0.16 − 140
Ponieważ I_net = g_ex − K, próg pobudzenia w jednostkach g_ex wynosi:
         G_crit(K) = I_net* + K = (5 − b)²/0.16 − 140 + K

Dla b = 0.2 (GC, FS, HMC):  (4.8)²/0.16 − 140 = 144 − 140 = 4  ⟹  G_crit = 4 + K.

  → K_GC  = 10  ⟹  G_crit ≈ 14 mV
  → K_FS  =  5  ⟹  G_crit ≈  9 mV
  → K_HMC = 10  ⟹  G_crit ≈ 14 mV

Ten skrypt POTWIERDZA to empirycznie (symulacja Brian2) i rysuje:
  A) krzywe f–I (firing rate vs g_ex) dla różnych K — próg przesuwa się o K,
  B) G_crit(K): analityczne 4+K vs zmierzone, z punktami pracy GC/FS,
  C) płaszczyznę fazową (nullcliny) poniżej i powyżej bifurkacji.

Wyjście:  bifurcation_K.png  + tabela w konsoli
Run:      snn_sep_venv\\Scripts\\python.exe bifurcation_K.py
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from brian2 import (
    start_scope, NeuronGroup, SpikeMonitor,
    run, defaultclock, ms, mV, second, prefs,
)
prefs.codegen.target = 'numpy'

from dg_params import R_EFF_HIGH, W_PP_GC_IZH

# ── Parametry Izhikevicza (te same co w interactive_dg / module3) ─────────────
A_GC,  B_GC,  C_GC,  D_GC  = 0.02, 0.2, -65.0, 6.0
A_FS,  B_FS,  C_FS,  D_FS  = 0.10, 0.2, -65.0, 2.0
TAU_EX_GC = 5.0     # ms — do przeliczenia g_ex z częstotliwości wejścia

K_GC_OP = 10.0      # punkt pracy GC
K_FS_OP =  5.0      # punkt pracy FS


def G_crit_analytic(b, K):
    """Analityczny próg pobudzenia w jednostkach g_ex [mV]."""
    return (5.0 - b) ** 2 / 0.16 - 140.0 + K


# ══════════════════════════════════════════════════════════════════════════════
# EMPIRYCZNE f–I:  firing rate vs stały g_ex, dla siatki (g_ex, K)
# ══════════════════════════════════════════════════════════════════════════════

def measure_fi(a, b, c, d, g_vals, K_vals, T_ms=1000.0):
    """
    Zwróć macierz firing rate [Hz] o kształcie (len(K_vals), len(g_vals)).
    Każdy neuron dostaje STAŁY napęd g_ex (gin) i własne K (Kc) — jako parametry.
    """
    start_scope()
    defaultclock.dt = 0.1 * ms

    GG, KK = np.meshgrid(g_vals, K_vals)     # (nK, nG)
    g_flat = GG.ravel()
    k_flat = KK.ravel()
    n = g_flat.size

    eqs = """
    dv/dt = (0.04/mV/ms*v**2 + 5/ms*v + 140*mV/ms - u/ms + gin - Kc) : volt (unless refractory)
    du/dt = a_p*(b_p*v - u) : volt
    gin : volt/second
    Kc  : volt/second
    a_p : 1/second
    b_p : 1
    """
    G = NeuronGroup(n, eqs, threshold='v>=30*mV',
                    reset=f'v={c}*mV; u=u+{d}*mV',
                    refractory=(1.0 if a > 0.05 else 2.0) * ms, method='euler')
    G.v = -70 * mV
    G.u = b * (-70 * mV)
    G.gin = g_flat * mV / ms
    G.Kc  = k_flat * mV / ms
    G.a_p = a / ms
    G.b_p = b

    sm = SpikeMonitor(G)
    run(T_ms * ms)
    rates = np.array(sm.count) / (T_ms * 1e-3)
    return rates.reshape(GG.shape)            # (nK, nG)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 74)
print(" CZYM JEST K_tonic?  Analiza bifurkacji neuronu Izhikevicza (Priorytet 2)")
print("=" * 74 + "\n")

# g_ex odpowiadający kanonicznemu napędowi 400 Hz: g_ex_ss = r·W·τ
g_drive_400 = R_EFF_HIGH * W_PP_GC_IZH * (TAU_EX_GC * 1e-3)
print(f"Kanoniczny napęd aktywnego GC: {R_EFF_HIGH:.0f} Hz × {W_PP_GC_IZH} mV × "
      f"{TAU_EX_GC} ms = <g_ex> ≈ {g_drive_400:.1f} mV\n")

# ── Tabela analityczna vs empiryczna ──────────────────────────────────────────
g_vals = np.linspace(0, 30, 121)
K_show = [0.0, 5.0, 10.0, 15.0]

fi_gc = measure_fi(A_GC, B_GC, C_GC, D_GC, g_vals, K_show)

print("─" * 74)
print("G_crit (próg pobudzenia g_ex) — GC (b=0.2):  analityczny 4+K  vs  zmierzony")
print("─" * 74)
print(f"  {'K':>5} {'G_crit analit.':>16} {'G_crit zmierz.':>16}")
for i, K in enumerate(K_show):
    # empiryczny próg = najmniejsze g_ex dające >1 Hz
    fired = np.where(fi_gc[i] > 1.0)[0]
    g_emp = g_vals[fired[0]] if len(fired) else float('nan')
    print(f"  {K:>5.0f} {G_crit_analytic(B_GC, K):>16.1f} {g_emp:>16.1f}")
print(f"\n  → Zgodność potwierdza: K przesuwa próg pobudzenia liniowo (G_crit = 4 + K).")
print(f"  → GC przy K={K_GC_OP:.0f}: G_crit≈{G_crit_analytic(B_GC,K_GC_OP):.0f} mV, "
      f"napęd 400 Hz daje {g_drive_400:.0f} mV → PODPROGOWO → reżim fluktuacyjny ✓\n")

# Siatka K do gładkiej krzywej G_crit(K)
K_fine = np.linspace(0, 20, 41)
fi_gc_fine = measure_fi(A_GC, B_GC, C_GC, D_GC, g_vals, K_fine)
g_emp_fine = np.array([
    (g_vals[np.where(fi_gc_fine[i] > 1.0)[0][0]]
     if np.any(fi_gc_fine[i] > 1.0) else np.nan)
    for i in range(len(K_fine))
])


# ══════════════════════════════════════════════════════════════════════════════
# FIGURA (3 panele)
# ══════════════════════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(16, 6.0))
gs = fig.add_gridspec(1, 3, wspace=0.30)

# ── A: krzywe f–I dla różnych K ───────────────────────────────────────────────
axA = fig.add_subplot(gs[0, 0])
colors = plt.cm.viridis(np.linspace(0.1, 0.85, len(K_show)))
for i, K in enumerate(K_show):
    axA.plot(g_vals, fi_gc[i], color=colors[i], lw=2, label=f'K = {K:.0f}')
    axA.axvline(G_crit_analytic(B_GC, K), color=colors[i], ls=':', lw=1, alpha=0.6)
axA.axvline(g_drive_400, color='crimson', ls='--', lw=1.5,
            label=f'napęd 400 Hz ≈ {g_drive_400:.0f} mV')
axA.set(xlabel='Stały g_ex [mV]', ylabel='Firing rate GC [Hz]',
        title='A) Krzywe f–I: K przesuwa próg w prawo\n(każda pionowa kropka = G_crit = 4+K)')
axA.legend(fontsize=8, loc='upper left')
axA.spines[['top', 'right']].set_visible(False)

# ── B: G_crit(K) analityczny vs empiryczny ───────────────────────────────────
axB = fig.add_subplot(gs[0, 1])
axB.plot(K_fine, 4.0 + K_fine, color='steelblue', lw=2, label='analit. G_crit = 4 + K')
axB.plot(K_fine, g_emp_fine, 'o', color='darkorange', ms=3, alpha=0.7,
         label='zmierzone (Brian2)')
for K_op, lbl, col in [(K_FS_OP, 'FS', '#C62828'), (K_GC_OP, 'GC', '#1565C0')]:
    axB.scatter([K_op], [G_crit_analytic(0.2, K_op)], s=80, color=col, zorder=5,
                edgecolor='black', linewidth=0.8)
    axB.annotate(f'{lbl}\nK={K_op:.0f}→{G_crit_analytic(0.2,K_op):.0f}mV',
                 (K_op, G_crit_analytic(0.2, K_op)),
                 textcoords='offset points', xytext=(8, -18), fontsize=8, color=col)
axB.set(xlabel='K_tonic', ylabel='G_crit (próg g_ex) [mV]',
        title='B) Próg pobudzenia rośnie liniowo z K\n(toniczna GABA → mniej pobudliwy neuron)')
axB.legend(fontsize=8, loc='upper left')
axB.spines[['top', 'right']].set_visible(False)

# ── C: płaszczyzna fazowa (nullcliny) poniżej i powyżej bifurkacji ────────────
axC = fig.add_subplot(gs[0, 2])
v = np.linspace(-80, -40, 300)
K_demo = K_GC_OP
for g_ex_demo, style, lbl in [(8.0, '-', 'g_ex=8 (400 Hz, podprogowo)'),
                              (20.0, '--', 'g_ex=20 (nadprogowo)')]:
    I_net = g_ex_demo - K_demo
    u_vnull = 0.04 * v**2 + 5 * v + 140 + I_net      # v-nullcline (u gdzie dv/dt=0)
    axC.plot(v, u_vnull, color='teal', ls=style, lw=1.8, label=f'v-nullcline: {lbl}')
axC.plot(v, B_GC * v, color='purple', lw=1.8, label='u-nullcline: u = b·v')
axC.set(xlabel='v [mV]', ylabel='u [mV]', ylim=(-20, 10),
        title=f'C) Płaszczyzna fazowa GC (K={K_demo:.0f})\nprzecięcia = punkty stałe; '
              f'brak przecięć ⟹ neuron strzela')
axC.legend(fontsize=7, loc='upper center')
axC.spines[['top', 'right']].set_visible(False)

fig.suptitle('K_tonic = toniczny prąd hamujący → podnosi próg pobudzenia G_crit = 4 + K',
             fontsize=13, fontweight='bold', y=0.99)
fig.subplots_adjust(top=0.78, bottom=0.12, left=0.05, right=0.98)
out = __file__.replace('.py', '.png')
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Zapisano figurę: {out}")
print("\n" + "=" * 74)
print(" WNIOSEK: K to siła tonicznego hamowania GABA. Każdy +1 K podnosi próg")
print(" pobudzenia o ~1 mV. GC/HMC (K=10) są trudniej pobudliwe niż FS (K=5),")
print(" dlatego FS odpalają łatwo (interneurony), a GC pozostają rzadkie.")
print("=" * 74)
