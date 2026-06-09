"""
separation_parameters_sweep/heatmap_2d.py

2D parameter interaction heatmaps for the LIF granule-cell model.

For each parameter pair, every (x, y) grid point is simulated and pattern
separation (decorrelation R_in − R_out) is shown as colour.
White contour lines overlay mean output FR (Hz), revealing the iso-drive
structure and the reliable operating window.

Pairs analysed:
  1. W_SYN  x  V_thr   — weight vs threshold
  2. n_syn  x  W_SYN   — connectivity vs weight (iso-drive hyperbolas)
  3. tau_m  x  tau_syn  — membrane vs synaptic time constant
  4. t_ref  x  V_reset  — refractory period vs reset potential

Output: separation_parameters_sweep/heatmap_2d.png
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import TwoSlopeNorm

from single_neuron_patsep import make_patterns, mean_pairwise_r

# ── Simulation constants ──────────────────────────────────────────────────────
T   = 2.0
dt  = 1e-4
n_t = int(T / dt)

# ── Default parameters ────────────────────────────────────────────────────────
DEFAULT = dict(
    tau_m   = 20e-3,
    V_rest  = -70e-3,
    V_thr   = -55e-3,
    V_reset = -78e-3,
    t_ref   = 3e-3,
    tau_syn = 5e-3,
    n_syn   = 40,
    r_input = 10.0,
    W_SYN   = 6e-3,
)

# ── 2D sweep pair definitions ─────────────────────────────────────────────────
# x_unit / y_unit: multiply SI value by this to get display value
PAIRS = [
    dict(
        px="W_SYN", py="V_thr",
        x_vals = np.array([0.5, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15]) * 1e-3,
        y_vals = np.array([-66, -64, -62, -60, -58, -56, -54, -52, -50, -48, -46]) * 1e-3,
        x_label="Synaptic weight  W_SYN (mV)",
        y_label="Threshold  V_thr (mV)",
        x_unit=1e3, y_unit=1e3,
        title="W_SYN  ×  V_thr",
    ),
    dict(
        px="n_syn", py="W_SYN",
        x_vals = np.array([5, 10, 15, 20, 25, 30, 40, 50, 65, 80, 100, 130], dtype=float),
        y_vals = np.array([0.5, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15]) * 1e-3,
        x_label="No. synapses  n_syn",
        y_label="Synaptic weight  W_SYN (mV)",
        x_unit=1.0, y_unit=1e3,
        title="n_syn  ×  W_SYN",
    ),
    dict(
        px="tau_m", py="tau_syn",
        x_vals = np.array([4, 6, 8, 10, 13, 17, 20, 25, 32, 42, 55, 75]) * 1e-3,
        y_vals = np.array([0.5, 1, 2, 3, 5, 7, 10, 14, 19, 26, 35]) * 1e-3,
        x_label="Membrane time constant  tau_m (ms)",
        y_label="Synaptic time constant  tau_syn (ms)",
        x_unit=1e3, y_unit=1e3,
        title="tau_m  ×  tau_syn",
    ),
    dict(
        px="t_ref", py="V_reset",
        x_vals = np.array([0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6.5, 8, 10, 14]) * 1e-3,
        y_vals = np.array([-92, -89, -86, -83, -80, -78, -76, -74, -72, -70, -68]) * 1e-3,
        x_label="Refractory period  t_ref (ms)",
        y_label="Reset potential  V_reset (mV)",
        x_unit=1e3, y_unit=1e3,
        title="t_ref  ×  V_reset",
    ),
]

R_INPUT            = 0.75
SEEDS              = [42, 43, 44, 45]
N_PATTERNS         = 5
FR_CONTOUR_LEVELS  = [5, 15, 30, 60, 100]   # Hz iso-lines on each heatmap


# ── Parameterised LIF neuron ──────────────────────────────────────────────────

def simulate_lif_params(inputs_2d: np.ndarray, p: dict) -> np.ndarray:
    V = p["V_rest"];  g = 0.0;  ref_left = 0
    spikes = np.zeros(n_t, dtype=bool)
    decay  = 1.0 - dt / p["tau_syn"]
    leak   = dt  / p["tau_m"]
    for i in range(n_t):
        g = g * decay + inputs_2d[:, i].sum() * p["W_SYN"]
        if ref_left > 0:
            ref_left -= 1;  V = p["V_reset"]
        else:
            V += leak * (p["V_rest"] - V + g)
            if V >= p["V_thr"]:
                spikes[i] = True;  V = p["V_reset"]
                ref_left = int(p["t_ref"] / dt)
    return spikes


def run_experiment(params: dict, seed: int) -> tuple:
    """Returns (decorrelation, mean_FR)."""
    rng  = np.random.default_rng(seed)
    pats = make_patterns(N_PATTERNS, params["r_input"], R_INPUT,
                         int(params["n_syn"]), T, dt, rng)
    input_trains = [pat.sum(axis=0) for pat in pats]
    R_in = mean_pairwise_r(input_trains)
    out_spikes, frs = [], []
    for pat in pats:
        spk = simulate_lif_params(pat, params)
        out_spikes.append(spk)
        frs.append(spk.sum() / T)
    R_out = mean_pairwise_r(out_spikes)
    return R_in - R_out, float(np.mean(frs))


# ── 2D grid sweep ─────────────────────────────────────────────────────────────

def sweep_2d(pair: dict) -> tuple:
    """
    Returns (dec_grid, fr_grid) each of shape (len(y_vals), len(x_vals)),
    averaged over SEEDS.
    """
    x_vals, y_vals = pair["x_vals"], pair["y_vals"]
    nx, ny = len(x_vals), len(y_vals)
    dec = np.zeros((ny, nx, len(SEEDS)))
    fr  = np.zeros((ny, nx, len(SEEDS)))

    for xi, xv in enumerate(x_vals):
        for yi, yv in enumerate(y_vals):
            for si, seed in enumerate(SEEDS):
                params = {**DEFAULT, pair["px"]: xv, pair["py"]: yv}
                d, f = run_experiment(params, seed)
                dec[yi, xi, si] = d
                fr[yi, xi, si]  = f

    return dec.mean(-1), fr.mean(-1)


# ── Run all pairs ─────────────────────────────────────────────────────────────

print(f"Running 2D sweeps  (R_in={R_INPUT}, {len(SEEDS)} seeds)\n")

pair_results = []
for pair in PAIRS:
    n_sims = len(pair["x_vals"]) * len(pair["y_vals"]) * len(SEEDS)
    print(f"  {pair['title']:22s}  "
          f"{len(pair['x_vals'])} x {len(pair['y_vals'])} grid  "
          f"x {len(SEEDS)} seeds  =  {n_sims} sims ...",
          end="", flush=True)
    dec_grid, fr_grid = sweep_2d(pair)
    pair_results.append((dec_grid, fr_grid))
    print("  done")

print("\nAll sweeps complete.\n")


# ── Visualisation ─────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(15, 12))
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.50, wspace=0.42)

# diverging norm: red = convergence, white/yellow = no change, green = separation
NORM = TwoSlopeNorm(vmin=-0.2, vcenter=0.0, vmax=0.7)
CMAP = "RdYlGn"

for idx, (pair, (dec_grid, fr_grid)) in enumerate(zip(PAIRS, pair_results)):
    ax = fig.add_subplot(gs[idx // 2, idx % 2])

    x_disp = pair["x_vals"] * pair["x_unit"]
    y_disp = pair["y_vals"] * pair["y_unit"]

    # ── heatmap ──────────────────────────────────────────────────────────────
    im = ax.pcolormesh(x_disp, y_disp, dec_grid,
                       cmap=CMAP, norm=NORM, shading="nearest")
    cbar = plt.colorbar(im, ax=ax, pad=0.02, fraction=0.046)
    cbar.set_label("Decorrelation  (R_in − R_out)", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    # ── FR iso-contours ───────────────────────────────────────────────────────
    cs = ax.contour(x_disp, y_disp, fr_grid,
                    levels=FR_CONTOUR_LEVELS,
                    colors="white", linewidths=[0.8, 1.0, 1.1, 1.2, 1.3],
                    alpha=0.80,
                    linestyles=[":", "--", "-.", "-", (0, (3, 1, 1, 1))])
    ax.clabel(cs, fmt="%g Hz", fontsize=7, inline=True,
              use_clabeltext=True)

    # ── default value marker ──────────────────────────────────────────────────
    x_def = DEFAULT[pair["px"]] * pair["x_unit"]
    y_def = DEFAULT[pair["py"]] * pair["y_unit"]
    ax.plot(x_def, y_def, "*", color="white", ms=14,
            mec="black", mew=0.8, zorder=6, label="Default")

    ax.set_xlabel(pair["x_label"], fontsize=9)
    ax.set_ylabel(pair["y_label"], fontsize=9)
    ax.set_title(pair["title"], fontsize=11, fontweight="bold", pad=8)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=7, loc="upper left", framealpha=0.65)

fig.suptitle(
    f"2D Parameter Interaction — Pattern Separation  (R_in = {R_INPUT})\n"
    "Colour: decorrelation (R_in − R_out)     "
    "White contours: mean output FR (Hz)     "
    "★: default values",
    fontsize=11, fontweight="bold", y=1.02,
)

out_dir  = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, "heatmap_2d.png")
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path}")
plt.show()
