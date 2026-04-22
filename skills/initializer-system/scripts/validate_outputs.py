#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path.cwd()


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def load_json(path_str: str) -> dict[str, Any]:
    path = ROOT / path_str
    if not path.is_file():
        fail(f"missing file: {path_str}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid json in {path_str}: {exc}")


def require_keys(obj: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        fail(f"{label} missing keys: {', '.join(missing)}")


def static_prefix(pattern: str) -> Path:
    prefix = pattern.split("<", 1)[0].rstrip("/")
    return ROOT / prefix if prefix else ROOT


def ensure_path_exists(path_str: str, label: str) -> None:
    if not (ROOT / path_str).exists():
        fail(f"{label} does not exist: {path_str}")


def ensure_pattern_prefix(pattern: str, label: str) -> None:
    prefix = static_prefix(pattern)
    if not prefix.exists():
        fail(f"{label} static prefix does not exist: {pattern}")


def load_package_scripts(package_dir: Path) -> dict[str, Any] | None:
    package_json = package_dir / "package.json"
    if not package_json.is_file():
        return None
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    scripts = data.get("scripts")
    return scripts if isinstance(scripts, dict) else None


def validate_script_command(cwd: Path, command: str, command_id: str) -> None:
    match = re.match(r"^(npm|bun)\s+run\s+([A-Za-z0-9:_-]+)$", command.strip())
    if not match:
        return
    scripts = load_package_scripts(cwd)
    if scripts is None:
        fail(f"{command_id} declares '{command}' but {cwd.relative_to(ROOT)}/package.json is missing")
    script_name = match.group(2)
    if script_name not in scripts:
        fail(f"{command_id} declares missing package script '{script_name}' in {cwd.relative_to(ROOT)}/package.json")


def validate_profile(profile: dict[str, Any]) -> None:
    require_keys(
        profile,
        [
            "profile_version",
            "generated_at",
            "project",
            "system_target",
            "technology",
            "repository_mapping",
            "roles",
            "verification_commands",
            "initialization_outputs",
        ],
        "profile",
    )
    require_keys(profile["project"], ["name", "repository_root", "summary"], "profile.project")
    require_keys(
        profile["system_target"],
        [
            "orchestration_model",
            "canonical_group_key",
            "canonical_tool_key",
            "supports_group_tool_pipeline",
        ],
        "profile.system_target",
    )
    require_keys(profile["technology"], ["surfaces", "database", "testing"], "profile.technology")
    require_keys(
        profile["repository_mapping"],
        ["canonical_patterns", "executable_patterns", "integration_files"],
        "profile.repository_mapping",
    )
    require_keys(
        profile["initialization_outputs"],
        ["profile_path", "manifest_path", "skill_manual_path", "migration_plan_path"],
        "profile.initialization_outputs",
    )

    roles = profile["roles"]
    if not isinstance(roles, list) or not roles:
        fail("profile.roles must be a non-empty list")

    seen_roles: set[str] = set()
    has_architect = False
    for role in roles:
        require_keys(
            role,
            [
                "role_id",
                "role_kind",
                "scope",
                "skill_path",
                "builder_skill_path",
                "allowed_path_patterns",
                "forbidden_path_patterns",
                "required_inputs",
                "report_name",
            ],
            "role",
        )
        role_id = role["role_id"]
        if role_id in seen_roles:
            fail(f"duplicate role_id in profile.roles: {role_id}")
        seen_roles.add(role_id)
        if role_id == "architect":
            has_architect = True

        ensure_path_exists(role["skill_path"], f"role skill for {role_id}")
        builder_path = role["builder_skill_path"]
        if builder_path:
            ensure_path_exists(builder_path, f"builder skill for {role_id}")
        for pattern in role["allowed_path_patterns"]:
            ensure_pattern_prefix(pattern, f"allowed pattern for {role_id}")
        for pattern in role["forbidden_path_patterns"]:
            ensure_pattern_prefix(pattern, f"forbidden pattern for {role_id}")

    if not has_architect:
        fail("profile.roles must contain architect")

    repo_mapping = profile["repository_mapping"]
    for pattern in repo_mapping["canonical_patterns"].values():
        if not str(pattern).strip():
            fail("repository_mapping.canonical_patterns contains an empty value")
    for pattern in repo_mapping["executable_patterns"].values():
        ensure_pattern_prefix(pattern, "executable_patterns")
    for path_str in repo_mapping["integration_files"]:
        ensure_path_exists(path_str, "integration file")

    commands = profile["verification_commands"]
    if not isinstance(commands, list) or not commands:
        fail("profile.verification_commands must be a non-empty list")
    for item in commands:
        require_keys(item, ["command_id", "cwd", "command", "purpose"], "verification command")
        cwd = ROOT / item["cwd"]
        if not cwd.exists():
            fail(f"verification command cwd does not exist: {item['cwd']}")
        if not item["command"].strip():
            fail(f"verification command is empty: {item['command_id']}")
        validate_script_command(cwd, item["command"], item["command_id"])

    outputs = profile["initialization_outputs"]
    ensure_path_exists(outputs["profile_path"], "profile output")
    ensure_path_exists(outputs["manifest_path"], "manifest output")
    ensure_path_exists(outputs["skill_manual_path"], "skill manual output")
    ensure_path_exists(outputs["migration_plan_path"], "migration plan output")


def validate_manifest(manifest: dict[str, Any], profile: dict[str, Any]) -> None:
    require_keys(
        manifest,
        ["manifest_version", "project_profile_path", "shared_protocol_files", "skills"],
        "manifest",
    )
    if manifest["project_profile_path"] != profile["initialization_outputs"]["profile_path"]:
        fail("manifest.project_profile_path does not match profile.initialization_outputs.profile_path")

    for path_str in manifest["shared_protocol_files"]:
        ensure_path_exists(path_str, "shared protocol file")

    profile_roles = {role["role_id"] for role in profile["roles"]}
    skills = manifest["skills"]
    if not isinstance(skills, list) or not skills:
        fail("manifest.skills must be a non-empty list")

    seen_roles: set[str] = set()
    for entry in skills:
        require_keys(
            entry,
            ["skill_id", "role_id", "role_kind", "skill_path", "status", "selection_reason", "depends_on"],
            "manifest skill",
        )
        role_id = entry["role_id"]
        if role_id not in profile_roles:
            fail(f"manifest role_id not found in profile.roles: {role_id}")
        if role_id in seen_roles:
            fail(f"duplicate role_id in manifest.skills: {role_id}")
        seen_roles.add(role_id)
        ensure_path_exists(entry["skill_path"], f"manifest skill for {role_id}")
        builder_path = entry.get("builder_skill_path")
        if builder_path:
            ensure_path_exists(builder_path, f"manifest builder skill for {role_id}")
        if entry["status"] not in {"generated", "existing_project_skill", "shared_template"}:
            fail(f"invalid manifest status for {role_id}: {entry['status']}")
        if not str(entry["selection_reason"]).strip():
            fail(f"empty selection_reason for {role_id}")
        for path_str in entry["depends_on"]:
            ensure_path_exists(path_str, f"manifest dependency for {role_id}")


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python3 skills/initializer-system/scripts/validate_outputs.py "
            "<profile-json> <manifest-json>"
        )
        raise SystemExit(1)

    profile_path, manifest_path = sys.argv[1], sys.argv[2]
    profile = load_json(profile_path)
    manifest = load_json(manifest_path)
    validate_profile(profile)
    validate_manifest(manifest, profile)
    print("Initializer outputs are structurally valid.")


if __name__ == "__main__":
    main()
