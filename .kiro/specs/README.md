# Kiro Specs

This directory stores reviewed Kiro specification artifacts.

Kiro Specs are appropriate for work that benefits from structured requirements, design review, and trackable implementation tasks. Commit useful generated specs alongside code so they preserve intent and implementation history.

## First recommended spec

After the Phase 0 repository inspection has been reviewed, create a **Feature Spec** named:

```text
live-osm-germany-baseline
```

Use the **Requirements-First** workflow for the first experiment.

Do not use Quick Plan for this first spec. The live OSM change crosses safety, external-service, UI-state, and verification boundaries, so review each phase before implementation.

Suggested prompt:

```text
Create a Requirements-First Feature Spec for replacing the current
Görlitz-only live OpenStreetMap lookup with Germany-wide location search.

Preserve the existing RepairApp taxonomy, OSM normalization logic, and
safety behavior.

The feature must accept an explicit German city or postal-code submission,
validate that the resolved location is in Germany, calculate a bounded
search area, issue bounded Overpass requests only, expose visible OSM
attribution and live-data state, and distinguish loading, success,
no-results, invalid-location, timeout, HTTP 429, malformed-response,
configuration-error, and upstream-failure states.

Do not add AWS infrastructure, Terraform, IAM changes, a database, MCP
servers, or autonomous workflows as part of this spec.

Before generating implementation tasks, account for the Phase 0 repository
inspection and identify the smallest reversible change.
```

## Expected generated artifacts

A Feature Spec should generate:

```text
.kiro/specs/live-osm-germany-baseline/
├── requirements.md
├── design.md
└── tasks.md
```

Review and approve:

1. requirements,
2. design,
3. tasks,

before starting implementation.

Do not create placeholder `requirements.md`, `design.md`, or `tasks.md` files manually before Kiro generates and you review them.
