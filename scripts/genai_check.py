#!/usr/bin/env python3
"""Check the Vietnamese Generative AI slide store and hand out its lessons without overlap.

The store `genai-for-beginners/vi/` turns the 21 lessons of microsoft/generative-ai-for-beginners
into Vietnamese lessons and Moda slide decks (docs/genai-slides.md). Several Claude sessions build
them at once, so who may take which lesson is computable and lives here, not in a reviewer's head:

  check            (default) every lesson folder, the source map and the assignment board
  status           every lesson: free, doing or done, read from this checkout and every origin/* branch
  claim ID...      write the `doing` record of lessons assigned to the current branch
                   (--take-over: the board moved the lesson here from a branch whose session died)
  scope            fail unless this branch changes only its own lesson folders (run before opening a PR)

What `check` enforces, per `lessons/<id>/`:
  - the id is in source-map.json; the folder holds only lesson.md, deck.yaml and <id>.pptx
  - deck.yaml is a `doing` record (id, status, owner, session, claimed_at) or a `done` record (adds
    done_at, moda_canvas, moda_url, slide_count, size, exports, layouts, review)
  - a done deck: 10 to 12 slides, size 1920x1080, exports pending | badged, review passed, and the
    layout table of docs/genai-slides.md (known kinds, one per slide, at least five kinds, never the
    same kind on two adjacent slides, the first concept on its signature kind or a named fallback)
  - lesson.md, once the deck is done (a `doing` lesson may hold a draft): a `# ` title, `## Từ viết tắt`
    as the first section, `## Nhìn hình trả lời` and `## Nguồn đối chiếu` sections, the latter linking
    the pinned source file and crediting it (MIT), and no code fence left open
  - <id>.pptx exists exactly when exports is badged: a whole ZIP holding a presentation, with as
    many slides as slide_count and the moda.app badge on every slide (it is never removed)
The board (assignments.yaml) gives each id to at most one branch, and only ids of the source map.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys
import zipfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE_REL = "genai-for-beginners/vi"
STORE = ROOT / STORE_REL
LESSON_ID = re.compile(r"ga-(\d{2})")
RANGE = re.compile(r"(ga-\d{2})\.\.(ga-\d{2})")
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
CANVAS_ID = re.compile(r"cvs_[0-9A-Za-z]{20,}")
MODA_URL = "https://moda.app/canvas/"
DECK_SIZE = "1920x1080"
SLIDE_COUNTS = range(10, 13)  # docs/genai-slides.md: 10 to 12 slides
STATUSES = ("doing", "done")
EXPORTS = ("pending", "badged")
REVIEWS = ("passed",)  # a deck is done only after the reviewer agent's findings are settled
BOARD_STATUSES = ("assigned", "done")
DOING_KEYS = {"id", "status", "owner", "session", "claimed_at"}
DONE_KEYS = DOING_KEYS | {"done_at", "moda_canvas", "moda_url", "slide_count", "size", "exports", "layouts", "review"}
# docs/genai-slides.md, *Bố cục*: the closed list of layout kinds, in the order that fixes the signature layout
# (the first concept's slide takes the kind at position lesson number mod 12, counted from 0)
LAYOUT_KINDS = ("sequence-diagram", "flow", "two-column-comparison", "2x2-matrix", "lookup-table", "card-grid",
                "numbered-rows", "connection-diagram", "layers", "timeline", "one-big-number", "one-highlighted-sentence")
MIN_LAYOUT_KINDS = 5
LAYOUT_KEYS = {"slides", "first_concept", "cannot"}
FIRST_SECTION = "Từ viết tắt"
SOURCES_SECTION = "Nguồn đối chiếu"
CREDIT = ("microsoft/generative-ai-for-beginners", "MIT")  # docs/genai-slides.md: the attribution line
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
SETUP_BRANCH = "origin/claude/genai-slides-setup"  # the base of the worker branches until it merges into main
REQUIRED_SECTIONS = ("Từ viết tắt", "Nhìn hình trả lời", "Nguồn đối chiếu")
PPTX_PARTS = ("[Content_Types].xml", "ppt/presentation.xml")
PPTX_SLIDE = re.compile(r"ppt/slides/slide\d+\.xml")
MODA_BADGE = b"moda-export-watermark"  # the picture Moda's free plan puts on every slide it exports
MAX_PPTX_BYTES = 512 * 1024 * 1024


class GitError(Exception):
    """git could not be read: nothing is decided on a guess (exit 2)."""


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def load_source_map(store: pathlib.Path) -> dict[str, dict]:
    data = json.loads((store / "source-map.json").read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in data["lessons"]}


def expand_range(text: object) -> list[str] | None:
    """`ga-01..ga-07` as its ids, or None when it is not a range."""
    match = RANGE.fullmatch(text) if isinstance(text, str) else None
    if not match:
        return None
    first, last = (int(LESSON_ID.fullmatch(part).group(1)) for part in match.groups())
    return [f"ga-{number:02d}" for number in range(first, last + 1)] if first <= last else None


def load_board(store: pathlib.Path) -> object:
    return yaml.safe_load((store / "assignments.yaml").read_text(encoding="utf-8"))


def board_problems(board: object, known: set[str]) -> list[str]:
    if not isinstance(board, list):
        return ["assignments.yaml must be a list of rows (range, branch, status)"]
    problems: list[str] = []
    seen: dict[str, int] = {}
    for number, row in enumerate(board, start=1):
        if not (isinstance(row, dict) and set(row) == {"range", "branch", "status"}):
            problems.append(f"assignments.yaml row {number}: needs exactly range, branch and status")
            continue
        ids = expand_range(row["range"])
        if ids is None:
            problems.append(f"assignments.yaml row {number}: range must look like ga-01..ga-07")
            continue
        if not _text(row["branch"]):
            problems.append(f"assignments.yaml row {number}: branch is missing")
        if row["status"] not in BOARD_STATUSES:
            problems.append(f"assignments.yaml row {number}: status must be one of {', '.join(BOARD_STATUSES)}")
        for lesson_id in ids:
            if lesson_id not in known:
                problems.append(f"assignments.yaml row {number}: {lesson_id} is not in source-map.json")
            elif lesson_id in seen:
                problems.append(f"assignments.yaml: {lesson_id} is in rows {seen[lesson_id]} and {number}")
            else:
                seen[lesson_id] = number
    return problems


def assigned_branch(board: list[dict], lesson_id: str) -> tuple[str, str] | None:
    """The branch a lesson is assigned to and the row's status, or None."""
    for row in board:
        if lesson_id in (expand_range(row.get("range")) or []):
            return row.get("branch"), row.get("status")
    return None


def layout_problems(layouts: object, lesson_id: str, slide_count: object) -> list[str]:
    """What is wrong with a deck's layout table; empty when it holds."""
    if not isinstance(layouts, dict):
        return ["layouts must be a mapping with slides, first_concept and, after a fallback, cannot"]
    problems = [f"layouts: key {key!r} is not allowed" for key in layouts if key not in LAYOUT_KEYS]
    kinds = layouts.get("slides")
    if not (isinstance(kinds, list) and all(isinstance(kind, str) for kind in kinds)):
        return problems + ["layouts: slides must be the list of every slide's layout kind, in order"]
    unknown = sorted({kind for kind in kinds if kind not in LAYOUT_KINDS})
    if unknown:
        problems.append(f"layouts: {', '.join(repr(kind) for kind in unknown)} is not one of the kinds "
                        f"({', '.join(LAYOUT_KINDS)})")
    total = slide_count if _count(slide_count) else len(kinds)
    if len(kinds) != total:
        problems.append(f"layouts: slides holds {len(kinds)} kinds for {total} slides; one kind per slide")
    if len(set(kinds)) < MIN_LAYOUT_KINDS:
        problems.append(f"layouts: {len(set(kinds))} different kinds; a deck uses at least {MIN_LAYOUT_KINDS}")
    repeats = [f"{number} and {number + 1}" for number, (before, after) in enumerate(zip(kinds, kinds[1:]), start=1)
               if before == after]
    if repeats:
        problems.append(f"layouts: the same kind on adjacent slides {', '.join(repeats)}")
    first = layouts.get("first_concept")
    if not (_count(first) and 2 <= first <= total - 1):
        return problems + [f"layouts: first_concept must be the number of the first concept's slide, from 2 to "
                           f"{total - 1} (the cover and the terms and sources slide are not concepts)"]
    cannot = layouts.get("cannot", {})
    if not (isinstance(cannot, dict) and all(isinstance(kind, str) and _text(why) for kind, why in cannot.items())):
        return problems + ["layouts: cannot must give, for each kind that could not show the content, the reason"]
    match = LESSON_ID.fullmatch(lesson_id)
    if first > len(kinds) or kinds[first - 1] not in LAYOUT_KINDS or not match:
        return problems
    start = int(match.group(1)) % len(LAYOUT_KINDS)
    chosen = LAYOUT_KINDS.index(kinds[first - 1])
    passed = [LAYOUT_KINDS[(start + step) % len(LAYOUT_KINDS)] for step in range((chosen - start) % len(LAYOUT_KINDS))]
    if sorted(cannot) != sorted(passed):
        problems.append(f"layouts: slide {first}, the first concept's, takes {LAYOUT_KINDS[start]} for {lesson_id} or, "
                        f"when the content cannot be shown that way, the next kind that can; it is {kinds[first - 1]}, "
                        f"so cannot must name {', '.join(passed) or 'no kind'} and names "
                        f"{', '.join(sorted(cannot)) or 'no kind'}")
    return problems


def record_problems(record: object, lesson_id: str) -> list[str]:
    """What is wrong with one deck.yaml; empty when it is well formed."""
    if not isinstance(record, dict):
        return ["deck.yaml is not a mapping"]
    status = record.get("status")
    if status not in STATUSES:
        return [f"status must be one of {', '.join(STATUSES)}"]
    allowed = DOING_KEYS if status == "doing" else DONE_KEYS
    problems = [f"key {key!r} is not allowed on a {status} record" for key in record if key not in allowed]
    problems += [f"key {key!r} is missing" for key in sorted(allowed - set(record))]
    if record.get("id") != lesson_id:
        problems.append(f"id must be {lesson_id}")
    for key in ("owner", "session"):
        if key in record and not _text(record[key]):
            problems.append(f"{key} must be text")
    for key in ("claimed_at", "done_at"):
        if key in record and not (isinstance(record[key], str) and STAMP.fullmatch(record[key])):
            problems.append(f"{key} must look like 2026-10-20T09:00:00Z")
    if status == "doing":
        return problems
    if "moda_canvas" in record and not (isinstance(record["moda_canvas"], str)
                                        and CANVAS_ID.fullmatch(record["moda_canvas"])):
        problems.append("moda_canvas must be the cvs_ id of the Moda canvas")
    url = record.get("moda_url")
    if "moda_url" in record and not (isinstance(url, str) and url.startswith(MODA_URL) and len(url) > len(MODA_URL)
                                     and " " not in url):
        problems.append(f"moda_url must start with {MODA_URL}")
    if "slide_count" in record and not (_count(record["slide_count"]) and record["slide_count"] in SLIDE_COUNTS):
        problems.append(f"slide_count must be between {SLIDE_COUNTS.start} and {SLIDE_COUNTS.stop - 1}")
    if "size" in record and record["size"] != DECK_SIZE:
        problems.append(f"size must be {DECK_SIZE}")
    if "exports" in record and record["exports"] not in EXPORTS:
        problems.append(f"exports must be one of {', '.join(EXPORTS)}")
    if "review" in record and record["review"] not in REVIEWS:
        problems.append("review must be passed: a deck is done only once the reviewer agent's findings are settled")
    if "layouts" in record:
        problems += layout_problems(record["layouts"], lesson_id, record.get("slide_count"))
    return problems


def scan_fences(text: str) -> tuple[list[tuple[str, bool]], bool]:
    """Every line with whether it sits in a code fence, and whether a fence is left open. A fence closes on a
    line of the same character at least as long as its opener (CommonMark); a backtick opener cannot hold a
    backtick in its info string, so an inline ```x``` is not a fence."""
    lines: list[tuple[str, bool]] = []
    opener = None
    for line in text.splitlines():
        match = FENCE.fullmatch(line)
        if opener is None:
            if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
                opener = match.group(1)
            lines.append((line, opener is not None))
            continue
        if (match and match.group(1)[0] == opener[0] and len(match.group(1)) >= len(opener)
                and not match.group(2).strip()):
            opener = None
        lines.append((line, True))
    return lines, opener is not None


def sections(text: str) -> list[tuple[str, str]]:
    """Every `## ` section of a Markdown text as (heading, body), outside code fences."""
    found: list[tuple[str, list[str]]] = []
    for line, fenced in scan_fences(text)[0]:
        if not fenced and line.startswith("## "):
            found.append((line[3:].strip(), []))
        elif found:
            found[-1][1].append(line)
    return [(heading, "\n".join(body)) for heading, body in found]


def lesson_problems(text: str, entry: dict) -> list[str]:
    problems: list[str] = []
    if not text.startswith("# "):
        problems.append("lesson.md must start with a `# ` title")
    if scan_fences(text)[1]:
        problems.append("lesson.md leaves a code fence open")
    found = sections(text)
    headings = [heading for heading, _ in found]
    if not headings or headings[0] != FIRST_SECTION:
        problems.append(f"lesson.md: the first section must be `## {FIRST_SECTION}`")
    for name in REQUIRED_SECTIONS:
        if name not in headings:
            problems.append(f"lesson.md: section `## {name}` is missing")
    sources = "\n".join(body for heading, body in found if heading == SOURCES_SECTION)
    if SOURCES_SECTION in headings:
        if entry["source_url"] not in sources:
            problems.append(f"lesson.md: `## {SOURCES_SECTION}` must link the pinned source {entry['source_url']}")
        if not all(word in sources for word in CREDIT):
            problems.append(f"lesson.md: `## {SOURCES_SECTION}` must credit the source: "
                            "microsoft/generative-ai-for-beginners (MIT License, © Microsoft Corporation)")
    return problems


def pptx_damage(path: pathlib.Path) -> str | None:
    """Why a file is not a whole PowerPoint presentation, or None."""
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if sum(info.file_size for info in archive.infolist()) > MAX_PPTX_BYTES:
                return f"its parts add up to more than {MAX_PPTX_BYTES >> 20} MB unpacked"
            try:
                damaged = archive.testzip()
            except Exception:  # every codec has its own error for a part it cannot unpack
                return "a part cannot be read (unsupported compression, encryption or damaged data)"
    except (zipfile.BadZipFile, OSError):
        return "not a ZIP archive"
    if damaged:
        return f"{damaged} is damaged"
    missing = [part for part in PPTX_PARTS if part not in names]
    return f"{', '.join(missing)} missing" if missing else None


def pptx_badges(path: pathlib.Path) -> tuple[int, int]:
    """How many slides carry Moda's badge, and how many slides the file has."""
    with zipfile.ZipFile(path) as archive:
        slides = [name for name in archive.namelist() if PPTX_SLIDE.fullmatch(name)]
        return sum(MODA_BADGE in archive.read(name) for name in slides), len(slides)


def folder_problems(folder: pathlib.Path, entry: dict) -> list[str]:
    lesson_id = entry["id"]
    allowed = {"lesson.md", "deck.yaml", f"{lesson_id}.pptx"}
    problems = [f"{path.name} does not belong in a lesson folder (only {', '.join(sorted(allowed))})"
                for path in sorted(folder.iterdir()) if path.name not in allowed or not path.is_file()
                or path.is_symlink()]
    deck = folder / "deck.yaml"
    if not deck.is_file():
        return problems + ["deck.yaml is missing: a lesson folder exists only once the lesson is claimed"]
    try:
        record = yaml.safe_load(deck.read_text(encoding="utf-8"))
    except (yaml.YAMLError, ValueError) as error:
        return problems + [f"deck.yaml does not parse: {error}"]
    problems += record_problems(record, lesson_id)
    done = isinstance(record, dict) and record.get("status") == "done"
    lesson = folder / "lesson.md"
    if lesson.is_file() and done:
        try:
            problems += lesson_problems(lesson.read_text(encoding="utf-8"), entry)
        except ValueError as error:
            problems.append(f"lesson.md is not UTF-8 text: {error}")
    elif done:
        problems.append("lesson.md is missing: a done deck is built from its lesson")
    pptx = folder / f"{lesson_id}.pptx"
    badged = done and record.get("exports") == "badged"
    if pptx.is_file() and not badged:
        problems.append(f"{pptx.name} is here but the record does not say exports: badged")
    elif badged and not pptx.is_file():
        problems.append(f"exports is badged but {pptx.name} is missing")
    elif badged:
        damage = pptx_damage(pptx)
        if damage:
            problems.append(f"{pptx.name}: {damage}")
        else:
            badges, slides = pptx_badges(pptx)
            if slides != record.get("slide_count"):
                problems.append(f"{pptx.name} has {slides} slides; the record says {record.get('slide_count')}")
            if badges != slides:
                problems.append(f"{pptx.name}: {slides - badges} slides lack the moda.app badge; export the deck "
                                "as Moda gives it and never edit the file")
    return problems


def check(store: pathlib.Path = STORE) -> list[str]:
    try:
        source = load_source_map(store)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f"source-map.json cannot be read: {error}"]
    problems = [f"source-map.json: {lesson_id} has no source_url" for lesson_id, entry in source.items()
                if not _text(entry.get("source_url"))]
    try:
        problems += board_problems(load_board(store), set(source))
    except (OSError, yaml.YAMLError) as error:
        problems.append(f"assignments.yaml cannot be read: {error}")
    lessons = store / "lessons"
    for folder in sorted(lessons.iterdir()) if lessons.is_dir() else []:
        if folder.name not in source or not folder.is_dir() or folder.is_symlink():
            problems.append(f"lessons/{folder.name}: not a lesson of source-map.json")
            continue
        problems += [f"lessons/{folder.name}: {problem}" for problem in folder_problems(folder, source[folder.name])]
    return problems


def git(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def current_branch() -> str:
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch == "HEAD":
        raise GitError("detached HEAD: check out the branch the board assigns you")
    return branch


def parse_held(text: str, where: str) -> dict:
    """A deck record read from a branch; one that cannot be read still holds its lesson."""
    try:
        record = yaml.safe_load(text)
    except (yaml.YAMLError, ValueError):
        record = None
    return record if isinstance(record, dict) else {"owner": f"an unreadable deck.yaml on {where}", "status": "doing"}


def refresh(args: argparse.Namespace) -> None:
    """Fetch every branch of origin: a cloud session's clone tracks only main, and a claim that cannot see the
    other sessions' branches protects nothing."""
    if not args.no_fetch:
        git("fetch", "--quiet", "origin", "+refs/heads/*:refs/remotes/origin/*")


def remote_refs() -> list[str]:
    return [ref for ref in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").split()
            if ref not in ("origin", "origin/HEAD")]


def holders() -> dict[str, list[tuple[str, dict]]]:
    """Every deck.yaml on every origin/* branch and in this checkout, as id -> [(where, record)]."""
    found: dict[str, list[tuple[str, dict]]] = {}
    for ref in remote_refs():
        listing = git("ls-tree", "-r", "--name-only", ref, "--", f"{STORE_REL}/lessons")
        for path in listing.split():
            parts = path.split("/")
            if parts[-1] != "deck.yaml" or len(parts) != 5:
                continue
            found.setdefault(parts[-2], []).append((ref, parse_held(git("show", f"{ref}:{path}"), ref)))
    for deck in sorted((STORE / "lessons").glob("ga-*/deck.yaml")):
        text = deck.read_bytes().decode("utf-8", errors="replace")
        found.setdefault(deck.parent.name, []).append(("checkout", parse_held(text, "this checkout")))
    return found


def claim_problem(lesson_id: str, branch: str, board: list[dict], held: list[tuple[str, dict]],
                  take_over: bool = False) -> str | None:
    """Why the current branch may not claim a lesson, or None. The board is the authority: with take_over, a
    `doing` record of another branch (whose session died and whose range the coordinator moved here) yields;
    a `done` deck never does."""
    assignment = assigned_branch(board, lesson_id)
    if assignment is None:
        return f"{lesson_id} is on no row of assignments.yaml; ask the coordinator"
    owner, status = assignment
    if owner != branch:
        return f"{lesson_id} is assigned to {owner}, not to {branch}"
    if status != "assigned":
        return f"{lesson_id}'s range is {status}; it takes no more work"
    for where, record in held:
        if record.get("owner") == branch:
            continue
        if record.get("status") == "done":
            return f"{lesson_id} is already done by {record.get('owner')} ({where})"
        if not take_over:
            return (f"{lesson_id} is already held by {record.get('owner')} ({where}); if the coordinator moved it "
                    "to this branch, claim it with --take-over")
    return None


def scope_problems(paths: list[str], ids: list[str]) -> list[str]:
    """Each changed path outside the lesson folders of the given ids."""
    prefixes = tuple(f"{STORE_REL}/lessons/{lesson_id}/" for lesson_id in ids)
    return [f"{path} is outside this branch's lesson folders" for path in paths if not path.startswith(prefixes)]


def stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_status(args: argparse.Namespace) -> int:
    source = load_source_map(STORE)
    board = load_board(STORE)
    problems = board_problems(board, set(source))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    refresh(args)
    found = holders()
    for lesson_id, entry in source.items():
        assignment = assigned_branch(board, lesson_id)
        records = found.get(lesson_id, [])
        done = [r for _, r in records if r.get("status") == "done"]
        doing = [r for _, r in records if r.get("status") == "doing"]
        if done:
            state = f"done by {done[0].get('owner')} (exports {done[0].get('exports')})"
        elif doing:
            state = f"doing by {doing[0].get('owner')}"
        else:
            state = "free"
        owners = {r.get("owner") for _, r in records if r.get("owner")}
        warning = "  WARNING: held by several branches" if len(owners) > 1 else ""
        where = assignment[0] if assignment else "unassigned"
        print(f"{lesson_id}  {state:<45} board: {where}{warning}  {entry['title_vi']}")
    return 0


def cmd_claim(args: argparse.Namespace) -> int:
    source = load_source_map(STORE)
    board = load_board(STORE)
    problems = board_problems(board, set(source))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    branch = current_branch()
    refresh(args)
    if not remote_refs():
        print("no origin/* branch is known (run `git fetch origin`): a claim cannot see other sessions", file=sys.stderr)
        return 2
    found = holders()
    refusals = [problem for lesson_id in args.ids for problem in
                [f"{lesson_id} is not in source-map.json" if lesson_id not in source
                 else claim_problem(lesson_id, branch, board, found.get(lesson_id, []), args.take_over)] if problem]
    if refusals:
        print("\n".join(refusals), file=sys.stderr)
        return 1
    for lesson_id in args.ids:
        deck = STORE / "lessons" / lesson_id / "deck.yaml"
        record = yaml.safe_load(deck.read_text(encoding="utf-8")) if deck.exists() else None
        if isinstance(record, dict) and record.get("owner") == branch:
            print(f"{lesson_id}: already claimed by this branch")
            continue
        if isinstance(record, dict) and record.get("status") == "doing":  # --take-over of a record in this checkout
            verb = f"taken over from {record.get('owner')}"
            record.update(owner=branch, session=args.session)
        else:
            record = {"id": lesson_id, "status": "doing", "owner": branch, "session": args.session,
                      "claimed_at": stamp()}
            verb = "claimed"
        deck.parent.mkdir(parents=True, exist_ok=True)
        deck.write_text(yaml.safe_dump(record, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"{lesson_id}: {verb} for {branch}; commit and push it before building")
    return 0


def cmd_scope(args: argparse.Namespace) -> int:
    board = load_board(STORE)
    problems = board_problems(board, set(load_source_map(STORE)))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    branch = current_branch()
    refresh(args)
    ids = [lesson_id for row in board if row["branch"] == branch for lesson_id in expand_range(row["range"])]
    base = args.base or (SETUP_BRANCH if SETUP_BRANCH in remote_refs() else "origin/main")
    paths = git("diff", "--name-only", f"{base}...HEAD").split()
    problems = scope_problems(paths, ids)
    for problem in problems:
        print(problem)
    print(f"{len(problems)} path(s) out of scope against {base}" if problems
          else f"scope OK: {len(paths)} changed path(s) against {base}, all in {branch}'s lesson folders")
    return 1 if problems else 0


def cmd_check(_args: argparse.Namespace) -> int:
    problems = check()
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problem(s)" if problems else "genai store OK")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-fetch", action="store_true",
                        help="do not fetch every origin branch first (status, claim and scope fetch by default)")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="check the store (default)")
    sub.add_parser("status", help="free / doing / done for every lesson, across origin/* branches")
    claim = sub.add_parser("claim", help="claim lessons assigned to the current branch")
    claim.add_argument("ids", nargs="+")
    claim.add_argument("--session", required=True, help="this session's id (session_...)")
    claim.add_argument("--take-over", action="store_true",
                       help="take a `doing` lesson from a branch the board no longer assigns it to")
    scope = sub.add_parser("scope", help="fail unless this branch changes only its own lesson folders")
    scope.add_argument("--base", help=f"compare against this ref (default {SETUP_BRANCH} while it exists, "
                                      "else origin/main)")
    args = parser.parse_args(argv)
    command = {"status": cmd_status, "claim": cmd_claim, "scope": cmd_scope}.get(args.command, cmd_check)
    try:
        return command(args)
    except BrokenPipeError:  # `status | head`
        return 0
    except (GitError, OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
