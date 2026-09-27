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

Only the shape is read: the numbered question headings, the option letters grouped
under each heading, and the answer key. That is what every
language must agree on, since a translation that reorders the options has to reorder
the key with them — and the eye does not catch it when it does not.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

OPTION = re.compile(r"^\s*[-*] (?P<letter>[A-Z])\) ")
ANSWER = re.compile(r"^\s*(?P<number>\d+)\. \*\*(?P<letter>[A-Z])\*\*")
QUESTION = re.compile(r"^\s*\*\*(?:Câu |Question |問)(?P<number>\d+)\.\*\*")
QUESTIONS = 3
LETTERS = "ABC"


@dataclass(frozen=True)
class Quiz:
    questions: tuple[tuple[int, str], ...]  # (question number, its option letters), in order
    answers: tuple[tuple[int, str], ...]  # (question number, letter), in order

    @property
    def options(self) -> str:
        return "".join(options for _, options in self.questions)

    @property
    def key(self) -> str:
        return "".join(letter for _, letter in self.answers)

    @property
    def well_formed(self) -> bool:
        return (
            [number for number, _ in self.questions] == list(range(1, QUESTIONS + 1))
            and all(options == LETTERS for _, options in self.questions)
            and [number for number, _ in self.answers] == list(range(1, QUESTIONS + 1))
            and all(letter in LETTERS for _, letter in self.answers)
        )


def read_quiz(lines: Iterable[str]) -> Quiz:
    """The quiz in these lines of a quiz section, code blocks already left out."""
    questions: list[tuple[int, list[str]]] = []
    answers: list[tuple[int, str]] = []
    for line in lines:
        question = QUESTION.match(line)
        if question:
            questions.append((int(question.group("number")), []))
            continue
        option = OPTION.match(line)
        if option:
            if questions:
                questions[-1][1].append(option.group("letter"))
            continue
        answer = ANSWER.match(line)
        if answer:
            answers.append((int(answer.group("number")), answer.group("letter")))
    grouped = tuple((number, "".join(options)) for number, options in questions)
    return Quiz(grouped, tuple(answers))
