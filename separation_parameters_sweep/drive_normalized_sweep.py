"""
separation_parameters_sweep/drive_normalized_sweep.py

Drive-normalized parameter sweep for the LIF granule-cell model.

For each parameter value, W_SYN is found via bisection so that the neuron
fires at FR_TARGET = 10 Hz on average.  The decorrelation measured at that
normalized drive is compared to the "raw" decorrelation at default W_SYN.

This isolates the *pure* effect of each parameter from the FR confound:
if a parameter changes decorrelation only because it changes FR, the
normalized curve will be flat; if it has an intrinsic effect the curves
will diverge.

Parameters swept  (W_SYN excluded — it is the normalization knob):
  tau_m, V_thr, t_ref, tau_syn, n_syn, r_input

Output: separation_parameters_sweep/drive_normalized_sweep.png
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

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

# ── Experiment constants ──────────────────────────────────────────────────────
FR_TARGET      = 10.0         # Hz — target mean FR for normalization
BISECT_TOL     = 0.5          # Hz — stop bisection when |FR - target| < tol
BISECT_SEEDS   = [42, 43, 44] # seeds used to estimate FR during bisection
W_MIN          = 0.1e-3       # V — lower bound for bisection
W_MAX          = 40e-3        # V — upper bound

R_INPUT        = 0.75
SEEDS          = [42, 43, 44, 45, 46]
N_PATTERNS     = 5

# ── Parameters to sweep ───────────────────────────────────────────────────────
SWEEPS = {
    "tau_m": dict(
        label   = "Membrane  tau_m (ms)",
        vals    = np.array([4, 6, 8, 10, 12.5, 15, 17.5, 20, 25, 30, 40, 55, 80]) * 1e-3,
        unit    = 1e3,
        default = DEFAULT["tau_m"],
    ),
    "V_thr": dict(
        label   = "Threshold  V_thr (mV)",
        vals    = np.arange(-68, -41, 2) * 1e-3,
        unit    = 1e3,
        default = DEFAULT["V_thr"],
    ),
    "t_ref": dict(
        label   = "Refractory  t_ref (ms)",
        vals    = np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.5, 8.0, 10.0, 13.0]) * 1e-3,
        unit    = 1e3,
        default = DEFAULT["t_ref"],
    ),
    "tau_syn": dict(
        label   = "Synaptic  tau_syn (ms)",
        vals    = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 14.0, 19.0, 26.0, 35.0]) * 1e-3,
        unit    = 1e3,
        default = DEFAULT["tau_syn"],
    ),
    "n_syn": dict(
        label   = "No. synapses  n_syn",
        vals    = np.array([4, 6, 8, 10, 15, 20, 25, 30, 40, 50, 65, 80, 100, 130], dtype=float),
        unit    = 1.0,
        default = float(DEFAULT["n_syn"]),
    ),
    "r_input": dict(
        label   = "Input rate  r_input (Hz)",
        vals    = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 13.0, 17.0, 22.0, 28.0, 35.0, 45.0]),
        unit    = 1.0,
        default = DEFAULT["r_input"],
    ),
}


# ── Parameterised LIF neuron ──────────────────────────────────────────────────

def simulate_lif(inputs_2d: np.ndarray, p: dict) -> np.ndarray:
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


def mean_fr(params: dict, seeds: list) -> float:
    """Estimate mean output FR (Hz) over multiple seeds."""
    frs = []
    for seed in seeds:
        rng  = np.random.default_rng(seed)
        pats = make_patterns(N_PATTERNS, params["r_input"], R_INPUT,
                             int(params["n_syn"]), T, dt, rng)
        for pat in pats:
            spk = simulate_lif(pat, params)
            frs.append(spk.sum() / T)
    return float(np.mean(frs))


def find_normalized_wsyn(params_base: dict) -> float | None:
    """
    Bisect W_SYN to hit FR_TARGET.
    Returns W_SYN (V) or None if the target is unreachable in [W_MIN, W_MAX].
    """
    p_lo = {**params_base, "W_SYN": W_MIN}
    p_hi = {**params_base, "W_SYN": W_MAX}
    fr_lo = mean_fr(p_lo, BISECT_SEEDS)
    fr_hi = mean_fr(p_hi, BISECT_SEEDS)

    if fr_lo > FR_TARGET or fr_hi < FR_TARGET:
        return None  # target not bracketed

    w_lo, w_hi = W_MIN, W_MAX
    for _ in range(20):               # max ~20 iterations → <1 ms precision
        w_mid = (w_lo + w_hi) / 2
        fr_mid = mean_fr({**params_base, "W_SYN": w_mid}, BISECT_SEEDS)
        if abs(fr_mid - FR_TARGET) < BISECT_TOL:
            return w_mid
        if fr_mid < FR_TARGET:
            w_lo = w_mid
        else:
            w_hi = w_mid
    return (w_lo + w_hi) / 2


def run_experiment(params: dict, seed: int) -> tuple:
    """Returns (decorrelation, mean_FR)."""
    rng  = np.random.default_rng(seed)
    pats = make_patterns(N_PATTERNS, params["r_input"], R_INPUT,
                         int(params["n_syn"]), T, dt, rng)
    out_spikes, frs = [], []
    for pat in pats:
        spk = simulate_lif(pat, params)
        out_spikes.append(spk)
        frs.append(spk.sum() / T)
    R_in  = mean_pairwise_r([pat.sum(axis=0) for pat in pats])
    R_out = mean_pairwise_r(out_spikes)
    return R_in - R_out, float(np.mean(frs))


# ── Run sweeps ────────────────────────────────────────────────────────────────

print(f"Drive-normalized sweep  (FR_target={FR_TARGET} Hz, R_in={R_INPUT})\n")

results = {}  # param_name -> dict with arrays

for pname, spec in SWEEPS.items():
    vals   = spec["vals"]
    n_vals = len(vals)

    dec_raw = np.zeros((n_vals, len(SEEDS)))
    fr_raw  = np.zeros((n_vals, len(SEEDS)))
    dec_nrm = np.full((n_vals, len(SEEDS)), np.nan)
    fr_nrm  = np.full((n_vals, len(SEEDS)), np.nan)
    w_nrm   = np.full(n_vals, np.nan)   # W_SYN found per value

    label_safe = spec["label"].encode("ascii", "replace").decode()
    print(f"  {label_safe}")

    for vi, val in enumerate(vals):
        params_base = {**DEFAULT, pname: val}

        # ── raw (default W_SYN) ────────────────────────────────────────────
        for si, seed in enumerate(SEEDS):
            d, f = run_experiment(params_base, seed)
            dec_raw[vi, si] = d
            fr_raw[vi, si]  = f

        # ── normalized W_SYN ──────────────────────────────────────────────
        w_found = find_normalized_wsyn(params_base)
        w_nrm[vi] = w_found if w_found is not None else np.nan

        if w_found is not None:
            params_nrm = {**params_base, "W_SYN": w_found}
            for si, seed in enumerate(SEEDS):
                d, f = run_experiment(params_nrm, seed)
                dec_nrm[vi, si] = d
                fr_nrm[vi, si]  = f

        val_disp = val * spec["unit"]
        w_str = f"{w_found*1e3:.2f} mV" if w_found is not None else "N/A"
        print(f"    val={val_disp:.3g}  W_norm={w_str}  "
              f"dec_raw={dec_raw[vi].mean():.3f}  "
              f"dec_nrm={np.nanmean(dec_nrm[vi]):.3f}")

    results[pname] = dict(
        vals    = vals,
        dec_raw = dec_raw,
        fr_raw  = fr_raw,
        dec_nrm = dec_nrm,
        fr_nrm  = fr_nrm,
        w_nrm   = w_nrm,
    )

print("\nAll sweeps complete.\n")


# ── Visualisation ─────────────────────────────────────────────────────────────

n_params = len(SWEEPS)
fig = plt.figure(figsize=(16, 14))
gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.60, wspace=0.42)

for idx, (pname, spec) in enumerate(SWEEPS.items()):
    ax = fig.add_subplot(gs[idx // 2, idx % 2])
    ax2 = ax.twinx()

    res   = results[pname]
    vals  = res["vals"]
    xd    = vals * spec["unit"]
    xdef  = spec["default"] * spec["unit"]

    # ── decorrelation: raw ────────────────────────────────────────────────────
    d_raw_m = res["dec_raw"].mean(axis=1)
    d_raw_s = res["dec_raw"].std(axis=1)
    ax.plot(xd, d_raw_m, "o-", color="#d73027", lw=1.5, ms=4, label="Raw (default W_SYN)")
    ax.fill_between(xd, d_raw_m - d_raw_s, d_raw_m + d_raw_s, color="#d73027", alpha=0.15)

    # ── decorrelation: normalized ─────────────────────────────────────────────
    valid = ~np.isnan(res["dec_nrm"]).all(axis=1)
    if valid.any():
        xn     = xd[valid]
        d_nrm_m = np.nanmean(res["dec_nrm"][valid], axis=1)
        d_nrm_s = np.nanstd(res["dec_nrm"][valid], axis=1)
        ax.plot(xn, d_nrm_m, "s-", color="#1a9850", lw=1.5, ms=4,
                label=f"Normalized (FR={FR_TARGET:.0f} Hz)")
        ax.fill_between(xn, d_nrm_m - d_nrm_s, d_nrm_m + d_nrm_s,
                        color="#1a9850", alpha=0.15)

    # ── W_SYN required (secondary axis) ──────────────────────────────────────
    w_disp = res["w_nrm"] * 1e3   # mV
    ax2.plot(xd, w_disp, "^--", color="#4575b4", lw=1.0, ms=3, alpha=0.70,
             label="W_SYN used (mV)")
    ax2.axhline(DEFAULT["W_SYN"] * 1e3, color="#4575b4", lw=0.6,
                ls=":", alpha=0.5)
    ax2.set_ylabel("W_SYN for FR target (mV)", fontsize=7.5, color="#4575b4")
    ax2.tick_params(axis="y", labelcolor="#4575b4", labelsize=7)

    # ── default marker ────────────────────────────────────────────────────────
    ax.axvline(xdef, color="black", lw=0.8, ls="--", alpha=0.5, label="Default")

    ax.axhline(0, color="gray", lw=0.6, ls=":")
    ax.set_xlabel(spec["label"], fontsize=9)
    ax.set_ylabel("Decorrelation  (R_in − R_out)", fontsize=8.5)
    ax.tick_params(labelsize=8)

    # combine legends from both axes
    lines1, labs1 = ax.get_legend_handles_labels()
    lines2, labs2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labs1 + labs2, fontsize=6.5,
              loc="upper left", framealpha=0.7, ncol=1)

    title = spec["label"].split("  ")[0]
    ax.set_title(title, fontsize=10, fontweight="bold", pad=6)

fig.suptitle(
    f"Drive-normalized Sweep  (R_in = {R_INPUT},  FR target = {FR_TARGET} Hz)\n"
    "Red: raw decorrelation at default W_SYN     "
    "Green: normalized (W_SYN adjusted to fix FR)     "
    "Blue triangles: W_SYN required",
    fontsize=10, fontweight="bold", y=1.01,
)

out_dir  = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, "drive_normalized_sweep.png")
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path}")
plt.show()
