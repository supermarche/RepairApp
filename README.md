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
6. Show matching resources on an OpenStreetMap map and in resource cards.

## Data limitations

The local-help results always start with a small in-repository demo dataset. It
is intended for the hackathon jury demo and does not represent live coverage.

The map uses Leaflet with OpenStreetMap tiles. Public map tiles and the optional
Overpass request are used only for the hackathon demo.

The "Load live OSM resources" button performs one bounded Overpass query for the
Gorlitz area and imports a practical subset of repair-related objects, such as
electronics repair, repair shops, bicycle repair services, and recycling
centres. Live data is never fetched automatically.

If the Overpass request fails or returns no useful matches, the local demo
dataset remains visible as the fallback.

Geolocation, Nominatim search, a backend, a database, provider registration, and
coverage dashboards are intentionally deferred until after the hackathon MVP.
