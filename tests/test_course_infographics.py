"""Text fitting and the SVG infographics: legible, complete, identical on every run.

The pictures themselves are checked by eye in a browser; what is computable is
checked here — nothing drawn outside the canvas (the cycle's bottom arrow once
was), line breaks that respect each script, and output that does not change
between two runs, so CI can tell a stale file from a current one.
"""

from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.core import yamlio
from src.core.build import roadmap_svg
from src.core.infographics import INNER, WIDTH, render
from src.core.model import ROOT
from src.core.textfit import NO_LINE_END, NO_LINE_START, text_width, tokenize, wrap
from src.core.validate import validate
from src.utils.catalogs import translator_for

SVG = "{http://www.w3.org/2000/svg}"
SPECS = sorted((ROOT / "course/data/diagrams").glob("*.yaml"))
LANGUAGES = ("vi", "en", "ja")


def load(path: Path) -> dict:
    return yamlio.loads(yamlio.read_text(path))


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

    def test_the_roadmap_shows_every_module_inside_its_canvas(self) -> None:
        for language in LANGUAGES:
            with self.subTest(language=language):
                svg = roadmap_svg(self.course, language, translator_for(language))
                assert_inside_canvas(self, svg)
                for module in self.course.modules:
                    self.assertIn(module.title[language].split(" ")[0], svg)
                self.assertLessEqual(float(ET.fromstring(svg).get("width")), WIDTH)


if __name__ == "__main__":
    unittest.main()
