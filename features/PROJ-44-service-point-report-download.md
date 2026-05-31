# PROJ-44: Service-Point-Übergabe-Report (PDF- & Text-Download, mehrere Zielgruppen-Varianten)

## Status: In Review

**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Kurzbeschreibung

Ein Download, mit dem der Nutzer den aktuellen Vorgang als **Übergabe-Report** für eine
**Service-/Annahmestelle** (Repair Café, Werkstatt-Theke) mitnehmen kann. Der Report ist in
**mehreren Varianten je Zielgruppe** verfügbar (z. B. kompakte Übergabe-Kurzfassung, ausführliches
Werkstatt-Protokoll, Eigen-Beleg für den Nutzer) und kann je Variante als **echtes PDF**
heruntergeladen werden — zusätzlich als **Klartext/Markdown-Report** für Geräte/Wege ohne PDF.

> Abgrenzung zu **PROJ-10** (Protokoll-Export & Teilen): PROJ-10 liefert ein einzelnes
> Klartext-Format und eine HTML-Lese-Ansicht, deren „PDF" nur über den **Browser-Druck**
> entsteht (kein Datei-Download vom Server) und nur eine Zielgruppe kennt. PROJ-44 ergänzt
> einen **server-seitig erzeugten PDF-Download** mit **auswählbaren, zielgruppen-spezifischen
> Report-Varianten** sowie einen parallelen Text-/Markdown-Download. Die gemeinsame
> Datenbeschaffung (`export._collect`) wird wiederverwendet, nicht dupliziert.

## Abhängigkeiten

- **Benötigt:** PROJ-9 (Vorgangs-Persistenz) — der zu rendernde Vorgangszustand muss serverseitig vorliegen.
- **Benötigt:** PROJ-10 (Export-Renderer) — die Datenbeschaffung (`export._collect`) und die
  bestehenden Renderer werden als Basis genutzt/erweitert.
- **Benötigt:** PROJ-33 (Karten-Decomposition) bzw. der **karten-/state-basierte Vorgangszustand** aus
  Stufe 4 — der Report muss den aktuellen Datenvertrag lesen (siehe Edge Case „Architektur-Drift").
- **Wünschenswert:** PROJ-25 (Vertrauens-Indikator), PROJ-24 (Mehrsprachigkeit de/en) — für
  konsistente Quelle/Konfidenz-Ausweisung und Sprachwahl im Report.

## User Stories

- Als Nutzerin, die ihr Gerät an einer **Annahmestelle** abgibt, möchte ich einen kompakten
  Übergabe-Report als **PDF herunterladen**, damit die Helfer sofort Gerät, Symptom, bereits
  getestete Schritte und die Einschätzung sehen — ohne dass ich alles mündlich erklären muss.
- Als Nutzer möchte ich beim Download zwischen **mehreren Report-Varianten / Zielgruppen** wählen
  (z. B. *Kurz-Übergabe* fürs Repair Café, *ausführliches Protokoll* für die Fachwerkstatt,
  *Eigen-Beleg* für mich), damit das Dokument zum jeweiligen Empfänger passt.
- Als Nutzerin ohne Drucker oder PDF-Viewer möchte ich denselben Report alternativ als
  **Klartext/Markdown** herunterladen oder kopieren, damit ich ihn auch ohne PDF weitergeben kann.
- Als **Annahmestellen-Helfer**, der den ausgedruckten Report bekommt, möchte ich **Eigentum/
  Kostenträger** sowie **Sicherheits- und Datenhinweise** (Fremdgerät, datentragend) klar
  hervorgehoben sehen, damit ich Fremd- und datentragende Geräte korrekt behandle.
- Als Nutzer, dessen Vorgang noch **unvollständig** ist (keine Diagnose/Ampel), möchte ich
  trotzdem einen Report herunterladen können, der klar als *„in Bearbeitung"* gekennzeichnet ist,
  damit der Empfänger den Stand richtig einordnet.

## Akzeptanzkriterien

- [x] Aus dem Protokoll-/Service-Point-Bereich lässt sich der aktuelle Vorgang als **PDF-Datei
      herunterladen** (echter `Content-Disposition: attachment`-Download vom Server, kein reiner
      Browser-Druck).
- [x] Es stehen **mindestens zwei Zielgruppen-Varianten** zur Auswahl (umgesetzt: *Kurz-Übergabe
      Annahmestelle*, *Vollprotokoll Werkstatt*, *Eigen-Beleg* — 3 Varianten); die gewählte Variante
      bestimmt Umfang/Layout des Reports.
- [x] Die **PDF-Dateinamen** sind sprechend und enthalten Vorgang-ID und Variante
      (z. B. `reparatur-uebergabe_<vorgang-id>.pdf`, `reparatur-werkstattprotokoll_<vorgang-id>.pdf`).
- [x] Derselbe Report ist zusätzlich als **Klartext/Markdown** herunterladbar (eigener Download
      bzw. kopierbarer Text), inhaltlich konsistent zur PDF-Variante.
- [x] Die **Kurz-Übergabe-Variante** enthält mindestens: Gerät + Symptom, Warn-Ampel je Achse
      (Sicherheit/Aufwand/Kosten/Machbarkeit) mit Level, bereits getestete/durchgeführte Schritte,
      Empfehlung sowie Quelle/Konfidenz (Vertrauens-Indikator, inkl. „KI-Fallback"-Kennzeichnung).
- [x] **Eigentum/Kostenträger** (D14) wird in jeder Variante ausgewiesen; ist das Gerät als
      **fremd** oder **datentragend / zur Fremdabgabe** markiert, wird ein entsprechender
      **Hinweis hervorgehoben** im Report dargestellt.
- [x] Ein **unvollständiger** Vorgang (fehlende Diagnose/Ampel) ist exportierbar und wird im Report
      sichtbar als *„in Bearbeitung / unvollständig"* gekennzeichnet, statt den Download zu verweigern.
- [x] Schlägt die **PDF-Erzeugung** fehl (z. B. Renderer/Tool nicht verfügbar), erhält der Nutzer
      eine **klare Meldung** und mindestens einen funktionierenden Ersatzweg (Text/Markdown-Download
      bzw. Druck-Ansicht) — kein stiller Fehlschlag, kein Server-Crash (ehrliche Degradation, D3).
- [x] Bei unbekannter Vorgang-ID antwortet der Download-Endpunkt mit **404** und klarer Fehlermeldung.
- [x] Der Report-Inhalt liest den **aktuellen, karten-/state-basierten Vorgangszustand** (Stufe 4),
      nicht ein veraltetes Datenmodell — der Service-Point-Report bildet ab, was im Chat-Flow
      tatsächlich erarbeitet wurde.
- [x] Texte mit echten **Umlauten/Emojis** (kein ASCII-Escaping), konsistent zur SPEC-Konvention;
      bei mehrsprachigem Vorgang (de/en) folgt der Report der Vorgangssprache.

## Edge Cases

- **Architektur-Drift (wichtig):** Was passiert, weil `repair/export.py` heute noch das alte
  `device`-Monolith-Modell (Stufe 1–3) liest, der Vorgangszustand seit Stufe 4 (PROJ-33/37) aber
  **karten-basiert** ist? → Der Service-Point-Report muss die **aktuelle Quelle** abbilden; die
  Datenbeschaffung (`_collect`) ist entsprechend an den karten-/state-basierten Zustand
  anzupassen, sonst zeigt der Report „noch nicht ermittelt", obwohl im Chat-Flow Ergebnisse
  vorliegen. (Genaue Lösung → `/architecture`.)
- **Frage:** Was passiert, wenn keine PDF-Engine/kein Renderer verfügbar ist? **Antwort:** Der
  PDF-Download meldet sauber „PDF derzeit nicht verfügbar" und verweist auf den Text/Markdown-
  Download bzw. die Druck-Ansicht — der Vorgang bleibt exportierbar.
- **Frage:** Was passiert bei einer **unbekannten oder ungültigen Variante** im Download-Aufruf?
  **Antwort:** Es wird auf die Standard-Variante (*Kurz-Übergabe*) zurückgefallen, kein Fehler.
- **Frage:** Was passiert mit **Affiliate-/Provisions-Hinweisen** (Ersatzteil-Bestelloptionen) im
  Service-Point-Report? **Antwort:** Solche Hinweise sind im Übergabe-Report nicht
  handlungsleitend; falls dargestellt, bleibt die Provisions-/Affiliate-Kennzeichnung erhalten
  (keine versteckte Werbung), in der Kurz-Übergabe-Variante können sie entfallen.
- **Frage:** Was passiert bei einem **datentragenden Gerät zur Fremdabgabe** (D23/PROJ-20)?
  **Antwort:** Der Report hebt den Datenlösch-/Backup-Status sichtbar hervor, damit der Nutzer
  vor der Abgabe an der Theke erinnert wird.
- **Frage:** Was passiert bei einem Vorgang mit **mehreren Defekten** (PROJ-21)? **Antwort:** Der
  Report listet die Einzeldefekte und das Gesamt-Fazit; die Kurz-Übergabe-Variante zeigt mindestens
  den Knackpunkt und die Gesamtempfehlung.
- **Frage:** Enthält der Report **personenbezogene Daten** (Freitext, Eigentümername)? **Antwort:**
  Der Report bildet den fachlichen Vorgangszustand ab; die feingranulare Anonymisierungs-Steuerung
  (D10) ist — wie bei PROJ-10 — bewusst NICHT Teil dieses Features.

## Technische Anforderungen

- Stack-konform: **Flask-Backend + Vanilla-JS-Frontend** (kein Kotlin/Fritz2); neuer Download-
  Endpunkt analog zu den bestehenden Export-Routen (`/api/vorgang/<id>/…`).
- **Echtes server-seitiges PDF** erfordert eine Render-Engine. Die konkrete Wahl entscheidet
  `/architecture`; im Repo existieren bereits zwei Muster (pandoc + WeasyPrint im `pdf`-Skill,
  wkhtmltopdf im `issues-pdf-report`-Agent) — bevorzugt eine, die `webapp/`-eigene HTML→PDF-
  Erzeugung ohne externe Netzdienste erlaubt.
- Jede neue Engine/Limit wird **ausschließlich über `.env`** konfiguriert und in
  `webapp/.env.example` dokumentiert (kein Hardcode, Drift-Guard `test_config_drift.py`); jeder
  Wert braucht einen sinnvollen Default, damit die App ohne `.env` startet.
- Wiederverwendung statt Duplikat: gemeinsame Datenbeschaffung (`export._collect`) und – wo
  möglich – die HTML-/Text-Renderer aus `repair/export.py`; Varianten sind Sichten darauf.
- JSON/Text mit echten Umlauten/Emojis (`ensure_ascii=False`), konsistent zur bestehenden
  SPEC-Konvention.

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)

**Erstellt:** 2026-05-31 — Architektur-Entscheidungen für die Umsetzung (3-Agenten-Team).

### Architektur-Drift-Lösung (Kernproblem)

`repair/export.py` (PROJ-10) liest das **alte `device`-Monolith-Modell** (`state.device`,
`state.diagnosis`, `state.lights`, `state.ownership`, `state.answers` …), das der Chat-Flow
(Stufe 4, PROJ-37) **nicht mehr** befüllt. Der echte Vorgangszustand steckt heute in
`state["karten"]` — einer Liste validierter Karten `{typ, daten}` (Schemata in `repair/cards.py`).
PROJ-44 wird `export.py` **nicht** umbauen (PROJ-10/HTML-Lese-Ansicht bleibt unangetastet),
sondern eine **neue, karten-lesende Datenschicht** `repair/report.py` einführen. Quelle der
Wahrheit ist `state["karten"]` + `state["lang"]` + `state["medien"]` + Vorgang-Meta.

Karten→Report-Mapping (Karten-Typen aus `cards.py`):
- `aufnahme` → Gerät/Symptom (`symptom`, `kategorie`, `bedingungen`, `seit_wann`, `getestet`)
  + Eigentum/Kostenträger (`eigentum.ist_eigentuemer`, `eigentum.kostentraeger`).
- `diagnose` → Ursachen-Kandidaten (`kandidaten`), `unklar`-Flag, `trust`.
- `ampel` → Warn-Ampel je Achse (`achsen.{sicherheit,komplexitaet,kosten,machbarkeit}` mit
  Level `gruen|gelb|rot`), `gesamt`, `begruendung`, optional `defekt`, `trust`. **Mehrere
  ampel-Karten ⇒ Mehrfachdefekte** (PROJ-21): einzeln auflisten + Gesamt nach schwächstem Glied.
- `vergleich` → Empfehlung (`empfehlung` repair|pro|neu|entsorgung), `begruendung`, `trust`.
- `schritte` → durchgeführte/getestete Schritte (`schritte[].titel`, `safety`, `danger`, `handoff`).
- `hinweis` → **hervorgehoben**: `art ∈ {garantie,rueckruf,datenloeschung,sicherheit,eigentum}`,
  `text`, `schwere ∈ {info,warnung,kritisch}`. Fremd-/datentragend-Hinweise prominent.
- `anbieter`/`ersatzteil` → nur im Vollprotokoll; Affiliate-Kennzeichnung (`affiliate_hinweis`) bleibt.
- `erfolg` → optionaler Mehrwert-Abschnitt.
- Vertrauens-Indikator (D3/PROJ-25): `trust`-Objekt der jeweils maßgeblichen Karte
  (Konfidenz `unklar` ⇒ „KI-Fallback / nicht belegt"-Kennzeichnung).
- **Vollständigkeit:** unvollständig, wenn weder `ampel` noch `vergleich` noch `diagnose`
  vorliegt → Report-Kopf trägt sichtbar „in Bearbeitung / unvollständig" (Download trotzdem möglich).

### PDF-Engine-Entscheidung

**PyMuPDF (`fitz.Story`)** — bereits Dependency (`requirements.txt`, v1.27.2, `fitz.Story`
verifiziert vorhanden), **reines Wheel** (keine System-/Netz-Abhängigkeit, anders als WeasyPrint/
wkhtmltopdf/pandoc). Rendert HTML+CSS in-process → PDF-Bytes. Damit erfüllt sich die Spec-Vorgabe
„`webapp`-eigene HTML→PDF ohne externe Netzdienste". Gekapselt in `repair/pdf_engine.py`.
**Ehrliche Degradation (D3):** Fehlt das Modul / scheitert das Rendern / ist per `.env`
deaktiviert → klarer Fehler + Verweis auf Text-/Markdown-Download (kein Crash, kein stiller Fehler).

### Verbindlicher Schnittstellen-Vertrag (eingefroren — Agenten halten sich exakt daran)

**`repair/report.py`** (Agent A — neue Datei, liest Karten, kein OpenAI):
```python
VARIANTEN: dict[str, dict]   # key → {"label_de","label_en","dateiname"} ; Default-Key = "uebergabe"
DEFAULT_VARIANTE = "uebergabe"
# Mind. 2 (Spec): "uebergabe" (Kurz-Übergabe Annahmestelle, DEFAULT),
#                 "werkstatt" (Vollprotokoll), zusätzlich "eigenbeleg" (Eigen-Beleg) erwünscht.

def varianten() -> list[dict]: ...           # [{key,label,dateiname}] in Vorgangssprache (für UI/Endpoint)
def normalisiere_variante(v: str|None, lang="de") -> str:  # unbekannt/leer → DEFAULT_VARIANTE (kein Fehler)
def sammle_report(state: dict, meta: dict) -> dict: ...    # karten-basierter, normalisierter Report-Dict
def render_markdown(state: dict, meta: dict, variante: str, lang: str="de") -> str: ...
def render_text(state: dict, meta: dict, variante: str, lang: str="de") -> str: ...
def render_html(state: dict, meta: dict, variante: str, lang: str="de") -> str: ...   # vollständiges HTML-Dokument für die PDF-Engine
```
- `meta` = Store-Form `{id, created, updated}` (wie `store.get_vorgang()` liefert; `id` = Vorgang-ID).
- Sprache: `state.get("lang")` maßgeblich; Parameter `lang` ist Fallback. Echte Umlaute/Emojis,
  **kein** ASCII-Escaping (HTML escapt nur für die Sicherheit via `html.escape`).
- Darf nie hart scheitern (fehlende Felder → „noch nicht ermittelt"/weglassen).

**`repair/pdf_engine.py`** (Agent B — neue Datei):
```python
def verfuegbar() -> bool: ...                 # PyMuPDF importierbar UND per .env aktiviert
def html_zu_pdf(html: str) -> bytes: ...      # rendert via fitz.Story; wirft PdfNichtVerfuegbar bei Fehler/Deaktivierung
class PdfNichtVerfuegbar(RuntimeError): ...   # vom Endpoint in 503 + Verweis auf Text/MD übersetzt
```
- Config (Agent B, `repair/config.py` + `.env.example`): `REPORT_PDF_ENABLED` (Default „an",
  tolerant wie `flask_debug()`), Getter `report_pdf_enabled() -> bool`. **Kein Hardcode**,
  Drift-Guard `tests/test_config_drift.py` muss grün bleiben (lokal: `python tests/test_config_drift.py`).

**Routen (Agent C, `app.py`)** — analog zu `/api/vorgang/<id>/export.txt`:
- `GET /api/vorgang/<vid>/report.pdf?variante=<key>` → `application/pdf`,
  `Content-Disposition: attachment; filename="<dateiname>_<vid>.pdf"`. Unbekannte vid → **404**
  `{error,code:"no_vorgang"}`. Unbekannte/leere Variante → Default (kein Fehler). PDF-Fehler →
  **503** `{error,code:"pdf_unavailable"}` mit Hinweis auf `.md`/`.txt`.
- `GET /api/vorgang/<vid>/report.md?variante=<key>` → `text/markdown; charset=utf-8`, attachment.
- `GET /api/vorgang/<vid>/report.txt?variante=<key>` → `text/plain; charset=utf-8`, attachment.
- `GET /api/vorgang/<vid>/report/varianten` → `{varianten:[{key,label,dateiname}], default}` für die UI.

**Frontend (Agent C, `static/js/screens.js` + `app.js` + `static/css/repair.css`):**
- Report-Button im `ChatScreen`-AppBar-`right`-Slot (Dokument-Icon), sichtbar sobald ein Vorgang
  existiert. Öffnet ein Sheet/Overlay (Muster: `MediaConsentSheet`/`rk-sheet`) mit
  **Varianten-Auswahl** (Radio/Chips aus `/report/varianten`) + Download-Buttons **PDF / Markdown /
  Text** (echte `attachment`-Downloads via `<a download href=…>`/`window.location`) + „Kopieren".
  Bestehende `rk-*`-Klassen nutzen; neue CSS minimal additiv. Deutsch-only-Konvention beachten
  (i18n-Keys in beiden Sprachblöcken in `app.js` ergänzen, aktive Sprache bleibt `de`).
- PDF-Download-Fehler (503): freundlicher Hinweis-Toast + Markdown/Text als funktionierender Weg.

### Build-Reihenfolge & Eigentum (kein Datei-Konflikt)
- **Agent A** ⇒ `repair/report.py` + `tests/test_report.py` (eigenständig, Fundament).
- **Agent B** ⇒ `repair/pdf_engine.py` + `tests/test_pdf_engine.py` + `config.py`-Getter + `.env.example`.
- **Agent C** ⇒ Routen in `app.py` + Frontend (`screens.js`/`app.js`/`repair.css`) + `SPEC.md`/`README.md`-Doku.
- Schnittstellen oben sind **eingefroren**; A/B/C arbeiten parallel gegen diese Signaturen. Integration
  + End-to-End-Test (echte App, **nicht headless**, Karten-State via `PUT /api/vorgang/<id>` injiziert,
  kein OpenAI nötig) erfolgt durch den Lead nach Rückkehr der Agenten.

## QA Test Results

**Durchgeführt:** 2026-05-31 (Lead-Integration, 3-Agenten-Team).

**Unit-/Integrationstests:** `204 passed` (gesamte Suite), davon neu:
- `tests/test_report.py` — 93 Tests: Karten→Report-Extraktion, alle 3 Varianten × 3 Formate,
  Unvollständigkeit, Mehrfachdefekte, Fremd-/datentragend-Hervorhebung, echte Umlaute.
- `tests/test_pdf_engine.py` — 17 Tests: gültige PDF-Bytes (`%PDF`), Deaktivierung via ENV,
  `PdfNichtVerfuegbar`, `report_pdf_enabled()`-Parsing.
- Drift-Guard `tests/test_config_drift.py` — 9/9 (kein `.env`-Drift durch `REPORT_PDF_ENABLED`).

**Route-Integration (Flask-Test-Client, Karten-State injiziert, kein OpenAI):** `varianten` 200,
`report.{pdf,md,txt}` 200 für alle Varianten, unbekannte Variante → Default-Fallback (kein Fehler),
unbekannte Vorgang-ID → **404 `no_vorgang`**, `REPORT_PDF_ENABLED=0` → **503 `pdf_unavailable`**
mit Verweis auf Text/Markdown (MD weiter 200 — ehrliche Degradation). Inhalts-Stichprobe der
Kurz-Übergabe enthält Symptom, Ampel-Level (`rot`), Empfehlung (`pro`), Eigentum/Kostenträger
(`Vermieter`) und echte Umlaute (`Wäschetrockner`).

**End-to-End-Browser (nicht headless, Playwright, lokaler Server):** Report-Button (📄) in der
ChatScreen-AppBar → Sheet mit 3 Varianten-Chips + Buttons PDF/Markdown/Text/Kopieren öffnet sich;
Varianten-Auswahl schaltet um; PDF-Download liefert gültiges 1-seitiges PDF
(`reparatur-werkstattprotokoll_<vid>.pdf`, korrekter varianten-spezifischer Dateiname inkl.
Vorgang-ID) mit korrektem Inhalt inkl. „in Bearbeitung"-Markierung für unvollständige Vorgänge.

**Während QA gefundene & behobene Bugs:**
1. Frontend-Blob-Download nutzte einen generischen Dateinamen (`reparatur-report_<vid>.<ext>`) ohne
   Varianten-Bezug → verletzte AK „Dateiname enthält Variante". Fix: Helfer `reportDateiname()`
   leitet `<variante.dateiname>_<vid>.<ext>` aus `/report/varianten` ab (`app.js`).
2. Varianten-Chip nutzte `onChange` am Radio-Input, das der `h()`-Helper nicht unterstützt
   (nur `onClick/onInput/onKeydown`) → Auswahl wirkungslos. Fix: Handler an `onClick` des Labels
   (`screens.js`).

## Deployment
_Wird von /deploy hinzugefügt_ — **Hinweis:** kein Merge durchgeführt (auf Wunsch). Stand: implementiert
& verifiziert auf Branch `worktree-features-chatgpt`; Status „In Review".
