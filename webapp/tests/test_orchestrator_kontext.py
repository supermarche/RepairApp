"""Tests für PROJ-41: Kontext-Verdichtung & Token-Budget der Orchestrierung.

Prüft die verdichtete Sende-Sicht (repair/kontext.sende_sicht) im Zusammenspiel
mit dem Orchestrator: Rollen-Volltext-Entladung, Verlaufs-Digest, strukturelle
Gültigkeit der Sende-Liste, Erhalt der Backstop-Hinweise/Medien-Evidenz,
Token-Wachstum sowie Byte-Stabilität des System-Präfix. Reine Python-Unit-Tests
(kein Browser, kein echter API-Call — FakeClient schneidet die messages mit).
"""
from __future__ import annotations

import os
import sys

WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WEBAPP not in sys.path:
    sys.path.insert(0, WEBAPP)

from repair import orchestrator, kontext, config  # noqa: E402


# ── Mini-Fakes (analog test_orchestrator_loop) ────────────────────────────────
class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class _ToolCall:
    def __init__(self, cid, name, args):
        self.id = cid
        self.type = "function"
        self.function = type("F", (), {"name": name, "arguments": args})


class _Choice:
    def __init__(self, msg): self.message = msg


class _Resp:
    def __init__(self, msg): self.choices = [_Choice(msg)]


class RecordingClient:
    """Beantwortet jeden Turn sofort mit Text und schneidet je create() die
    gesendeten messages mit (Liste von Snapshots)."""
    def __init__(self, antwort="Verstanden."):
        self.calls = 0
        self.gesehen: list[list] = []
        self.antwort = antwort
        self.chat = type("C", (), {"completions": self})()

    def create(self, **kw):
        self.calls += 1
        self.gesehen.append(kw.get("messages"))
        return _Resp(_Msg(content=self.antwort))


def _struktur_gueltig(messages: list[dict]) -> bool:
    """Jede assistant-Nachricht mit tool_calls muss von tool-Antworten für JEDE
    tool_call_id gefolgt sein; kein verwaister tool_call_id."""
    erwartet: list[str] = []  # offene tool_call_ids in Reihenfolge
    for msg in messages:
        role = msg.get("role")
        if role == "tool":
            tcid = msg.get("tool_call_id")
            if tcid not in erwartet:
                return False  # verwaiste tool-Antwort
            erwartet.remove(tcid)
        else:
            if erwartet:
                return False  # offene tool_calls nicht direkt beantwortet
            if role == "assistant":
                for tc in msg.get("tool_calls") or []:
                    erwartet.append(tc["id"])
    return not erwartet


# ── Edge Case: kurzer Vorgang → unverändert ───────────────────────────────────
def test_kurzer_vorgang_unveraendert():
    prefix = orchestrator.system_prefix("de")
    state = {"messages": [
        {"role": "user", "content": "Toaster kaputt"},
        {"role": "assistant", "content": "Was genau?"},
        {"role": "user", "content": "Wird nicht warm"},
    ], "karten": []}
    sicht = kontext.sende_sicht(prefix, state)
    assert sicht == prefix + state["messages"]  # exakt prefix + voller Verlauf


def test_leerer_verlauf_nur_prefix():
    prefix = orchestrator.system_prefix("de")
    assert kontext.sende_sicht(prefix, {"messages": [], "karten": []}) == prefix


# ── Rollen-Volltext-Entladung ─────────────────────────────────────────────────
def _verlauf_mit_zwei_rollen(volltext_diag: str, volltext_bew: str) -> list[dict]:
    """Baut einen Verlauf: lade_rolle('diagnose') früh, später lade_rolle('bewertung')."""
    return [
        {"role": "user", "content": "Mein Laptop startet nicht."},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "r1", "type": "function",
                         "function": {"name": "lade_rolle",
                                      "arguments": '{"name":"diagnose"}'}}]},
        {"role": "tool", "tool_call_id": "r1", "content": volltext_diag},
        {"role": "assistant", "content": "Diagnose läuft."},
        {"role": "user", "content": "Und jetzt?"},
        {"role": "assistant", "content": "Weiter."},
        {"role": "user", "content": "Bewerte das mal."},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "r2", "type": "function",
                         "function": {"name": "lade_rolle",
                                      "arguments": '{"name":"bewertung"}'}}]},
        {"role": "tool", "tool_call_id": "r2", "content": volltext_bew},
        {"role": "assistant", "content": "Bewertung folgt."},
        {"role": "user", "content": "Ok danke."},
    ]


def test_alte_rolle_entladen_aktive_bleibt():
    volltext_diag = "DIAGNOSE-VOLLTEXT " * 80
    volltext_bew = "BEWERTUNG-VOLLTEXT " * 80
    state = {
        "messages": _verlauf_mit_zwei_rollen(volltext_diag, volltext_bew),
        "karten": [], "geladene_rollen": ["diagnose", "bewertung"],
    }
    # woertlich_turns=1 erzwingt Verdichtung; alle Turns liegen aber im jungen Bereich
    # sobald Budget groß genug — hier groß, damit Rollen-Tools wörtlich im jungen Teil
    # landen und die Entladung (nicht der Digest) greift.
    os.environ["KONTEXT_WOERTLICH_TURNS"] = "10"
    os.environ["KONTEXT_TOKEN_BUDGET"] = "1000000"
    try:
        prefix = orchestrator.system_prefix("de")
        sicht = kontext.sende_sicht(prefix, state)
    finally:
        os.environ.pop("KONTEXT_WOERTLICH_TURNS", None)
        os.environ.pop("KONTEXT_TOKEN_BUDGET", None)

    body = "\n".join(str(m.get("content") or "") for m in sicht)
    # Diagnose ist NICHT mehr aktiv (bewertung ist die letzte) → Volltext entladen.
    assert "DIAGNOSE-VOLLTEXT" not in body
    assert "lade_rolle('diagnose')" in body  # Verweis statt Volltext
    # bewertung ist die aktive Rolle → Volltext bleibt.
    assert "BEWERTUNG-VOLLTEXT" in body
    # tool_call_id-Struktur bleibt gültig.
    assert _struktur_gueltig(sicht)
    # state-Verlauf wurde NICHT mutiert.
    assert "DIAGNOSE-VOLLTEXT" in "".join(
        str(m.get("content") or "") for m in state["messages"])


def test_rollen_volltext_nicht_in_jedem_folge_turn():
    """Akzeptanz: ein geladener Rollen-Volltext wird nicht in jedem Turn voll gesendet."""
    volltext = "DIAGNOSE-VOLLTEXT-MARKER " * 100
    state = {
        "messages": _verlauf_mit_zwei_rollen(volltext, "BEW " * 100),
        "karten": [], "geladene_rollen": ["diagnose", "bewertung"],
    }
    client = RecordingClient()
    orchestrator.run_turn(state, "Noch eine Info.", client=client, model="x")
    gesendet = client.gesehen[0]
    body = "\n".join(str(m.get("content") or "") for m in gesendet)
    assert "DIAGNOSE-VOLLTEXT-MARKER" not in body
    assert _struktur_gueltig(gesendet)


# ── Verlaufs-Digest bei langem Vorgang ────────────────────────────────────────
def _langer_verlauf(n_turns: int) -> list[dict]:
    msgs: list[dict] = []
    for i in range(n_turns):
        msgs.append({"role": "user", "content": f"Nachricht Nummer {i} vom Nutzer."})
        msgs.append({"role": "assistant", "content": f"Antwort {i} vom Assistenten."})
    return msgs


def test_langer_vorgang_wird_verdichtet_juengste_woertlich():
    os.environ["KONTEXT_WOERTLICH_TURNS"] = "3"
    os.environ["KONTEXT_TOKEN_BUDGET"] = "1000"
    try:
        prefix = orchestrator.system_prefix("de")
        state = {
            "messages": _langer_verlauf(10),
            "karten": [{"typ": "aufnahme",
                        "daten": {"symptom": "startet nicht", "kategorie": "Laptop"}}],
            "geladene_rollen": [],
        }
        sicht = kontext.sende_sicht(prefix, state)
    finally:
        os.environ.pop("KONTEXT_WOERTLICH_TURNS", None)
        os.environ.pop("KONTEXT_TOKEN_BUDGET", None)

    body = "\n".join(str(m.get("content") or "") for m in sicht)
    # Digest vorhanden, direkt nach dem Präfix.
    assert "Verdichteter Vorgangs-Stand" in body
    digest_idx = next(i for i, m in enumerate(sicht)
                      if "Verdichteter Vorgangs-Stand" in str(m.get("content") or ""))
    assert digest_idx == len(prefix)  # genau nach dem System-Präfix
    # Jüngste Nachrichten wörtlich enthalten.
    assert "Nachricht Nummer 9 vom Nutzer." in body
    assert "Antwort 9 vom Assistenten." in body
    # Älteste Nachricht NICHT mehr wörtlich.
    assert "Nachricht Nummer 0 vom Nutzer." not in body
    # Erkanntes Gerät im Digest.
    assert "Laptop" in body
    assert _struktur_gueltig(sicht)


def test_genau_ein_digest():
    os.environ["KONTEXT_WOERTLICH_TURNS"] = "2"
    try:
        prefix = orchestrator.system_prefix("de")
        state = {"messages": _langer_verlauf(8), "karten": [], "geladene_rollen": []}
        sicht = kontext.sende_sicht(prefix, state)
    finally:
        os.environ.pop("KONTEXT_WOERTLICH_TURNS", None)
    digests = [m for m in sicht
               if "Verdichteter Vorgangs-Stand" in str(m.get("content") or "")]
    assert len(digests) == 1


# ── Backstop-/Sicherheits-Hinweise + Medien-Evidenz im Digest ─────────────────
def test_backstop_hinweis_bleibt_im_digest():
    os.environ["KONTEXT_WOERTLICH_TURNS"] = "1"
    try:
        prefix = orchestrator.system_prefix("de")
        state = {
            "messages": _langer_verlauf(6),
            "karten": [{"typ": "hinweis", "daten": {
                "art": "sicherheit", "schwere": "kritisch",
                "text": "Stromschlaggefahr — vor jedem Eingriff Netzstecker ziehen."}}],
            "geladene_rollen": [], "medien": ["m1", "m2"],
        }
        sicht = kontext.sende_sicht(prefix, state)
    finally:
        os.environ.pop("KONTEXT_WOERTLICH_TURNS", None)
    body = "\n".join(str(m.get("content") or "") for m in sicht)
    assert "WICHTIGER HINWEIS" in body
    assert "Stromschlaggefahr" in body          # Sicherheits-Hinweis erhalten
    assert "Medien-Evidenz" in body             # PROJ-31 referenziert
    assert "2 Foto" in body


# ── Token-Wachstum: spät < naiv-kumulativ ─────────────────────────────────────
def test_token_wachstum_langsamer_als_kumulativ():
    os.environ["KONTEXT_WOERTLICH_TURNS"] = "3"
    os.environ["KONTEXT_TOKEN_BUDGET"] = "2000"
    try:
        prefix = orchestrator.system_prefix("de")
        # langer Verlauf mit großen Nachrichten (simuliert wachsende Tokenmenge)
        msgs = []
        for i in range(12):
            msgs.append({"role": "user", "content": f"Frage {i} " + "x" * 400})
            msgs.append({"role": "assistant", "content": f"Antwort {i} " + "y" * 400})
        state = {"messages": msgs, "karten": [], "geladene_rollen": []}
        sicht = kontext.sende_sicht(prefix, state)
    finally:
        os.environ.pop("KONTEXT_WOERTLICH_TURNS", None)
        os.environ.pop("KONTEXT_TOKEN_BUDGET", None)

    geschaetzt = sum(kontext._msg_tokens(m) for m in sicht)
    naiv = sum(kontext._msg_tokens(m) for m in prefix) + \
        sum(kontext._msg_tokens(m) for m in state["messages"])
    assert geschaetzt < naiv  # verdichtet ist kleiner als prefix + voller Verlauf


# ── System-Präfix byte-stabil ─────────────────────────────────────────────────
def test_system_prefix_byte_stabil():
    a = orchestrator.system_prefix("de")
    b = orchestrator.system_prefix("de")
    assert a == b
    prefix = orchestrator.system_prefix("de")
    state = {"messages": _langer_verlauf(8), "karten": [], "geladene_rollen": []}
    os.environ["KONTEXT_WOERTLICH_TURNS"] = "2"
    try:
        sicht = kontext.sende_sicht(prefix, state)
    finally:
        os.environ.pop("KONTEXT_WOERTLICH_TURNS", None)
    # Die ersten len(prefix) Nachrichten der Sende-Sicht sind unverändert das Präfix.
    assert sicht[: len(prefix)] == prefix
    # system_prefix wurde durch sende_sicht nicht mutiert.
    assert orchestrator.system_prefix("de") == a


# ── Budget zu klein → Mindest-Kontext garantiert ──────────────────────────────
def test_budget_zu_klein_mindestkontext():
    os.environ["KONTEXT_WOERTLICH_TURNS"] = "2"
    os.environ["KONTEXT_TOKEN_BUDGET"] = "500"  # minimal erlaubt
    try:
        prefix = orchestrator.system_prefix("de")
        msgs = []
        for i in range(10):
            msgs.append({"role": "user", "content": f"U{i} " + "z" * 2000})
            msgs.append({"role": "assistant", "content": f"A{i} " + "w" * 2000})
        state = {"messages": msgs, "karten": [], "geladene_rollen": []}
        sicht = kontext.sende_sicht(prefix, state)
    finally:
        os.environ.pop("KONTEXT_WOERTLICH_TURNS", None)
        os.environ.pop("KONTEXT_TOKEN_BUDGET", None)
    body = "\n".join(str(m.get("content") or "") for m in sicht)
    # Trotz winzigem Budget: Digest + jüngste woertlich_turns Turns bleiben.
    assert "Verdichteter Vorgangs-Stand" in body
    assert "U9 " in body and "A9 " in body
    assert "U8 " in body  # = 2 wörtliche Turns
    assert _struktur_gueltig(sicht)


# ── Re-Disclosure: Rolle später erneut ladbar ─────────────────────────────────
def test_re_disclosure_verweis_nennt_lade_rolle():
    state = {
        "messages": _verlauf_mit_zwei_rollen("DIAG " * 50, "BEW " * 50),
        "karten": [], "geladene_rollen": ["diagnose", "bewertung"],
    }
    os.environ["KONTEXT_TOKEN_BUDGET"] = "1000000"
    os.environ["KONTEXT_WOERTLICH_TURNS"] = "10"
    try:
        prefix = orchestrator.system_prefix("de")
        sicht = kontext.sende_sicht(prefix, state)
    finally:
        os.environ.pop("KONTEXT_TOKEN_BUDGET", None)
        os.environ.pop("KONTEXT_WOERTLICH_TURNS", None)
    body = "\n".join(str(m.get("content") or "") for m in sicht)
    assert "lade_rolle('diagnose')" in body  # Re-Disclosure-Hinweis


# ── Config: Defaults + Fail-fast (analog test_vision/test_config_drift) ────────
def test_config_defaults():
    for var in ("KONTEXT_TOKEN_BUDGET", "KONTEXT_WOERTLICH_TURNS"):
        os.environ.pop(var, None)
    assert config.kontext_token_budget() == config.DEFAULT_KONTEXT_TOKEN_BUDGET
    assert config.kontext_woertlich_turns() == config.DEFAULT_KONTEXT_WOERTLICH_TURNS
    config.validate()  # darf nicht werfen


def _expect_fail(var: str, value: str):
    old = os.environ.get(var)
    os.environ[var] = value
    try:
        try:
            config.validate()
        except config.ConfigError as exc:
            assert var in str(exc)
            return
        raise AssertionError(f"{var}={value!r} hätte Fail-fast auslösen müssen")
    finally:
        if old is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = old


def test_config_fail_fast_kontext():
    _expect_fail("KONTEXT_TOKEN_BUDGET", "abc")
    _expect_fail("KONTEXT_TOKEN_BUDGET", "10")        # < 500
    _expect_fail("KONTEXT_TOKEN_BUDGET", "2000000")   # > 1_000_000
    _expect_fail("KONTEXT_WOERTLICH_TURNS", "0")      # < 1
    _expect_fail("KONTEXT_WOERTLICH_TURNS", "999")    # > 100
    _expect_fail("KONTEXT_WOERTLICH_TURNS", "xyz")
