"""
dataset_overview.py — Kompleksowe podsumowanie datasetu PatchPatSep2s_Public.

Generuje:
  1. Raport tekstowy w konsoli
  2. Rysunek PNG z:
       A) Schemat biologiczny obwodu DG
       B) Liczba nagrań per typ komórki
       C) Rozkład wartości R (korelacja wejściowa)
       D) Liczba plików per protokół
       E) Tabela: co jest inputem/outputem w każdym folderze

Uruchomienie: python dataset_overview.py
"""

from pathlib import Path
from collections import defaultdict
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

DATASET = Path(__file__).parent / "dataset" / "PatchPatSep2s_Public" / "PatchPatSep2s_Public"

# ══════════════════════════════════════════════════════════════════════════════
# METADANE FOLDERÓW (opis biologiczny każdego eksperymentu)
# ══════════════════════════════════════════════════════════════════════════════

FOLDER_META = {
    "GCyo_P10Hz_2": {
        "label":       "GC młode\n(yo)",
        "cell_type":   "Granule Cell (GC)",
        "input_rate":  "10 Hz",
        "input_type":  "Poisson",
        "drug":        "brak",
        "color":       "#4C9BE8",
        "description": (
            "Główny dataset. Granule cells (neurony ziarniste) z młodych myszy.\n"
            "Wejście: Poissonowe spike trains ~10 Hz przez lateral perforant path (LPP).\n"
            "Najszerszy zakres R (0.05–1.0), najlepsza jakość danych."
        ),
    },
    "GCandFS_yo_P10Hz_1": {
        "label":       "GC + FSIN\n(yo)",
        "cell_type":   "GC + Fast-Spiking Interneuron",
        "input_rate":  "10 Hz",
        "input_type":  "Poisson (5 wzorców: 13,18,29,41,49)",
        "drug":        "brak",
        "color":       "#E87F4C",
        "description": (
            "Jednoczesne nagranie GC i fast-spiking interneuronów (FSIN).\n"
            "FSIN to interneurony GABAergiczne odpowiedzialne za feed-forward inhibition.\n"
            "Wzorce numerowane (13,18,29,41,49) zamiast R-wartości."
        ),
    },
    "GC_yo_BeforeAfterGZN_P10Hz": {
        "label":       "GC przed/po\ngabazinie",
        "cell_type":   "Granule Cell (GC)",
        "input_rate":  "10 Hz",
        "input_type":  "Poisson",
        "drug":        "Gabazine (GABA-A bloker)",
        "color":       "#E84C6E",
        "description": (
            "GC nagrywane przed i po podaniu gabazyny (blokada GABA-A receptorów).\n"
            "Cel: zbadanie roli inhibicji w pattern separation.\n"
            "Bez inhibicji GC powinny być bardziej podatne na wejście → mniejsza separacja."
        ),
    },
    "GCad_Sa_B10HzandPdeltaFR": {
        "label":       "GC dorosłe\n(ad)",
        "cell_type":   "Granule Cell (GC) — dorosłe",
        "input_rate":  "10 Hz (Poisson) + zmienne FR",
        "input_type":  "Poisson + B10Hz + ΔFR range",
        "drug":        "brak",
        "color":       "#4CE87F",
        "description": (
            "Granule cells z dorosłych myszy.\n"
            "Porównanie: młode vs dorosłe GC w pattern separation.\n"
            "Protokoły: oryginalny 10 Hz + bursty 10 Hz + Poisson z zmiennym FR (7–31.5 Hz)."
        ),
    },
    "HMC_yo_P10Hz": {
        "label":       "HMC\n(yo)",
        "cell_type":   "Hilar Mossy Cell (HMC)",
        "input_rate":  "10 Hz",
        "input_type":  "Poisson",
        "drug":        "różne prądy/napięcia",
        "color":       "#B44CE8",
        "description": (
            "Hilar mossy cells — neurony wzgórza (hilus) DG, glutamatergiczne.\n"
            "Łączą GC z sobą (feedback) i z interneuronami.\n"
            "Separacja czasowo-zależna: inna niż GC przy krótkich/długich bin-ach."
        ),
    },
    "CA3andGCgzn_yo_P30Hz": {
        "label":       "CA3 + GC\n(gabazyna, 30 Hz)",
        "cell_type":   "CA3 Pyramidal + GC",
        "input_rate":  "30 Hz",
        "input_type":  "Poisson",
        "drug":        "Gabazine (100 nM) — częściowa blokada",
        "color":       "#E8D44C",
        "description": (
            "CA3 pyramidal cells + GC, wejście 30 Hz z częściową blokadą GABA-A.\n"
            "CA3 normalnie nie strzela przy 10 Hz; gabazyna + 30 Hz umożliwia firing.\n"
            "Subfoldery: CA3/, GCctrl/, FSIN/ — porównanie separacji między obszarami.\n"
            "CA3 pokazuje silniejszą separację niż GC przy długich bin-ach."
        ),
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# SKANOWANIE DATASETU
# ══════════════════════════════════════════════════════════════════════════════

def extract_r_value(filename: str):
    """Wyciąga wartość R z nazwy pliku, np. 'R0.75 001.axgd' → 0.75."""
    m = re.search(r"R\s?(\d+\.?\d*)", filename, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


def scan_dataset(dataset_path: Path) -> dict:
    stats = {}
    for folder in sorted(dataset_path.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        axgd_files = list(folder.rglob("*.axgd"))
        if not axgd_files:
            continue

        r_values  = []
        protocols = defaultdict(int)

        for f in axgd_files:
            name = f.name
            r = extract_r_value(name)
            if r is not None:
                r_values.append(r)

            if re.search(r"CCIV|CC-IV|VC-IV|IVcurve", name, re.IGNORECASE):
                protocols["CCIV (IV krzywa)"] += 1
            elif re.search(r"PatSep|patsep", name, re.IGNORECASE):
                protocols["PatSep"] += 1
            elif re.search(r"FindStim", name, re.IGNORECASE):
                protocols["FindStim"] += 1
            elif re.search(r"^R\d", name):
                protocols["PatSep (stary format R*)"] += 1
            elif re.search(r"^\d{2}\s", name):
                protocols["PatSep (wzorzec nr)"] += 1
            else:
                protocols["inne"] += 1

        # Unikalne komórki (foldery GC1, GC2, ... lub pyr1, pyr2 ...)
        cell_folders = set()
        for f in axgd_files:
            parts = f.relative_to(folder).parts
            if len(parts) >= 2:
                cell_folders.add(parts[-2])

        stats[folder.name] = {
            "n_files":      len(axgd_files),
            "n_cells":      len(cell_folders),
            "r_values":     r_values,
            "protocols":    dict(protocols),
            "r_unique":     sorted(set(round(r, 3) for r in r_values)),
        }

    return stats


print(f"Skanuję: {DATASET}\n")
stats = scan_dataset(DATASET)

# ══════════════════════════════════════════════════════════════════════════════
# RAPORT TEKSTOWY
# ══════════════════════════════════════════════════════════════════════════════

SEP = "═" * 70
print(SEP)
print("  PODSUMOWANIE DATASETU: PatchPatSep2s_Public")
print(SEP)
total_files = sum(s["n_files"] for s in stats.values())
print(f"  Łącznie plików .axgd : {total_files}")
print(f"  Łącznie folderów     : {len(stats)}\n")

for folder_name, s in stats.items():
    meta = FOLDER_META.get(folder_name, {})
    print(f"{'─'*70}")
    print(f"  📁  {folder_name}")
    print(f"      Typ komórki : {meta.get('cell_type', '?')}")
    print(f"      Input rate  : {meta.get('input_rate', '?')}  |  "
          f"Input type: {meta.get('input_type', '?')}")
    print(f"      Lek/warunek : {meta.get('drug', '?')}")
    print(f"      Pliki .axgd : {s['n_files']}  |  "
          f"Komórki: {s['n_cells']}")
    if s["r_unique"]:
        print(f"      Wartości R  : {s['r_unique']}")
    print(f"      Protokoły   : {s['protocols']}")
    if meta.get("description"):
        for line in meta["description"].split("\n"):
            print(f"      → {line}")
    print()

print(SEP)
print("  LEGENDA: CO JEST INPUTEM, CO OUTPUTEM")
print(SEP)
print("""
  INPUT  (do neuronu):
    • Poissonowe spike trains generowane przez oprogramowanie
    • Dostarczone przez theta pipetę do lateral perforant path (LPP)
    • Parametr R = parzystą korelacja między N=5 wzorcami (Pearson, bin 10 ms)
    • Tempo: 10 Hz (GC) lub 30 Hz (CA3), czas trwania: 2 sekundy

  OUTPUT (nagrany z neuronu):
    • Kanał 0 pliku .axgd: potencjał błonowy [mV] — zawiera action potentials
    • Kanał 1 (jeśli istnieje): prąd komendowy [pA] lub inne

  CCIV pliki (nie PatSep):
    • Charakteryzacja intrinsic właściwości komórki
    • Wstrzykiwanie kroków prądu → V_rest, R_in, rheobase, kształt AP

  PROTOKÓŁ EKSPERYMENTU:
    1. Wygeneruj 5 wzorców Poissona z korelacją R
    2. Podaj wzorzec 1 → nagraj odpowiedź GC (kilka sweepów)
    3. Podaj wzorzec 2 → nagraj odpowiedź GC (kilka sweepów)
    ...
    5. Podaj wzorzec 5 → nagraj odpowiedź GC
    6. Oblicz parzystą korelację output spike trainów → R_out
    7. Wynik: R_out < R_in = pattern separation!
""")

# ══════════════════════════════════════════════════════════════════════════════
# WIZUALIZACJA
# ══════════════════════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(18, 14))
gs_main = gridspec.GridSpec(3, 3, figure=fig,
                            hspace=0.55, wspace=0.4,
                            height_ratios=[1.6, 1.2, 1.2])

# ── Panel A: Schemat biologiczny ─────────────────────────────────────────────
ax_A = fig.add_subplot(gs_main[0, :])
ax_A.set_xlim(0, 10)
ax_A.set_ylim(0, 3)
ax_A.axis("off")
ax_A.set_title("A)  Schemat obwodu biologicznego — co jest inputem i outputem w datasecie",
               fontsize=11, fontweight="bold", pad=8)

def draw_box(ax, x, y, w, h, label, sublabel="", color="#4C9BE8", fontsize=10):
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.05",
                          facecolor=color, edgecolor="white",
                          linewidth=2, alpha=0.9, zorder=3)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2 + (0.12 if sublabel else 0), label,
            ha="center", va="center", fontsize=fontsize,
            fontweight="bold", color="white", zorder=4)
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.18, sublabel,
                ha="center", va="center", fontsize=8,
                color="white", alpha=0.9, zorder=4)

def draw_arrow(ax, x1, x2, y, color="gray", label="", lw=2):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=lw, mutation_scale=16))
    if label:
        ax.text((x1 + x2)/2, y + 0.18, label,
                ha="center", va="bottom", fontsize=8, color=color)

# EC
draw_box(ax_A, 0.2, 1.1, 1.4, 0.8, "Kora\nśródwęchowa", "(EC)", "#5A7FA0")
# LPP
draw_box(ax_A, 1.9, 1.1, 1.5, 0.8, "LPP stymulacja", "(theta pipeta)", "#7A7A7A")
# DG GC
draw_box(ax_A, 3.7, 0.8, 1.6, 1.4, "Granule Cell\n(DG)", "WYJŚCIE = V(t)", "#4C9BE8")
# CA3
draw_box(ax_A, 5.7, 1.1, 1.4, 0.8, "CA3\nPyramidal", "(w gabazynie)", "#E8D44C")
# FSIN
draw_box(ax_A, 3.7, 0.0, 1.6, 0.6, "Fast-Spiking\nInterneuron", "", "#E87F4C")

# Strzałki
draw_arrow(ax_A, 1.6,  1.9, 1.5, "#5A7FA0", "in vivo path")
draw_arrow(ax_A, 3.4,  3.7, 1.5, "#7A7A7A", "elektryczna stymulacja")
draw_arrow(ax_A, 5.3,  5.7, 1.5, "#4C9BE8", "mossy fibers")
ax_A.annotate("", xy=(4.5, 0.8), xytext=(4.5, 0.6),
              arrowprops=dict(arrowstyle="-|>", color="#E87F4C", lw=1.5))

# Etykiety INPUT/OUTPUT
ax_A.text(1.65, 2.3, "INPUT = Poisson spike train\n(R = 0.05 … 1.0, 10 Hz, 2 s)",
          ha="center", fontsize=9, color="#7A7A7A",
          bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))
ax_A.text(4.5, 2.55, "OUTPUT = potencjał błonowy [mV]\n(kanał 0 w .axgd, zawiera spajki)",
          ha="center", fontsize=9, color="#2060A0",
          bbox=dict(boxstyle="round", facecolor="#ddeeff", alpha=0.8))
ax_A.annotate("", xy=(4.5, 2.2), xytext=(4.5, 2.5),
              arrowprops=dict(arrowstyle="-|>", color="#2060A0", lw=1.2))
ax_A.annotate("", xy=(2.65, 2.15), xytext=(2.65, 2.3),
              arrowprops=dict(arrowstyle="-|>", color="#7A7A7A", lw=1.2))

# Pattern separation annotation
ax_A.text(7.2, 1.5,
          "PATTERN SEPARATION:\nR_output < R_input\n(wzorce bardziej różne\nna wyjściu niż wejściu)",
          ha="left", fontsize=9, color="darkgreen",
          bbox=dict(boxstyle="round", facecolor="#dfffdf", alpha=0.85))

# ── Panel B: Liczba plików per folder ───────────────────────────────────────
ax_B = fig.add_subplot(gs_main[1, 0])
folder_names = list(stats.keys())
n_files_list = [stats[f]["n_files"] for f in folder_names]
colors_B = [FOLDER_META.get(f, {}).get("color", "#888888") for f in folder_names]
short_labels = [FOLDER_META.get(f, {}).get("label", f[:12]) for f in folder_names]

bars = ax_B.barh(range(len(folder_names)), n_files_list,
                  color=colors_B, edgecolor="white", linewidth=0.8)
ax_B.set_yticks(range(len(folder_names)))
ax_B.set_yticklabels(short_labels, fontsize=8)
ax_B.set_xlabel("Liczba plików .axgd", fontsize=9)
ax_B.set_title("B)  Pliki .axgd per\ntyp eksperymentu", fontsize=10, fontweight="bold")
for bar, n in zip(bars, n_files_list):
    ax_B.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
              str(n), va="center", fontsize=8)
ax_B.spines[["top", "right"]].set_visible(False)

# ── Panel C: Rozkład wartości R w całym datasecie ────────────────────────────
ax_C = fig.add_subplot(gs_main[1, 1])
all_r = []
for s in stats.values():
    all_r.extend(s["r_values"])

r_bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
counts, edges = np.histogram(all_r, bins=r_bins)
centers = [(edges[i] + edges[i+1])/2 for i in range(len(edges)-1)]
labels_r = [f"{edges[i]:.2f}–{edges[i+1]:.2f}" for i in range(len(edges)-1)]

ax_C.bar(centers, counts, width=0.09,
         color=plt.cm.RdYlGn(np.array(centers)),
         edgecolor="white", linewidth=0.8)
ax_C.set_xlabel("R_input (korelacja wzorców)", fontsize=9)
ax_C.set_ylabel("Liczba nagrań", fontsize=9)
ax_C.set_title("C)  Rozkład R_input\nw całym datasecie", fontsize=10, fontweight="bold")
ax_C.set_xticks([0.05, 0.25, 0.5, 0.75, 0.9, 1.0])
ax_C.spines[["top", "right"]].set_visible(False)

# ── Panel D: Liczba komórek per folder ──────────────────────────────────────
ax_D = fig.add_subplot(gs_main[1, 2])
n_cells_list = [stats[f]["n_cells"] for f in folder_names]
bars_D = ax_D.barh(range(len(folder_names)), n_cells_list,
                    color=colors_B, edgecolor="white", linewidth=0.8)
ax_D.set_yticks(range(len(folder_names)))
ax_D.set_yticklabels(short_labels, fontsize=8)
ax_D.set_xlabel("Liczba unikalnych komórek", fontsize=9)
ax_D.set_title("D)  Komórki\nper typ eksperymentu", fontsize=10, fontweight="bold")
for bar, n in zip(bars_D, n_cells_list):
    ax_D.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
              str(n), va="center", fontsize=8)
ax_D.spines[["top", "right"]].set_visible(False)

# ── Panel E: Tabela — opis każdego folderu ───────────────────────────────────
ax_E = fig.add_subplot(gs_main[2, :])
ax_E.axis("off")
ax_E.set_title("E)  Co zawiera każdy folder — input, output, warunki",
               fontsize=10, fontweight="bold", pad=6)

col_labels = ["Folder", "Typ komórki", "Input (wejście)", "Output (wyjście)",
              "R zakres", "Lek/warunek"]
rows = []
for fname, s in stats.items():
    meta = FOLDER_META.get(fname, {})
    r_rng = (f"{min(s['r_unique']):.2f}–{max(s['r_unique']):.2f}"
             if s["r_unique"] else "—")
    rows.append([
        meta.get("label", fname).replace("\n", " "),
        meta.get("cell_type", "?"),
        f"Poisson spike train\n{meta.get('input_rate','?')} przez LPP",
        "Potencjał błonowy [mV]\n(kanał 0 .axgd)",
        r_rng,
        meta.get("drug", "?"),
    ])

col_widths = [0.13, 0.20, 0.20, 0.18, 0.10, 0.19]
col_positions = [0.0]
for w in col_widths[:-1]:
    col_positions.append(col_positions[-1] + w)

# Nagłówki
for ci, (label, xpos) in enumerate(zip(col_labels, col_positions)):
    ax_E.text(xpos + col_widths[ci]/2, 0.97, label,
              transform=ax_E.transAxes,
              ha="center", va="top", fontsize=8.5, fontweight="bold",
              color="white",
              bbox=dict(boxstyle="square,pad=0.3", facecolor="#2C5F8A", linewidth=0))

# Wiersze
row_height = 0.145
for ri, row in enumerate(rows):
    y = 0.97 - (ri + 1) * row_height
    bg = "#f2f7fc" if ri % 2 == 0 else "white"
    folder_name = list(stats.keys())[ri]
    row_color = FOLDER_META.get(folder_name, {}).get("color", "#888888")

    # Kolorowy pasek po lewej
    ax_E.add_patch(mpatches.FancyBboxPatch(
        (0, y - 0.01), col_widths[0], row_height,
        transform=ax_E.transAxes,
        boxstyle="square,pad=0", facecolor=row_color, alpha=0.25, linewidth=0))

    for ci, (cell, xpos) in enumerate(zip(row, col_positions)):
        ax_E.text(xpos + col_widths[ci]/2, y + row_height/2,
                  cell,
                  transform=ax_E.transAxes,
                  ha="center", va="center", fontsize=7.5,
                  multialignment="center")

fig.suptitle("PatchPatSep2s_Public — Podsumowanie datasetu\n"
             "Patch-clamp nagrania pattern separation w hippocampie (Dentate Gyrus)",
             fontsize=13, fontweight="bold", y=0.98)

out_path = Path(__file__).parent / "dataset_overview.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"\nZapisano rysunek: {out_path}")
plt.show()
