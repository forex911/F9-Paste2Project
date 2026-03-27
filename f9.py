#!/usr/bin/env python3
"""
tree_creator.py — Create directory/file structures from tree-format input.

Handles:
  - Clean Unix  'tree' output
  - Windows     'tree /f' output  (including malformed/mixed indentation)
  - Hand-drawn  ASCII trees

Usage:
  python tree_creator.py                        # paste from stdin (interactive)
  python tree_creator.py -f structure.txt       # read from file
  python tree_creator.py -c                     # read from clipboard
  python tree_creator.py --dry-run              # preview without creating
  python tree_creator.py --undo                 # remove last created structure
  python tree_creator.py -o /some/base/dir      # output to specific base directory
  python tree_creator.py -q                     # quiet mode (no per-item output)
  python tree_creator.py -v                     # verbose mode (extra detail)
  python tree_creator.py --log output.log       # also write log to file
"""

import os
import re
import sys
import json
import argparse
import datetime
from pathlib import Path

# ── ANSI colour helpers ───────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
CYAN   = "\033[36m"
YELLOW = "\033[33m"
RED    = "\033[31m"
DIM    = "\033[2m"

def supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

USE_COLOR = supports_color()

def c(text: str, *codes: str) -> str:
    if not USE_COLOR:
        return text
    return "".join(codes) + text + RESET

def info(msg):    print(c(msg, CYAN))
def success(msg): print(c(msg, GREEN, BOLD))
def warn(msg):    print(c(msg, YELLOW))
def error(msg):   print(c(msg, RED, BOLD), file=sys.stderr)
def dim(msg):     print(c(msg, DIM))


# ── Skip-line patterns ────────────────────────────────────────────────────────

SKIP_LINE_RE = re.compile(
    r'^\s*(?:'
    r'Folder PATH listing'
    r'|Volume (?:serial number|in drive)'
    r'|[A-Za-z]:[.\\/]?$'
    r'|[A-Za-z]:\\.*>tree'
    r')',
    re.IGNORECASE,
)

# Characters that are pure tree-graphics (never part of a file name)
TREE_GRAPHIC_CHARS = frozenset('│├└─|\\')


# ── Name extraction ───────────────────────────────────────────────────────────

def extract_name(line: str) -> str:
    """Strip all tree-drawing chars and return the bare file/dir name."""
    name = re.sub(r'[│├└─|\\]', '', line).strip()
    if '#' in name:
        name = name[:name.index('#')]
    return name.rstrip('/').strip()


def name_column(line: str) -> int:
    """
    Return the 0-based column index of the first character that is NOT a
    tree-graphic character or whitespace.  This is the raw indent level
    signal that works even for malformed / mixed Windows tree /f output.
    """
    for i, ch in enumerate(line):
        if ch not in TREE_GRAPHIC_CHARS and ch not in ' \t':
            return i
    return 0


def is_dir_hint(line: str) -> bool:
    """True when the line explicitly ends with '/' before any comment."""
    clean = line[:line.index('#')] if '#' in line else line
    return clean.rstrip().endswith('/')


def is_purely_structural(line: str) -> bool:
    """True when the line contains nothing but tree-graphic chars / spaces."""
    return not re.sub(r'[│├└─|\\  \t]', '', line).strip()


# ── Level normalisation ───────────────────────────────────────────────────────

def normalise_levels(raw_col: list[int]) -> list[int]:
    """
    Convert raw column positions into 0-based nesting levels.

    Strategy
    --------
    1. Find the minimum column (= level 0).
    2. Collect the sorted unique columns and map them to 0, 1, 2 …
       This is robust to any indent step size (4, 8, 2 …) and to
       the column offset introduced by Windows tree /f's leading │ chars.
    """
    if not raw_col:
        return []
    unique_sorted = sorted(set(raw_col))
    col_to_level  = {col: lvl for lvl, col in enumerate(unique_sorted)}
    return [col_to_level[c] for c in raw_col]


# ── Main parser ───────────────────────────────────────────────────────────────

def validate_name(name: str) -> tuple[bool, str]:
    if not name:
        return False, "empty name"
    if any(ch in '<>"|?*\x00' for ch in name):
        return False, "illegal character(s)"
    if ".." in Path(name).parts:
        return False, "path traversal"
    if Path(name).is_absolute():
        return False, "absolute path"
    return True, ""


def parse_lines(lines: list[str]) -> list[dict]:
    """
    Parse tree-formatted lines into a flat list of
      {'name': str, 'is_dir': bool, 'level': int}

    Works for:
      • Unix  'tree'   — 4-char indent groups (│   ├── └──)
      • Windows 'tree /f' — even when the output is malformed / mixed
      • Hand-drawn ASCII trees
    """
    pre_entries: list[dict] = []   # before level normalisation

    for raw in lines:
        line = raw.rstrip('\n\r')

        if not line or not line.strip():
            continue
        if SKIP_LINE_RE.match(line.strip()):
            continue
        if is_purely_structural(line):
            continue

        name = extract_name(line)
        if not name:
            continue
        # Skip bare drive-root tokens like "C:."
        if re.fullmatch(r'[A-Za-z]:[.\\/]?', name):
            continue
        if name.startswith('#'):
            continue

        ok, reason = validate_name(name)
        if not ok:
            warn(f"  ⚠  Skipping {name!r}: {reason}")
            continue

        pre_entries.append({
            "name":      name,
            "raw_col":   name_column(line),
            "_hint_dir": is_dir_hint(line),
        })

    if not pre_entries:
        return []

    # ── Normalise raw columns → levels ──────────────────────────────────────
    levels = normalise_levels([e["raw_col"] for e in pre_entries])

    entries: list[dict] = []
    for e, lvl in zip(pre_entries, levels):
        entries.append({
            "name":      e["name"],
            "level":     lvl,
            "is_dir":    e["_hint_dir"],
            "_hint_dir": e["_hint_dir"],
        })

    # ── Infer directories from structure ────────────────────────────────────
    # Any entry whose next sibling/child has a deeper level is a directory.
    for i, entry in enumerate(entries):
        if entry["_hint_dir"]:
            entry["is_dir"] = True
        elif i + 1 < len(entries) and entries[i + 1]["level"] > entry["level"]:
            entry["is_dir"] = True
        else:
            entry["is_dir"] = False
        del entry["_hint_dir"]

    return entries


# ── Structure creation ────────────────────────────────────────────────────────

UNDO_FILE = Path(".tree_creator_undo.json")


def create_structure(
    entries:   list[dict],
    base_dir:  Path,
    dry_run:   bool = False,
    quiet:     bool = False,
    verbose:   bool = False,
    log_lines: "list | None" = None,
) -> dict:
    """
    Walk entries and create dirs/files under base_dir.
    path_stack tracks the chain of ancestor directories so each item
    is placed under the correct parent regardless of raw indentation.
    """
    path_stack:    list[Path] = []
    created_dirs:  list[str]  = []
    created_files: list[str]  = []
    skipped:       list[str]  = []
    errors_list:   list[str]  = []

    def log(msg):
        if log_lines is not None:
            log_lines.append(msg)
        if not quiet:
            print(msg)

    for entry in entries:
        level  = entry["level"]
        name   = entry["name"]
        is_dir = entry["is_dir"]

        # Trim path_stack so it holds exactly `level` ancestor paths.
        # level 0 → no parent  → file/dir lives directly in base_dir
        # level 1 → one parent → lives inside path_stack[0]
        while len(path_stack) > level:
            path_stack.pop()

        parent = path_stack[-1] if path_stack else base_dir
        path   = parent / name

        try:
            rel = path.relative_to(base_dir)
        except ValueError:
            rel = path

        try:
            if is_dir:
                lbl = c("DIR  ", CYAN, BOLD) if USE_COLOR else "DIR  "
                if dry_run:
                    log(f"  {lbl} [dry-run] {rel}/")
                elif path.exists():
                    log(f"  {lbl} {c('exists', DIM)}  {rel}/")
                    skipped.append(str(rel) + "/")
                else:
                    path.mkdir(parents=True, exist_ok=True)
                    log(f"  {lbl} {rel}/")
                    created_dirs.append(str(rel) + "/")
                # Always push so children resolve under this dir
                path_stack.append(path)

            else:
                lbl = c("FILE ", GREEN, BOLD) if USE_COLOR else "FILE "
                if dry_run:
                    log(f"  {lbl} [dry-run] {rel}")
                elif path.exists():
                    log(f"  {lbl} {c('exists', DIM)}  {rel}")
                    skipped.append(str(rel))
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
                    log(f"  {lbl} {rel}")
                    created_files.append(str(rel))

        except PermissionError:
            msg = f"  {c('ERROR', RED, BOLD)} {rel}: permission denied"
            error(msg)
            if log_lines is not None:
                log_lines.append(msg)
            errors_list.append(str(rel))
        except OSError as exc:
            msg = f"  {c('ERROR', RED, BOLD)} {rel}: {exc}"
            error(msg)
            if log_lines is not None:
                log_lines.append(msg)
            errors_list.append(str(rel))

    return {
        "created_dirs":  created_dirs,
        "created_files": created_files,
        "skipped":       skipped,
        "errors":        errors_list,
    }


# ── Undo support ──────────────────────────────────────────────────────────────

def save_undo(summary: dict, base_dir: Path):
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "base_dir":  str(base_dir),
        "dirs":      summary["created_dirs"],
        "files":     summary["created_files"],
    }
    UNDO_FILE.write_text(json.dumps(data, indent=2))


def do_undo():
    if not UNDO_FILE.exists():
        error("No undo record found.")
        sys.exit(1)

    data     = json.loads(UNDO_FILE.read_text())
    base_dir = Path(data["base_dir"])
    ts       = data["timestamp"]

    warn(f"Undoing creation from {ts}  (base: {base_dir})")

    for rel in reversed(data["files"]):
        p = base_dir / rel
        if p.exists():
            p.unlink()
            dim(f"  removed file  {rel}")

    for rel in reversed(data["dirs"]):
        p = base_dir / rel.rstrip("/")
        if p.exists():
            try:
                p.rmdir()
                dim(f"  removed dir   {rel}")
            except OSError:
                warn(f"  non-empty, skipped: {rel}")

    UNDO_FILE.unlink()
    success("✅ Undo complete.")


# ── Input helpers ─────────────────────────────────────────────────────────────

def read_stdin_interactive() -> list[str]:
    eof = "CTRL+Z then ENTER" if sys.platform == "win32" else "CTRL+D"
    info(f"Paste your tree structure, then press {eof}:")
    print(c("-" * 50, DIM))
    try:
        return sys.stdin.readlines()
    except KeyboardInterrupt:
        print()
        error("Interrupted.")
        sys.exit(1)


def read_file(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        error(f"File not found: {path}")
        sys.exit(1)
    try:
        return p.read_text(encoding="utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        error(f"Could not decode {path} as UTF-8.")
        sys.exit(1)


def read_clipboard() -> list[str]:
    try:
        import subprocess
        if sys.platform == "darwin":
            text = subprocess.check_output("pbpaste", text=True)
        elif sys.platform == "win32":
            import tkinter as tk
            root = tk.Tk(); root.withdraw()
            text = root.clipboard_get(); root.destroy()
        else:
            try:
                text = subprocess.check_output(
                    ["xclip", "-selection", "clipboard", "-o"], text=True
                )
            except FileNotFoundError:
                text = subprocess.check_output(
                    ["xsel", "--clipboard", "--output"], text=True
                )
    except Exception as exc:
        error(f"Clipboard read failed: {exc}")
        sys.exit(1)
    return text.splitlines(keepends=True)


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(summary: dict, dry_run: bool):
    d = len(summary["created_dirs"])
    f = len(summary["created_files"])
    s = len(summary["skipped"])
    e = len(summary["errors"])

    sep = c("─" * 50, DIM)
    print(sep)
    if dry_run:
        info(f"  DRY-RUN — nothing written to disk")
        info(f"  Would create: {d} dir(s), {f} file(s)")
    else:
        success(f"  ✅  Created : {d} dir(s), {f} file(s)")
        if s:
            warn(f"  ⚠   Skipped : {s} (already existed)")
        if e:
            error(f"  ✖   Errors  : {e}")
    print(sep)


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Create a directory/file tree from a text structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("-f", "--file",      metavar="PATH",
                     help="Read from a text file")
    src.add_argument("-c", "--clipboard", action="store_true",
                     help="Read from the clipboard")

    p.add_argument("-o", "--output-dir", metavar="DIR", default=".",
                   help="Base directory (default: cwd)")
    p.add_argument("--dry-run",          action="store_true",
                   help="Preview without touching the filesystem")
    p.add_argument("--undo",             action="store_true",
                   help="Remove the last created structure")
    p.add_argument("--no-color",         action="store_true",
                   help="Disable coloured output")

    vg = p.add_mutually_exclusive_group()
    vg.add_argument("-q", "--quiet",   action="store_true",
                    help="Suppress per-item output")
    vg.add_argument("-v", "--verbose", action="store_true",
                    help="Extra detail")
    p.add_argument("--log", metavar="FILE",
                   help="Also write output to a log file")
    return p


def main():
    parser = build_parser()
    args   = parser.parse_args()

    global USE_COLOR
    if args.no_color:
        USE_COLOR = False

    if args.undo:
        do_undo()
        return

    base_dir = Path(args.output_dir).resolve()
    if not base_dir.exists():
        try:
            base_dir.mkdir(parents=True)
            info(f"Created output directory: {base_dir}")
        except OSError as exc:
            error(f"Cannot create {base_dir}: {exc}")
            sys.exit(1)
    if not base_dir.is_dir():
        error(f"Not a directory: {base_dir}")
        sys.exit(1)

    if args.file:
        lines = read_file(args.file)
        if not args.quiet:
            dim(f"  Source: {args.file}")
    elif args.clipboard:
        lines = read_clipboard()
        if not args.quiet:
            dim("  Source: clipboard")
    else:
        lines = read_stdin_interactive()

    if not lines:
        error("No input received.")
        sys.exit(1)

    entries = parse_lines(lines)
    if not entries:
        error("No valid entries found after parsing.")
        sys.exit(1)

    if args.verbose and not args.quiet:
        dim(f"  Entries parsed: {len(entries)}")

    if not args.quiet:
        label = c("DRY-RUN — ", YELLOW, BOLD) if args.dry_run else ""
        print()
        info(f"  {label}Output → {base_dir}")
        print(c("─" * 50, DIM))

    log_lines: "list | None" = [] if args.log else None

    summary = create_structure(
        entries,
        base_dir=base_dir,
        dry_run=args.dry_run,
        quiet=args.quiet,
        verbose=args.verbose,
        log_lines=log_lines,
    )

    print_summary(summary, dry_run=args.dry_run)

    if not args.dry_run and (summary["created_dirs"] or summary["created_files"]):
        save_undo(summary, base_dir)
        if args.verbose:
            dim(f"  Undo record → {UNDO_FILE}")

    if args.log and log_lines is not None:
        try:
            with open(args.log, "w", encoding="utf-8") as fh:
                fh.write(f"tree_creator log — {datetime.datetime.now()}\n")
                fh.write(f"base_dir: {base_dir}\n")
                fh.write("─" * 50 + "\n")
                fh.write("\n".join(log_lines) + "\n")
            dim(f"  Log → {args.log}")
        except OSError as exc:
            warn(f"Could not write log: {exc}")

    if summary["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
