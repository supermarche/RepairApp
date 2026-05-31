import json
import os
import app as flask_app
from repair import orchestrator, protokoll_log


def _client():
    flask_app.app.config["TESTING"] = True
    return flask_app.app.test_client()


def test_vorgang_anlegen():
    res = _client().post("/api/vorgang")
    assert res.status_code == 200
    assert res.get_json()["vorgang_id"]


def test_chat_turn(monkeypatch):
    def fake_run_turn(state, text, **kw):
        return {"antwort_text": "Hallo!", "karten": [], "abgebrochen": False}
    monkeypatch.setattr(orchestrator, "run_turn", fake_run_turn)
    c = _client()
    vid = c.post("/api/vorgang").get_json()["vorgang_id"]
    res = c.post("/api/chat", json={"vorgang_id": vid, "text": "Toaster kaputt"})
    assert res.status_code == 200
    assert res.get_json()["antwort_text"] == "Hallo!"


def test_chat_leerer_text_400():
    c = _client()
    vid = c.post("/api/vorgang").get_json()["vorgang_id"]
    res = c.post("/api/chat", json={"vorgang_id": vid, "text": "  "})
    assert res.status_code == 400
    assert res.get_json()["code"] == "empty"


def test_diagnose_route_entfernt():
    res = _client().post("/api/diagnose", json={"text": "x"})
    assert res.status_code == 404


def test_chat_protokoll_landet_unter_vid(monkeypatch, tmp_path):
    # PROJ-28/PROJ-37: /api/chat sendet snake_case `vorgang_id`. Das Anfrage-Protokoll
    # muss diese vid erkennen und den Eintrag in <vid>.md schreiben — nicht in der
    # Sammeldatei _ohne-vorgang.md (Regression: _prot_extract_vid kannte nur vorgangId).
    monkeypatch.setattr(protokoll_log, "PROTOKOLL_DIR", str(tmp_path))
    monkeypatch.setenv("PROTOKOLL_ENABLED", "1")

    def fake_run_turn(state, text, **kw):
        return {"antwort_text": "ok", "karten": [], "abgebrochen": False}

    monkeypatch.setattr(orchestrator, "run_turn", fake_run_turn)
    c = _client()
    vid = c.post("/api/vorgang").get_json()["vorgang_id"]
    res = c.post("/api/chat", json={"vorgang_id": vid, "text": "Toaster kaputt"})
    assert res.status_code == 200
    assert os.path.exists(os.path.join(str(tmp_path), f"{vid}.md"))
    assert not os.path.exists(os.path.join(str(tmp_path), "_ohne-vorgang.md"))


def test_chat_ai_error_gibt_502(monkeypatch):
    # PROJ-40: run_turn liefert ai_error → /api/chat antwortet mit HTTP 502.
    def fake_run_turn(state, text, **kw):
        return {"antwort_text": "Verbindung gestört.", "karten": [],
                "abgebrochen": False, "_turn_rollen": [], "_turn_tools": [],
                "error": "RuntimeError: boom", "code": "ai_error"}

    monkeypatch.setattr(orchestrator, "run_turn", fake_run_turn)
    c = _client()
    vid = c.post("/api/vorgang").get_json()["vorgang_id"]
    res = c.post("/api/chat", json={"vorgang_id": vid, "text": "Toaster kaputt"})
    assert res.status_code == 502
    assert res.get_json()["code"] == "ai_error"


def test_chat_turn_keys_lecken_nicht_in_client_antwort(monkeypatch):
    # PROJ-43: _turn_rollen/_turn_tools dürfen NICHT in der Client-Antwort landen.
    def fake_run_turn(state, text, **kw):
        return {"antwort_text": "ok", "karten": [], "abgebrochen": False,
                "_turn_rollen": ["diagnose"],
                "_turn_tools": [{"tool": "lade_rolle", "ok": True}]}

    monkeypatch.setattr(orchestrator, "run_turn", fake_run_turn)
    c = _client()
    vid = c.post("/api/vorgang").get_json()["vorgang_id"]
    body = c.post("/api/chat",
                  json={"vorgang_id": vid, "text": "x"}).get_json()
    assert set(body.keys()) == {"vorgang_id", "antwort_text", "karten", "abgebrochen"}
    assert "_turn_rollen" not in body and "_turn_tools" not in body


def test_chat_uebernimmt_medienids_in_state(monkeypatch):
    # PROJ-31 im Chat-Flow: medienIds landen im Vorgangs-State (für extrahiere_aus_medien).
    gesehen = {}

    def fake_run_turn(state, text, **kw):
        gesehen["medien"] = list(state.get("medien") or [])
        return {"antwort_text": "ok", "karten": [], "abgebrochen": False}

    monkeypatch.setattr(orchestrator, "run_turn", fake_run_turn)
    c = _client()
    vid = c.post("/api/vorgang").get_json()["vorgang_id"]
    res = c.post("/api/chat", json={"vorgang_id": vid, "text": "Foto anbei",
                                    "medienIds": ["m1", "m2"]})
    assert res.status_code == 200
    assert gesehen["medien"] == ["m1", "m2"]
