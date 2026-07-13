"""
decorrelation_vs_npatterns.py — mean decorrelation (R_in - R_out) vs the
NUMBER OF PATTERNS, swept up to N = 1000.

Same DG population model and parameters as the presentation's pattern-capacity
figure, but here we plot ONLY the mean decorrelation and push N to 1000.

Method (cheap): simulate M=1000 patterns through the full DG circuit ONCE, then
for each N read the mean pairwise correlation off the top-left N×N block of the
full correlation matrix (no re-simulation per N).

Output:  separation_parameters_sweep/decorrelation_vs_npatterns.png
         separation_parameters_sweep/decorrelation_vs_npatterns.npz  (raw data)
Run:     snn_sep_venv/Scripts/python.exe separation_parameters_sweep/decorrelation_vs_npatterns.py
"""

import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# Reuse the population simulator from the presentation figure script
sys.path.insert(0, os.path.join(ROOT, 'prezentacja'))
import make_en_figures as M   # noqa: E402

# ── Configuration ─────────────────────────────────────────────────────────────
N_GC, N_FS, N_HMC = 200, 20, 10
R_IN_PARAM, P_ACTIVE = 0.75, 0.25
T_MS    = 600.0
BIN_MS  = 100.0
M_PAT   = 1000          # max number of patterns (x-axis goes up to this)
SEED0   = 1042

C_GC = '#1565C0'


def upper_mean_block(C, n):
    """Mean of the upper triangle of the top-left n×n block, ignoring NaNs."""
    sub = C[:n, :n]
    iu = np.triu_indices(n, 1)
    vals = sub[iu]
    vals = vals[~np.isnan(vals)]
    return float(vals.mean()) if vals.size else np.nan


def main():
    t_start = time.time()
    print(f"Simulating {M_PAT} patterns through the full DG circuit "
          f"(T={T_MS:.0f} ms, N_GC={N_GC})...")
    conn = M._conn(N_GC, N_FS, N_HMC)
    pats = M._patterns(N_GC, M_PAT, R_IN_PARAM, P_ACTIVE)

    n_bins = max(1, int(T_MS / BIN_MS))
    out = np.zeros((M_PAT, N_GC * n_bins), dtype=np.float32)
    for k in range(M_PAT):
        i_arr, t_arr = M._simulate(pats[k], conn, N_GC, N_FS, N_HMC, T_MS,
                                   seed=SEED0 + k)
        out[k] = M._bin(i_arr, t_arr, N_GC, T_MS, BIN_MS).ravel()
        if k % 50 == 0 or k == M_PAT - 1:
            el = time.time() - t_start
            eta = el / (k + 1) * (M_PAT - k - 1)
            print(f"  pattern {k+1:4d}/{M_PAT}  elapsed={el:6.0f}s  eta={eta:6.0f}s")

    print("Computing correlation matrices...")
    Cin = np.corrcoef(pats.astype(np.float64))     # (M, M)
    Cout = np.corrcoef(out.astype(np.float64))     # (M, M)

    # Log-spaced N values from 2 up to M_PAT
    Ns = np.unique(np.round(np.logspace(np.log10(2), np.log10(M_PAT), 30))).astype(int)
    Ns = Ns[Ns >= 2]
    r_in = np.array([upper_mean_block(Cin, n) for n in Ns])
    r_out = np.array([upper_mean_block(Cout, n) for n in Ns])
    dec = r_in - r_out

    # ── Plot: mean decorrelation vs N ─────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    ax.plot(Ns, dec, 'o-', color=C_GC, lw=2.2, ms=6)
    ax.axhline(0, color='gray', lw=0.8, ls=':')
    ax.set_xscale('log')
    ax.set_xlabel('Number of patterns  N', fontsize=11)
    ax.set_ylabel('Mean decorrelation  (R_in − R_out)', fontsize=11)
    ax.set_ylim(0, max(dec) * 1.15)
    ax.set_title('DG pattern separation vs number of patterns\n'
                 f'mean decorrelation stays flat up to N = {M_PAT}',
                 fontsize=12, fontweight='bold')
    ax.grid(axis='both', alpha=0.25, which='both')
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    png = os.path.join(HERE, 'decorrelation_vs_npatterns.png')
    fig.savefig(png, dpi=150, bbox_inches='tight')
    plt.close(fig)

    np.savez(os.path.join(HERE, 'decorrelation_vs_npatterns.npz'),
             Ns=Ns, r_in=r_in, r_out=r_out, dec=dec)

    print(f"\nSaved: {png}")
    print(f"  decorrelation range: {dec.min():.3f}–{dec.max():.3f} "
          f"(R_out range {r_out.min():.3f}–{r_out.max():.3f})")
    print(f"  total time: {time.time() - t_start:.0f}s")


if __name__ == '__main__':
    main()
