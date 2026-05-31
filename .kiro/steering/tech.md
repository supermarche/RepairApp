---
inclusion: always
---
# RepairApp Technical Constraints

## Current technical baseline

The immediate implementation target is a browser-level live OSM baseline.

Inspect the existing code before assuming a JavaScript framework, package manager, test runner, build system, or backend runtime.

A browser-only integration is a temporary demonstrator baseline, not the target production integration model.

## External dependencies

Treat these as separate replaceable dependencies:

1. a Nominatim-compatible geocoding provider,
2. an Overpass-compatible provider,
3. a map-tile provider only if the current UI displays a map,
4. a RepairApp backend adapter after that later phase is explicitly started.

Public community endpoints are shared, rate-limited services. Keep endpoints configurable and make degraded behavior visible.

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

## Verification baseline

Manual checks for Phase 1:

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

Add automated tests where they provide immediate value, especially for taxonomy normalization and dependency-state mapping.

If run, test, lint, or build commands are not documented yet, inspect the repository and report that gap. Do not invent commands.

## Later phases

A small backend adapter belongs to Phase 2 after the browser-level live path works.

AWS sandbox infrastructure belongs to Phase 5 after engineering and observability baselines exist.

Do not add a database, Terraform, IAM changes, AWS resources, MCP servers, or autonomous tools unless the corresponding reviewed phase or experiment explicitly requires them.
