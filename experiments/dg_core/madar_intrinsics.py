"""
dg_core/madar_intrinsics.py — właściwości błony z danych Madara, per typ komórki.

Po co
-----
Prof. Błasiak pyta o natywne właściwości błony GC (τ, V_rest, próg). Dotąd
odpowiadaliśmy wartościami wziętymi z modelu. Tutaj bierzemy je Z DANYCH.

Skąd to się bierze — i dlaczego tak tanio
------------------------------------------
Madar opisał właściwości KAŻDEJ komórki wprost w swoich plikach MATLAB
(`dataset/PatSepSpikeTrains/NameFiles/*.m`) — jako pola `Vrest`, `Rm`, `Cm`, `Rs`
albo jako komentarze `% Vrest = -51mV; Rm = 120MOhm; Cm = 30pF`. To jest gotowy
pomiar eksperymentatora, więc nie musimy go odtwarzać z surowego sygnału:
żadnej detekcji spajków, żadnego dopasowywania krzywych, zero decyzji
analitycznych, które recenzent mógłby zakwestionować.

⚠️ **Kluczowa pułapka: ta sama komórka powtarza się pod wieloma warunkami R.**
Pliki indeksują nagrania, nie komórki. Bez deduplikacji po polu `ID` liczebności
byłyby zawyżone kilkukrotnie, a rozkłady — obciążone w stronę komórek, które
nagrano w większej liczbie warunków. Deduplikujemy po (typ komórki, ID).

Co to daje kalibracji
---------------------
1. **τ_m = Rm · Cm** — jedyny parametr z zestawu prof. Błasiak, którego model
   Izhikevicza nie ma jawnie. Tu dostajemy jego rozkład z pomiaru.
2. **V_rest** — wprost porównywalne z punktem stałym modelu (`calibrate.izh_fixed_points`).
3. **Rozkłady, nie punkty** — czyli podstawa pod heterogeniczną populację
   zamiast identycznych klonów.
4. **Dane dla FS**, których NIE DA SIĘ dostać z ramp prądowych — w zestawie
   `GCandFS_yo_P10Hz_1` nie ma ani jednego pliku CCIV.

Użycie
------
    python -m dg_core.madar_intrinsics            # z katalogu experiments/
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# NameFiles → typ komórki. Jeden plik może opisywać jeden typ; nazwy są Madara.
FILE_CELL_TYPE = {
    'PatSepFileListAllGC_2010toDec2015.m': 'GC',
    'PatSepFilesBeforeGabazine.m':         'GC',
    'PatSepFilesAfterGabazine.m':          'GC',
    'PatSepFiles_DGGCctrl_gzine_30Hz.m':   'GC',
    'PatSepFilesFalconHawk_SFrange_Sa.m':  'GC',
    'PatSepFilesListFS.m':                 'FS',
    'PatSepHilarMossyCells.m':             'HMC',
    'PatSepFiles_CA3_gzine_30Hz.m':        'CA3',
}

_REPO = Path(__file__).resolve().parents[2]
NAMEFILES_DIR = _REPO / 'dataset' / 'PatSepSpikeTrains' / 'NameFiles'

# ── Wzorce trzech formatów, w jakich Madar zapisał te same wielkości ──────────
# 1) skalarny:  Vrest{1}(3) = -60;
_SCALAR = re.compile(r'(Vrest|Rm|Cm|Rs|ID)\{(\d+)\}\((\d+)\)\s*=\s*(-?[\d.]+|NaN)')
# 2) tablicowy: Vrest{1} = [-68, -72, -55, -72];
_ARRAY = re.compile(r'(Vrest|Rm|Cm|Rs|ID)\{(\d+)\}\s*=\s*\[([^\]]*)\]')
# 3) komentarz: % Vrest = -51mV; Rm = 120MOhm; Cm = 30pF
_COMMENT = re.compile(
    r'Vrest\s*=\s*(-?[\d.]+)\s*mV.*?'
    r'(?:Rm\s*=\s*([\d.]+)\s*MOhm)?.*?'
    r'(?:Cm\s*=\s*([\d.]+)\s*pF)?', re.IGNORECASE)


@dataclass
class Cell:
    """Jedna komórka — nie jedno nagranie."""
    cell_type: str
    cid: str              # identyfikator w obrębie typu (z pola ID albo z pozycji)
    v_rest: float = float('nan')
    rm_mohm: float = float('nan')
    cm_pf: float = float('nan')

    @property
    def tau_m_ms(self) -> float:
        """τ_m = Rm · Cm  [MΩ · pF = µs] → ms."""
        return self.rm_mohm * self.cm_pf * 1e-3


def _to_f(s: str) -> float:
    s = s.strip()
    return float('nan') if s.upper() == 'NAN' or not s else float(s)


def parse_namefile(path: Path, cell_type: str) -> dict[str, Cell]:
    """Wyciąga komórki z jednego pliku .m, kluczowane po ID (deduplikacja)."""
    text = path.read_text(encoding='utf-8', errors='replace')
    # (grupa, indeks) → {pole: wartość};  grupa = warunek R, indeks = pozycja
    slots: dict[tuple[str, str], dict[str, float]] = {}

    for field, grp, idx, val in _SCALAR.findall(text):
        slots.setdefault((grp, idx), {})[field] = _to_f(val)

    for field, grp, body in _ARRAY.findall(text):
        for i, tok in enumerate(body.split(',')):
            slots.setdefault((grp, str(i + 1)), {})[field] = _to_f(tok)

    cells: dict[str, Cell] = {}
    for (grp, idx), f in slots.items():
        # ID jest właściwym identyfikatorem komórki; bez niego fallback na pozycję,
        # ale wtedy deduplikacja jest słabsza i trzeba to wiedzieć.
        cid = str(int(f['ID'])) if not np.isnan(f.get('ID', float('nan'))) else f'{grp}_{idx}'
        c = cells.setdefault(cid, Cell(cell_type, cid))
        for src, dst in (('Vrest', 'v_rest'), ('Rm', 'rm_mohm'), ('Cm', 'cm_pf')):
            v = f.get(src, float('nan'))
            if not np.isnan(v) and np.isnan(getattr(c, dst)):
                setattr(c, dst, v)

    # Format komentarzowy (HMC) — tylko dla komórek, których nie złapały wzorce 1–2.
    if not cells:
        for i, line in enumerate(text.splitlines()):
            if 'Vrest' not in line:
                continue
            m = _COMMENT.search(line)
            if m:
                cells[f'c{i}'] = Cell(
                    cell_type, f'c{i}',
                    _to_f(m.group(1)),
                    _to_f(m.group(2)) if m.group(2) else float('nan'),
                    _to_f(m.group(3)) if m.group(3) else float('nan'))
    return cells


def load_all(namefiles_dir: Path = NAMEFILES_DIR) -> list[Cell]:
    """Wszystkie komórki ze wszystkich NameFiles, zdeduplikowane po (typ, ID)."""
    if not namefiles_dir.is_dir():
        raise FileNotFoundError(f"Brak katalogu NameFiles: {namefiles_dir}")
    by_key: dict[tuple[str, str], Cell] = {}
    for fname, ctype in FILE_CELL_TYPE.items():
        p = namefiles_dir / fname
        if not p.exists():
            continue
        for cid, cell in parse_namefile(p, ctype).items():
            key = (ctype, cid)
            if key not in by_key:
                by_key[key] = cell
            else:  # uzupełnij brakujące pola z innego pliku opisującego tę samą komórkę
                for attr in ('v_rest', 'rm_mohm', 'cm_pf'):
                    if np.isnan(getattr(by_key[key], attr)):
                        setattr(by_key[key], attr, getattr(cell, attr))
    return list(by_key.values())


def summarize(cells: list[Cell]) -> dict[str, dict]:
    """Mediana i IQR per typ komórki. Mediana, nie średnia — rozkłady są skośne."""
    out = {}
    for ctype in ('GC', 'FS', 'HMC', 'CA3'):
        sub = [c for c in cells if c.cell_type == ctype]
        if not sub:
            continue
        stats = {'n_cells': len(sub)}
        for label, vals in (
            ('V_rest [mV]', [c.v_rest for c in sub]),
            ('Rm [MΩ]', [c.rm_mohm for c in sub]),
            ('Cm [pF]', [c.cm_pf for c in sub]),
            ('tau_m [ms]', [c.tau_m_ms for c in sub]),
        ):
            a = np.array(vals, dtype=float)
            a = a[np.isfinite(a)]
            stats[label] = (
                {'n': len(a), 'median': float(np.median(a)),
                 'q1': float(np.percentile(a, 25)), 'q3': float(np.percentile(a, 75)),
                 'min': float(a.min()), 'max': float(a.max())}
                if len(a) else {'n': 0}
            )
        out[ctype] = stats
    return out


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    cells = load_all()
    summ = summarize(cells)

    print("\n" + "═" * 78)
    print("  WŁAŚCIWOŚCI BŁONY Z DANYCH MADARA  (mediana [IQR], po deduplikacji komórek)")
    print("═" * 78)
    print(f"  {'typ':<6}{'n':>5}  {'V_rest [mV]':>22}{'tau_m [ms]':>22}{'Rm [MΩ]':>18}")
    print("  " + "─" * 74)
    for ctype, s in summ.items():
        def fmt(key):
            d = s[key]
            return f"{d['median']:.0f} [{d['q1']:.0f}–{d['q3']:.0f}] n={d['n']}" if d['n'] else "—"
        print(f"  {ctype:<6}{s['n_cells']:>5}  {fmt('V_rest [mV]'):>22}"
              f"{fmt('tau_m [ms]'):>22}{fmt('Rm [MΩ]'):>18}")

    print("\n  ODNIESIENIE DO MODELU:")
    gc = summ.get('GC', {})
    if gc and gc.get('V_rest [mV]', {}).get('n'):
        d = gc['V_rest [mV]']
        print(f"    • V_rest GC zmierzone: mediana {d['median']:.0f} mV, "
              f"zakres {d['min']:.0f}…{d['max']:.0f} mV")
        print(f"      Model przy K_GC=10 daje −78.7 mV, przy K_GC=0 daje −70.0 mV.")
    if gc and gc.get('tau_m [ms]', {}).get('n'):
        d = gc['tau_m [ms]']
        print(f"    • τ_m GC zmierzone: mediana {d['median']:.0f} ms "
              f"[{d['q1']:.0f}–{d['q3']:.0f}]")
        print(f"      Izhikevich NIE MA jawnego τ_m; jego szybka składowa to ~1 ms,")
        print(f"      a całkowanie czasowe w sieci niosą stałe synaptyczne (5/8 ms).")
        print(f"      To jest realna rozbieżność modelu z danymi, do opisania w Methods.")
    print("═" * 78 + "\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
