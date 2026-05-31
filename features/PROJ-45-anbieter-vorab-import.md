# PROJ-45: Vorab-Import von Reparatur-Anbietern (OpenStreetMap + reparatur-initiativen.de)

## Status: Architected

**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Abhängigkeiten

- PROJ-11 (Vermittlung von Reparatur-Anbietern) — löst dort den vertagten offenen Punkt „OSM-Konkretisierung" ein.
- PROJ-30 (Konfiguration ausschließlich über `.env`) — Region/Endpunkt/Quellverzeichnis werden `.env`-gesteuert.

## Kontext

Heute speist sich die Vermittlung (`repair/anbieter.py`) aus einem **statischen, kuratierten Demo-Seed** mit Fantasie-Adressen (`*.example`). PROJ-11 hatte die echte Datenanbindung bewusst vertagt: primäre Zielquelle `reparatur-initiativen.de`, OpenStreetMap ergänzend, „vor Umsetzung zu konkretisieren". PROJ-45 setzt diese Anbindung um — als **Vorab-Import** in eine eigene lokale Tabelle, nicht als Live-Abfrage pro Vorgang.

**Warum OSM/Initiativen statt Google:** Die Daten beider Quellen dürfen **dauerhaft gespeichert** werden (OpenStreetMap: ODbL; reparatur-initiativen.de: offene Initiativen-Daten). Die Google-Places-Nutzungsbedingungen verbieten genau dieses Persistieren — Google scheidet für eine eigene Anbieter-Tabelle aus.

**Konkrete Datengrundlage (vorhanden in `sources/`):** Es gibt bereits einen Overpass-Export für die **Zielregion Görlitz / Niesky / Löbau** (`sources/goerlitz-niesky-loebau-places.geojson`, 11 Einträge) sowie die dazugehörige, dokumentierte Overpass-Query (`sources/overpass-api.md`) mit einem Maker-/Repair-/DIY-fokussierten Tag-Set. Zusätzlich liegen zwei kuratierte Freitext-Recherchen (`sources/existing_makerspaces_goerlitz.md`, `sources/existing_doityourself_shops.md`) vor — reicher Inhalt im `entity[…]`-Format **ohne strukturierte Adressfelder** (siehe Ausbaustufen).

## User Stories

- Als **Betreiber** möchte ich einen Overpass-Export (GeoJSON) für meine Region ablegen und per Kommandozeile in die Anbieter-Tabelle importieren, damit die Vermittlung echte statt erfundener Stellen liefert.
- Als **Betreiber** möchte ich, dass der Import auch ohne vorbereitete Datei funktioniert (Live-Abfrage der konfigurierten Region als Rückfallebene), damit ich nicht zwingend manuell exportieren muss.
- Als **Betreiber** möchte ich Region, Endpunkt und Quellverzeichnis über `.env` festlegen, damit ich die Region wechseln/erweitern kann, ohne Code zu ändern.
- Als **Betreiber** möchte ich das Lauf-Ergebnis nachvollziehen (importiert/aktualisiert/verworfen, Datenstand, genutzte Quelle), damit ich Aktualität und Erfolg kontrollieren kann.
- Als **Nutzer** möchte ich, dass die Vermittlung weiterhin sofort funktioniert — auch ohne je gelaufenen Import —, damit ich nie vor einer leeren Liste stehe.
- Als **Nutzer** möchte ich auch Stellen sehen, die in OSM nur als Punkt (ohne Hausnummer) erfasst sind, mit Ortsbezug und Kartenlink, damit ich keine echte Anlaufstelle wegen einer fehlenden Hausnummer verpasse.

## Akzeptanzkriterien

- [ ] Ein manuell startbares Import-Werkzeug liest **GeoJSON-Dateien aus dem Quellverzeichnis** (Default: `sources/`) und schreibt die Anbieter in eine eigene lokale Tabelle.
- [ ] Liegt **keine** verwertbare Datei vor, fällt der Import auf eine **Live-Overpass-Abfrage** der konfigurierten Region zurück (Datei bevorzugt, Live als Fallback).
- [ ] Region, Overpass-Endpunkt und Quellverzeichnis sind über `.env` konfigurierbar; ohne Konfiguration gelten dokumentierte Defaults (Region: Görlitz/Niesky/Löbau).
- [ ] OSM-Tags werden gemäß einer festen **Mapping-Tabelle** auf die bestehenden Typen `repaircafe`/`werkstatt`/`profi` abgebildet; das Schema in `cards.py`/`SPEC.md` und das Frontend bleiben **unverändert**.
- [ ] Jeder importierte Eintrag trägt: stabile Herkunfts-ID (OSM-Objekt-ID), Quelle, Attribution (ODbL), Importdatum (Datenstand) sowie Koordinaten.
- [ ] Einträge **ohne vollständige Adresse** (keine Straße/PLZ) werden **behalten**: mit Koordinaten und — sofern vorhanden — Ortsname, und sind als „Adresse unvollständig" markiert. Kein Eintrag geht allein wegen fehlender Hausnummer verloren.
- [ ] Importierte Daten und der bestehende kuratierte Seed werden **zusammengeführt** (Merge); die kuratierte Liste bleibt erhalten und dient als Fallback.
- [ ] Ein erneuter Import aktualisiert vorhandene Einträge anhand der Herkunfts-ID (Upsert), statt Dubletten anzulegen.
- [ ] Die öffentliche Schnittstelle der Vermittlung (`list_anbieter(kat, ort)`) bleibt unverändert; bestehende Aufrufer (Chat-Werkzeug, `/api/anbieter`) funktionieren ohne Anpassung.
- [ ] Ist eine Datei defekt oder die Live-Quelle nicht erreichbar, scheitert der Import nicht hart: er meldet es klar, verarbeitet was verwertbar ist und lässt den vorhandenen Datenbestand unangetastet.
- [ ] Quell-Endpunkt und Region stehen nicht hartkodiert im Code (Drift-Guard bleibt grün).

## Edge Cases

- **Frage:** Was, wenn ein OSM-Eintrag nur Koordinaten, aber keine Adresse hat (z. B. RABRYKA, BayWa im vorhandenen Export)? **Antwort:** Er wird behalten — Koordinaten + Ortsname werden geführt, „Adresse unvollständig" markiert, ein Kartenlink ist ableitbar. Nur Einträge **ohne Namen und ohne Koordinaten** werden verworfen; die Verwurfszahl steht im Lauf-Ergebnis (kein stilles Wegschneiden).
- **Frage:** Was, wenn keine GeoJSON-Datei vorliegt? **Antwort:** Live-Overpass-Abfrage der konfigurierten Region als Fallback; scheitert auch die, bleibt der vorhandene Bestand erhalten und es wird gemeldet.
- **Frage:** Was, wenn Overpass das Rate-Limit verhängt oder nicht antwortet? **Antwort:** Nicht-fataler Fehler; Quelle wird für den Lauf übersprungen, Bestand bleibt, klare Meldung im Ergebnis.
- **Frage:** Was, wenn eine GeoJSON-Datei syntaktisch defekt ist? **Antwort:** Diese Datei wird mit Meldung übersprungen, die übrigen Dateien werden normal verarbeitet.
- **Frage:** Was, wenn dieselbe Stelle in mehreren Exporten/Quellen vorkommt? **Antwort:** Die OSM-Objekt-ID hält sie zusammen (Upsert, keine Dublette). Eine fachliche Dedup über Quellgrenzen hinweg (Name+Ort) ist Ausbaustufe.
- **Frage:** Was, wenn der Betreiber eine ungültige Region/Endpunkt konfiguriert? **Antwort:** Fail-fast beim Import-Start mit benennender Meldung (analog PROJ-30), bevor Netzabrufe starten.
- **Frage:** Was, wenn nach dem Import zu einer Kategorie/Ort nichts passt? **Antwort:** Ehrlicher Leertreffer wie bisher (PROJ-11) — die Funktion erfindet nichts dazu.

## Technische Anforderungen

- Stack: Flask-Backend, stdlib (`sqlite3`, `urllib`, `json`) — möglichst **keine neue Laufzeit-Abhängigkeit** (GeoJSON ist JSON; kein GIS-Paket nötig).
- „Warnen statt sperren" / Fail-soft für die App: ein fehlender oder gescheiterter Import darf die Vermittlung nie blockieren.
- ODbL-Pflichten: Attribution mitführen; gespeicherte Daten sind erlaubt.
- Overpass-Nutzungsrichtlinien beim Live-Fallback beachten (faire Frequenz, kein Bulk-Hämmern).

## Tech Design (Solution Architect)

### A) Komponenten- & Datenfluss-Struktur

Dies ist ein **betreiberseitiges Daten-Feature** — keine neue End­nutzer-UI. Struktur als Modul-/Flussbaum:

```
Betreiber startet Import (Kommandozeile, von Hand)
│
└── Import-Werkzeug  (neu: repair/anbieter_import.py)
    ├── liest Region/Endpunkt/Quellverzeichnis aus .env (über repair/config.py)
    ├── Quelle A (bevorzugt): GeoJSON-Datei(en) im Quellverzeichnis  ← sources/*.geojson
    │     └── parst Features, mappt OSM-Tags → Typ/Kategorien
    ├── Quelle B (Fallback, wenn keine Datei): Live-Overpass-Abfrage der Region
    │     └── feste Tag-Query (aus sources/overpass-api.md übernommen)
    ├── prüft & verwirft nur Einträge ohne Name UND ohne Koordinaten
    ├── markiert Einträge ohne Straße/PLZ als „Adresse unvollständig"
    └── schreibt per Upsert (OSM-ID als Schlüssel) in die Anbieter-Tabelle (neu: anbieter.db)

Vermittlung (bestehend: repair/anbieter.py · list_anbieter)
│
├── liest aus der Anbieter-Tabelle (importierte Daten)
├── führt sie mit dem kuratierten Seed zusammen  (Merge)
└── ist die Tabelle leer/fehlt → nur kuratierter Seed (Fallback)
        │
        └── Aufrufer unverändert:
            ├── Chat-Werkzeug (repair/tools.py)
            └── HTTP-Endpunkt  POST/GET /api/anbieter (app.py)
```

Der **harte Schnitt** liegt allein zwischen *Import-Werkzeug* und *Tabelle*. `list_anbieter` behält Name und Signatur; Merge + Fallback sind intern. Für Frontend, Chat-Orchestrator und API ändert sich **nichts**.

### B) Datenmodell (Klartext, kein SQL)

**Neue lokale Tabelle „Anbieter"** in einer eigenen Datei `anbieter.db` (paket-relativ abgeleitet wie `vorgaenge.db`/`wissensbasis.db` — Layout, kein `.env`-Eintrag; gehört in `.gitignore`).

Jeder Anbieter-Eintrag hat:

- **Herkunfts-ID** — die OSM-Objekt-ID (z. B. `node/1459843579`). Eindeutiger Upsert-Schlüssel.
- **Quelle** — „OpenStreetMap" (später ggf. „reparatur-initiativen.de").
- **Typ** — `repaircafe`, `werkstatt` oder `profi` (gleiche Werte wie heute; abgeleitet über die Mapping-Tabelle in D).
- **Name, Adresse, Ort, PLZ** — soweit vorhanden; fehlende Felder bleiben leer (nichts wird erfunden).
- **Koordinaten** — Längen-/Breitengrad aus der GeoJSON-Geometrie. Tragen die Verortung, wenn die Adresse fehlt, und erlauben einen Kartenlink.
- **Adresse-vollständig** — Markierung „ja/nein"; „nein", wenn Straße oder PLZ fehlt.
- **Kontakt, Öffnungszeiten, Spezialisierung, Kostenhinweis** — soweit aus den OSM-Tags ableitbar (`phone`/`contact:phone`, `opening_hours`, abgeleitete Spezialisierung, Typ-bedingter Kostenhinweis).
- **Kategorien** — Geräte-Kategorien zum Filtern (`kleingeraet`, `elektronik`, `grossgeraet`, `mobilitaet`, `alle`), aus den Tags abgeleitet.
- **Attribution** — Pflichthinweis „© OpenStreetMap-Mitwirkende (ODbL)".
- **Datenstand** — Importdatum (ISO-Zeitstempel).

Der **kuratierte Seed** in `anbieter.py` bleibt unverändert als Code-Liste bestehen, wird zur Laufzeit dazugemischt und ist Rückfallebene + Träger von Spezial-Einträgen (z. B. Hersteller-Versand-Service), die in OSM nicht stehen.

### C) Tech-Entscheidungen (WARUM)

1. **Datei bevorzugt, Live als Fallback** — die vorhandene GeoJSON ist die schnellste, robusteste Quelle (kein Netz/Rate-Limit beim Import) und entspricht dem realen Workflow (Overpass Turbo → Export → Datei). Der Live-Fallback nimmt dem Betreiber den Zwang zum manuellen Export, ohne den Datei-Weg zu verdrängen.
2. **Manuelles CLI-Werkzeug statt Scheduler/Server-Start-Import** — koppelt teure/netzabhängige Abrufe vom Server-Start ab, extern per Cron einplanbar. Server-Start bleibt schnell und netzunabhängig.
3. **Koordinaten behalten statt Adress-Pflicht** — der reale Export zeigt: ~5 von 11 Stellen (u. a. RABRYKA, das Maker-Zentrum der Region) haben in OSM keine Hausnummer. Verwerfen würde echte Anlaufstellen tilgen. Koordinaten + Ortsname + Kartenlink erhalten den Wert; die Unvollständigkeit wird ehrlich markiert.
4. **Bestehende 3 Typen + Mapping** — vermeidet einen Umbau an `cards.py`-Schema, `SPEC.md` und Frontend. Maker-/Material-Spezifika landen im Freitextfeld „Spezialisierung", nicht in neuen Typen (das bleibt eine bewusste Ausbaustufe).
5. **Merge statt Ablösung** — kuratierte Liste ist gleichzeitig Fallback (leere/fehlende DB) und Träger von Spezial-Einträgen.
6. **Stabile Schnittstelle (`list_anbieter`)** — Merge hinter der bestehenden Funktion; kein Aufrufer muss angefasst werden. Minimale Angriffsfläche.
7. **Standardbibliothek statt neuer Pakete** — GeoJSON ist JSON (`json`), Live-Abruf über `urllib`, Speicherung über `sqlite3`. Kein GIS-/HTTP-Zusatzpaket, keine neue Lieferketten-/Lizenzfläche.
8. **Endpunkt-Default im Quell-Modul, nicht in `config.py`** — der Drift-Guard (`tests/test_config_drift.py`) verbietet `http(s)://`-Literale außerhalb einer Allowlist kuratierter Datenmodule (`anbieter.py`, `foerderung.py` …). Der Overpass-Default-Endpunkt gehört daher in ein allowlist-fähiges Anbieter-Quellmodul; `config.py` liefert nur die `.env`-Overrides (`ANBIETER_REGION`, `OVERPASS_URL`, `ANBIETER_SOURCES_DIR`) + Fail-fast-Validierung. (Allowlist wird um das neue Modul ergänzt.)
9. **Fail-soft im Import, Fail-fast bei Konfig** — defekte Datei / unerreichbare Live-Quelle ⇒ melden & überspringen, Bestand bleibt; ungültige Region/Endpunkt ⇒ Abbruch *vor* dem ersten Netzabruf mit benennender Meldung.

### D) OSM-Tag → Typ/Kategorie-Mapping (Klartext)

Quelle des Tag-Sets: `sources/overpass-api.md`. Abbildung auf die bestehenden Typen; Maker-/Material-Details in „Spezialisierung":

| OSM-Tag(s) | Typ | Spezialisierungs-/Kategorie-Hinweis |
|---|---|---|
| `workshop=repaircafe` | `repaircafe` | Repair-Café — gemeinsames Reparieren · Kategorien: `elektronik`, `kleingeraet`, `alle` |
| `leisure=hackerspace`, `fablab=yes`, `workshop=fablab` | `repaircafe` | Makerspace/FabLab (offene Werkstatt) · `service:3dprinter`/`service:lasercutter`/`shop=woodwork` reichern die Spezialisierung an |
| `amenity=workshop` | `werkstatt` | allgemeine Werkstatt |
| `social_facility=workshop` | `werkstatt` | soziale/Inklusions-Werkstatt |
| `amenity=coworking_space`, `office=coworking` | `werkstatt` | offene Arbeitsräume (i. d. R. kostenpflichtig) |
| `shop=doityourself` | `werkstatt` | Baumarkt — Materialbezug · Kategorie `alle` |
| `shop=woodwork` | `werkstatt` | Holzwerkstatt/Material |

Mehrere zutreffende Tags ⇒ der spezifischere gewinnt für den Typ; Geräte-/Service-Tags ergänzen die Spezialisierung kumulativ. Kostenhinweis wird typ-bedingt gesetzt (Repair-Café: „ehrenamtlich/Spendenbasis"; Werkstatt/Baumarkt/Coworking: „kostenpflichtig").

### E) Neue `.env`-Werte (zu dokumentieren in `.env.example`)

| Variable | Zweck | Default |
|---|---|---|
| `ANBIETER_REGION` | Region für die Live-Overpass-Abfrage (geocodeArea-Name(n)) | `Görlitz` / Niesky / Löbau (dokumentiert) |
| `OVERPASS_URL` | Overpass-API-Endpunkt (Live-Fallback) | öffentlicher Overpass-Endpunkt (Literal im Quell-Modul) |
| `ANBIETER_SOURCES_DIR` | Verzeichnis der GeoJSON-Exporte | `sources/` (paket-relativ) |

Alle mit Default ⇒ App/Import laufen ohne `.env`-Eintrag. URL-Default als Literal im Anbieter-Quellmodul (Allowlist); Region-/Verzeichnis-Default als Konstante in `config.py`.

### F) Abhängigkeiten (Packages)

- **Keine neuen.** `sqlite3`, `urllib`, `json`, `logging` aus der Standardbibliothek (alle bereits im Projekt verwendet).

### G) Ausbaustufen (bewusst NICHT in dieser Stufe)

- **Kuratierte Freitext-Quellen** (`sources/existing_makerspaces_goerlitz.md`, `…doityourself_shops.md`): reicher Inhalt, aber `entity[…]`-Format ohne Adressfelder → separate manuelle/LLM-gestützte Überführung in den kuratierten Seed, nicht Teil des automatischen GeoJSON-Imports.
- **reparatur-initiativen.de** als zweite strukturierte Live-Quelle (Repair-Café-Verzeichnis).
- Geocoding fehlender Adressen via Nominatim (max. 1 Anfrage/s) für echte Straßen/Entfernungen.
- Fachliche Dedup über Quellgrenzen (Name+Ort, OSM ↔ Initiativen).
- Neue Typen (`makerspace`, `baumarkt`/`materialquelle`) inkl. Schema-/SPEC-/Frontend-Anpassung.
- Bundesweiter Bulk-Import via Geofabrik-Dump; automatischer periodischer Import (Scheduler/Admin-Endpunkt).
