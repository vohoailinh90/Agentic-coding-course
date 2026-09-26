"""The Vietnamese additions to the copied i18n runtime, and the catalog loaders."""

from __future__ import annotations

import json
import os
import re
import unittest
from datetime import date
from unittest import mock

from src.core.model import ROOT
from src.core.validate import Finding
from src.utils import i18n
from src.utils.catalogs import translator, translator_for
from src.utils.console import render_finding


class VietnameseTests(unittest.TestCase):
    def test_dates(self) -> None:
        self.assertEqual(i18n.format_date(date(2026, 9, 5), "vi"), "ngày 5 tháng 9 năm 2026")
        self.assertEqual(i18n.format_date(date(2026, 9, 5), "vi", "short"), "05/09/2026")

    def test_locale_names(self) -> None:
        self.assertEqual(i18n.normalize_locale("Vietnamese_Vietnam"), "vi")
        self.assertEqual(i18n.normalize_locale("vi_VN.UTF-8"), "vi")
        self.assertEqual(i18n.LANGUAGE_NAMES["vi"], "Tiếng Việt")

    def test_vietnamese_has_one_plural_form(self) -> None:
        self.assertEqual(i18n.plural_category("vi", 1), "other")


class CatalogTests(unittest.TestCase):
    def test_every_course_language_has_a_catalog(self) -> None:
        self.assertEqual(sorted(translator("en").locales), ["en", "ja", "vi"])

    def test_app_lang_picks_the_language(self) -> None:
        with mock.patch.dict(os.environ, {"APP_LANG": "vi"}):
            self.assertEqual(translator().locale, "vi")

    def test_a_pinned_translator_ignores_the_environment(self) -> None:
        with mock.patch.dict(os.environ, {"APP_LANG": "ja"}):
            self.assertEqual(translator_for("vi").locale, "vi")
            self.assertEqual(translator_for("ko").locale, "en")


if __name__ == "__main__":
    unittest.main()


class FindingMessageTests(unittest.TestCase):
    """Every validator finding can be printed, in every language.

    Params reach Translator.t as keywords, so a placeholder named like one of its
    own arguments (`key`, `count`) cannot be filled: `{key}` once made `validate`
    crash on the first missing section instead of naming it.
    """

    def test_every_finding_renders_in_every_language(self) -> None:
        for language in ("vi", "en", "ja"):
            tr = translator_for(language)
            catalog = json.loads((ROOT / "src/locales" / f"{language}.json").read_text(encoding="utf-8"))
            for code, message in catalog["findings"].items():
                names = set(re.findall(r"{(\w+)}", message))
                with self.subTest(language=language, code=code):
                    self.assertFalse(names & {"key", "count"}, "these names belong to Translator.t")
                    params = {name: f"<{name}>" for name in names}
                    if "expected" in params and code == "field_type":
                        params["expected"] = "text"  # rendered through types.<expected>
                    text = render_finding(tr, Finding("error", code, params))
                    self.assertNotRegex(text, r"{\w+}")
                    for name, value in params.items():
                        if value.startswith("<"):
                            self.assertIn(value, text)
