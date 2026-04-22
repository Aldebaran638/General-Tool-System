#!/usr/bin/env python3
"""
Template Residue Scanner

Scans the repository for known template brand residues.
Fails CI if any forbidden strings are found in tracked files.

Usage:
    python scripts/check-template-residue.py

Exit codes:
    0 - No residues found
    1 - Residues found (CI should fail)
"""

import os
import subprocess
import sys
from pathlib import Path

# Forbidden template residues (case-insensitive matching)
FORBIDDEN_RESIDUES = [
    "Generic Demo Template",
    "FastAPI Cloud",
    "Invoice Management System",
    "generic-demo-template",
    "fastapi-full-stack-template",
    "security@tiangolo.com",
    "@tiangolo",
]

# Files and directories to skip (upstream credits, lock files, etc.)
SKIP_PATHS = [
    ".git",
    ".copier",           # Upstream credit preserved
    ".github/ISSUE_TEMPLATE",  # GitHub templates, maintained separately
    "node_modules",
    "package-lock.json",  # Auto-generated, contains old package name
    "bun.lock",           # Auto-generated lock file
    "uv.lock",            # Auto-generated lock file
    ".pytest_cache",
    "__pycache__",
    "htmlcov",
    "release-notes.md",   # Historical release notes, preserved
    "check-template-residue.py",  # Skip self
]

# File extensions to skip (binary, generated)
SKIP_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz",
    ".woff", ".woff2", ".ttf", ".eot",
    ".lock",
)


def should_skip(path: Path, repo_root: Path) -> bool:
    """Check if a path should be skipped."""
    rel_path = path.relative_to(repo_root)
    
    # Check skip directories
    for part in rel_path.parts:
        if part in SKIP_PATHS:
            return True
    
    # Check skip file names
    if path.name in SKIP_PATHS:
        return True
    
    # Check extensions
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    
    return False


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Scan a single file for forbidden residues.
    
    Returns list of (line_number, line_content, matched_residue)
    """
    matches = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                for residue in FORBIDDEN_RESIDUES:
                    if residue.lower() in line.lower():
                        # Skip lines that are upstream credits
                        if "upstream" in line.lower() or "originally generated" in line.lower():
                            continue
                        matches.append((line_num, line.rstrip("\n"), residue))
                        break  # Only report first match per line
    except UnicodeDecodeError:
        # Binary file, skip
        pass
    except Exception as e:
        print(f"Warning: Could not read {path}: {e}")
    
    return matches


def main() -> int:
    repo_root = Path(__file__).parent.parent.resolve()
    
    # Get list of tracked files from git
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_files = [repo_root / f for f in result.stdout.strip().split("\n") if f]
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or git command failed")
        return 1
    
    total_violations = 0
    
    for file_path in tracked_files:
        if not file_path.exists():
            continue
        
        if should_skip(file_path, repo_root):
            continue
        
        matches = scan_file(file_path)
        if matches:
            rel_path = file_path.relative_to(repo_root)
            print(f"\n[FAIL] {rel_path}")
            for line_num, line, residue in matches:
                print(f"   Line {line_num}: Found '{residue}'")
                # Show context (truncated if too long)
                context = line.strip()
                if len(context) > 100:
                    context = context[:97] + "..."
                print(f"   -> {context}")
            total_violations += len(matches)
    
    if total_violations > 0:
        print(f"\n{'='*60}")
        print(f"FAIL: Found {total_violations} template residue(s)")
        print(f"{'='*60}")
        print("\nTo fix:")
        print("1. Replace forbidden strings with your product branding")
        print("2. If a match is a false positive, add it to SKIP_PATHS")
        print("3. If upstream credit is intentional, ensure it's in .copier/")
        return 1
    else:
        print("[PASS] No template residues found. Repository branding is clean.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
