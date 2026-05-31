# PROJ-42: Ehrliche Degradations-Signalisierung bei Medien-/Tool-Fehlern

## Status: Planned

**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Abhängigkeiten

- PROJ-39 (Medien-Extraktion repariert) — erst den Crash beheben, dann verbleibende echte Fehler ehrlich signalisieren
- PROJ-34 (Daten-Tools) — `extrahiere_aus_medien` reicht den Status an den Orchestrator
- PROJ-25 (Vertrauens-Indikator, D3) — ehrliche Konfidenz-/Quellenkommunikation
- PROJ-31 (Vision-Diagnose) — Quelle der Degradation
- Fachlicher Bezug: PROJ-40 (gemeinsame Fehlerklasse bei API-Fehlern)

## Beschreibung

**Verbesserung.** Wenn die Medien-Extraktion **technisch** scheitert (der Code-Crash aus
PROJ-39 oder ein API-/Timeout-Fehler), liefert das Tool aktuell ununterscheidbar dasselbe
Signal wie „Bild ist lesbar, aber es war nichts Verwertbares erkennbar" — beides endet in
`nichtsErkannt` (`vision.py:347-349`). Im Protokoll `PGPv-p6krV4WLlzk` (Turn 4) sagt das
Modell dem Nutzer daraufhin „Die Bildauswertung hat leider nichts erkannt" — obwohl die
Auswertung **gar nicht lief**. Das ist eine Unwahrheit gegenüber dem Nutzer und verletzt den
Grundsatz des durchgängigen Vertrauens-Indikators (D3, PROJ-25): Es wird eine erfolgte,
ergebnislose Prüfung suggeriert, wo in Wahrheit ein technischer Fehler vorlag.

Ziel: Tool-Ergebnisse müssen „**technisch fehlgeschlagen**" von „**erfolgreich, aber nichts
erkannt**" unterscheidbar machen, und der Orchestrator/das Modell muss entsprechend ehrlich
kommunizieren.

## User Stories

- Als Nutzer möchte ich erfahren, wenn die Bildauswertung technisch nicht funktioniert hat (statt der falschen Auskunft „nichts erkannt"), damit ich weiß, dass es an der App liegt und nicht an meinem Foto.
- Als Nutzer möchte ich bei erfolgreicher, aber ergebnisloser Auswertung einen konkreten Tipp (besseres Licht, näher heran, Typenschild), damit ich ein nützlicheres Foto liefern kann.
- Als Orchestrator möchte ich aus dem Tool-Ergebnis erkennen, ob ein technischer Fehler oder ein echtes Nullresultat vorliegt, damit ich nicht fälschlich behaupte, etwas sei geprüft worden.
- Als Betreiber möchte ich, dass technische Degradationen als solche protokolliert werden, damit ich sie von normalen Nullresultaten trennen kann.

## Akzeptanzkriterien

- [ ] Das Medien-/Extraktions-Tool unterscheidet im Ergebnis klar zwischen `technischer_fehler` und `nichts_erkannt` (eigenes Feld/Status), nicht nur ein gemeinsames `nichtsErkannt`.
- [ ] Bei technischem Fehler kommuniziert die App dem Nutzer ehrlich, dass die Auswertung nicht durchgeführt werden konnte — keine Formulierung, die eine erfolgte Prüfung suggeriert.
- [ ] Bei erfolgreicher, aber ergebnisloser Auswertung bleibt die bestehende „nichts erkannt"-Formulierung inkl. Foto-Tipp zulässig.
- [ ] Der Vertrauens-Indikator/Hinweis (D3, PROJ-25) wird bei technischem Fehler nicht als „geprüft mit Konfidenz" dargestellt.
- [ ] Technische Fehler werden mit Ursache protokolliert (PROJ-28/29) und sind von Nullresultaten unterscheidbar.
- [ ] Ein Test prüft beide Pfade: erzwungener technischer Fehler → ehrliche Fehlermeldung; gemockte leere Erkennung → „nichts erkannt" + Tipp.

## Edge Cases

- Technischer Fehler bei einem von mehreren Bildern → pro Medium differenzierte Rückmeldung, nicht pauschal „nichts erkannt".
- API-Timeout der Vision-Auswertung → als technischer Fehler behandelt (verwandt mit PROJ-40).
- Teilerfolg (ein Feld erkannt, Rest nicht) → wird als Teilergebnis dargestellt, nicht als „nichts".
- Nutzer lädt ein nicht konvertierbares Dokument hoch → ehrlicher technischer Hinweis statt „nichts erkannt".

## Technische Anforderungen (optional)

- Betroffen: `webapp/repair/vision.py` (Rückgabe-Schema um Fehlerart erweitern), `webapp/repair/tools.py` (`extrahiere_aus_medien`-Dispatch reicht Status durch), Hinweistext/Prompt im Orchestrator.
- Abhängig von PROJ-39 (erst Crash beheben, dann ehrliche Restfehler signalisieren).
- Keine zwingende neue `.env`-Konfiguration.
- Bezug: D3, PROJ-25, PROJ-31, PROJ-40 (gemeinsame Fehlerklasse).

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)
_Wird von /architecture hinzugefügt_

## QA Test Results
_Wird von /qa hinzugefügt_

## Deployment
_Wird von /deploy hinzugefügt_
