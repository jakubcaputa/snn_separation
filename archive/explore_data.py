"""
explore_data.py — visualize sample recordings from PatchPatSep2s_Public.

Install:
    pip install neo matplotlib numpy quantities

What this shows:
    1. CCIV sweep — step-current injections, used to characterize intrinsic
       properties (Rin, rheobase, AP shape). Multiple sweeps overlaid.
    2. PatSep sweep — correlated Poisson synaptic input at a given correlation
       coefficient R. Multiple trials overlaid to see spike reliability.
"""

from pathlib import Path
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

try:
    from neo.io import AxographIO
except ImportError:
    sys.exit("neo not found. Run:  pip install neo quantities")

# Dane leza w repo (dataset/ jest w .gitignore - pobierane osobno, BioStudies S-BSST219).
DATASET = (Path(__file__).resolve().parents[1]
           / "dataset" / "PatchPatSep2s_Public" / "PatchPatSep2s_Public")

# ── helpers ──────────────────────────────────────────────────────────────────

def load(path: Path):
    """Return a neo Block from an .axgd file."""
    reader = AxographIO(filename=str(path))
    return reader.read_block(lazy=False)


def print_info(block, path: Path):
    segs = block.segments
    print(f"\n{'─'*60}")
    print(f"  {path.parent.parent.parent.name} / {path.parent.parent.name} / "
          f"{path.parent.name} / {path.name}")
    print(f"  sweeps : {len(segs)}")
    if segs:
        for i, sig in enumerate(segs[0].analogsignals):
            sr = float(sig.sampling_rate.rescale("kHz").magnitude)
            dur = float(sig.duration.rescale("ms").magnitude)
            print(f"  ch {i}  : {sig.name or '(unnamed)'}  "
                  f"[{sig.units.dimensionality}]  {sr:.1f} kHz  {dur:.0f} ms")


def plot_sweeps(ax, block, ch: int = 0, max_sweeps: int = 20, label: str = ""):
    """Overlay traces for one channel across sweeps."""
    segs = block.segments
    n = min(len(segs), max_sweeps)
    cmap = plt.cm.viridis
    for i in range(n):
        sig = segs[i].analogsignals[ch]
        t = sig.times.rescale("ms").magnitude
        v = sig.magnitude.flatten()
        color = cmap(i / max(n - 1, 1))
        ax.plot(t, v, color=color, lw=0.8, alpha=0.75,
                label=f"sweep {i+1}" if i < 6 else "")
    sig0 = segs[0].analogsignals[ch]
    ax.set_ylabel(f"{sig0.name or 'Ch'+str(ch)}\n({sig0.units.dimensionality})",
                  fontsize=9)
    ax.set_xlabel("time (ms)", fontsize=9)
    ax.set_title(label, fontsize=10, pad=4)
    ax.grid(True, alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if 1 < n <= 6:
        ax.legend(fontsize=7, loc="upper right")


# ── find sample files ─────────────────────────────────────────────────────────

def find_one(pattern: str) -> Path | None:
    hits = sorted(DATASET.rglob(pattern))
    return hits[0] if hits else None


cciv_path   = find_one("CCIV 001.axgd")          # IV characterization
patsep_path = find_one("PatSep_R0.75_10Hz*.axgd") # R=0.75 corr, 10 Hz

if cciv_path is None and patsep_path is None:
    sys.exit("Could not find any target .axgd files under DATASET.")

# ── load & print info ─────────────────────────────────────────────────────────

targets = []
if cciv_path:
    b = load(cciv_path)
    print_info(b, cciv_path)
    targets.append(("CCIV — intrinsic properties", b, cciv_path))

if patsep_path:
    b = load(patsep_path)
    print_info(b, patsep_path)
    targets.append(("PatSep R=0.75 @ 10 Hz", b, patsep_path))

# ── plot ──────────────────────────────────────────────────────────────────────

for title, block, path in targets:
    n_ch = len(block.segments[0].analogsignals)
    fig, axes = plt.subplots(n_ch, 1,
                             figsize=(14, 3.5 * n_ch),
                             sharex=False)
    if n_ch == 1:
        axes = [axes]

    fig.suptitle(
        f"{path.parent.parent.parent.name} / {path.parent.name} / {path.name}",
        fontsize=10, y=1.01
    )

    for ch, ax in enumerate(axes):
        label = title if ch == 0 else ""
        plot_sweeps(ax, block, ch=ch, max_sweeps=20, label=label)

    plt.tight_layout()

plt.show()
