# PROJ-47: Spracheingabe im Chat (Diktat per OpenAI-Whisper)

## Status: Planned
**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Abhängigkeiten
- Benötigt: PROJ-37 (Chat-Flow: API & Frontend) — die Eingabezeile des `ChatScreen` ist der Ort des Mikrofon-Buttons.
- Baut auf: PROJ-27 (Multimodale Eingabe) — liefert den server-seitigen Transkriptions-Endpunkt `POST /api/transkription` und `multimodal.transkribiere()`, die hier erstmals vom Frontend angebunden werden.
- Bezug: PROJ-30 (`.env`-Konfiguration) — `WHISPER_MODEL` (Default `whisper-1`) ist bereits vorhanden.
- Bezug: PROJ-22 (Consent-Gate) / D10 — vor erster Mikrofon-Nutzung greift die bestehende Medien-Einwilligung.

## Kontext / Abgrenzung
Spracheingabe existiert bislang **nur** in der Legacy-Media-Capture-Komponente über die
Browser-`webkitSpeechRecognition`-API und ist im **aktiven** `ChatScreen` (PROJ-37) **nicht**
verfügbar. Der server-seitige Whisper-Endpunkt `POST /api/transkription` existiert, wird aber
vom Frontend **nicht aufgerufen**. Dieses Feature schließt die Lücke: Spracheingabe direkt in
der laufenden Chat-Eingabezeile, transkribiert über die **OpenAI-API (Whisper)** — denselben
Cloud-Dienst, den die App ohnehin nutzt. Damit funktioniert die Spracheingabe browserübergreifend
(auch Firefox), nicht nur in Chrome/Edge.

## User Stories
- Als Nutzer mit schmutzigen oder belegten Händen während der Reparatur möchte ich meine Chat-Nachricht **per Sprache diktieren**, statt zu tippen, damit ich den Vorgang nicht unterbrechen muss.
- Als Nutzer möchte ich in **jedem** Chat-Turn das Mikrofon nutzen können (nicht nur bei der ersten Schilderung), damit ich auch Rückfragen des Assistenten mündlich beantworten kann.
- Als Nutzer möchte ich den erkannten Text **vor dem Senden im Eingabefeld sehen und korrigieren** können, damit eine Fehlerkennung (z. B. Dialekt) nicht ungeprüft abgeschickt wird.
- Als Nutzer möchte ich nach einer abgeschlossenen Aufnahme die **Aufnahme wiederholen** oder **weitere Informationen ergänzen** (anhängen) können, damit ich meine Eingabe vervollständigen kann, ohne von vorne zu beginnen.
- Als Nutzer mit einem Browser ohne Mikrofon-Zugriff möchte ich, dass die Spracheingabe **sauber als nicht verfügbar** dargestellt wird und die Texteingabe uneingeschränkt weiterläuft, damit mich das nicht blockiert.

## Akzeptanzkriterien
- [ ] In der Eingabezeile des `ChatScreen` gibt es einen **Mikrofon-Button** (neben 📎-Anhang und Senden), der in **jedem** Chat-Turn verfügbar ist, solange keine Anfrage läuft.
- [ ] Ein Klick startet die Audioaufnahme im Browser; ein **sichtbarer Live-Indikator** („Ich höre zu …") zeigt die laufende Aufnahme an, ein erneuter Klick (bzw. Stopp) beendet sie.
- [ ] Das aufgenommene Audio wird an `POST /api/transkription` gesendet und über die **OpenAI-API (Whisper, `WHISPER_MODEL`, Default `whisper-1`)** zu Text transkribiert.
- [ ] Der erkannte Text wird **in das Chat-Eingabefeld eingefügt** und ist dort **manuell editierbar**; das Absenden erfolgt erst durch den Nutzer (kein Auto-Senden).
- [ ] Nach Abschluss einer Aufnahme kann der Nutzer die **Aufnahme wiederholen** (ersetzt den per Sprache erfassten Text) **oder ergänzen** (eine weitere Aufnahme hängt ihren Text an den vorhandenen Feldinhalt an, statt ihn zu überschreiben).
- [ ] Während der Aufnahme bzw. der laufenden Transkription ist der Senden-Button gesperrt/als „beschäftigt" erkennbar; nach Erhalt des Transkripts ist die Eingabe wieder frei.
- [ ] Vor der **ersten** Mikrofon-Nutzung wird die bestehende Medien-Einwilligung (PROJ-22/D10) eingeholt; ohne Einwilligung bleibt das Mikrofon gesperrt, Texteingabe bleibt offen.
- [ ] Auf Geräten/Browsern ohne Mikrofon-Zugriff wird der Button **als nicht verfügbar** dargestellt; die Text- und 📎-Eingabe bleiben vollständig nutzbar.
- [ ] Die Sprach-UI respektiert die aktive App-Sprache (de/en, vgl. PROJ-24): Indikator- und Hinweistexte sind lokalisiert, und die gewählte Sprache wird (sofern unterstützt) an die Transkription weitergereicht.

## Edge Cases
- **Nutzer verweigert den Mikrofon-Zugriff (Browser-Permission) oder bricht die Aufnahme ab?** Es wird ein verständlicher Hinweis gezeigt, kein Text eingefügt, und die Texteingabe läuft unverändert weiter — keine Sackgasse.
- **Audio enthält keine erkennbare Sprache / Transkript ist leer?** Verständlicher Hinweis („nichts erkannt"); das Eingabefeld bleibt unverändert, der Nutzer kann erneut aufnehmen oder tippen.
- **Whisper/OpenAI nicht verfügbar (kein API-Key → `no_backend`, Timeout, `ai_error`)?** Die App meldet die Nicht-Verfügbarkeit klar (analog zur bestehenden `no_backend`-Behandlung) und fällt sauber auf manuelle Texteingabe zurück, ohne Datenverlust am bereits getippten Feldinhalt.
- **Nutzer hat bereits Text getippt und nimmt dann auf?** Die „Ergänzen"-Aktion hängt das Transkript an den vorhandenen Text an; „Wiederholen" ersetzt nur den zuletzt per Sprache erfassten Anteil, nicht den manuell getippten Vorlauf (klare, nicht-überraschende Trennung).
- **Aufnahme zu lang / Datei zu groß?** Es greift das bestehende Upload-Limit (`MAX_UPLOAD_BYTES`); bei Überschreitung erscheint ein verständlicher Hinweis statt eines Server-Fehlers.
- **Dialekt / starke Hintergrundgeräusche → unsicheres Transkript?** Da der Text editierbar im Feld landet und vor dem Senden geprüft werden kann, ist die Korrektur Teil des normalen Flows (kein Auto-Senden).
- **Browser ohne `MediaRecorder`/`getUserMedia`?** Mikrofon-Button erscheint als nicht verfügbar; Text/📎 bleiben nutzbar.

## Technische Anforderungen
- Stack-Rahmen: Flask + Vanilla-JS gemäß `webapp/SPEC.md`; Frontend-Erweiterung im `ChatScreen` (`static/js/screens.js`) und der Chat-Steuerung (`static/js/app.js`).
- Audioaufnahme browserseitig über `MediaRecorder`/`getUserMedia` (kein zusätzliches NPM-Paket), Upload des Audio-Blobs an den **bestehenden** `POST /api/transkription` (multipart `file`/`audio` oder Rohdaten — Endpunkt akzeptiert beides).
- Keine neue server-seitige Konfiguration nötig: `WHISPER_MODEL` (Default `whisper-1`) und das OpenAI-Backend sind bereits vorhanden. Falls neue `.env`-Werte entstehen (z. B. Audio-spezifisches Limit), gemäß PROJ-30 in `repair/config.py` + `.env.example` dokumentieren (kein Hardcode, kein Drift).
- Transkriptions-Verhalten ohne API-Key: Endpunkt liefert bereits einen sauberen Hinweis statt Crash; das Frontend muss diesen Fall (`source != "whisper"` bzw. Fehler) als „Spracheingabe gerade nicht verfügbar" darstellen.
- Lokalisierte UI-Texte (de/en) in den bestehenden i18n-Tabellen (`app.js`); die App-Sprache wird, wo möglich, an die Transkription übergeben.
- Datenschutz-/Consent-Detailumsetzung ist eigenes Projekt (D10) und wird hier nur über das bestehende Consent-Gate referenziert, nicht neu ausgestaltet.

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)
_Wird von /architecture hinzugefügt_

## QA Test Results
_Wird von /qa hinzugefügt_

## Deployment
_Wird von /deploy hinzugefügt_
