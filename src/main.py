"""Command line for the course content store. Run it from the repository root:

    python -m src.main validate                      # check everything (CI runs this)
    python -m src.main stats                         # course size and writing progress
    python -m src.main build [--check]               # course homes, glossary pages, infographics
    python -m src.main scaffold <lesson-id>          # start a lesson in every language
    python -m src.main fb-draft <lesson-id> [--post-lang vi] [--out FILE]

`--lang vi|en|ja` picks the language of the messages (otherwise $APP_LANG, then
the system language). Exit status: 0 success, 1 content problems, 2 bad usage.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.core.model import ROOT
from src.core.validate import validate
from src.tools import build, fb_draft, scaffold, stats
from src.utils.catalogs import translator
from src.utils.console import print_findings
from src.utils.i18n import Translator


def _common(tr: Translator, *, on_subcommand: bool) -> argparse.ArgumentParser:
    """--lang and --root, accepted both before and after the command name."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--lang", choices=tr.locales,
        default=argparse.SUPPRESS if on_subcommand else None,
        help=tr.t("cli.lang_help", choices=", ".join(tr.locales)),
    )
    common.add_argument(
        "--root", type=Path,
        default=argparse.SUPPRESS if on_subcommand else ROOT,
        help=tr.t("cli.root_help"),
    )
    return common


def build_parser(tr: Translator) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.main", description=tr.t("cli.description"),
        parents=[_common(tr, on_subcommand=False)],
    )
    commands = parser.add_subparsers(
        dest="command", required=True, metavar="COMMAND", title=tr.t("cli.commands_title"),
    )

    def command(name: str, help_key: str) -> argparse.ArgumentParser:
        return commands.add_parser(
            name, help=tr.t(help_key), description=tr.t(help_key),
            parents=[_common(tr, on_subcommand=True)],
        )

    command("validate", "cli.validate_help")
    command("stats", "cli.stats_help")
    build_parser_ = command("build", "cli.build_help")
    build_parser_.add_argument("--check", action="store_true", help=tr.t("cli.build_check_help"))
    scaffold_parser = command("scaffold", "cli.scaffold_help")
    scaffold_parser.add_argument("lesson", help=tr.t("cli.lesson_help"))
    fb_parser = command("fb-draft", "cli.fb_help")
    fb_parser.add_argument("lesson", help=tr.t("cli.lesson_help"))
    fb_parser.add_argument("--post-lang", choices=tr.locales, help=tr.t("cli.post_lang_help"))
    fb_parser.add_argument("--out", type=Path, help=tr.t("cli.out_help"))
    return parser


def run_validate(root: Path, tr: Translator) -> int:
    report = validate(root)
    print_findings(report.findings, tr)
    if report.ok:
        print(tr.t("validate.ok", files=len(report.docs), warnings=len(report.warnings)))
        return 0
    print(tr.t("validate.failed", errors=len(report.errors), warnings=len(report.warnings)))
    return 1


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # Japanese and Vietnamese on a Windows console
    arguments = sys.argv[1:] if argv is None else list(argv)
    early = argparse.ArgumentParser(add_help=False)
    early.add_argument("--lang")
    known, _ = early.parse_known_args(arguments)
    tr = translator(known.lang)
    args = build_parser(tr).parse_args(arguments)
    root = args.root.resolve()
    if args.command == "validate":
        return run_validate(root, tr)
    if args.command == "stats":
        return stats.run(root, tr)
    if args.command == "build":
        return build.run(root, tr, check=args.check)
    if args.command == "scaffold":
        return scaffold.run(root, tr, args.lesson)
    return fb_draft.run(root, tr, args.lesson, args.post_lang, args.out)


if __name__ == "__main__":
    sys.exit(main())
