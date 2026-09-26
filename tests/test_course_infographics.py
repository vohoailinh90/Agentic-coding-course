"""Text fitting and the SVG infographics: legible, complete, identical on every run.

The pictures themselves are checked by eye in a browser; what is computable is
checked here — nothing drawn outside the canvas (the cycle's bottom arrow once
was), no two lines of text and no two boxes on top of each other, line breaks
that respect each script, and output that does not change between two runs, so
CI can tell a stale file from a current one.

The course's own diagrams do not use every template or every option, so the
same checks also run on STRESS: valid specs with long text in every language,
each template at its smallest and largest size.
"""

from __future__ import annotations

import itertools
import math
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.core import yamlio
from src.core.build import roadmap_svg
from src.core.infographics import INK, INNER, WIDTH, crowded, render
from src.core.model import ROOT
from src.core.textfit import NO_LINE_END, NO_LINE_START, text_width, tokenize, wrap
from src.core.validate import Report, _diagram, validate
from src.utils.catalogs import translator_for

SVG = "{http://www.w3.org/2000/svg}"
SPECS = sorted((ROOT / "course/data/diagrams").glob("*.yaml"))
LANGUAGES = ("vi", "en", "ja")


def load(path: Path) -> dict:
    return yamlio.loads(yamlio.read_text(path))


def _t(vi: str, en: str, ja: str) -> dict:
    return {"vi": vi, "en": en, "ja": ja}


NAMES = [
    ("🎯", "blue", _t("Hiểu rõ yêu cầu", "Understand the request", "依頼を理解する")),
    ("🗺️", "violet", _t("Lập kế hoạch từng bước", "Plan the steps", "手順を計画する")),
    ("🛠️", "green", _t("Dùng công cụ để làm việc", "Use tools to do the work", "ツールを使って作業する")),
    ("🔍", "amber", _t("Tự kiểm tra kết quả", "Check its own result", "結果を自分で確かめる")),
    ("📝", "rose", _t("Báo cáo cho người giao việc", "Report back to whoever asked", "依頼した人に報告する")),
    ("🔁", "teal", _t("Sửa lỗi và làm lại nếu cần thiết", "Fix mistakes and try again if needed",
                     "必要ならミスを直してやり直す")),
]
CAPTION = _t("Đọc kỹ mục tiêu, các ràng buộc và cách người giao việc sẽ kiểm tra kết quả cuối cùng",
             "Read the goal, the constraints and how the person who asked will check the final result",
             "目標と制約、そして依頼した人が最終結果をどう確かめるかをよく読む")
BRIEF = _t("Ghi lại điều vừa học được", "Write down what it learned", "学んだことを書き留める")
ARROW = _t("nếu kết quả chưa đạt thì quay lại và sửa tiếp",
           "if the result is not good enough, go back and fix it",
           "結果が足りなければ、戻ってもう一度直す")
SHORT = _t("Có", "Yes", "はい")
LONG = _t("AI agent tự lập kế hoạch, dùng công cụ và tự kiểm tra kết quả trước khi báo cáo lại cho bạn",
          "The AI agent plans, uses tools and checks its own result before it reports back to you",
          "AIエージェントが自分で計画し、ツールを使い、結果を確かめてからあなたに報告する")
TAKEAWAY = _t("Bạn đặt mục tiêu và kiểm tra kết quả cuối cùng; agent lo phần việc ở giữa",
              "You set the goal and check the final result; the agent does the work in between",
              "目標を決めて最後の結果を確かめるのはあなた。その間の作業はエージェントが担う")


def _steps(count: int, *, arrows: bool = True, caption: dict = CAPTION, arrow: dict = ARROW) -> list[dict]:
    steps = []
    for icon, color, name in NAMES[:count]:
        step = {"icon": icon, "color": color, "name": name, "caption": caption}
        if arrows:
            step["arrow"] = arrow
        steps.append(step)
    return steps


def _stress() -> dict[str, dict]:
    title = _t("Một sơ đồ thử nghiệm với tiêu đề khá dài để kiểm tra việc xuống dòng",
               "A test diagram with a rather long title to exercise line wrapping",
               "折り返しを確かめるための、やや長いタイトルの試験用の図")
    common = {"title": title, "subtitle": CAPTION, "takeaway": TAKEAWAY}
    rows = [_t(f"Hàng {n}", f"Row {n}", f"行{n}") for n in range(1, 7)]
    specs = {
        "compare-versus": {
            "template": "compare", **common, "rows": rows, "versus": True, "emphasis_row": 2,
            "columns": [
                {"icon": "🗺️", "color": "blue", "name": NAMES[0][2], "values": [SHORT] * 6},
                {"icon": "🚕", "color": "violet", "name": NAMES[5][2], "values": [LONG] * 6,
                 "highlight": True, "badge": ARROW},
            ],
        },
        "compare-four": {
            "template": "compare", **common, "rows": rows[:3],
            "columns": [
                {"icon": icon, "color": color, "name": name, "values": [LONG, SHORT, LONG][: 3],
                 **({"badge": SHORT} if position % 2 else {})}
                for position, (icon, color, name) in enumerate(NAMES[:4])
            ],
        },
    }
    for count in (2, 4):
        terms = [{"icon": icon, "color": color, "name": name, "caption": CAPTION}
                 for icon, color, name in NAMES[:count]]
        result = {"icon": "🤖", "color": "indigo", "name": NAMES[5][2], "caption": CAPTION}
        specs[f"equation-{count}"] = {"template": "equation", **common, "terms": terms, "result": result}
    for count in (2, 4, 6):
        specs[f"flow-{count}"] = {"template": "flow", **common, "steps": _steps(count)}
    specs["flow-5"] = {"template": "flow", **common, "steps": _steps(5, arrow=LONG)}  # labels of 3+ lines
    specs["flow-2-vertical"] = {"template": "flow", **common, "direction": "vertical", "steps": _steps(2)}
    specs["flow-6-horizontal"] = {"template": "flow", **common, "direction": "horizontal",
                                  "steps": _steps(6, arrows=False)}
    for count in (3, 4, 5, 6):
        points = [{"icon": icon, "color": color, "name": name, "caption": CAPTION} for icon, color, name in NAMES[:count]]
        specs[f"summary-{count}"] = {"template": "summary", **common, "points": points}
    center = {"icon": "🤖", "name": _t("AI agent", "AI agent", "AIエージェント")}
    for count in (3, 4, 5):
        specs[f"cycle-{count}"] = {"template": "cycle", **common, "steps": _steps(count), "center": center}
    specs["cycle-6"] = {"template": "cycle", **common, "steps": _steps(6, caption=BRIEF), "center": center}
    return specs


STRESS = _stress()
# More text than six cards round a ring can hold at this width: reported, not drawn over.
CROWDED = {"template": "cycle", "title": BRIEF, "center": {"icon": "🤖", "name": BRIEF},
           "steps": _steps(6, caption={language: f"{LONG[language]} {LONG[language]}" for language in LONG})}


def text_boxes(root: ET.Element) -> list[tuple[tuple[float, float, float, float], str]]:
    """Every line of text as (x, y, width, height), from the same width estimate the layout uses."""
    boxes = []
    for element in root.iter(f"{SVG}text"):
        size = float(element.get("font-size"))
        bold = element.get("font-weight") == "700"
        anchor = element.get("text-anchor", "start")
        spans = list(element.iter(f"{SVG}tspan")) or [element]
        for span in spans:
            content = span.text or ""
            x, y = float(span.get("x")), float(span.get("y"))
            width = text_width(content, size, bold=bold)
            left = {"middle": x - width / 2, "end": x - width}.get(anchor, x)
            boxes.append(((left, y - 0.8 * size, width, size), content))
    return boxes


def shape_boxes(root: ET.Element) -> list[tuple[tuple[float, float, float, float], str]]:
    """Cards, arrow labels and the takeaway: boxes that must never cover one another."""
    boxes = []
    for rect in root.iter(f"{SVG}rect"):
        if (rect.get("x"), rect.get("y")) == ("1", "1") or rect.get("fill") == INK:
            continue  # the frame holds everything; a badge sits on its card's edge on purpose
        box = tuple(float(rect.get(key)) for key in ("x", "y", "width", "height"))
        boxes.append((box, f"rect {box}"))
    return boxes


def into_the_hub(root: ET.Element) -> list[str]:
    """Boxes that reach into a cycle's centre disc."""
    problems = []
    for disc in root.iter(f"{SVG}circle"):
        if disc.get("r") != "78":
            continue
        cx, cy = float(disc.get("cx")), float(disc.get("cy"))
        for (x, y, width, height), name in shape_boxes(root):
            if math.hypot(min(max(cx, x), x + width) - cx, min(max(cy, y), y + height) - cy) < 78:
                problems.append(f"{name} reaches into the centre disc")
    return problems


def text_outside_its_box(root: ET.Element) -> list[str]:
    """Lines of text that run out of the smallest box their first line starts in.

    The whole-canvas frame counts as a box, so a title or a label drawn on the
    background passes; a caption spilling out of a card, which a card too short
    for its text would cause, does not.
    """
    boxes = [tuple(float(rect.get(key)) for key in ("x", "y", "width", "height")) for rect in root.iter(f"{SVG}rect")]
    problems = []
    for element in root.iter(f"{SVG}text"):
        size = float(element.get("font-size"))
        spans = list(element.iter(f"{SVG}tspan")) or [element]
        first_x, first_y = float(spans[0].get("x")), float(spans[0].get("y"))
        around = [box for box in boxes
                  if box[0] <= first_x <= box[0] + box[2] and box[1] <= first_y - 0.8 * size <= box[1] + box[3]]
        if not around:
            continue  # nothing to be outside of
        x, y, width, height = min(around, key=lambda box: box[2] * box[3])
        for span in spans:
            if float(span.get("y")) + 0.2 * size > y + height + 1:
                problems.append(f"{span.text!r} runs out of the box at y={y + height:.1f}")
    return problems


def overlapping(boxes: list[tuple[tuple[float, float, float, float], str]]) -> list[str]:
    problems = []
    for (a, name_a), (b, name_b) in itertools.combinations(boxes, 2):
        across = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
        down = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
        if across > 1 and down > 1:
            problems.append(f"{name_a!r} overlaps {name_b!r}")
    return problems


def assert_inside_canvas(test: unittest.TestCase, svg: str) -> None:
    """No shape or line of text reaches past the edges of the drawing."""
    root = ET.fromstring(svg)
    width, height = float(root.get("width")), float(root.get("height"))
    test.assertEqual(root.get("viewBox"), f"0 0 {int(width)} {int(height)}")
    for rect in root.iter(f"{SVG}rect"):
        x, y = float(rect.get("x")), float(rect.get("y"))
        test.assertLessEqual(x + float(rect.get("width")), width + 0.5, ET.tostring(rect)[:120])
        test.assertLessEqual(y + float(rect.get("height")), height + 0.5, ET.tostring(rect)[:120])
    for circle in root.iter(f"{SVG}circle"):
        if circle.get("fill-opacity") in ("0.05", "0.06"):
            continue  # the decorative corner blobs bleed off the card on purpose
        test.assertLessEqual(float(circle.get("cy")) + float(circle.get("r")), height + 0.5)
    for span in root.iter(f"{SVG}tspan"):
        test.assertLessEqual(float(span.get("y")), height, span.text)


class WrapTests(unittest.TestCase):
    def test_vietnamese_breaks_between_words_only(self) -> None:
        text = "Lập kế hoạch, tự làm, tự kiểm tra kết quả của chính mình"
        lines = wrap(text, 150, 17)
        self.assertGreater(len(lines), 1)
        self.assertEqual(" ".join(lines).split(), text.split())
        for line in lines:
            self.assertLessEqual(text_width(line, 17), 150)

    def test_japanese_punctuation_never_starts_a_line(self) -> None:
        text = "目標を決め、最後の結果を確かめるのはあなた。タクシーでも、到着地を確かめるのはあなたの役目。"
        for width in range(90, 400, 7):
            with self.subTest(width=width):
                lines = wrap(text, width, 18)
                self.assertEqual("".join(lines), text)
                for line in lines:
                    self.assertNotIn(line[0], NO_LINE_START)
                    self.assertNotIn(line[-1], NO_LINE_END)

    def test_a_katakana_word_is_not_split(self) -> None:
        self.assertEqual(tokenize("AIエージェント ≈ タクシー運転手"), ["AIエージェント ", "≈ ", "タクシー", "運", "転", "手"])
        # Only where the word fits on a line at all: a wider word is split by design.
        narrowest = int(text_width("Googleマップ", 21, bold=True)) + 1
        for width in range(narrowest, 330, 10):
            with self.subTest(width=width):
                lines = wrap("チャットボット ≈ Googleマップ", width, 21, bold=True)
                self.assertTrue(any("Googleマップ" in line for line in lines), lines)

    def test_a_word_wider_than_the_line_is_split_by_characters(self) -> None:
        lines = wrap("Supercalifragilisticexpialidocious", 80, 17)
        self.assertGreater(len(lines), 1)
        self.assertEqual("".join(lines), "Supercalifragilisticexpialidocious")
        for line in lines:
            self.assertLessEqual(text_width(line, 17), 80)

    def test_a_newline_forces_a_break(self) -> None:
        self.assertEqual(wrap("one\ntwo", 500, 17), ["one", "two"])


class RenderTests(unittest.TestCase):
    def test_the_stress_specs_are_valid_specs(self) -> None:
        # Otherwise the checks below would pass or fail on inputs no author can write.
        for name, spec in STRESS.items():
            with self.subTest(spec=name):
                report = Report()
                self.assertIsNotNone(_diagram(report, name, spec, LANGUAGES), report.findings)
                self.assertEqual(report.findings, [])

    def test_nothing_overlaps_in_any_diagram(self) -> None:
        specs = {path.stem: load(path) for path in SPECS} | STRESS
        for name, spec in specs.items():
            for language in LANGUAGES:
                with self.subTest(diagram=name, language=language):
                    svg = render(spec, language)
                    assert_inside_canvas(self, svg)
                    root = ET.fromstring(svg)
                    self.assertEqual(overlapping(text_boxes(root)), [])
                    self.assertEqual(overlapping(shape_boxes(root)), [])
                    self.assertEqual(into_the_hub(root), [])
                    self.assertEqual(text_outside_its_box(root), [])
                    self.assertFalse(crowded(spec, language))

    def test_too_much_text_is_reported_rather_than_drawn_over(self) -> None:
        report = Report()
        self.assertIsNotNone(_diagram(report, "crowded", CROWDED, LANGUAGES), report.findings)
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.assertTrue(crowded(CROWDED, language))
                assert_inside_canvas(self, render(CROWDED, language))  # still drawn, for the author to see

    def test_an_equation_joins_its_terms_with_plus_and_ends_with_equals(self) -> None:
        for count in (2, 4):
            with self.subTest(terms=count):
                root = ET.fromstring(render(STRESS[f"equation-{count}"], "en"))
                operators = [element.text for element in root.iter(f"{SVG}text") if element.get("font-size") == "24"]
                self.assertEqual(operators, ["+"] * (count - 1) + ["="])

    def test_a_flow_is_horizontal_up_to_four_steps_and_has_one_arrow_between_steps(self) -> None:
        for name, horizontal in (("flow-2", True), ("flow-4", True), ("flow-5", False), ("flow-6", False),
                                 ("flow-2-vertical", False), ("flow-6-horizontal", True)):
            with self.subTest(spec=name):
                spec = STRESS[name]
                root = ET.fromstring(render(spec, "vi"))
                cards = [rect for rect in root.iter(f"{SVG}rect") if rect.get("rx") == "18"]
                self.assertEqual(len(cards), len(spec["steps"]))
                tops = [float(card.get("y")) for card in cards]
                lefts = [float(card.get("x")) for card in cards]
                if horizontal:
                    self.assertEqual(len(set(tops)), 1)
                    self.assertEqual(lefts, sorted(lefts))
                else:
                    self.assertEqual(len(set(lefts)), 1)
                    self.assertEqual(tops, sorted(tops))
                arrows = [line for line in root.iter(f"{SVG}line") if line.get("class") == "flow"]
                self.assertEqual(len(arrows), len(spec["steps"]) - 1)

    def test_a_summary_numbers_its_points_on_a_centred_grid(self) -> None:
        for count, rows in ((3, [3]), (4, [2, 2]), (5, [3, 2]), (6, [3, 3])):
            with self.subTest(points=count):
                root = ET.fromstring(render(STRESS[f"summary-{count}"], "en"))
                cards = [rect for rect in root.iter(f"{SVG}rect") if rect.get("rx") == "18"]
                tops = sorted({float(card.get("y")) for card in cards})
                self.assertEqual([sum(float(card.get("y")) == top for card in cards) for top in tops], rows)
                for top in tops:  # every row, a short last one included, is centred
                    row = [card for card in cards if float(card.get("y")) == top]
                    left = min(float(card.get("x")) for card in row)
                    right = max(float(card.get("x")) + float(card.get("width")) for card in row)
                    self.assertAlmostEqual((left + right) / 2, WIDTH / 2, delta=0.5)
                badges = [element.text for element in root.iter(f"{SVG}text") if element.get("font-size") == "13"]
                self.assertEqual(badges, [str(number) for number in range(1, count + 1)])

    def test_every_diagram_renders_inside_its_canvas_in_every_language(self) -> None:
        self.assertGreater(len(SPECS), 0)
        for path in SPECS:
            spec = load(path)
            for language in LANGUAGES:
                with self.subTest(diagram=path.stem, language=language):
                    svg = render(spec, language)
                    assert_inside_canvas(self, svg)
                    root = ET.fromstring(svg)
                    self.assertEqual(root.get("lang"), language)
                    self.assertEqual(root.find(f"{SVG}title").text, spec["title"][language])
                    self.assertEqual(render(spec, language), svg)  # deterministic

    def test_motion_is_optional_and_respects_reduced_motion(self) -> None:
        svg = render(load(ROOT / "course/data/diagrams/agent-loop.yaml"), "vi")
        self.assertIn("prefers-reduced-motion: reduce", svg)
        root = ET.fromstring(svg)
        # the static picture is complete: every shape carries its own colour
        for shape in root.iter(f"{SVG}rect"):
            self.assertIsNotNone(shape.get("fill"))

    def test_the_cycle_keeps_the_label_under_its_ring(self) -> None:
        # The arrow round the bottom of the ring, and its label, once ran into the
        # takeaway below the diagram: the ring must end above it.
        spec = load(ROOT / "course/data/diagrams/agent-loop.yaml")
        for language in LANGUAGES:
            with self.subTest(language=language):
                svg = render(spec, language)
                assert_inside_canvas(self, svg)
                root = ET.fromstring(svg)
                cy = float(next(c for c in root.iter(f"{SVG}circle") if c.get("r") == "78").get("cy"))
                arc = next(p.get("d") for p in root.iter(f"{SVG}path") if " A" in p.get("d"))
                radius = float(re.search(r" A([\d.]+),", arc).group(1))
                takeaway = next(r for r in root.iter(f"{SVG}rect")  # the full-width amber pill
                                if r.get("fill") == "#FFFBEB" and float(r.get("width")) == INNER)
                labels = [r for r in root.iter(f"{SVG}rect")
                          if r.get("fill") == "#FFFFFF" and r.get("stroke") == "#E2E8F0"]
                self.assertEqual(len(labels), 3)
                top = float(takeaway.get("y"))
                self.assertGreaterEqual(top, cy + radius)
                for label in labels:
                    self.assertLessEqual(float(label.get("y")) + float(label.get("height")), top)


class RoadmapTests(unittest.TestCase):
    def setUp(self) -> None:
        report = validate(ROOT, check_generated=False)
        self.assertIsNotNone(report.course)
        self.course = report.course

    def test_the_roadmap_road_is_painted(self) -> None:
        # A bounding-box gradient on a vertical line has a zero-width box, and
        # browsers then paint nothing: the road vanished once.
        svg = roadmap_svg(self.course, "vi", translator_for("vi"))
        gradient = next(element for element in ET.fromstring(svg).iter(f"{SVG}linearGradient")
                        if element.get("id") == "road")
        self.assertEqual(gradient.get("gradientUnits"), "userSpaceOnUse")

    def test_the_roadmap_counts_each_module_s_minimum_path_lessons(self) -> None:
        self.assertTrue(self.course.minimum_path)
        for language in LANGUAGES:
            tr = translator_for(language)
            svg = roadmap_svg(self.course, language, tr)
            for module in self.course.modules:
                count = sum(lesson.id in self.course.minimum_path for lesson in module.lessons)
                with self.subTest(language=language, module=module.id):
                    label = tr.t("roadmap.minimum", lessons=count)
                    if count:
                        self.assertIn(label, svg)
                    else:
                        self.assertNotIn(label, svg)

    def test_the_roadmap_shows_every_module_inside_its_canvas(self) -> None:
        for language in LANGUAGES:
            with self.subTest(language=language):
                svg = roadmap_svg(self.course, language, translator_for(language))
                assert_inside_canvas(self, svg)
                self.assertEqual(overlapping(text_boxes(ET.fromstring(svg))), [])
                for module in self.course.modules:
                    self.assertIn(module.title[language].split(" ")[0], svg)
                self.assertLessEqual(float(ET.fromstring(svg).get("width")), WIDTH)


if __name__ == "__main__":
    unittest.main()
