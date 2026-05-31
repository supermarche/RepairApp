---
inclusion: always
---
# RepairApp Project Structure

## Workspace layout

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

## Directory responsibilities

### `AGENTS.md`

Shared repository instructions for coding agents. It contains stable working agreements, current phase boundaries, approval gates, and verification expectations.

Kiro also reads root-level `AGENTS.md`. Avoid duplicating its full content inside steering files.

### `docs/PROJECT_BRIEF.md`

Detailed reference specification for:

- product direction,
- safety behavior,
- live OSM integration,
- external dependency states,
- roadmap,
- Codex and Kiro experiments,
- approval gates.

Read it before architecture decisions or roadmap changes.

### `.kiro/steering/`

Workspace-local Kiro context.

Keep steering files focused:

- `product.md` explains the product and safety invariants,
- `structure.md` explains repository organization and change placement,
- `tech.md` explains technical constraints and verification expectations.

Do not copy the broad training steering set from external references into this workspace.

### `.kiro/specs/`

Store reviewed Kiro Feature Specs or Bugfix Specs here.

Commit useful generated spec artifacts alongside code so they preserve intent, design decisions, and task history.

### `app/`

Existing RepairApp implementation.

Inspect the actual structure before editing. Do not assume a framework, package manager, test runner, or build process until repository inspection confirms it.

## External reference repositories

The local directory `references/` contains read-only learning material.
It is intentionally excluded from version control.


```text
references/
├── ai-agents-and-mcp/
└── hands-on-aws-operations-with-chatgpt/
```

Treat these as pattern catalogs only.

Adopt a pattern only when it solves a current RepairApp problem. Do not modify reference repositories as part of RepairApp work.

## Change-placement rules

- Keep the first Germany-wide OSM change as small and reversible as possible.
- Preserve the current taxonomy and normalization flow unless a reviewed requirement changes them.
- Add new directories only when a concrete need exists.
- Add nested `AGENTS.md`, additional steering files, hooks, MCP configuration, or IaC only when their scope is justified and reviewed.
- Keep secrets out of the repository.
