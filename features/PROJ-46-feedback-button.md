``# PROJ-46: Feedback-Button (Prozess-Anmerkungen des Nutzers)

## Status: In Review
**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Kurzbeschreibung
Ein jederzeit erreichbarer Feedback-Button in der Web-App, über den der Anwender während
eines laufenden Reparaturvorgangs einen Freitext-Hinweis zum aktuellen Prozess abgeben kann
(z. B. „die letzte Frage war unverständlich", „diese Diagnose passt nicht", „super hilfreich").
Das Feedback wird **lokal beim Betreiber** gespeichert und mit dem Kontext des Vorgangs
verknüpft — es findet **kein externer Versand** statt.

## Abhängigkeiten
- Benötigt: **PROJ-9** (Serverseitige Vorgangs-Persistenz) — Feedback ist immer an eine `vorgang_id` gebunden.
- Benötigt: **PROJ-28** (Anfrage-Protokoll als Markdown) — ein Feedback-Hinweis wird zusätzlich in das Vorgangs-Protokoll geschrieben.
- Bezug: **PROJ-30** (Konfiguration über `.env`) — neue Schalter/Limits ausschließlich über `.env`.
- Bezug: **PROJ-29** (zentrales Logging) — Feedback-Eingang wird über `logging.getLogger(__name__)` protokolliert.

## User Stories
- Als **Anwender** möchte ich während eines Reparaturvorgangs jederzeit einen Feedback-Button
  sehen und antippen können, damit ich spontan eine Anmerkung loswerden kann, ohne den Prozess zu verlieren.
- Als **Anwender** möchte ich in ein Textfeld frei schreiben können, was mich am aktuellen
  Schritt stört oder begeistert, damit mein konkretes Anliegen erfasst wird.
- Als **Anwender** möchte ich nach dem Absenden eine kurze Bestätigung sehen, damit ich weiß,
  dass meine Anmerkung angekommen ist.
- Als **Anwender** möchte ich den Feedback-Dialog jederzeit ohne Absenden schließen können,
  damit ich nicht zum Abschicken gezwungen werde.
- Als **Betreiber** möchte ich jedes Feedback mit Zeitstempel, Vorgangs-ID, aktuellem
  Schritt/Screen und der zuletzt gezeigten KI-Antwort gespeichert bekommen, damit ich es im
  Kontext auswerten und die App verbessern kann.
- Als **Betreiber** möchte ich im Vorgangs-Protokoll einen Hinweis sehen, dass zu diesem
  Vorgang Feedback abgegeben wurde, damit der Bezug zum Reparaturfall erhalten bleibt.

## Akzeptanzkriterien

### UI / Frontend
- [ ] Bei laufendem Vorgang (vorhandene `vorgang_id`) ist ein Feedback-Button durchgängig sichtbar/erreichbar.
- [ ] Ohne laufenden Vorgang ist der Button **nicht** auslösbar (ausgeblendet oder deaktiviert) — Feedback ist immer vorgangsgebunden.
- [ ] Ein Klick öffnet einen Dialog/Bereich mit einem mehrzeiligen Freitextfeld und den Aktionen „Senden" und „Abbrechen/Schließen".
- [ ] Der Dialog folgt dem bestehenden Theme/Klassennamen-Vertrag (`SPEC.md`) und dem aktiven Theme (Default Werkstatt).
- [ ] Nach erfolgreichem Senden erscheint eine kurze Dank-/Bestätigungsmeldung; der Dialog schließt sich (bzw. zeigt klar den Erfolg).
- [ ] „Abbrechen/Schließen" verwirft die Eingabe und schließt den Dialog ohne Server-Aufruf.

### Backend / API
- [ ] Neuer Endpunkt **`POST /api/feedback`** mit `{vorgang_id, text}` (Frontend ergänzt verfügbaren Kontext, s. u.).
- [ ] Erfolgsantwort **HTTP 200** `{ok: true}` (bzw. `{feedback_id}`); JSON immer mit `ensure_ascii=False`.
- [ ] Fehlerfälle als `{error, code}`: `400 empty` (leerer/whitespace-Text), `404 no_vorgang` (unbekannte `vorgang_id`), `400 too_long` (Text über Limit).
- [ ] Automatisch erfasster Kontext je Eintrag: **Zeitstempel**, **Vorgangs-ID**, **aktueller Schritt/Screen** (Statemachine-Zustand), **zuletzt gezeigte KI-Antwort/Karte**.
- [ ] Speicherung erfolgt **zweifach**: (a) in eigener Persistenz (eigene Tabelle/Datei, zentral auswertbar) **und** (b) als Hinweis-Eintrag im Vorgangs-Protokoll (PROJ-28).
- [ ] Es erfolgt **kein externer Versand** des Feedbacks (keine Cloud, kein Mail-Versand) — reine lokale Speicherung beim Betreiber.
- [ ] Eingang wird über `logging.getLogger(__name__)` geloggt (ohne PII auf INFO-Level).

### Konfiguration (`.env`)
- [ ] Funktion über `.env` schaltbar (z. B. `FEEDBACK_ENABLED`, Default `true`) und in `.env.example` dokumentiert.
- [ ] Maximale Textlänge über `.env` konfigurierbar (z. B. `MAX_FEEDBACK_BYTES`) mit sinnvollem Default; in `.env.example` dokumentiert.
- [ ] Drift-Guard (`tests/test_config_drift.py`) bleibt grün — keine Hardcode-Defaults außerhalb `config.py`.

## Edge Cases
- **Leeres / nur-Whitespace-Feedback:** wird abgelehnt (`400 empty`); UI verhindert das Senden bzw. zeigt einen Hinweis.
- **Sehr langer Text:** über dem Limit → `400 too_long`; UI begrenzt/warnt vor dem Senden.
- **Kein aktiver Vorgang:** Button nicht auslösbar; ein dennoch abgesetzter Request ohne gültige `vorgang_id` → `404 no_vorgang`.
- **Unbekannte/abgelaufene `vorgang_id`:** `404 no_vorgang`, kein Crash, kein verwaister Eintrag.
- **Mehrfaches Feedback im selben Vorgang:** alle Einträge werden gespeichert (Append, kein Überschreiben), je mit eigenem Zeitstempel.
- **Doppelklick / mehrfaches Senden desselben Texts:** UI verhindert Doppel-Submit (Button während Request deaktiviert); Server bleibt idempotenz-tolerant (mehrfaches Speichern schadet nicht, führt aber nicht zum Fehler).
- **Sonderzeichen / Emojis / Umlaute:** werden korrekt gespeichert (`ensure_ascii=False`), kein ASCII-Escaping.
- **Noch keine KI-Antwort vorhanden** (Feedback direkt nach Vorgangsanlage): Kontextfeld „letzte KI-Antwort" bleibt leer, Speicherung gelingt trotzdem.
- **Feedback-Funktion deaktiviert (`FEEDBACK_ENABLED=false`):** Button erscheint nicht; Endpunkt antwortet sauber ablehnend (kein Crash).
- **PII im Freitext:** wird wie Nutzereingaben behandelt — lokal gespeichert, nicht extern versendet; Logging des Inhalts nur auf DEBUG (Dev), nicht auf INFO.

## Technische Anforderungen (optional)
- Antwortzeit `POST /api/feedback`: < 200 ms (reine lokale Speicherung, kein LLM-Aufruf).
- Sicherheit/Datenschutz: ausschließlich lokale Persistenz beim Betreiber, kein externer Versand; Inhalt ist PII-tragend und entsprechend zu behandeln.
- Konsistenz mit bestehender Architektur: Endpunkt in `app.py`, Persistenz analog `store.py`/`protokoll_log.py`, Karten-/Klassennamen-Vertrag aus `SPEC.md`.

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)
_Wird von /architecture hinzugefügt_

## QA Test Results
**Stand 2026-05-31 — Gesamturteil: FREIGABE** (3-Agenten-Team: Backend / Frontend / QA).

**Umgesetzt:**
- Backend: Endpunkt `POST /api/feedback` (`app.py`), neue lokale Persistenz `repair/feedback.py`
  (SQLite `feedback.db`, append-only, gitignored), `.env`-Schalter `FEEDBACK_ENABLED` (Default an)
  + `MAX_FEEDBACK_BYTES` (Default 4000, Fail-fast-validiert) zentral in `repair/config.py`.
  Zweitablage im Vorgangs-Protokoll über `ENDPOINT_ROLLE["api_feedback"]="feedback"` (PROJ-28).
- Frontend: 💬-Feedback-Button in der ChatScreen-AppBar (nur bei vorhandenem Vorgang),
  Feedback-Sheet (`FeedbackSheet` in `screens.js`, Muster ReportSheet), State/Handler in `app.js`,
  i18n de+en, CSS `rk-feedback-*` (in `SPEC.md` dokumentiert).

**Verifikation (echte Ergebnisse):**
- `pytest tests/` → **237 passed** (inkl. `tests/test_feedback.py`); `tests/test_config_drift.py` 9/9 grün.
- HTTP/curl: 200 `{ok, feedback_id}` (Umlaut/Emoji unescaped); 400 `empty`; 400 `too_long`;
  404 `no_vorgang`; 403 `disabled` (bei `FEEDBACK_ENABLED=0`, kein Crash). Zweifach-Speicherung
  (feedback.db + protokolle/<vid>.md mit Rolle `feedback`) und Mehrfach-Feedback (Append) bestätigt.
- Browser (nicht-headless, Playwright): Button sichtbar, Sheet öffnet, Senden bei leer/Whitespace
  gesperrt, Senden→200+Dank+Auto-Close, Abbrechen ohne Request, Doppel-Submit→1 Request,
  Emoji/Sonderzeichen korrekt, Theme-konsistent.
- Security: kein externer Versand; Feedback-Text nicht auf INFO geloggt (nur id/vid/Länge);
  `feedback.db` gitignored; robuste 4xx statt 500 bei Fehleingaben.

**Im QA behobene Bugs:** (1) 500-Crash bei Nicht-Objekt-JSON-Body → jetzt 400 (`app.py`);
(2) Senden-Button wurde beim Tippen nicht aktiviert (disabled-Zustand nur beim Render) →
Live-Umschaltung im input-Handler ohne Re-Render (`screens.js`).

## Deployment
_Wird von /deploy hinzugefügt_
