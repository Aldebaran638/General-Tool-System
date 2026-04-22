#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATOR = SCRIPT_DIR / "validate_outputs.py"
OUTPUT_PATHS = {
    "profile_path": "ai-system/project-skill-profile.json",
    "manifest_path": "ai-system/generated-skills-manifest.json",
    "skill_manual_path": "ai-system/skill-manual.md",
    "migration_plan_path": "ai-system/migration-plan.md",
}


def write_text(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(root: Path, rel_path: str, payload: dict[str, Any]) -> None:
    write_text(root, rel_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def role(
    role_id: str,
    role_kind: str,
    scope: str,
    skill_path: str,
    builder_skill_path: str | None,
    allowed_path_patterns: list[str],
    forbidden_path_patterns: list[str],
    required_inputs: list[str],
    report_name: str,
) -> dict[str, Any]:
    return {
        "role_id": role_id,
        "role_kind": role_kind,
        "scope": scope,
        "skill_path": skill_path,
        "builder_skill_path": builder_skill_path,
        "allowed_path_patterns": allowed_path_patterns,
        "forbidden_path_patterns": forbidden_path_patterns,
        "required_inputs": required_inputs,
        "report_name": report_name,
    }


def command(command_id: str, cwd: str, shell_command: str, purpose: str) -> dict[str, str]:
    return {
        "command_id": command_id,
        "cwd": cwd,
        "command": shell_command,
        "purpose": purpose,
    }


def manifest_skill(
    skill_id: str,
    role_id: str,
    role_kind: str,
    skill_path: str,
    builder_skill_path: str | None,
    selection_reason: str,
    depends_on: list[str],
    owned_scopes: list[str],
) -> dict[str, Any]:
    return {
        "skill_id": skill_id,
        "role_id": role_id,
        "role_kind": role_kind,
        "skill_path": skill_path,
        "builder_skill_path": builder_skill_path,
        "status": "generated",
        "selection_reason": selection_reason,
        "depends_on": depends_on,
        "owned_scopes": owned_scopes,
    }


def base_profile(
    *,
    project_name: str,
    summary: str,
    surfaces: list[dict[str, str]],
    database: dict[str, str],
    testing: dict[str, list[str]],
    repository_mapping: dict[str, Any],
    roles: list[dict[str, Any]],
    verification_commands: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "profile_version": "1.0",
        "generated_at": "2026-04-22",
        "project": {
            "name": project_name,
            "repository_root": ".",
            "summary": summary,
        },
        "system_target": {
            "orchestration_model": "architect-led-multi-agent",
            "canonical_group_key": "group",
            "canonical_tool_key": "tool_key",
            "supports_group_tool_pipeline": True,
        },
        "technology": {
            "surfaces": surfaces,
            "database": database,
            "testing": testing,
        },
        "repository_mapping": repository_mapping,
        "roles": roles,
        "verification_commands": verification_commands,
        "initialization_outputs": OUTPUT_PATHS,
    }


def base_manifest(shared_protocol_files: list[str], skills: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "manifest_version": "1.0",
        "project_profile_path": OUTPUT_PATHS["profile_path"],
        "shared_protocol_files": shared_protocol_files,
        "skills": skills,
    }


def write_common_outputs(root: Path, profile: dict[str, Any], manifest: dict[str, Any]) -> None:
    write_json(root, OUTPUT_PATHS["profile_path"], profile)
    write_json(root, OUTPUT_PATHS["manifest_path"], manifest)
    write_text(root, OUTPUT_PATHS["skill_manual_path"], "# Skill Manual\n\nGenerated for external smoke testing.\n")
    write_text(root, OUTPUT_PATHS["migration_plan_path"], "# Migration Plan\n\nGenerated for external smoke testing.\n")


def create_ts_platform_kit(root: Path) -> None:
    write_text(
        root,
        "package.json",
        '{\n  "name": "ts-platform-kit",\n  "private": true,\n  "scripts": {\n    "lint": "echo lint-ok"\n  }\n}\n',
    )
    write_text(
        root,
        "apps/web/package.json",
        '{\n  "name": "web",\n  "private": true,\n  "scripts": {\n    "build": "echo build-ok",\n    "test": "echo web-test-ok"\n  }\n}\n',
    )
    write_text(
        root,
        "services/api/package.json",
        '{\n  "name": "api",\n  "private": true,\n  "scripts": {\n    "test": "echo api-test-ok"\n  }\n}\n',
    )
    write_text(root, "apps/web/src/routes/_app.tsx", "export function AppShell() { return null }\n")
    write_text(root, "apps/web/src/navigation/tool-nav.ts", "export const toolNavigation = []\n")
    write_text(root, "apps/web/src/tools/ops/invoice_console/index.tsx", "export function InvoiceConsolePage() { return null }\n")
    write_text(root, "apps/web/tests/ops/invoice_console/index.spec.ts", "export {}\n")
    write_text(root, "services/api/src/app.ts", "export const apiApp = {}\n")
    write_text(root, "services/api/src/modules/ops/invoice_console/router.ts", "export const invoiceConsoleRouter = {}\n")
    write_text(root, "services/api/tests/ops/invoice_console/index.test.ts", "export {}\n")
    write_text(root, "docs/architecture/tool-system.md", "# Tool System\n")
    write_text(root, "skills/generated/architect-skill.md", "# Architect Skill\n")
    write_text(root, "skills/generated/web-tool-worker.md", "# Web Tool Worker\n")
    write_text(root, "skills/generated/api-tool-worker.md", "# API Tool Worker\n")
    write_text(root, "skills/generated/qa-worker.md", "# QA Worker\n")
    write_text(root, "skills/generated/web-tool-builder.md", "# Web Tool Builder\n")
    write_text(root, "skills/generated/api-tool-builder.md", "# API Tool Builder\n")

    profile = base_profile(
        project_name="TS Platform Kit",
        summary="A sample TypeScript web and API monorepo initialized for an architect-led tool pipeline.",
        surfaces=[
            {"surface_id": "web_ui", "kind": "ui", "language": "TypeScript", "framework": "React Router"},
            {"surface_id": "api", "kind": "api", "language": "TypeScript", "framework": "Node HTTP"},
        ],
        database={
            "engine": "PostgreSQL",
            "access_pattern": "service-local repositories",
            "migration_mechanism": "Prisma Migrate",
        },
        testing={"primary_frameworks": ["Playwright", "Vitest"]},
        repository_mapping={
            "canonical_patterns": {
                "tool_root": "src/tools/<group>/<tool_key>/",
                "tool_test_root": "tests/<group>/<tool_key>/",
            },
            "executable_patterns": {
                "web_tool_root": "apps/web/src/tools/<group>/<tool_key>/",
                "web_test_root": "apps/web/tests/<group>/<tool_key>/",
                "api_tool_root": "services/api/src/modules/<group>/<tool_key>/",
                "api_test_root": "services/api/tests/<group>/<tool_key>/",
            },
            "integration_files": [
                "apps/web/src/routes/_app.tsx",
                "apps/web/src/navigation/tool-nav.ts",
                "services/api/src/app.ts",
                "docs/architecture/tool-system.md",
            ],
        },
        roles=[
            role(
                "architect",
                "architect",
                "project",
                "skills/generated/architect-skill.md",
                None,
                ["docs/", "skills/", "ai-system/"],
                ["apps/web/src/", "services/api/src/"],
                ["user requirement", "project profile", "generated skills manifest"],
                "architect packet",
            ),
            role(
                "web_tool_worker",
                "executor",
                "single-tool-web",
                "skills/generated/web-tool-worker.md",
                "skills/generated/web-tool-builder.md",
                ["apps/web/src/tools/", "apps/web/src/routes/", "apps/web/src/navigation/", "apps/web/tests/"],
                ["services/api/", "skills/"],
                ["architect packet", "design document", "test document", "task list"],
                "web report",
            ),
            role(
                "api_tool_worker",
                "executor",
                "single-tool-api",
                "skills/generated/api-tool-worker.md",
                "skills/generated/api-tool-builder.md",
                ["services/api/src/modules/", "services/api/src/", "services/api/tests/"],
                ["apps/web/", "skills/"],
                ["architect packet", "design document", "test document", "task list"],
                "api report",
            ),
            role(
                "qa_worker",
                "reviewer",
                "single-tool-verification",
                "skills/generated/qa-worker.md",
                None,
                ["apps/web/tests/", "services/api/tests/", "docs/", "ai-system/"],
                ["apps/web/src/", "services/api/src/", "skills/"],
                ["architect packet", "web report", "api report", "test document"],
                "qa report",
            ),
        ],
        verification_commands=[
            command("repo_lint", ".", "npm run lint", "Validate repository-wide script wiring."),
            command("web_build", "apps/web", "npm run build", "Validate the web tool build."),
            command("web_test", "apps/web", "npm run test", "Validate web tool tests."),
            command("api_test", "services/api", "npm run test", "Validate API tool tests."),
        ],
    )
    manifest = base_manifest(
        ["docs/architecture/tool-system.md"],
        [
            manifest_skill(
                "architect-main",
                "architect",
                "architect",
                "skills/generated/architect-skill.md",
                None,
                "This sample repo starts from generated architect rules rather than hand-authored project skills.",
                ["docs/architecture/tool-system.md"],
                ["task decomposition", "review"],
            ),
            manifest_skill(
                "web-worker-main",
                "web_tool_worker",
                "executor",
                "skills/generated/web-tool-worker.md",
                "skills/generated/web-tool-builder.md",
                "The web role is project-specific and was generated from the repository mapping.",
                ["docs/architecture/tool-system.md", "apps/web/src/routes/_app.tsx", "apps/web/src/navigation/tool-nav.ts"],
                ["web tool implementation"],
            ),
            manifest_skill(
                "api-worker-main",
                "api_tool_worker",
                "executor",
                "skills/generated/api-tool-worker.md",
                "skills/generated/api-tool-builder.md",
                "The API role is project-specific and was generated from the repository mapping.",
                ["docs/architecture/tool-system.md", "services/api/src/app.ts"],
                ["api tool implementation"],
            ),
            manifest_skill(
                "qa-worker-main",
                "qa_worker",
                "reviewer",
                "skills/generated/qa-worker.md",
                None,
                "The sample repo uses a generated QA role to verify one tool at a time.",
                ["docs/architecture/tool-system.md"],
                ["verification"],
            ),
        ],
    )
    write_common_outputs(root, profile, manifest)


def create_java_spring_suite(root: Path) -> None:
    write_text(root, "settings.gradle.kts", 'rootProject.name = "java-spring-suite"\n')
    write_text(root, "build.gradle.kts", "plugins {\n    java\n}\n\nrepositories {\n    mavenCentral()\n}\n")
    write_text(root, "gradlew", "#!/bin/sh\necho gradle-wrapper-placeholder\n")
    write_text(root, "server/src/main/java/com/acme/Application.java", "package com.acme;\n\npublic class Application {}\n")
    write_text(root, "server/src/main/java/com/acme/ToolModuleRegistry.java", "package com.acme;\n\npublic class ToolModuleRegistry {}\n")
    write_text(
        root,
        "server/src/main/java/com/acme/modules/finance/invoice_reconciliation/InvoiceReconciliationController.java",
        "package com.acme.modules.finance.invoice_reconciliation;\n\npublic class InvoiceReconciliationController {}\n",
    )
    write_text(root, "server/src/main/resources/application.yml", "spring:\n  application:\n    name: java-spring-suite\n")
    write_text(
        root,
        "server/src/test/java/com/acme/modules/finance/invoice_reconciliation/InvoiceReconciliationControllerTest.java",
        "package com.acme.modules.finance.invoice_reconciliation;\n\npublic class InvoiceReconciliationControllerTest {}\n",
    )
    write_text(root, "docs/architecture/domain-tools.md", "# Domain Tools\n")
    write_text(root, "skills/generated/architect-skill.md", "# Architect Skill\n")
    write_text(root, "skills/generated/backend-tool-worker.md", "# Backend Tool Worker\n")
    write_text(root, "skills/generated/test-worker.md", "# Test Worker\n")
    write_text(root, "skills/generated/spring-module-builder.md", "# Spring Module Builder\n")

    profile = base_profile(
        project_name="Java Spring Suite",
        summary="A sample Spring repository initialized for an architect-led domain tool pipeline.",
        surfaces=[{"surface_id": "spring_api", "kind": "api", "language": "Java", "framework": "Spring Boot"}],
        database={"engine": "PostgreSQL", "access_pattern": "JPA repositories", "migration_mechanism": "Flyway"},
        testing={"primary_frameworks": ["JUnit", "Spring Boot Test"]},
        repository_mapping={
            "canonical_patterns": {
                "tool_root": "src/tools/<group>/<tool_key>/",
                "tool_test_root": "tests/<group>/<tool_key>/",
            },
            "executable_patterns": {
                "backend_tool_root": "server/src/main/java/com/acme/modules/<group>/<tool_key>/",
                "backend_test_root": "server/src/test/java/com/acme/modules/<group>/<tool_key>/",
            },
            "integration_files": [
                "build.gradle.kts",
                "server/src/main/java/com/acme/ToolModuleRegistry.java",
                "docs/architecture/domain-tools.md",
            ],
        },
        roles=[
            role(
                "architect",
                "architect",
                "project",
                "skills/generated/architect-skill.md",
                None,
                ["docs/", "skills/", "ai-system/"],
                ["server/src/main/java/"],
                ["user requirement", "project profile", "generated skills manifest"],
                "architect packet",
            ),
            role(
                "backend_tool_worker",
                "executor",
                "single-tool-backend",
                "skills/generated/backend-tool-worker.md",
                "skills/generated/spring-module-builder.md",
                ["server/src/main/java/com/acme/modules/", "server/src/test/java/com/acme/modules/"],
                ["skills/", "docs/"],
                ["architect packet", "design document", "test document", "task list"],
                "backend report",
            ),
            role(
                "test_worker",
                "reviewer",
                "single-tool-verification",
                "skills/generated/test-worker.md",
                None,
                ["server/src/test/java/", "docs/", "ai-system/"],
                ["server/src/main/java/", "skills/"],
                ["architect packet", "backend report", "test document"],
                "test report",
            ),
        ],
        verification_commands=[
            command("gradle_test", ".", "./gradlew test", "Validate Spring module tests."),
            command("gradle_check", ".", "./gradlew check", "Validate the repository quality gate."),
        ],
    )
    manifest = base_manifest(
        ["docs/architecture/domain-tools.md"],
        [
            manifest_skill(
                "architect-main",
                "architect",
                "architect",
                "skills/generated/architect-skill.md",
                None,
                "The Spring sample starts from generated architect rules instead of project-authored skills.",
                ["docs/architecture/domain-tools.md"],
                ["task decomposition", "review"],
            ),
            manifest_skill(
                "backend-worker-main",
                "backend_tool_worker",
                "executor",
                "skills/generated/backend-tool-worker.md",
                "skills/generated/spring-module-builder.md",
                "The Spring sample generates a backend worker from the server module mapping.",
                ["docs/architecture/domain-tools.md", "server/src/main/java/com/acme/ToolModuleRegistry.java", "build.gradle.kts"],
                ["spring module implementation"],
            ),
            manifest_skill(
                "test-worker-main",
                "test_worker",
                "reviewer",
                "skills/generated/test-worker.md",
                None,
                "The Spring sample generates a dedicated reviewer role for backend validation.",
                ["docs/architecture/domain-tools.md"],
                ["verification"],
            ),
        ],
    )
    write_common_outputs(root, profile, manifest)


def create_mobile_ops_suite(root: Path) -> None:
    write_text(
        root,
        "package.json",
        '{\n  "name": "mobile-ops-suite",\n  "private": true,\n  "scripts": {\n    "lint": "echo mobile-lint-ok"\n  }\n}\n',
    )
    write_text(
        root,
        "mobile/app/package.json",
        '{\n  "name": "mobile-app",\n  "private": true,\n  "scripts": {\n    "test": "echo mobile-test-ok"\n  }\n}\n',
    )
    write_text(
        root,
        "api/package.json",
        '{\n  "name": "mobile-api",\n  "private": true,\n  "scripts": {\n    "test": "echo mobile-api-test-ok"\n  }\n}\n',
    )
    write_text(root, "mobile/app/src/navigation/tool-tabs.tsx", "export const toolTabs = []\n")
    write_text(root, "mobile/app/src/tools/field/service_board/Screen.tsx", "export function ServiceBoardScreen() { return null }\n")
    write_text(root, "mobile/app/tests/field/service_board/index.spec.ts", "export {}\n")
    write_text(root, "api/src/server.ts", "export const server = {}\n")
    write_text(root, "api/src/modules/field/service_board/handler.ts", "export const handler = {}\n")
    write_text(root, "api/tests/field/service_board/index.test.ts", "export {}\n")
    write_text(root, "docs/architecture/mobile-tools.md", "# Mobile Tools\n")
    write_text(root, "skills/generated/architect-skill.md", "# Architect Skill\n")
    write_text(root, "skills/generated/mobile-tool-worker.md", "# Mobile Tool Worker\n")
    write_text(root, "skills/generated/api-tool-worker.md", "# API Tool Worker\n")
    write_text(root, "skills/generated/qa-worker.md", "# QA Worker\n")
    write_text(root, "skills/generated/mobile-tool-builder.md", "# Mobile Tool Builder\n")
    write_text(root, "skills/generated/api-tool-builder.md", "# API Tool Builder\n")

    profile = base_profile(
        project_name="Mobile Ops Suite",
        summary="A sample mobile plus API workspace initialized for an architect-led tool pipeline.",
        surfaces=[
            {"surface_id": "mobile_ui", "kind": "mobile", "language": "TypeScript", "framework": "React Native"},
            {"surface_id": "api", "kind": "api", "language": "TypeScript", "framework": "Node HTTP"},
        ],
        database={
            "engine": "PostgreSQL",
            "access_pattern": "service-local repositories",
            "migration_mechanism": "Drizzle Kit",
        },
        testing={"primary_frameworks": ["Detox", "Vitest"]},
        repository_mapping={
            "canonical_patterns": {
                "tool_root": "src/tools/<group>/<tool_key>/",
                "tool_test_root": "tests/<group>/<tool_key>/",
            },
            "executable_patterns": {
                "mobile_tool_root": "mobile/app/src/tools/<group>/<tool_key>/",
                "mobile_test_root": "mobile/app/tests/<group>/<tool_key>/",
                "api_tool_root": "api/src/modules/<group>/<tool_key>/",
                "api_test_root": "api/tests/<group>/<tool_key>/",
            },
            "integration_files": [
                "mobile/app/src/navigation/tool-tabs.tsx",
                "api/src/server.ts",
                "docs/architecture/mobile-tools.md",
            ],
        },
        roles=[
            role(
                "architect",
                "architect",
                "project",
                "skills/generated/architect-skill.md",
                None,
                ["docs/", "skills/", "ai-system/"],
                ["mobile/app/src/", "api/src/"],
                ["user requirement", "project profile", "generated skills manifest"],
                "architect packet",
            ),
            role(
                "mobile_tool_worker",
                "executor",
                "single-tool-mobile",
                "skills/generated/mobile-tool-worker.md",
                "skills/generated/mobile-tool-builder.md",
                ["mobile/app/src/tools/", "mobile/app/src/navigation/", "mobile/app/tests/"],
                ["api/", "skills/"],
                ["architect packet", "design document", "test document", "task list"],
                "mobile report",
            ),
            role(
                "api_tool_worker",
                "executor",
                "single-tool-api",
                "skills/generated/api-tool-worker.md",
                "skills/generated/api-tool-builder.md",
                ["api/src/modules/", "api/src/", "api/tests/"],
                ["mobile/", "skills/"],
                ["architect packet", "design document", "test document", "task list"],
                "api report",
            ),
            role(
                "qa_worker",
                "reviewer",
                "single-tool-verification",
                "skills/generated/qa-worker.md",
                None,
                ["mobile/app/tests/", "api/tests/", "docs/", "ai-system/"],
                ["mobile/app/src/", "api/src/", "skills/"],
                ["architect packet", "mobile report", "api report", "test document"],
                "qa report",
            ),
        ],
        verification_commands=[
            command("repo_lint", ".", "npm run lint", "Validate workspace script wiring."),
            command("mobile_test", "mobile/app", "npm run test", "Validate mobile tool tests."),
            command("api_test", "api", "npm run test", "Validate API tests."),
        ],
    )
    manifest = base_manifest(
        ["docs/architecture/mobile-tools.md"],
        [
            manifest_skill(
                "architect-main",
                "architect",
                "architect",
                "skills/generated/architect-skill.md",
                None,
                "The mobile workspace starts from generated architect rules.",
                ["docs/architecture/mobile-tools.md"],
                ["task decomposition", "review"],
            ),
            manifest_skill(
                "mobile-worker-main",
                "mobile_tool_worker",
                "executor",
                "skills/generated/mobile-tool-worker.md",
                "skills/generated/mobile-tool-builder.md",
                "The mobile worker is generated from the mobile app tool mapping.",
                ["docs/architecture/mobile-tools.md", "mobile/app/src/navigation/tool-tabs.tsx"],
                ["mobile tool implementation"],
            ),
            manifest_skill(
                "api-worker-main",
                "api_tool_worker",
                "executor",
                "skills/generated/api-tool-worker.md",
                "skills/generated/api-tool-builder.md",
                "The API worker is generated from the companion API mapping.",
                ["docs/architecture/mobile-tools.md", "api/src/server.ts"],
                ["api tool implementation"],
            ),
            manifest_skill(
                "qa-worker-main",
                "qa_worker",
                "reviewer",
                "skills/generated/qa-worker.md",
                None,
                "The mobile workspace uses a generated QA role for cross-surface verification.",
                ["docs/architecture/mobile-tools.md"],
                ["verification"],
            ),
        ],
    )
    write_common_outputs(root, profile, manifest)


def create_data_pipeline_lab(root: Path) -> None:
    write_text(root, "pipelines/src/registry.py", "PIPELINE_REGISTRY = {}\n")
    write_text(root, "pipelines/src/tools/analytics/revenue_snapshot/job.py", "def run_job() -> str:\n    return 'ok'\n")
    write_text(root, "pipelines/tests/analytics/revenue_snapshot/test_job.py", "def test_job_placeholder() -> None:\n    assert True\n")
    write_text(root, "docs/architecture/data-tools.md", "# Data Tools\n")
    write_text(root, "skills/generated/architect-skill.md", "# Architect Skill\n")
    write_text(root, "skills/generated/data-pipeline-worker.md", "# Data Pipeline Worker\n")
    write_text(root, "skills/generated/data-pipeline-builder.md", "# Data Pipeline Builder\n")
    write_text(root, "skills/generated/qa-worker.md", "# QA Worker\n")

    profile = base_profile(
        project_name="Data Pipeline Lab",
        summary="A sample Python data pipeline repository initialized for an architect-led tool pipeline.",
        surfaces=[{"surface_id": "data_pipeline", "kind": "data", "language": "Python", "framework": "Dagster-style jobs"}],
        database={"engine": "BigQuery", "access_pattern": "warehouse queries and Python jobs", "migration_mechanism": "dbt"},
        testing={"primary_frameworks": ["pytest"]},
        repository_mapping={
            "canonical_patterns": {
                "tool_root": "src/tools/<group>/<tool_key>/",
                "tool_test_root": "tests/<group>/<tool_key>/",
            },
            "executable_patterns": {
                "pipeline_tool_root": "pipelines/src/tools/<group>/<tool_key>/",
                "pipeline_test_root": "pipelines/tests/<group>/<tool_key>/",
            },
            "integration_files": [
                "pipelines/src/registry.py",
                "docs/architecture/data-tools.md",
            ],
        },
        roles=[
            role(
                "architect",
                "architect",
                "project",
                "skills/generated/architect-skill.md",
                None,
                ["docs/", "skills/", "ai-system/"],
                ["pipelines/src/"],
                ["user requirement", "project profile", "generated skills manifest"],
                "architect packet",
            ),
            role(
                "data_pipeline_worker",
                "executor",
                "single-tool-data-pipeline",
                "skills/generated/data-pipeline-worker.md",
                "skills/generated/data-pipeline-builder.md",
                ["pipelines/src/tools/", "pipelines/tests/"],
                ["skills/", "docs/"],
                ["architect packet", "design document", "test document", "task list"],
                "data pipeline report",
            ),
            role(
                "qa_worker",
                "reviewer",
                "single-tool-verification",
                "skills/generated/qa-worker.md",
                None,
                ["pipelines/tests/", "docs/", "ai-system/"],
                ["pipelines/src/", "skills/"],
                ["architect packet", "data pipeline report", "test document"],
                "qa report",
            ),
        ],
        verification_commands=[
            command(
                "pipeline_pytest",
                ".",
                "python -m pytest pipelines/tests/analytics/revenue_snapshot/test_job.py -q",
                "Validate pipeline tool tests.",
            ),
            command(
                "initializer_validation",
                ".",
                "python3 skills/initializer-system/scripts/validate_outputs.py ai-system/project-skill-profile.json ai-system/generated-skills-manifest.json",
                "Validate initializer outputs.",
            ),
        ],
    )
    manifest = base_manifest(
        ["docs/architecture/data-tools.md"],
        [
            manifest_skill(
                "architect-main",
                "architect",
                "architect",
                "skills/generated/architect-skill.md",
                None,
                "The data pipeline sample starts from generated architect rules.",
                ["docs/architecture/data-tools.md"],
                ["task decomposition", "review"],
            ),
            manifest_skill(
                "pipeline-worker-main",
                "data_pipeline_worker",
                "executor",
                "skills/generated/data-pipeline-worker.md",
                "skills/generated/data-pipeline-builder.md",
                "The data pipeline worker is generated from the pipeline tool mapping.",
                ["docs/architecture/data-tools.md", "pipelines/src/registry.py"],
                ["pipeline tool implementation"],
            ),
            manifest_skill(
                "qa-worker-main",
                "qa_worker",
                "reviewer",
                "skills/generated/qa-worker.md",
                None,
                "The data pipeline sample uses a generated QA role for verification.",
                ["docs/architecture/data-tools.md"],
                ["verification"],
            ),
        ],
    )
    write_common_outputs(root, profile, manifest)


FIXTURE_BUILDERS = {
    "ts-platform-kit": create_ts_platform_kit,
    "java-spring-suite": create_java_spring_suite,
    "mobile-ops-suite": create_mobile_ops_suite,
    "data-pipeline-lab": create_data_pipeline_lab,
}


def load_profile_name(root: Path) -> tuple[str, list[str]]:
    profile_path = root / OUTPUT_PATHS["profile_path"]
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    roles = [role_data["role_id"] for role_data in data.get("roles", [])]
    return data["project"]["name"], roles


def run_fixture(root: Path) -> None:
    profile = OUTPUT_PATHS["profile_path"]
    manifest = OUTPUT_PATHS["manifest_path"]
    project_name, roles = load_profile_name(root)
    print(f"[fixture] {root.name} :: {project_name}")
    print(f"  workspace: {root}")
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


def build_fixtures(base_dir: Path) -> list[Path]:
    roots: list[Path] = []
    for fixture_name, builder in FIXTURE_BUILDERS.items():
        root = base_dir / fixture_name
        root.mkdir(parents=True, exist_ok=True)
        builder(root)
        roots.append(root)
    return roots


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="initializer-smoke-", dir="/tmp") as temp_dir:
        base_dir = Path(temp_dir)
        roots = build_fixtures(base_dir)
        print("Running initializer smoke tests on external temp repositories...")
        for root in roots:
            run_fixture(root)
        print(f"Smoke tests passed: {len(roots)} fixture(s)")
        print(f"External fixture root: {base_dir}")


if __name__ == "__main__":
    main()
