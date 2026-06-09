"""
visualize_dg.py — Co dzieje się w zakręcie zębatym (DG)?

Ładuje prawdziwe nagrania granule cells z datasetu PatchPatSep2s_Public
i pokazuje:
  1. Ślady napięcia (voltage traces) dla kilku sweepów — widać potencjały czynnościowe
  2. Raster plot spajków w różnych próbach
  3. Macierz korelacji output spike trainów vs R_input
  4. Wykres R_input vs R_output — "pattern separation"

Dataset: GCyo_P10Hz_2 / (pierwsze dostępne nagranie GC)
Wejście:  Sygnały Poissona ~10 Hz, korelacja R (0.5, 0.75, 0.90, 1.0)
Wyjście:  Potencjał błonowy GC [kanał 0, mV] z action potentials

Instalacja:  pip install neo matplotlib numpy scipy quantities
Uruchomienie: python visualize_dg.py
"""

from pathlib import Path
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import pearsonr

try:
    from neo.io import AxographIO
except ImportError:
    sys.exit("neo nie znalezione. Uruchom:  pip install neo quantities")

# ── Ścieżka do datasetu ───────────────────────────────────────────────────────
DATASET = Path(__file__).parent / "dataset" / "PatchPatSep2s_Public" / "PatchPatSep2s_Public"
GC_FOLDER = DATASET / "GCyo_P10Hz_2"

if not GC_FOLDER.exists():
    sys.exit(f"Nie znaleziono folderu: {GC_FOLDER}")


# ── Ładowanie pliku ──────────────────────────────────────────────────────────
def load_block(path: Path):
    return AxographIO(filename=str(path)).read_block(lazy=False)


def get_voltage_traces(block, ch: int = 0):
    """Zwraca listę (t_ms, v_mV) dla każdego sweepu."""
    traces = []
    for seg in block.segments:
        if ch >= len(seg.analogsignals):
            continue
        sig = seg.analogsignals[ch]
        t_ms = sig.times.rescale("ms").magnitude
        v    = sig.magnitude.flatten()
        # Wykrywanie jednostek: jeśli wartości < 1, to prawdopodobnie w V → konwertuj na mV
        if np.abs(v).max() < 1.0:
            v = v * 1000.0
        traces.append((t_ms, v))
    return traces


def print_block_info(block, path: Path):
    segs = block.segments
    print(f"  {path.name}: {len(segs)} sweepów", end="")
    if segs:
        for i, sig in enumerate(segs[0].analogsignals):
            sr  = float(sig.sampling_rate.rescale("kHz").magnitude)
            dur = float(sig.duration.rescale("ms").magnitude)
            print(f"  | ch{i}: {sig.name or '?'} [{sig.units}] {sr:.0f}kHz {dur:.0f}ms",
                  end="")
    print()


# ── Detekcja spajków ─────────────────────────────────────────────────────────
def extract_spikes(t_ms, v_mv, threshold_mv: float = -20.0):
    """Detekcja przez przekroczenie progu (narastające zbocze)."""
    above  = v_mv > threshold_mv
    cross  = np.diff(above.astype(np.int8), prepend=0) == 1
    return t_ms[cross]


# ── Korelacja output spike trainów ──────────────────────────────────────────
def bin_spikes(spk_times_ms, T_ms: float, bin_ms: float = 10.0):
    """Binowanie spajków: zwraca wektor zliczeń."""
    bins   = np.arange(0, T_ms + bin_ms, bin_ms)
    counts, _ = np.histogram(spk_times_ms, bins=bins)
    return counts.astype(float)


def pairwise_r_matrix(spike_lists, T_ms: float, bin_ms: float = 10.0):
    """Macierz Pearson R dla listy spike train-ów."""
    counts = [bin_spikes(spk, T_ms, bin_ms) for spk in spike_lists]
    n      = len(counts)
    R_mat  = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            if counts[i].std() > 0 and counts[j].std() > 0:
                r, _ = pearsonr(counts[i], counts[j])
                R_mat[i, j] = R_mat[j, i] = r if not np.isnan(r) else 0.0
    return R_mat


def mean_upper_r(R_mat):
    idx = np.triu_indices_from(R_mat, k=1)
    return R_mat[idx].mean()


# ── Znajdź pliki dla każdej wartości R ──────────────────────────────────────
# Zbieramy pliki posortowane po wartości R z pierwszego dostępnego GC

R_TARGETS = {0.50: "R0.5*.axgd",
             0.75: "R0.75*.axgd",
             0.90: "R0.9*.axgd",
             1.00: "R1.0*.axgd"}

print(f"\nSzukam plików w: {GC_FOLDER}")
selected = {}   # R_val → Path

for r_val, pattern in R_TARGETS.items():
    hits = sorted(GC_FOLDER.rglob(pattern))
    # pomijamy pliki "in reality FS" (błędnie oznaczone)
    hits = [h for h in hits if "FSneuron" not in str(h) and "FS" not in str(h)]
    # wyeliminuj duplikaty R0.75 vs R0.750 — bierz pierwsze
    if hits:
        selected[r_val] = hits[0]
        print(f"  R={r_val:.2f}: {hits[0].relative_to(DATASET)}")
    else:
        print(f"  R={r_val:.2f}: brak pliku")

if not selected:
    sys.exit("Nie znaleziono żadnych plików PatSep.")

# ── Ładowanie danych ─────────────────────────────────────────────────────────
print("\nŁadowanie bloków...")
data = {}
for r_val, path in selected.items():
    block  = load_block(path)
    print_block_info(block, path)
    traces = get_voltage_traces(block, ch=0)
    T_ms   = traces[0][0][-1] if traces else 2000.0
    data[r_val] = dict(path=path, traces=traces, T_ms=T_ms)

r_vals = sorted(data.keys())
n_r    = len(r_vals)

# ── Rysowanie ────────────────────────────────────────────────────────────────
COLORS = plt.cm.plasma(np.linspace(0.1, 0.85, n_r))
MAX_VOLTAGE_SWEEPS = 8    # ile śladów napięcia nakładamy
SPIKE_THR_MV       = -20  # próg detekcji spajków [mV]
BIN_MS             = 10   # szerokość binu do korelacji [ms]
SHOW_MS            = 2000 # okno czasowe na wykresach [ms]

fig = plt.figure(figsize=(5 * n_r, 13))
gs  = gridspec.GridSpec(4, n_r, figure=fig,
                        hspace=0.55, wspace=0.35,
                        height_ratios=[3, 2, 2, 1.5])

r_in_list  = []
r_out_list = []

for col, (r_val, color) in enumerate(zip(r_vals, COLORS)):
    d      = data[r_val]
    traces = d["traces"]
    T_ms   = d["T_ms"]
    n_sw   = len(traces)

    # — Wiersz 0: ślady napięcia ─────────────────────────────────────────────
    ax0 = fig.add_subplot(gs[0, col])
    for i, (t_ms, v) in enumerate(traces[:MAX_VOLTAGE_SWEEPS]):
        alpha = 0.7 if i == 0 else 0.35
        lw    = 1.0 if i == 0 else 0.5
        ax0.plot(t_ms, v, lw=lw, alpha=alpha, color=color)

    ax0.axhline(SPIKE_THR_MV, color="k", ls="--", lw=0.8, alpha=0.5,
                label=f"próg {SPIKE_THR_MV} mV")
    ax0.set_xlim(0, min(T_ms, SHOW_MS))
    ax0.set_ylim(-100, 50)
    ax0.set_title(f"R_input = {r_val:.2f}\n({n_sw} sweepów)", fontsize=10)
    ax0.set_xlabel("Czas (ms)", fontsize=8)
    if col == 0:
        ax0.set_ylabel("V (mV)", fontsize=9)
        ax0.legend(fontsize=7, loc="upper right")
    ax0.spines[["top", "right"]].set_visible(False)

    # — Wiersz 1: raster spajków ─────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[1, col])
    all_spikes = []
    for sw_i, (t_ms, v) in enumerate(traces):
        spk = extract_spikes(t_ms, v, SPIKE_THR_MV)
        all_spikes.append(spk)
        vis = spk[spk <= SHOW_MS]
        ax1.scatter(vis, np.full_like(vis, sw_i + 1),
                    s=3, color=color, alpha=0.8, linewidths=0)

    ax1.set_xlim(0, min(T_ms, SHOW_MS))
    ax1.set_ylim(0.4, n_sw + 0.6)
    ax1.set_xlabel("Czas (ms)", fontsize=8)
    if col == 0:
        ax1.set_ylabel("Sweep #", fontsize=9)
    mean_fr = np.mean([len(s) / (T_ms * 1e-3) for s in all_spikes])
    ax1.set_title(f"Output spajki  fr={mean_fr:.1f} Hz", fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    # — Wiersz 2: macierz korelacji ──────────────────────────────────────────
    ax2 = fig.add_subplot(gs[2, col])
    if len(all_spikes) >= 2:
        R_mat    = pairwise_r_matrix(all_spikes, T_ms, BIN_MS)
        mean_r   = mean_upper_r(R_mat)
        im       = ax2.imshow(R_mat, vmin=-0.2, vmax=1.0,
                              cmap="RdYlGn", aspect="auto")
        plt.colorbar(im, ax=ax2, shrink=0.7, label="Pearson R")
        ax2.set_title(f"Output corr  (mean R={mean_r:.3f})", fontsize=9)
        ax2.set_xlabel("Sweep #", fontsize=8)
        if col == 0:
            ax2.set_ylabel("Sweep #", fontsize=9)
        r_in_list.append(r_val)
        r_out_list.append(mean_r)

# — Wiersz 3: R_input vs R_output ────────────────────────────────────────────
ax3 = fig.add_subplot(gs[3, :])
if r_in_list:
    r_in_arr  = np.array(r_in_list)
    r_out_arr = np.array(r_out_list)
    ax3.plot([0, 1], [0, 1], "--", color="gray", alpha=0.5,
             label="brak separacji (R_out = R_in)")
    ax3.plot(r_in_arr, r_out_arr, "o-", color="steelblue",
             lw=2, ms=9, label="GC output R (nagrania)")
    ax3.fill_between(r_in_arr, r_out_arr, r_in_arr,
                     alpha=0.15, color="steelblue", label="decorrelation")
    for ri, ro in zip(r_in_arr, r_out_arr):
        ax3.annotate(f"{ro:.2f}", (ri, ro),
                     textcoords="offset points", xytext=(5, 5), fontsize=8)
    ax3.set_xlabel("R_input (korelacja wzorców wejściowych)", fontsize=9)
    ax3.set_ylabel("R_output (korelacja outputu GC)", fontsize=9)
    ax3.set_title("Pattern separation: zakręt zębaty dekoreluje wzorce wejściowe",
                  fontsize=10)
    ax3.set_xlim(0, 1.1)
    ax3.set_ylim(-0.2, 1.1)
    ax3.legend(fontsize=8)
    ax3.spines[["top", "right"]].set_visible(False)

fig.suptitle("Granule Cells (DG) — prawdziwe nagrania patch-clamp\n"
             f"Dataset: GCyo_P10Hz_2 | {DATASET.name}",
             fontsize=12, fontweight="bold")

out_path = Path(__file__).parent / "visualize_dg.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"\nZapisano: {out_path}")
plt.show()
