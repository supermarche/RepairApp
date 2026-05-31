"""PROJ-40 (Robustheit bei API-Fehlern) + PROJ-43 (Beobachtbarkeit).

Reine Python-Unit-Tests gegen orchestrator.run_turn und protokoll_log —
kein Browser/headless.
"""
import logging

from repair import orchestrator, protokoll_log


# ─── Fake-Client-Bausteine (analog test_orchestrator_loop.py) ─────────────────


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
    def __init__(self, msg):
        self.message = msg


class _Resp:
    def __init__(self, msg):
        self.choices = [_Choice(msg)]


def _state():
    return {"messages": [], "karten": [], "geladene_rollen": [],
            "entscheidungsprotokoll": [], "vorgang_id": "vTEST123"}


# ─── PROJ-40: API-Fehler im Turn ──────────────────────────────────────────────


class _ThrowClient:
    """create() wirft sofort — simuliert BadRequest/RateLimit/Netzwerkfehler."""
    def __init__(self, exc=None):
        self.calls = 0
        self._exc = exc or RuntimeError("boom: simulierter API-Fehler")
        self.chat = type("C", (), {"completions": self})()

    def create(self, **kw):
        self.calls += 1
        raise self._exc


def test_api_fehler_in_erster_iteration_gibt_ai_error_ohne_throw():
    state = _state()
    # darf NICHT werfen
    result = orchestrator.run_turn(state, "Toaster kaputt",
                                   client=_ThrowClient(), model="x")
    assert result["code"] == "ai_error"
    assert result["error"]
    assert result["karten"] == []  # keine Karten in erster Iteration
    assert result["abgebrochen"] is False


def test_api_fehler_loggt_fehlerklasse(caplog):
    state = _state()
    with caplog.at_level(logging.WARNING, logger="repair.orchestrator"):
        orchestrator.run_turn(state, "x",
                              client=_ThrowClient(ValueError("kaputt")), model="x")
    assert any("ValueError" in r.message or "ValueError" in str(r.args)
               for r in caplog.records)


def test_timeout_wird_wie_api_fehler_behandelt():
    state = _state()
    result = orchestrator.run_turn(
        state, "x", client=_ThrowClient(TimeoutError("zeit")), model="x")
    assert result["code"] == "ai_error"


def test_api_fehler_nach_tool_call_behaelt_karten():
    # Erst ein erfolgreicher zeige_karte-Tool-Call, dann wirft create() in Runde 2.
    class HalbThrow:
        def __init__(self):
            self.calls = 0
            self.chat = type("C", (), {"completions": self})()

        def create(self, **kw):
            self.calls += 1
            if self.calls == 1:
                tc = _ToolCall("t1", "zeige_karte",
                               '{"typ":"hinweis","daten":{"art":"sicherheit",'
                               '"text":"Stecker ziehen."}}')
                return _Resp(_Msg(tool_calls=[tc]))
            raise RuntimeError("API weg")

    state = _state()
    result = orchestrator.run_turn(state, "x", client=HalbThrow(), model="x")
    assert result["code"] == "ai_error"
    assert any(k["typ"] == "hinweis" for k in result["karten"])
    # auch im persistenten State erhalten
    assert any(k["typ"] == "hinweis" for k in state["karten"])


def test_state_konsistent_nach_fehler_kein_haengender_tool_call():
    # Nach dem Fehler darf keine assistant-Nachricht mit tool_calls OHNE zugehörige
    # tool-Antworten im Verlauf stehen (sonst bricht der nächste Turn).
    state = _state()
    orchestrator.run_turn(state, "x", client=_ThrowClient(), model="x")
    for m in state["messages"]:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            raise AssertionError("hängender assistant-tool_calls-Eintrag")
    # user-Nachricht wurde angehängt, aber kein assistant-Eintrag
    assert state["messages"][-1]["role"] == "user"


def test_wiederholter_fehler_ueber_turns_kein_wachsender_korrupter_state():
    state = _state()
    client = _ThrowClient()
    orchestrator.run_turn(state, "Turn 1", client=client, model="x")
    orchestrator.run_turn(state, "Turn 2", client=client, model="x")
    # genau zwei user-Nachrichten, keine assistant/tool-Reste
    rollen = [m["role"] for m in state["messages"]]
    assert rollen == ["user", "user"]


# ─── PROJ-43: Beobachtbarkeit (Logging + Protokoll) ───────────────────────────


class _RolleUndToolClient:
    """Turn 1: lade_rolle('diagnose') + finde_foerderung; Turn-Ende: Text."""
    def __init__(self):
        self.calls = 0
        self.chat = type("C", (), {"completions": self})()

    def create(self, **kw):
        self.calls += 1
        if self.calls == 1:
            tc1 = _ToolCall("t1", "lade_rolle", '{"name":"diagnose"}')
            tc2 = _ToolCall("t2", "finde_foerderung", "{}")
            return _Resp(_Msg(tool_calls=[tc1, tc2]))
        return _Resp(_Msg(content="Fertig."))


def test_lade_rolle_loggt_auf_info_und_turn_rollen(caplog):
    state = _state()
    with caplog.at_level(logging.INFO, logger="repair.orchestrator"):
        result = orchestrator.run_turn(state, "Gerät defekt",
                                       client=_RolleUndToolClient(), model="x")
    # INFO-Eintrag mit Rolle + Vorgang-ID
    info_msgs = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert any("diagnose" in m and "vTEST123" in m for m in info_msgs)
    # turn-lokale Rollen/Tools im Ergebnis (nicht in Client-Antwort)
    assert result["_turn_rollen"] == ["diagnose"]
    namen = [t["tool"] for t in result["_turn_tools"]]
    assert "lade_rolle" in namen and "finde_foerderung" in namen
    # fachliches Ergebnis unverändert
    assert result["antwort_text"] == "Fertig."
    assert result["abgebrochen"] is False


def test_turn_ohne_rollenwechsel_leere_turn_rollen():
    class NurText:
        def __init__(self):
            self.chat = type("C", (), {"completions": self})()

        def create(self, **kw):
            return _Resp(_Msg(content="Hallo."))

    state = _state()
    result = orchestrator.run_turn(state, "x", client=NurText(), model="x")
    assert result["_turn_rollen"] == []
    assert result["_turn_tools"] == []


def test_mehrere_lade_rolle_in_reihenfolge():
    class ZweiRollen:
        def __init__(self):
            self.calls = 0
            self.chat = type("C", (), {"completions": self})()

        def create(self, **kw):
            self.calls += 1
            if self.calls == 1:
                tc1 = _ToolCall("t1", "lade_rolle", '{"name":"aufnahme"}')
                tc2 = _ToolCall("t2", "lade_rolle", '{"name":"diagnose"}')
                return _Resp(_Msg(tool_calls=[tc1, tc2]))
            return _Resp(_Msg(content="ok"))

    state = _state()
    result = orchestrator.run_turn(state, "x", client=ZweiRollen(), model="x")
    assert result["_turn_rollen"] == ["aufnahme", "diagnose"]


def test_fehlgeschlagener_tool_call_als_fehlgeschlagen_markiert():
    class BadTool:
        def __init__(self):
            self.calls = 0
            self.chat = type("C", (), {"completions": self})()

        def create(self, **kw):
            self.calls += 1
            if self.calls == 1:
                # ungültiger Karten-Typ → dispatch liefert error
                tc = _ToolCall("t1", "zeige_karte",
                               '{"typ":"gibtsnicht","daten":{}}')
                return _Resp(_Msg(tool_calls=[tc]))
            return _Resp(_Msg(content="ok"))

    state = _state()
    result = orchestrator.run_turn(state, "x", client=BadTool(), model="x")
    fehl = [t for t in result["_turn_tools"] if not t["ok"]]
    assert fehl and fehl[0]["tool"] == "zeige_karte"


def test_protokoll_weist_turn_rollen_und_tools_aus(monkeypatch, tmp_path):
    # PROJ-43: Für /api/chat steht im Protokoll die tatsächliche Rolle, nicht "lotse".
    monkeypatch.setattr(protokoll_log, "PROTOKOLL_DIR", str(tmp_path))
    monkeypatch.setenv("PROTOKOLL_ENABLED", "1")
    protokoll_log.protokolliere(
        method="POST", path="/api/chat", endpoint="api_chat",
        request_payload={"kind": "json", "json": {"text": "x"}},
        response_json={"antwort_text": "ok", "karten": [], "abgebrochen": False},
        status=200, vid="vABC123",
        turn_rollen=["diagnose"],
        turn_tools=[{"tool": "lade_rolle", "ok": True},
                    {"tool": "finde_foerderung", "ok": True}],
    )
    md = (tmp_path / "vABC123.md").read_text(encoding="utf-8")
    assert "Rolle `diagnose`" in md
    assert "Rolle `lotse`" not in md
    assert "Geladene Rollen:" in md and "`diagnose`" in md
    assert "Tool-Aufrufe:" in md and "lade_rolle" in md
    # bestehende Abschnitte bleiben rückwärts lesbar
    assert "KI-Entscheidung" in md and "Token-Statistik" in md


def test_protokoll_keine_rolle_geladen_kein_lotse_vortaeuschen(monkeypatch, tmp_path):
    monkeypatch.setattr(protokoll_log, "PROTOKOLL_DIR", str(tmp_path))
    monkeypatch.setenv("PROTOKOLL_ENABLED", "1")
    protokoll_log.protokolliere(
        method="POST", path="/api/chat", endpoint="api_chat",
        request_payload={"kind": "json", "json": {"text": "x"}},
        response_json={"antwort_text": "ok"},
        status=200, vid="vNONE99",
        turn_rollen=[], turn_tools=[],
    )
    md = (tmp_path / "vNONE99.md").read_text(encoding="utf-8")
    assert "nur Lotse-Kontext" in md
    assert "keine Rolle geladen" in md
    # Header täuscht keine Fachrolle vor
    assert "Rolle `lotse`" not in md


def test_protokoll_fallback_rolle_fuer_andere_endpunkte(monkeypatch, tmp_path):
    # Nicht-Orchestrator-Endpunkt behält das rolle_fuer-Verhalten.
    monkeypatch.setattr(protokoll_log, "PROTOKOLL_DIR", str(tmp_path))
    monkeypatch.setenv("PROTOKOLL_ENABLED", "1")
    protokoll_log.protokolliere(
        method="POST", path="/api/recherche", endpoint="api_recherche",
        request_payload={"kind": "json", "json": {}},
        response_json={"herkunft": "kuratiert"},
        status=200, vid="vR123",
    )
    md = (tmp_path / "vR123.md").read_text(encoding="utf-8")
    assert "Rolle `recherche`" in md
    # Orchestrierungs-Abschnitt erscheint NICHT bei anderen Endpunkten
    assert "Orchestrierung (Rollen & Tools)" not in md
