# PROJ-45: Vorab-Import von Reparatur-Anbietern (OpenStreetMap + reparatur-initiativen.de)

## Status: Architected

**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Abhängigkeiten

- PROJ-11 (Vermittlung von Reparatur-Anbietern) — löst dort den vertagten offenen Punkt „OSM-Konkretisierung" ein.
- PROJ-30 (Konfiguration ausschließlich über `.env`) — Quell-Endpunkte/Region werden `.env`-gesteuert.

## Kontext

Heute speist sich die Vermittlung (`repair/anbieter.py`) aus einem **statischen, kuratierten Demo-Seed** mit Fantasie-Adressen (`*.example`). PROJ-11 hatte die echte Datenanbindung bewusst vertagt: primäre Zielquelle `reparatur-initiativen.de`, OpenStreetMap ergänzend, „vor Umsetzung zu konkretisieren". PROJ-44 setzt diese Anbindung um — als **Vorab-Import** in eine eigene lokale Tabelle, nicht als Live-Abfrage pro Vorgang.

**Warum OSM/Initiativen statt Google:** Die Daten beider Quellen dürfen **dauerhaft gespeichert** werden (OpenStreetMap: ODbL; reparatur-initiativen.de: offene Initiativen-Daten). Die Google-Places-Nutzungsbedingungen verbieten genau dieses Persistieren — Google scheidet für eine eigene Anbieter-Tabelle aus.

## User Stories

- Als **Betreiber** möchte ich die Anbieter-Tabelle einmalig/periodisch mit echten, lokal gespeicherten Reparatur-Stellen aus OpenStreetMap und reparatur-initiativen.de befüllen, damit die Vermittlung echte statt erfundener Adressen liefert.
- Als **Betreiber** möchte ich den abgedeckten geografischen Bereich über `.env` festlegen, damit ich klein anfangen (eine Region) und später erweitern kann, ohne Code zu ändern.
- Als **Betreiber** möchte ich den Import von Hand anstoßen und sein Ergebnis (importiert/aktualisiert/übersprungen, Datenstand) nachvollziehen, damit ich Aktualität und Erfolg kontrollieren kann.
- Als **Nutzer** möchte ich, dass die Vermittlung weiterhin sofort funktioniert — auch wenn noch nie importiert wurde oder ein Import gescheitert ist —, damit ich nie vor einer leeren Liste stehe.
- Als **Nutzer** möchte ich pro Anbieter Quelle und Datenstand erkennen, damit ich die Verlässlichkeit einschätzen und vor dem Hinbringen Kontakt aufnehmen kann.

## Akzeptanzkriterien

- [ ] Ein manuell startbares Import-Werkzeug holt Reparatur-Anbieter aus OpenStreetMap (Overpass) und aus reparatur-initiativen.de und schreibt sie in eine eigene lokale Tabelle.
- [ ] Der abgedeckte Bereich (Region / Bounding-Box / Ort) ist über `.env` konfigurierbar; ohne Konfiguration gilt ein dokumentierter Default.
- [ ] Jeder importierte Eintrag trägt: stabile Herkunfts-ID, Quelle (OSM / reparatur-initiativen.de), Attributionshinweis (ODbL) und Importdatum (Datenstand).
- [ ] Importierte Daten und der bestehende kuratierte Seed werden **zusammengeführt** (Merge); die kuratierte Liste bleibt erhalten und dient als Fallback.
- [ ] Ist die Tabelle leer oder der Import nie gelaufen, liefert die Vermittlung weiterhin den kuratierten Seed — kein Funktionsausfall, keine leere Liste.
- [ ] Ein erneuter Import aktualisiert vorhandene Einträge anhand der Herkunfts-ID, statt Dubletten anzulegen (Upsert).
- [ ] Die öffentliche Schnittstelle der Vermittlung (`list_anbieter(kat, ort)`) bleibt unverändert; bestehende Aufrufer (Chat-Werkzeug, `/api/anbieter`) funktionieren ohne Anpassung.
- [ ] Ist eine externe Quelle nicht erreichbar, scheitert der Import nicht hart: er meldet die eingeschränkte Verfügbarkeit, importiert die erreichbare Quelle und lässt den vorhandenen Datenbestand unangetastet.
- [ ] Quell-Endpunkte und Region stehen nicht hartkodiert im Code (Drift-Guard bleibt grün); Default-Endpunkte liegen an einer zulässigen, dokumentierten Stelle.
- [ ] Die Attribution „© OpenStreetMap-Mitwirkende" ist pro OSM-Eintrag mitführbar und in der Vermittlung anzeigbar.

## Edge Cases

- **Frage:** Was, wenn Overpass das Rate-Limit verhängt oder zeitweise nicht antwortet? **Antwort:** Der Import behandelt das als nicht-fatalen Fehler, überspringt die Quelle für diesen Lauf, behält den vorhandenen Bestand und meldet es klar im Lauf-Ergebnis.
- **Frage:** Was, wenn ein OSM-Eintrag unvollständig ist (keine Adresse, kein Name)? **Antwort:** Einträge ohne Mindestangaben (Name + verortbare Angabe) werden verworfen statt halb importiert; die Verwurfszahl wird im Lauf-Ergebnis genannt (kein stilles Wegschneiden).
- **Frage:** Was, wenn dieselbe Stelle in beiden Quellen vorkommt? **Antwort:** Die Herkunfts-ID je Quelle hält sie getrennt; eine spätere fachliche Dedup-Heuristik (Name+Ort) ist als Ausbaustufe vermerkt, nicht Teil dieser Stufe — die Mehrfachnennung wird dokumentiert, nicht still gefiltert.
- **Frage:** Was, wenn der Betreiber eine ungültige Region/Bbox konfiguriert? **Antwort:** Fail-fast beim Import-Start mit benennender Meldung (analog PROJ-30), bevor Netzabrufe starten.
- **Frage:** Was, wenn nach dem Import zu einer Kategorie/Ort nichts passt? **Antwort:** Ehrlicher Leertreffer wie bisher (PROJ-11) — die Funktion erfindet nichts dazu.

## Technische Anforderungen

- Stack: Flask-Backend, stdlib (`sqlite3`, `urllib`, `json`) — möglichst **keine neue Laufzeit-Abhängigkeit**.
- „Warnen statt sperren" / Fail-soft für die App: ein fehlender oder gescheiterter Import darf die Vermittlung nie blockieren.
- ODbL-Pflichten: Attribution mitführen; gespeicherte Daten sind erlaubt.
- Nominatim-/Overpass-Nutzungsrichtlinien beachten (kein Bulk-Hämmern, faire Abfragefrequenz).

## Tech Design (Solution Architect)

### A) Komponenten- & Datenfluss-Struktur

Dies ist ein **betreiberseitiges Daten-Feature** — keine neue End­nutzer-UI. Struktur als Modul-/Flussbaum:

```
Betreiber startet Import (Kommandozeile, von Hand)
│
└── Import-Werkzeug  (neu: repair/anbieter_import.py)
    ├── liest Region + Quell-Endpunkte aus .env  (über repair/config.py)
    ├── Quelle 1: OpenStreetMap / Overpass
    │     └── fragt Reparatur-Stellen der Region ab
    │         (Radwerkstätten, Elektronik-/Geräte-Reparatur)
    ├── Quelle 2: reparatur-initiativen.de
    │     └── holt Repair Cafés / Initiativen der Region
    ├── prüft & verwirft unvollständige Einträge
    └── schreibt per Upsert in die Anbieter-Tabelle  (neu: anbieter.db)

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

Der **harte Schnitt** dieses Features liegt allein zwischen *Import-Werkzeug* und *Tabelle*. `list_anbieter` behält Name und Signatur; alles dahinter (Merge + Fallback) ist intern. Damit ändert sich für Frontend, Chat-Orchestrator und API **nichts**.

### B) Datenmodell (Klartext, kein SQL)

**Neue lokale Tabelle „Anbieter"** in einer eigenen Datei `anbieter.db` (paket-relativ abgeleitet wie `vorgaenge.db`/`wissensbasis.db` — das ist Layout, keine Deployment-Konfiguration, daher kein `.env`-Eintrag; gehört in `.gitignore`).

Jeder Anbieter-Eintrag hat:

- **Herkunfts-ID** — eindeutiger Schlüssel je Quelle (z. B. die OSM-Objekt-ID bzw. die Kennung der Initiative). Dient dem Upsert (kein Dublettenwuchs bei Re-Import).
- **Quelle** — „OpenStreetMap" oder „reparatur-initiativen.de".
- **Typ** — `repaircafe`, `werkstatt` oder `profi` (gleiche Werte wie heute in `anbieter.py`).
- **Name, Adresse, Ort, PLZ** — Standortangaben.
- **Kontakt, Öffnungszeiten, Spezialisierung, Kostenhinweis** — soweit aus der Quelle verfügbar; fehlende Felder bleiben leer (werden nicht erfunden).
- **Kategorien** — Geräte-Kategorien zum Filtern (`kleingeraet`, `elektronik`, `grossgeraet`, `mobilitaet`, `alle`) — aus den Quell-Merkmalen abgeleitet.
- **Attribution** — Pflichthinweis (z. B. „© OpenStreetMap-Mitwirkende, ODbL").
- **Datenstand** — Importdatum (ISO-Zeitstempel), als Aktualitätsanzeige.

Der **kuratierte Seed** in `anbieter.py` bleibt unverändert als Code-Liste bestehen und wird zur Laufzeit dazugemischt — er ist die Rückfallebene und enthält Spezial-Einträge (z. B. Hersteller-Versand-Service), die in OSM nicht stehen.

### C) Tech-Entscheidungen (WARUM)

1. **Vorab-Import statt Live-Abfrage** — die Vermittlung antwortet ohne Netz-Latenz und unabhängig von Erreichbarkeit/Rate-Limit der Quellen. Aktualität wird über das Importdatum transparent gemacht statt über Echtzeit erkauft.
2. **Manuelles CLI-Werkzeug statt Scheduler/Server-Start-Import** — passt zum aktuellen Stack ohne Hintergrund-Dienst, koppelt teure Netzabrufe vom Server-Start ab und lässt sich extern per Cron einplanen. Der Server-Start bleibt schnell und netzunabhängig.
3. **Konfigurierbare Region (Bbox/Ort) statt bundesweit** — kleiner, rate-limit-freundlicher Datenstand zum Start; per `.env` erweiterbar, ohne Code zu ändern. Vermeidet großen Erst-Download und langen Importlauf.
4. **Merge statt Ablösung** — die kuratierte Liste ist gleichzeitig Fallback (leere/fehlende DB) *und* Träger von Spezial-Einträgen. Robuster als „DB ist alleinige Wahrheit".
5. **Stabile Schnittstelle (`list_anbieter`)** — der Merge passiert hinter der bestehenden Funktion; kein Aufrufer (Chat-Werkzeug, API, Frontend) muss angefasst werden. Minimale Angriffsfläche.
6. **Standardbibliothek statt neuer Pakete** — Abruf über `urllib`, Speicherung über `sqlite3` (beides bereits im Einsatz). Keine neue Laufzeit-Abhängigkeit, keine zusätzliche Lieferketten-/Lizenzfläche.
7. **Endpunkt-Defaults im Quell-Modul, nicht in `config.py`** — der Drift-Guard (`tests/test_config_drift.py`) verbietet `http(s)://`-Literale in allen Modulen außer einer Allowlist kuratierter Datenmodule (`anbieter.py`, `foerderung.py` …). Die Default-Endpunkte gehören daher konzeptuell zu den kuratierten Quellen und liegen in einem allowlist-fähigen Anbieter-Quellmodul; `config.py` liefert nur die `.env`-Overrides (`OVERPASS_URL`, `REPARATUR_INITIATIVEN_URL`, `ANBIETER_REGION`) und die Fail-fast-Validierung. (Die Allowlist wird um das neue Modul ergänzt.)
8. **Fail-soft im Import, Fail-fast bei Konfig** — unerreichbare Quelle ⇒ Lauf meldet & überspringt, Bestand bleibt; ungültige Region ⇒ Abbruch *vor* dem ersten Netzabruf mit benennender Meldung (Linie von PROJ-30).

### D) Neue `.env`-Werte (zu dokumentieren in `.env.example`)

| Variable | Zweck | Default |
|---|---|---|
| `ANBIETER_REGION` | abzudeckender Bereich (Bounding-Box bzw. Orts-/Gebietskennung für Overpass) | dokumentierter Beispiel-Bereich (eine Stadt) |
| `OVERPASS_URL` | Overpass-API-Endpunkt | öffentlicher Overpass-Endpunkt |
| `REPARATUR_INITIATIVEN_URL` | Datenendpunkt reparatur-initiativen.de | offizieller Initiativen-Datenendpunkt |

Alle drei mit Default ⇒ App/Import laufen auch ohne `.env`-Eintrag. Defaults für die beiden URLs als Literal im Anbieter-Quellmodul (Allowlist), Region-Default als Konstante in `config.py`.

### E) Abhängigkeiten (Packages)

- **Keine neuen.** Nutzung von `sqlite3`, `urllib`, `json`, `logging` aus der Standardbibliothek (alle bereits im Projekt verwendet).

### F) Ausbaustufen (bewusst NICHT in dieser Stufe)

- Fachliche Dedup-Heuristik über Quellgrenzen hinweg (Name+Ort-Abgleich OSM ↔ Initiativen).
- Geocoding fehlender Koordinaten über Nominatim (für echte Entfernungsberechnung statt Textfilter).
- Bundesweiter Bulk-Import via Geofabrik-Dump.
- Automatischer periodischer Import (Scheduler/Admin-Endpunkt).
