"""
article/build_presentation.py — prezentacja „gdzie jesteśmy" (.pptx, 16:9).

Każdy slajd ma figurę albo wizualny element danych; tekst tylko tyle, ile trzeba,
żeby figura była zrozumiała. Pełne objaśnienie każdego slajdu (co widać, jak
policzone, co znaczy): STATUS.md sek. 7.

Figury pochodzą z article/figures/slides/ (generuje je make_article_figures.py)
oraz — na slajdach zapasowych — z experiments/*/results/. Najpierw figury, potem
deck:

    python article/make_article_figures.py
    python article/build_presentation.py

Wynik: article/prezentacja_stan_prac.pptx
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).parent
REPO = HERE.parent
SL = HERE / "figures" / "slides"
RES_E1 = REPO / "experiments" / "e1_regime_map" / "results"
RES_E2 = REPO / "experiments" / "e2_motif_attribution" / "results"
OUT = HERE / "prezentacja_stan_prac.pptx"

# ── Paleta: granat jako kolor dominujący, cynober (jak w figurach) jako akcent ─
NAVY = RGBColor(0x1B, 0x2A, 0x41)
INK = RGBColor(0x1F, 0x29, 0x33)
MUTED = RGBColor(0x5B, 0x6B, 0x7B)
LIGHT = RGBColor(0xF3, 0xF5, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0xD5, 0x5E, 0x00)      # cynober — ten sam co w figurach
BLUE = RGBColor(0x00, 0x72, 0xB2)
GREEN = RGBColor(0x00, 0x9E, 0x73)
SOFT_ACC = RGBColor(0xFB, 0xEB, 0xDD)    # jasne tło karty rekomendowanej

HEAD = "Cambria"
BODY = "Calibri"

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.55)


# ══════════════════════════════════════════════════════════════════════════════
# Pomocniki
# ══════════════════════════════════════════════════════════════════════════════

def _bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _text(slide, x, y, w, h, runs, *, size=16, color=INK, font=BODY, bold=False,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name=None, margin=0.0,
          line_spacing=None, bullets=False, space_after=6):
    """Pole tekstowe. `runs` = str albo lista akapitów; akapit = str albo lista
    (tekst, {opcje}) do formatowania pojedynczych fragmentów."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    m = Inches(margin)
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = m
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if line_spacing:
            p.line_spacing = line_spacing
        if bullets:
            _bullet(p)
        pieces = para if isinstance(para, list) else [(para, {})]
        for txt, opt in pieces:
            r = p.add_run()
            r.text = txt
            f = r.font
            f.name = opt.get('font', font)
            f.size = Pt(opt.get('size', size))
            f.bold = opt.get('bold', bold)
            f.italic = opt.get('italic', False)
            f.color.rgb = opt.get('color', color)
    return tb


def _bullet(p):
    """Prawdziwy punktor PowerPointa (buChar), a nie znak wklejony w tekst."""
    pPr = p._p.get_or_add_pPr()
    pPr.set('marL', str(Emu(Inches(0.28))))
    pPr.set('indent', str(-Emu(Inches(0.28))))
    for tag in ('a:buNone', 'a:buChar', 'a:buAutoNum'):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    bu = etree.SubElement(pPr, qn('a:buChar'))
    bu.set('char', '•')


def _box(slide, x, y, w, h, fill, *, line=None, radius=0.06, name=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shp.adjustments[0] = radius
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(2)
    shp.shadow.inherit = False
    if name:
        shp.name = name
    return shp


def _picture(slide, path, x, y, max_w, max_h, *, align='center', name=None):
    """Obraz dopasowany do pudełka z zachowaniem proporcji."""
    with Image.open(path) as im:
        ar = im.width / im.height
    w, h = max_w, int(max_w / ar)
    if h > max_h:
        h, w = max_h, int(max_h * ar)
    if align == 'center':
        x = x + (max_w - w) // 2
    pic = slide.shapes.add_picture(str(path), x, y, w, h)
    if name:
        pic.name = name
    return pic


def _title(slide, text, *, tag=None, color=INK):
    """Tytuł zawsze w tym samym miejscu. `tag` = znacznik eksperymentu (E1, E2…)
    w kółku przed tytułem — motyw powtarzany na slajdach eksperymentów."""
    x = MARGIN
    if tag:
        chip = _box(slide, MARGIN, Inches(0.5), Inches(0.95), Inches(0.62), NAVY,
                    radius=0.5, name=f"tag {tag}")
        tf = chip.text_frame
        tf.margin_left = tf.margin_right = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = tag
        r.font.name, r.font.size, r.font.bold = BODY, Pt(20), True
        r.font.color.rgb = WHITE
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        x = MARGIN + Inches(1.15)
    _text(slide, x, Inches(0.38), W - x - MARGIN, Inches(0.9), text,
          size=32, font=HEAD, bold=True, color=color, anchor=MSO_ANCHOR.MIDDLE,
          name="title")


def _num(slide, n, dark=False):
    _text(slide, W - MARGIN - Inches(0.6), H - Inches(0.45), Inches(0.6), Inches(0.3),
          str(n), size=11, color=(WHITE if dark else MUTED), align=PP_ALIGN.RIGHT,
          name="slide number")


def _notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def _qa_column(slide, x, y, w, items):
    """Prawa kolumna slajdu eksperymentu: Pytanie / Jak policzone / Wniosek."""
    cy = y
    for head, body, style in items:
        _text(slide, x, cy, w, Inches(0.32), head.upper(), size=12, bold=True,
              color=(ACCENT if style == 'key' else MUTED), name=f"label {head}")
        cy += Inches(0.34)
        lines = body if isinstance(body, list) else [body]
        n_chars = sum(len(t if isinstance(t, str) else ''.join(s for s, _ in t))
                      for t in lines)
        size = 16 if style == 'key' else 14
        # szacunek wysokości: ~44 znaki/wiersz przy 16 pt w kolumnie 4.4"
        per_line = 40 if size == 16 else 48
        rows = max(1, -(-n_chars // per_line)) + (len(lines) - 1)
        hh = Inches(0.29 * rows * size / 14 + 0.12)
        _text(slide, x, cy, w, hh, lines, size=size,
              color=(INK if style != 'muted' else MUTED),
              bold=False, name=f"text {head}")
        cy += hh + Inches(0.22)
    return cy


def _exp_slide(prs, n, tag, title, fig, items, notes):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    _title(s, title, tag=tag)
    _picture(s, fig, MARGIN, Inches(1.5), Inches(7.55), Inches(5.3), align='left',
             name=f"figure {tag}")
    _qa_column(s, Inches(8.45), Inches(1.6), Inches(4.35), items)
    _num(s, n)
    _notes(s, notes)
    return s


# ══════════════════════════════════════════════════════════════════════════════
# Slajdy
# ══════════════════════════════════════════════════════════════════════════════

def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    blank = prs.slide_layouts[6]
    prs.core_properties.title = "Separacja wzorców w modelu zakrętu zębatego — stan prac"
    prs.core_properties.author = "Jakub Caputa"

    # 1 ── Tytuł ───────────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, NAVY)
    _text(s, MARGIN, Inches(1.7), Inches(6.4), Inches(2.4),
          "Separacja wzorców w modelu zakrętu zębatego",
          size=40, font=HEAD, bold=True, color=WHITE, name="title")
    _text(s, MARGIN, Inches(4.15), Inches(6.2), Inches(1.0),
          "Gdzie jesteśmy: wyniki, pułapki pomiarowe i decyzja o kierunku",
          size=20, color=RGBColor(0xCA, 0xD5, 0xE2), name="subtitle")
    _text(s, MARGIN, Inches(5.7), Inches(6.2), Inches(0.5),
          "Jakub Caputa  ·  październik 2026", size=16,
          color=RGBColor(0xCA, 0xD5, 0xE2), name="author")
    card = _box(s, Inches(7.35), Inches(1.15), Inches(5.45), Inches(5.2), WHITE,
                radius=0.04, name="figure card")
    _picture(s, SL / "fig2-circuit.png", Inches(7.55), Inches(1.35), Inches(5.05),
             Inches(4.8), name="circuit figure")
    _notes(s, "Model sieci spajkującej zakrętu zębatego, związany danymi patch-clamp. "
              "Prezentacja: co ustaliliśmy, co okazało się pułapką pomiarową, "
              "i jaka decyzja jest do podjęcia.")

    # 2 ── W skrócie ───────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, WHITE)
    _title(s, "W skrócie")
    cards = [
        ("obalona", "Hipoteza H1",
         "Separacja nie ma optimum przy pośredniej aktywności. Rośnie po prostu "
         "wtedy, gdy sieć cichnie.", NAVY),
        ("2 z 2", "Punkty odniesienia",
         "Oba naturalne null-e zawodzą — każdy w przeciwną stronę. To główny "
         "wynik metodologiczny.", ACCENT),
        ("−0.23 / +0.22", "Mossy cells",
         "Same pogarszają separację, w parze z hamowaniem pomagają najbardziej. "
         "Jedyny wynik odporny na kontrolę.", GREEN),
    ]
    cw, gap, cy = Inches(3.85), Inches(0.37), Inches(1.75)
    for i, (big, label, body, col) in enumerate(cards):
        cx = MARGIN + i * (cw + gap)
        _box(s, cx, cy, cw, Inches(3.75), LIGHT, name=f"card {label}")
        _text(s, cx + Inches(0.3), cy + Inches(0.3), cw - Inches(0.5), Inches(1.0),
              big, size=30, font=HEAD, bold=True, color=col, name=f"stat {label}")
        _text(s, cx + Inches(0.3), cy + Inches(1.35), cw - Inches(0.6), Inches(0.4),
              label, size=16, bold=True, name=f"label {label}")
        _text(s, cx + Inches(0.3), cy + Inches(1.8), cw - Inches(0.6), Inches(1.8),
              body, size=15, color=MUTED, name=f"body {label}")
    _text(s, MARGIN, Inches(5.95), W - 2 * MARGIN, Inches(0.6),
          [[("Do decyzji: ", {'bold': True, 'color': ACCENT}),
            ("czym jest teza pracy, skoro pierwotna upadła — slajd 12.", {})]],
          size=18, name="bottom line")
    _num(s, 2)
    _notes(s, "Trzy rzeczy do zapamiętania. Pierwotna hipoteza upadła i nie da się jej "
              "uratować ani większą siatką, ani inną miarą. Najciekawszy wynik jest "
              "metodologiczny: z czym porównywać obwód. Na plusie zostaje rola mossy "
              "cells jako motywu warunkowego.")

    # 3 ── Czym jest separacja ─────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, WHITE)
    _title(s, "Czym jest separacja wzorców")
    _picture(s, SL / "fig1-concept.png", MARGIN, Inches(1.55), W - 2 * MARGIN,
             Inches(3.7), name="figure concept")
    _text(s, MARGIN, Inches(5.55), Inches(7.6), Inches(1.4),
          [[("Separacja = spadek korelacji ", {'bold': True}),
            ("między wzorcami po przejściu przez obwód: r_in 0.73 → r_out 0.58.", {})],
           [("Pułapka: ", {'bold': True, 'color': ACCENT}),
            ("ta liczba rośnie sama, gdy sieć cichnie. O tym jest reszta prezentacji.",
             {})]],
          size=17, name="takeaway")
    _text(s, Inches(8.6), Inches(5.6), Inches(4.2), Inches(1.3),
          "Jedna symulacja domyślnej konfiguracji: 200 komórek ziarnistych, "
          "podobieństwo wejść 0.75, 25% komórek napędzanych, 600 ms.",
          size=13, color=MUTED, name="method")
    _num(s, 3)
    _notes(s, "Lewo: dwa wzorce wejściowe, czarne paski to komórki z silnym napędem. "
              "Środek: częstotliwość każdej komórki. Prawo: korelacja wejść i wyjść. "
              "To jest definicja operacyjna całej pracy.")

    # 4 ── Model ───────────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, WHITE)
    _title(s, "Model: obwód i dwie osie hamowania")
    _picture(s, SL / "fig2-circuit.png", MARGIN, Inches(1.45), Inches(6.9),
             Inches(5.5), align='left', name="figure circuit")
    _text(s, Inches(7.85), Inches(1.75), Inches(4.95), Inches(4.8), [
        [("Neurony Izhikevicza w Brian2: ", {'bold': True}),
         ("200 GC, 20 FS, 10 HMC. Wejście z drogi przeszywającej.", {})],
        [("Hamowanie toniczne K_GC: ", {'bold': True, 'color': BLUE}),
         ("stały prąd w równaniu napięcia, zawsze włączony.", {})],
        [("Hamowanie fazowe W_FS→GC: ", {'bold': True, 'color': ACCENT}),
         ("synaptyczne, wyzwalane spajkami interneuronów.", {})],
        [("Trzy motywy do lezji: ", {'bold': True}),
         ("wyprzedzający FF, zwrotny FB i pobudzająca pętla mossy cells MC.", {})],
    ], size=17, bullets=True, space_after=14, name="model bullets")
    _num(s, 4)
    _notes(s, "Rozdzielenie hamowania tonicznego i fazowego to sedno modelu — "
              "w literaturze często zlewa się je w jedno. Trzy motywy można wyłączać "
              "niezależnie, co pozwala zmierzyć wkład każdego.")

    # 5 ── Punkt pracy ─────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, WHITE)
    _title(s, "Punkt pracy jest przypięty danymi")
    _picture(s, SL / "fig3-operating-point.png", MARGIN, Inches(1.5),
             W - 2 * MARGIN, Inches(4.15), name="figure operating point")
    _text(s, MARGIN, Inches(5.85), W - 2 * MARGIN, Inches(1.2), [
        [("Napęd 8 mV < próg 14 mV: ", {'bold': True}),
         ("komórki strzelają tylko na fluktuacjach — stąd rzadki kod.  ", {}),
         ("Ten sam parametr ", {'bold': True}),
         ("daje spoczynek −78.7 mV, w środku zakresu z 42 komórek z danych Madara.", {})],
    ], size=17, name="takeaway")
    _num(s, 5)
    _notes(s, "Oba panele są policzone analitycznie z punktów stałych równania "
              "Izhikevicza i sprawdzone symulacją. Pokazujemy, że model nie jest "
              "dostrojony pod wynik: kluczowy parametr jest związany pomiarem.")

    # 6 ── E1 ──────────────────────────────────────────────────────────────────
    _exp_slide(prs, 6, "E1", "Separacja rośnie, gdy sieć cichnie",
               SL / "slide-e1.png", [
                   ("Pytanie", "Czy separacja ma optimum przy pośrednim poziomie "
                               "aktywności (hipoteza H1)?", 'plain'),
                   ("Jak policzone", "Siatka 10 × 9 parametrów hamowania × 5 seedów "
                                     "= 450 punktów. Separacja wobec zmierzonej "
                                     "frakcji aktywnych komórek.", 'muted'),
                   ("Wniosek", "Optimum nie istnieje. Maksimum zawsze ląduje tuż przy "
                               "progu odrzucania cichych punktów i przesuwa się "
                               "razem z nim — to artefakt miary.", 'key'),
               ],
               "Gwiazdki to maksimum separacji przy czterech różnych progach "
               "odrzucania. Każda siedzi tuż przy swoim progu. Gdyby istniało "
               "optimum biologiczne, gwiazdki stałyby w jednym miejscu.")

    # 7 ── E1′ ─────────────────────────────────────────────────────────────────
    _exp_slide(prs, 7, "E1′", "Hamowanie fazowe nic nie zmienia",
               SL / "slide-e1p.png", [
                   ("Pytanie", "Czy hamowanie fazowe zmienia separację, gdy aktywność "
                               "jest wyrównana?", 'plain'),
                   ("Jak policzone", "Aktywność ustawiona bisekcją na 6 poziomach; "
                                     "9 wartości W_FS→GC × 3 rzadkości wejścia × "
                                     "5 seedów; 733 dostrojone punkty.", 'muted'),
                   ("Wniosek", "Linie są płaskie: wysokość ustala aktywność, nie "
                               "hamowanie (łączne nachylenie −0.003, p = 0.60). "
                               "Efekt z E1 był efektem wyciszenia sieci.", 'key'),
               ],
               "Każda linia to inny zadany poziom aktywności. Linie leżą na różnych "
               "wysokościach, ale żadna nie rośnie z hamowaniem fazowym. Jeśli "
               "cokolwiek, nachylenia są lekko ujemne i żadne nie jest istotne po "
               "korekcie na sześć porównań.")

    # 8 ── Null-e ──────────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, WHITE)
    _title(s, "Z czym w ogóle porównujemy obwód?")
    _picture(s, SL / "fig5-nulls.png", MARGIN, Inches(1.45), W - 2 * MARGIN,
             Inches(3.95), name="figure nulls")
    colw = (W - 2 * MARGIN - Inches(0.4)) // 2
    _box(s, MARGIN, Inches(5.55), colw, Inches(1.35), LIGHT, name="card permutation")
    _text(s, MARGIN + Inches(0.2), Inches(5.65), colw - Inches(0.4), Inches(1.2), [
        [("Permutacja: ", {'bold': True}),
         ("niszczy całą informację o wzorcu, więc r_out = 0. To sufit, którego nic, "
          "co koduje bodziec, nie osiągnie.", {})]], size=15, name="text permutation")
    x2 = MARGIN + colw + Inches(0.4)
    _box(s, x2, Inches(5.55), colw, Inches(1.35), LIGHT, name="card projection")
    _text(s, x2 + Inches(0.2), Inches(5.65), colw - Inches(0.4), Inches(1.2), [
        [("Losowa projekcja: ", {'bold': True}),
         ("z definicji zachowuje korelację (78% r_in). Bicie jej to niska "
          "poprzeczka — a przewaga DG w ~61% to sam próg spajkowania.", {})]],
        size=15, name="text projection")
    _num(s, 8)
    _notes(s, "To jest pointa prezentacji. Żeby powiedzieć, że DG separuje, potrzebny "
              "jest punkt odniesienia o tej samej rzadkości. Dwa naturalne zawodzą w "
              "przeciwne strony i zamiast wyznaczać poziom szansy, obejmują obwód z "
              "dwóch stron. Panel b: obwód bez żadnego hamowania już daje większość "
              "przewagi nad losowym kodem.")

    # 9 ── E2 ──────────────────────────────────────────────────────────────────
    _exp_slide(prs, 9, "E2", "Mossy cells: motyw warunkowy",
               SL / "slide-e2.png", [
                   ("Pytanie", "Który motyw hamowania niesie separację?", 'plain'),
                   ("Jak policzone", "Lezje 2³ = 8 koalicji motywów, wartości "
                                     "Shapleya; 36 punktów statystyki wejścia × "
                                     "5 seedów, przy kanonicznym napędzie.", 'muted'),
                   ("Wniosek", "Mossy cells same szkodzą (−0.23), w parach z "
                               "hamowaniem pomagają najbardziej (+0.21…+0.22). "
                               "Korekta nullem nic nie zmienia.", 'key'),
                   ("Zastrzeżenie", "Przy napędzie ×0.5 efekty są ~4× mniejsze; "
                                    "nie są kontrolowane aktywnością.", 'muted'),
               ],
               "Pełne słupki to wkład liczony na surowej separacji, kreskowane — po "
               "korekcie nullem. Są praktycznie identyczne, bo null nie zależy od "
               "lezji, a wartości Shapleya są niewrażliwe na stałą. To jedyny wynik "
               "pozytywny, który przeszedł kontrolę.")

    # 10 ── 1A ─────────────────────────────────────────────────────────────────
    _exp_slide(prs, 10, "1A", "Odbiorca nie korzysta na DG",
               SL / "slide-1a.png", [
                   ("Pytanie", "Czy klasyfikator liniowy rozpoznaje wzorce lepiej "
                               "po przejściu przez DG?", 'plain'),
                   ("Jak policzone", "Cztery wejścia do tego samego klasyfikatora: "
                                     "surowe, przez DG, DG bez hamowania, losowy kod "
                                     "o tej samej rzadkości.", 'muted'),
                   ("Wniosek", "Nie. DG 0.885 wobec 0.940 dla wejścia; losowy kod "
                               "remisuje z DG, a usunięcie hamowania poprawia "
                               "wynik.", 'key'),
               ],
               "Miara niezależna od korelacji, więc nie podlega pułapce z E1. Wynik "
               "jest spójny z resztą: przewaga DG to głównie rzadkość, a nie "
               "architektura hamowania.")

    # 11 ── Co stoi, co upadło ─────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, WHITE)
    _title(s, "Co upadło, co stoi, co jest nowe")
    cols = [
        ("Upadło", NAVY, [
            "Separacja ma optimum przy pośredniej aktywności",
            "Hamowanie fazowe steruje separacją",
            "DG pomaga odbiorcy liniowemu"]),
        ("Stoi", GREEN, [
            "Punkt pracy zgodny z danymi Madara",
            "Mossy cells jako motyw warunkowy — odporne na null",
            "DG dekoreluje lepiej niż losowy kod rzadki, głównie dzięki progowi"]),
        ("Metodologia", ACCENT, [
            "Oba naturalne null-e zawodzą, w przeciwne strony",
            "Próg odrzucania cichych punktów przesuwa maksimum",
            "Retencja informacji idzie za rzadkością wejścia"]),
    ]
    cw, gap = Inches(3.85), Inches(0.37)
    for i, (head, col, items) in enumerate(cols):
        cx = MARGIN + i * (cw + gap)
        _box(s, cx, Inches(1.6), cw, Inches(4.95), LIGHT, name=f"column {head}")
        _text(s, cx + Inches(0.3), Inches(1.85), cw - Inches(0.6), Inches(0.5),
              head, size=22, font=HEAD, bold=True, color=col, name=f"head {head}")
        _text(s, cx + Inches(0.3), Inches(2.55), cw - Inches(0.6), Inches(3.8),
              items, size=16, bullets=True, space_after=14, name=f"items {head}")
    _num(s, 11)
    _notes(s, "Podsumowanie. Lewa kolumna: czego już nie da się obronić w żadnym "
              "wariancie. Środkowa: co można cytować. Prawa: wyniki metodologiczne, "
              "których w literaturze o separacji wzorców nie ma.")

    # 12 ── Decyzja ────────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, WHITE)
    _title(s, "Decyzja: czym jest teza pracy")
    opts = [
        ("(a)", "Artykuł metodologiczny",
         "Jak nie mierzyć separacji. Dowód: komplet. Koszt: samo pisanie.", False),
        ("(b)", "Mossy cells: motyw warunkowy",
         "Dowód: Shapley. Ryzyko: efekt zależy od napędu i nie jest kontrolowany aktywnością.", False),
        ("(c)", "Regulacja zamiast separacji",
         "Kontroler adaptacyjny. Dowód: brak. Koszt: nowy moduł, miesiące.", False),
        ("(d)", "Padaczka: utrata mossy cells",
         "Przepisana przez sam plan (bramka G2). Koszt: jeden sweep.", True),
    ]
    cw, ch = Inches(5.95), Inches(2.05)
    for i, (k, head, body, rec) in enumerate(opts):
        cx = MARGIN + (i % 2) * (cw + Inches(0.33))
        cy = Inches(1.6) + (i // 2) * (ch + Inches(0.3))
        _box(s, cx, cy, cw, ch, (SOFT_ACC if rec else LIGHT),
             line=(ACCENT if rec else None), name=f"option {k}")
        _text(s, cx + Inches(0.3), cy + Inches(0.25), Inches(0.8), Inches(0.6), k,
              size=26, font=HEAD, bold=True, color=(ACCENT if rec else NAVY),
              name=f"key {k}")
        _text(s, cx + Inches(1.1), cy + Inches(0.28), cw - Inches(1.4), Inches(0.5),
              head, size=19, bold=True, name=f"head {k}")
        _text(s, cx + Inches(1.1), cy + Inches(0.85), cw - Inches(1.4), Inches(1.1),
              body, size=15, color=MUTED, name=f"body {k}")
    _text(s, MARGIN, Inches(6.55), W - 2 * MARGIN, Inches(0.5),
          [[("Rekomendacja: ", {'bold': True, 'color': ACCENT}),
            ("(d) jako teza nośna + (a) jako osobny, krótszy artykuł.", {})]],
          size=18, name="recommendation")
    _num(s, 12)
    _notes(s, "Wariant d nie jest naszym pomysłem: plan badawczy przewidywał, że jeśli "
              "H1 nie przejdzie, przechodzimy na odporność i padaczkę. Mossy cells to "
              "jedyny motyw o dużych efektach, a spór dormant basket cell kontra "
              "irritable mossy cell jest otwarty, więc wynik będzie publikowalny "
              "niezależnie od znaku.")

    # 13 ── Następne kroki ─────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    _bg(s, WHITE)
    _title(s, "Następne kroki")
    steps = [
        ("Decyzja o tezie", "Wybór wariantu ze slajdu 12; dopiero po nim "
                            "przepisanie hipotez w planie."),
        ("Trzy pytania kalibracyjne", "Udział hamowania tonicznego (~74%), "
                                      "częstotliwość FS (~46 Hz), reżim kalibracji: "
                                      "in vitro czy in vivo."),
        ("Bodźce z eksperymentu", "Protokoły Madara jako wejście modelu — przydatne "
                                  "w każdym wariancie."),
        ("Draft artykułu o narzędziu", "Kompilacja na Overleafie i uzupełnienie "
                                       "brakujących elementów."),
        ("Osobna ścieżka ML", "Rzadkość jako trzeci czynnik uczenia — propozycja, "
                              "bez wyników."),
    ]
    for i, (head, body) in enumerate(steps):
        cy = Inches(1.6) + i * Inches(1.0)
        circ = s.shapes.add_shape(MSO_SHAPE.OVAL, MARGIN, cy, Inches(0.6), Inches(0.6))
        circ.name = f"step {i + 1}"
        circ.fill.solid()
        circ.fill.fore_color.rgb = (ACCENT if i == 0 else NAVY)
        circ.line.fill.background()
        tf = circ.text_frame
        tf.margin_left = tf.margin_right = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = str(i + 1)
        r.font.name, r.font.size, r.font.bold = BODY, Pt(18), True
        r.font.color.rgb = WHITE
        _text(s, MARGIN + Inches(0.85), cy - Inches(0.02), Inches(3.6), Inches(0.65),
              head, size=18, bold=True, anchor=MSO_ANCHOR.MIDDLE, name=f"head {i + 1}")
        _text(s, MARGIN + Inches(4.55), cy - Inches(0.02), Inches(7.7), Inches(0.65),
              body, size=15, color=MUTED, anchor=MSO_ANCHOR.MIDDLE,
              name=f"body {i + 1}")
    _num(s, 13)
    _notes(s, "Krok pierwszy blokuje resztę. Pytania kalibracyjne są wysłane do prof. "
              "Błasiak. Bodźce z eksperymentu warto zrobić niezależnie od decyzji.")

    # 14–16 ── Zapas: gęste figury analityczne na pytania z sali ───────────────
    backups = [
        ("Zapas: E1 — pełna mapa reżimów", RES_E1 / "regime_map_full.png",
         "Panel c: separacja zmienia się niemal wyłącznie wzdłuż osi hamowania "
         "tonicznego (pionowo), prawie wcale wzdłuż fazowego. Panel d: kurs wymiany "
         "separacja–informacja jest gładki, bez wyróżnionego punktu."),
        ("Zapas: E1′ — kontrola dostrojenia", RES_E1 / "matched_activity_full.png",
         "Panel d: czy bisekcja trafiła w zadaną aktywność. 77 z 810 punktów było "
         "poza zasięgiem i jest wykluczonych. Panel c: maksimum retencji idzie za "
         "rzadkością wejścia — tautologia estymatora."),
        ("Zapas: E2 — profile wkładów motywów", RES_E2 / "fig2_shapley_profiles.png",
         "Wkłady motywów w funkcji podobieństwa i rzadkości wejścia. Mossy cells są "
         "martwe przy domyślnych wagach (górny rząd), stąd dwa reżimy w każdym "
         "sweepie."),
    ]
    for j, (title, path, cap) in enumerate(backups):
        s = prs.slides.add_slide(blank)
        _bg(s, WHITE)
        _title(s, title, color=MUTED)
        _picture(s, path, MARGIN, Inches(1.4), W - 2 * MARGIN, Inches(4.95),
                 name="backup figure")
        _text(s, MARGIN, Inches(6.45), W - 2 * MARGIN, Inches(0.7), cap, size=14,
              color=MUTED, name="caption")
        _num(s, 14 + j)
        _notes(s, "Slajd zapasowy na pytania z sali. " + cap)

    prs.save(OUT)
    print(f"zapisano {OUT}  ({len(prs.slides)} slajdów)")


if __name__ == '__main__':
    build()
