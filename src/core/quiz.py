"""The quiz that ends a lesson: three questions with options A–C, and an answer key.

In a lesson file (docs/content-guide.md, *Quiz format*):

    **Câu 1.** Question?

    - A) ...
    - B) ...
    - C) ...

    <details>
    <summary>Xem đáp án</summary>

    1. **B** — one sentence on why.

    </details>

Only the shape is read: the option letters and the answer key. That is what every
language must agree on, since a translation that reorders the options has to reorder
the key with them — and the eye does not catch it when it does not.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

OPTION = re.compile(r"^\s*[-*] (?P<letter>[A-Z])\) ")
ANSWER = re.compile(r"^\s*(?P<number>\d+)\. \*\*(?P<letter>[A-Z])\*\*")
QUESTIONS = 3
LETTERS = "ABC"


@dataclass(frozen=True)
class Quiz:
    options: str  # the letters of the option lines, in order: "ABCABCABC" when well formed
    answers: tuple[tuple[int, str], ...]  # (question number, letter), in order

    @property
    def key(self) -> str:
        return "".join(letter for _, letter in self.answers)

    @property
    def well_formed(self) -> bool:
        return (
            self.options == LETTERS * QUESTIONS
            and [number for number, _ in self.answers] == list(range(1, QUESTIONS + 1))
            and all(letter in LETTERS for _, letter in self.answers)
        )


def read_quiz(lines: Iterable[str]) -> Quiz:
    """The quiz in these lines of a quiz section, code blocks already left out."""
    options: list[str] = []
    answers: list[tuple[int, str]] = []
    for line in lines:
        option = OPTION.match(line)
        if option:
            options.append(option.group("letter"))
            continue
        answer = ANSWER.match(line)
        if answer:
            answers.append((int(answer.group("number")), answer.group("letter")))
    return Quiz("".join(options), tuple(answers))
