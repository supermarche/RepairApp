# RepairApp Agent Instructions

## Read first

Read `docs/PROJECT_BRIEF.md` before architecture decisions, roadmap changes, OSM integration work, AWS work, or agent experiments.

Treat repositories under `references/` as read-only pattern catalogs. Do not copy their code, prompts, steering rules, or configurations mechanically.

## Repository layout

```text
RepairApp/
├── AGENTS.md
├── docs/
│   └── PROJECT_BRIEF.md
├── .kiro/
│   ├── steering/
│   │   ├── product.md
│   │   ├── structure.md
│   │   └── tech.md
│   └── specs/
└── app/
```

The current application code lives under `app/`. Inspect the actual files before assuming a framework, package manager, test command, or build command.

## Current delivery phase

The browser-level Germany-wide live OSM baseline is the Phase 1 prerequisite.

The next reviewed implementation stage is Phase 2 — a small backend adapter. Start it only after the browser-level live path has passed the Phase 1 acceptance checks.

For Phase 2:

1. inspect the current browser-to-provider request flow,
2. identify the smallest useful RepairApp API boundary,
3. route browser location-search requests through the RepairApp API,
4. centralize validation, cache lookup, timeout handling, rate limiting, provider configuration, and consistent error mapping,
5. add structured integration logs, dependency-level measurements, and readiness behavior,
6. preserve the current taxonomy, OSM normalization logic, visible live-data states, attribution, and safety behavior.

AWS infrastructure remains outside the current scope.

Do not add AWS resources, Terraform, IAM changes, deployment configuration, paid services, or a database solely to enlarge the architecture.

## Stable product constraints

Safety classification is mandatory and independent from external-service availability.

A failed request must never weaken, suppress, or bypass safety guidance.

Apply extra caution to mains electricity, lithium-ion batteries, gas, heating systems, medical devices, structural elements, vehicles, injury risks, and privacy.

Do not present assumptions as confirmed diagnoses.

Live OpenStreetMap-derived data is the primary source of local repair-resource results.

Germany-wide support means bounded searches for user-selected German cities or postal codes. It does not mean a Germany-wide Overpass query, bulk download, or preloaded country-wide dataset.

Preserve the existing RepairApp taxonomy and OSM normalization unless a reviewed requirement explicitly changes them.

## OSM integration constraints

For Phase 1:

- accept an explicit city or postal-code submission,
- resolve the requested location,
- validate that it is in Germany,
- calculate a bounded search area,
- query relevant OSM objects only inside that bounded area,
- deduplicate normalized results,
- show visible OpenStreetMap attribution and live-data status,
- keep external endpoints configurable,
- provide a manual retry path,
- distinguish loading, success, no results, invalid location, timeout, HTTP 429, malformed response, configuration error, and upstream failure,
- use fixtures only for tests or clearly marked development scenarios,
- never present fixture or stale data as live,
- do not implement public-geocoding autocomplete,
- do not send requests after every keystroke,
- do not execute unnecessary parallel Overpass requests,
- do not preload Germany-wide data.

## Working method

Before editing:

1. inspect repository structure and `git status`,
2. read `README.md`, this file, and relevant docs,
3. identify the current roadmap phase,
4. summarize the current state,
5. propose the smallest useful reversible change,
6. list files to modify,
7. define verification steps,
8. state risks and non-goals,
9. stop before editing unless implementation was explicitly requested.

After editing, report:

1. files changed,
2. behavior changed,
3. commands run,
4. verification results,
5. unresolved risks,
6. rollback method,
7. next smallest step.

Avoid unrelated refactors.

## Verification baseline

Before Phase 2 implementation, rerun the Germany-wide browser-level baseline checks as a regression gate:

- Görlitz,
- Dresden,
- Berlin,
- a valid German postal code,
- an invalid location,
- a location outside Germany,
- no matching resources,
- timeout simulation,
- HTTP 429 simulation,
- malformed-response simulation,
- missing-configuration simulation.

Add automated checks where they provide immediate value, especially for taxonomy normalization, dependency-state mapping, cache behavior, and adapter error mapping.

If canonical run, test, lint, or build commands are not documented yet, inspect the repository and report that gap. Do not invent commands.

## Kiro experiment boundary

Kiro is part of the project learning plan and should be evaluated early on a small, reversible task in parallel with the live OSM baseline.

Use workspace-local Kiro artifacts:

- `.kiro/steering/`
- `.kiro/specs/`
- `.kiro/hooks/` only after a reviewed use case exists

Do not copy all steering rules from `../references/ai-agents-and-mcp/`. Start with the three focused workspace steering files already included in this repository.

For the first Kiro experiment:

1. inspect the repository,
2. compare `.kiro/steering/` with this file and `docs/PROJECT_BRIEF.md`,
3. create one reviewed Feature Spec,
4. review requirements, design, and tasks before implementation.

Do not enable global steering rules, MCP servers, AWS credentials, write-capable external tools, autonomous pull requests, or large refactors during the first Kiro experiment.

## Tool-selection rule

Choose the least complex suitable approach:

```text
manual change
→ script
→ CI check
→ Codex task
→ Kiro Spec
→ MCP-assisted workflow
→ specialized agent
→ long-running autonomous agent
```

Use more autonomy only when it provides measurable value.

## Approval gates

Do not perform these actions without explicit approval:

- `git push`,
- merge,
- rebase,
- force push,
- deleting files without justification,
- destructive operations,
- `terraform apply`,
- `terraform destroy`,
- provisioning paid AWS resources,
- changing IAM,
- exposing a public endpoint,
- adding secrets,
- penetration testing,
- enabling write-capable MCP tools,
- sending data to a new external service,
- connecting an autonomous agent to a repository,
- creating pull requests automatically.

Never store secrets in the repository. Use environment variables, `.env.example`, and appropriate secret storage.

## Immediate task

Inspect the browser-level Germany-wide live OSM baseline and report the smallest reversible plan for adding the Phase 2 small backend adapter.

Preserve the current taxonomy, OSM normalization logic, visible live-data states, attribution, and safety behavior. Keep AWS infrastructure outside this task.

Stop before editing unless implementation is explicitly requested.
