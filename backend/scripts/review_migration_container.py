from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from loguru import logger


def run_command(
    args: list[str],
    cwd: Path,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    logger.debug("Running command: {}", " ".join(args))
    result = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=capture_output,
        check=False,
    )
    if result.stdout:
        logger.debug("stdout:\n{}", result.stdout.rstrip())
    if result.stderr:
        logger.debug("stderr:\n{}", result.stderr.rstrip())
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Command failed")
    return result


def extract_revision_id(text: str) -> str | None:
    for token in text.replace("(", " ").replace(")", " ").split():
        if len(token) >= 8 and all(ch in "0123456789abcdef" for ch in token.lower()):
            return token
    return None


def find_revision_file(version_files: list[Path], revision_id: str) -> Path | None:
    for path in version_files:
        if path.name.startswith(f"{revision_id}_"):
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("message", help="Short migration description")
    args = parser.parse_args()

    # Use container paths
    backend_dir = Path("/app")
    versions_dir = backend_dir / "app" / "alembic" / "versions"

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    if not backend_dir.exists():
        raise RuntimeError(f"Backend directory not found: {backend_dir}")
    if not versions_dir.exists():
        raise RuntimeError(f"Alembic versions directory not found: {versions_dir}")

    version_files = sorted(versions_dir.glob("*.py"))

    # Use container's alembic directly
    current_result = run_command(
        ["alembic", "current"],
        cwd=backend_dir,
    )
    current_revision = extract_revision_id(f"{current_result.stdout}\n{current_result.stderr}")
    if current_revision:
        if find_revision_file(version_files, current_revision) is None:
            raise RuntimeError(
                "Current database revision is missing from backend/app/alembic/versions. "
                "Restore the missing migration file or rebuild the local database first."
            )

    heads_result = run_command(
        ["alembic", "heads"],
        cwd=backend_dir,
    )
    head_revision = extract_revision_id(f"{heads_result.stdout}\n{heads_result.stderr}")
    if current_revision and head_revision and current_revision != head_revision:
        raise RuntimeError(
            "The database is not at the latest revision. "
            "Run 'alembic upgrade head' first, then retry."
        )

    before = {path.name for path in versions_dir.glob("*.py")}

    logger.info("Generating migration...")
    try:
        run_command(
            ["alembic", "revision", "--autogenerate", "-m", args.message],
            cwd=backend_dir,
        )
    except Exception as exc:
        raise RuntimeError(
            "Migration generation failed. Common cause: the database is not up to date. "
            "Run 'alembic upgrade head' first, then retry."
        ) from exc

    after_paths = sorted(versions_dir.glob("*.py"))
    new_files = [path for path in after_paths if path.name not in before]
    if len(new_files) != 1:
        raise RuntimeError(f"Expected exactly one new migration file, found: {len(new_files)}")

    migration_file = new_files[0]

    try:
        logger.info("New migration file: {}", migration_file)
        print("\n----- BEGIN MIGRATION -----")
        print(migration_file.read_text(encoding="utf-8"))
        print("----- END MIGRATION -----\n")
        print("Check:")
        print("- correct table")
        print("- correct columns")
        print("- no extra operations")
        print("- sensible downgrade")
        print("")

        while True:
            answer = input("Apply this migration now? (Y/N): ").strip().lower()
            if answer == "y":
                logger.info("Applying migration...")
                run_command(
                    ["alembic", "upgrade", "head"],
                    cwd=backend_dir,
                )
                logger.info("Migration applied successfully.")
                return 0
            if answer == "n":
                print("")
                print("Edit the migration file, then rerun this script when ready:")
                print(migration_file)
                print("")
                return 0
            print("Please enter Y or N.")
    except Exception:
        if migration_file.exists():
            migration_file.unlink()
            logger.warning("Deleted generated migration file after failure: {}", migration_file)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
