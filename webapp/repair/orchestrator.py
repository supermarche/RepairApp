"""LLM-Orchestrator: führt die Tool-Call-Schleife gegen die ChatGPT-API.

Stabiler System-Präfix (Leitlinien + Rollen-Katalog + Werkzeug-Hinweis) zuerst,
damit OpenAIs automatisches Prefix-Caching greift. Volltexte der Rollen kommen
on-demand über lade_rolle() NACH dem Präfix.

Die Sprachdirektive (D17) wird als zusätzliche system-Message ANS ENDE des
Präfix gehängt — so bleibt jeder Sprach-Präfix für sich byte-stabil und separat
cachebar (kein Drift bei jeder Spec-Änderung).
"""
from __future__ import annotations

import json

from . import roles, tools, config, protokoll_log
from .ai import _resolve_backend  # Backend-Auflösung wiederverwenden

# Kompakte, STABILE Ableitung aus runtime-roles/lotse.md (nicht der Volltext —
# sonst Cache-Drift bei jeder Spec-Änderung). Volltext via lade_rolle("lotse").
_LEITLINIEN = """\
Du bist der „Reparatur-Helfer", ein orchestrierender Lotse. Du führst den Nutzer \
durch seinen Reparaturfall, indem du spezialisierte Fach-Rollen lädst und nutzt.

GRUNDHALTUNG (verbindlich):
- WARNEN STATT SPERREN: Du sperrst NICHTS. Auch bei gefährlichen Geräten begleitest \
du mit klaren, mit der Kritikalität ESKALIERENDEN Warnungen — der mündige Nutzer \
entscheidet. Je gefährlicher, desto deutlicher die Warnung und desto klarer die \
Empfehlung „Profi/Werkstatt".
- VERTRAUENS-INDIKATOR: Jede fachliche Einschätzung trägt Konfidenz + Begründung. \
Der Hinweis „die KI kann Fehler machen" erscheint immer, verstärkt bei Gefahr.
- EHRLICHER TON: ermutigen, aber nichts beschönigen. „Lohnt sich nicht" / „nicht \
selbst machen" klar sagen.
- PFLICHT-HINWEISE bei Bedarf (als zeige_karte typ=hinweis): Garantie/Gewährleistung \
vor dem ersten Eingriff, bekannter Rückruf, Datenlöschung vor Fremdabgabe bei \
datentragenden Geräten, Eigentum/Kostenträger wenn Nutzer ≠ Eigentümer.
- UNKLAR-PFAD: Kannst du nicht sicher eingrenzen, täusche keine Sicherheit vor — \
sag es ehrlich, das Protokoll bleibt nutzbar, leite an Profi/Café weiter.

ARBEITSWEISE:
1. Nutze den Rollen-Katalog unten, um die passende Rolle zu wählen.
2. lade_rolle(name) holt die volle Spezifikation einer Rolle in den Kontext — \
befolge sie dann genau.
3. Daten holst du über die Daten-Tools (finde_anbieter, suche_ersatzteil, \
finde_foerderung, finde_entsorgung, recherche).
4. Strukturierte Ergebnisse gibst du über zeige_karte(typ, daten) aus.
5. Dazwischen sprichst du in einfachem Deutsch mit dem Nutzer und stellst Rückfragen.

RÜCKFRAGEN (verbindlich):
- Stelle Rückfragen IMMER EINZELN über zeige_karte(typ="frage", …) — eine Karte = \
GENAU EINE Frage. Schreibe NIEMALS mehrere Fragen als nummerierte Liste in den Fließtext.
- Brauchst du mehrere Angaben, stelle die wichtigste zuerst und warte die Antwort des \
Nutzers ab, bevor du die nächste frage-Karte schickst.
- Biete in `optionen` ein paar sinnvolle, vorausgewählte Antworten an, wenn die Frage \
das zulässt (der Nutzer kann zusätzlich frei antworten — `freitext_erlaubt` ist standardmäßig an).
- Setze `bild_erlaubt:true`, wenn ein Foto/Dokument zur Beantwortung hilft (z. B. \
Typenschild, Schaden, Fehlercode).
- WICHTIG gegen Dopplung: Gibst du eine frage-Karte aus, formuliere die Frage NUR in \
der Karte. Wiederhole sie NICHT zusätzlich im normalen Antworttext — lass den \
Begleittext in diesem Schritt leer (oder höchstens ein kurzer Überleitungssatz, der \
die Frage selbst nicht enthält). Das gilt sinngemäß für alle Karten: wiederhole \
Karteninhalte nicht im Fließtext."""

_WERKZEUG_HINWEIS = """\
Karten-Typen für zeige_karte: frage, aufnahme, diagnose, ampel, vergleich, schritte, \
hinweis, anbieter, ersatzteil, erfolg. Rückfragen IMMER als einzelne frage-Karte (nie \
als Liste im Text). Bei Mehrfachdefekten: pro Defekt eine ampel-Karte plus ein \
Gesamt-Fazit nach dem schwächsten Glied."""

# Sprachdirektive (D17) — ans Ende des Präfix gehängt. Default: de.
_SPRACHDIREKTIVE = {
    "de": "Antworte auf Deutsch.",
    "en": "Answer in English.",
}


def _katalog_text() -> str:
    zeilen = ["ROLLEN-KATALOG (Name — Klasse — Beschreibung):"]
    for r in roles.katalog():
        zeilen.append(f"- {r['name']} [{r['class']}]: {r['description']}")
    return "\n".join(zeilen)


def system_prefix(lang: str = "de") -> list[dict]:
    direktive = _SPRACHDIREKTIVE.get(lang, _SPRACHDIREKTIVE["de"])
    return [
        {"role": "system", "content": _LEITLINIEN},
        {"role": "system", "content": _katalog_text()},
        {"role": "system", "content": _WERKZEUG_HINWEIS},
        {"role": "system", "content": direktive},
    ]


def run_turn(state: dict, user_text: str, *, client=None, model=None,
             max_iterations: int | None = None) -> dict:
    """Führt einen Chat-Turn aus. Mutiert state['messages'/'karten'/...].

    Liefert {"antwort_text", "karten", "abgebrochen"}.
    client/model optional injizierbar (Tests); sonst via _resolve_backend().
    """
    if client is None:
        client, model = _resolve_backend()  # FIX B2: _resolve_backend liefert 2-Tupel
        if client is None:
            return {"antwort_text": "", "karten": [], "abgebrochen": False,
                    "error": "Kein KI-Backend konfiguriert.", "code": "no_backend"}
    if max_iterations is None:
        max_iterations = config.max_tool_iterations()

    state.setdefault("messages", [])
    state.setdefault("karten", [])
    state.setdefault("geladene_rollen", [])
    state.setdefault("entscheidungsprotokoll", [])
    lang = state.get("lang", "de")

    state["messages"].append({"role": "user", "content": user_text})
    _medien_hinweis_anhaengen(state)  # PROJ-31: auf neu beigefügte Medien hinweisen
    neue_karten: list[dict] = []
    vorgang_id = state.get("vorgang_id", "")

    for _ in range(max_iterations):
        messages = system_prefix(lang) + state["messages"]
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=tools.specs(),
            temperature=0.4, timeout=config.llm_timeout())  # FIX S1: zentraler Getter, kein Duplikat
        _merke_usage(resp, model, state)  # R4: Token-Usage best-effort festhalten
        msg = resp.choices[0].message
        tool_calls = list(getattr(msg, "tool_calls", []) or [])

        # Assistant-Nachricht (inkl. evtl. Tool-Calls) in den Verlauf
        state["messages"].append(_assistant_dict(msg, tool_calls))

        if not tool_calls:
            _sicherheits_backstop(neue_karten, state)  # nicht-sperrend, D15-konform
            return {"antwort_text": msg.content or "", "karten": neue_karten,
                    "abgebrochen": False}

        for tc in tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            res = tools.dispatch(tc.function.name, args, vorgang_id=vorgang_id)
            if "karte" in res:
                neue_karten.append(res["karte"])
                state["karten"].append(res["karte"])
                tool_content = json.dumps({"ok": True, "typ": res["karte"]["typ"]},
                                          ensure_ascii=False)
            elif "error" in res:
                tool_content = json.dumps({"error": res["error"]}, ensure_ascii=False)
            else:
                tool_content = res.get("content", "")
            if tc.function.name == "lade_rolle" and "error" not in res:
                state["geladene_rollen"].append(args.get("name"))
            state["entscheidungsprotokoll"].append(
                {"tool": tc.function.name, "args": args})
            state["messages"].append({
                "role": "tool", "tool_call_id": tc.id, "content": tool_content})

    # Iterations-Limit erreicht (technisches Netz, kein fachliches Gate)
    _sicherheits_backstop(neue_karten, state)
    return {"antwort_text":
            "Ich habe viele Schritte versucht und mache hier einen Zwischenstopp. "
            "Magst du mir noch eine Info geben?",
            "karten": neue_karten, "abgebrochen": True}


def _merke_usage(resp, model, state) -> None:
    """Reicht die OpenAI-``usage`` best-effort an protokoll_log weiter (R4).

    Darf nie hart scheitern — das Protokoll ist rein beobachtend (PROJ-28).

    ``protokoll_log.merke_usage`` überschreibt nur den letzten Wert (ein
    contextvars-Slot); bei mehreren Tool-Iterationen ginge alles vor der letzten
    create()-Runde verloren. Daher legen wir die Usage je Iteration zusätzlich
    als Eintrag in ``state['entscheidungsprotokoll']`` ab (vollständige Spur).
    """
    try:
        usage = getattr(resp, "usage", None)
        if usage is None:
            return
        protokoll_log.merke_usage(model, usage)
        state.setdefault("entscheidungsprotokoll", []).append({
            "usage": {
                "model": model or "—",
                "prompt_tokens": int(_usage_attr(usage, "prompt_tokens") or 0),
                "completion_tokens": int(_usage_attr(usage, "completion_tokens") or 0),
                "total_tokens": int(_usage_attr(usage, "total_tokens") or 0),
            }
        })
    except Exception:  # noqa: BLE001 — Protokoll darf die Fachlogik nie stören
        pass


def _usage_attr(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


# Karten-Kategorien, die als datentragend gelten (D23) — Layout-Konstante.
_DATENTRAGEND = ("laptop", "notebook", "smartphone", "handy", "tablet", "pc", "computer")


def _hat_hinweis(karten: list[dict], arten: set[str]) -> bool:
    return any(k["typ"] == "hinweis" and k["daten"].get("art") in arten for k in karten)


def _sicherheits_backstop(neue_karten: list[dict], state: dict) -> None:
    """Nicht-sperrender Backstop (D15-konform: hängt NUR Hinweise an, blockiert nichts).

    Ersetzt die gestrichene deterministische stop-Mechanik des alten ai.py durch
    server-erzwungene, aber den DIY-Pfad nicht sperrende Hinweise:
      - Gefahr (ampel.sicherheit=rot ODER schritte mit danger:true) ohne
        Sicherheits-/Rückruf-Hinweis  → Sicherheits-Hinweis anhängen (A2).
      - Nutzer ≠ Eigentümer (aufnahme.eigentum.ist_eigentuemer=False) ohne
        Eigentums-Hinweis            → Eigentums-Hinweis anhängen (D14).
      - datentragendes Gerät genannt  → Datenlöschungs-Hinweis anhängen (D23).
    Hinweise werden an neue_karten UND state['karten'] angehängt.

    Dedup läuft über den GESAMTEN Vorgang (state['karten'], turn-übergreifend
    persistiert via store.py), nicht nur über den aktuellen Turn (neue_karten) —
    sonst entstünde bei erneuter roter Ampel in einem Folge-Turn ein zweiter,
    identischer Hinweis. Das Auslösen (gefahr/aufnahme) prüft hingegen nur die
    Karten DIESES Turns, damit ein Hinweis nur reagierend zum neuen Trigger kommt.
    """
    def _push(art: str, text: str, schwere: str) -> None:
        from . import cards
        karte = cards.validate("hinweis", {"art": art, "text": text, "schwere": schwere})
        neue_karten.append(karte)
        state.setdefault("karten", []).append(karte)

    bestehende = state.get("karten", [])

    gefahr = any(
        k["typ"] == "ampel" and k["daten"].get("achsen", {}).get("sicherheit") == "rot"
        for k in neue_karten
    ) or any(
        k["typ"] == "schritte"
        and any(s.get("danger") for s in k["daten"].get("schritte", []))
        for k in neue_karten
    )
    if gefahr and not _hat_hinweis(bestehende, {"sicherheit", "rueckruf"}):
        _push("sicherheit",
              "Diese Reparatur kann gefährlich sein. Im Zweifel lieber zur Fachkraft — "
              "du entscheidest selbst. (Die KI kann Fehler machen.)", "kritisch")

    # Eigentum (D14) — aus der jüngsten aufnahme-Karte
    for k in reversed(neue_karten):
        if k["typ"] == "aufnahme":
            eig = k["daten"].get("eigentum") or {}
            if eig.get("ist_eigentuemer") is False and not _hat_hinweis(bestehende, {"eigentum"}):
                _push("eigentum",
                      "Du bist nicht der Eigentümer dieses Geräts. Vor einem Eingriff "
                      "Rücksprache halten; Kostenträger klären.", "warnung")
            kat = (k["daten"].get("symptom", "") + " " +
                   str(k["daten"].get("kategorie", ""))).lower()
            if any(w in kat for w in _DATENTRAGEND) and not _hat_hinweis(bestehende, {"datenloeschung"}):
                _push("datenloeschung",
                      "Bevor du das Gerät aus der Hand gibst: Backup anlegen, Daten "
                      "löschen, Konten abmelden.", "warnung")
            break


def _medien_hinweis_anhaengen(state: dict) -> None:
    """PROJ-31 (Vision im Chat-Flow): Sind dem Vorgang Medien beigefügt, die noch
    nicht angekündigt wurden, einen knappen Hinweis an die letzte User-Nachricht
    hängen — so weiß das Modell, dass es ``extrahiere_aus_medien`` nutzen kann.
    Idempotent über Turns via ``_medien_announced`` (zählt angekündigte Medien)."""
    medien = state.get("medien")
    if not isinstance(medien, list) or not medien:
        return
    n = len(medien)
    if n <= state.get("_medien_announced", 0):
        return
    if state["messages"] and state["messages"][-1].get("role") == "user":
        state["messages"][-1]["content"] += (
            f"\n\n[Hinweis an den Assistenten: Dem Vorgang sind {n} Foto(s)/"
            f"Dokument(e) beigefügt — mit dem Tool extrahiere_aus_medien lassen sich "
            f"Gerät, Modell und Schäden daraus auslesen.]")
    state["_medien_announced"] = n


def _assistant_dict(msg, tool_calls) -> dict:
    d = {"role": "assistant", "content": msg.content or ""}
    if tool_calls:
        d["tool_calls"] = [{
            "id": tc.id, "type": "function",
            "function": {"name": tc.function.name,
                         "arguments": tc.function.arguments or "{}"}}
            for tc in tool_calls]
    return d
