# PROJ-38: Responsive Web-Layout statt Handy-Attrappe

## Status: Done
**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Kontext / Problem

Die App wird aktuell in ein simuliertes Smartphone gerendert: `#phone-root` → `.rk-phone`
mit fester Größe `384 × 812 px` (`.rk-canvas`), schwarzem Geräterahmen (`border: 13px solid`,
46px-Ecken, Schlagschatten), gefälschter Statusleiste (`.rk-statusbar`: Uhrzeit „9:41",
Signalbalken, Akku-Symbol) und iPhone-Home-Indikator (`.rk-home`). Das ist ein 1:1-Port des
Design-Prototyps (`docs/design-handoff/project/`) — ein **Mockup-Bild**, keine echte Website.

Folge: Auf dem Desktop schwebt ein Handy mittig auf grauer Bühne; die Seite skaliert nicht mit
dem Browser. Auf dem echten Handy entsteht ein „Handy-im-Handy"-Effekt mit doppelter Statusleiste.

**Ziel:** eine echte responsive Website, die den Browser füllt und von Mobil bis Desktop
funktioniert — **mobil-first**, auf breiten Bildschirmen als **zentrierte Lese-Spalte**.

## Entscheidungen (mit dem Nutzer abgestimmt, 2026-05-31)

- **Desktop-Layout:** zentrierte Lese-Spalte — Inhalt mobil-first, auf breiten Screens in
  begrenzter Breite mittig, füllt aber den Browser ohne Phone-Rahmen.
- **Mockup-Chrome:** komplett entfernen — Geräterahmen, Statusleiste (Uhrzeit/Signal/Akku)
  und Home-Indikator fallen ersatzlos weg.
- **Umfang:** Hülle responsiv machen **+ Desktop-Feinschliff**. Bestehende Screens/Flows
  bleiben inhaltlich identisch; angepasst werden Container, Skalierung, Abstände und
  Touch→Maus-Verhalten, damit die Screens auf großen Bildschirmen sauber wirken.

## Abhängigkeiten
- Keine harte Feature-Abhängigkeit. **Querschnitts-UI-Änderung:** betrifft die Render-Hülle,
  die alle Screens nutzen (`PhoneFrame()` in `ui.js`, Mount in `app.js`, Layout-Tokens in
  `repair.css`/`index.html`). Keine Backend- oder API-Änderung.

## User Stories
- Als **Handy-Nutzer** möchte ich die App im Vollbild meines Browsers benutzen, damit ich
  keine doppelte Statusleiste und keinen Handy-im-Handy-Effekt sehe.
- Als **Desktop-Nutzer** möchte ich eine lesbare, mittig zentrierte Inhaltsspalte statt eines
  schwebenden Telefonbildes, damit sich die Seite wie eine echte Website anfühlt.
- Als **Nutzer auf einem Tablet / im Querformat** möchte ich, dass sich das Layout flüssig
  anpasst, ohne dass Inhalte abgeschnitten werden oder horizontal scrollen.
- Als **Nutzer** möchte ich Theme- und Sprachumschalter weiterhin gut erreichbar haben, damit
  der Funktionsumfang erhalten bleibt.
- Als **Nutzer mit Tastatur/Maus** möchte ich, dass Klick-/Hover-Ziele auch ohne Touch gut
  bedienbar sind (Hover-Zustände, sichtbarer Fokus).

## Akzeptanzkriterien
- [x] `.rk-phone`-Geräterahmen (schwarzer Rand, 46px-Ecken, Geräte-Schlagschatten) wird entfernt;
      die App rendert direkt in den Seiteninhalt.
- [x] Gefälschte Statusleiste (`.rk-statusbar` inkl. „9:41", Signalbalken, Akku-SVG) ist
      vollständig entfernt — kein DOM-Knoten, keine CSS-Reste.
- [x] Home-Indikator (`.rk-home`) ist entfernt.
- [x] Feste Maße `384 × 812 px` (`.rk-canvas`) entfallen; der Inhalt nutzt die Viewport-Breite.
- [x] Auf schmalen Viewports (≤ ~480px) füllt der Inhalt die volle Breite mit angemessenem
      seitlichem Innenabstand (kein horizontales Scrollen, kein Beschnitt). _Verifiziert: 320/360/390px, kein H-Scroll._
- [x] Auf breiten Viewports wird der Inhalt auf eine **maximale Breite** begrenzt und horizontal
      **zentriert** (Lese-Spalte). _max-width: `--app-max` (Default 640px); bei 1280px zentriert verifiziert._
- [x] Die Seite nutzt natürliches Seiten-Scrolling; es gibt keinen separaten Innen-Scrollbereich,
      der eine Telefon-Hülle simuliert. _`.rk-body` overflow-y: visible; AppBar/Footer `position: sticky`._
- [x] Theme-Umschalter und Sprach-Umschalter bleiben sichtbar, bedienbar und korrekt
      positioniert (mobil wie Desktop). _Im Seitenkopf `.rk-pagehead`._
- [x] Theme-Wechsel funktioniert weiterhin: Theme-CSS-Variablen werden weiterhin auf den
      passenden Wurzel-Container gesetzt. _Jetzt direkt auf `.rk-app` (inline-style); Mutig→`--bg:#141118` greift verifiziert._
- [x] Alle bestehenden Screens/Flows (Start, Triage, Diagnose, Bewertung, Vergleich, Vermittlung,
      Entsorgung, Ersatzteile, Multimodal/Vision-Bestätigung, Protokoll/Export …) rendern korrekt
      und sind weiterhin vollständig nutzbar — keine inhaltliche Änderung. _Keine Screen-/Renderer-Logik geändert, nur die Hülle._
- [x] Touch-Interaktionen funktionieren weiterhin; zusätzlich gibt es sinnvolle Hover- und
      sichtbare Fokus-Zustände für Maus/Tastatur. _`:focus-visible`-Ring global; Hover via `@media (hover: hover)`._
- [x] `viewport`-Meta-Tag bleibt korrekt (`width=device-width, initial-scale=1.0`); kein
      doppeltes Skalieren.
- [x] Keine toten CSS-Regeln zur Telefon-Hülle bleiben übrig (aufgeräumt, nicht nur überschrieben).

## Edge Cases
- **Sehr breiter Monitor (z.B. ≥ 1440px):** Inhalt bleibt zentriert in max-width, kein
  überdehntes Layout, kein riesiger Leerraum-Bruch.
- **Sehr kleines/schmales Gerät (z.B. 320px):** kein Überlauf, kein abgeschnittener Text,
  Buttons bleiben tippbar (Mindestgröße).
- **Querformat auf dem Handy (niedrige Höhe):** Inhalt scrollt natürlich, App-Bar/Footer
  verdecken keine Inhalte dauerhaft.
- **Theme-Wechsel nach dem Umbau:** Variablen-Vererbung muss auf dem neuen Wurzel-Container
  greifen — keine „farblosen" Screens, weil die Variablen vorher nur an `.rk-phone` hingen.
- **Lange Inhalte (z.B. ausführliche Diagnose/Protokoll):** Seiten-Scroll statt
  Innen-Scroll; Sticky-Elemente (falls vorhanden) dürfen nicht springen.
- **Browser-Zoom / großer System-Font:** Layout bleibt nutzbar, bricht nicht.
- **Bestehende Tests / Selektoren:** Falls Tests oder Skripte auf `.rk-phone`/`.rk-statusbar`
  prüfen, müssen sie angepasst werden (im QA-Schritt verifizieren).

## Technische Anforderungen (optional)
- **Browser-Support:** aktuelle Chrome, Firefox, Safari (inkl. mobile Safari/Chrome).
- **Keine neuen Frontend-Frameworks** — bleibt Vanilla-JS + Tailwind-Scaffold + `repair.css`
  gemäß `webapp/SPEC.md`. Theme-Variablen-Modell bleibt erhalten.
- **Keine Backend-/API-Änderung.**
- **Performance:** keine zusätzlichen blockierenden Ressourcen; reines Layout/CSS + kleine
  JS-Anpassung der Render-Hülle.
- **`webapp/SPEC.md`** (Klassennamen-/Theme-Token-Vertrag) ggf. nachziehen, wenn Hüllen-Klassen
  entfallen — Drift vermeiden.

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)

Reine Frontend-/CSS-Querschnittsänderung an der Render-Hülle — keine Backend-/API-Änderung.

- **Hülle:** `index.html` rendert `.rk-page > .rk-pagehead (Theme-/Sprach-Switcher) + #phone-root`.
  Layout vollständig in `repair.css` (Layout-Tokens `--page-bg`, `--app-max` am `:root`).
- **Lese-Spalte:** `.rk-app` ist die Spalte: mobil volle Breite, ab Inhalt `max-width: var(--app-max)`
  (Default **640px**), `margin: 0 auto`, `background: var(--bg)`. Ab `min-width: 700px` dünne
  Seitenränder zur Bühne. Theme-Variablen werden in `app.js` (`buildPhone`) per `style.setProperty`
  **direkt auf `.rk-app`** gesetzt (vorher am entfernten `.rk-phone`).
- **Scrolling:** natürliches Seiten-Scrolling (`.rk-body { overflow: visible }`); `.rk-appbar`
  `position: sticky; top:0`, `.rk-footer` `position: sticky; bottom:0`.
- **Overlays:** `.rk-sheet-scrim` und `.rk-toast` auf `position: fixed` (viewport-deckend);
  Sheet/Toast auf Spaltenbreite (`max-width: var(--app-max)`) zentriert.
- **Entfernt:** `ui.js#PhoneFrame` (+ Export), CSS `.rk-phone/.rk-statusbar/.rk-time/.rk-status-right/
  .rk-bars/.rk-batt/.rk-screen/.rk-home/.rk-canvas`, JS `State.phoneEl`. `SPEC.md`
  (Klassen-/Theme-Token-Vertrag) nachgezogen.

## QA Test Results

Manuell im Browser (Playwright, `python app.py` ohne OPENAI-Key) verifiziert:

- **Desktop (1280×860):** zentrierte 640px-Lesespalte auf neutraler Bühne, sticky AppBar oben,
  sticky Eingabe-Footer unten, keine Telefon-Hülle. ✅
- **Mobil (390/360px) & schmal (320px):** volle Breite, kein horizontales Scrollen
  (`scrollWidth == clientWidth`), 0 Phone-Chrome-Knoten (`.rk-phone/.rk-statusbar/.rk-home/.rk-canvas`). ✅
- **Natürliches Scrolling:** `.rk-body` `overflow-y: visible`; AppBar/Footer `position: sticky`. ✅
- **Theme-Wechsel:** Klick „Mutig" → `.rk-app` erhält `rk-theme-mutig`, `--bg:#141118` und dunkler
  `background-color` greifen (keine farblosen Screens). ✅
- **Overlay:** injiziertes `.rk-sheet-scrim` ist `position: fixed`, deckt den Viewport
  (390×760) vollständig, Sheet auf Spaltenbreite zentriert. ✅
- **Konsole:** keine JS-Fehler (nur favicon-404 + Tailwind-CDN-Hinweis, beide vorbestehend). ✅
- **JS-Syntax:** `node --check` für `ui.js` und `app.js` grün. ✅

## Deployment
_Wird von /deploy hinzugefügt_
