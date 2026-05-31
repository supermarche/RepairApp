# PROJ-40: Orchestrator-Robustheit bei API-Fehlern im Turn

## Status: Done

**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Abhängigkeiten

- PROJ-35 (LLM-Orchestrator-Schleife) — schließt eine dort offene AC-Lücke
- PROJ-9 (Vorgangs-Persistenz) — State darf bei Turn-Fehlern nicht korrumpieren
- PROJ-28 / PROJ-29 (Protokoll & Logging) — definierte Fehlerklasse statt generischer 500

## Beschreibung

**Bug.** `run_turn` umschließt den OpenAI-Call (`orchestrator.py:121`) nicht mit
Fehlerbehandlung. Tritt während eines Turns ein API-Fehler auf (BadRequest wie ein vom
Modell nicht unterstützter Parameter, Rate-Limit, Timeout, Netzwerkfehler), wird die
Exception ungefangen weitergereicht. `app.py` protokolliert sie über
`got_request_exception` als „Unbehandelte Exception" und liefert HTTP **500** — statt des in
PROJ-35 vorgesehenen `ai_error` (502). Zusätzlich gehen **bereits gesammelte Karten**
(`neue_karten`) verloren, und der mutierte State wird **nicht persistiert**, weil
`app.py:366` (`store.save_vorgang`) nach dem Throw nie erreicht wird. Damit ist das
PROJ-35-Akzeptanzkriterium „Netzwerk-/API-Fehler mitten im Turn → definierter Fehler
(`ai_error`), kein Absturz; bereits gesammelte Karten gehen nicht verloren" **nicht erfüllt**.

**Belege:** `webapp/logs/repair.log` — `2026-05-31 14:33:23` und `14:34:14`:
`openai.BadRequestError: Error code: 400 … 'temperature' does not support 0.4 …` gefolgt von
„ERROR repair.app: Unbehandelte Exception bei POST /api/chat" (voller Traceback). Der
konkrete Temperature-Auslöser ist mit Commit `c987fa6` bereits behoben; die zugrunde
liegende **fehlende Fehlerkapselung** besteht weiter und betrifft jede künftige API-Fehlerart.

## User Stories

- Als Nutzer möchte ich bei einem KI-/Netzwerkfehler eine verständliche Fehlermeldung statt eines Absturzes, damit ich es erneut versuchen oder anders weitermachen kann.
- Als Nutzer möchte ich, dass bereits in diesem Turn erzeugte Karten nicht verloren gehen, wenn später im selben Turn ein Fehler auftritt.
- Als Betreiber möchte ich, dass API-Fehler als definierter `ai_error` (502) zurückkommen und mit Fehlerklasse protokolliert werden, nicht als generische 500, damit Monitoring und Fehlerbilder sauber sind.
- Als Betreiber möchte ich, dass ein Turn-Fehler den persistierten Vorgangs-Zustand nicht korrumpiert, damit der nächste Turn konsistent fortsetzt.

## Akzeptanzkriterien

- [ ] Ein während `run_turn` auftretender OpenAI-/Netzwerkfehler wird gefangen und führt zu `{error, code:"ai_error"}` (HTTP 502), keiner unbehandelten Exception.
- [ ] Vor dem Fehler im selben Turn erzeugte Karten gehen nicht verloren — sie sind im Ergebnis enthalten oder im persistierten Vorgang verfügbar.
- [ ] Der Vorgangs-Zustand bleibt nach einem Turn-Fehler konsistent (kein halb geschriebener `messages`-Verlauf, der den nächsten Turn bricht).
- [ ] Der Fehler wird mit Fehlerklasse/-ursache protokolliert (PROJ-28/29), ohne zusätzliche Klartext-PII über das übliche Maß hinaus.
- [ ] Das PROJ-35-AC „Netzwerk-/API-Fehler mitten im Turn → definierter Fehler, kein Absturz" ist nachweislich erfüllt.
- [ ] Ein automatischer Test simuliert einen werfenden `create()`-Aufruf und prüft: Rückgabe `ai_error`, kein Throw, Karten-/State-Verhalten wie spezifiziert.

## Edge Cases

- Fehler in der ersten Iteration (noch keine Karten) → sauberer `ai_error`, leere Karten.
- Fehler nach mehreren Tool-Calls (Karten vorhanden) → Karten bleiben erhalten.
- Timeout (`config.llm_timeout()`) → wird wie ein API-Fehler behandelt, kein Absturz.
- Modell akzeptiert einen gesendeten Parameter nicht (BadRequest, wie temperature) → `ai_error` + aussagekräftiges Log statt 500.
- Wiederholter Fehler über mehrere Turns → idempotentes Verhalten, kein wachsender korrupter State.

## Technische Anforderungen (optional)

- Betroffen: `webapp/repair/orchestrator.py:119-163` (Fehlerkapselung um Schleife/`create()`), `webapp/app.py:365-369` (der `ai_error`-Pfad existiert, wird bei einem Throw aber nicht erreicht).
- Offene Design-Entscheidung für /architecture: Karten-/State-Erhalt — `run_turn` gibt Teilergebnis + `code` zurück **oder** `app.py` persistiert den State in einem `finally`. Dieses Requirement legt nur das **Verhalten** fest, nicht die Implementierung.
- Keine zwingende neue `.env`-Konfiguration.
- Bezug: PROJ-35 (AC-Lücke), PROJ-9, PROJ-28/29.

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)
_Wird von /architecture hinzugefügt_

## QA Test Results
_Wird von /qa hinzugefügt_

## Deployment
_Wird von /deploy hinzugefügt_
