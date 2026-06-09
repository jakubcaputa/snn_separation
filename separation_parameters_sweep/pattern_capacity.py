"""
separation_parameters_sweep/pattern_capacity.py

Pattern capacity experiment for the LIF granule-cell model.

Sweeps the number of patterns (N_PATTERNS) from 2 to N_MAX and measures
how well a single LIF neuron can separate them.  At each N:
  - N patterns are generated with the same pairwise R_in
  - The neuron produces one spike train per pattern
  - All C(N,2) pairwise output correlations R_out are measured

Metrics reported vs N:
  1. Mean pairwise decorrelation  (R_in − mean R_out)
  2. Worst-case pairwise R_out   (max over all pairs — the "hardest" pair)
  3. Fraction of pairs that CONVERGE  (R_out > R_in)
  4. Distribution of pairwise R_out  (violin / box per N)

Three R_in levels: 0.50, 0.75, 0.90

Interpretation:
  For a single linear output neuron, pairwise R_out depends only on the
  pair, so it should be roughly constant in N (each new pattern adds new
  pairs but doesn't change existing ones).  Any deviation from flatness
  reveals finite-sample noise growth.

Output: separation_parameters_sweep/pattern_capacity.png
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from itertools import combinations

from single_neuron_patsep import make_patterns, mean_pairwise_r, bin_train

# ── Simulation constants ──────────────────────────────────────────────────────
T   = 2.0
dt  = 1e-4
n_t = int(T / dt)

# ── Default neuron parameters ─────────────────────────────────────────────────
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
N_VALS    = list(range(2, 51, 2)) + [55, 60, 70, 80]  # 2..50 step 2 + a few larger
SEEDS     = [42, 43, 44, 45, 46]
R_LEVELS  = [0.50, 0.75, 0.90]
R_COLORS  = ["#4575b4", "#d73027", "#1a9850"]
BIN_MS    = 10.0

FR_MIN    = 3.0   # Hz — ignore seeds where FR is too low (near-silent)


# ── LIF simulator ─────────────────────────────────────────────────────────────

def simulate_lif(inputs_2d: np.ndarray) -> np.ndarray:
    p = DEFAULT
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


def pairwise_r_out(out_spikes: list, bin_ms: float = BIN_MS) -> np.ndarray:
    """All C(N,2) pairwise Pearson R for the output spike trains."""
    bins = [bin_train(s, bin_ms) for s in out_spikes]
    rs = []
    for i, j in combinations(range(len(bins)), 2):
        a, b = bins[i].astype(float), bins[j].astype(float)
        if a.std() < 1e-9 or b.std() < 1e-9:
            rs.append(0.0)
        else:
            rs.append(float(np.corrcoef(a, b)[0, 1]))
    return np.array(rs)


# ── Run experiment ────────────────────────────────────────────────────────────

print("Pattern capacity experiment\n")
print(f"  N values : {N_VALS}")
print(f"  R_in     : {R_LEVELS}")
print(f"  Seeds    : {SEEDS}\n")

# results[r_idx][n_idx] = dict with keys: r_in, pairwise_rout, mean_dec, max_rout, frac_conv
all_results = {}

for ri, R_in_target in enumerate(R_LEVELS):
    print(f"  R_in = {R_in_target}")
    level_res = []

    for ni, N in enumerate(N_VALS):
        pairwise_routs_all = []    # collect all pairwise R_out across seeds
        mean_rin_per_seed  = []
        frs_per_seed       = []

        for seed in SEEDS:
            rng  = np.random.default_rng(seed)
            pats = make_patterns(N, DEFAULT["r_input"], R_in_target,
                                 DEFAULT["n_syn"], T, dt, rng)

            out_spikes = []
            fr_list    = []
            for pat in pats:
                spk = simulate_lif(pat)
                out_spikes.append(spk)
                fr_list.append(spk.sum() / T)

            mean_fr = float(np.mean(fr_list))
            if mean_fr < FR_MIN:
                continue   # skip near-silent runs

            # actual R_in (may differ slightly from target due to finite N)
            in_trains = [pat.sum(axis=0) for pat in pats]
            r_in_actual = mean_pairwise_r(in_trains)

            pw = pairwise_r_out(out_spikes)
            pairwise_routs_all.append(pw)
            mean_rin_per_seed.append(r_in_actual)
            frs_per_seed.append(mean_fr)

        if len(pairwise_routs_all) == 0:
            level_res.append(None)
            continue

        pw_flat = np.concatenate(pairwise_routs_all)
        r_in    = float(np.mean(mean_rin_per_seed))
        mean_dec     = float(r_in - np.mean(pw_flat))
        worst_rout   = float(np.max(pw_flat))
        frac_conv    = float(np.mean(pw_flat > r_in))
        mean_fr_val  = float(np.mean(frs_per_seed))

        level_res.append(dict(
            N             = N,
            r_in          = r_in,
            pairwise_rout = pw_flat,
            mean_dec      = mean_dec,
            worst_rout    = worst_rout,
            frac_conv     = frac_conv,
            mean_fr       = mean_fr_val,
        ))

        if (ni + 1) % 5 == 0 or N == N_VALS[-1]:
            print(f"    N={N:3d}  dec={mean_dec:.3f}  "
                  f"worst_Rout={worst_rout:.3f}  "
                  f"frac_conv={frac_conv:.2f}  "
                  f"FR={mean_fr_val:.1f} Hz")

    all_results[R_in_target] = level_res

print("\nAll simulations done.\n")


# ── Visualisation ─────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(16, 12))
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.50, wspace=0.38)

ax_dec  = fig.add_subplot(gs[0, 0])   # mean decorrelation vs N
ax_wst  = fig.add_subplot(gs[0, 1])   # worst-case R_out vs N
ax_conv = fig.add_subplot(gs[1, 0])   # fraction converging vs N
ax_vln  = fig.add_subplot(gs[1, 1])   # R_out distribution for R_in=0.75

# ── helper ────────────────────────────────────────────────────────────────────

def extract_series(level_res):
    """Extract (ns, decs, wsts, convs) filtering None entries."""
    ns, decs, wsts, convs = [], [], [], []
    for entry in level_res:
        if entry is None:
            continue
        ns.append(entry["N"])
        decs.append(entry["mean_dec"])
        wsts.append(entry["worst_rout"])
        convs.append(entry["frac_conv"])
    return (np.array(ns), np.array(decs),
            np.array(wsts), np.array(convs))


# ── mean decorrelation ────────────────────────────────────────────────────────
for ri, R_in_target in enumerate(R_LEVELS):
    ns, decs, wsts, convs = extract_series(all_results[R_in_target])
    c = R_COLORS[ri]
    ax_dec.plot(ns, decs, "o-", color=c, lw=1.5, ms=4,
                label=f"R_in={R_in_target}")
ax_dec.axhline(0, color="gray", lw=0.6, ls=":")
ax_dec.set_xlabel("Number of patterns  N", fontsize=9)
ax_dec.set_ylabel("Mean decorrelation  (R_in − mean R_out)", fontsize=8.5)
ax_dec.set_title("Mean decorrelation vs N", fontsize=10, fontweight="bold")
ax_dec.legend(fontsize=8, framealpha=0.7)
ax_dec.tick_params(labelsize=8)

# ── worst-case R_out ──────────────────────────────────────────────────────────
for ri, R_in_target in enumerate(R_LEVELS):
    ns, decs, wsts, convs = extract_series(all_results[R_in_target])
    c = R_COLORS[ri]
    ax_wst.plot(ns, wsts, "s--", color=c, lw=1.5, ms=4,
                label=f"R_in={R_in_target}")
    ax_wst.axhline(R_in_target, color=c, lw=0.6, ls=":", alpha=0.6)
ax_wst.set_xlabel("Number of patterns  N", fontsize=9)
ax_wst.set_ylabel("Worst-case R_out  (max over all pairs)", fontsize=8.5)
ax_wst.set_title("Worst-case output correlation vs N", fontsize=10, fontweight="bold")
ax_wst.legend(fontsize=8, framealpha=0.7)
ax_wst.tick_params(labelsize=8)

# ── fraction converging ───────────────────────────────────────────────────────
for ri, R_in_target in enumerate(R_LEVELS):
    ns, decs, wsts, convs = extract_series(all_results[R_in_target])
    c = R_COLORS[ri]
    ax_conv.plot(ns, convs * 100, "^-", color=c, lw=1.5, ms=4,
                 label=f"R_in={R_in_target}")
ax_conv.set_xlabel("Number of patterns  N", fontsize=9)
ax_conv.set_ylabel("Pairs where R_out > R_in  (%)", fontsize=8.5)
ax_conv.set_title("Fraction of converging pairs vs N", fontsize=10, fontweight="bold")
ax_conv.legend(fontsize=8, framealpha=0.7)
ax_conv.tick_params(labelsize=8)

# ── R_out distribution — violin for R_in = 0.75 ──────────────────────────────
TARGET_R = 0.75
level_res_75 = all_results[TARGET_R]

# pick a reasonable subset of N values for violin readability
n_show = [2, 5, 10, 15, 20, 30, 40, 50, 60, 80]
violin_data  = []
violin_positions = []
for N in n_show:
    # find closest N in results
    match = [e for e in level_res_75 if e is not None and e["N"] == N]
    if not match:
        # find nearest
        available = [e for e in level_res_75 if e is not None]
        if not available:
            continue
        match = [min(available, key=lambda e: abs(e["N"] - N))]
    entry = match[0]
    violin_data.append(entry["pairwise_rout"])
    violin_positions.append(entry["N"])

if violin_data:
    vp = ax_vln.violinplot(violin_data, positions=violin_positions,
                           widths=[max(1, p * 0.4) for p in violin_positions],
                           showmedians=True, showextrema=True)
    for body in vp["bodies"]:
        body.set_facecolor("#d73027")
        body.set_alpha(0.45)
    vp["cmedians"].set_color("black")
    vp["cmedians"].set_linewidth(1.2)

    ax_vln.axhline(TARGET_R, color="black", lw=1.0, ls="--",
                   label=f"R_in = {TARGET_R}")

ax_vln.set_xlabel("Number of patterns  N", fontsize=9)
ax_vln.set_ylabel("Pairwise R_out", fontsize=8.5)
ax_vln.set_title(f"Distribution of pairwise R_out  (R_in = {TARGET_R})",
                 fontsize=10, fontweight="bold")
ax_vln.legend(fontsize=8, framealpha=0.7)
ax_vln.tick_params(labelsize=8)

fig.suptitle(
    "Pattern Capacity — Single LIF Granule Cell\n"
    "How many patterns can one neuron separate as N grows?",
    fontsize=11, fontweight="bold", y=1.02,
)

out_dir  = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, "pattern_capacity.png")
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path}")
plt.show()
