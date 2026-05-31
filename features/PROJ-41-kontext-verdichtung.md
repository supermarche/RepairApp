# PROJ-41: Kontext-Verdichtung & Token-Budget der Orchestrierung

## Status: Planned

**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Abhängigkeiten

- PROJ-35 (LLM-Orchestrator-Schleife) — hatte Kontext-Kürzung explizit als „spätere Iteration" benannt; dies ist diese Iteration
- PROJ-32 (Rollen-Registry & Progressive Disclosure) — Rollen-Volltexte aus `lade_rolle` sind der größte Einzelposten
- PROJ-9 (Vorgangs-Persistenz) — Ort eines kompakten Zustands-Digests
- PROJ-28 (Anfrage-Protokoll) — Token-Messung vorher/nachher

## Beschreibung

**Verbesserung.** Pro Turn wird der gesamte bisherige Verlauf (`state["messages"]`) erneut
an OpenAI gesendet (`orchestrator.py:120`: `messages = system_prefix(lang) + state["messages"]`),
und geladene Rollen-Volltexte (`lade_rolle`, PROJ-32) verbleiben **dauerhaft** als
Tool-Messages im Verlauf. Dadurch wachsen die Prompt-Tokens stark mit der Vorgangslänge.

**Beleg:** Protokoll `PGPv-p6krV4WLlzk` — `prompt_tokens` über 7 Turns:
2801 → 2962 → 3861 → 4922 → 5086 → 5458 → **9118**. Der Sprung im letzten Turn fällt mit
einer Diagnose-/Recherche-Phase zusammen, in der Volltexte/Tool-Ergebnisse hinzukamen.

Ziel ist der **Mittelweg**: Es bleibt **ein** durchgehender logischer Vorgangs-Kontext
(keine separaten KI-Sessions pro Rollenwechsel), aber der **gesendete** Kontext wird
begrenzt — durch Entladen nicht mehr aktiver Rollen-Volltexte und Verdichtung des älteren
Verlaufs zu einem kompakten Zustands-Digest, während die jüngsten Nachrichten wörtlich
erhalten bleiben. Der stabile System-Präfix (PROJ-35) bleibt unangetastet/cachebar.

## User Stories

- Als Betreiber möchte ich, dass die Prompt-Tokens pro Turn nicht unbegrenzt mit der Vorgangslänge wachsen, damit Kosten und Latenz beherrschbar bleiben.
- Als Betreiber möchte ich, dass ein einmal geladener Rollen-Volltext nicht in jedem folgenden Turn erneut mitgeschickt wird, wenn er nicht mehr aktiv gebraucht wird, damit der größte Einzelposten entfällt.
- Als Nutzer möchte ich, dass die KI auch in langen Vorgängen den roten Faden behält (Gerät, Symptome, bisherige Entscheidungen), obwohl der Kontext verdichtet wird.
- Als Betreiber möchte ich ein konfigurierbares Kontext-/Token-Budget, damit ich das Verhalten ohne Code-Änderung steuern kann (`.env`, PROJ-30).

## Akzeptanzkriterien

- [ ] Geladene Rollen-Volltexte werden nach Gebrauch aus dem fortgeschriebenen Verlauf entfernt oder durch einen kompakten Verweis ersetzt, sodass sie nicht in jedem Folge-Turn erneut gesendet werden.
- [ ] Bei langen Vorgängen wird der ältere Verlauf zu einem kompakten Zustands-Digest verdichtet (erkanntes Gerät, Symptome, bisherige Karten/Entscheidungen), während die jüngsten Nachrichten wörtlich erhalten bleiben.
- [ ] Es bleibt **ein** durchgehender logischer Vorgangs-Kontext — es werden keine separaten KI-Sessions pro Rollenwechsel gestartet.
- [ ] Die Prompt-Token pro Turn wachsen nach Verdichtung nachweislich langsamer als kumulativ-linear (Vergleichsmessung vorher/nachher an einem Mehr-Turn-Vorgang, z. B. dem NAS-Szenario).
- [ ] Der System-Präfix bleibt byte-stabil/cachebar (PROJ-35 nicht verletzt); Verdichtung betrifft nur den variablen Verlaufsteil.
- [ ] Schwellen (z. B. Token-Budget/Turn, Anzahl wörtlich erhaltener Nachrichten) sind über `.env` konfigurierbar und in `.env.example` dokumentiert (PROJ-30, Drift-Guard).
- [ ] Diagnose-/Empfehlungsqualität bleibt erhalten: ein Regressions-Szenario führt nach Verdichtung zu einer gleichwertig sinnvollen Diagnose.

## Edge Cases

- Sehr kurzer Vorgang (unter Schwelle) → keine Verdichtung, Verhalten unverändert.
- Rolle wird später erneut gebraucht → kann via `lade_rolle` erneut geladen werden (Re-Disclosure), ohne durchgängig mitzulaufen.
- Wichtige Sicherheits-/Garantie-Hinweise (Backstop-Karten, PROJ-36) dürfen durch Verdichtung nicht verloren gehen.
- Medien-Evidenz (PROJ-31) muss im Digest referenziert bleiben, auch wenn der ursprüngliche Tool-Output verdichtet wird.
- Budget zu klein gewählt → ein definierter Mindest-Kontext (jüngste N Nachrichten + Digest) bleibt garantiert erhalten.

## Technische Anforderungen (optional)

- Betroffen: `webapp/repair/orchestrator.py` (Aufbau von `messages`, Verlaufs-Verdichtung), ggf. `repair/store.py` (Digest im State), `repair/roles.py` (Entlade-/Verweis-Strategie).
- Neue Konfiguration (z. B. `KONTEXT_TOKEN_BUDGET`, `KONTEXT_WOERTLICH_TURNS`) in `config.py` + `.env.example` (PROJ-30).
- Konkrete Strategie (Entladen vs. Zusammenfassen vs. beides, eigene Verdichtungs-KI-Runde vs. heuristisch) entscheidet /architecture.
- Bezug: PROJ-35 (explizit benannte Folge-Iteration), PROJ-32, PROJ-28 (Messung), PROJ-36 (Backstop-Erhalt).

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)
_Wird von /architecture hinzugefügt_

## QA Test Results
_Wird von /qa hinzugefügt_

## Deployment
_Wird von /deploy hinzugefügt_
