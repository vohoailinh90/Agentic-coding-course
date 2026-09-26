"""Estimate rendered text width and wrap text to a width, without a font engine.

The infographics are SVG files that GitHub, browsers and phones render with
whatever fonts the reader has, so exact metrics are unknowable. These widths
are deliberately a little generous for common UI fonts (Segoe UI, Noto Sans,
Yu Gothic, Hiragino, IPA Gothic): an estimated line is never narrower than the
rendered one, so wrapped text stays inside its box. Boxes grow in height to fit
the lines, so nothing needs to overflow horizontally.

Line breaking follows the scripts in the course:
- Vietnamese and English break at spaces; a word wider than the whole line is
  split by characters as a last resort.
- Japanese may break between kanji and kana, except that closing punctuation
  (、。）」 …) never starts a line and opening brackets (（「 …) never end one
  (kinsoku shori). A run of katakana and Latin letters is one word — a
  loanword such as エージェント or Googleマップ is never split — unless it is
  wider than the whole line.
"""

from __future__ import annotations

import unicodedata

# Characters that must not start a line, and ones that must not end a line.
NO_LINE_START = set("、。，．・：；！？）」』】〕〉》ーぁぃぅぇぉっゃゅょァィゥェォッャュョ)]}”’,.!?:;…‐–—％")
NO_LINE_END = set("（「『【〔〈《([{“‘")

_NARROW = set("iljI.,:;'!|·")
_MEDIUM = set("()[]{}\"`-–/\\*")
_WIDE_LATIN = set("mwMW@%&")
_ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0xFE0E, 0xFE0F}
BOLD_FACTOR = 1.08


def is_wide(char: str) -> bool:
    """East Asian wide or full-width: kana, kanji, full-width punctuation."""
    return unicodedata.east_asian_width(char) in ("W", "F")


def is_word_char(char: str) -> bool:
    """Letters that belong to one unbreakable word: Latin, digits, katakana (incl. ー and small kana)."""
    code = ord(char)
    if 0x30A0 <= code <= 0x30FF or 0x31F0 <= code <= 0x31FF or 0xFF66 <= code <= 0xFF9F:
        return True
    return char.isascii() and char.isalnum() or unicodedata.category(char).startswith("L") and not is_wide(char)


def is_emoji(char: str) -> bool:
    code = ord(char)
    return 0x1F000 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF or 0x2B00 <= code <= 0x2BFF


def char_width(char: str) -> float:
    """Width of one character in em."""
    code = ord(char)
    if code in _ZERO_WIDTH or unicodedata.combining(char):
        return 0.0
    if is_emoji(char):
        return 1.25
    if is_wide(char):
        return 1.0
    if char == " ":
        return 0.3
    if char in "—…→←↔":
        return 1.0
    if char in _NARROW:
        return 0.32
    if char in _MEDIUM:
        return 0.42
    if char in _WIDE_LATIN:
        return 0.92
    if char.isupper():
        return 0.7
    if char.isdigit():
        return 0.6
    return 0.58  # lowercase Latin, including precomposed Vietnamese letters


def text_width(text: str, size: float, *, bold: bool = False) -> float:
    """Estimated width in px of `text` set at `size` px."""
    width = sum(char_width(char) for char in text) * size
    return width * BOLD_FACTOR if bold else width


def _can_break(before: str, after: str) -> bool:
    """Whether a line may end between these two characters."""
    if before == " ":
        return True
    if after == " ":
        return False  # the space stays with the word before it
    if after in NO_LINE_START or before in NO_LINE_END:
        return False
    if is_word_char(before) and is_word_char(after):
        return False  # inside a Latin, Vietnamese or katakana word
    return is_wide(before) or is_wide(after) or is_emoji(before)


def tokenize(text: str) -> list[str]:
    """Split text into the smallest pieces a line may end after."""
    tokens: list[str] = []
    current = ""
    for index, char in enumerate(text):
        current += char
        following = text[index + 1] if index + 1 < len(text) else ""
        if following and _can_break(char, following):
            tokens.append(current)
            current = ""
    if current:
        tokens.append(current)
    return tokens


def wrap(text: str, max_width: float, size: float, *, bold: bool = False) -> list[str]:
    """Lines of `text` that each fit `max_width` px; `\\n` forces a break."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for token in tokenize(paragraph.strip()):
            candidate = line + token
            if text_width(candidate.rstrip(), size, bold=bold) <= max_width:
                line = candidate
                continue
            if line.strip():
                lines.append(line.rstrip())
                line = ""
            token = token.lstrip()
            if text_width(token.rstrip(), size, bold=bold) <= max_width:
                line = token
                continue
            for char in token:  # a single piece wider than the line: split it by characters
                if line and text_width((line + char).rstrip(), size, bold=bold) > max_width:
                    lines.append(line.rstrip())
                    line = ""
                line += char
        lines.append(line.rstrip())
    return lines


def widest(lines: list[str], size: float, *, bold: bool = False) -> float:
    return max((text_width(line, size, bold=bold) for line in lines), default=0.0)
