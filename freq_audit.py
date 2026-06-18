"""
freq_audit.py — Priorytet 1 / krok 1:  AUDYT CZĘSTOTLIWOŚCI SYGNAŁU.

Cel: pokazać twardymi liczbami, jakie częstotliwości FAKTYCZNIE wchodzą i
wychodzą z sieci DG, i odpowiedzieć na pytanie ze spotkania:
    „czy 600 Hz aggregate nie jest za dużo?"

Co robi ten skrypt (nic NIE zmienia w modelach — tylko mierzy):

  A) Superpozycja Poissona — pokazuje, że N włókien × r_fiber Hz daje proces
     nieodróżnialny od jednego procesu r_agg = N·r_fiber Hz.  Tu nie ma błędu.

  B) Stan ustalony g_ex — ile mV pobudzenia daje dany aggregate rate
     (analitycznie:  <g_ex> = r_agg · W · τ_ex)  i jak to się ma do progu
     bifurkacji G_crit (z komentarzy module3: GC G_crit≈14 mV przy K=10).

  C) EMPIRYCZNA krzywa wejście→wyjście — uruchamia PRAWDZIWY neuron GC
     (Izhikevich, parametry z dg_module3_inh_comparison.py) dla zakresu
     aggregate rate i mierzy output firing rate GC.  Tu zobaczymy, czy GC
     jest w reżimie RZADKIEGO KODOWANIA (DG: aktywne GC ~1–10 Hz, reszta ~0)
     czy strzela za szybko.

  D) Porównanie międzymodelowe — czego używa każdy skrypt w repo
     (single_neuron 10 Hz/syn, microcircuit 15 Hz/syn, module3 15 Hz/syn).

Wyjście:  konsola (tabele) + freq_audit.png
Run:      snn_sep_venv\\Scripts\\python.exe freq_audit.py
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

# Konsola Windows (cp1250) nie radzi sobie z Unicode — wymuś UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from brian2 import (
    start_scope, NeuronGroup, Synapses,
    SpikeMonitor, StateMonitor, SpikeGeneratorGroup, PoissonGroup,
    run, defaultclock, ms, mV, Hz, prefs,
)

prefs.codegen.target = 'numpy'

# ══════════════════════════════════════════════════════════════════════════════
# PARAMETRY GC — skopiowane 1:1 z dg_module3_inh_comparison.py
# (żeby audyt mierzył dokładnie ten neuron, którego używamy w obwodzie)
# ══════════════════════════════════════════════════════════════════════════════

A_GC, B_GC, C_GC, D_GC = 0.02, 0.2, -65.0, 6.0
K_TONIC_GC = 10.0      # toniczna GABA → G_crit ≈ 14 mV (patrz Priorytet 2)
TAU_EX_GC  = 5.0       # ms — AMPA
W_PP_GC    = 4.0       # mV — waga PP → GC

GC_EQS = (
    f"dv/dt  = (0.04/mV/ms * v**2 + 5/ms * v + 140*mV/ms"
    f" - u/ms + g_ex/ms - {K_TONIC_GC}*mV/ms) : volt (unless refractory)\n"
    f"dg_ex/dt = -g_ex / ({TAU_EX_GC}*ms) : volt\n"
    f"du/dt  = {A_GC}/ms * ({B_GC} * v - u) : volt\n"
)

# Reżimy wejścia używane w repo
N_FIBERS_PER_GC = 40       # liczba włókien PP na jeden GC (model)
REGIMES = {
    'single_neuron (10 Hz/fiber)': 10.0,
    'microcircuit  (15 Hz/fiber)': 15.0,
    'module3       (15 Hz/fiber)': 15.0,
}

# Reżim wartości „aktywny/nieaktywny" obecnie zaszyty w module3 / microcircuit
R_EFF_HIGH = 600.0   # Hz aggregate — GC aktywny
R_EFF_LOW  = 40.0    # Hz aggregate — tło

T_MS  = 2000.0
DT_MS = 0.1


# ══════════════════════════════════════════════════════════════════════════════
# A) SUPERPOZYCJA POISSONA — czy 40×15 Hz ≡ 1×600 Hz?
# ══════════════════════════════════════════════════════════════════════════════

def audit_superposition(rng):
    """Porównaj statystyki g_ex dla 40 włókien×15 Hz vs 1 włókna×600 Hz."""
    n_steps = int(T_MS / DT_MS)

    def aggregate_spike_count(n_fibers, r_fiber):
        p = r_fiber * DT_MS * 1e-3
        total = 0
        for _ in range(n_fibers):
            total += int(np.count_nonzero(rng.random(n_steps) < p))
        return total

    n_multi = aggregate_spike_count(N_FIBERS_PER_GC, 15.0)
    n_lump  = aggregate_spike_count(1, 600.0)

    print("─" * 74)
    print("A) SUPERPOZYCJA POISSONA  (twierdzenie: niezależne Poissony się sumują)")
    print("─" * 74)
    print(f"  40 włókien × 15 Hz przez {T_MS:.0f} ms : {n_multi:5d} spikes "
          f"(oczek. {int(40*15*T_MS/1000):5d})  → {n_multi/(T_MS/1000):.0f} Hz agg.")
    print(f"   1 proces × 600 Hz przez {T_MS:.0f} ms : {n_lump:5d} spikes "
          f"(oczek. {int(600*T_MS/1000):5d})  → {n_lump/(T_MS/1000):.0f} Hz agg.")
    print("  → Statystycznie nieodróżnialne. LUMPING SAM W SOBIE NIE JEST BŁĘDEM.")
    print("    Pytanie nie brzmi 'czy 600 Hz', lecz 'jaki OUTPUT GC to daje?' (sek. C)\n")
    return n_multi, n_lump


# ══════════════════════════════════════════════════════════════════════════════
# B) STAN USTALONY g_ex  =  r_agg · W · τ_ex
# ══════════════════════════════════════════════════════════════════════════════

def g_ex_steady_state(r_agg_hz, w_mV=W_PP_GC, tau_ms=TAU_EX_GC):
    """Średnie g_ex [mV] dla wejścia Poissona r_agg, wagi w, stałej τ."""
    return r_agg_hz * w_mV * (tau_ms * 1e-3)


def audit_steady_state():
    G_crit = 4.0 + K_TONIC_GC      # próg bifurkacji ≈ 4 mV bazowo + K
    print("─" * 74)
    print(f"B) STAN USTALONY g_ex = r_agg · W · τ   (W={W_PP_GC} mV, τ={TAU_EX_GC} ms)")
    print(f"   Próg bifurkacji G_crit ≈ {G_crit:.0f} mV  (4 mV bazowo + K={K_TONIC_GC})")
    print("─" * 74)
    print(f"  {'r_agg [Hz]':>12} {'<g_ex> [mV]':>13} {'reżim':>28}")
    for r in [40, 200, 400, 600, 800, 1000]:
        g = g_ex_steady_state(r)
        if g < G_crit - 2:
            reg = "podprogowy (fluktuacyjny)"
        elif g < G_crit + 2:
            reg = "blisko G_crit (czuły)"
        else:
            reg = "nadprogowy (mean-driven)"
        print(f"  {r:>12} {g:>13.1f} {reg:>28}")
    print(f"\n  600 Hz → <g_ex>={g_ex_steady_state(600):.0f} mV  (poniżej G_crit={G_crit:.0f})"
          f" → GC napędzany FLUKTUACJAMI, nie średnią — to dobrze dla separacji.")
    print(f"  Ale empiryczny output trzeba zmierzyć (sek. C).\n")
    return G_crit


# ══════════════════════════════════════════════════════════════════════════════
# C) EMPIRYCZNA KRZYWA WEJŚCIE → WYJŚCIE  (prawdziwy neuron GC)
# ══════════════════════════════════════════════════════════════════════════════

def measure_gc_output(r_agg_hz, rng, n_trials=8):
    """
    Uruchom n_trials niezależnych neuronów GC, każdy z własnym aggregate
    Poissonem r_agg, i zwróć średni output firing rate [Hz].
    """
    start_scope()
    defaultclock.dt = DT_MS * ms

    # n_trials neuronów GC, każdy dostaje 1 aggregate Poisson (1:1)
    pp = PoissonGroup(n_trials, rates=r_agg_hz * Hz)
    gc = NeuronGroup(n_trials, GC_EQS,
                     threshold='v >= 30*mV',
                     reset=f'v = {C_GC}*mV; u = u + {D_GC}*mV',
                     refractory=2 * ms, method='euler')
    gc.v = -70 * mV
    gc.u = B_GC * (-70 * mV)
    gc.g_ex = 0 * mV

    syn = Synapses(pp, gc, on_pre=f'g_ex_post += {W_PP_GC}*mV', delay=4 * ms)
    syn.connect(i=np.arange(n_trials), j=np.arange(n_trials))

    sm = SpikeMonitor(gc)
    run(T_MS * ms)

    counts = np.array(sm.count)            # spikes per neuron
    rates  = counts / (T_MS * 1e-3)        # Hz
    return float(rates.mean()), float(rates.std())


def audit_io_curve(rng):
    print("─" * 74)
    print("C) EMPIRYCZNY OUTPUT GC  (prawdziwy neuron Izhikevich, 8 prób/rate)")
    print("    DG = rzadkie kodowanie: AKTYWNE GC ~1–10 Hz, tło ~0 Hz")
    print("─" * 74)
    rates_in = [40, 100, 200, 300, 400, 500, 600, 800, 1000]
    out_mean, out_std = [], []
    print(f"  {'r_agg [Hz]':>12} {'output GC [Hz]':>18} {'ocena':>22}")
    for r in rates_in:
        m, s = measure_gc_output(r, rng)
        out_mean.append(m); out_std.append(s)
        if m < 0.5:
            verdict = "milczy"
        elif m <= 12:
            verdict = "✓ fizjologiczne"
        elif m <= 25:
            verdict = "wysoko"
        else:
            verdict = "✗ ZA SZYBKO"
        print(f"  {r:>12} {m:>10.1f} ± {s:>4.1f} {verdict:>22}")

    m600, _ = out_mean[rates_in.index(600)], None
    m40,  _ = out_mean[rates_in.index(40)],  None
    print(f"\n  Obecny setup:  aktywny=600 Hz → {m600:.1f} Hz output, "
          f"tło=40 Hz → {m40:.1f} Hz output")
    if m600 > 25:
        print("  → WNIOSEK: output GC ZA WYSOKI. Trzeba obniżyć r_agg lub W_PP_GC.")
    elif m600 > 12:
        print("  → WNIOSEK: output GC nieco za wysoki jak na DG; rozważyć obniżenie.")
    else:
        print("  → WNIOSEK: output GC w zakresie fizjologicznym.")
    print()
    return rates_in, out_mean, out_std


# ══════════════════════════════════════════════════════════════════════════════
# D) PORÓWNANIE MIĘDZYMODELOWE
# ══════════════════════════════════════════════════════════════════════════════

def audit_cross_model():
    print("─" * 74)
    print("D) NIESPÓJNOŚĆ MIĘDZY SKRYPTAMI  (per-fiber → aggregate)")
    print("─" * 74)
    print(f"  {'skrypt':>30} {'r_fiber':>9} {'×N':>5} {'r_agg':>8} {'<g_ex>':>8}")
    for name, r_fiber in REGIMES.items():
        r_agg = r_fiber * N_FIBERS_PER_GC
        g = g_ex_steady_state(r_agg)
        print(f"  {name:>30} {r_fiber:>6.0f} Hz {N_FIBERS_PER_GC:>5} {r_agg:>6.0f} Hz {g:>6.1f} mV")
    print("  → single_neuron używa 10 Hz/fiber, pozostałe 15 Hz/fiber. Do ujednolicenia.\n")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURA
# ══════════════════════════════════════════════════════════════════════════════

def make_figure(rates_in, out_mean, out_std, G_crit):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Lewy panel: g_ex(r_agg) vs G_crit
    rr = np.linspace(0, 1050, 200)
    gg = g_ex_steady_state(rr)
    ax1.plot(rr, gg, color='steelblue', lw=2, label='<g_ex> = r·W·τ')
    ax1.axhline(G_crit, color='crimson', ls='--', lw=1.5,
                label=f'G_crit ≈ {G_crit:.0f} mV (K={K_TONIC_GC})')
    ax1.axvline(600, color='gray', ls=':', lw=1.2, label='obecny „aktywny" = 600 Hz')
    ax1.axvline(40,  color='lightgray', ls=':', lw=1.2, label='obecne tło = 40 Hz')
    ax1.fill_between(rr, 0, G_crit, color='green', alpha=0.06)
    ax1.fill_between(rr, G_crit, gg.max(), color='red', alpha=0.06)
    ax1.set(xlabel='Aggregate input rate r_agg [Hz]', ylabel='<g_ex> [mV]',
            title='B) Stan ustalony pobudzenia vs próg bifurkacji\n'
                  'zielone = fluktuacyjny, czerwone = mean-driven')
    ax1.legend(fontsize=8, loc='upper left')
    ax1.spines[['top', 'right']].set_visible(False)

    # Prawy panel: empiryczny output GC
    ax2.errorbar(rates_in, out_mean, yerr=out_std, fmt='o-', color='darkorange',
                 lw=2, ms=7, capsize=3, label='zmierzony output GC')
    ax2.axhspan(1, 10, color='green', alpha=0.10, label='cel DG: 1–10 Hz (aktywne)')
    ax2.axhline(25, color='crimson', ls='--', lw=1.2, label='25 Hz (za szybko)')
    ax2.axvline(600, color='gray', ls=':', lw=1.2, label='obecny „aktywny" = 600 Hz')
    ax2.set(xlabel='Aggregate input rate r_agg [Hz]', ylabel='Output GC firing rate [Hz]',
            title='C) Empiryczny output prawdziwego neuronu GC\n'
                  '(Izhikevich, parametry module3)')
    ax2.legend(fontsize=8, loc='upper left')
    ax2.spines[['top', 'right']].set_visible(False)

    fig.suptitle('Audyt częstotliwości DG — czy 600 Hz aggregate jest za dużo?',
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = __file__.replace('.py', '.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Zapisano figurę: {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("\n" + "=" * 74)
    print(" AUDYT CZĘSTOTLIWOŚCI SYGNAŁU W SIECI DG  (Priorytet 1 / krok 1)")
    print("=" * 74 + "\n")

    rng = np.random.default_rng(42)

    audit_superposition(rng)
    G_crit = audit_steady_state()
    rates_in, out_mean, out_std = audit_io_curve(rng)
    audit_cross_model()
    make_figure(rates_in, out_mean, out_std, G_crit)

    print("\n" + "=" * 74)
    print(" KONIEC AUDYTU — patrz freq_audit.png oraz tabele powyżej")
    print("=" * 74)
