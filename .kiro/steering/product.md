---
inclusion: always
---
# RepairApp Product Overview

## Purpose

RepairApp helps users decide what to do with damaged, worn, or malfunctioning items and find nearby repair resources.

The project started as a hackathon MVP. Treat it as a small production-like lab workload for learning reliable delivery patterns, not as a mission-critical system.

## Core user flow

```text
user problem
→ category and symptoms
→ safety classification
→ recommended action
→ German city or postal-code search
→ live local repair-resource lookup
→ visible data-source status
```

## Safety invariant

Safety classification is mandatory and independent from external-service availability.

A failed geocoding, Overpass, tile-service, backend, or network request must never weaken, suppress, or bypass safety guidance.

Always distinguish:

- safe diagnostics,
- safe user actions,
- actions requiring tools,
- actions requiring prior experience,
- actions requiring a specialist,
- cases where self-repair must not be recommended.

Apply additional caution to:

- mains electricity,
- lithium-ion batteries,
- gas,
- heating systems,
- medical devices,
- structural elements,
- vehicles,
- sharp objects,
- fire risks,
- water damage near electrical components,
- injury risks,
- data security,
- privacy.

Do not present assumptions as confirmed diagnoses.

## Current product goal

The browser-level Germany-wide live OSM lookup is the Phase 1 prerequisite. The next reviewed product stage is a small backend adapter after the browser-level acceptance checks pass.

The adapter should move public-service integration behind a RepairApp API while preserving bounded searches around submitted German cities or postal codes, the existing taxonomy, OSM normalization logic, visible live-data status, attribution, and safety behavior.

## Product boundaries

Do not silently replace unavailable live results with fixtures or stale data.

Fixture mode is allowed only for tests, controlled development scenarios, and clearly marked demonstrations.

The backend adapter is the next reviewed stage after the browser-level baseline. Keep it small and do not add a database unless a measured need exists.

AWS infrastructure, MCP integrations, and autonomous-agent workflows belong to later reviewed phases. They must not be added merely to enlarge the architecture.
