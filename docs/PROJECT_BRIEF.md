# RepairApp — Live OSM Workload and AWS Frontier Agents Lab

## 1. Purpose

RepairApp is a small, real workload developed progressively.

It supports repair culture by helping users decide what to do with damaged, worn, or malfunctioning items. The application should help a user:

1. identify the item category,
2. describe symptoms or the current condition,
3. detect safety risks,
4. compare available actions,
5. choose an appropriate next step,
6. find nearby repair resources,
7. reduce the risk of a similar problem in the future.

Possible actions include:

- safe diagnostics,
- maintenance,
- cleaning,
- replacement of consumables,
- self-repair,
- professional repair,
- temporary workarounds,
- spare-parts sourcing,
- reuse,
- recycling,
- safe disposal,
- warranty claims,
- seller-liability options.

The project started as a hackathon MVP. It is evolving from a local demonstration into a small production-like lab workload with:

- a real external dependency,
- network failures,
- explicit degraded states,
- measurable operational behavior,
- progressive DevSecOps practices,
- observability,
- controlled AWS experiments,
- selective MCP usage,
- agent-assisted operational exercises.

Do not describe RepairApp as truly mission-critical. Treat it as a learning workload for production patterns.

The application must remain understandable, demonstrable, reversible, and small enough to develop incrementally.

---

## 2. Core product flow

The target user flow is:

```text
user problem
→ category and symptoms
→ safety classification
→ recommended action
→ German location search
→ live local repair-resource lookup
→ visible data-source and dependency status
```

The primary user path should retrieve live OpenStreetMap-derived repair-resource data for a user-selected German location.

RepairApp must not silently replace unavailable live results with sample data.

---

## 3. Safety baseline

Safety classification is mandatory.

It must remain independent from geocoding, Overpass, tile-service, backend, or network availability.

A failed external request must never weaken, suppress, or bypass safety guidance.

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

When information is incomplete, describe the result as a preliminary classification or recommendation.

---

## 4. Live OpenStreetMap-derived data baseline

Live OpenStreetMap-derived data is the primary source of local repair-resource results. It is not optional enrichment.

Public Nominatim-compatible geocoding services, Overpass-compatible endpoints, and map-tile services are replaceable external dependencies. They are not guaranteed production services.

Keep endpoints configurable and make degraded behavior explicit.

### 4.1 Germany-wide scope

Germany-wide support means location-based searches across Germany.

It does not mean:

- a Germany-wide Overpass query,
- a bulk download,
- preloading all German repair resources,
- scraping map tiles,
- bulk geocoding,
- background crawling.

Users search by German city or postal code.

Each submitted location search should lead to a bounded request flow:

```text
explicit user submission
→ geocode requested location
→ validate country
→ derive bounded search area
→ execute bounded Overpass query
→ normalize matching OSM objects
→ deduplicate results
→ display live-data state and attribution
```

### 4.2 Required functional behavior

The application must:

1. accept an explicit city or postal-code submission,
2. resolve the requested location,
3. validate that the result is in Germany,
4. calculate a bounded search area,
5. query relevant OSM objects only inside that area,
6. preserve the existing RepairApp taxonomy,
7. preserve and extend the existing OSM normalization logic carefully,
8. deduplicate results,
9. display visible OpenStreetMap attribution,
10. expose the current live-data state,
11. handle failures without pretending that fixtures or stale data are live,
12. provide a manual retry path where appropriate.

### 4.3 Required implementation outcome

Remove the hardcoded Görlitz bounding box as the default.

Support:

- Görlitz,
- Dresden,
- Berlin,
- other German cities,
- valid German postal codes,

without city-specific code changes.

Use bounded Overpass queries only.

Keep external-service endpoints configurable.

### 4.4 Explicit non-goals

Do not:

- preload Germany-wide data,
- perform a country-wide Overpass query,
- bulk geocode,
- add public-geocoding autocomplete,
- send geocoding requests after every keystroke,
- execute unnecessary parallel Overpass queries,
- scrape or prefetch tiles,
- bypass provider cache headers,
- hide failures behind sample results,
- add AWS infrastructure during the browser-only baseline,
- introduce a database without a measured need.

Fixtures are allowed only for:

- automated tests,
- controlled development scenarios,
- failure simulation,
- clearly marked demo mode.

Fixture mode must never be presented as live mode.

Map-tile configuration is required only if the current application displays a map. Do not add map rendering merely to satisfy this specification.

---

## 5. External dependency contract

Treat the following as separate dependencies:

1. geocoding provider,
2. Overpass provider,
3. map-tile provider, when a map is displayed,
4. RepairApp backend adapter, after it is introduced.

Track them separately because they can fail independently.

### 5.1 Minimum dependency states

Use explicit dependency states:

```text
idle
loading
live_success
no_results
invalid_location
timeout
rate_limited
upstream_error
malformed_response
configuration_error
development_fixture
```

Do not collapse all failures into a generic `no_results` message.

### 5.2 UI distinctions

The UI should clearly distinguish:

- live results loaded successfully,
- no matching live resources found,
- requested location is invalid,
- requested location is outside Germany,
- live lookup is unavailable,
- a timeout occurred,
- the provider rejected the request due to rate limiting,
- malformed provider data was received,
- configuration is missing or invalid,
- development fixture mode is active,
- manual retry is available.

### 5.3 Operational event fields

Where relevant, record:

- dependency name,
- provider name,
- request timestamp,
- elapsed time,
- HTTP response status,
- normalized result count,
- error class,
- retry decision,
- fixture-mode status.

Avoid logging:

- full user problem descriptions,
- unnecessary raw geocoding input,
- personal data,
- precise location details beyond what is operationally necessary.

Prefer normalized operational fields such as:

- submitted city,
- postal-code prefix where appropriate,
- dependency,
- status class,
- elapsed time,
- result count.

---

## 6. OpenStreetMap service-policy guardrails

When public OSM ecosystem services are used, comply with current provider policies.

Provider policies can change. Verify them again before implementation, deployment, and public demonstration.

At minimum:

- use explicit user-triggered location searches,
- respect public Nominatim usage limits,
- do not implement client-side autocomplete against public Nominatim,
- do not send a request after every keystroke,
- identify the application appropriately through supported request headers or browser referer behavior,
- show visible attribution,
- cache repeated geocoding results after introducing a backend adapter,
- keep endpoints replaceable,
- use bounded Overpass requests,
- avoid bulk queries,
- avoid unnecessary parallel requests,
- use conservative timeouts,
- use conservative result limits,
- do not prefetch or scrape map tiles,
- respect cache headers,
- document that public endpoints may throttle, block, withdraw access, or change policy.

For the browser-only phase, use explicit submitted requests and clearly document limitations.

Before describing RepairApp as operationally controlled beyond a demo, introduce a backend adapter or equivalent controlled integration layer.

---

## 7. Browser-only baseline

The first implementation phase may call public services from the browser.

This is a temporary demonstrator baseline, not the target production integration model.

The browser-only baseline should:

- perform explicit user-triggered geocoding requests,
- derive a bounded search area,
- execute one conservative Overpass request where possible,
- expose loading and degraded states,
- measure request latency in the browser,
- display attribution,
- provide retry behavior,
- keep provider endpoints configurable.

Document browser-only limitations:

- limited control over request headers,
- limited caching,
- no centralized rate limiting,
- limited observability,
- dependency on public endpoint availability,
- limited protection against excessive repeated requests,
- no stable readiness model.

---

## 8. Backend-adapter baseline

After the browser-level live path works, introduce a small backend adapter.

Target flow:

```text
browser
→ RepairApp API
→ input validation
→ Germany validation
→ cache lookup
→ timeout handling
→ rate limiting
→ geocoding provider
→ bounded Overpass provider
→ normalization
→ response
```

The backend adapter should provide:

- centralized configuration,
- conservative timeouts,
- controlled retries,
- cache support,
- rate limiting,
- structured logs,
- dependency-level metrics,
- consistent error mapping,
- readiness behavior,
- fixture injection for controlled tests.

Keep the adapter small.

Do not add a database unless a measured need exists.

---

## 9. Operational measurements

Expose enough behavior to support real diagnostics.

### 9.1 Browser-only measurements

Measure or display where practical:

- location-search attempts,
- geocoding success count,
- geocoding failure count,
- Overpass success count,
- Overpass failure count,
- request latency,
- timeout events,
- HTTP 429 responses,
- malformed-response events,
- normalized result counts,
- visible dependency status.

### 9.2 Backend-adapter measurements

After introducing the backend adapter, measure:

- API request count,
- geocoding latency,
- Overpass latency,
- response status by dependency,
- timeout count,
- rate-limit count,
- malformed-response count,
- configuration-error count,
- cache hit ratio,
- degraded-mode count,
- readiness state,
- structured integration-error logs.

### 9.3 Initial service indicators

Define a small number of indicators:

- percentage of submitted location searches resolved successfully,
- percentage of resolved locations receiving a completed Overpass response,
- dependency latency distribution,
- percentage of requests ending in degraded mode,
- cache hit ratio after caching is introduced.

Do not invent aggressive SLO values before collecting baseline measurements.

---

## 10. Learning objective

Use RepairApp to learn when traditional tools are sufficient and when agents provide measurable value.

Evaluate progressively:

- manual changes,
- small scripts,
- CI checks,
- Codex,
- Kiro IDE or CLI,
- Kiro steering files,
- Kiro Specs,
- Kiro hooks,
- MCP servers,
- Infrastructure as Code,
- observability,
- controlled incidents,
- AWS Security Agent,
- AWS DevOps Agent,
- Kiro Autonomous Agent,
- Kiro Web or equivalent autonomous workflows later.

For each tool or agent, record:

1. the problem solved,
2. why a simpler manual workflow, script, or CI job is insufficient,
3. the context provided,
4. the permissions granted,
5. the risks introduced,
6. the verification method,
7. the rollback or shutdown method,
8. the measurable value obtained.

Do not use more autonomy merely because it is available.

---

## 11. Tool-selection rule

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

---

## 12. Codex role

Codex remains the primary implementation agent unless a specific experiment intentionally compares another workflow.

For Codex tasks:

- provide a narrow goal,
- define constraints,
- identify relevant files when known,
- ask Codex to inspect the repository before editing,
- define acceptance criteria,
- define verification commands,
- request a report of changed files,
- prohibit unrelated refactors,
- prohibit commits unless explicitly requested,
- prohibit pushes unless explicitly requested.

### 12.1 Codex context efficiency

Use Codex context deliberately:

- keep prompts precise and bounded,
- remove unrelated history,
- avoid pasting large files when Codex can inspect them locally,
- keep root `AGENTS.md` concise,
- use nested `AGENTS.md` or `AGENTS.override.md` files only for directory-specific rules,
- enable only MCP servers needed for the current task,
- disable unused MCP servers,
- use a smaller available model for routine edits where appropriate,
- use a stronger model for architecture, ambiguous debugging, security analysis, and high-risk infrastructure changes,
- treat model names, prices, credits, quotas, and limits as changeable external configuration.

---

## 13. Early Kiro experiment

Test Kiro IDE early, in parallel with the live OSM baseline, but only on a small, reversible task.

Use a dedicated branch such as:

```text
experiment/kiro-steering-spec
```

Initial Kiro scope:

- inspect the existing repository,
- generate or refine workspace-local steering files only,
- compare the generated understanding with the existing `AGENTS.md`,
- create one small Kiro Feature Spec,
- review requirements, design, and tasks before implementation.

A suitable first Kiro Feature Spec is:

```text
Add explicit live-data status and error-state handling for German location
search without changing the safety model or adding AWS infrastructure.
```

Do not start with:

- global steering rules,
- MCP servers,
- AWS credentials,
- `terraform apply`,
- write-capable external tools,
- autonomous pull requests,
- large refactors,
- automatic production changes.

Treat Kiro Web or autonomous mode as a later, separate experiment requiring an explicit decision about:

- cost,
- repository access,
- permissions,
- review,
- rollback,
- shutdown.

---

## 14. Reference material

Use these repositories only as pattern catalogs:

- `https://github.com/brightkeycloud-chad/hands-on-aws-operations-with-chatgpt`
- `https://github.com/brightkeycloud-chad/ai-agents-and-mcp`

Do not copy them mechanically.

Adopt a pattern only when it solves a current RepairApp problem.

Do not copy third-party code, prompts, configurations, steering rules, or documentation verbatim unless licensing and suitability have been reviewed explicitly.

Treat reference repositories as potentially unsafe until inspected.

---

## 15. Working phases

### Phase 0 — Inspect current state

Before changes:

- inspect the repository structure,
- inspect `git status`,
- read `README.md`,
- read project instructions,
- identify the exact hardcoded Görlitz logic,
- identify taxonomy and OSM normalization,
- identify current UI states,
- identify local demo data,
- identify fixture and fallback behavior,
- identify whether tests already exist,
- list the smallest files that need to change.

### Phase 1 — Live OSM Germany baseline

Implement dynamic German location search and bounded Overpass queries.

Required:

- explicit city or postal-code submission,
- Germany validation,
- bounded search area,
- preserved taxonomy,
- preserved normalization,
- visible attribution,
- visible live-data status,
- explicit loading states,
- explicit error states,
- manual retry,
- configuration points for external endpoints,
- minimal documentation.

AWS infrastructure is outside Phase 1. Do not add it as part of this phase.

Verify manually with:

- Görlitz,
- Dresden,
- Berlin,
- valid German postal code,
- invalid location,
- location outside Germany,
- empty result,
- timeout simulation,
- HTTP 429 simulation,
- malformed-response simulation,
- missing-configuration simulation.

### Phase 2 — Small backend adapter

Add a minimal backend adapter only after the browser-level live path works.

This phase is required before claiming meaningful operational control over the external dependency.

Measure:

- request count,
- dependency latency,
- external errors,
- timeout count,
- rate-limit count,
- malformed responses,
- cache hit ratio,
- readiness.

Do not add a database unless a measured need exists.

### Phase 3 — Engineering baseline

Add only what is needed:

- taxonomy regression tests,
- dependency-state tests,
- fixtures,
- linting,
- minimal CI,
- `.env.example`,
- secret scanning,
- concise run instructions,
- minimal container build if justified.

### Phase 4 — Observability and controlled incidents

Add:

- structured logs,
- health behavior,
- readiness behavior,
- metrics,
- a short runbook,
- controlled failure injection.

Start with:

- timeout,
- HTTP 429,
- wrong endpoint,
- missing configuration,
- malformed response,
- broken readiness,
- empty valid response.

For each incident, compare:

1. expected symptoms,
2. observed behavior,
3. manual diagnosis,
4. agent-assisted diagnosis,
5. rollback,
6. lessons learned.

### Phase 5 — Minimal AWS sandbox

Propose at most two deployment options and recommend the simpler one.

Use:

- an isolated sandbox,
- an EU region by default,
- Infrastructure as Code,
- least privilege,
- tags,
- external secret handling,
- cost awareness,
- documented `plan`, `apply`, `verify`, and `destroy`,
- explicit approval before provisioning.

Do not add EKS unless justified by a specific learning objective.

### Later phases

Progressively evaluate:

- read-only AWS operational checks,
- architecture diagrams,
- cost-estimation workflows,
- controlled remediation proposals,
- selective read-only MCP,
- AWS Security Agent,
- AWS DevOps Agent,
- a narrow autonomous Kiro task,
- Kubernetes or GitOps only when justified.

Do not create artificial infrastructure merely to complete exercises.

Compare agent results with a manual baseline.

---

## 16. Approval gates

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

Never store secrets in the repository.

Use:

- environment variables,
- `.env.example`,
- appropriate secret storage,
- least-privilege access,
- explicit configuration documentation.

---

## 17. Working method

### Before editing

1. inspect the repository,
2. identify the current phase,
3. summarize the current state,
4. propose the smallest useful reversible change,
5. list files to modify,
6. define verification steps,
7. state risks,
8. state non-goals,
9. stop before editing unless implementation was explicitly requested.

### After editing

Report:

1. files changed,
2. behavior changed,
3. commands run,
4. verification results,
5. unresolved risks,
6. rollback method,
7. next smallest step.

Do not expand scope without a concrete reason.

---

## 18. Immediate task

Transform the existing Görlitz-only OSM integration into a live Germany-wide location-search workflow while preserving:

- the current taxonomy,
- the current OSM normalization logic,
- the current safety behavior.

AWS infrastructure is part of the later roadmap but outside the current task.

First:

1. inspect the repository,
2. identify the exact hardcoded Görlitz logic,
3. list the smallest files to modify,
4. propose the implementation plan,
5. define acceptance criteria,
6. define manual checks,
7. identify risks and non-goals,
8. stop before editing unless implementation is explicitly requested.
