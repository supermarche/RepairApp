"""Kontext-Verdichtung & Token-Budget der Orchestrierung (PROJ-41).

Pro Turn wird nicht mehr der gesamte Verlauf (``state["messages"]``) an OpenAI
gesendet. Stattdessen baut ``sende_sicht()`` aus dem vollständigen Audit-Verlauf
eine **verdichtete Sende-Sicht**:

- ``state["messages"]`` bleibt UNANGETASTET (vollständiger Audit-/Persistenz-Verlauf).
- (a) **Rollen-Volltext-Entladung:** tool-Messages, die Ergebnis eines
  ``lade_rolle``-Calls sind, werden — bis auf die zuletzt geladene (aktive) Rolle —
  durch einen kompakten Verweis ersetzt (content gekürzt, ``tool_call_id`` bleibt,
  damit die tool_call↔tool-Pairing-Struktur gültig bleibt). Re-Disclosure jederzeit
  via erneutem ``lade_rolle`` möglich.
- (b) **Verlaufs-Digest:** Der Verlauf wird an User-Nachrichten-Grenzen in „Turns"
  geteilt. Die jüngsten ``KONTEXT_WOERTLICH_TURNS`` Turns bleiben WÖRTLICH. Ältere
  Turns werden zu GENAU EINER kompakten system-Digest-Nachricht zusammengefasst
  (erkanntes Gerät, Symptome, gezeigte Karten, Entscheidungen, Medien-Evidenz und —
  verbindlich — aktive Sicherheits-/Garantie-/Rückruf-/Eigentums-/Datenlöschungs-
  Hinweise aus ``state["karten"]``, PROJ-36/Backstop). Der Digest wird direkt nach
  dem (unveränderten, cachebaren) System-Präfix eingefügt.

Heuristisch, OHNE zusätzliche KI-Runde — robust und ohne API-Call testbar. Die
Token-Schätzung ist bewusst grob (``~len/4``); keine Tokenizer-Dependency.

OpenAI-Strukturregel beachtet: Eine assistant-Nachricht mit ``tool_calls`` muss von
tool-Antworten für JEDE ``tool_call_id`` gefolgt sein. Daher werden nur VOLLSTÄNDIGE
Turns (assistant+tool-Paare gemeinsam) wegverdichtet — nie ein Paar zerrissen.
"""
from __future__ import annotations

import json

from . import config


def _tokens(text: str) -> int:
    """Grobe, abhängigkeitsfreie Token-Schätzung (~4 Zeichen/Token)."""
    return (len(text) + 3) // 4


def _msg_tokens(msg: dict) -> int:
    """Geschätzte Tokens einer Nachricht inkl. tool_calls-Argumente."""
    total = _tokens(str(msg.get("content") or "")) + 4  # kleiner Rollen-/Meta-Overhead
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function", {})
        total += _tokens(str(fn.get("name", ""))) + _tokens(str(fn.get("arguments", "")))
    return total


def _aktive_rolle(messages: list[dict]) -> str | None:
    """Name der zuletzt via lade_rolle geladenen (= aktiven) Rolle, falls vorhanden."""
    aktiv = None
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        for tc in msg.get("tool_calls") or []:
            if tc.get("function", {}).get("name") == "lade_rolle":
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except (ValueError, TypeError):
                    args = {}
                if args.get("name"):
                    aktiv = args["name"]
    return aktiv


def _lade_rolle_tool_call_ids(messages: list[dict]) -> dict[str, str]:
    """tool_call_id -> Rollenname für alle lade_rolle-Aufrufe im Verlauf."""
    out: dict[str, str] = {}
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        for tc in msg.get("tool_calls") or []:
            if tc.get("function", {}).get("name") == "lade_rolle":
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except (ValueError, TypeError):
                    args = {}
                if tc.get("id"):
                    out[tc["id"]] = args.get("name") or "?"
    return out


def _entlade_rollen(messages: list[dict], aktive_rolle: str | None) -> list[dict]:
    """Ersetzt den content von lade_rolle-tool-Messages durch einen Verweis.

    Ausnahme: die LETZTE tool-Message zur aktiven Rolle behält ihren Volltext.
    Nur der content wird gekürzt — Message + tool_call_id bleiben erhalten.
    """
    rolle_je_id = _lade_rolle_tool_call_ids(messages)
    if not rolle_je_id:
        return messages

    # tool_call_id der ZULETZT geladenen aktiven Rolle bestimmen (Volltext behalten).
    aktive_id = None
    for msg in messages:
        if msg.get("role") == "tool" and msg.get("tool_call_id") in rolle_je_id:
            if rolle_je_id[msg["tool_call_id"]] == aktive_rolle:
                aktive_id = msg["tool_call_id"]

    out: list[dict] = []
    for msg in messages:
        if (msg.get("role") == "tool"
                and msg.get("tool_call_id") in rolle_je_id
                and msg.get("tool_call_id") != aktive_id):
            rolle = rolle_je_id[msg["tool_call_id"]]
            verweis = (f"[Rolle '{rolle}' wurde geladen — Volltext zur Token-Ersparnis "
                       f"entladen; bei Bedarf erneut lade_rolle('{rolle}').]")
            out.append({**msg, "content": verweis})
        else:
            out.append(msg)
    return out


def _split_turns(messages: list[dict]) -> list[list[dict]]:
    """Teilt den Verlauf an user-Nachrichten-Grenzen in Turns.

    Ein Turn beginnt mit einer user-Nachricht und umfasst die darauf folgenden
    assistant/tool-Nachrichten bis zur nächsten user-Nachricht. Nachrichten vor
    der ersten user-Nachricht bilden einen führenden „Turn" (selten).
    """
    turns: list[list[dict]] = []
    cur: list[dict] = []
    for msg in messages:
        if msg.get("role") == "user" and cur:
            turns.append(cur)
            cur = [msg]
        else:
            cur.append(msg)
    if cur:
        turns.append(cur)
    return turns


def _kurz(text: str, n: int = 160) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _digest_text(alte_turns: list[list[dict]], state: dict) -> str:
    """Baut die kompakte Zustands-Zusammenfassung der weggekürzten Turns.

    Quellen: state["karten"] (gezeigte Karten inkl. Backstop-Hinweise, PROJ-36),
    geladene Rollen und die User-Eingaben der verdichteten Turns (roter Faden).
    """
    karten = state.get("karten") or []
    zeilen: list[str] = [
        "[Verdichteter Vorgangs-Stand — ältere Nachrichten zusammengefasst, "
        "jüngste folgen wörtlich:]"
    ]

    # Erkanntes Gerät / Symptome aus der jüngsten aufnahme-Karte.
    aufnahme = next((k for k in reversed(karten) if k.get("typ") == "aufnahme"), None)
    if aufnahme:
        d = aufnahme.get("daten", {})
        teile = []
        if d.get("kategorie"):
            teile.append(f"Gerät/Kategorie: {_kurz(d['kategorie'], 80)}")
        if d.get("symptom"):
            teile.append(f"Symptom: {_kurz(d['symptom'])}")
        if d.get("seit_wann"):
            teile.append(f"seit: {_kurz(d['seit_wann'], 60)}")
        eig = d.get("eigentum") or {}
        if eig.get("ist_eigentuemer") is False:
            teile.append("Nutzer ist NICHT Eigentümer")
        if teile:
            zeilen.append("- " + "; ".join(teile))

    # Diagnose-Kandidaten (Kernaussagen).
    diagnose = next((k for k in reversed(karten) if k.get("typ") == "diagnose"), None)
    if diagnose:
        kand = diagnose.get("daten", {}).get("kandidaten") or []
        namen = [_kurz(k.get("name") or k.get("titel") or k.get("ursache") or "", 60)
                 for k in kand if isinstance(k, dict)]
        namen = [n for n in namen if n]
        if namen:
            zeilen.append("- Diagnose-Kandidaten: " + ", ".join(namen[:5]))

    # Ampel-Einschätzungen (Defekt + Gesamt).
    ampeln = [k for k in karten if k.get("typ") == "ampel"]
    for a in ampeln[-3:]:
        d = a.get("daten", {})
        defekt = _kurz(d.get("defekt") or "Einschätzung", 50)
        zeilen.append(f"- Ampel ({defekt}): gesamt={d.get('gesamt', '?')}, "
                      f"sicherheit={d.get('achsen', {}).get('sicherheit', '?')}")

    # Übrige gezeigte Karten-Typen (Überblick), ohne die schon genannten.
    schon = {"aufnahme", "diagnose", "ampel", "hinweis"}
    weitere = sorted({k.get("typ") for k in karten if k.get("typ") not in schon})
    if weitere:
        zeilen.append("- Bereits gezeigte Karten: " + ", ".join(weitere))

    # VERBINDLICH: aktive Sicherheits-/Garantie-/Rückruf-/Eigentums-/Datenlösch-
    # Hinweise (Backstop, PROJ-36) dürfen NIE verloren gehen.
    hinweise = [k for k in karten if k.get("typ") == "hinweis"]
    if hinweise:
        for h in hinweise:
            d = h.get("daten", {})
            zeilen.append(f"- WICHTIGER HINWEIS ({d.get('art', '?')}, "
                          f"{d.get('schwere', 'info')}): {_kurz(d.get('text'), 140)}")

    # Medien-Evidenz (PROJ-31) referenziert lassen.
    medien = state.get("medien")
    if isinstance(medien, list) and medien:
        zeilen.append(f"- Medien-Evidenz: {len(medien)} Foto(s)/Dokument(e) beigefügt "
                      "(per extrahiere_aus_medien auswertbar).")

    # Geladene Rollen (Re-Disclosure-Hinweis).
    rollen = state.get("geladene_rollen") or []
    if rollen:
        zeilen.append("- Bisher genutzte Rollen: "
                      + ", ".join(sorted(set(rollen)))
                      + " (bei Bedarf via lade_rolle erneut ladbar).")

    # Roter Faden: die User-Eingaben der verdichteten Turns.
    user_eingaben = []
    for turn in alte_turns:
        for msg in turn:
            if msg.get("role") == "user" and msg.get("content"):
                user_eingaben.append(_kurz(msg["content"], 120))
    if user_eingaben:
        zeilen.append("- Nutzer-Verlauf (gekürzt): " + " | ".join(user_eingaben[-6:]))

    return "\n".join(zeilen)


def sende_sicht(prefix: list[dict], state: dict) -> list[dict]:
    """Baut die zu sendende Nachrichtenliste: prefix + (Digest?) + verdichteter Verlauf.

    ``state["messages"]`` wird NICHT mutiert. ``prefix`` (system_prefix) bleibt
    byte-stabil und unverändert vorangestellt.
    """
    messages = state.get("messages") or []
    if not messages:
        return list(prefix)

    woertlich_turns = config.kontext_woertlich_turns()
    budget = config.kontext_token_budget()

    turns = _split_turns(messages)
    aktive_rolle = _aktive_rolle(messages)

    # Rollen-Volltext-Entladung läuft IMMER (auch bei kurzem Vorgang ohne Digest):
    # der größte Einzelposten — ältere, nicht mehr aktive Rollen-Volltexte — wird
    # auch dann nicht in jedem Folge-Turn voll gesendet, wenn (noch) keine
    # Verlaufs-Verdichtung nötig ist.
    entladen = _entlade_rollen(list(messages), aktive_rolle)

    # Edge Case: kurzer Vorgang unter Schwelle → KEINE Verlaufs-Verdichtung
    # (nur Rollen-Entladung, die strukturneutral ist und nur den content kürzt).
    if len(turns) <= woertlich_turns:
        return list(prefix) + entladen

    # Wieviele jüngste Turns wörtlich behalten? Höchstens woertlich_turns (mehr
    # NIE — sonst entfiele der Digest). Das Budget ist eine weiche OBERgrenze: ist
    # selbst dieser jüngste Block größer als das Budget, wird er auf weniger Turns
    # gekürzt — aber MINDESTENS ein Turn bleibt garantiert wörtlich (Mindest-Kontext).
    behalten = min(woertlich_turns, len(turns) - 1)  # mind. 1 alter Turn → Digest
    while behalten > 1:
        kosten = sum(_msg_tokens(m) for t in turns[-behalten:] for m in t)
        if kosten <= budget:
            break
        behalten -= 1

    # Turns auf der entladenen Sicht neu aufteilen (gleiche Grenzen, gekürzte
    # Rollen-Volltexte). So bleibt die tool_call↔tool-Pairing-Struktur gültig.
    turns_entladen = _split_turns(entladen)
    alte_turns = turns_entladen[:-behalten]
    junge_turns = turns_entladen[-behalten:]

    verlauf: list[dict] = []
    if alte_turns:
        verlauf.append({"role": "system", "content": _digest_text(alte_turns, state)})
    verlauf.extend(m for t in junge_turns for m in t)

    return list(prefix) + verlauf
