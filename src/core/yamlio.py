"""Strict YAML and text loading for the hand-edited files under course/.

Two traps in plain `yaml.safe_load` matter for a content store edited by hand:

- a mapping that names the same key twice keeps the last value without a word,
  so a lesson with two `title:` lines silently loses one; and
- files saved on Windows arrive with a BOM or CRLF line endings.

`loads` refuses the first and `read_text` normalizes the second.
"""

from __future__ import annotations

from pathlib import Path

import yaml


class ContentYAMLError(ValueError):
    """A content file is not valid YAML, or names a key twice."""


# libyaml's parser when PyYAML was built with it (the PyPI wheels are), which is
# several times faster; construction — and so the duplicate-key rule below — is
# the same Python code either way.
_SafeLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


class _StrictLoader(_SafeLoader):
    """A safe loader that refuses a mapping which names the same key twice."""

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
            seen = set()
            for key_node, _value in node.value:
                key = self.construct_object(key_node, deep=True)
                try:
                    duplicate = key in seen
                except TypeError:  # an unhashable key; the base class reports it
                    continue
                if duplicate:
                    raise yaml.constructor.ConstructorError(
                        "while constructing a mapping", node.start_mark,
                        f"found duplicate key {key!r}", key_node.start_mark,
                    )
                seen.add(key)
        return super().construct_mapping(node, deep=deep)


def read_text(path: Path) -> str:
    """The file as UTF-8 text, without a BOM and with `\\n` line endings.

    Raises UnicodeDecodeError when the file is not UTF-8.
    """
    text = path.read_text(encoding="utf-8-sig")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def loads(text: str):
    """Parse YAML text strictly; raise ContentYAMLError with a one-line reason."""
    try:
        return yaml.load(text, Loader=_StrictLoader)  # noqa: S506 - _StrictLoader is a safe loader
    except yaml.YAMLError as exc:
        raise ContentYAMLError(" ".join(str(exc).split())) from exc
