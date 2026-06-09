"""
explore_gc1_r090.py — plot all R0.90 recordings from GC1 (2011-8-10).

Each file = one run of the pattern separation protocol at R=0.90 correlation.
Each sweep within a file = one trial (different random Poisson realization,
same correlation coefficient).

Install:  pip install neo matplotlib numpy quantities
Run:      python explore_gc1_r090.py
"""

from pathlib import Path
import sys
import numpy as np
import matplotlib.pyplot as plt

try:
    from neo.io import AxographIO
except ImportError:
    sys.exit("neo not found. Run:  pip install neo quantities")

GC1 = Path(r"C:\Users\jjaku\PhD\Neuro\PatchPatSep2s_Public\PatchPatSep2s_Public"
           r"\GCyo_P10Hz_2\2011-8-10\GC1")

files = [GC1 / "R0.90 001.axgd", GC1 / "R0.90 002.axgd"]

if not files:
    sys.exit(f"No R0.9*.axgd files found in {GC1}")

print(f"Found {len(files)} file(s):")
for f in files:
    print(f"  {f.name}")


def load(path: Path):
    reader = AxographIO(filename=str(path))
    return reader.read_block(lazy=False)


# ── load all files ────────────────────────────────────────────────────────────

blocks = []
for f in files:
    b = load(f)
    blocks.append((f.name, b))
    segs = b.segments
    print(f"\n{f.name}")
    print(f"  sweeps : {len(segs)}")
    for i, sig in enumerate(segs[0].analogsignals):
        sr  = float(sig.sampling_rate.rescale("kHz").magnitude)
        dur = float(sig.duration.rescale("ms").magnitude)
        print(f"  ch {i}  : {sig.name or '(unnamed)'}  "
              f"[{sig.units.dimensionality}]  {sr:.1f} kHz  {dur:.0f} ms")

# ── plot ──────────────────────────────────────────────────────────────────────
# Layout: one column per file, one row per channel.

n_files = len(blocks)
n_ch    = len(blocks[0][1].segments[0].analogsignals)

fig, axes = plt.subplots(
    n_ch, n_files,
    figsize=(7 * n_files, 3.5 * n_ch),
    sharex="row", sharey="row",
    squeeze=False,
)

fig.suptitle("GCyo_P10Hz_2 / 2011-8-10 / GC1 — R=0.90", fontsize=12)

cmap = plt.cm.viridis

for col, (fname, block) in enumerate(blocks):
    segs   = block.segments
    n_sw   = len(segs)

    for row in range(n_ch):
        ax = axes[row, col]

        for sw in range(n_sw):
            if row >= len(segs[sw].analogsignals):
                continue
            sig   = segs[sw].analogsignals[row]
            t     = sig.times.rescale("ms").magnitude
            v     = sig.magnitude.flatten()
            color = cmap(sw / max(n_sw - 1, 1))
            ax.plot(t, v, color=color, lw=0.7, alpha=0.75)

        if row == 0:
            ax.set_title(fname, fontsize=9)

        if col == 0:
            sig0  = segs[0].analogsignals[row]
            label = sig0.name or f"ch {row}"
            units = sig0.units.dimensionality
            ax.set_ylabel(f"{label}\n({units})", fontsize=9)

        if row == n_ch - 1:
            ax.set_xlabel("time (ms)", fontsize=9)

        ax.grid(True, alpha=0.2)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

# Colorbar to show sweep order
sm = plt.cm.ScalarMappable(cmap=cmap,
                            norm=plt.Normalize(vmin=1, vmax=n_sw))
sm.set_array([])
cbar = fig.colorbar(sm, ax=axes[:, -1], shrink=0.6, pad=0.02)
cbar.set_label("sweep #", fontsize=9)

plt.tight_layout()
plt.show()
