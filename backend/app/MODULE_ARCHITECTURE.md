# Universal Backend Module Architecture

This document defines a language-agnostic backend architecture for tool-based systems.

Its purpose is not to force one framework or one file naming style.

It does preserve one canonical module root:

`src/tools/<group>/<tool>/`

When this architecture is applied inside a repository that has an existing backend root mapping, the repository-specific module path must be declared explicitly and treated as the executable implementation path.

Its purpose is to define stable architectural principles that can be mapped into Python, TypeScript, Java, Go, or other backend stacks.

Any AI or engineer reading this document should be able to:

- understand the intended module design immediately
- inspect an existing project and identify structural conflicts
- migrate old code into the target shape gradually
- choose a language-appropriate inner structure without violating the architecture

---

## 1. Core Goal

Each business tool must be implemented as an isolated backend module under:

`src/tools/<group>/<tool>/`

A module should contain everything needed for that tool's business behavior:

- request entry logic
- business orchestration
- persistence access
- domain models
- module-local configuration
- module-local cross-cutting logic when needed

The architecture must optimize for:

- low coupling
- clear dependency direction
- module isolation
- predictable migration
- cross-language adaptability

This document defines responsibilities and boundaries first.

The module root is fixed by product design.

The internal layout under that root is language-adaptive.

For this repository, the executable backend module path is:

`backend/app/modules/<group>/<tool-key>/`

This path is the repository-local implementation mapping of:

`src/tools/<group>/<tool>/`

All AI execution in this repository must treat `backend/app/modules/<group>/<tool-key>/` as the concrete implementation root while preserving the same architectural meaning.

---

## 2. Non-Negotiable Principles

These principles must hold in every language and framework.

### 2.1 One tool, one module

Each business tool belongs to one module boundary.

That boundary must be rooted at:

`src/tools/<group>/<tool>/`

Examples:

- item management is one module
- user administration is one module
- user management is one module

If a feature has its own routes, business rules, persistence rules, and API contract, it should usually be its own module.

`<group>` represents the product-level tool grouping.

`<tool>` represents the concrete tool within that group.

This root structure is part of the architecture because the system itself is organized around tools.

---

### 2.2 Direction of dependency is one-way

The canonical business chain is:

`interface -> application -> persistence -> infrastructure`

A more implementation-oriented view is:

`controller -> service -> dao -> database`

Allowed direction:

- controller may call service
- service may call dao
- dao may call database or ORM infrastructure

Forbidden direction:

- dao must not call service
- service must not depend on controller or HTTP request objects as business dependencies
- controller must not access database directly

This direction is more important than any folder layout.

---

### 2.3 Shared infrastructure is allowed, shared business logic is not

Allowed shared code:

- database connection/session management
- auth helpers
- logging
- config loading
- response helpers
- storage adapters
- message queue clients
- cache clients

Not allowed as shared defaults:

- shared service layer across unrelated modules
- shared dao layer containing mixed business domains
- global business rules file for multiple modules

If logic represents business meaning for one tool, it should live in that module.

---

### 2.4 Models with different responsibilities must stay distinct

The architecture distinguishes between:

- input models
- query models
- storage models
- output models

These may be implemented as separate folders, separate files, or a smaller grouped form in lightweight stacks.

But their responsibilities must remain distinct even if the files are combined.

---

### 2.5 Migration is incremental, not destructive

When an existing project does not match this architecture:

- do not rewrite everything at once
- stop expanding the old structure
- introduce new modules using the target shape
- migrate old code module by module
- delete old structure only after replacement is verified

The architecture is a direction for convergence, not an excuse for chaotic big-bang rewrites.

---

## 3. Required Conceptual Layers

Every module must support the following conceptual roles.

The exact inner folder names may vary by language.

### 3.1 Interface layer

Examples:

- controller
- router handlers
- HTTP endpoint handlers
- RPC handlers
- GraphQL resolvers

Responsibilities:

- receive requests
- parse and validate input
- call application/service layer
- format standardized responses

Must not:

- own core business decisions
- access persistence directly
- coordinate multi-step business workflows directly

Short meaning:

The interface layer handles transport in and transport out.

---

### 3.2 Application layer

Examples:

- service
- use case layer
- application service

Responsibilities:

- orchestrate business behavior
- coordinate one or more persistence operations
- manage transaction boundaries
- call external services when the business flow requires it
- transform storage results into output-facing models

Must not:

- depend on transport-specific objects as core business dependencies
- directly embed low-level SQL or storage access logic

Short meaning:

The application layer decides how the business works.

---

### 3.3 Persistence layer

Examples:

- dao
- repository
- gateway

Responsibilities:

- perform direct database access
- execute create/read/update/delete operations
- apply query conditions
- return storage-facing results

Must not:

- depend on controller
- depend on service
- make high-level business policy decisions

Short meaning:

The persistence layer decides how data is read and written.

---

### 3.4 Infrastructure layer

Examples:

- database engine
- ORM session factory
- cache adapter
- object storage adapter
- auth infrastructure
- logging infrastructure

Responsibilities:

- provide technical capabilities
- provide execution environment for persistence and integration

Must not become:

- a hidden business layer
- a dumping ground for business rules

Short meaning:

Infrastructure supports the system but does not define the business.

---

## 4. Domain Model Categories

These categories are conceptual and should exist even if a small project chooses a compact file layout.

### 4.1 DTO

Full name:

`Data Transfer Object`

Purpose:

- define input structures entering the module
- optionally define transport-facing response wrappers

Typical examples:

- create request body
- update request body
- command input payload

DTO answers:

What is being sent into or out of the interface?

---

### 4.2 Query

Purpose:

- define query conditions
- represent filtering, pagination, sorting, and search conditions

Typical examples:

- list filters
- report query conditions
- paginated search request

Query answers:

How should data be searched or filtered?

---

### 4.3 DO

Meaning:

storage-facing domain object

Purpose:

- define persisted entity shape
- represent stored data structure

Typical examples:

- ORM entity
- SQLModel model
- Prisma entity mapping
- JPA entity

Rules:

- DO is a model, not a dao
- DO must not contain high-level business orchestration

DO answers:

What does stored data look like?

---

### 4.4 VO

Full name:

`View Object`

Purpose:

- define output structures prepared for client consumption
- normalize, combine, rename, or hide internal storage fields

Typical examples:

- detail view response
- list item view
- summary record

Rules:

- VO should be produced by the application layer
- VO must not be written back to persistence as if it were a storage model

VO answers:

What should the caller see?

---

## 5. Canonical Request Flow

The intended request flow is:

1. interface layer receives request
2. interface layer parses input into DTO or Query
3. application layer executes business logic
4. persistence layer reads or writes data
5. application layer transforms results into VO or response DTO
6. interface layer returns standardized response

This flow is mandatory in meaning, but not in naming.

Example mapping:

- `controller -> service -> dao`
- `router handler -> service -> repository`
- `resolver -> use case -> repository`

If the dependency direction is preserved, the architecture is still valid.

---

## 6. How To Map This Architecture Into Real Projects

This architecture is cross-language.

That means inner-role mapping is required.

The module root is fixed:

`src/tools/<group>/<tool>/`

### 6.1 Python / FastAPI style mapping

Common mapping inside `src/tools/<group>/<tool>/`:

- interface layer -> `router.py`
- application layer -> `service.py`
- persistence layer -> `repository.py`
- DTO / Query / VO -> `schemas.py` or `schemas/`
- DO -> `models.py`
- infrastructure -> `core/`, `db/`, `shared/`, `common/`

Recommended compact module example:

```txt
src/tools/<group>/<tool>/
  router.py
  service.py
  repository.py
  schemas.py
  models.py
```

This compact structure is valid if responsibilities remain clean.

---

### 6.2 TypeScript / Node style mapping

Common mapping inside `src/tools/<group>/<tool>/`:

- interface layer -> `controller/` or route handlers
- application layer -> `service/`
- persistence layer -> `dao/` or `repository/`
- DTO / Query / VO -> `domain/` or dedicated model folders
- DO -> entity/model files
- infrastructure -> `infra/`, `db/`, `core/`, `shared/`

Example:

```txt
src/tools/<group>/<tool>/
  router/
  controller/
  service/
  dao/
  domain/
    dto/
    do/
    query/
    vo/
```

This is one valid implementation, not the only valid implementation.

---

### 6.3 Rule for all languages

Do not judge compliance only by the inner folder names.

Judge compliance by:

- whether the module is placed under the correct tool root
- whether module boundaries are clear
- whether responsibilities are separated
- whether dependencies flow one way
- whether business logic is leaving transport and persistence concerns in the correct layers

---

## 7. Structural Forms: Expanded And Compact

Two inner-structure forms are acceptable under the same canonical tool root.

### 7.1 Expanded form

Best when:

- the module is large
- many engineers collaborate on it
- the language ecosystem prefers explicit directories
- DTO, Query, VO, and DO are meaningfully distinct

Example:

```txt
src/tools/<group>/<tool>/
  conf/
  router/
  interceptor/
  controller/
  service/
  dao/
  domain/
    dto/
    do/
    query/
    vo/
```

---

### 7.2 Compact form

Best when:

- the module is still small
- the stack is Python or another concise ecosystem
- forcing too many folders would create ceremony without clarity

Example:

```txt
src/tools/<group>/<tool>/
  router.py
  service.py
  repository.py
  schemas.py
  models.py
```

---

### 7.3 Decision rule

Use the smallest structure that still preserves:

- module isolation
- clean dependencies
- model responsibility separation
- migration clarity

Do not add folders just to satisfy aesthetics.

Do not collapse layers if doing so hides architectural responsibilities.

---

## 8. How To Evaluate An Existing Project

When inspecting a real project, classify files into three groups.

### 8.1 Module-local business code

Should usually move into a specific module:

- business routes
- business services
- business repositories
- business schemas
- business entities that belong to one tool

Examples:

- item API handlers
- user administration business logic
- order reporting queries

---

### 8.2 Shared infrastructure code

Should usually remain outside modules:

- app startup
- framework bootstrapping
- DB engine/session setup
- auth middleware and auth helpers
- global config
- logging setup
- common response utilities

Examples:

- `core/config`
- `core/db`
- framework dependency injection helpers
- root application entrypoint

---

### 8.3 Historical mixed code

This is the main migration target.

Typical examples:

- global `api/routes/` mixing many business domains
- global `crud.py`
- global `models.py` containing entities from unrelated tools
- utility files containing both business rules and shared helpers

These files are usually signs of pre-module structure.

They should stop growing and be split gradually into tool modules.

---

## 8.4 Global Areas That Are Usually Allowed To Remain Global

The following areas are usually valid outside `src/tools/<group>/<tool>/` because they are infrastructure or application bootstrap, not tool business logic:

- application entrypoints
- framework bootstrapping
- global router aggregation
- database engine or session creation
- auth dependency resolution
- middleware registration
- logging setup
- environment and config loading
- storage client setup
- shared error and response formatting helpers
- test bootstrap and migration bootstrap

Typical examples:

- `main`
- `core/config`
- `core/db`
- `core/security`
- dependency injection helpers
- migration setup

Important rule:

Global code is allowed when it supports many tools without owning the business rules of one tool.

---

## 8.5 Global Areas That Should Be Treated As Migration Targets By Default

The following global areas should be treated as suspicious by default and usually migrated into `src/tools/<group>/<tool>/`:

- global route files containing concrete business endpoints
- global CRUD files containing module-specific persistence logic
- global service files containing module-specific workflows
- global models files containing entities for many unrelated tools
- global utils files containing domain validation or domain policy for one tool
- global constants files containing one tool's business meanings

These files are not always wrong forever, but they must justify their existence.

If they mainly serve one tool, they belong to that tool.

---

## 8.6 File Classification Decision Rule

When deciding whether a file belongs inside a tool module, ask these questions in order:

1. Does this file express business meaning for one specific tool?
2. Would another unrelated tool reasonably depend on it?
3. Is it transport logic, business orchestration, persistence logic, or tool-specific model definition?
4. If moved into one tool module, would clarity improve and coupling decrease?

Interpretation:

- if the file is tool-specific, move it into `src/tools/<group>/<tool>/`
- if the file is generic infrastructure, keep it global
- if the file mixes both, split it

---

## 8.7 Preferred Outcome Of Evaluation

After evaluation, the project should trend toward this state:

- tool business code lives under `src/tools/<group>/<tool>/`
- shared infrastructure stays outside tool modules
- global mixed business files stop growing
- each tool has an obvious module home
- a new contributor can tell where a new feature should be added without guessing

---

## 9. Conflict Detection Rules

An AI or engineer should flag structural conflict when any of the following appears.

### 9.1 Business code is outside its module without a good reason

Examples:

- item routes in a global routes folder
- module-specific validation in a global utilities file
- one module's repository logic living in a shared CRUD file

---

### 9.2 One file mixes multiple architectural roles

Examples:

- route handler performing SQL directly
- repository deciding permissions and business policy
- service manipulating HTTP request or response objects as core logic

---

### 9.3 One global file owns many unrelated domains

Examples:

- global models file containing entities for users, items, reports, dashboards, and permissions
- global CRUD file with unrelated business operations for many tools

This usually indicates the project is organized around technical shortcuts instead of business modules.

---

### 9.4 Shared layer becomes a hidden business layer

Examples:

- `core/` containing item lifecycle rules
- `common/` containing user permission policy
- `utils/` containing real domain decisions for one tool

Shared directories must not become business dumping grounds.

---

### 9.5 Tool root exists only in name, but business code still lives elsewhere

Examples:

- `src/tools/<group>/<tool>/` exists but routes are still created in a global routes area
- the module root exists but persistence logic remains in a global CRUD file
- the module root exists but models still accumulate in a global model registry file

This indicates incomplete migration or architectural drift.

---

### 9.6 Module grouping does not follow the product tool model

Examples:

- directories are split only by technical layer and not by tool
- one tool's code is spread across multiple unrelated top-level areas with no clear module home
- a frontend tool cannot be mapped cleanly to one backend module root

If the product is organized around tools, backend structure must reflect that.

---

## 10. Migration Rules

When adapting an old project, follow this order.

1. Identify module boundaries by business capability and map them into `src/tools/<group>/<tool>/`.
2. Freeze expansion of historical mixed structure.
3. Create a target module for one business capability under `src/tools/<group>/<tool>/`.
4. Move route logic into the module interface layer.
5. Move business logic into the module application layer.
6. Move persistence logic into the module persistence layer.
7. Split mixed models into DTO, Query, DO, and VO roles where useful.
8. Keep shared infrastructure outside the module.
9. Update application registration to point to the new module.
10. Delete old files only after replacement is verified.

Important migration rule:

If a project is already moving toward modular structure, prefer convergence over purity.

Do not force a larger folder tree if a compact module already preserves the architecture well.

---

## 10.1 Migration Priority Rules

When choosing what to migrate first, prioritize in this order:

1. business routes still outside the correct tool root
2. business services or workflows still outside the correct tool root
3. persistence code still mixed in global CRUD or repository files
4. tool-specific models trapped in global model files
5. tool-specific helpers hidden in shared utils or constants

This order usually reduces confusion fastest because it gives each tool a visible home early.

---

## 10.2 What An AI Should Preserve While Moving Code

When moving code into `src/tools/<group>/<tool>/`, an AI should preserve:

- route paths unless intentional API change is requested
- request and response contracts unless intentional change is requested
- persistence behavior unless intentional schema change is requested
- authorization behavior unless intentional change is requested
- transaction boundaries unless there is a clear bug

Architectural migration should not silently change product behavior.

---

## 10.3 What An AI Should Prefer When There Is Ambiguity

If there is ambiguity during migration, prefer these decisions:

- prefer moving tool-specific code into the tool root
- prefer keeping infrastructure global
- prefer splitting mixed files over creating new shared business abstractions
- prefer compact inner structure when the module is still small
- prefer expanded inner structure only when the module complexity justifies it

---

## 11. What Must Be Preserved During Refactoring

During any migration or rewrite, preserve these invariants:

- API behavior remains intentionally controlled
- database behavior remains intentionally controlled
- module dependencies become clearer, not more tangled
- shared infrastructure remains shared
- business logic becomes more local to the module
- old mixed structure stops expanding

Refactoring is successful when the project becomes easier to reason about, not merely more nested.

---

## 12. AI Execution Guide

If an AI is asked to restructure a backend according to this document, it should follow this process.

### Step 1

Inspect the current project and identify:

- app entrypoints
- shared infrastructure
- current business modules
- historical mixed business files
- the intended tool grouping model

### Step 2

Classify each file as one of:

- shared infrastructure
- module-local business code
- migration leftover

### Step 3

Place the business capability under the correct canonical root:

- `src/tools/<group>/<tool>/`

Then choose a language-appropriate inner mapping.

Examples:

- Python project may use compact module files inside `src/tools/<group>/<tool>/`
- TypeScript project may use expanded directories inside `src/tools/<group>/<tool>/`

### Step 4

Preserve conceptual roles even if file layout is compact.

The AI must not collapse:

- interface logic
- business orchestration
- persistence access
- storage model
- output model

into one indistinguishable blob.

### Step 5

Migrate one module at a time.

Do not expand legacy mixed files after a module target has been created.

### Step 6

Keep shared infrastructure outside modules unless it is actually business-specific.

### Step 7

After migration, verify:

- dependencies flow one way
- business code is localized
- module entry registration is correct
- old conflicting structure is reduced
- the backend module path matches the product's tool grouping model

---

## 12.1 AI Default Assumptions

Unless the project clearly proves otherwise, an AI should assume:

- the correct backend module home for business code is `src/tools/<group>/<tool>/`
- global business code is legacy unless justified
- `core`, `infra`, `shared`, and bootstrap areas are usually infrastructure
- routes, services, repositories, schemas, and entities for one tool should converge into one module root

---

## 12.2 AI Refactoring Checklist

Before declaring a migration complete, an AI should confirm:

- the tool has a clear home under `src/tools/<group>/<tool>/`
- transport logic is in the interface layer
- business workflow logic is in the application layer
- persistence logic is in the persistence layer
- tool-specific models are no longer scattered globally
- global code that remains is truly infrastructural
- the old conflicting path is no longer the default place for future code

---

## 12.3 AI Prohibited Mistakes

An AI following this document must avoid:

- keeping new business code in a global mixed directory when a tool root already exists
- moving infrastructure into a tool module without tool-specific reason
- treating folder renaming alone as successful architecture migration
- merging multiple tools into one module just because they share a table or helper
- creating shared business layers prematurely to avoid making clear module boundaries

---

## 13. Practical Judgement Rules

When deciding whether something is redundant, use these rules.

### A directory is not redundant just because it is global

Examples of usually valid global areas:

- app startup
- config
- db setup
- auth dependencies
- logging

These are infrastructure.

---

### A directory is suspicious when it globally owns business behavior for many tools

Examples:

- global routes folder with many unrelated tool endpoints
- global CRUD file with logic for many unrelated modules
- global models file containing all tool entities indefinitely

These are common migration targets.

---

### A file may remain global temporarily during migration

Temporary coexistence is acceptable when:

- new modules follow the target architecture
- old code is no longer the default direction
- migration has a clear path

Permanent architectural ambiguity is not acceptable.

---

## 14. Minimum Memory Guide

Remember the architecture with this summary:

- interface receives and returns
- application decides business behavior
- persistence reads and writes data
- infrastructure supports execution
- dto defines input transfer
- query defines search conditions
- do defines stored structure
- vo defines caller-facing output

If a project preserves these meanings, it is aligned with this architecture even when the filenames differ.
