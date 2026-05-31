# PROJ-47: Spracheingabe im Chat (Diktat per OpenAI-Whisper)

## Status: In Review
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
- [x] In der Eingabezeile des `ChatScreen` gibt es einen **Mikrofon-Button** (neben 📎-Anhang und Senden), der in **jedem** Chat-Turn verfügbar ist, solange keine Anfrage läuft.
- [x] Ein Klick startet die Audioaufnahme im Browser; ein **sichtbarer Live-Indikator** („🎙️ Ich höre zu …") zeigt die laufende Aufnahme an, ein erneuter Klick (bzw. Stopp) beendet sie.
- [x] Das aufgenommene Audio wird an `POST /api/transkription` gesendet und über die **OpenAI-API (Whisper, `WHISPER_MODEL`, Default `whisper-1`)** zu Text transkribiert.
- [x] Der erkannte Text wird **in das Chat-Eingabefeld eingefügt** und ist dort **manuell editierbar**; das Absenden erfolgt erst durch den Nutzer (kein Auto-Senden).
- [x] Nach Abschluss einer Aufnahme kann der Nutzer die **Aufnahme wiederholen** (ersetzt den per Sprache erfassten Anteil) **oder ergänzen** (eine weitere Aufnahme hängt ihren Text an den vorhandenen Feldinhalt an, statt ihn zu überschreiben).
- [x] Während der Aufnahme bzw. der laufenden Transkription ist der Senden-Button gesperrt/als „beschäftigt" erkennbar; nach Erhalt des Transkripts ist die Eingabe wieder frei.
- [x] Vor der **ersten** Mikrofon-Nutzung wird die bestehende Medien-Einwilligung (PROJ-22/D10) eingeholt; ohne Einwilligung bleibt das Mikrofon gesperrt, Texteingabe bleibt offen.
- [x] Auf Geräten/Browsern ohne Mikrofon-Zugriff wird der Button **als nicht verfügbar** dargestellt; die Text- und 📎-Eingabe bleiben vollständig nutzbar.
- [x] Die Sprach-UI respektiert die aktive App-Sprache (de/en, vgl. PROJ-24): Indikator- und Hinweistexte sind lokalisiert, und die gewählte Sprache wird (sofern unterstützt) an die Transkription weitergereicht.

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

**Erstellt:** 2026-05-31 — Architektur für die Umsetzung (3-Agenten-Team).

### Ausgangslage (verifiziert)
- Backend ist vorhanden: `POST /api/transkription` (app.py) nimmt multipart `file`/`audio` **oder**
  Rohdaten und ruft `multimodal.transkribiere(audio_bytes)`. Diese nutzt OpenAI-Whisper
  (`config.whisper_model()`, Default `whisper-1`) und liefert `{text, source:"whisper"}` bei Erfolg
  bzw. `{text:"", source:"hinweis", hinweis}` ohne Audio/Key/bei Fehler — **scheitert nie hart**.
  **Lücke:** Sprache ist auf `language="de"` **hartcodiert** (AK #8 verlangt Durchreichen de/en).
- Frontend: aktiver `ChatScreen` (screens.js, ~Z. 1940) hat in der `inputrow` nur 📎-Anhang +
  Text + Senden. Spracheingabe existiert nur in inaktiven Legacy-Screens via
  `webkitSpeechRecognition` — **nicht** im ChatScreen. Diese Legacy-Pfade bleiben unangetastet.
- `h()`-Helper (ui.js) unterstützt **nur** `onClick/onInput/onKeydown` (kein `onChange`).
- Consent: `State.medienConsent` (Bool) + `MediaConsentSheet` (über `State.mediaConsentOpen`),
  Pattern: Aktion zwischenspeichern → nach `onMediaConsentAccept` ausführen.
- `State.draft` wird bei `setDraft` **ohne Re-Render** gehalten (Fokus-Erhalt); Einfügen von
  Transkript-Text muss daher `State.draft` UND das Input-`value` aktualisieren (render() ersetzt DOM).

### Engine-Wahl
Browserseitige Aufnahme über **`MediaRecorder` + `getUserMedia`** (kein NPM-Paket), Upload des
Audio-Blobs (multipart `file`) an den **bestehenden** `POST /api/transkription`. Transkription
ausschließlich über die **OpenAI-Whisper-Cloud** (kein Browser-`webkitSpeechRecognition` mehr →
funktioniert auch in Firefox).

### Verbindlicher Schnittstellen-Vertrag (eingefroren)

**Agent A — Backend (`repair/multimodal.py` + `app.py`-Route + Test):**
```python
def transkribiere(audio_bytes: bytes | None = None, lang: str = "de") -> dict
# lang ∈ {"de","en"} (sonst → "de"); wird als language an die Whisper-API übergeben.
# Rückgabe-Form UNVERÄNDERT: {text, source:"whisper"} | {text:"", source:"hinweis", hinweis}
```
- `POST /api/transkription` liest die Sprache aus (Reihenfolge): Form-Feld `lang` → Query `?lang=`
  → JSON `lang` → Default `"de"`; nur `de`/`en` zulässig. Reicht sie an `transkribiere()` durch.
  Verhalten/Statuscodes sonst unverändert (immer HTTP 200 mit `{text,source,…}`).
- Test `tests/test_transkription.py`: lang-Parsing (de/en/unbekannt→de), kein-Audio-Hinweis,
  kein-Key-Hinweis (ohne `OPENAI_API_KEY`), Whisper-Pfad via gemocktem OpenAI-Client.

**Agent B — Audio-Engine (`static/js/voice.js` NEU + `templates/index.html`):**
```js
window.VoiceRecorder = {
  verfuegbar: function () -> bool,        // !!(navigator.mediaDevices?.getUserMedia) && window.MediaRecorder
  aufnahmeLaeuft: function () -> bool,
  starten: function () -> Promise<void>,  // getUserMedia + MediaRecorder.start(); rej[Error{code:'no_permission'|'no_support'|'fehler'}]
  abbrechen: function () -> void,         // Aufnahme + Stream verwerfen, KEIN Upload
  stoppenUndTranskribieren: function (opts) -> Promise<{text, source, hinweis, ok}>
  // opts = {lang}. Stoppt Aufnahme, lädt Blob als multipart 'file' an /api/transkription?lang=<lang>,
  // gibt geparstes JSON zurück + ok:(source==='whisper' && text nicht leer). Wirft NICHT bei
  // Transkriptionsfehler → {ok:false, source:'hinweis', hinweis, text:''}. Stream immer freigeben.
};
```
- `index.html`: `<script src=".../voice.js">` **vor** `app.js` einhängen (app.js nutzt `window.VoiceRecorder`).
- Selbstständig, KEINE UI, KEIN App-State. MIME tolerant wählen (z. B. `audio/webm`; Fallback Default).

**Agent C — Chat-UI & Verdrahtung (`static/js/screens.js` + `static/js/app.js` + `static/css/repair.css`):**
- `ChatScreen`-`inputrow`: **Mikrofon-Button** neben 📎 und ➤. Sichtbar immer; **disabled**, wenn
  `!VoiceRecorder.verfuegbar()` (mit Titel „Spracheingabe nicht verfügbar") oder `busy`.
- Aufnahme-Zustand: Live-Indikator („🎙️ Ich höre zu …", lokalisiert) + Mic-Button wird zum Stopp;
  während Aufnahme/Transkription ist **Senden gesperrt** (`busy`). Nach Transkript: Eingabe frei.
- Klick-Fluss (app.js): Mic-Klick → falls `!State.medienConsent` → `MediaConsentSheet` (Aktion
  zwischenspeichern, nach Accept Aufnahme starten) → `VoiceRecorder.starten()` (catch → `toast`
  mit lokalisiertem Hinweis je `err.code`, kein Sackgassen-Zustand). Stopp → `stoppenUndTranskribieren({lang: State.lang})`.
- **Text-Einfügung:** Transkript wird in `State.draft` eingefügt und ist editierbar; **kein
  Auto-Senden**. „Ergänzen" hängt Transkript an den bestehenden Feldinhalt an; „Wiederholen" ersetzt
  nur den zuletzt per Sprache erfassten Anteil (Tracking via `State.voiceBaseText`/`State.lastVoiceText`),
  nicht den manuell getippten Vorlauf. Nach erster Aufnahme „🔁 Wiederholen"/„➕ Ergänzen" anbieten.
- Degradation: Transkript leer/`source!='whisper'` → lokalisierter Hinweis („nichts erkannt" bzw.
  „Spracheingabe gerade nicht verfügbar"), Feldinhalt bleibt erhalten. i18n-Keys in **de UND en**.
- CSS: minimal additiv (Indikator-Puls, Mic-aktiv-Status), bestehende `rk-chat-*`-Klassen bevorzugen.

### Eigentum (kein Datei-Konflikt)
- **A** ⇒ `repair/multimodal.py`, `app.py` (nur `/api/transkription`), `tests/test_transkription.py`.
- **B** ⇒ `static/js/voice.js` (NEU), `templates/index.html` (Script-Tag).
- **C** ⇒ `static/js/screens.js`, `static/js/app.js`, `static/css/repair.css` (+ i18n in app.js).
- Keine zwei Agenten teilen eine Datei. Schnittstellen eingefroren; Integration + Browser-Test
  (echt, **nicht headless**) durch den Lead.

## QA Test Results

**Durchgeführt:** 2026-05-31 (Lead-Integration, 3-Agenten-Team).

**Unit-/Integrationstests:** `219 passed` (gesamte Suite), davon neu `tests/test_transkription.py`
(15 Tests): lang-Parsing (de/en/unbekannt→de) in Route + Funktion, kein-Audio-/kein-Key-Hinweis,
Whisper-Pfad mit gemocktem OpenAI-Client (verifiziert, dass `language` korrekt übergeben wird).
`node --check` für voice.js/app.js/screens.js fehlerfrei; Script-Reihenfolge ui→screens→voice→app.

**End-to-End-Browser (nicht headless, Playwright, lokaler Server):**
- Mikrofon-Button (🎙️) in der ChatScreen-Eingabezeile sichtbar/aktiv (Chromium unterstützt MediaRecorder).
- Erste Mic-Nutzung öffnet das Medien-Consent-Sheet (nennt Mikrofon); nach „Einverstanden" startet die Aufnahme.
- Aufnahme: Live-Indikator „🎙️ Ich höre zu …", Mic→⏹, Senden + 📎 gesperrt (busy-Lock).
- Stopp → Transkript wird ins (editierbare) Feld eingefügt, kein Auto-Senden; `lang:"de"` wird an die
  Transkription durchgereicht.
- „➕ Ergänzen" hängt eine weitere Aufnahme an den Feldinhalt an; „🔁 Wiederholen" ersetzt **nur** den
  zuletzt per Sprache erfassten Anteil (manuell/zuvor erfasster Vorlauf bleibt erhalten).
- Degradation: leeres/fehlgeschlagenes Transkript → Feldinhalt unverändert + Hinweis-Toast;
  Mikrofon-Zugriff verweigert (`no_permission`) → Toast „Mikrofon-Zugriff verweigert …", keine Aufnahme,
  Texteingabe läuft weiter; `verfuegbar()=false` → Button disabled „Spracheingabe nicht verfügbar",
  Text/📎 voll nutzbar.

Keine neuen Bugs während QA (Test deterministisch mit gestubbtem `window.VoiceRecorder` für den
Transkript-Pfad, da echtes Mikrofon/Whisper im automatisierten Browser nicht verfügbar).

## Deployment
_Wird von /deploy hinzugefügt_ — **Hinweis:** kein Merge durchgeführt (auf Wunsch). Stand: implementiert
& verifiziert auf Branch `worktree-features-chatgpt`; Status „In Review".
