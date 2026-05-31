# Reparatur-Helfer — Web-App

Echte Web-App-Nachbildung des Claude-Design-Prototyps `ReparaturApp.html`.
**Python (Flask)**-Backend + Vanilla-JS-Frontend + Tailwind CSS. Der gesamte
Reparatur-Flow läuft **ausschließlich** als LLM-orchestrierter Chat über die
OpenAI-Cloud (Function-Calling + typisierte Karten) — es gibt keine
hinterlegten Demo-/Seed-Geräte mehr.

Verbindlicher Vertrag (Schema, Endpunkte): [`SPEC.md`](SPEC.md).

## Schnellstart

```bash
cd webapp

# 1. virtuelle Umgebung anlegen & aktivieren
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Konfiguration anlegen — OpenAI-Key ist Pflicht (s. u.)
cp .env.example .env

# 4. starten
python app.py                       # → http://127.0.0.1:5000
# oder:
flask --app app run                 # ggf. --debug für Auto-Reload
```

Die App läuft auf **Port 5000**.

## Diagnose-Backend (OpenAI, Orchestrator-Flow)

Der Chat-Flow (`POST /api/chat`) läuft ausschließlich über die OpenAI-Cloud
(Function-Calling-Schleife im `repair/orchestrator.py`):

- Key in `.env` eintragen: `OPENAI_API_KEY=sk-...`
- Modell optional über `OPENAI_MODEL`, Default `gpt-4o-mini`.
- Timeout je Antwort über `LLM_TIMEOUT` (Sekunden), Default `180`.
- Tool-Call-Runden pro Chat-Turn über `MAX_TOOL_ITERATIONS`, Default `12`.

**Ohne gesetzten Key** antwortet `POST /api/chat` mit einem sauberen Fehler
(`HTTP 503`, `"code": "no_backend"`) und das Frontend zeigt einen Hinweis — es
wird nie hart gescheitert, aber es gibt auch keinen Demo-Modus (keine
hinterlegten Seed-Geräte).

## API-Endpunkte

| Methode + Pfad            | Antwort                                                        |
|---------------------------|----------------------------------------------------------------|
| `GET  /`                  | rendert `templates/index.html` (SPA-Shell)                     |
| `POST /api/vorgang`       | Body optional `{"lang":"de"\|"en"}` → `{"vorgang_id": "…"}` (**HTTP 200**, bewusste Abweichung von 201) |
| `POST /api/chat`          | Body `{"vorgang_id","text"}` → Erfolg `{"vorgang_id", "antwort_text", "karten": [{typ, daten}…], "abgebrochen"}` |

`POST /api/chat` führt **einen** Chat-Turn über den Orchestrator aus; die
`karten` sind typisierte, server-validierte Karten (9 Typen, s. `repair/cards.py`
und `SPEC.md`). `abgebrochen=true`, wenn das Iterations-Limit (`MAX_TOOL_ITERATIONS`)
erreicht wurde. Im Fehlerfall liefert der Endpunkt ein Objekt
`{"error": "…", "code": "…"}` mit passendem HTTP-Status: `400` (leerer Text,
`empty`), `404` (unbekannter Vorgang, `no_vorgang`), `503` (kein LLM-Backend,
`no_backend`), `502` (KI-/Upstream-Fehler, `ai_error`). Alle JSON-Antworten sind
UTF-8 mit echten Emojis/Umlauten (kein ASCII-Escaping).

### Stufe-2-Service-Endpunkte (PROJ-11/12/13/14/26)

Alle liefern HTTP 200 mit kuratiertem Seed (scheitern nie hart). Query-Parameter
sind optional und filtern nur; ein Leertreffer liefert `fallback: true` + `hinweis`.

| Methode + Pfad                | Query          | Antwort (Kurzform)                                          |
|-------------------------------|----------------|-------------------------------------------------------------|
| `GET /api/anbieter`           | `?kat=&ort=`   | `{items[], fallback, hinweis}` — Repair-Café/Werkstatt/Profi |
| `GET /api/entsorgung`         | `?kat=&ort=`   | `{items[], fallback, hinweis}` — Wertstoffhof/Rücknahme/Sammelstelle (+Rohstoff) |
| `GET /api/alternativen`       | `?kat=`        | `{items[], breakEven, hinweis, fallback}` — Alternativgeräte |
| `GET /api/ersatzteile`        | `?device=&defekt=` | `{items[], guenstigsteZuerst, hinweis, fallback}` — günstigste zuerst, Affiliate-Leitplanke (D8) |
| `GET /api/triage/universal`   | —              | `{fragen[]}` — 5 systematische, gerätunabhängige Fragen      |

Alle Service-Daten sind **kuratierte Demodaten** (jeder Eintrag mit `quelle` +
`kuratiert: true`, keine Netzwerk-/Scraping-Zugriffe).

## Logging (PROJ-29)

Die App schreibt zur Laufzeit ein **zentrales Log gleichzeitig in eine Datei und
auf die Konsole**:

- **Speicherort:** `webapp/logs/repair.log` (das `logs/`-Verzeichnis wird beim
  Start automatisch angelegt; es ist gitignored).
- **Rotation & Aufbewahrung:** täglich um Mitternacht; **14** Tage werden
  vorgehalten, ältere Dateien automatisch gelöscht. Rotierte Dateien tragen ein
  Datums-Suffix, z. B. `repair.log.2026-05-30`.
- **Level konfigurieren:** über `LOG_LEVEL` in der `.env`
  (`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`). Default ist **`DEBUG`**;
  ungültige Werte fallen ohne Crash auf `DEBUG` zurück.
- **Inhalt:** jeder API-Request (Methode, Pfad, Status — 4xx/5xx auf
  `WARNING`/`ERROR`), die Werkzeug-Zugriffslogs, Schlüssel-Ereignisse der
  Fach-Module (Diagnose-Quelle `ai`/`fallback` + Modell, Lotse-Routing,
  Vorgangs-CRUD, Wissensbasis-Freigaben, Recherche-Herkunft, Medien-Metadaten)
  sowie jede unbehandelte Exception **mit Stacktrace**.

> ⚠ **Datenschutz-Hinweis (PII):** Auf `DEBUG` können auch
> **Klartext-Nutzereingaben** (Freitext-Symptome, Standort, Medien-Metadaten) im
> Log landen. Diese Tiefe ist **nur für die lokale Dev-Umgebung** gedacht — für
> Produktion `LOG_LEVEL=INFO` (oder höher) setzen.

## Konfiguration — ausschließlich über `.env` (PROJ-30)

Jede zur Laufzeit/Deployment veränderliche Einstellung wird **nur** über
Umgebungsvariablen gesteuert, geladen aus `webapp/.env` (`python-dotenv`,
`load_dotenv()` in `app.py`). Es gibt **keine** zweite Konfigurationsquelle und
keine im Code hartkodierten Endpunkte/Keys/Modelle/Limits. Die getypten/
validierten Werte bündelt `repair/config.py`; jeder Wert hat einen Default,
sodass die App auch **ganz ohne** `.env` startet.

| Variable | Default | Zweck |
|---|---|---|
| `OPENAI_API_KEY` | _(leer)_ | OpenAI-Cloud-Key (Pflicht für die Diagnose) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modell für die Diagnose |
| `LLM_TIMEOUT` | `180` | Timeout (s) je LLM-Antwort — **> 0**, sonst Fail-fast |
| `MAX_TOOL_ITERATIONS` | `12` | Tool-Call-Runden pro Chat-Turn (Orchestrator) — **≥ 1**, sonst Fail-fast |
| `WHISPER_MODEL` | `whisper-1` | Modell für die Audio-Transkription (PROJ-27) |
| `VISION_MODEL` | _(leer)_ | Vision-Modell für die Bild-/Dokument-Auswertung (PROJ-31); leer → Cloud-Diagnosemodell (`OPENAI_MODEL`, kann Vision) |
| `MAX_UPLOAD_BYTES` | `10485760` | Max. Mediengröße in Bytes — **> 0**, sonst Fail-fast |
| `MAX_MEDIEN_PRO_ANFRAGE` | `6` | Max. Medien je Diagnose-Anfrage (PROJ-31) — **1..100**, sonst Fail-fast |
| `MAX_PDF_SEITEN` | `5` | Max. ausgewertete PDF-Seiten je Dokument (PROJ-31) — **1..50**, sonst Fail-fast |
| `SEARXNG_URL` | _(leer)_ | SearXNG für die Online-Recherche (PROJ-16) |
| `PROTOKOLL_ENABLED` | `1` | Anfrage-Protokoll an/aus (PROJ-28) |
| `LOG_LEVEL` | `DEBUG` | Log-Level (PROJ-29) |
| `FLASK_DEBUG` | `1` | Flask-Debug-Modus (tolerant: `0`/`false`/leer = aus) |
| `HOST` | `127.0.0.1` | Bind-Adresse (z. B. `0.0.0.0` im Container) |
| `PORT` | `5000` | TCP-Port — **1..65535**, sonst Fail-fast |
| `REPORT_PDF_ENABLED` | `1` | Service-Point-Report-PDF an/aus (PROJ-44): `0`/`false` deaktiviert den PDF-Download, Text-/Markdown-Download bleibt verfügbar |
| `FEEDBACK_ENABLED` | `1` | Feedback-Button an/aus (PROJ-46): `0`/`false` blendet Button aus; `/api/feedback` antwortet sauber ablehnend (403 disabled) |
| `MAX_FEEDBACK_BYTES` | `4000` | Max. Feedback-Textlänge in Bytes (UTF-8, PROJ-46) — **1..10000000**, sonst Fail-fast |
| `PROMPT_CACHE_KEY_ENABLED` | `1` | Expliziten `prompt_cache_key` je Sprache senden (PROJ-48): `0`/`false` deaktiviert; nur Auto-Caching läuft weiter |
| `PROMPT_CACHE_KEY_PREFIX` | `repair` | Präfix des `prompt_cache_key` (PROJ-48); Schlüssel = `<präfix>-<sprache>`, z. B. `repair-de` |

**Fail-fast:** Fehlende Variablen fallen still auf den Default zurück.
Syntaktisch **ungültige** Werte (`PORT=abc`, `PORT=99999`, `LLM_TIMEOUT=xyz`,
`MAX_UPLOAD_BYTES=-1`) brechen den Start mit einer klaren, die Variable und den
erwarteten Bereich benennenden Meldung ab (`config.validate()` in `app.py`).

`VISION_MODEL` ist seit PROJ-31 aktiv (bleibt mit sinnvollem Default
auskommentiert; Vision läuft über OpenAI). **Ausnahme** (kein `.env`):
layout-abgeleitete Pfade (`DB_PATH`, `MEDIA_DIR`).

**PDF-Auswertung (PROJ-31):** Für die Vision-Auswertung beigefügter **PDFs**
wird `PyMuPDF` benötigt (in `requirements.txt`). Es ist **optional/lazy**
importiert — fehlt es, degradiert die PDF-Auswertung mit Hinweis statt zu
crashen (Bilder funktionieren weiterhin).

**Drift-Guard lokal ausführen** — gleicht `.env.example` ↔ Code in beide
Richtungen ab und schlägt bei verbotenen Hardcode-Mustern an:

```bash
cd webapp
python tests/test_config_drift.py        # standalone (ohne pytest)
# oder, falls pytest installiert:
python -m pytest tests/test_config_drift.py -q
```

## Projektstruktur (Backend-Anteil)

```
webapp/
  app.py               Flask-App + Routen
  requirements.txt     Flask, openai, python-dotenv
  .env.example         Vorlage für die Konfiguration
  repair/
    __init__.py
    config.py          zentrale .env-Konfiguration: getypte Getter + Fail-fast-Validierung (PROJ-30)
    ai.py              _resolve_backend() — OpenAI-Backend-Auflösung für den Orchestrator
    roles.py           Rollen-Registry: liest docs/runtime-roles/*.md, Progressive Disclosure (PROJ-32)
    cards.py           Karten-Schemata (9 Typen) + validate(typ, daten) (PROJ-33)
    tools.py           OpenAI-Function-Calling: specs() + dispatch() (PROJ-34)
    orchestrator.py    system_prefix() + run_turn() Tool-Call-Schleife + Backstop (PROJ-35/36)
    schema.py          normalize_device() — Validierung/Reparatur eines device-Objekts (Alt-Helfer)
    logconf.py         setup_logging() — zentrales Logging (Datei+Konsole, tägl. Rotation, PROJ-29)
    protokoll_log.py   protokolliere() — Anfrage-Protokoll als Markdown pro Vorgang (PROJ-28)
    foerderung.py      kuratierte Reparatur-Förderungen (PROJ-6)
    store.py           Vorgang-Persistenz (sqlite3, PROJ-9)
    export.py          Protokoll-Renderer txt + Lese-Ansicht HTML (PROJ-10, +Stufe-2-Abschnitte)
    anbieter.py        kuratierte Reparatur-Anbieter (PROJ-11)
    entsorgung.py      kuratierte Entsorgungs-/Recyclingwege (PROJ-12)
    produktsuche.py    kuratierte Alternativgeräte + Break-Even (PROJ-13)
    ersatzteile.py     kuratierte Ersatzteile, günstigste zuerst (PROJ-14)
    triage.py          universelle, gerätunabhängige Triage-Fragen (PROJ-26)
  templates/index.html [AGENT-B]   SPA-Shell
  static/js, static/css [AGENT-B/C] Frontend
```

## Tests (Definition of Done aus SPEC.md)

Backend-Smoke-Test (ohne Backend → sauberer Fehler statt Crash):

```bash
cd webapp
env -u OPENAI_API_KEY .venv/bin/python -c \
  "from repair import orchestrator; print(orchestrator.run_turn({'messages':[]}, 'Toaster kaputt').get('code'))"
# erwartet:
#   no_backend
```

Konfigurations-Drift-Guard (PROJ-30) — prüft `.env.example` ↔ Code und Hardcode-Muster:

```bash
cd webapp
python tests/test_config_drift.py
# erwartet:
#   9/9 Checks bestanden.
```

Endpunkte manuell prüfen (Server läuft auf :5000):

```bash
# entfernte Routen sind jetzt 404 (Demo-Geräte und der alte Single-Shot /api/diagnose)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/api/devices            # 404
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:5000/api/diagnose \
  -H "Content-Type: application/json" -d '{"text":"x"}'                                # 404
# Chat-Flow: Vorgang anlegen (200), dann ein Turn (503 ohne Key, 200 mit gesetztem OPENAI_API_KEY)
VID=$(curl -s -X POST http://127.0.0.1:5000/api/vorgang | python -c "import sys,json;print(json.load(sys.stdin)['vorgang_id'])")
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" -d "{\"vorgang_id\":\"$VID\",\"text\":\"Meine Mikrowelle brummt laut\"}"
# Stufe-2/3-Dienste (kuratierte Daten) bleiben verfügbar
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/api/anbieter           # 200
```

Voller UI-Flow (mit gesetztem OpenAI-Key): siehe `SPEC.md`
„Lauf-/Testkriterien" — Freitext → `/api/vorgang` + `/api/chat`, Chat-Renderer
mit typisierten Karten, Theme-Switcher.
