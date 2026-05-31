# PROJ-43: Beobachtbarkeit der Orchestrierung (Rollenwechsel & Tool-Calls)

## Status: Planned

**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Abhängigkeiten

- PROJ-35 (LLM-Orchestrator-Schleife) — die Tool-Call-Schleife, deren Verlauf sichtbar werden soll
- PROJ-32 (Rollen-Registry & Progressive Disclosure) — `lade_rolle`-Wechsel sind das Hauptereignis
- PROJ-28 (Anfrage-Protokoll) / PROJ-29 (Zentrales Logging) — die beiden Beobachtungskanäle
- PROJ-34 (Daten-Tools) — Tool-Aufrufe (`recherche`, `suche_ersatzteil`, `extrahiere_aus_medien` …)

## Beschreibung

**Verbesserung (Beobachtbarkeit).** Rollenwechsel und Tool-Aufrufe des Orchestrators sind
heute aus den Standard-Beobachtungskanälen **nicht** ersichtlich:

1. **`repair.log` schweigt zu Rollenwechseln.** `tools.dispatch()` loggt `lade_rolle` nicht
   (`tools.py:83-84`); nur das `recherche`-Tool schreibt eigene Log-Zeilen. Wer im Log nach
   `lade_rolle` sucht, findet **nichts** — Rollenwechsel sind nur über die DB
   (`vorgaenge.db` → `state["geladene_rollen"]` / `entscheidungsprotokoll`) rekonstruierbar.
2. **Das Anfrage-Protokoll ist sogar irreführend.** Der Eintrag-Header „Rolle `lotse`"
   stammt aus `protokoll_log.rolle_fuer(endpoint)` (`protokoll_log.py:86`, Endpunkt→Rolle-
   Mapping). Da jeder Chat-Turn auf `/api/chat` läuft, steht dort **immer** `lotse` —
   unabhängig davon, welche Fachrolle die KI tatsächlich geladen hat.

**Beleg (Lauf 2026-05-31, Vorgang `vsE9FuKIKrF44aDH`):** Die DB zeigt
`geladene_rollen = ['aufnahme', 'diagnose', 'bewertung', 'recherche']` und ein
`entscheidungsprotokoll` mit `lade_rolle`/`recherche`/`suche_ersatzteil`/`zeige_karte`-
Aufrufen. Im Protokoll-Markdown (`vsE9FuKIKrF44aDH.md`) tragen aber **alle** Einträge den
Header „Rolle `lotse`", und `repair.log` enthält **keinen** `lade_rolle`-Eintrag.

Ziel: Rollenwechsel und Tool-Aufrufe in beiden Kanälen ehrlich und auffindbar machen —
ohne den fachlichen Ablauf zu verändern.

## User Stories

- Als Betreiber möchte ich Rollenwechsel (`lade_rolle`) und Tool-Aufrufe im `repair.log` sehen, damit ich den Orchestrierungs-Verlauf nachvollziehen kann, ohne in die SQLite-DB schauen zu müssen.
- Als Betreiber möchte ich, dass das Anfrage-Protokoll je Turn die **tatsächlich** geladenen Rollen und ausgeführten Tools ausweist, statt pauschal „Rolle `lotse`", damit das Protokoll der Realität entspricht.
- Als Betreiber möchte ich pro Turn eine kompakte Aufruf-Sequenz (welche Rolle, welche Tools, in welcher Reihenfolge), damit ich Fehlerbilder und Diagnosequalität schnell beurteilen kann.
- Als Entwickler möchte ich aus Log und Protokoll erkennen können, ob im ersten Lauf gar keine Rolle geladen wurde (reiner Lotse-Kontext) vs. ob eine Fachrolle aktiv war, damit ich Regressionen in der Progressive Disclosure früh sehe.

## Akzeptanzkriterien

- [ ] `lade_rolle`-Aufrufe werden in `repair.log` protokolliert (Rollenname + Vorgang-ID, Level INFO), nicht nur in der DB.
- [ ] Tool-Aufrufe des Orchestrators werden in `repair.log` mit Tool-Namen festgehalten (mindestens auf DEBUG; keine sensiblen Klartext-Argumente über das übliche PII-Maß hinaus, vgl. PROJ-29).
- [ ] Das Anfrage-Protokoll (PROJ-28) weist je Turn die in diesem Turn tatsächlich **geladenen Rollen** und **ausgeführten Tools** aus — statt des pauschalen, vom Endpunkt abgeleiteten „Rolle `lotse`".
- [ ] Ist in einem Turn keine Fachrolle geladen worden, ist das im Protokoll als solches erkennbar (z. B. „nur Lotse-Kontext"), kein irreführender Fachrollen-Eintrag.
- [ ] Die Protokoll-Darstellung bleibt rückwärts lesbar (bestehende Abschnitte „KI-Entscheidung"/„Token-Statistik" bleiben erhalten); die Rollen-/Tool-Angabe ergänzt sie.
- [ ] Ein automatischer Test prüft: ein Turn mit `lade_rolle("diagnose")` + einem Daten-Tool erzeugt entsprechende Log-Einträge und die korrekte Rollen-/Tool-Ausweisung im Protokoll.
- [ ] Keine Änderung am fachlichen Chat-Ergebnis (`antwort_text`, `karten`, `abgebrochen`) durch die zusätzliche Beobachtbarkeit.

## Edge Cases

- Turn ohne Rollenwechsel (reiner Lotse-Kontext) → Log/Protokoll weisen „keine Rolle geladen" aus, nicht „lotse" als Fachrolle.
- Mehrere `lade_rolle` in einem Turn (z. B. `aufnahme`→`diagnose`) → alle in Reihenfolge sichtbar, nicht nur die letzte.
- Tool-Argumente mit Nutzer-PII (Freitext) → im Log gemäß PROJ-29-Leitlinie behandelt (Tool-Name ja, sensible Argumente nur bei Bedarf/auf DEBUG, nicht auf INFO).
- Tool-Aufruf schlägt fehl (`error` im Dispatch-Ergebnis) → wird als fehlgeschlagen erkennbar protokolliert, nicht stillschweigend ausgelassen.
- Sehr viele Tool-Aufrufe in einem Turn → Log-/Protokoll-Ausgabe bleibt kompakt (keine Volltexte der Rollen-Bodies oder Karten-Daten ins Log).

## Technische Anforderungen (optional)

- Betroffen: `webapp/repair/orchestrator.py` (Logging in der Tool-Schleife, `state["geladene_rollen"]`/`entscheidungsprotokoll` werden bereits geführt), `webapp/repair/tools.py` (`dispatch` für `lade_rolle`/Tools), `webapp/repair/protokoll_log.py` (Rollen-/Tool-Ausweisung je Turn statt `rolle_fuer(endpoint)`-Pauschale).
- Quelle der Wahrheit ist der bereits vorhandene Vorgangs-Zustand (`geladene_rollen`, `entscheidungsprotokoll`) — es müssen keine neuen Daten erhoben, nur sichtbar gemacht werden.
- PII-Leitlinie aus PROJ-29 beachten (DEBUG = lokal/Dev, produktiv mind. INFO).
- Keine zwingende neue `.env`-Konfiguration.
- Bezug: PROJ-35, PROJ-32, PROJ-28, PROJ-29, PROJ-34.

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)
_Wird von /architecture hinzugefügt_

## QA Test Results
_Wird von /qa hinzugefügt_

## Deployment
_Wird von /deploy hinzugefügt_
