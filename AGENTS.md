# RepairApp Agent Instructions

RepairApp is a small hackathon MVP based on the documented "Problemanalyse" workflow. Keep the project intentionally simple, local, and easy to demo.

## Project Direction

- Keep the hackathon MVP intentionally small.
- Use a plain static web app with HTML, CSS, and JavaScript modules.
- Do not add a backend, database, authentication, external APIs, package manager, or build system unless explicitly requested.
- Preserve the existing Markdown research and planning documents.
- Use deterministic local rules and mock data for the first demo.

## OpenStreetMap Demo Exception

- External APIs and map libraries remain disallowed by default.
- For the RepairApp hackathon demo, Leaflet, OpenStreetMap tiles, and a single bounded user-triggered Overpass API query are allowed.
- The local deterministic demo dataset must remain available as a fallback.
- Do not add geolocation, Nominatim, a backend, a database, a framework, a package manager, or a build system.

## Problemanalyse Workflow

Use the existing Markdown documents as the source of truth for the demo flow:

1. Capture the user's description of the object and problem.
2. Classify the object type.
3. Classify the failure, condition, and safety risk.
4. Show possible actions: reset, maintenance, repair, professional repair, workaround, replacement, or recycling.
5. Recommend one concise next step.
6. Provide one short prevention tip.

## Safety Rules

- Treat electrical, battery, fire, smoke, heat, leaking, sharp, unstable, and injury-related cases conservatively.
- High-risk cases must suppress unsafe DIY recommendations.
- High-risk cases must prioritize stopping use, professional help, replacement, or recycling.
- Unknown or ambiguous cases should avoid false certainty and give cautious guidance.

## Implementation Discipline

- Make one focused implementation change at a time.
- Avoid overengineering and keep rule logic transparent.
- Prefer readable mock data and simple keyword rules over abstractions.
- After each implementation step, summarize changed files and verification results.
- Do not implement the app unless the user explicitly asks for implementation.
