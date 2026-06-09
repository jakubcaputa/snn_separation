"""
separation_parameters_sweep/parameter_sweep.py

Sweeps each neuron and synapse parameter of the LIF granule-cell model and
measures its impact on pattern separation (decorrelation of output spike trains).

Imports core functions from single_neuron_patsep.py:
  - make_patterns  : generate N correlated Poisson input patterns
  - bin_train      : bin a spike train into spike-count bins
  - mean_pairwise_r: mean pairwise Pearson R across a list of spike trains

A parameterised LIF simulator is defined here so every parameter can be
varied independently while keeping the rest at their default values.

Outputs (saved in this directory):
  parameter_sweep_neuron.png  — tau_m, V_thr, t_ref, V_reset
  parameter_sweep_synapse.png — tau_syn, n_syn, W_SYN, r_input
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from single_neuron_patsep import make_patterns, bin_train, mean_pairwise_r

# ── Simulation constants (must match single_neuron_patsep.py) ─────────────────
T   = 2.0
dt  = 1e-4
n_t = int(T / dt)

# ── Baseline parameters ───────────────────────────────────────────────────────
DEFAULT = dict(
    tau_m   = 20e-3,    # membrane time constant [s]
    V_rest  = -70e-3,   # resting potential [V]
    V_thr   = -55e-3,   # spike threshold [V]
    V_reset = -78e-3,   # reset potential after spike [V]
    t_ref   = 3e-3,     # absolute refractory period [s]
    tau_syn = 5e-3,     # synaptic time constant [s]
    n_syn   = 40,       # number of perforant-path synapses
    r_input = 10.0,     # mean input firing rate [Hz]
    W_SYN   = 6e-3,     # synaptic weight [V]
)

# ── Parameter sweep definitions ───────────────────────────────────────────────
# fmt: (display_label, display_unit, SI_values_array)
#
# NEURON parameters — intrinsic membrane/spike properties
NEURON_SWEEPS = {
    # tau_m: 2–120 ms; finer steps in the 5–40 ms physiological range
    "tau_m": (
        "Membrane tau_m", "ms",
        np.array([2, 4, 6, 8, 10, 12.5, 15, 17.5, 20, 25, 30,
                  40, 55, 80, 120]) * 1e-3,
    ),
    # V_thr: -68 to -42 mV (2–28 mV above rest=-70 mV), 2 mV steps
    "V_thr": (
        "Threshold V_thr", "mV",
        np.arange(-68, -41, 2) * 1e-3,
    ),
    # t_ref: 0.25–22 ms; sub-ms resolution near zero, coarser at long values
    "t_ref": (
        "Refractory t_ref", "ms",
        np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0,
                  5.0, 6.5, 8.0, 10.0, 13.0, 17.0, 22.0]) * 1e-3,
    ),
    # V_reset: -95 to -57 mV (just below V_thr=-55 mV), 2 mV steps
    # As V_reset → V_thr the neuron fires at max rate (only t_ref limits it)
    "V_reset": (
        "Reset V_reset", "mV",
        np.arange(-95, -55, 2) * 1e-3,
    ),
}

# SYNAPSE parameters — input drive and connectivity
SYNAPSE_SWEEPS = {
    # tau_syn: 0.25–50 ms; fine below 5 ms (AMPA-like), coarser for NMDA range
    "tau_syn": (
        "Synaptic tau_syn", "ms",
        np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.0,
                  10.0, 14.0, 19.0, 26.0, 35.0, 50.0]) * 1e-3,
    ),
    # n_syn: 2–200; fine at low counts where threshold non-linearity bites
    "n_syn": (
        "No. synapses n_syn", "",
        np.array([2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50,
                  65, 80, 100, 130, 160, 200], dtype=float),
    ),
    # W_SYN: 0.25–20 mV; 0.25–1 mV sub-threshold regime, 1–20 mV supra
    "W_SYN": (
        "Synaptic weight", "mV",
        np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0,
                  7.0, 8.0, 10.0, 12.0, 15.0, 20.0]) * 1e-3,
    ),
    # r_input: 0.5–75 Hz; fine at low rates (Poisson variability dominant)
    "r_input": (
        "Input rate r_in", "Hz",
        np.array([0.5, 1, 2, 3, 4, 5, 7, 10, 13, 17,
                  22, 28, 35, 45, 60, 75], dtype=float),
    ),
}

# R_input levels tested for each parameter (three curves per panel)
R_INPUT_LEVELS = [0.50, 0.75, 0.90]
R_COLORS       = ["#4575b4", "#d73027", "#1a9850"]

SEEDS      = [42, 43, 44, 45, 46]
N_PATTERNS = 5

# Reliable FR window: below FR_MIN too few spikes for stable Pearson R;
# above FR_MAX the neuron saturates and R_out → R_in regardless of params.
FR_MIN = 5.0    # Hz
FR_MAX = 80.0   # Hz


# ── Parameterised LIF neuron ──────────────────────────────────────────────────

def simulate_lif_params(inputs_2d: np.ndarray, p: dict) -> np.ndarray:
    """LIF simulation with explicit parameter dict; returns bool spike array."""
    V        = p["V_rest"]
    g        = 0.0
    ref_left = 0
    spikes   = np.zeros(n_t, dtype=bool)
    decay    = 1.0 - dt / p["tau_syn"]
    leak     = dt  / p["tau_m"]

    for i in range(n_t):
        g = g * decay + inputs_2d[:, i].sum() * p["W_SYN"]
        if ref_left > 0:
            ref_left -= 1
            V = p["V_reset"]
        else:
            V += leak * (p["V_rest"] - V + g)
            if V >= p["V_thr"]:
                spikes[i] = True
                V         = p["V_reset"]
                ref_left  = int(p["t_ref"] / dt)
    return spikes


# ── Single experiment ─────────────────────────────────────────────────────────

def run_experiment(params: dict, R_input: float, seed: int) -> tuple:
    """Returns (decorrelation, mean_FR, R_in, R_out)."""
    rng = np.random.default_rng(seed)
    pats = make_patterns(N_PATTERNS, params["r_input"], R_input,
                         int(params["n_syn"]), T, dt, rng)

    input_trains = [pat.sum(axis=0) for pat in pats]
    R_in = mean_pairwise_r(input_trains)

    out_spikes, frs = [], []
    for pat in pats:
        spk = simulate_lif_params(pat, params)
        out_spikes.append(spk)
        frs.append(spk.sum() / T)

    R_out = mean_pairwise_r(out_spikes)
    return R_in - R_out, float(np.mean(frs)), R_in, R_out


# ── Parameter sweep ───────────────────────────────────────────────────────────

def sweep_parameter(param_name: str, values: np.ndarray, R_input: float) -> tuple:
    """Returns (dec_mean, dec_std, fr_mean, fr_std, rout_mean, rout_std)."""
    n_val  = len(values)
    n_seed = len(SEEDS)
    dec  = np.zeros((n_val, n_seed))
    fr   = np.zeros((n_val, n_seed))
    rout = np.zeros((n_val, n_seed))

    for vi, val in enumerate(values):
        for si, seed in enumerate(SEEDS):
            params = {**DEFAULT, param_name: val}
            d, f, _, r_out = run_experiment(params, R_input=R_input, seed=seed)
            dec[vi, si]  = d
            fr[vi, si]   = f
            rout[vi, si] = r_out

    return (dec.mean(1),  dec.std(1),
            fr.mean(1),   fr.std(1),
            rout.mean(1), rout.std(1))


# ── Run all sweeps ────────────────────────────────────────────────────────────

def run_all_sweeps(sweeps_dict: dict, group_name: str) -> dict:
    results = {}
    print(f"\n{'='*60}")
    print(f"  {group_name} parameters")
    print(f"{'='*60}")
    for pname, (label, unit, values) in sweeps_dict.items():
        results[pname] = {}
        for R_input in R_INPUT_LEVELS:
            tag = label.encode("ascii", "replace").decode()
            print(f"  {tag:30s}  R_in={R_input:.2f}  "
                  f"({len(values)} vals x {len(SEEDS)} seeds)",
                  end="", flush=True)
            dec_m, dec_s, fr_m, fr_s, rout_m, rout_s = sweep_parameter(pname, values, R_input)
            results[pname][R_input] = dict(
                label=label, unit=unit, values=values,
                dec_m=dec_m,   dec_s=dec_s,
                fr_m=fr_m,     fr_s=fr_s,
                rout_m=rout_m, rout_s=rout_s,
            )
            print("  done")
    return results


print("Running parameter sweep — this may take a few minutes...\n")
neuron_results  = run_all_sweeps(NEURON_SWEEPS,  "NEURON")
synapse_results = run_all_sweeps(SYNAPSE_SWEEPS, "SYNAPSE")
print("\nAll sweeps complete.")


# ── Plotting helper ───────────────────────────────────────────────────────────

def plot_group(sweeps_dict: dict, results: dict,
               group_title: str, out_path: str,
               metric: str = "dec",
               fr_filter: bool = False) -> None:
    """
    Render a 2x2 figure for one parameter group and save it.

    metric    : "dec"  → y = R_in − R_out  (pattern separation index)
                "rout" → y = R_out          (raw output correlation)
    fr_filter : if True, mask data points where per-curve FR is outside
                [FR_MIN, FR_MAX] — only reliable estimates are drawn.
                The FR secondary axis shows threshold bands.
    """
    assert metric in ("dec", "rout")

    keys   = list(sweeps_dict.keys())
    n_keys = len(keys)
    n_cols = 2
    n_rows = (n_keys + 1) // n_cols

    fig = plt.figure(figsize=(14, n_rows * 4.8))
    gs  = gridspec.GridSpec(n_rows, n_cols, figure=fig,
                            hspace=0.72, wspace=0.50)
    axes = [fig.add_subplot(gs[r, c])
            for r in range(n_rows) for c in range(n_cols)]

    for ax_idx, pname in enumerate(keys):
        ax   = axes[ax_idx]
        label, unit, values = sweeps_dict[pname]

        if unit in ("ms", "mV"):
            x_disp    = values * 1e3
            x_default = DEFAULT[pname] * 1e3
            x_label   = f"{label} ({unit})"
        else:
            x_disp    = values
            x_default = DEFAULT[pname]
            x_label   = f"{label}" + (f" ({unit})" if unit else "")

        ax2 = ax.twinx()

        for R_input, color in zip(R_INPUT_LEVELS, R_COLORS):
            res        = results[pname][R_input]
            fr_m, fr_s = res["fr_m"], res["fr_s"]

            if metric == "dec":
                y_m, y_s = res["dec_m"], res["dec_s"]
            else:
                y_m, y_s = res["rout_m"], res["rout_s"]

            # compute valid mask once; when fr_filter=False all points are kept
            if fr_filter:
                valid = (fr_m >= FR_MIN) & (fr_m <= FR_MAX)
            else:
                valid = np.ones(len(fr_m), dtype=bool)

            x_plot = x_disp[valid]
            y_m    = y_m[valid]
            y_s    = y_s[valid]

            ax.fill_between(x_plot, y_m - y_s, y_m + y_s,
                            alpha=0.14, color=color)
            ax.plot(x_plot, y_m, "o-", color=color, lw=2, ms=4.5,
                    label=f"R_in={R_input:.2f}")

            if metric == "rout":
                ax.axhline(R_input, color=color, ls="--", lw=0.9, alpha=0.45)

            if R_input == 0.75:
                # FR line uses the same valid mask so it never extends the x-axis
                # beyond where the decorrelation curves have data
                ax2.plot(x_plot, fr_m[valid], "s--", color="#888888",
                         lw=1.2, ms=4, alpha=0.70, label="FR @ R=0.75")
                ax2.fill_between(x_plot,
                                 (fr_m - fr_s)[valid], (fr_m + fr_s)[valid],
                                 alpha=0.08, color="#888888")

                # shade unreliable FR zones on the secondary axis
                if fr_filter:
                    fr_max_plot = max(fr_m.max() * 1.15, FR_MAX * 1.2)
                    ax2.axhspan(0,          FR_MIN,      color="#e08020",
                                alpha=0.18, zorder=0)
                    ax2.axhspan(FR_MAX, fr_max_plot,     color="#e08020",
                                alpha=0.18, zorder=0)
                    ax2.axhline(FR_MIN, color="#e08020", ls="--",
                                lw=1.0, alpha=0.80, label=f"FR_min={FR_MIN:.0f} Hz")
                    ax2.axhline(FR_MAX, color="#e08020", ls="--",
                                lw=1.0, alpha=0.80, label=f"FR_max={FR_MAX:.0f} Hz")
                    ax2.set_ylim(0, fr_max_plot)

        ax.axvline(x_default, color="black", ls=":", lw=1.3,
                   alpha=0.60, label="Default")

        if metric == "dec":
            ax.axhline(0, color="black", ls="-", lw=0.6, alpha=0.20)
            ax.set_ylabel("Pattern Separation Index  (R_in − R_out)", fontsize=8)
        else:
            ax.set_ylabel("Output correlation  R_out", fontsize=8)
            ax.set_ylim(-0.05, 1.05)

        ax.set_xlabel(x_label, fontsize=9)
        ax2.set_ylabel("Mean FR (Hz)", fontsize=7, color="#888888")
        ax2.tick_params(axis="y", labelcolor="#888888", labelsize=7)
        ax.tick_params(axis="both", labelsize=8)
        ax.spines["top"].set_visible(False)
        ax2.spines["top"].set_visible(False)
        ax.set_title(label, fontsize=10, fontweight="bold", pad=7)

        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="best",
                  framealpha=0.75, handlelength=1.5)

    for ax in axes[n_keys:]:
        ax.set_visible(False)

    defaults_str = (
        f"tau_m={DEFAULT['tau_m']*1e3:.0f}ms  "
        f"V_thr={DEFAULT['V_thr']*1e3:.0f}mV  "
        f"t_ref={DEFAULT['t_ref']*1e3:.0f}ms  "
        f"V_reset={DEFAULT['V_reset']*1e3:.0f}mV  |  "
        f"tau_syn={DEFAULT['tau_syn']*1e3:.0f}ms  "
        f"n_syn={int(DEFAULT['n_syn'])}  "
        f"W_syn={DEFAULT['W_SYN']*1e3:.0f}mV  "
        f"r_in={DEFAULT['r_input']:.0f}Hz"
    )
    metric_label = "Pattern Separation Index" if metric == "dec" else "Output Correlation R_out"
    filter_label = f"  |  valid FR only: {FR_MIN:.0f}–{FR_MAX:.0f} Hz" if fr_filter else ""
    fig.suptitle(
        f"LIF Granule-Cell — {group_title} Parameters  [{metric_label}{filter_label}]\n"
        f"Baseline: {defaults_str}",
        fontsize=10, fontweight="bold", y=1.01,
    )

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.show()


# ── Generate and save figures ─────────────────────────────────────────────────

out_dir = os.path.dirname(os.path.abspath(__file__))

# All data points (no FR filter)
plot_group(NEURON_SWEEPS,  neuron_results,  "Neuron",  metric="dec",
           out_path=os.path.join(out_dir, "parameter_sweep_neuron.png"))

plot_group(SYNAPSE_SWEEPS, synapse_results, "Synapse", metric="dec",
           out_path=os.path.join(out_dir, "parameter_sweep_synapse.png"))

plot_group(NEURON_SWEEPS,  neuron_results,  "Neuron",  metric="rout",
           out_path=os.path.join(out_dir, "parameter_sweep_neuron_rout.png"))

plot_group(SYNAPSE_SWEEPS, synapse_results, "Synapse", metric="rout",
           out_path=os.path.join(out_dir, "parameter_sweep_synapse_rout.png"))

# Valid FR range only (FR_MIN–FR_MAX Hz) — reliable estimates
plot_group(NEURON_SWEEPS,  neuron_results,  "Neuron",  metric="dec",
           fr_filter=True,
           out_path=os.path.join(out_dir, "parameter_sweep_neuron_valid.png"))

plot_group(SYNAPSE_SWEEPS, synapse_results, "Synapse", metric="dec",
           fr_filter=True,
           out_path=os.path.join(out_dir, "parameter_sweep_synapse_valid.png"))
