"""
single_neuron_patsep.py — Minimalna symulacja pattern separation.

Model biologiczny:
  - Jeden neuron Leaky-Integrate-and-Fire (LIF) ≈ granule cell (GC) w DG
  - Wejście: N wzorców Poissona (~10 Hz, 2s) z parami korelacją R_input
  - Wyjście: spike train neuronu dla każdego wzorca
  - Wynik: R_output < R_input  →  pattern separation!

Mechanizm:
  - Próg napięciowy (threshold) działa jak nieliniowość
  - Neurn nie odpala na każdy spike wejściowy (subthreshold dynamics)
  - Okres refrakcji zabrania odpowiedzi zbyt blisko w czasie
  - Fluktuacje Poissona sprawiają, że podobne (ale nie identyczne) wzorce
    dają różne (mniej skorelowane) odpowiedzi

Instalacja:  pip install numpy matplotlib scipy
Uruchomienie: python single_neuron_patsep.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import pearsonr

rng = np.random.default_rng(42)

# ══════════════════════════════════════════════════════════════════════════════
# PARAMETRY SYMULACJI
# ══════════════════════════════════════════════════════════════════════════════

# Czas i kroki całkowania
T   = 2.0     # czas trwania próby [s]
dt  = 1e-4    # krok całkowania [s]  (0.1 ms)
n_t = int(T / dt)
t   = np.arange(n_t) * dt   # oś czasu [s]

# Parametry eksperymentu (jak w artykule)
N_PATTERNS = 5     # liczba korelowanych wzorców
R_TARGETS  = [0.25, 0.50, 0.75, 0.90]   # testowane wartości korelacji
R_DEMO     = 0.75  # wartość używana w szczegółowej wizualizacji

# Parametry neuronu LIF (przybliżenie GC)
#   tau_m = 20 ms,  próg = 20 mV powyżej resting
tau_m   = 20e-3   # stała czasowa błony [s]
V_rest  = -70e-3  # potencjał spoczynkowy [V]
V_thr   = -55e-3  # próg akcji [V]   (-55 mV = 15 mV powyżej resting)
                  # 40 niezależnych synaps Poissona 10 Hz daje V_mean≈-58 mV, SD_V≈2.7 mV
                  # → próg jest ~1σ powyżej średniej → FR_out ≈ 8–12 Hz
V_reset = -78e-3  # potencjał po spajku [V]
t_ref   = 3e-3    # bezwzględny okres refrakcji [s]

# Parametry synaptyczne (prąd pobudzający, AMPA-like)
tau_syn = 5e-3    # stała czasowa synaptyczna [s]  (5 ms)
n_syn   = 40      # liczba synaps perforant path → GC
r_input = 10.0    # srednie tempo wejściowe [Hz]
# Waga synaptyczna [V]: każdy spike powoduje skok g_syn o w_syn [V].
# Efektywne napięcie spoczynkowe przy średnim wejściu:
#   g_mean = n_syn × r_input × w_syn × tau_syn
# Chcemy g_mean ≈ 12 mV (próg jest 20 mV powyżej), by neurn strzelał
# sporadycznie od fluktuacji:
#   w_syn = 0.012 / (40 × 10 × 0.005) = 6e-3 V
W_SYN = 6e-3   # [V] — dostrajaj tu jeśli firing rate wyjścia jest za wysoki/niski

# Parametr binowania korelacji (jak w artykule: τ_w = 10 ms)
BIN_MS = 10.0   # [ms]


# ══════════════════════════════════════════════════════════════════════════════
# GENEROWANIE KORELOWANYCH WZORCÓW POISSONA
# ══════════════════════════════════════════════════════════════════════════════

def make_patterns(N: int, r: float, R: float, n_syn: int,
                  T: float, dt: float, rng) -> list:
    """
    Generuje N wzorców wejściowych jako tablice (n_syn, n_steps) bool.

    Metoda "common + private":
      - Każda synapsa ma WSPÓLNY strumień Poissona (rate = R × r) dzielony
        przez wszystkie wzorce → korelacja między wzorcami ≈ R
      - Każdy wzorzec dodaje PRYWATNY strumień (rate = (1-R) × r) →
        różnica między wzorcami

    Korelacja Pearson binowanych spike trainów ≈ R (dla niskich rate).
    """
    n_steps  = int(T / dt)
    r_common  = R * r
    r_private = (1.0 - R) * r

    patterns = [np.zeros((n_syn, n_steps), dtype=bool) for _ in range(N)]

    for s in range(n_syn):
        # Jeden wspólny "szablon" na synapsę — dzielony przez wszystkie wzorce
        common = rng.random(n_steps) < (r_common * dt)
        for k in range(N):
            private = rng.random(n_steps) < (r_private * dt)
            # Sumowanie zdarzeń (OR ≈ unia, poprawne dla niskich rate)
            patterns[k][s] = common | private

    return patterns


# ══════════════════════════════════════════════════════════════════════════════
# SYMULACJA NEURONU LIF
# ══════════════════════════════════════════════════════════════════════════════

def simulate_lif(inputs_2d: np.ndarray) -> tuple:
    """
    Symuluje jeden neuron LIF.

    Równania:
        dg/dt   = -g/tau_syn + sum_spikes × W_SYN   (prąd synaptyczny)
        dV/dt   = (V_rest - V + g) / tau_m           (błona RC)
        jeśli V ≥ V_thr: spike → V = V_reset, refrakcja t_ref

    inputs_2d : (n_syn, n_steps) bool — spajki wejściowe
    Zwraca    : (spikes bool n_steps, V_trace float n_steps)
    """
    V        = V_rest
    g        = 0.0         # synatyczna "siła napędowa" [V]
    ref_left = 0           # pozostałe kroki refrakcji
    spikes   = np.zeros(n_t, dtype=bool)
    V_trace  = np.zeros(n_t)

    for i in range(n_t):
        # Synatyczne wejście: eksponencjalny zanik + impuls od spajków
        g = g * (1.0 - dt / tau_syn) + inputs_2d[:, i].sum() * W_SYN

        if ref_left > 0:
            ref_left -= 1
            V = V_reset
        else:
            dV = (dt / tau_m) * (V_rest - V + g)
            V  = V + dV
            if V >= V_thr:
                spikes[i] = True
                V         = V_reset
                ref_left  = int(t_ref / dt)

        V_trace[i] = V

    return spikes, V_trace


# ══════════════════════════════════════════════════════════════════════════════
# OBLICZANIE KORELACJI
# ══════════════════════════════════════════════════════════════════════════════

def bin_train(spk: np.ndarray, bin_ms: float = BIN_MS) -> np.ndarray:
    """Binuje spike train do wektora zliczeń."""
    bin_size = int(bin_ms * 1e-3 / dt)
    n_bins   = n_t // bin_size
    return spk[:n_bins * bin_size].reshape(n_bins, bin_size).sum(axis=1).astype(float)


def mean_upper_r(mat: np.ndarray) -> float:
    """Średnia elementów ponad główną przekątną macierzy korelacji."""
    idx = np.triu_indices_from(mat, k=1)
    return float(mat[idx].mean())


def mean_pairwise_r(trains: list, bin_ms: float = BIN_MS) -> float:
    """Średnia par Pearson R po wszystkich parach spike trainów."""
    counts = [bin_train(tr, bin_ms) for tr in trains]
    rs = []
    for i in range(len(counts)):
        for j in range(i + 1, len(counts)):
            if counts[i].std() > 0 and counts[j].std() > 0:
                r, _ = pearsonr(counts[i], counts[j])
                if not np.isnan(r):
                    rs.append(r)
    return float(np.mean(rs)) if rs else 0.0


# ══════════════════════════════════════════════════════════════════════════════
# GŁÓWNA PĘTLA — skan po R_TARGETS
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Symulacja LIF neuronu (GC) dla różnych R_input...\n")
    results = []   # lista (R_target, R_in_meas, R_out_meas, out_rates)

    for R_target in R_TARGETS:
        pats = make_patterns(N_PATTERNS, r_input, R_target, n_syn, T, dt, rng)

        # Korelacja wejścia (mierzona z sumy synaps)
        input_trains = [p.sum(axis=0) for p in pats]
        R_in = mean_pairwise_r(input_trains)

        out_spikes = []
        out_rates  = []
        for k in range(N_PATTERNS):
            spk, _ = simulate_lif(pats[k])
            out_spikes.append(spk)
            out_rates.append(spk.sum() / T)

        R_out = mean_pairwise_r(out_spikes)
        results.append((R_target, R_in, R_out, out_rates))

        fr_mean = np.mean(out_rates)
        print(f"  R_target={R_target:.2f}  |  R_in={R_in:.3f}  R_out={R_out:.3f}"
              f"  |  decorr={R_in - R_out:.3f}  |  FR_out={fr_mean:.1f} Hz")

    print()
    if np.mean([r[2] for r in results]) > np.mean([r[1] for r in results]):
        print("  UWAGA: R_out > R_in — zwiększ W_SYN lub zmniejsz próg V_thr")
    elif np.mean([r[3][0] for r in results]) < 0.5:
        print("  UWAGA: firing rate bardzo niski — zwiększ W_SYN")
    else:
        print("  Pattern separation działa: R_out < R_in we wszystkich przypadkach.")


    # ══════════════════════════════════════════════════════════════════════════════
    # SZCZEGÓŁOWA WIZUALIZACJA dla R_DEMO
    # ══════════════════════════════════════════════════════════════════════════════

    pats_demo = make_patterns(N_PATTERNS, r_input, R_DEMO, n_syn, T, dt, rng)
    out_spk_demo = []
    out_vol_demo = []
    for k in range(N_PATTERNS):
        spk, V = simulate_lif(pats_demo[k])
        out_spk_demo.append(spk)
        out_vol_demo.append(V)

    in_trains_demo = [p.sum(axis=0) for p in pats_demo]
    R_in_demo  = mean_pairwise_r(in_trains_demo)
    R_out_demo = mean_pairwise_r(out_spk_demo)

    COLORS = plt.cm.tab10(np.linspace(0, 0.45, N_PATTERNS))
    T_MS   = T * 1000        # czas w milisekundach
    WIN_MS = T_MS            # pełne okno czasowe [ms]
    win_n  = int(WIN_MS * 1e-3 / dt)

    fig = plt.figure(figsize=(16, 14))
    gs  = gridspec.GridSpec(4, 2, figure=fig, hspace=0.55, wspace=0.4,
                            height_ratios=[2, 2, 2.5, 2])

    # ── Panel A: raster wejścia ────────────────────────────────────────────────
    ax_A = fig.add_subplot(gs[0, 0])
    for k, tr in enumerate(in_trains_demo):
        spk_t = t[tr > 0] * 1000
        ax_A.scatter(spk_t, np.full_like(spk_t, k + 1),
                     s=1.5, color=COLORS[k], alpha=0.7, linewidths=0)
    ax_A.set_xlim(0, T_MS)
    ax_A.set_ylim(0.4, N_PATTERNS + 0.6)
    ax_A.set_yticks(range(1, N_PATTERNS + 1))
    ax_A.set_xlabel("Czas (ms)")
    ax_A.set_ylabel("Wzorzec #")
    ax_A.set_title(f"A)  Wzorce WEJŚCIOWE  (R_input = {R_DEMO})\n"
                   f"    zmierzone R_in = {R_in_demo:.3f}", fontsize=10)
    ax_A.spines[["top", "right"]].set_visible(False)

    # ── Panel B: raster wyjścia ────────────────────────────────────────────────
    ax_B = fig.add_subplot(gs[0, 1])
    for k, spk in enumerate(out_spk_demo):
        spk_t = t[spk] * 1000
        ax_B.scatter(spk_t, np.full_like(spk_t, k + 1),
                     s=8, color=COLORS[k], alpha=0.9, linewidths=0)
    ax_B.set_xlim(0, T_MS)
    ax_B.set_ylim(0.4, N_PATTERNS + 0.6)
    ax_B.set_yticks(range(1, N_PATTERNS + 1))
    ax_B.set_xlabel("Czas (ms)")
    ax_B.set_ylabel("Wzorzec #")
    ax_B.set_title(f"B)  Spike trainy WYJŚCIOWE (LIF neuron)\n"
                   f"    zmierzone R_out = {R_out_demo:.3f}  |  "
                   f"dekorelacja = {R_in_demo - R_out_demo:.3f}", fontsize=10)
    ax_B.spines[["top", "right"]].set_visible(False)

    # ── Panel C: napięcie błony — wzorzec 1 i 2 ───────────────────────────────
    ax_C = fig.add_subplot(gs[1, :])
    for k in [0, 1]:
        ax_C.plot(t[:win_n] * 1000, out_vol_demo[k][:win_n] * 1000,
                  lw=0.8, alpha=0.85, color=COLORS[k],
                  label=f"Wzorzec {k + 1}")
    ax_C.axhline(V_thr * 1000, color="k", ls="--", lw=1.0, alpha=0.6,
                 label=f"Próg ({V_thr*1000:.0f} mV)")
    ax_C.axhline(V_rest * 1000, color="gray", ls=":", lw=0.8, alpha=0.4,
                 label=f"V_rest ({V_rest*1000:.0f} mV)")
    ax_C.set_xlim(0, WIN_MS)
    ax_C.set_xlabel("Czas (ms)")
    ax_C.set_ylabel("V (mV)")
    ax_C.set_title(f"C)  Potencjał błony — wzorce 1 & 2 (pełne {WIN_MS:.0f} ms)\n"
                   f"    Mimo R_in = {R_DEMO}, wzorce produkują różne czasy spajków",
                   fontsize=10)
    ax_C.legend(fontsize=8, loc="upper right", ncol=4)
    ax_C.spines[["top", "right"]].set_visible(False)

    # ── Panel D: korelacja pary wejście ─────────────────────────────────────────
    ax_D = fig.add_subplot(gs[2, 0])
    in_counts = [bin_train(tr) for tr in in_trains_demo]
    R_mat_in  = np.eye(N_PATTERNS)
    for i in range(N_PATTERNS):
        for j in range(i + 1, N_PATTERNS):
            if in_counts[i].std() > 0:
                r, _ = pearsonr(in_counts[i], in_counts[j])
                R_mat_in[i, j] = R_mat_in[j, i] = r

    im_D = ax_D.imshow(R_mat_in, vmin=-0.2, vmax=1.0, cmap="RdYlGn", aspect="auto")
    plt.colorbar(im_D, ax=ax_D, label="Pearson R")
    ax_D.set_title(f"D)  Macierz korelacji WEJŚCIA\n    mean = {mean_upper_r(R_mat_in):.3f}",
                   fontsize=10)
    ax_D.set_xlabel("Wzorzec #")
    ax_D.set_ylabel("Wzorzec #")

    # ── Panel E: korelacja wyjścia ───────────────────────────────────────────────
    ax_E = fig.add_subplot(gs[2, 1])
    out_counts = [bin_train(spk) for spk in out_spk_demo]
    R_mat_out  = np.eye(N_PATTERNS)
    for i in range(N_PATTERNS):
        for j in range(i + 1, N_PATTERNS):
            if out_counts[i].std() > 0 and out_counts[j].std() > 0:
                r, _ = pearsonr(out_counts[i], out_counts[j])
                R_mat_out[i, j] = R_mat_out[j, i] = r

    im_E = ax_E.imshow(R_mat_out, vmin=-0.2, vmax=1.0, cmap="RdYlGn", aspect="auto")
    plt.colorbar(im_E, ax=ax_E, label="Pearson R")
    ax_E.set_title(f"E)  Macierz korelacji WYJŚCIA\n    mean = {mean_upper_r(R_mat_out):.3f}",
                   fontsize=10)
    ax_E.set_xlabel("Wzorzec #")
    ax_E.set_ylabel("Wzorzec #")

    # ── Panel F: R_in vs R_out skan ───────────────────────────────────────────────
    ax_F = fig.add_subplot(gs[3, :])
    r_in_arr  = np.array([r[1] for r in results])
    r_out_arr = np.array([r[2] for r in results])

    ax_F.plot([0, 1], [0, 1], "--", color="gray", alpha=0.5, label="brak separacji")
    ax_F.plot(r_in_arr, r_out_arr, "o-", color="steelblue",
              lw=2.5, ms=10, label="LIF neuron (GC model)")
    ax_F.fill_between(r_in_arr, r_out_arr, r_in_arr,
                      alpha=0.15, color="steelblue", label="dekorelacja (↓ R)")
    for ri, ro, rt in zip(r_in_arr, r_out_arr, [r[0] for r in results]):
        ax_F.annotate(f"R={rt}", (ri, ro),
                      textcoords="offset points", xytext=(6, -14), fontsize=8)

    ax_F.set_xlabel("R_input  (korelacja wzorców wejściowych Poissona)", fontsize=9)
    ax_F.set_ylabel("R_output  (korelacja spike trainów wyjściowych)", fontsize=9)
    ax_F.set_title("F)  Pattern Separation: LIF neuron dekoreluje podobne wzorce wejściowe\n"
                   f"    (N={N_PATTERNS} wzorców, r_input={r_input} Hz, τ_syn={tau_syn*1000:.0f} ms,"
                   f" n_syn={n_syn}, W_syn={W_SYN*1000:.1f} mV)",
                   fontsize=10)
    ax_F.set_xlim(-0.05, 1.1)
    ax_F.set_ylim(-0.2, 1.1)
    ax_F.legend(fontsize=8, loc="upper left")
    ax_F.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Jeden neuron LIF jako model Granule Cell — Pattern Separation w DG",
                 fontsize=13, fontweight="bold")

    out_path = __file__.replace(".py", ".png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Zapisano: {out_path}")
    plt.show()
