---
inclusion: always
---
# RepairApp Technical Constraints

## Current technical baseline

The browser-level live OSM baseline is the Phase 1 prerequisite.

The next reviewed implementation target is Phase 2 — a small backend adapter, started only after the browser-level live path has passed the Phase 1 acceptance checks.

Inspect the existing code before assuming a JavaScript framework, package manager, test runner, build system, or backend runtime.

A browser-only integration is a temporary demonstrator baseline. Phase 2 moves public-service integration behind a RepairApp API.

## External dependencies

Treat these as separate replaceable dependencies:

1. a Nominatim-compatible geocoding provider,
2. an Overpass-compatible provider,
3. a map-tile provider only if the current UI displays a map,
4. a RepairApp backend adapter introduced in Phase 2 as the next integration boundary.

Public community endpoints are shared, rate-limited services. Keep endpoints configurable and make degraded behavior visible.

After Phase 2 starts, the browser should call the RepairApp API instead of calling geocoding or Overpass providers directly.

## Phase 1 OSM request flow

```text
explicit user submission
→ geocode requested city or postal code
→ validate Germany
→ derive bounded search area
→ execute bounded Overpass query
→ normalize OSM tags into the existing taxonomy
→ deduplicate results
→ display results, attribution, and live-data state
```

Do not:

- issue a Germany-wide Overpass query,
- preload a country-wide dataset,
- bulk geocode,
- add public-geocoding autocomplete,
- send a request after every keystroke,
- execute unnecessary parallel Overpass requests,
- prefetch or scrape tiles,
- bypass provider cache headers,
- present fixtures or stale data as live.

## Phase 2 backend-adapter request flow

After the Phase 1 acceptance checks pass:

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

Keep the adapter small. Centralize configuration, caching, conservative timeouts, rate limiting, consistent error mapping, structured integration logs, dependency-level measurements, readiness behavior, and controlled fixture injection. Do not add a database unless a measured need exists.

## Dependency states

Represent failures explicitly. Do not collapse them into `no_results`.

Minimum states:

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

The UI should distinguish invalid location, location outside Germany, empty live results, timeout, HTTP 429, malformed provider data, missing configuration, and upstream failure.

## Logging and measurements

For the browser-level baseline, measure or display where practical:

- location-search attempts,
- geocoding success and failure,
- Overpass success and failure,
- request latency,
- timeout events,
- HTTP 429 responses,
- malformed-response events,
- normalized result counts,
- visible dependency state.

Avoid logging personal data, full free-text problem descriptions, or unnecessary raw input.

Prefer normalized operational fields such as dependency name, provider, status class, elapsed time, and result count.

For the backend adapter, also measure API request count, dependency latency, timeout and rate-limit counts, malformed-response and configuration-error counts, cache hit ratio, degraded-mode count, and readiness state.

## Verification baseline

Before Phase 2 implementation, rerun the Phase 1 manual checks as a regression gate:

- Görlitz,
- Dresden,
- Berlin,
- valid German postal code,
- invalid location,
- location outside Germany,
- no matching resources,
- timeout simulation,
- HTTP 429 simulation,
- malformed-response simulation,
- missing-configuration simulation.

Add automated tests where they provide immediate value, especially for taxonomy normalization, dependency-state mapping, cache behavior, and adapter error mapping.

If run, test, lint, or build commands are not documented yet, inspect the repository and report that gap. Do not invent commands.

## Later phases

The small backend adapter is the Phase 2 stage immediately after the browser-level live path passes its acceptance checks.

AWS sandbox infrastructure belongs to Phase 5 after engineering and observability baselines exist.

Do not add a database, Terraform, IAM changes, AWS resources, MCP servers, or autonomous tools unless the corresponding reviewed phase or experiment explicitly requires them.
