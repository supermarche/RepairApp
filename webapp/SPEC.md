# Reparatur-Helfer — Implementierungs-Vertrag (verbindlich)

Wir bauen den Claude-Design-Prototyp `ReparaturApp.html` als echte Web-App nach.
Quelle / Design-of-truth: `../docs/design-handoff/project/` (HTML/CSS/JSX-Prototyp).
**Pixelgenau nachbauen** — die `repair.css`-Werte und `repair-themes.js`-Tokens sind maßgeblich.

Stack: **Python (Flask)** Backend + **Vanilla-JS**-Statemachine im Frontend + **Tailwind CSS**.
Zusätzlich: **OpenAI ChatGPT-API** für echte Live-Diagnose aus Freitext.

> Dieses Dokument ist der **lebende Vertrag** der Web-App: Datenschema, API,
> Klassennamen-Kopplung (JS↔CSS) und Theme-Tokens. Bei jeder Änderung an
> `orchestrator.py`/`cards.py`, dem Frontend oder dem CSS hier zuerst nachsehen.
> (Die historischen Stufen-Baupläne STUFE1–3 wurden nach Umsetzung entfernt — die
> PROJ-Historie steht in `../features/INDEX.md` und in Git.)
>
> **Stufe-4-Umbau (harter Schnitt, PROJ-32..37):** Der frühere Single-Shot
> `POST /api/diagnose` + `device`-Monolith ist **entfernt**. Der gesamte
> Reparatur-Flow läuft jetzt als **LLM-orchestrierter Chat** (`orchestrator.py`)
> mit Function-Calling (`tools.py`) und typisierten **Karten** (`cards.py`).
> Der maßgebliche Datenvertrag sind die **Karten-Schemata** unten — nicht mehr
> das `device`-Objekt.

## Verzeichnis

```
webapp/
  app.py                 Flask-App, Routen
  requirements.txt
  .env.example
  README.md              Setup/Run/Test-Anleitung
  repair/
    __init__.py
    config.py            zentrale .env-Konfiguration (getypte Getter + Fail-fast, PROJ-30)
    ai.py                OpenAI-Backend-Auflösung (_resolve_backend) für den Orchestrator
    roles.py             Rollen-Registry / Progressive Disclosure (PROJ-32)
    cards.py             Karten-Schemata + validate(typ, daten) (PROJ-33)
    tools.py             OpenAI-Function-Calling: specs() + dispatch() (PROJ-34)
    orchestrator.py      system_prefix() + run_turn() Tool-Call-Schleife (PROJ-35/36)
    vision.py            Vision-Extraktion (Stufe 1) + PDF->Bild, im Chat-Flow via Tool (PROJ-31)
    schema.py            Validierung/Normalisierung eines device-Objekts (Alt-Helfer)
    …                    weitere Fach-Module (siehe README „Projektstruktur")
  templates/
    index.html           SPA-Shell (enthält den HEAD-BLOCK unten 1:1)
  static/
    js/
      ui.js              Bausteine (Screen, AppBar, Buttons, Ampel, Sheet)
      screens.js         Screen-Renderer (Start, Triage, Ampel, Decision, Repair, Result, Path, Protocol)
      app.js             Statemachine + Live-Diagnose + Theme-Switcher
    css/
      repair.css         Komponenten-Styling + Themes (Port von repair.css + repair-themes.js)
```

Es gibt **keine** Demo-/Seed-Geräte; der Flow läuft ausschließlich über OpenAI
(LLM-orchestriert). Die gemeinsamen Verträge (Karten-Schemata, Klassennamen,
HEAD-Block) stehen unten.

## Datenvertrag: die **Karten** (`repair/cards.py` ist maßgeblich)

Der Orchestrator (`orchestrator.py` `run_turn`) gibt strukturierte Ergebnisse als
**Karten** aus — über das Tool `zeige_karte(typ, daten)`, server-seitig in
`cards.validate(typ, daten)` gegen ein JSON-Schema (Draft 2020-12) geprüft. Jede
Karte ist `{"typ": "<typ>", "daten": {…}}`. Es gibt **9 Karten-Typen**; das
Schema in `cards.py` ist die Quelle der Wahrheit, hier die verbindliche Übersicht:

```jsonc
// Querschnittsfeld trust (Vertrauens-Indikator, D3) — Pflicht in diagnose/ampel/vergleich/schritte
trust = {
  "level":     "hoch" | "mittel" | "niedrig",
  "quelle":    "…",                            // woher die Einschätzung stammt
  "konfidenz": "hoch" | "mittel" | "niedrig" | "unklar",
  "hinweis":   "…"                             // „die KI kann Fehler machen", verstärkt bei Gefahr
}
// Ampel-Level (achsen + gesamt): "gruen" | "gelb" | "rot"  → 🟢/🟡/🔴
```

| Typ | Pflichtfelder | Wesentliche Felder |
|---|---|---|
| `aufnahme` | `symptom` | `kategorie`, `bedingungen`, `seit_wann`, `getestet`, `eigentum:{ist_eigentuemer:bool, kostentraeger}` |
| `diagnose` | `kandidaten`, `unklar`, `trust` | `kandidaten[]`, `abgrenzungsfragen[]`, `unklar:bool` |
| `ampel` | `achsen`, `gesamt`, `begruendung`, `trust` | `achsen:{sicherheit,komplexitaet,kosten,machbarkeit}` (je Level), `gesamt` (Level), `defekt` (pro Defekt eine Ampel, D24) |
| `vergleich` | `empfehlung`, `begruendung`, `trust` | `repair`/`pro`/`neu`/`entsorgung` (Objekte), `empfehlung:"repair"\|"pro"\|"neu"\|"entsorgung"`, `geschaetzt:bool` |
| `schritte` | `schritte`, `trust` | `schritte[]:{titel,anfaenger,profi,safety,danger,handoff}`, `garantie_hinweis`, `misserfolg_pfad`, `bestaetigung_noetig:bool` (D25), `bestaetigung_text` |
| `hinweis` | `art`, `text` | `art:"garantie"\|"rueckruf"\|"datenloeschung"\|"sicherheit"\|"eigentum"`, `schwere:"info"\|"warnung"\|"kritisch"` |
| `anbieter` | `eintraege` | `eintraege[]` (Objekte) |
| `ersatzteil` | `eintraege` | `eintraege[]`, `affiliate_hinweis` (D8) |
| `erfolg` | — | `gespart_geld`, `gespart_co2`, `mutmach_satz` |

> **Nicht-sperrender Backstop (D15, PROJ-36):** Bei Gefahr (`ampel.achsen.sicherheit="rot"`
> oder ein `schritte`-Eintrag mit `danger:true`), bei Nutzer ≠ Eigentümer
> (`aufnahme.eigentum.ist_eigentuemer=false`) oder bei datentragenden Geräten hängt
> `orchestrator._sicherheits_backstop` server-erzwungen einen `hinweis` an — er
> **sperrt nichts**, sondern warnt eskalierend (der mündige Nutzer entscheidet).

## API-Endpunkte

- `GET  /`                      → rendert `index.html`
- `POST /api/vorgang`           → Body optional `{ "lang": "de"|"en" }` (Default `de`).
                                   Legt einen Vorgang an. Antwort: `{ "vorgang_id": "…" }`.
                                   **HTTP 200** (bewusste Abweichung von 201 — der Chat-Flow
                                   behandelt das Anlegen als gewöhnlichen Lese-/Schreib-Schritt,
                                   das Frontend prüft nur auf `vorgang_id`, kein `Location`-Header).
- `POST /api/chat`              → Body `{ "vorgang_id": "…", "text": "…" }`. Führt **einen**
                                   Chat-Turn über den Orchestrator aus (Tool-Call-Schleife gegen OpenAI).
                                   Erfolg (HTTP 200): `{ "vorgang_id", "antwort_text", "karten": [ {typ, daten} … ], "abgebrochen": bool }`.
                                   `karten` sind validierte Karten (s. o.); `abgebrochen=true`, wenn
                                   das Iterations-Limit (`MAX_TOOL_ITERATIONS`, Default 12) erreicht wurde.
  Fehlerfall (nie hart scheitern): `{ "error": "…", "code": "…" }` mit HTTP-Status —
  `400` (leerer Text, `empty`), `404` (unbekannter Vorgang, `no_vorgang`),
  `503` (kein Key, `no_backend`), `502` (KI-/Upstream-Fehler, `ai_error`).
  **PROJ-31 (Vision, additiv):** Der `/api/chat`-Body darf zusätzlich `medienIds` (am Vorgang
  gespeicherte Foto-/Dokument-Medien) enthalten; der Orchestrator wertet sie über das Tool
  `extrahiere_aus_medien` (→ `repair/vision.py`) aus und speist die erkannten Felder als Kontext
  in den Dialog. Ohne `medienIds` verhält sich der Endpunkt unverändert.
- `POST /api/extrahieren`        → Body `{ "vorgangId?", "medienIds?", "text?", "lang?" }` (PROJ-31, Stufe 1)
                                   Antwort **immer** HTTP 200 (scheitert nie hart):
                                   `{ "felder": {kategorie, modell, schaeden[], kaufdatum, haendler, hinweise[]},
                                      "source": "vision|no_vision_backend|vision_error|keine_medien",
                                      "hinweis", "bildAnzahl", "nichtsErkannt" }`. Vision läuft über OpenAI
                                   (Modell `VISION_MODEL` → sonst `OPENAI_MODEL`); PDFs werden serverseitig
                                   in Seitenbilder gewandelt.

- `POST /api/feedback`           → Body `{ "vorgang_id": "…", "text": "…", "screen": "…", "letzte_antwort": "…" }`.
                                   Speichert Prozess-Feedback des Nutzers lokal (kein externer Versand).
                                   `screen`: kurzes Zustands-Label (z. B. `"chat"` oder `"abgeschlossen"`).
                                   `letzte_antwort`: Text der letzten Assistenz-Antwort (oder `""`).
                                   Erfolg **HTTP 200**: `{ "ok": true, "feedback_id": "…" }`.
                                   Fehler: `{ "error": "…", "code": "…" }` mit Status —
                                   `400` (`empty`: leerer/Whitespace-Text), `400` (`too_long`: Text über Limit),
                                   `404` (`no_vorgang`: unbekannte Vorgangs-ID), `403` (`disabled`: Feature deaktiviert via `FEEDBACK_ENABLED=false`).
                                   (PROJ-46)

- `GET /api/vorgang/<vid>/report/varianten` → `{varianten:[{key,label,dateiname}], default}`
  (PROJ-44). 404 `{error, code:"no_vorgang"}` wenn Vorgang unbekannt.
- `GET /api/vorgang/<vid>/report.pdf?variante=<key>` → `application/pdf`,
  `Content-Disposition: attachment; filename="<dateiname>_<vid>.pdf"` (PROJ-44).
  Unbekannte vid → 404. Unbekannte/leere Variante → Default (`uebergabe`), kein Fehler.
  PDF-Engine nicht verfügbar (oder `REPORT_PDF_ENABLED=0`) → 503 `{error, code:"pdf_unavailable"}`.
- `GET /api/vorgang/<vid>/report.md?variante=<key>` → `text/markdown; charset=utf-8`,
  `Content-Disposition: attachment` (PROJ-44). 404 bei unbekannter vid.
- `GET /api/vorgang/<vid>/report.txt?variante=<key>` → `text/plain; charset=utf-8`,
  `Content-Disposition: attachment` (PROJ-44). 404 bei unbekannter vid.

> Die App bietet weitere Endpunkte (Vorgang-Persistenz `GET/PUT /api/vorgang/<id>`,
> kuratierte Service-Daten, Wissensbasis, Lotse, Consent, Multimodal …) —
> vollständige Liste in `app.py` bzw. README. Maßgeblich für *neue* Arbeit ist der
> Vertragskern hier: die **Karten-Schemata**, das `/api/chat`-Fehlerschema,
> Klassennamen und Themes.

## Konfiguration — ausschließlich über `.env` (verbindlich, PROJ-30)

Jede zur Laufzeit/Deployment veränderliche Einstellung wird **nur** über Umgebungsvariablen
gesteuert (geladen aus `webapp/.env` via `python-dotenv`; `load_dotenv()` in `app.py` ist die
einzige Lade-Stelle). **Keine** zweite Konfigurationsquelle, **keine** hartkodierten Endpunkte,
Keys, Modelle, Limits oder Bind-Adressen im Code. Getypte/validierte Werte bündelt
`repair/config.py` (u. a. `MAX_TOOL_ITERATIONS`, Default 12, für die Orchestrator-Schleife);
jeder Wert hat einen sinnvollen Default (App startet auch ohne `.env`).
Ungültige Werte → **Fail-fast** beim Start (`config.validate()`). Neue Konfig: per
`os.environ.get(...)`/`config`-Getter lesen **und** in `.env.example` dokumentieren — der
Drift-Guard `tests/test_config_drift.py` erzwingt beides (lauffähig ohne Server). Ausnahme:
layout-abgeleitete Pfade (`DB_PATH`, `MEDIA_DIR`). Vollständige Variablentabelle: `README.md`.

## ChatGPT-Integration (Orchestrator-Flow)

- Lib: `openai` (>=1.0). Key aus `OPENAI_API_KEY` (via `python-dotenv`). Modell aus `OPENAI_MODEL`
  (Default `gpt-4o-mini`). `repair/ai.py` liefert nur noch `_resolve_backend()` → `(client, model)`;
  bei fehlendem Key/Lib `(None, None)` → der Orchestrator antwortet `no_backend`.
- `orchestrator.system_prefix(lang)` baut einen **stabilen** (cachefreundlichen) System-Präfix:
  Leitlinien + Rollen-Katalog (`roles.katalog()`) + Werkzeug-Hinweis + Sprachdirektive. Rollen-Volltexte
  kommen on-demand via Tool `lade_rolle(name)` (Progressive Disclosure, PROJ-32).
- `orchestrator.run_turn(state, text)` führt die Function-Calling-Schleife (`tools.specs()`/`dispatch()`)
  mit Iterations-Limit (`config.max_tool_iterations()`, Default 12). Tools: `lade_rolle`, `zeige_karte`,
  `finde_anbieter`, `suche_ersatzteil`, `finde_foerderung`, `finde_entsorgung`, `recherche`.
- `zeige_karte(typ, daten)` wird server-seitig in `cards.validate(typ, daten)` geprüft (s. Karten-Schemata oben);
  ungültige Karten werden als Tool-Fehler an das Modell zurückgemeldet, statt hart zu scheitern.
- Sicherheit ist **nicht-sperrend** (D15): kein deterministisches Stop-Gate mehr, stattdessen der
  `_sicherheits_backstop`, der bei Gefahr/Fremd-Eigentum/datentragenden Geräten Hinweis-Karten anhängt.

## HEAD-BLOCK (1:1 in `<head>` von index.html)

```html
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Reparatur-Helfer</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet" />
<script src="https://cdn.tailwindcss.com"></script>
<script>
  // Tailwind nur fürs Layout/Canvas-Scaffold; Komponenten-Look kommt aus repair.css (Theme-Variablen).
  tailwind.config = { corePlugins: { preflight: false } };
</script>
<link rel="stylesheet" href="{{ url_for('static', filename='css/repair.css') }}" />
```

JS am Body-Ende, in dieser Reihenfolge:
```html
<script src="{{ url_for('static', filename='js/ui.js') }}"></script>
<script src="{{ url_for('static', filename='js/screens.js') }}"></script>
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
```

## Frontend-Verhalten (Port von repair-app.jsx + repair-screens.jsx + repair-ui.jsx)

- **Responsive Website (PROJ-38), keine Smartphone-Attrappe:** Die App rendert in eine
  **App-Spalte** (`.rk-app`) — mobil-first volle Breite, auf breiten Screens als zentrierte
  Lesespalte (`max-width: var(--app-max)`, Default 640px) auf neutraler Bühne (`--page-bg`).
  Geräterahmen, gefälschte Statusleiste und Home-Indikator entfallen ersatzlos; natürliches
  Seiten-Scrolling, AppBar/Footer sind `position: sticky`.
- Theme-Switcher (im Seitenkopf `.rk-pagehead`, über der Spalte): Solide / Werkstatt / Mutig →
  setzt CSS-Variablen **direkt am `.rk-app`-Element** (per inline-style) + Klasse `rk-theme-<id>`
  und `rk-case-<upper|none>` ebenfalls am `.rk-app`. **Default: Werkstatt.**
- Startscreen-Eingabefeld: Freitext startet den Chat — beim ersten Senden legt das Frontend per
  `POST /api/vorgang` einen Vorgang an und schickt den Text dann an `POST /api/chat`. Es gibt keine
  Geräteliste/Beispiele mehr; Freitext (+ Multimodal) ist der einzige Einstieg. Antwortet die API mit
  einem Fehler-Objekt, zeigt das Frontend den Hinweistext (`error`) an.
- Der Flow ist ein **Chat-Renderer**: `app.js`/`screens.js` zeigen `antwort_text` als Nachricht und
  rendern die zurückgegebenen `karten` (typisiert, s. Karten-Schemata) mit den vorhandenen
  Komponenten-Klassen. Der unbedingte Vertrauens-Footer („die KI kann Fehler machen") ist immer sichtbar.
- Klassennamen 1:1 wie in `repair.css` übernehmen (siehe Liste unten) — sonst greift das Styling nicht.

## Klassennamen-Vertrag (JS erzeugt sie, CSS stylt sie — exakt diese Namen)

`rk-page rk-pagehead rk-topbar
rk-app rk-screenwrap rk-body rk-footer rk-appbar rk-appbar-side rk-right rk-appbar-title
rk-bar-device rk-bar-step rk-iconbtn rk-eyebrow rk-q rk-q-tight rk-q-hint
rk-brand rk-brand-mark rk-brand-name rk-hero rk-hero-sub rk-input rk-input-ph rk-input-mic
rk-methods rk-method rk-method-e rk-method-t rk-mine rk-mine-head rk-device rk-device-e
rk-device-main rk-device-name rk-device-sub rk-device-go rk-device-sheet
rk-dots rk-dot done now rk-answers rk-answer rk-answer-on rk-freeanswer rk-triage-foot
rk-ampelcard rk-light rk-light-emoji rk-light-main rk-light-key rk-light-note rk-light-face
rk-verdict rk-verdict-go rk-verdict-stop rk-verdict-title rk-verdict-body
rk-trust rk-trust-dot rk-trust-i rk-aiwarn rk-aiwarn-strong
rk-paths rk-big rk-primary rk-soft rk-big-row rk-big-emoji rk-big-text rk-big-title rk-big-sub rk-big-arrow rk-reco
rk-compare rk-compare-head rk-compare-row rk-compare-k
rk-repair-tools rk-depth rk-speak rk-step-title rk-step-body rk-callout rk-callout-danger rk-callout-safety
rk-handoff rk-repair-foot rk-ghost rk-full rk-navrow rk-nav rk-nav-primary rk-nav-ghost
rk-slot rk-slot-tag rk-result-center rk-result-emoji rk-result-q rk-result-btns rk-big-yes rk-big-no
rk-win rk-impact rk-impact-cell rk-impact-num rk-impact-lab rk-win-foot rk-share-line
rk-proto rk-proto-head rk-proto-e rk-proto-name rk-proto-detail rk-proto-sec rk-proto-val
rk-proto-tags rk-proto-tag rk-proto-tag-muted rk-proto-ampel rk-proto-why rk-proto-reason
rk-proto-owner rk-proto-share rk-share-btn
rk-sheet-scrim rk-sheet rk-sheet-grip rk-sheet-title rk-sheet-note rk-sheet-fine rk-sheet-hr rk-sheet-level
rk-feedback-sheet rk-feedback-textarea rk-feedback-actions rk-feedback-send rk-feedback-cancel rk-feedback-thanks rk-feedback-thanks-icon rk-feedback-char-hint rk-feedback-char-warn
rk-theme-solide rk-theme-werkstatt rk-theme-mutig rk-case-upper rk-case-none`

## Theme-Tokens (Port von repair-themes.js — alle drei Themes als CSS-Variablen-Sets)

Werte 1:1 aus `../docs/design-handoff/project/repair-themes.js`. Default-Theme **Werkstatt** (Orange `--accent:#ff5a1f`, Indigo `--accent2:#2a2575`, harte Schatten `4px 4px 0 #16140f`, Space Grotesk).
CSS muss ohne Tweaks funktionieren: setze sinnvolle `--font-size:16px`, `--motion:.22s`, `--pad`, `--gap` als Defaults am `.rk-app`.
Theme-Switch erfolgt per JS (setzt die Variablen am `.rk-app`-Element): `app.js` hält die drei Token-Sets (Port aus repair-themes.js) und setzt sie auf die App-Spalte; `repair.css` liefert die regelbasierte Komponenten-CSS + die `--*`-Defaults + theme-spezifische Overrides (`.rk-theme-werkstatt …`, `.rk-theme-mutig …`). Die Layout-Tokens `--page-bg` und `--app-max` (Lesespalten-Breite) stehen am `:root`.

## Lauf-/Testkriterien (Definition of Done)

1. `pip install -r requirements.txt` && `flask --app app run` (oder `python app.py`) startet auf :5000.
2. `/` zeigt das Phone mit Startscreen im Werkstatt-Theme; Theme-Switcher wechselt live.
3. Freitext im Startfeld + gesetzter `OPENAI_API_KEY` → `POST /api/vorgang` (200, `vorgang_id`) →
   `POST /api/chat` liefert `antwort_text` + typisierte `karten`, die der Chat-Renderer anzeigt.
4. Bei Gefahr (rote Sicherheits-Ampel oder `danger:true`-Schritt): der nicht-sperrende Backstop hängt
   eine `hinweis`-Karte (`art:"sicherheit"`, `schwere:"kritisch"`) an; der DIY-Pfad bleibt offen,
   aber die `vergleich`-Karte empfiehlt klar „Profi" — der mündige Nutzer entscheidet (D15).
5. Protokoll/Verlauf füllt sich live; der Vorgang-State wird je Turn via `store.save_vorgang` persistiert.
6. Ohne `OPENAI_API_KEY` (oder bei API-Fehler): `POST /api/chat` antwortet mit Fehler-Objekt
   (`no_backend`/`ai_error`), das Frontend zeigt den Hinweis — kein Crash.
