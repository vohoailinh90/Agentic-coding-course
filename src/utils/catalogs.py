"""The CLI's message catalogs (src/locales/{vi,en,ja}.json) and how to load them."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from src.utils.i18n import FALLBACK_LOCALE, Translator

LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"


def translator(locale: str | None = None) -> Translator:
    """The user's language: `--lang`, then $APP_LANG, then the POSIX variables, then the OS."""
    return Translator.from_dir(LOCALES_DIR, locale=locale)


def translator_for(language: str) -> Translator:
    """A translator pinned to `language` whatever the environment says.

    Generated files (OUTLINE.md, posts) must not change with the machine that
    renders them, so a language without a catalog falls back to English
    explicitly instead of to $APP_LANG or the OS locale.
    """
    pinned = Translator.from_dir(LOCALES_DIR, locale=language)
    pinned.set_locale(language if language in pinned.locales else FALLBACK_LOCALE)
    return pinned


def translators_for(languages: Iterable[str]) -> dict[str, Translator]:
    return {language: translator_for(language) for language in languages}
