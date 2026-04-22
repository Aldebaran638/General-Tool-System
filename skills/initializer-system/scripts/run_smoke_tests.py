#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
FIXTURES_DIR = SKILL_ROOT / "fixtures"
VALIDATOR = SCRIPT_DIR / "validate_outputs.py"


def fixture_roots() -> list[Path]:
    return sorted(path for path in FIXTURES_DIR.iterdir() if path.is_dir())


def load_profile_name(root: Path) -> tuple[str, list[str]]:
    profile_path = root / "ai-system" / "project-skill-profile.json"
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    roles = [role["role_id"] for role in data.get("roles", [])]
    return data["project"]["name"], roles


def run_fixture(root: Path) -> None:
    profile = "ai-system/project-skill-profile.json"
    manifest = "ai-system/generated-skills-manifest.json"
    project_name, roles = load_profile_name(root)
    print(f"[fixture] {root.name} :: {project_name}")
    print(f"  roles: {', '.join(roles)}")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), profile, manifest],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.stdout.strip():
        print(f"  stdout: {result.stdout.strip()}")
    if result.returncode != 0:
        if result.stderr.strip():
            print(f"  stderr: {result.stderr.strip()}")
        raise SystemExit(f"Smoke test failed for fixture: {root.name}")


def main() -> None:
    roots = fixture_roots()
    if not roots:
        raise SystemExit("No fixtures found.")

    print("Running initializer smoke tests...")
    for root in roots:
        run_fixture(root)
    print(f"Smoke tests passed: {len(roots)} fixture(s)")


if __name__ == "__main__":
    main()
