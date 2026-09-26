"""The Vietnamese additions to the copied i18n runtime, and the catalog loaders."""

from __future__ import annotations

import os
import unittest
from datetime import date
from unittest import mock

from src.utils import i18n
from src.utils.catalogs import translator, translator_for


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
