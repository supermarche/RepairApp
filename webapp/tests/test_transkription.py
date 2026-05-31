"""Tests für PROJ-47 — Spracheingabe: transkribiere() + POST /api/transkription.

Abgedeckte Fälle (ohne echten OpenAI-Call):
* kein Audio → source "hinweis"
* kein OPENAI_API_KEY → source "hinweis"
* lang-Normalisierung: "en" bleibt "en"; "fr"/""/ None → "de"
* Whisper-Pfad via gemocktem OpenAI-Client: language-Argument wird korrekt
  übergeben, Rückgabe {text, source:"whisper"}
* Route POST /api/transkription: multipart-Audio + Form ``lang=en`` →
  transkribiere mit lang="en"; Query ``?lang=en`` → lang="en";
  unbekannte Sprache (``?lang=fr``) → normalisiert auf "de"

Lauffähig ohne pytest:  ``python tests/test_transkription.py``
Mit pytest:             ``python -m pytest tests/test_transkription.py``
"""

from __future__ import annotations

import io
import os
import sys

WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WEBAPP not in sys.path:
    sys.path.insert(0, WEBAPP)

# Backend-Variablen für deterministische Tests entfernen.
for _k in ("OPENAI_API_KEY",):
    os.environ.pop(_k, None)

import app as flask_app  # noqa: E402
from repair import multimodal  # noqa: E402


# ── Hilfsobjekte für gemockten OpenAI-Whisper-Client ─────────────────────────

class _FakeTranscription:
    """Simuliert das Rückgabe-Objekt von client.audio.transcriptions.create()."""
    def __init__(self, text: str = "Hallo Welt") -> None:
        self.text = text


class _FakeTranscriptions:
    """Fängt den create()-Aufruf ab und zeichnet kwargs auf."""
    def __init__(self, response_text: str = "Hallo Welt") -> None:
        self.calls: list[dict] = []
        self._response_text = response_text

    def create(self, **kwargs) -> _FakeTranscription:
        self.calls.append(kwargs)
        return _FakeTranscription(self._response_text)


class _FakeAudio:
    def __init__(self, response_text: str = "Hallo Welt") -> None:
        self.transcriptions = _FakeTranscriptions(response_text)


class _FakeOpenAI:
    """Minimaler OpenAI-Client-Ersatz für Whisper-Tests."""
    def __init__(self, response_text: str = "Hallo Welt", **_kwargs) -> None:
        self.audio = _FakeAudio(response_text)


def _patch_openai(monkeypatch_dict: dict, response_text: str = "Test erkannt"):
    """Patcht openai.OpenAI innerhalb von repair.multimodal.

    Gibt die _FakeTranscriptions-Instanz zurück (für Assertions über .calls).
    Stellt nach dem Test den Original-Import wieder her.
    """
    import repair.multimodal as mm_module

    fake_client = _FakeOpenAI(response_text=response_text)
    original = {}

    class _PatchedOpenAI:
        def __init__(self, **kwargs):
            pass

        @property
        def audio(self):
            return fake_client.audio

    # openai.OpenAI in dem Scope patchen, den multimodal.transkribiere nutzt
    try:
        import openai as _openai_mod
        original["OpenAI"] = _openai_mod.OpenAI
        _openai_mod.OpenAI = _PatchedOpenAI
        monkeypatch_dict["_openai_mod"] = _openai_mod
        monkeypatch_dict["original"] = original
    except ImportError:
        pass

    return fake_client.audio.transcriptions


def _restore_openai(monkeypatch_dict: dict) -> None:
    """Stellt das Original-openai.OpenAI wieder her."""
    mod = monkeypatch_dict.get("_openai_mod")
    orig = monkeypatch_dict.get("original", {})
    if mod and "OpenAI" in orig:
        mod.OpenAI = orig["OpenAI"]


# ── Einheit: repair.multimodal.transkribiere ─────────────────────────────────

def test_kein_audio_liefert_hinweis() -> None:
    """transkribiere(None) → source "hinweis"."""
    result = multimodal.transkribiere(None)
    assert result["source"] == "hinweis"
    assert result["text"] == ""
    assert result["hinweis"]


def test_leere_bytes_liefert_hinweis() -> None:
    """transkribiere(b"") → source "hinweis" (falsy bytes)."""
    result = multimodal.transkribiere(b"")
    assert result["source"] == "hinweis"


def test_kein_api_key_liefert_hinweis() -> None:
    """Ohne OPENAI_API_KEY → source "hinweis"."""
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        result = multimodal.transkribiere(b"fake-audio-data")
        assert result["source"] == "hinweis"
        assert result["text"] == ""
    finally:
        if old is not None:
            os.environ["OPENAI_API_KEY"] = old


def test_lang_normalisierung_en_bleibt_en() -> None:
    """lang="en" wird unverändert an Whisper weitergereicht."""
    os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-mocking"
    mp: dict = {}
    transcriptions = _patch_openai(mp, response_text="Hello World")
    try:
        result = multimodal.transkribiere(b"fake-audio", lang="en")
    finally:
        _restore_openai(mp)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result["source"] == "whisper"
    assert result["text"] == "Hello World"
    assert transcriptions.calls, "create() wurde nicht aufgerufen"
    assert transcriptions.calls[0]["language"] == "en"


def test_lang_normalisierung_de_wird_genutzt() -> None:
    """lang="de" (Default) wird an Whisper weitergereicht."""
    os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-mocking"
    mp: dict = {}
    transcriptions = _patch_openai(mp, response_text="Hallo Welt")
    try:
        result = multimodal.transkribiere(b"fake-audio")  # kein lang → Default "de"
    finally:
        _restore_openai(mp)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result["source"] == "whisper"
    assert transcriptions.calls[0]["language"] == "de"


def test_lang_normalisierung_unbekannte_sprache_wird_de() -> None:
    """lang="fr" → wird auf "de" normalisiert (vor dem API-Aufruf)."""
    os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-mocking"
    mp: dict = {}
    transcriptions = _patch_openai(mp)
    try:
        result = multimodal.transkribiere(b"fake-audio", lang="fr")
    finally:
        _restore_openai(mp)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result["source"] == "whisper"
    assert transcriptions.calls[0]["language"] == "de"


def test_lang_normalisierung_leer_wird_de() -> None:
    """lang="" → wird auf "de" normalisiert."""
    os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-mocking"
    mp: dict = {}
    transcriptions = _patch_openai(mp)
    try:
        multimodal.transkribiere(b"fake-audio", lang="")
    finally:
        _restore_openai(mp)
        os.environ.pop("OPENAI_API_KEY", None)

    assert transcriptions.calls[0]["language"] == "de"


def test_lang_normalisierung_none_wird_de() -> None:
    """lang=None → wird auf "de" normalisiert."""
    os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-mocking"
    mp: dict = {}
    transcriptions = _patch_openai(mp)
    try:
        multimodal.transkribiere(b"fake-audio", lang=None)  # type: ignore[arg-type]
    finally:
        _restore_openai(mp)
        os.environ.pop("OPENAI_API_KEY", None)

    assert transcriptions.calls[0]["language"] == "de"


def test_whisper_pfad_liefert_text_und_source_whisper() -> None:
    """Erfolgreicher Whisper-Aufruf → {text, source:"whisper"}."""
    os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-mocking"
    mp: dict = {}
    _patch_openai(mp, response_text="Toaster macht Knackgeräusch")
    try:
        result = multimodal.transkribiere(b"fake-audio-bytes", lang="de")
    finally:
        _restore_openai(mp)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result["source"] == "whisper"
    assert result["text"] == "Toaster macht Knackgeräusch"
    assert "hinweis" not in result or result.get("hinweis") in (None, "")


# ── Route: POST /api/transkription ────────────────────────────────────────────

def _make_test_client():
    return flask_app.app.test_client()


def test_route_kein_audio_liefert_200_mit_hinweis() -> None:
    """POST /api/transkription ohne Audio → HTTP 200, source "hinweis"."""
    c = _make_test_client()
    r = c.post("/api/transkription")
    assert r.status_code == 200
    j = r.get_json()
    assert j["source"] == "hinweis"


def test_route_multipart_lang_form_field() -> None:
    """Multipart-Audio + Form-Feld ``lang=en`` → transkribiere mit lang="en".

    Wir patchen multimodal.transkribiere direkt, um den OpenAI-Aufruf zu umgehen
    und das lang-Argument zu verifizieren.
    """
    aufrufe: list[dict] = []

    def fake_transkribiere(audio_bytes=None, lang="de"):
        aufrufe.append({"audio_bytes": audio_bytes, "lang": lang})
        return {"text": "Test", "source": "whisper"}

    original = multimodal.transkribiere
    multimodal.transkribiere = fake_transkribiere
    try:
        c = _make_test_client()
        data = {
            "file": (io.BytesIO(b"fake-audio"), "aufnahme.webm", "audio/webm"),
            "lang": "en",
        }
        r = c.post("/api/transkription", data=data, content_type="multipart/form-data")
    finally:
        multimodal.transkribiere = original

    assert r.status_code == 200
    j = r.get_json()
    assert j["source"] == "whisper"
    assert aufrufe, "transkribiere() wurde nicht aufgerufen"
    assert aufrufe[0]["lang"] == "en"


def test_route_query_param_lang_en() -> None:
    """POST /api/transkription?lang=en → lang="en" an transkribiere übergeben."""
    aufrufe: list[dict] = []

    def fake_transkribiere(audio_bytes=None, lang="de"):
        aufrufe.append({"lang": lang})
        return {"text": "Hello", "source": "whisper"}

    original = multimodal.transkribiere
    multimodal.transkribiere = fake_transkribiere
    try:
        c = _make_test_client()
        r = c.post(
            "/api/transkription?lang=en",
            data=b"fake-audio",
            content_type="audio/webm",
        )
    finally:
        multimodal.transkribiere = original

    assert r.status_code == 200
    assert aufrufe[0]["lang"] == "en"


def test_route_query_param_unbekannte_sprache_wird_de() -> None:
    """?lang=fr → normalisiert auf "de" und an transkribiere übergeben."""
    aufrufe: list[dict] = []

    def fake_transkribiere(audio_bytes=None, lang="de"):
        aufrufe.append({"lang": lang})
        return {"text": "", "source": "hinweis", "hinweis": "test"}

    original = multimodal.transkribiere
    multimodal.transkribiere = fake_transkribiere
    try:
        c = _make_test_client()
        r = c.post(
            "/api/transkription?lang=fr",
            data=b"fake-audio",
            content_type="audio/webm",
        )
    finally:
        multimodal.transkribiere = original

    assert r.status_code == 200
    assert aufrufe[0]["lang"] == "de"


def test_route_json_body_lang() -> None:
    """JSON-Body ``{"lang": "en"}`` → lang="en" an transkribiere übergeben."""
    aufrufe: list[dict] = []

    def fake_transkribiere(audio_bytes=None, lang="de"):
        aufrufe.append({"lang": lang})
        return {"text": "Hi", "source": "whisper"}

    original = multimodal.transkribiere
    multimodal.transkribiere = fake_transkribiere
    try:
        c = _make_test_client()
        r = c.post(
            "/api/transkription",
            json={"lang": "en"},
        )
    finally:
        multimodal.transkribiere = original

    assert r.status_code == 200
    assert aufrufe[0]["lang"] == "en"


def test_route_default_lang_ist_de() -> None:
    """POST ohne lang-Angabe → Default "de" an transkribiere übergeben."""
    aufrufe: list[dict] = []

    def fake_transkribiere(audio_bytes=None, lang="de"):
        aufrufe.append({"lang": lang})
        return {"text": "", "source": "hinweis", "hinweis": "kein audio"}

    original = multimodal.transkribiere
    multimodal.transkribiere = fake_transkribiere
    try:
        c = _make_test_client()
        r = c.post("/api/transkription")
    finally:
        multimodal.transkribiere = original

    assert r.status_code == 200
    assert aufrufe[0]["lang"] == "de"


# ── Standalone-Runner ──────────────────────────────────────────────────────────

def _run_standalone() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as exc:
            fails += 1
            print(f"  FAIL {t.__name__}\n       {exc}")
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"  ERR  {t.__name__}\n       {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - fails}/{len(tests)} Checks bestanden.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
