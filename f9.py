#!/usr/bin/env python3
"""
f9.py — Create directory/file structures from tree-format input.

Usage:
  python f9.py                        # paste from stdin (interactive)
  python f9.py -f structure.txt       # read from file
  python f9.py -c                     # read from clipboard
  python f9.py --dry-run              # preview without creating
  python f9.py --undo                 # remove last created structure
  python f9.py -o /some/base/dir      # output to specific base directory
  python f9.py -q                     # quiet mode (no per-item output)
  python f9.py -v                     # verbose mode (extra detail)
  python f9.py --log output.log       # also write log to file
"""

import os
import sys
import json
import shutil
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
BLUE   = "\033[34m"

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


# ── Tree parsing ──────────────────────────────────────────────────────────────

TREE_CHARS = set("│├─└ ")

def get_level(line: str) -> int:
    """Determine nesting depth, ignoring tree-drawing characters."""
    indent = 0
    for ch in line:
        if ch in TREE_CHARS:
            indent += 1
        elif ch == " ":
            indent += 1
        else:
            break
    return indent // 4

def clean_name(line: str) -> str:
    """Strip tree graphics, inline comments, and return the bare name."""
    stripped = line.strip()
    for ch in "│├─└ ─":
        stripped = stripped.lstrip(ch)
    # Strip inline comments (e.g. "app.py  # main backend")
    if "#" in stripped:
        stripped = stripped[:stripped.index("#")]
    return stripped.rstrip("/").strip()

def is_comment(line: str) -> bool:
    """Lines starting with # (after stripping tree chars) are comments."""
    return clean_name(line).startswith("#")

def validate_name(name: str) -> tuple[bool, str]:
    """Return (ok, reason). Reject dangerous or invalid names."""
    if not name:
        return False, "empty name"
    bad_chars = set('<>:"|?*\x00')
    if any(ch in bad_chars for ch in name):
        return False, f"contains illegal character(s): {bad_chars & set(name)}"
    # Prevent path traversal
    if ".." in Path(name).parts:
        return False, "path traversal ('..')"
    if Path(name).is_absolute():
        return False, "absolute paths are not allowed"
    return True, ""

def parse_lines(lines: list[str]) -> list[dict]:
    """
    Parse tree-formatted lines into a flat list of
    {'name', 'is_dir', 'level'} dicts.
    """
    entries = []
    for raw in lines:
        line = raw.rstrip()
        if not line or line.isspace() or is_comment(line):
            continue
        level  = get_level(line)
        name   = clean_name(line)
        if not name:
            continue
        # Strip inline comment before checking for trailing slash
        # e.g. "uploads/            # temp images" → is_dir = True
        line_no_comment = line[:line.index("#")].rstrip() if "#" in line else line
        is_dir = line_no_comment.endswith("/")
        ok, reason = validate_name(name)
        if not ok:
            warn(f"  ⚠  Skipping invalid entry {name!r}: {reason}")
            continue
        entries.append({"name": name, "is_dir": is_dir, "level": level})
    return entries


# ── Structure creation ────────────────────────────────────────────────────────

UNDO_FILE = Path(".tree_creator_undo.json")

def create_structure(
    entries:    list[dict],
    base_dir:   Path,
    dry_run:    bool  = False,
    quiet:      bool  = False,
    verbose:    bool  = False,
    log_lines:  list  = None,
) -> dict:
    """
    Walk entries and create dirs/files under base_dir.
    Returns a summary dict.
    """
    stack: list[str]  = []
    paths: list[Path] = []
    created_dirs:  list[str] = []
    created_files: list[str] = []
    skipped:       list[str] = []
    errors:        list[str] = []

    def log(msg):
        if log_lines is not None:
            log_lines.append(msg)
        if not quiet:
            print(msg)

    for entry in entries:
        level  = entry["level"]
        name   = entry["name"]
        is_dir = entry["is_dir"]

        # Trim stack to current depth
        while len(stack) > level:
            stack.pop()
            paths.pop()

        # Resolve full path
        if not paths:
            path = base_dir / name
        else:
            path = paths[-1] / name

        rel = path.relative_to(base_dir) if base_dir != Path(".") else path

        try:
            if is_dir:
                label = c("DIR  ", CYAN, BOLD) if USE_COLOR else "DIR  "
                if dry_run:
                    log(f"  {label} [dry-run] {rel}/")
                elif path.exists():
                    log(f"  {label} {c('exists', DIM)}  {rel}/")
                    skipped.append(str(rel) + "/")
                else:
                    path.mkdir(parents=True, exist_ok=True)
                    log(f"  {label} {rel}/")
                    created_dirs.append(str(rel) + "/")

                stack.append(name)
                paths.append(path)

            else:
                label = c("FILE ", GREEN, BOLD) if USE_COLOR else "FILE "
                if dry_run:
                    log(f"  {label} [dry-run] {rel}")
                elif path.exists():
                    log(f"  {label} {c('exists', DIM)}  {rel}")
                    skipped.append(str(rel))
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
                    log(f"  {label} {rel}")
                    created_files.append(str(rel))

        except PermissionError as e:
            msg = f"  {c('ERROR', RED, BOLD)} {rel}: permission denied"
            error(msg)
            if log_lines is not None:
                log_lines.append(msg)
            errors.append(str(rel))
        except OSError as e:
            msg = f"  {c('ERROR', RED, BOLD)} {rel}: {e}"
            error(msg)
            if log_lines is not None:
                log_lines.append(msg)
            errors.append(str(rel))

    return {
        "created_dirs":  created_dirs,
        "created_files": created_files,
        "skipped":       skipped,
        "errors":        errors,
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
        error("No undo record found. Run a creation first.")
        sys.exit(1)

    data     = json.loads(UNDO_FILE.read_text())
    base_dir = Path(data["base_dir"])
    ts       = data["timestamp"]
    dirs     = data["dirs"]
    files    = data["files"]

    warn(f"Undoing creation from {ts}")
    warn(f"Base dir: {base_dir}")

    # Remove files first
    for rel in reversed(files):
        p = base_dir / rel
        if p.exists():
            p.unlink()
            dim(f"  removed file  {rel}")
        else:
            dim(f"  not found     {rel}")

    # Remove dirs deepest-first
    for rel in reversed(dirs):
        p = base_dir / rel.rstrip("/")
        if p.exists():
            try:
                p.rmdir()          # only removes if empty
                dim(f"  removed dir   {rel}")
            except OSError:
                warn(f"  non-empty dir skipped: {rel}")

    UNDO_FILE.unlink()
    success("✅ Undo complete.")


# ── Input methods ─────────────────────────────────────────────────────────────

def read_stdin_interactive() -> list[str]:
    eof = "CTRL+Z then ENTER" if sys.platform == "win32" else "CTRL+D"
    info(f"Paste your tree structure below, then press {eof}:")
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
    if not p.is_file():
        error(f"Not a file: {path}")
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
            # Linux — try xclip then xsel
            try:
                text = subprocess.check_output(
                    ["xclip", "-selection", "clipboard", "-o"], text=True
                )
            except FileNotFoundError:
                text = subprocess.check_output(
                    ["xsel", "--clipboard", "--output"], text=True
                )
    except Exception as e:
        error(f"Clipboard read failed: {e}")
        sys.exit(1)
    return text.splitlines(keepends=True)


# ── Summary printer ───────────────────────────────────────────────────────────

def print_summary(summary: dict, dry_run: bool, log_lines: list = None):
    d = len(summary["created_dirs"])
    f = len(summary["created_files"])
    s = len(summary["skipped"])
    e = len(summary["errors"])

    sep = c("─" * 50, DIM)
    print(sep)

    if dry_run:
        info(f"  DRY-RUN preview — nothing was written to disk")
        info(f"  Would create: {d} dir(s), {f} file(s)")
    else:
        success(f"  ✅  Created : {d} dir(s), {f} file(s)")
        if s:
            warn(f"  ⚠   Skipped : {s} (already existed)")
        if e:
            error(f"  ✖   Errors  : {e}")

    print(sep)

    if log_lines is not None:
        for line in log_lines:
            pass  # already logged during creation


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Create a directory/file tree from a text structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("-f", "--file",      metavar="PATH",
                     help="Read structure from a text file")
    src.add_argument("-c", "--clipboard", action="store_true",
                     help="Read structure from the clipboard")

    p.add_argument("-o", "--output-dir",  metavar="DIR", default=".",
                   help="Base directory to create structure in (default: cwd)")
    p.add_argument("--dry-run",           action="store_true",
                   help="Preview what would be created without touching the filesystem")
    p.add_argument("--undo",              action="store_true",
                   help="Remove the last created structure (uses undo record)")
    p.add_argument("--no-color",          action="store_true",
                   help="Disable coloured output")

    verbosity = p.add_mutually_exclusive_group()
    verbosity.add_argument("-q", "--quiet",   action="store_true",
                           help="Suppress per-item output; show only summary")
    verbosity.add_argument("-v", "--verbose", action="store_true",
                           help="Show extra detail")
    p.add_argument("--log",               metavar="FILE",
                   help="Write output to a log file as well")
    return p


def main():
    parser = build_parser()
    args   = parser.parse_args()

    global USE_COLOR
    if args.no_color:
        USE_COLOR = False

    # ── Undo mode ──────────────────────────────────────────────────────────────
    if args.undo:
        do_undo()
        return

    # ── Resolve base dir ───────────────────────────────────────────────────────
    base_dir = Path(args.output_dir).resolve()
    if not base_dir.exists():
        try:
            base_dir.mkdir(parents=True)
            info(f"Created output directory: {base_dir}")
        except OSError as e:
            error(f"Cannot create output directory {base_dir}: {e}")
            sys.exit(1)
    if not base_dir.is_dir():
        error(f"Output path is not a directory: {base_dir}")
        sys.exit(1)

    # ── Read input ─────────────────────────────────────────────────────────────
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
        error("No input received. Nothing to do.")
        sys.exit(1)

    # ── Parse ──────────────────────────────────────────────────────────────────
    entries = parse_lines(lines)
    if not entries:
        error("No valid entries found after parsing.")
        sys.exit(1)

    if args.verbose and not args.quiet:
        dim(f"  Parsed {len(entries)} entries")

    # ── Header ─────────────────────────────────────────────────────────────────
    if not args.quiet:
        label = c("DRY-RUN — ", YELLOW, BOLD) if args.dry_run else ""
        print()
        info(f"  {label}Output → {base_dir}")
        print(c("─" * 50, DIM))

    # ── Log file setup ─────────────────────────────────────────────────────────
    log_lines: list | None = [] if args.log else None

    # ── Create ─────────────────────────────────────────────────────────────────
    summary = create_structure(
        entries,
        base_dir=base_dir,
        dry_run=args.dry_run,
        quiet=args.quiet,
        verbose=args.verbose,
        log_lines=log_lines,
    )

    # ── Summary ────────────────────────────────────────────────────────────────
    print_summary(summary, dry_run=args.dry_run, log_lines=log_lines)

    # ── Save undo record ───────────────────────────────────────────────────────
    if not args.dry_run and (summary["created_dirs"] or summary["created_files"]):
        save_undo(summary, base_dir)
        if args.verbose:
            dim(f"  Undo record saved to {UNDO_FILE}")

    # ── Write log file ─────────────────────────────────────────────────────────
    if args.log and log_lines is not None:
        try:
            with open(args.log, "w", encoding="utf-8") as fh:
                fh.write(f"tree_creator log — {datetime.datetime.now()}\n")
                fh.write(f"base_dir: {base_dir}\n")
                fh.write("─" * 50 + "\n")
                fh.write("\n".join(log_lines) + "\n")
            dim(f"  Log written → {args.log}")
        except OSError as e:
            warn(f"Could not write log: {e}")

    # Exit non-zero if there were errors
    if summary["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
