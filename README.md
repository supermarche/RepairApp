# Repair App

contribution to [Digitale Oberlausitz e.V. Hackathon 2026](https://hackathon2026.digitale-oberlausitz.eu) 

## Local demo

Run the static RepairApp MVP locally:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000/app/> in a browser.

## Demo flow

The static MVP follows the documented Problemanalyse workflow:

1. Describe the problem and select the object category.
2. Classify the safety risk with deterministic local keyword rules.
3. Determine what kind of help is needed.
4. Show possible action options and one recommended next step.
5. Match the case with local repair resources from demo data.

## Data limitations

The current local-help results use a small in-repository demo dataset. It is
intended for the hackathon jury demo and does not represent live coverage.

Live OpenStreetMap or Overpass integration, geolocation, maps, provider
registration, and coverage dashboards are intentionally deferred until after the
hackathon MVP.
