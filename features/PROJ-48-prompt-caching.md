# PROJ-48: Prompt-Caching beobachtbar machen & gezielt steuern

## Status: Planned
**Erstellt:** 2026-05-31
**Zuletzt aktualisiert:** 2026-05-31

## Kontext

OpenAIs Prompt-Caching ist **vollautomatisch**: identische Prompt-Präfixe ab ~1024 Tokens
werden serverseitig gecacht und als `cached_tokens` vergünstigt abgerechnet (kein API-Schalter
zum „Einschalten"). Der Orchestrator ist dafür bereits gebaut — `orchestrator.system_prefix()`
ist byte-stabil, die Sprachdirektive (D17) hängt separat am Ende, Digest/Verlauf
(`kontext.sende_sicht`) kommen erst **nach** dem Präfix.

Was fehlt, ist die **Sichtbarkeit und gezielte Steuerung**:
- `usage.prompt_tokens_details.cached_tokens` wird **nirgends ausgelesen** (weder
  `orchestrator._merke_usage` noch `protokoll_log.merke_usage`). Es ist damit aktuell **nicht
  verifizierbar**, ob das Caching überhaupt greift, wie hoch die Trefferquote ist und welche
  Ersparnis entsteht.
- Der optionale `prompt_cache_key` (verbessert das Cache-Routing) wird nicht gesetzt.
- Es gibt keinen Guard, der die Byte-Stabilität von `system_prefix()` + `tools.specs()` gegen
  versehentlichen Cache-Drift bei künftigen Änderungen absichert.

Dieses Feature schließt diese drei Lücken — es führt **kein** neues KI-Verhalten ein, sondern
macht eine bestehende OpenAI-Eigenschaft messbar, steuerbar und gegen Regression abgesichert.

## Abhängigkeiten
- Benötigt: **PROJ-35** (LLM-Orchestrator-Schleife) — Ort des KI-Calls (`run_turn`).
- Benötigt: **PROJ-28** (Anfrage-Protokoll) — Token-Statistik wird dort ausgewiesen.
- Benötigt: **PROJ-29** (zentrales Logging) — INFO-Zeile pro Turn.
- Benötigt: **PROJ-30** (.env-Konfiguration) — neue Werte ausschließlich über `.env`.
- Bezug: **PROJ-41** (`kontext.sende_sicht`) — die verdichtete Sende-Sicht darf den stabilen
  Präfix nicht verletzen (relevant für die Stabilitäts-Härtung).
- Bezug: **PROJ-43** (Beobachtbarkeit der Orchestrierung) — gleicher Geist, ergänzt um Cache-Metrik.

## User Stories
- Als **Betreiber** möchte ich pro Anfrage sehen, wie viele Prompt-Tokens aus dem Cache kamen
  (`cached_tokens`) und wie hoch die Trefferquote ist, damit ich verifizieren kann, dass das
  Prompt-Caching tatsächlich greift, und die Kostenersparnis belegen kann.
- Als **Betreiber** möchte ich die Cache-Kennzahl knapp im laufenden Log sehen, damit ich die
  Wirkung im Betrieb beobachten kann, ohne jede Protokoll-Datei zu öffnen.
- Als **Entwickler** möchte ich einen stabilen `prompt_cache_key` je Sprache senden, damit
  vorgangsübergreifende Anfragen mit identischem Präfix bevorzugt dieselbe Cache-Instanz treffen
  und die Trefferquote steigt.
- Als **Entwickler** möchte ich einen Guard-Test, der anschlägt, sobald `system_prefix()` oder
  `tools.specs()` ihre Byte-Repräsentation ändern, damit ich Cache-Drift bewusst entscheide
  statt versehentlich die Trefferquote zu zerstören.
- Als **Betreiber** möchte ich Caching ohne Code-Änderung über `.env` konfigurieren können
  (Cache-Key-Präfix, Ein/Aus des expliziten Keys), passend zur `.env`-Disziplin des Projekts.

## Akzeptanzkriterien

### Beobachtbarkeit (cached_tokens)
- [ ] `protokoll_log.merke_usage` liest `usage.prompt_tokens_details.cached_tokens` aus und legt
      es zusätzlich zu prompt/completion/total im Usage-Slot ab (Default `0`, wenn das Feld fehlt).
- [ ] Die Token-Statistik in `protokolle/<vid>.md` (PROJ-28, `_token_markdown`) weist
      `cached_tokens` **und** eine Cache-Trefferquote `cached_tokens / prompt_tokens` (in %,
      0 % wenn `prompt_tokens == 0`) aus.
- [ ] `orchestrator._merke_usage` nimmt `cached_tokens` zusätzlich in den
      `state['entscheidungsprotokoll']`-Usage-Eintrag jeder Iteration auf.
- [ ] Pro Turn wird **eine** INFO-Zeile geloggt (`repair.orchestrator`) mit
      prompt/cached/completion-Tokens + Trefferquote + Vorgang-ID — **keine** Klartext-Eingaben
      (PII-Leitlinie PROJ-29).

### prompt_cache_key (statisch je Sprache)
- [ ] `client.chat.completions.create(...)` in `run_turn` erhält einen `prompt_cache_key`, der
      **nur** von der Sprache abhängt (z. B. `"<präfix>-de"` / `"<präfix>-en"`), nicht von der
      `vorgang_id` — damit verschiedene Vorgänge derselben Sprache denselben Schlüssel teilen.
- [ ] Das Key-Präfix ist über `.env` konfigurierbar (Default sinnvoll, z. B. `repair`),
      gelesen über einen Getter in `repair/config.py`, dokumentiert in `.env.example`.
- [ ] Ein `.env`-Schalter erlaubt es, den expliziten Key abzuschalten (dann nur Auto-Caching,
      kein `prompt_cache_key` im Call) — Default „an".
- [ ] Ist der explizite Key aus oder die Sprache unbekannt, bricht nichts; bei unbekannter
      Sprache greift derselbe Fallback wie bei der Sprachdirektive (`de`).

### Prefix-Stabilität härten
- [ ] Ein Guard-Test (analog `tests/test_config_drift.py`) pinnt die Byte-Repräsentation von
      `system_prefix("de")`, `system_prefix("en")` und `tools.specs()` und schlägt bei
      Abweichung mit klarer, benennender Meldung an.
- [ ] Der Test macht explizit, dass eine **bewusste** Präfix-Änderung erlaubt ist (Pin wird im
      selben Commit mitgezogen) — er verhindert nur **unbeabsichtigten** Drift.
- [ ] Der Test prüft, dass `sende_sicht(system_prefix(lang), state)` den Präfix unverändert und
      als echtes Listen-Präfix voranstellt (keine Mutation, keine Umordnung der ersten N
      System-Messages).

### Allgemein / Konfiguration
- [ ] Alle neuen `.env`-Werte sind in `repair/config.py` zentral getypt/validiert (PROJ-30) und
      in `.env.example` mit Default-Hinweis dokumentiert; `test_config_drift.py` bleibt grün
      (kein Drift, kein Hardcode).
- [ ] Die App startet weiterhin ohne `.env` (sinnvolle Defaults) und ohne Backend sauber
      (`no_backend`-Pfad unverändert).

## Edge Cases
- **Älteres SDK / fehlendes `prompt_tokens_details`:** `cached_tokens` als `0` behandeln, kein
  Crash, kein `AttributeError` — best-effort wie die übrige Usage-Erfassung.
- **`prompt_tokens_details` vorhanden, `cached_tokens` `None`:** als `0` werten.
- **Modell ohne Caching-Unterstützung** (nur bestimmte Modelle cachen automatisch): `cached_tokens`
  bleibt `0` — das ist **kein** Fehler, sondern korrekt ausgewiesen (0 % Trefferquote).
- **Prompt < ~1024 Tokens:** wird von OpenAI nie gecacht → `cached_tokens = 0`, erwartet, kein
  Warnsignal.
- **SDK akzeptiert `prompt_cache_key` nicht** (sehr alte Version): der Call darf nicht hart
  scheitern — Übergabe defensiv (z. B. nur senden, wenn unterstützt / `extra_body`-tauglich),
  sonst sauberer Fallback auf Auto-Caching.
- **Nicht-OpenAI-kompatibles Backend** (Test-Doubles in `run_turn` über `client=`-Injektion):
  Tests injizieren Clients ohne `prompt_cache_key`-Akzeptanz → die Übergabe darf solche Tests
  nicht brechen.
- **`prompt_tokens == 0`** (Degradations-/Fehlerfall): Trefferquote als 0 % ausweisen statt
  Division durch Null.
- **Mehrere Tool-Iterationen pro Turn:** jede `create()`-Runde liefert eigene `cached_tokens`;
  die spätere Iteration (mit längerem, schon gesehenem Verlauf) hat typischerweise höhere
  Trefferquote — alle Iterationen landen im `entscheidungsprotokoll`, die INFO-Zeile fasst den
  Turn sinnvoll zusammen (z. B. letzte Runde oder Summe — bei Umsetzung festlegen).
- **Caching abgeschaltet (`.env`):** kein `prompt_cache_key` im Call; Beobachtbarkeit läuft
  trotzdem weiter (Auto-Caching kann auch ohne expliziten Key greifen).
- **Multimodale Calls** (`multimodal.py`, Vision/Whisper): Whisper hat keine Token-/Cache-Statistik;
  Vision ist **kein** Teil dieses Features (Fokus: Orchestrator-Chat-Call). Falls später gewünscht,
  separater Nachtrag.

## Technische Anforderungen (optional)
- **Keine neue Dependency** — `cached_tokens` kommt aus dem vorhandenen OpenAI-`usage`-Objekt;
  keine Tokenizer-Bibliothek (die Trefferquote nutzt die von OpenAI gelieferten Zahlen, keine
  eigene Schätzung).
- **Best-effort & nicht-blockierend** — die Cache-Erfassung darf (wie das gesamte Protokoll,
  PROJ-28) die HTTP-Antwort und die Fachlogik nie gefährden; jeder Fehler wird verschluckt.
- **Keine PII im Log** — nur Zahlen + Vorgang-ID, keine Nutzereingaben (PROJ-29).
- **Byte-Stabilität** — `system_prefix()` und `tools.specs()` bleiben deterministisch/stabil
  sortiert; die Sprachdirektive bleibt separate, letzte System-Message.

---
<!-- Folgende Abschnitte werden von nachfolgenden Skills hinzugefügt -->

## Tech Design (Solution Architect)
_Wird von /architecture hinzugefügt_

## QA Test Results
_Wird von /qa hinzugefügt_

## Deployment
_Wird von /deploy hinzugefügt_
