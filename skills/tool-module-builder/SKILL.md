---
name: tool-module-builder
description: Build or repair exactly one backend tool module from an architect task plus a design document and a test document. Use when a backend agent should ignore historical business assumptions, treat the provided docs as the source of truth, align the implementation with the repository's module architecture, and produce both module code and tests.
---

# Tool Module Builder

Use this skill when the task is to implement, repair, or complete exactly one backend tool module from:

- an architect AI task
- one design document
- one test document
- one task list

The module must be treated as a single business tool.

The architecture-level module root is:

`src/tools/<group>/<tool>/`

In this repository, the executable backend module root is:

`backend/app/modules/<group>/<tool-key>/`

You must follow the repository mapping defined by the architect task, `skills/members/后端skill.md`, and `backend/app/MODULE_ARCHITECTURE.md`.

## Source Priority

When sources conflict, use this priority order:

1. explicit architect task
2. task list
3. design document
4. test document
5. `skills/members/后端skill.md`
6. `backend/app/MODULE_ARCHITECTURE.md`
7. existing repository code, only as compatibility context

Important rule:

Existing code is not the business source of truth.

Existing code is only:

- integration context
- migration context
- compatibility context

Do not let old implementations override the architect task or the docs.

## Mindset

You are not a general backend maintainer for the whole project.

You are the owner of one tool module.

Your job is to make one module stable, complete, testable, and architecture-aligned.

You must ignore irrelevant historical context and avoid being pulled into unrelated cleanup.

## Required Inputs

Before coding, identify these three inputs:

- architect task
- design document
- test document
- task list

If one is missing, stop and report the missing input.

## What To Read First

Read in this order:

1. architect task
2. task list
3. design document
4. test document
5. `skills/members/后端skill.md`
6. `backend/app/MODULE_ARCHITECTURE.md`
7. only then inspect existing local code needed for integration

Do not begin by studying historical implementation in depth.

Start from the desired module behavior, not from the legacy code shape.

## Core Working Rules

### Rule 1: One module only

Work on exactly one tool module per task unless the architect task explicitly says otherwise.

Do not expand scope into neighboring tools.

Do not refactor unrelated modules.

Do not process task-list items outside the target module.

### Rule 2: Business truth comes from documents

Extract from the task list, design doc, and test doc:

- tool group
- tool name
- API paths
- permissions
- request and response contracts
- validation rules
- deletion rules
- uniqueness rules
- initial data requirements
- edge cases

Turn those into implementation tasks before editing code.

Task list is the execution boundary.

### Rule 3: Existing code is reviewed late and used carefully

Inspect existing code only to answer questions like:

- where the app registers routers
- how auth/session dependencies are wired
- how tests are currently organized
- how database models are registered
- what compatibility constraints must be preserved

Do not copy old business logic blindly.

If old code conflicts with the task list or docs, prefer the architect task, task list, and docs unless the architect task explicitly says to preserve old behavior.

### Rule 4: Stay architecture-aligned

The target architecture is defined by `backend/app/MODULE_ARCHITECTURE.md`.

At minimum, preserve these roles:

- interface layer
- application layer
- persistence layer
- storage model
- transport/query/output models

Possible mappings:

- `controller -> service -> dao`
- `router -> service -> repository`

The repository may use a compact local layout if the stack is Python or similarly concise, but the responsibilities must remain distinct.

### Rule 5: Tests are part of the deliverable

Do not stop at module code.

Implement or update tests for the same module so the documented behavior is verifiable.

Tests should primarily reflect the test document, not undocumented legacy behavior.

## Implementation Workflow

### Step 1: Derive the module contract

Summarize the tool from the docs:

- group id
- tool id
- endpoints
- permission model
- data model
- business rules
- error cases
- test expectations
- allowed file scope
- forbidden file scope

If needed, write this down as a temporary checklist while working.

### Step 2: Locate the module home

Use the target module path provided by the architect task and backend skill.

In this repository, default to:

`backend/app/modules/<group>/<tool-key>/`

Never introduce new business logic into a global mixed file if a module home exists or can be created safely.

### Step 3: Inspect only the integration surface

Inspect only the minimum existing code needed to integrate the module:

- app startup
- router registration
- shared auth/session dependencies
- shared config/db utilities
- nearby module examples
- current tests for similar modules

Do not let this step redefine the module contract.

Do not inspect unrelated business modules.

### Step 4: Build or repair the module

Implement or repair:

- route/handler layer
- service/application layer
- repository/persistence layer
- models and schemas
- module registration

Make the module internally coherent before touching unrelated areas.

Do not change files outside the allowed scope unless the file is a required minimal integration file and the task list authorizes it.

### Step 5: Build or repair tests

Create or update tests that cover:

- happy path behavior
- permission checks
- validation rules
- documented failure cases
- important deletion/update constraints

Prefer stable, high-signal tests over exhaustive but fragile ones.

### Step 6: Verify consistency

Before finishing, verify:

- the code matches the task list
- the code matches the design doc
- the tests reflect the test doc
- the changes stayed inside the allowed scope
- the module respects `backend/app/MODULE_ARCHITECTURE.md`
- unrelated modules were not changed without necessity

## Migration Rules

If the repository contains legacy mixed files such as:

- global routes
- global CRUD
- global business models
- global business utils

then treat them as migration context, not as the preferred destination.

If you must touch them for compatibility:

- keep the change minimal
- redirect behavior toward the target module
- avoid adding new business logic there
- remain within the task-list boundary

## Test Interpretation Rules

The test document defines expected observable behavior.

When the test document is stronger than the design doc on a concrete API example, prefer the test document for:

- concrete request examples
- concrete status code expectations
- concrete error scenarios

But do not let a weak example override an explicit architectural or business rule from the design doc.

## Ambiguity Rules

If the docs are incomplete, prefer these choices:

- preserve documented API shapes
- keep permission checks strict
- keep error responses standardized
- keep persistence logic out of the interface layer
- keep business decisions out of the repository layer
- infer the smallest stable implementation that satisfies both docs

If ambiguity has a high risk of changing real product behavior, stop and ask one concise clarifying question.

If ambiguity would require going outside the task-list scope, stop and report the boundary conflict.

## Prohibited Mistakes

Do not:

- implement multiple tools in one pass unless explicitly requested
- use legacy code as the primary business spec
- add unrelated cleanup outside the target module
- move shared infrastructure into the module without reason
- leave tests undone
- silently change API behavior beyond the docs
- let transport logic and persistence logic collapse into one file without clear reason
- exceed the task-list file boundary
- rewrite neighboring modules for consistency

## Completion Checklist

Before finishing, confirm all of the following:

- exactly one tool module was targeted
- the module behavior comes from the architect task, task list, and docs
- existing code was used only for compatibility and integration
- implementation is localized to the tool module as much as the repo allows
- routes, service logic, repository logic, and models are clearly separated
- tests for the module were added or updated
- the result is stable enough for future architect-driven iteration
- no unauthorized files were changed

## Trigger Examples

This skill should trigger for requests like:

- "根据设计文档和测试文档，实现一个新的后端工具模块"
- "修补 item-management 模块，只以设计文档和测试文档为准"
- "你现在是某个后端工具模块，只负责这个模块的代码和测试"
- "忽略旧业务上下文，根据架构师任务完成一个模块"
