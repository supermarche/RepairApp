# PRD — Reparatur-App

> **Erstellt:** 2026-05-30 · **Quelle:** `docs/konzept.adoc` (Decision-Log D1–D25),
> `docs/runtime-roles/` (14 Laufzeit-Rollen), `docs/funktionsabgleich.md` (Soll/Ist-Abgleich).
> **Phasenziel:** Machbarkeit prüfen und Akzeptanz testen (vgl. konzept.adoc → *Priorität & Zielsetzung dieser Phase*).

## Vision

Eine KI-gestützte Reparatur-App, die Menschen befähigt, eine **bewusste Entscheidung
zwischen Reparatur und Neukauf** zu treffen — und sie anschließend durch die Reparatur
begleitet. Sie zeigt mögliche Defekte, Reparaturwege, hilfreiche Adressen (Repair Café,
Werkstatt), Ersatzteilbezug, Fördermittel und den tatsächlichen Aufwand eines Austauschs.

**Drei Werthebel:** Ökologisch (Reparatur als sichtbare Alternative zum Wegwerfen),
Finanziell (echten Mehrwert gegenüber Neukauf aufzeigen), Sozial (Selbstwirksamkeit
fördern — Menschen ermutigen, sich mehr zuzutrauen).

**Herzstück:** die **Warn-Ampel** (D1) über vier Achsen — Sicherheit · Komplexität ·
Kostenaufwand · Machbarkeit. Grundhaltung durchgängig **„warnen statt sperren"** (D15):
der mündige Nutzer entscheidet, je kritischer desto deutlicher die Warnung.

## Zielnutzer

**Situative Rollen pro Vorgang** (eine Person kann mehrere ausfüllen): Eigentümer,
Nutzer, Diagnostiker, Reparateur, Teile-Beschaffer.

**Nutzer-Segmente als Achsen** (nicht als Schubladen): Budget · Zeit · Können ·
Motivation. Primäre Zielgruppe der Mission sind **ängstliche Erstnutzer:innen** — die
Gruppe, die sich Selbstreparatur bisher nicht zutraut. Ebenfalls adressiert:
Idealist:innen (priorisieren Nachhaltigkeit/Lernen) und Einkommensschwache.

## Core Features (Roadmap)

Priorität spiegelt die Stufen aus `docs/funktionsabgleich.md` §5 wider:
**P0 = Stufe 1** (fachliche Tiefe & ehrliche Pfade, nah am Phasenziel) ·
**P1 = Stufe 2** (Alternativpfade & Querschnittsdienste) ·
**P2 = Stufe 3** (Datengrundlage & Architektur).

| Prio | Feature | Rolle / D-Anker | Status |
|---|---|---|---|
| P0 | [PROJ-1 Eigentum & Kostenträger erfragen](../features/PROJ-1-eigentum-kostentraeger.md) | `aufnahme` · D14 | Planned |
| P0 | [PROJ-2 Freitext-Antwort in der Triage](../features/PROJ-2-freitext-triage.md) | `aufnahme` | Planned |
| P0 | [PROJ-3 Fähigkeits-Rückfrage](../features/PROJ-3-faehigkeits-rueckfrage.md) | `lotse`/`begleitung` · D11 | Planned |
| P0 | [PROJ-4 Unklar-Pfad (Diagnose-Sackgasse)](../features/PROJ-4-unklar-pfad.md) | `diagnose` · D20 | Planned |
| P0 | [PROJ-5 Reparatur-vs-Austausch-Vergleich](../features/PROJ-5-vergleichstabelle-reparatur-austausch.md) | `abwaegung` · D12/D18 | Planned |
| P0 | [PROJ-6 Förderung & Reparatur-Bonus](../features/PROJ-6-foerderung-reparatur-bonus.md) | `abwaegung` | Planned |
| P0 | [PROJ-7 Garantie-/Gewährleistungs-Gate](../features/PROJ-7-garantie-gate.md) | `begleitung` · D21 | Planned |
| P0 | [PROJ-8 Selbsteinschätzung vor Schicht B](../features/PROJ-8-selbsteinschaetzung-schicht-b.md) | `begleitung` · D25 | Planned |
| P0 | [PROJ-9 Serverseitige Vorgangs-Persistenz](../features/PROJ-9-vorgangs-persistenz.md) | `protokoll` · D7 | Planned |
| P0 | [PROJ-10 Protokoll-Export & Teilen](../features/PROJ-10-protokoll-export-teilen.md) | `protokoll` · D7 | Planned |
| P1 | [PROJ-11 Vermittlung von Anbietern](../features/PROJ-11-vermittlung-anbieter.md) | `vermittlung` | Planned |
| P1 | [PROJ-12 Entsorgungs-/Recyclingwege](../features/PROJ-12-entsorgung-wege.md) | `entsorgung` | Planned |
| P1 | [PROJ-13 Produktsuche / Alternativgeräte](../features/PROJ-13-produktsuche-alternativen.md) | `produktsuche` | Planned |
| P1 | [PROJ-14 Beschaffung von Ersatzteilen](../features/PROJ-14-beschaffung-ersatzteile.md) | `beschaffung` · D8 | Planned |
| P1 | [PROJ-25 Vertrauens-Indikator durchgängig](../features/PROJ-25-vertrauens-indikator.md) | Querschnitt · D3 | Planned |
| P1 | [PROJ-26 Universelle Triage-Fragen](../features/PROJ-26-universelle-triage-fragen.md) | `aufnahme` · D6 | Planned |
| P2 | [PROJ-15 Kuratierte Fehlerzustand-Sammlung](../features/PROJ-15-wissensbasis-fehlerzustaende.md) | `wissensbasis` · D13/D5 | Planned |
| P2 | [PROJ-16 Recherche-Dienst (kuratiert→Fallback→online)](../features/PROJ-16-recherche-dienst.md) | `recherche` · D2 | Planned |
| P2 | [PROJ-17 Diagnose auf kuratierter Sammlung](../features/PROJ-17-diagnose-kuratierte-sammlung.md) | `diagnose` · D4 | Planned |
| P2 | [PROJ-18 Rollen-/Agenten-Architektur](../features/PROJ-18-rollen-architektur.md) | `lotse` · D19 | Planned |
| P2 | [PROJ-19 Rückruf / Sicherheitsmangel](../features/PROJ-19-rueckruf-sicherheitsmangel.md) | Edge-Case · D22 | Planned |
| P2 | [PROJ-20 Datenlöschung vor Fremdabgabe](../features/PROJ-20-datenloeschung-fremdabgabe.md) | Edge-Case · D23 | Planned |
| P2 | [PROJ-21 Mehrfachdefekte mit Gesamt-Fazit](../features/PROJ-21-mehrfachdefekte.md) | `bewertung` · D24 | Planned |
| P2 | [PROJ-22 Consent-Gate (Einwilligung)](../features/PROJ-22-consent-gate.md) | `lotse` · D10 | Planned |
| P2 | [PROJ-23 Anonymisierung & Daten-Schwungrad](../features/PROJ-23-anonymisierung-schwungrad.md) | `protokoll`/`wissensbasis` · D10/D7 | Planned |
| P2 | [PROJ-24 Mehrsprachigkeit (Englisch)](../features/PROJ-24-mehrsprachigkeit-englisch.md) | Querschnitt · D17 | Planned |
| P2 | [PROJ-27 Multimodale Eingabe](../features/PROJ-27-multimodale-eingabe.md) | `aufnahme` · D9 | Planned |
| P2 | [PROJ-28 Anfrage-Protokoll als Markdown (Betreiber-Debug)](../features/PROJ-28-anfrage-protokoll-md.md) | Betrieb/Querschnitt | Planned |
| P2 | [PROJ-29 Zentrales Logging (Datei + Konsole, tägl. Rotation)](../features/PROJ-29-logging.md) | Betrieb/Querschnitt | Planned |
| P2 | [PROJ-30 Konfiguration ausschließlich über `.env`](../features/PROJ-30-konfiguration-ueber-env.md) | Betrieb/Querschnitt | Planned |
| P1 | [PROJ-31 Vision-Diagnose aus Foto & Dokument](../features/PROJ-31-vision-diagnose-foto-dokument.md) | `aufnahme`/`diagnose` · D9 | Planned |
| P3 | [PROJ-32 Rollen-Registry & Progressive Disclosure](../features/PROJ-32-rollen-registry-progressive-disclosure.md) | `lotse`/alle · D19 | Planned |
| P3 | [PROJ-33 Karten-Decomposition & `zeige_karte`](../features/PROJ-33-karten-decomposition-zeige-karte.md) | Journey · D1/D3 | Planned |
| P3 | [PROJ-34 Daten-Tools für Function-Calling](../features/PROJ-34-daten-tools-function-calling.md) | Querschnitt · D2/D8 | Planned |
| P3 | [PROJ-35 LLM-Orchestrator-Schleife](../features/PROJ-35-llm-orchestrator-schleife.md) | `lotse` · D19/D17 | Planned |
| P3 | [PROJ-36 Nicht-sperrender Sicherheits-Backstop](../features/PROJ-36-nicht-sperrender-sicherheits-backstop.md) | Querschnitt · D15/D3 | Planned |
| P3 | [PROJ-37 Chat-Flow: API & Frontend (harter Schnitt)](../features/PROJ-37-chat-flow-api-frontend.md) | `lotse` · D6/D19 | Planned |
| P0 | [PROJ-39 🐞 Medien-Extraktion repariert](../features/PROJ-39-medien-extraktion-fix.md) | `aufnahme`/`diagnose` · D9 | Planned |
| P0 | [PROJ-40 🐞 Orchestrator-Robustheit bei API-Fehlern](../features/PROJ-40-orchestrator-api-fehler-robustheit.md) | `lotse` · D7/D19 | Planned |
| P1 | [PROJ-41 ✨ Kontext-Verdichtung & Token-Budget](../features/PROJ-41-kontext-verdichtung.md) | `lotse`/Querschnitt · D19/D7 | Planned |
| P1 | [PROJ-42 ✨ Ehrliche Degradations-Signalisierung](../features/PROJ-42-ehrliche-degradation-medien.md) | Querschnitt · D3 | Planned |
| P1 | [PROJ-43 ✨ Beobachtbarkeit der Orchestrierung](../features/PROJ-43-orchestrierung-beobachtbarkeit.md) | Betrieb/Querschnitt | Planned |
| P1 | [PROJ-44 Service-Point-Übergabe-Report (PDF- & Text-Download)](../features/PROJ-44-service-point-report-download.md) | `protokoll`/`vermittlung` · D14/D3/D23 | Planned |
| P1 | [PROJ-46 Feedback-Button (Prozess-Anmerkungen des Nutzers)](../features/PROJ-46-feedback-button.md) | Querschnitt · D3/D7 | Planned |

> **P3 = Stufe 4 (Architektur-Umbau):** LLM-Orchestrierung über `runtime-roles`
> (OpenAI-only). Ersetzt den Single-Shot-Diagnosepfad durch einen orchestrierten Chat-Flow.
> Specs/Plan unter `docs/superpowers/`.
>
> **Stufe 5 (Orchestrierungs-Härtung):** PROJ-39…43 — Nachträge aus der Betriebs-Analyse
> vom 2026-05-31. Zwei Bugs (PROJ-39 kritisch, PROJ-40) + drei Verbesserungen (PROJ-41/42/43)
> am Stufe-4-Flow. Empfohlen: PROJ-39 zuerst.
>
> **Stufe 6 (Übergabe & Output):** PROJ-44 — Service-Point-Übergabe-Report. Erweitert den
> Export (PROJ-10) um einen server-seitig erzeugten PDF-Download mit zielgruppen-spezifischen
> Report-Varianten (Annahmestelle/Werkstatt) plus Klartext/Markdown.
>
> **Stufe 8 (Nutzer-Feedback):** PROJ-46 — Feedback-Button. Niederschwellige Freitext-Anmerkung
> zum laufenden Vorgang; lokal gespeichert (kein externer Versand), zweifach abgelegt (eigene
> Persistenz + Hinweis im Vorgangs-Protokoll).

## Erfolgsmetriken

Da das Phasenziel **Machbarkeit & Akzeptanz** ist (nicht Skalierung/Monetarisierung):

- **Akzeptanz:** Anteil der Nutzer, die die Warn-Ampel + Empfehlung als
  nachvollziehbar/vertrauenswürdig bewerten.
- **Selbstwirksamkeit:** Anteil der begleiteten Reparaturen, die der Nutzer als
  „zugetraut/erfolgreich" markiert (auch ehrlicher Misserfolg zählt als gültiges Ergebnis).
- **Ehrlichkeit der Pfade:** Anteil der Fälle mit korrektem Abraten/Profi-Verweis bzw.
  ehrlichem „unklar"-Ausgang statt vorgetäuschter Sicherheit.
- **Vollständigkeit des Protokolls:** Anteil der Vorgänge, deren Protokoll exportier-/
  teilbar ist und alle Pflichtfelder (Symptom, Ampel, Eigentum/Kostenträger, Quelle/Konfidenz) trägt.

## Constraints

- **Stack:** Python/Flask-Backend + Vanilla-JS-Statemachine-Frontend + Tailwind, optional
  OpenAI-Live-Diagnose. Verbindlich: `webapp/SPEC.md`. **Kein** Kotlin/Fritz2/Ktor (überholt).
- **App läuft auch ohne API-Key** — `POST /api/diagnose` fällt sauber auf Seed-Daten zurück.
- **Cloud-first** für KI-Qualität (D10), aber Einwilligung erforderlich.
- **Haftung liegt beim Anwender** (D16); die App gibt Hilfestellung, übernimmt keine
  Verantwortung für die Ausführung.
- **Datengrundlage:** zum Start keine externen Daten — eigene, KI-erstellte + menschlich
  geprüfte Grundlage (D13). Keine regionale Einschränkung.

## Non-Goals (bewusst ausgelagert / nicht in dieser Phase)

- **Detaillierte Datenschutz-Implementierung** (Rechtsgrundlage, Anonymisierungs-Verfahren) —
  eigenes Projekt; nur das *Consent-Gate* (PROJ-22) und ein *grobes* Schwungrad (PROJ-23) gehören in diese App.
- **Assistive Barrierefreiheit** (Screenreader, ARIA, große Schrift, Kontraste) — eigenes
  Thema über die Mehrsprachigkeit (D17) hinaus.
- **Ausgefeiltes KI-Kostenmodell** — erst nach Machbarkeits-/Akzeptanznachweis.
- **Rechtliche Absicherung** verbotener/hochgefährlicher Laien-Eingriffe (Gas, Hochvolt,
  feste 230-V-Installation) — offener Prüfpunkt, nicht hier zu lösen.
- **Hard-Stop-Geräteklassen** — es gibt keine Klasse, die Schicht B komplett abriegelt (D15).
