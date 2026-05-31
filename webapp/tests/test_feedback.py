"""Tests für den Feedback-Button-Endpunkt POST /api/feedback (PROJ-46).

Lauffähig ohne Server:
    python tests/test_feedback.py   (standalone)
    python -m pytest tests/test_feedback.py -q

Nutzt Flask test_client (analog test_api_chat.py); keine echte DB-Datei nötig
(feedback.py öffnet die DB in webapp/ — im Test wird der DB-Pfad über
monkeypatch auf einen tmp-Pfad umgebogen).
"""

from __future__ import annotations

import json
import os
import sys

# webapp/ ist das cwd der Tests — sys.path ergänzen, damit `import app` klappt.
_WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WEBAPP not in sys.path:
    sys.path.insert(0, _WEBAPP)

import app as flask_app
from repair import feedback, store


def _client():
    flask_app.app.config["TESTING"] = True
    return flask_app.app.test_client()


# ─── Hilfsfunktion: Vorgang anlegen ──────────────────────────────────────────

def _neue_vid(c=None) -> str:
    if c is None:
        c = _client()
    return c.post("/api/vorgang").get_json()["vorgang_id"]


# ─── Erfolgsfall ──────────────────────────────────────────────────────────────

def test_feedback_erfolg_200(monkeypatch, tmp_path):
    """Erfolgreiche Feedback-Speicherung liefert 200 {ok:true, feedback_id}."""
    monkeypatch.setattr(feedback, "DB_PATH", str(tmp_path / "feedback.db"))
    c = _client()
    vid = _neue_vid(c)
    res = c.post("/api/feedback", json={"vorgang_id": vid, "text": "Sehr hilfreich!"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["ok"] is True
    assert body["feedback_id"]


def test_feedback_id_ist_eindeutig(monkeypatch, tmp_path):
    """Zwei Feedbacks desselben Vorgangs haben unterschiedliche IDs."""
    monkeypatch.setattr(feedback, "DB_PATH", str(tmp_path / "feedback.db"))
    c = _client()
    vid = _neue_vid(c)
    id1 = c.post("/api/feedback", json={"vorgang_id": vid, "text": "Eins"}).get_json()["feedback_id"]
    id2 = c.post("/api/feedback", json={"vorgang_id": vid, "text": "Zwei"}).get_json()["feedback_id"]
    assert id1 != id2


# ─── Fehlerfälle ─────────────────────────────────────────────────────────────

def test_feedback_leerer_text_400(monkeypatch, tmp_path):
    """Leerer Text → 400 empty."""
    monkeypatch.setattr(feedback, "DB_PATH", str(tmp_path / "feedback.db"))
    c = _client()
    vid = _neue_vid(c)
    res = c.post("/api/feedback", json={"vorgang_id": vid, "text": ""})
    assert res.status_code == 400
    assert res.get_json()["code"] == "empty"


def test_feedback_whitespace_text_400(monkeypatch, tmp_path):
    """Nur-Whitespace-Text → 400 empty."""
    monkeypatch.setattr(feedback, "DB_PATH", str(tmp_path / "feedback.db"))
    c = _client()
    vid = _neue_vid(c)
    res = c.post("/api/feedback", json={"vorgang_id": vid, "text": "   \n\t  "})
    assert res.status_code == 400
    assert res.get_json()["code"] == "empty"


def test_feedback_zu_lang_400(monkeypatch, tmp_path):
    """Text über MAX_FEEDBACK_BYTES → 400 too_long."""
    monkeypatch.setattr(feedback, "DB_PATH", str(tmp_path / "feedback.db"))
    monkeypatch.setenv("MAX_FEEDBACK_BYTES", "10")
    c = _client()
    vid = _neue_vid(c)
    res = c.post("/api/feedback", json={"vorgang_id": vid, "text": "A" * 11})
    assert res.status_code == 400
    assert res.get_json()["code"] == "too_long"


def test_feedback_unbekannter_vorgang_404(monkeypatch, tmp_path):
    """Unbekannte vorgang_id → 404 no_vorgang."""
    monkeypatch.setattr(feedback, "DB_PATH", str(tmp_path / "feedback.db"))
    c = _client()
    res = c.post("/api/feedback", json={"vorgang_id": "nichtvorhanden123", "text": "Hallo"})
    assert res.status_code == 404
    assert res.get_json()["code"] == "no_vorgang"


def test_feedback_disabled_403(monkeypatch, tmp_path):
    """FEEDBACK_ENABLED=0 → 403 disabled."""
    monkeypatch.setattr(feedback, "DB_PATH", str(tmp_path / "feedback.db"))
    monkeypatch.setenv("FEEDBACK_ENABLED", "0")
    c = _client()
    vid = _neue_vid(c)
    res = c.post("/api/feedback", json={"vorgang_id": vid, "text": "Testtext"})
    assert res.status_code == 403
    assert res.get_json()["code"] == "disabled"


# ─── Append-Semantik (mehrfaches Feedback) ────────────────────────────────────

def test_feedback_mehrfach_append(monkeypatch, tmp_path):
    """Mehrere Feedbacks je Vorgang werden alle gespeichert (Append, kein Überschreiben)."""
    db = str(tmp_path / "feedback.db")
    monkeypatch.setattr(feedback, "DB_PATH", db)
    c = _client()
    vid = _neue_vid(c)
    for i in range(3):
        res = c.post("/api/feedback", json={"vorgang_id": vid, "text": f"Feedback {i}"})
        assert res.status_code == 200, f"Iteration {i}: {res.get_json()}"

    # Direkt in der DB nachzählen
    import sqlite3
    conn = sqlite3.connect(db)
    cnt = conn.execute("SELECT COUNT(*) FROM feedback WHERE vorgang_id=?", (vid,)).fetchone()[0]
    conn.close()
    assert cnt == 3


# ─── Umlaute, Emojis, Sonderzeichen ──────────────────────────────────────────

def test_feedback_umlaute_emojis(monkeypatch, tmp_path):
    """Umlaute und Emojis werden korrekt gespeichert (kein ASCII-Escaping)."""
    db = str(tmp_path / "feedback.db")
    monkeypatch.setattr(feedback, "DB_PATH", db)
    c = _client()
    vid = _neue_vid(c)
    text = "Schönes Ö, ü, ä, ß — und ein 🔧!"
    res = c.post("/api/feedback", json={"vorgang_id": vid, "text": text})
    assert res.status_code == 200

    # JSON-Antwort darf keine ASCII-Escape-Sequenzen enthalten
    raw = res.get_data(as_text=True)
    assert "\\u" not in raw, "Antwort enthält ASCII-Escaping — ensure_ascii=False verletzt"

    # DB-Inhalt prüfen
    import sqlite3
    conn = sqlite3.connect(db)
    stored = conn.execute("SELECT text FROM feedback WHERE vorgang_id=?", (vid,)).fetchone()[0]
    conn.close()
    assert stored == text


# ─── Persistenz in feedback.db prüfbar ────────────────────────────────────────

def test_feedback_persistenz_in_db(monkeypatch, tmp_path):
    """feedback.db wird angelegt und enthält den gespeicherten Eintrag."""
    db = str(tmp_path / "feedback.db")
    monkeypatch.setattr(feedback, "DB_PATH", db)
    c = _client()
    vid = _neue_vid(c)
    res = c.post("/api/feedback", json={
        "vorgang_id": vid,
        "text": "Persistenz-Test",
        "screen": "chat",
        "letzte_antwort": "Hallo Welt",
    })
    assert res.status_code == 200
    fid = res.get_json()["feedback_id"]

    import sqlite3
    assert os.path.exists(db), "feedback.db wurde nicht angelegt"
    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT id, vorgang_id, text, screen, letzte_antwort FROM feedback WHERE id=?",
        (fid,),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == fid
    assert row[1] == vid
    assert row[2] == "Persistenz-Test"
    assert row[3] == "chat"
    assert row[4] == "Hallo Welt"


# ─── Optionale Felder ─────────────────────────────────────────────────────────

def test_feedback_ohne_optionale_felder(monkeypatch, tmp_path):
    """Feedback ohne screen/letzte_antwort wird korrekt gespeichert."""
    monkeypatch.setattr(feedback, "DB_PATH", str(tmp_path / "feedback.db"))
    c = _client()
    vid = _neue_vid(c)
    res = c.post("/api/feedback", json={"vorgang_id": vid, "text": "Nur Text"})
    assert res.status_code == 200


# ─── Standalone-Runner ────────────────────────────────────────────────────────

def _run_standalone() -> int:
    """Führt alle test_*-Funktionen ohne pytest aus (für ``python tests/test_feedback.py``)."""
    import tempfile

    class _MonkeyPatch:
        """Minimales Monkeypatch für den Standalone-Betrieb."""
        def __init__(self):
            self._patches: list = []
            self._envs: list = []

        def setattr(self, obj, attr, val):
            old = getattr(obj, attr)
            setattr(obj, attr, val)
            self._patches.append((obj, attr, old))

        def setenv(self, name, val):
            old = os.environ.get(name)
            os.environ[name] = val
            self._envs.append((name, old))

        def undo(self):
            for obj, attr, old in reversed(self._patches):
                setattr(obj, attr, old)
            for name, old in reversed(self._envs):
                if old is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = old

    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    fails = 0
    for t in tests:
        mp = _MonkeyPatch()
        td = tempfile.mkdtemp()
        try:
            t(mp, type("P", (), {"__truediv__": lambda s, n: type("FP", (), {
                "__str__": lambda x: os.path.join(td, n)
            })()})())
            print(f"  ok   {t.__name__}")
        except Exception as exc:
            fails += 1
            print(f"  FAIL {t.__name__}\n       {exc}")
        finally:
            mp.undo()
    print(f"\n{len(tests) - fails}/{len(tests)} Tests bestanden.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
