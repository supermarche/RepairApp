# PROJ-39: Medien-Extraktion repariert (Vision-Tool im Chat-Flow)

## Status: Planned

**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Abhängigkeiten

- PROJ-31 (Vision-Diagnose aus Foto & Dokument) — der defekte Pfad
- PROJ-34 (Daten-Tools) — Tool `extrahiere_aus_medien`, das die Extraktion im Chat-Flow aufruft
- PROJ-35 (LLM-Orchestrator-Schleife) — konsumiert das Tool-Ergebnis

## Beschreibung

**Bug (kritisch).** `repair/vision.py:336` ruft in `extrahiere()` die Funktion
`ai._clean_json_text(content)` auf — dieses Symbol existiert in `repair/ai.py` **nicht**
(dort liegt nur `_resolve_backend`). Jede Foto-/PDF-Auswertung wirft daher `AttributeError`
und fällt in den Degradationspfad (`vision.py:347-349`). Im Chat-Flow ruft der Orchestrator
das Tool `extrahiere_aus_medien` (PROJ-34); dessen Ergebnis ist dadurch **immer** „nichts
erkannt", unabhängig vom Bildinhalt. Vermutete Ursache: ein Refactor im Umfeld des
LLM-Aufräumens hat `_clean_json_text` aus `ai.py` entfernt, der Aufruf in `vision.py` blieb
stehen.

**Belege:** `webapp/logs/repair.log` — `2026-05-31 13:55:14` und `2026-05-31 14:38:07`:
„Vision-Extraktion fehlgeschlagen (AttributeError: module 'repair.ai' has no attribute
'_clean_json_text') → Degradation." Im Protokoll `PGPv-p6krV4WLlzk` (Turn 4) erhält der
Nutzer nach Foto-Upload fälschlich die Frage mit Hinweis „Die Bildauswertung hat leider
nichts erkannt".

## User Stories

- Als Nutzer möchte ich, dass ein angehängtes Foto (LEDs, Typenschild, Fehlermeldung) tatsächlich ausgewertet wird, damit die Diagnose meine Bild-Evidenz nutzt.
- Als Orchestrator möchte ich vom `extrahiere_aus_medien`-Tool verwertbare Felder erhalten, wenn das Bild lesbar ist, damit ich nicht fälschlich „nichts erkannt" annehme.
- Als Betreiber möchte ich, dass die JSON-Bereinigung der KI-Antwort an genau einer erreichbaren Stelle existiert, damit Vision und Orchestrator dieselbe robuste Logik nutzen (kein toter Verweis auf ein nicht existentes Symbol).

## Akzeptanzkriterien

- [ ] `repair/vision.extrahiere()` läuft ohne `AttributeError` durch und liefert bei lesbarem Bild echte Felder (z. B. geraet/modell/symptom), nicht `nichtsErkannt`.
- [ ] Die in `vision.py` genutzte JSON-Bereinigungsfunktion existiert und ist erreichbar — entweder in `ai.py` wiederhergestellt oder der Aufruf auf die tatsächlich vorhandene Funktion umgestellt; kein Verweis auf ein nicht existentes Symbol.
- [ ] Markdown-Code-Fences (```` ```json … ``` ````) in der KI-Antwort werden vor `json.loads` zuverlässig entfernt (regressionssicher).
- [ ] Der Chat-Flow mit `medienIds` liefert bei erkennbarem Inhalt eine Extraktions-Evidenz/-Karte statt der Frage „Bildauswertung hat nichts erkannt".
- [ ] Ein automatischer Test deckt den Pfad ab: gemockte KI-Antwort mit Fences → geparste Felder; kein `AttributeError`.
- [ ] Ein Smoke-/Regressionstest stellt sicher, dass das Symbol nicht erneut verschwindet (z. B. Import-/Attribut-Check).

## Edge Cases

- KI-Antwort enthält kein JSON / leeren Inhalt → definierter `nichtsErkannt`/Hinweis (echte Degradation), kein Crash.
- KI-Antwort mit ```` ```json ````-Fences und Zusatztext → Fences/Text werden entfernt, JSON sauber geparst.
- Bild ohne erkennbaren Inhalt (verwackelt/dunkel) → ehrliches „nichts erkannt" (Wortwahl siehe PROJ-42).
- PDF-Eingang ohne installiertes PyMuPDF → bestehender Degradationspfad bleibt unverändert erhalten.

## Technische Anforderungen (optional)

- Betroffen: `webapp/repair/vision.py:336`; ggf. `webapp/repair/ai.py` (Bereitstellung/Wiederherstellung der Bereinigungsfunktion).
- Keine neue `.env`-Konfiguration.
- Bezug: PROJ-31, PROJ-34, PROJ-35.

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)
_Wird von /architecture hinzugefügt_

## QA Test Results
_Wird von /qa hinzugefügt_

## Deployment
_Wird von /deploy hinzugefügt_
