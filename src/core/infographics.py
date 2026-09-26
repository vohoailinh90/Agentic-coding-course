"""Render infographic specs (course/data/diagrams/*.yaml) to one SVG per language.

One spec holds the text in every course language; each language gets its own
SVG, so a diagram is drawn once and never drifts between translations. SVG is
text: it diffs in Git, stays sharp at any size, and GitHub shows it in Markdown.

Design rules, shared by every template:
- A solid light card as background, so the picture reads the same in GitHub's
  light and dark themes.
- Every colour, font and size is an attribute, so the static picture is complete
  even where CSS is ignored. The only <style> is optional motion (flowing arrows,
  a gently pulsing result) that stops under prefers-reduced-motion.
- Short labels only; boxes grow to fit wrapped text, never overflow sideways.
- `<title>` and `<desc>` carry the diagram in words for screen readers.
- Output is deterministic, so CI can tell a stale file from a current one.

Templates: compare, equation, cycle, flow; plus `render_roadmap` for the course
journey map, drawn from curriculum.yaml rather than from a spec.
"""

from __future__ import annotations

import math
from html import escape

from src.core.textfit import widest, wrap

WIDTH = 800
MARGIN = 28
INNER = WIDTH - 2 * MARGIN
# Latin fonts first for Vietnamese and English (so their letters never come from a
# Japanese font, whose Latin glyphs are often fixed-width); Japanese fonts first for
# Japanese. Each list falls back through the other script's fonts glyph by glyph.
LATIN_FONTS = "'Segoe UI', 'Noto Sans', 'Helvetica Neue', Arial, 'Liberation Sans'"
JAPANESE_FONTS = ("'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic UI', 'Yu Gothic', Meiryo, "
                  "'Noto Sans JP', 'Noto Sans CJK JP', IPAPGothic")


def font_family(lang: str) -> str:
    first, second = (JAPANESE_FONTS, LATIN_FONTS) if lang == "ja" else (LATIN_FONTS, JAPANESE_FONTS)
    return f"{first}, {second}, sans-serif"


EMOJI_FONT = "'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif"
INK = "#0F172A"
MUTED = "#475569"
FAINT = "#64748B"
LINE = "#E2E8F0"
LINE_HEIGHT = 1.32

# accent: strokes and badges · tint: card fill · soft: dividers and rows · deep: headings on tint
PALETTE: dict[str, dict[str, str]] = {
    "blue": {"accent": "#2563EB", "tint": "#EFF6FF", "soft": "#DBEAFE", "deep": "#1E3A8A"},
    "violet": {"accent": "#7C3AED", "tint": "#F5F3FF", "soft": "#EDE9FE", "deep": "#4C1D95"},
    "green": {"accent": "#059669", "tint": "#ECFDF5", "soft": "#D1FAE5", "deep": "#064E3B"},
    "amber": {"accent": "#D97706", "tint": "#FFFBEB", "soft": "#FEF3C7", "deep": "#78350F"},
    "rose": {"accent": "#E11D48", "tint": "#FFF1F2", "soft": "#FFE4E6", "deep": "#881337"},
    "teal": {"accent": "#0D9488", "tint": "#F0FDFA", "soft": "#CCFBF1", "deep": "#134E4A"},
    "orange": {"accent": "#EA580C", "tint": "#FFF7ED", "soft": "#FFEDD5", "deep": "#7C2D12"},
    "indigo": {"accent": "#4F46E5", "tint": "#EEF2FF", "soft": "#E0E7FF", "deep": "#312E81"},
    "pink": {"accent": "#DB2777", "tint": "#FDF2F8", "soft": "#FCE7F3", "deep": "#831843"},
    "slate": {"accent": "#475569", "tint": "#F8FAFC", "soft": "#E2E8F0", "deep": "#0F172A"},
}
# Colours given to modules on the roadmap, in order.
MODULE_COLORS = ("blue", "violet", "green", "amber", "rose", "teal", "orange", "indigo", "pink")

TEMPLATES = ("compare", "equation", "cycle", "flow")
MOTION = """
.flow { animation: flow 1.4s linear infinite; }
.pulse { animation: pulse 2.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }
@keyframes flow { to { stroke-dashoffset: -36; } }
@keyframes pulse { 50% { transform: scale(1.035); } }
@media (prefers-reduced-motion: reduce) { .flow, .pulse { animation: none; } }
""".strip()


def _n(value: float) -> str:
    """A coordinate with at most one decimal, so the output is stable and small."""
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


class Canvas:
    """Collects SVG markup, then wraps it in the shared frame."""

    def __init__(self, lang: str) -> None:
        self.lang = lang
        self.parts: list[str] = []
        self.defs: list[str] = []
        self.motion = False

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def text(self, lines: list[str], x: float, top: float, size: float, *, fill: str = INK,
             anchor: str = "middle", bold: bool = False, css: str = "") -> float:
        """Draw lines of text whose first line box starts at `top`; return the block height."""
        if not lines:
            return 0.0
        weight = ' font-weight="700"' if bold else ""
        klass = f' class="{css}"' if css else ""
        spans = []
        for index, line in enumerate(lines):
            baseline = top + size * LINE_HEIGHT * index + size * (LINE_HEIGHT - 1) / 2 + size * 0.84
            spans.append(f'<tspan x="{_n(x)}" y="{_n(baseline)}">{escape(line)}</tspan>')
        self.add(f'<text font-size="{_n(size)}" fill="{fill}" text-anchor="{anchor}"{weight}{klass}>'
                 + "".join(spans) + "</text>")
        return block(len(lines), size)

    def icon(self, icon: str, cx: float, cy: float, radius: float, color: str) -> None:
        tone = PALETTE[color]
        self.add(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(radius)}" fill="{tone["accent"]}"/>')
        self.add(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(radius - 3)}" fill="#FFFFFF" fill-opacity="0.2"/>')
        size = radius * 1.05
        self.add(f'<text x="{_n(cx)}" y="{_n(cy + size * 0.36)}" font-size="{_n(size)}" text-anchor="middle" '
                 f'font-family="{EMOJI_FONT}">{escape(icon)}</text>')

    def arrow_marker(self, name: str, color: str) -> str:
        marker_id = f"arrow-{name}"
        self.defs.append(
            f'<marker id="{marker_id}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>'
        )
        return marker_id

    def svg(self, height: float, title: str, desc: str) -> str:
        height = math.ceil(height)
        defs = [
            '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#F1F5F9"/></linearGradient>',
            *self.defs,
        ]
        head = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" '
            f'height="{height}" role="img" aria-labelledby="title desc" font-family="{font_family(self.lang)}" '
            f'lang="{self.lang}">',
            f'<title id="title">{escape(title)}</title>',
            f'<desc id="desc">{escape(desc)}</desc>',
        ]
        if self.motion:
            head.append(f"<style>\n{MOTION}\n</style>")
        head.append("<defs>" + "".join(defs) + "</defs>")
        frame = [
            f'<rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="24" fill="url(#bg)" '
            f'stroke="{LINE}" stroke-width="2"/>',
            f'<circle cx="{WIDTH - 40}" cy="36" r="90" fill="{PALETTE["violet"]["accent"]}" fill-opacity="0.06"/>',
            f'<circle cx="46" cy="{height - 30}" r="110" fill="{PALETTE["blue"]["accent"]}" fill-opacity="0.05"/>',
        ]
        return "\n".join(head + frame + self.parts + ["</svg>"]) + "\n"


def block(lines: int, size: float) -> float:
    """Height of `lines` lines of text at `size`."""
    return lines * size * LINE_HEIGHT


def _header(canvas: Canvas, spec: dict, lang: str) -> float:
    """Title and optional subtitle; returns the y where content starts."""
    y = 26.0
    y += canvas.text(wrap(spec["title"][lang], INNER - 40, 29, bold=True), WIDTH / 2, y, 29, bold=True)
    if spec.get("subtitle"):
        y += 4
        y += canvas.text(wrap(spec["subtitle"][lang], INNER - 60, 17), WIDTH / 2, y, 17, fill=MUTED)
    return y + 22


def _takeaway(canvas: Canvas, spec: dict, lang: str, y: float) -> float:
    """The optional one-line lesson under the diagram; returns the new bottom."""
    if not spec.get("takeaway"):
        return y
    size = 18
    lines = wrap("💡 " + spec["takeaway"][lang], INNER - 56, size, bold=True)
    height = block(len(lines), size) + 26
    tone = PALETTE["amber"]
    canvas.add(f'<rect x="{MARGIN}" y="{_n(y)}" width="{INNER}" height="{_n(height)}" rx="16" '
               f'fill="{tone["tint"]}" stroke="{tone["accent"]}" stroke-width="1.5"/>')
    canvas.text(lines, WIDTH / 2, y + 13, size, fill=tone["deep"], bold=True)
    return y + height + 20


def describe(spec: dict, lang: str) -> str:
    """The diagram in words, for <desc> and alt text."""
    parts: list[str] = []
    template = spec["template"]
    if template == "compare":
        for column in spec["columns"]:
            values = "; ".join(f"{row[lang]}: {value[lang]}" for row, value in zip(spec["rows"], column["values"]))
            parts.append(f"{column['name'][lang]} — {values}")
    elif template == "equation":
        terms = " + ".join(term["name"][lang] for term in spec["terms"])
        parts.append(f"{terms} = {spec['result']['name'][lang]}")
    else:
        parts.append(" → ".join(step["name"][lang] for step in spec["steps"]))
    if spec.get("takeaway"):
        parts.append(spec["takeaway"][lang])
    return ". ".join(parts)


# ---------------------------------------------------------------------------
# compare — columns side by side over shared row labels
# ---------------------------------------------------------------------------


def _compare(canvas: Canvas, spec: dict, lang: str, y: float) -> float:
    columns = spec["columns"]
    count = len(columns)
    versus = bool(spec.get("versus")) and count == 2
    gap = 64 if versus else 18
    width = (INNER - gap * (count - 1)) / count
    pad = 16
    text_w = width - 2 * pad
    emphasis = spec.get("emphasis_row")

    names = [wrap(column["name"][lang], text_w, 21, bold=True) for column in columns]
    badges = [wrap(column["badge"][lang], text_w - 20, 13, bold=True) if column.get("badge") else [] for column in columns]
    header_h = 30 + 44 + 10 + max(block(len(lines), 21) for lines in names) + 16
    row_layout = []
    for index, row in enumerate(spec["rows"], start=1):
        size = 19 if emphasis == index else 17
        labels = [wrap(row[lang], text_w, 13.5, bold=True) for _ in columns]
        values = [wrap(column["values"][index - 1][lang], text_w, size, bold=emphasis == index) for column in columns]
        height = 14 + max(block(len(lines), 13.5) for lines in labels) + 4 + max(block(len(v), size) for v in values) + 14
        row_layout.append((index, size, labels, values, height))
    card_h = header_h + sum(item[4] for item in row_layout) + 8

    for position, column in enumerate(columns):
        tone = PALETTE[column["color"]]
        x = MARGIN + position * (width + gap)
        highlight = bool(column.get("highlight"))
        stroke = f'stroke="{tone["accent"]}" stroke-width="{3.5 if highlight else 1.5}"'
        pulse = ' class="pulse"' if highlight else ""
        if highlight:
            canvas.motion = True
        canvas.add(f'<g{pulse}>')
        canvas.add(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(width)}" height="{_n(card_h)}" rx="20" '
                   f'fill="{tone["tint"]}" {stroke}/>')
        canvas.add(f'<path d="M{_n(x)},{_n(y + 20)} a20,20 0 0 1 20,-20 h{_n(width - 40)} a20,20 0 0 1 20,20 '
                   f'v{_n(header_h - 20)} h{_n(-width)} z" fill="{tone["accent"]}"/>')
        canvas.icon(column["icon"], x + width / 2, y + 30 + 22, 26, column["color"])
        canvas.text(names[position], x + width / 2, y + 30 + 44 + 10, 21, fill="#FFFFFF", bold=True)
        if badges[position]:
            badge_w = widest(badges[position], 13, bold=True) + 22
            badge_h = block(len(badges[position]), 13) + 8
            canvas.add(f'<rect x="{_n(x + width / 2 - badge_w / 2)}" y="{_n(y - badge_h / 2)}" '
                       f'width="{_n(badge_w)}" height="{_n(badge_h)}" rx="{_n(badge_h / 2)}" fill="{INK}"/>')
            canvas.text(badges[position], x + width / 2, y - badge_h / 2 + 4, 13, fill="#FFFFFF", bold=True)
        row_y = y + header_h
        for index, size, labels, values, height in row_layout:
            if index > 1:
                canvas.add(f'<line x1="{_n(x + pad)}" y1="{_n(row_y)}" x2="{_n(x + width - pad)}" y2="{_n(row_y)}" '
                           f'stroke="{tone["soft"]}" stroke-width="2"/>')
            top = row_y + 14
            top += canvas.text(labels[position], x + pad, top, 13.5, fill=FAINT, anchor="start", bold=True) + 4
            fill = tone["accent"] if emphasis == index else INK
            canvas.text(values[position], x + pad, top, size, fill=fill, anchor="start", bold=emphasis == index)
            row_y += height
        canvas.add("</g>")

    if versus:
        cx, cy = MARGIN + width + gap / 2, y + header_h / 2 + 8
        canvas.add(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="25" fill="{INK}"/>')
        canvas.add(f'<text x="{_n(cx)}" y="{_n(cy + 6)}" font-size="17" font-weight="700" fill="#FFFFFF" '
                   f'text-anchor="middle">VS</text>')
    return y + card_h + 24


# ---------------------------------------------------------------------------
# equation — terms joined by "+", and a result below them
# ---------------------------------------------------------------------------


def _term_card(canvas: Canvas, item: dict, lang: str, x: float, y: float, width: float, height: float,
               *, highlight: bool = False) -> None:
    tone = PALETTE[item["color"]]
    pad = 14
    if highlight:
        canvas.motion = True
        canvas.add('<g class="pulse">')
    canvas.add(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(width)}" height="{_n(height)}" rx="20" '
               f'fill="{tone["tint"]}" stroke="{tone["accent"]}" stroke-width="{3.5 if highlight else 2}"/>')
    canvas.icon(item["icon"], x + width / 2, y + 16 + 28, 28, item["color"])
    top = y + 16 + 56 + 10
    top += canvas.text(wrap(item["name"][lang], width - 2 * pad, 20, bold=True), x + width / 2, top, 20,
                       fill=tone["deep"], bold=True)
    if item.get("caption"):
        canvas.text(wrap(item["caption"][lang], width - 2 * pad, 15.5), x + width / 2, top + 4, 15.5, fill=MUTED)
    if highlight:
        canvas.add("</g>")


def _card_height(item: dict, lang: str, width: float) -> float:
    pad = 14
    height = 16 + 56 + 10 + block(len(wrap(item["name"][lang], width - 2 * pad, 20, bold=True)), 20)
    if item.get("caption"):
        height += 4 + block(len(wrap(item["caption"][lang], width - 2 * pad, 15.5)), 15.5)
    return height + 18


def _operator(canvas: Canvas, symbol: str, cx: float, cy: float) -> None:
    canvas.add(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="17" fill="#FFFFFF" stroke="{LINE}" stroke-width="2"/>')
    canvas.add(f'<text x="{_n(cx)}" y="{_n(cy + 8)}" font-size="24" font-weight="700" fill="{MUTED}" '
               f'text-anchor="middle">{escape(symbol)}</text>')


def _equation(canvas: Canvas, spec: dict, lang: str, y: float) -> float:
    terms = spec["terms"]
    gap = 44
    width = (INNER - gap * (len(terms) - 1)) / len(terms)
    height = max(_card_height(term, lang, width) for term in terms)
    for index, term in enumerate(terms):
        x = MARGIN + index * (width + gap)
        _term_card(canvas, term, lang, x, y, width, height)
        if index:
            _operator(canvas, "+", x - gap / 2, y + height / 2)
    # the "=" connector: a short downward arrow into the result
    top = y + height + 12
    marker = canvas.arrow_marker("result", MUTED)
    canvas.motion = True
    canvas.add(f'<line x1="{WIDTH / 2}" y1="{_n(top)}" x2="{WIDTH / 2}" y2="{_n(top + 46)}" stroke="{MUTED}" '
               f'stroke-width="3" stroke-dasharray="9 9" class="flow" marker-end="url(#{marker})"/>')
    _operator(canvas, "=", WIDTH / 2 + 40, top + 24)
    result_w = min(INNER, max(360.0, width * 1.6))
    result_h = _card_height(spec["result"], lang, result_w)
    result_y = top + 58
    _term_card(canvas, spec["result"], lang, WIDTH / 2 - result_w / 2, result_y, result_w, result_h, highlight=True)
    return result_y + result_h + 24


# ---------------------------------------------------------------------------
# flow and cycle — steps joined by labelled arrows
# ---------------------------------------------------------------------------


def _step_lines(step: dict, lang: str, width: float) -> tuple[list[str], list[str]]:
    name = wrap(step["name"][lang], width, 18.5, bold=True)
    caption = wrap(step["caption"][lang], width, 15) if step.get("caption") else []
    return name, caption


def _step_height(step: dict, lang: str, width: float) -> float:
    name, caption = _step_lines(step, lang, width)
    return 14 + 44 + 8 + block(len(name), 18.5) + (4 + block(len(caption), 15) if caption else 0) + 14


def _step_card(canvas: Canvas, step: dict, lang: str, x: float, y: float, width: float, height: float,
               number: int | None = None) -> None:
    tone = PALETTE[step["color"]]
    canvas.add(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(width)}" height="{_n(height)}" rx="18" '
               f'fill="{tone["tint"]}" stroke="{tone["accent"]}" stroke-width="2"/>')
    canvas.icon(step["icon"], x + width / 2, y + 14 + 22, 22, step["color"])
    if number is not None:
        canvas.add(f'<circle cx="{_n(x + 18)}" cy="{_n(y + 18)}" r="12" fill="{tone["deep"]}"/>')
        canvas.add(f'<text x="{_n(x + 18)}" y="{_n(y + 23)}" font-size="13" font-weight="700" fill="#FFFFFF" '
                   f'text-anchor="middle">{number}</text>')
    name, caption = _step_lines(step, lang, width - 24)
    top = y + 14 + 44 + 8
    top += canvas.text(name, x + width / 2, top, 18.5, fill=tone["deep"], bold=True)
    if caption:
        canvas.text(caption, x + width / 2, top + 4, 15, fill=MUTED)


def _arrow_label(canvas: Canvas, text: str, cx: float, cy: float, max_width: float) -> None:
    lines = wrap(text, max_width, 13.5)
    width = widest(lines, 13.5) + 18
    height = block(len(lines), 13.5) + 8
    canvas.add(f'<rect x="{_n(cx - width / 2)}" y="{_n(cy - height / 2)}" width="{_n(width)}" height="{_n(height)}" '
               f'rx="{_n(min(height / 2, 12))}" fill="#FFFFFF" stroke="{LINE}" stroke-width="1.5"/>')
    canvas.text(lines, cx, cy - height / 2 + 4, 13.5, fill=MUTED)


def _flow(canvas: Canvas, spec: dict, lang: str, y: float) -> float:
    steps = spec["steps"]
    marker = canvas.arrow_marker("flow", MUTED)
    canvas.motion = True
    vertical = spec.get("direction", "horizontal" if len(steps) <= 4 else "vertical") == "vertical"
    if vertical:
        width = INNER - 120
        x = MARGIN + 60
        for index, step in enumerate(steps):
            height = _step_height(step, lang, width - 24)
            _step_card(canvas, step, lang, x, y, width, height, number=index + 1)
            y += height
            if index < len(steps) - 1:
                canvas.add(f'<line x1="{WIDTH / 2}" y1="{_n(y + 4)}" x2="{WIDTH / 2}" y2="{_n(y + 50)}" stroke="{MUTED}" '
                           f'stroke-width="3" stroke-dasharray="9 9" class="flow" marker-end="url(#{marker})"/>')
                if step.get("arrow"):
                    _arrow_label(canvas, step["arrow"][lang], WIDTH / 2 + 110, y + 27, 180)
                y += 56
        return y + 24
    gap = 58
    width = (INNER - gap * (len(steps) - 1)) / len(steps)
    height = max(_step_height(step, lang, width - 24) for step in steps)
    for index, step in enumerate(steps):
        x = MARGIN + index * (width + gap)
        _step_card(canvas, step, lang, x, y, width, height, number=index + 1)
        if index < len(steps) - 1:
            x1, x2 = x + width + 6, x + width + gap - 6
            cy = y + height / 2
            canvas.add(f'<line x1="{_n(x1)}" y1="{_n(cy)}" x2="{_n(x2)}" y2="{_n(cy)}" stroke="{MUTED}" '
                       f'stroke-width="3" stroke-dasharray="9 9" class="flow" marker-end="url(#{marker})"/>')
    labels = [step.get("arrow") for step in steps[:-1]]
    if any(labels):
        top = y + height + 10
        for index, label in enumerate(labels):
            if label:
                cx = MARGIN + (index + 1) * (width + gap) - gap / 2
                _arrow_label(canvas, label[lang], cx, top + 14, width)
        return top + 44
    return y + height + 24


def _inside(px: float, py: float, box: tuple[float, float, float, float], margin: float = 10) -> bool:
    x, y, w, h = box
    return x - margin <= px <= x + w + margin and y - margin <= py <= y + h + margin


def _cycle(canvas: Canvas, spec: dict, lang: str, y: float) -> float:
    steps = spec["steps"]
    count = len(steps)
    radius = 185 if count <= 4 else 205
    card_w = 196 if count <= 4 else 170
    heights = [_step_height(step, lang, card_w - 24) for step in steps]
    angles = [-math.pi / 2 + 2 * math.pi * index / count for index in range(count)]
    top_extent = max([h / 2 - radius * math.sin(a) for h, a in zip(heights, angles)] + [radius + 16])
    cx, cy = WIDTH / 2, y + top_extent + 6
    boxes = []
    for angle, height in zip(angles, heights):
        px, py = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        boxes.append((px - card_w / 2, py - height / 2, card_w, height))
    tone = PALETTE[spec["center"].get("color", "indigo")]
    marker = canvas.arrow_marker("cycle", tone["accent"])
    canvas.motion = True
    # arcs first, so the cards sit on top of them
    for index in range(count):
        start, end = angles[index], angles[index] + 2 * math.pi / count
        step = math.radians(1)
        a0 = start
        while a0 < end and _inside(cx + radius * math.cos(a0), cy + radius * math.sin(a0), boxes[index]):
            a0 += step
        a1 = end
        nxt = boxes[(index + 1) % count]
        while a1 > a0 and _inside(cx + radius * math.cos(a1), cy + radius * math.sin(a1), nxt):
            a1 -= step
        x0, y0 = cx + radius * math.cos(a0), cy + radius * math.sin(a0)
        x1, y1 = cx + radius * math.cos(a1), cy + radius * math.sin(a1)
        large = 1 if a1 - a0 > math.pi else 0
        canvas.add(f'<path d="M{_n(x0)},{_n(y0)} A{radius},{radius} 0 {large} 1 {_n(x1)},{_n(y1)}" fill="none" '
                   f'stroke="{tone["accent"]}" stroke-width="3.5" stroke-dasharray="9 9" class="flow" '
                   f'marker-end="url(#{marker})"/>')
        if steps[index].get("arrow"):
            mid = (a0 + a1) / 2
            label_r = radius + 34
            _arrow_label(canvas, steps[index]["arrow"][lang], cx + label_r * math.cos(mid),
                         cy + label_r * math.sin(mid), 150)
    # the centre
    center = spec["center"]
    canvas.add('<g class="pulse">')
    canvas.add(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="78" fill="{tone["accent"]}"/>')
    canvas.add(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="70" fill="#FFFFFF" fill-opacity="0.14"/>')
    canvas.add(f'<text x="{_n(cx)}" y="{_n(cy - 8)}" font-size="34" text-anchor="middle" '
               f'font-family="{EMOJI_FONT}">{escape(center["icon"])}</text>')
    lines = wrap(center["name"][lang], 128, 16, bold=True)
    canvas.text(lines, cx, cy + 6, 16, fill="#FFFFFF", bold=True)
    canvas.add("</g>")
    for index, (step, box) in enumerate(zip(steps, boxes)):
        _step_card(canvas, step, lang, *box, number=index + 1)
    has_labels = any(step.get("arrow") for step in steps)
    ring_bottom = cy + radius + (54 if has_labels else 16)
    bottom = max([box[1] + box[3] for box in boxes] + [ring_bottom])
    return bottom + 26


RENDERERS = {"compare": _compare, "equation": _equation, "cycle": _cycle, "flow": _flow}


def render(spec: dict, lang: str) -> str:
    """The SVG of one diagram spec in one language."""
    canvas = Canvas(lang)
    y = _header(canvas, spec, lang)
    y = RENDERERS[spec["template"]](canvas, spec, lang, y)
    y = _takeaway(canvas, spec, lang, y)
    return canvas.svg(y + 8, spec["title"][lang], describe(spec, lang))


# ---------------------------------------------------------------------------
# roadmap — the course as a journey, drawn from curriculum.yaml
# ---------------------------------------------------------------------------


def render_roadmap(modules: list[dict], labels: dict[str, str], lang: str) -> str:
    """modules: [{number, icon, title, meta}] in one language; labels: title, subtitle, start, finish."""
    canvas = Canvas(lang)
    y = _header(canvas, {"title": {"x": labels["title"]}, "subtitle": {"x": labels["subtitle"]}}, "x")
    road_x = MARGIN + 52
    card_x = road_x + 48
    card_w = WIDTH - MARGIN - card_x
    pad = 18
    # start flag
    canvas.add(f'<text x="{road_x}" y="{_n(y + 26)}" font-size="28" text-anchor="middle" '
               f'font-family="{EMOJI_FONT}">🚩</text>')
    canvas.text([labels["start"]], card_x, y + 6, 17, fill=MUTED, anchor="start", bold=True)
    y += 48
    stops = []
    for position, module in enumerate(modules):
        color = MODULE_COLORS[position % len(MODULE_COLORS)]
        title = wrap(module["title"], card_w - 2 * pad - 50, 19, bold=True)
        height = 16 + block(len(title), 19) + 6 + block(1, 15) + 16
        stops.append((module, color, title, y, height))
        y += height + 18
    first_cy = stops[0][3] + stops[0][4] / 2
    last_cy = stops[-1][3] + stops[-1][4] / 2
    road_end = last_cy + 60
    # the road: a coloured band with moving white dashes
    gradient = "".join(
        f'<stop offset="{_n(index / max(1, len(stops) - 1))}" stop-color="{PALETTE[color]["accent"]}"/>'
        for index, (_, color, _, _, _) in enumerate(stops)
    )
    # userSpaceOnUse: a bounding-box gradient on a perfectly vertical line has a
    # zero-width box, and browsers then paint nothing at all.
    canvas.defs.append(
        f'<linearGradient id="road" gradientUnits="userSpaceOnUse" x1="{road_x}" y1="{_n(first_cy)}" '
        f'x2="{road_x}" y2="{_n(last_cy)}">{gradient}</linearGradient>'
    )
    canvas.motion = True
    canvas.add(f'<line x1="{road_x}" y1="{_n(first_cy - 60)}" x2="{road_x}" y2="{_n(road_end)}" stroke="url(#road)" '
               f'stroke-width="14" stroke-linecap="round"/>')
    canvas.add(f'<line x1="{road_x}" y1="{_n(first_cy - 60)}" x2="{road_x}" y2="{_n(road_end)}" stroke="#FFFFFF" '
               f'stroke-width="3" stroke-dasharray="9 9" class="flow"/>')
    for module, color, title, top, height in stops:
        tone = PALETTE[color]
        cy = top + height / 2
        canvas.add(f'<rect x="{_n(card_x)}" y="{_n(top)}" width="{_n(card_w)}" height="{_n(height)}" rx="18" '
                   f'fill="{tone["tint"]}" stroke="{tone["soft"]}" stroke-width="2"/>')
        canvas.add(f'<rect x="{_n(card_x)}" y="{_n(top)}" width="8" height="{_n(height)}" rx="4" fill="{tone["accent"]}"/>')
        canvas.add(f'<circle cx="{road_x}" cy="{_n(cy)}" r="24" fill="{tone["accent"]}" stroke="#FFFFFF" stroke-width="4"/>')
        canvas.add(f'<text x="{road_x}" y="{_n(cy + 7)}" font-size="19" font-weight="700" fill="#FFFFFF" '
                   f'text-anchor="middle">{escape(str(module["number"]))}</text>')
        canvas.add(f'<text x="{_n(card_x + pad + 16)}" y="{_n(top + 16 + 22)}" font-size="26" text-anchor="middle" '
                   f'font-family="{EMOJI_FONT}">{escape(module["icon"])}</text>')
        text_x = card_x + pad + 44
        line_top = top + 16
        line_top += canvas.text(title, text_x, line_top, 19, fill=tone["deep"], anchor="start", bold=True) + 6
        canvas.text([module["meta"]], text_x, line_top, 15, fill=MUTED, anchor="start")
    canvas.add(f'<text x="{road_x}" y="{_n(road_end + 36)}" font-size="30" text-anchor="middle" '
               f'font-family="{EMOJI_FONT}">🏆</text>')
    canvas.text([labels["finish"]], card_x, road_end + 12, 17, fill=MUTED, anchor="start", bold=True)
    bottom = road_end + 58
    description = ". ".join(f"{module['number']}. {module['title']} ({module['meta']})" for module in modules)
    return canvas.svg(bottom, labels["title"], description)
