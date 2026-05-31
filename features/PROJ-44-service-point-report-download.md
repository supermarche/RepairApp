# PROJ-44: Service-Point-Übergabe-Report (PDF- & Text-Download, mehrere Zielgruppen-Varianten)

## Status: Planned

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

- [ ] Aus dem Protokoll-/Service-Point-Bereich lässt sich der aktuelle Vorgang als **PDF-Datei
      herunterladen** (echter `Content-Disposition: attachment`-Download vom Server, kein reiner
      Browser-Druck).
- [ ] Es stehen **mindestens zwei Zielgruppen-Varianten** zur Auswahl (z. B. *Kurz-Übergabe
      Annahmestelle* und *Vollprotokoll Werkstatt*); die gewählte Variante bestimmt Umfang/Layout
      des Reports.
- [ ] Die **PDF-Dateinamen** sind sprechend und enthalten Vorgang-ID und Variante
      (z. B. `reparatur-uebergabe_<vorgang-id>.pdf`).
- [ ] Derselbe Report ist zusätzlich als **Klartext/Markdown** herunterladbar (eigener Download
      bzw. kopierbarer Text), inhaltlich konsistent zur PDF-Variante.
- [ ] Die **Kurz-Übergabe-Variante** enthält mindestens: Gerät + Symptom, Warn-Ampel je Achse
      (Sicherheit/Aufwand/Kosten/Machbarkeit) mit Level, bereits getestete/durchgeführte Schritte,
      Empfehlung sowie Quelle/Konfidenz (Vertrauens-Indikator, inkl. „KI-Fallback"-Kennzeichnung).
- [ ] **Eigentum/Kostenträger** (D14) wird in jeder Variante ausgewiesen; ist das Gerät als
      **fremd** oder **datentragend / zur Fremdabgabe** markiert, wird ein entsprechender
      **Hinweis hervorgehoben** im Report dargestellt.
- [ ] Ein **unvollständiger** Vorgang (fehlende Diagnose/Ampel) ist exportierbar und wird im Report
      sichtbar als *„in Bearbeitung / unvollständig"* gekennzeichnet, statt den Download zu verweigern.
- [ ] Schlägt die **PDF-Erzeugung** fehl (z. B. Renderer/Tool nicht verfügbar), erhält der Nutzer
      eine **klare Meldung** und mindestens einen funktionierenden Ersatzweg (Text/Markdown-Download
      bzw. Druck-Ansicht) — kein stiller Fehlschlag, kein Server-Crash (ehrliche Degradation, D3).
- [ ] Bei unbekannter Vorgang-ID antwortet der Download-Endpunkt mit **404** und klarer Fehlermeldung.
- [ ] Der Report-Inhalt liest den **aktuellen, karten-/state-basierten Vorgangszustand** (Stufe 4),
      nicht ein veraltetes Datenmodell — der Service-Point-Report bildet ab, was im Chat-Flow
      tatsächlich erarbeitet wurde.
- [ ] Texte mit echten **Umlauten/Emojis** (kein ASCII-Escaping), konsistent zur SPEC-Konvention;
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
_Wird von /architecture hinzugefügt_

## QA Test Results
_Wird von /qa hinzugefügt_

## Deployment
_Wird von /deploy hinzugefügt_
