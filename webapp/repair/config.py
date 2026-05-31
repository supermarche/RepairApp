"""Zentrale Konfiguration — einzige Quelle veränderlicher Einstellungen (PROJ-30).

Jede zur Laufzeit/Deployment veränderliche Einstellung wird ausschließlich über
Umgebungsvariablen gelesen (geladen aus ``webapp/.env`` via ``python-dotenv``;
``load_dotenv()`` bleibt die einzige Lade-Stelle, in ``app.py``). Dieses Modul
bündelt die *getypten/validierten* Zugriffe und liefert für jeden Wert einen
sinnvollen Default, sodass die App auch ganz ohne ``.env`` startet.

**Fail-fast:** ``validate()`` wird beim Start einmalig aufgerufen und prüft alle
bounded/numerischen Werte. Bei syntaktisch ungültiger Belegung bricht die App
mit einer klaren, benennenden Meldung ab (welche Variable, welcher Wert, welcher
erwartete Bereich) — statt später mit kryptischem Fehler oder falschem
Defaultverhalten weiterzulaufen. Fehlende Variablen sind kein Fehler (stiller
Rückfall auf den Default).

Bewusste Ausnahme (kein ``.env``): paket-relativ aus dem Dateilayout abgeleitete
Pfade (``DB_PATH`` in ``store.py``/``wissensbasis.py``, ``MEDIA_DIR`` in
``multimodal.py``) — das ist Code-Layout, keine Deployment-Konfiguration.

Hinweis für den Drift-Guard (``tests/test_config_drift.py``): literale
Default-Bind-Adressen/Ports/Modellnamen/Limits dürfen ausschließlich **hier** als
``DEFAULT_*``-Konstante stehen.
"""

from __future__ import annotations

import os


class ConfigError(Exception):
    """Ungültige Konfiguration — wird beim Start (Fail-fast) ausgelöst."""


# ── Zentrale Defaults (einzig erlaubte Stelle für solche Literale) ───────────
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
DEFAULT_WHISPER_MODEL = "whisper-1"
DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_LLM_TIMEOUT = 180.0  # s — CPU-Inferenz braucht länger als die Cloud
DEFAULT_MAX_TOOL_ITERATIONS = 12  # Tool-Call-Runden pro Chat-Turn (Orchestrator)
DEFAULT_MAX_MEDIEN_PRO_ANFRAGE = 6  # max. Medien je Diagnose-Anfrage (PROJ-31)
DEFAULT_MAX_PDF_SEITEN = 5  # max. ausgewertete PDF-Seiten je Dokument (PROJ-31)
DEFAULT_KONTEXT_TOKEN_BUDGET = 6000  # weiche Obergrenze gesendeter variabler Kontext (PROJ-41)
DEFAULT_KONTEXT_WOERTLICH_TURNS = 4  # jüngste Turns wörtlich erhalten (PROJ-41)
DEFAULT_REPORT_PDF_ENABLED = True   # PDF-Erzeugung für den Übergabe-Report (PROJ-44)
DEFAULT_MAX_FEEDBACK_BYTES = 4000   # max. Feedback-Textlänge in Bytes (PROJ-46)
DEFAULT_PROMPT_CACHE_KEY_PREFIX = "repair"  # Präfix des prompt_cache_key (PROJ-48)


def _raw(name: str) -> str | None:
    """Rohwert einer Variable: getrimmt, ohne umschließende Quotes; leer → None.

    Tolerant gegen Copy-&-Paste aus ``.env.example`` (Whitespace, ``"…"``/``'…'``).
    Eine gesetzte, aber leere Variable zählt als „nicht gesetzt" (Default-Pfad) —
    konsistent zur bestehenden ``.strip()``-Behandlung in ``ai.py``/``recherche.py``.
    """
    val = os.environ.get(name)
    if val is None:
        return None
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        val = val[1:-1].strip()
    return val or None


def _int(name: str, default: int, *, lo: int, hi: int) -> int:
    raw = _raw(name)
    if raw is None:
        return default
    try:
        val = int(raw)
    except ValueError:
        raise ConfigError(
            f"{name}={raw!r} ist keine ganze Zahl — erwartet wird eine Ganzzahl "
            f"im Bereich {lo}..{hi} (Default {default})."
        )
    if not (lo <= val <= hi):
        raise ConfigError(
            f"{name}={val} liegt außerhalb des erlaubten Bereichs {lo}..{hi} "
            f"(Default {default})."
        )
    return val


def _float_pos(name: str, default: float) -> float:
    raw = _raw(name)
    if raw is None:
        return default
    try:
        val = float(raw)
    except ValueError:
        raise ConfigError(
            f"{name}={raw!r} ist keine Zahl — erwartet wird eine positive "
            f"Sekundenzahl (Default {default})."
        )
    if val <= 0:
        raise ConfigError(
            f"{name}={val} muss > 0 sein — erwartet eine positive Sekundenzahl "
            f"(Default {default})."
        )
    return val


# ── Getypte Getter ───────────────────────────────────────────────────────────
def host() -> str:
    """Bind-Adresse der App (z. B. ``0.0.0.0`` im Container). Default 127.0.0.1."""
    return _raw("HOST") or DEFAULT_HOST


def port() -> int:
    """TCP-Port der App. Default 5000; gültig 1..65535 (sonst Fail-fast)."""
    return _int("PORT", DEFAULT_PORT, lo=1, hi=65535)


def whisper_model() -> str:
    """Modell für die Audio-Transkription (OpenAI Whisper). Default whisper-1."""
    return _raw("WHISPER_MODEL") or DEFAULT_WHISPER_MODEL


def max_upload_bytes() -> int:
    """Maximale Mediengröße in Bytes. Default 10485760 (10 MB); > 0 (sonst Fail-fast)."""
    return _int("MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES, lo=1, hi=2**63 - 1)


def vision_model() -> str | None:
    """Vision-Modell-Override für die Bild-/Dokument-Auswertung (PROJ-31).

    ``None`` (ungesetzt) → ``vision.py`` nutzt das Cloud-Diagnose-Modell
    (``OPENAI_MODEL`` / ``gpt-4o-…``, das ebenfalls Vision kann). Bewusst kein
    Default-Literal hier — der Default ist das ohnehin konfigurierte OpenAI-Modell.
    """
    return _raw("VISION_MODEL")


def max_medien_pro_anfrage() -> int:
    """Obergrenze Medien pro Diagnose-Anfrage. Default 6; 1..100 (sonst Fail-fast)."""
    return _int("MAX_MEDIEN_PRO_ANFRAGE", DEFAULT_MAX_MEDIEN_PRO_ANFRAGE, lo=1, hi=100)


def max_pdf_seiten() -> int:
    """Max. ausgewertete PDF-Seiten je Dokument. Default 5; 1..50 (sonst Fail-fast)."""
    return _int("MAX_PDF_SEITEN", DEFAULT_MAX_PDF_SEITEN, lo=1, hi=50)


def llm_timeout() -> float:
    """Timeout (Sekunden) für eine LLM-Antwort. Default 180; > 0 (sonst Fail-fast)."""
    return _float_pos("LLM_TIMEOUT", DEFAULT_LLM_TIMEOUT)


def max_tool_iterations() -> int:
    """Max. Tool-Call-Runden pro Chat-Turn (Endlosschleifen-/Kostenschutz).

    Default 12; >= 1 (sonst Fail-fast).
    """
    return _int("MAX_TOOL_ITERATIONS", DEFAULT_MAX_TOOL_ITERATIONS, lo=1, hi=2**31 - 1)


def kontext_token_budget() -> int:
    """Weiche Obergrenze (geschätzte Tokens) des gesendeten variablen Kontexts.

    Steuert die Kontext-Verdichtung (PROJ-41): Überschreitet der wörtlich
    erhaltene jüngste Verlauf dieses Budget, wird mehr älterer Verlauf in den
    Zustands-Digest verschoben. Heuristische Token-Schätzung (kein Tokenizer).
    Default 6000; gültig 500..1000000 (sonst Fail-fast).
    """
    return _int("KONTEXT_TOKEN_BUDGET", DEFAULT_KONTEXT_TOKEN_BUDGET,
                lo=500, hi=1_000_000)


def kontext_woertlich_turns() -> int:
    """Anzahl jüngster Turns, die WÖRTLICH (unverdichtet) gesendet werden (PROJ-41).

    Ältere Turns werden zu einem kompakten Zustands-Digest zusammengefasst.
    Default 4; gültig 1..100 (sonst Fail-fast).
    """
    return _int("KONTEXT_WOERTLICH_TURNS", DEFAULT_KONTEXT_WOERTLICH_TURNS,
                lo=1, hi=100)


def flask_debug() -> bool:
    """Flask-Debug-Modus. Tolerant: ``0``/``false``/leer = aus, sonst an. Default an."""
    return os.environ.get("FLASK_DEBUG", "1") not in ("0", "false", "False", "")


def report_pdf_enabled() -> bool:
    """PDF-Erzeugung für den Service-Point-Übergabe-Report (PROJ-44).

    Tolerant: ``0``/``false``/``False``/leer = aus, sonst an. Default an.
    Deaktivieren via ``REPORT_PDF_ENABLED=0`` in ``.env`` (z. B. für Staging
    ohne PyMuPDF-Wheel oder für Testläufe ohne PDF-Ausgabe).
    """
    return os.environ.get("REPORT_PDF_ENABLED", "1") not in ("0", "false", "False", "")


def feedback_enabled() -> bool:
    """Feedback-Funktion an/aus (PROJ-46).

    Tolerant: ``0``/``false``/``False``/leer = aus, sonst an. Default an.
    Deaktivieren via ``FEEDBACK_ENABLED=0`` in ``.env``; der Endpunkt
    ``/api/feedback`` antwortet dann sauber ablehnend (403, code disabled).
    """
    return os.environ.get("FEEDBACK_ENABLED", "1") not in ("0", "false", "False", "")


def max_feedback_bytes() -> int:
    """Maximale Feedback-Textlänge in Bytes (UTF-8, PROJ-46).

    Default 4000; gültig 1..10000000 (sonst Fail-fast).
    """
    return _int("MAX_FEEDBACK_BYTES", DEFAULT_MAX_FEEDBACK_BYTES, lo=1, hi=10_000_000)


def prompt_cache_key_enabled() -> bool:
    """Expliziten prompt_cache_key je Sprache senden (PROJ-48).

    Tolerant: ``0``/``false``/``False``/leer = aus, sonst an. Default an.
    Deaktivieren via ``PROMPT_CACHE_KEY_ENABLED=0``; dann nur Auto-Caching,
    kein prompt_cache_key im Call.
    """
    return os.environ.get("PROMPT_CACHE_KEY_ENABLED", "1") not in ("0", "false", "False", "")


def prompt_cache_key_prefix() -> str:
    """Präfix des prompt_cache_key (PROJ-48).

    Schlüssel = ``<präfix>-<sprache>``, z. B. ``repair-de``.
    Default ``repair``.
    """
    return _raw("PROMPT_CACHE_KEY_PREFIX") or DEFAULT_PROMPT_CACHE_KEY_PREFIX


# ── Fail-fast-Validierung beim Start ──────────────────────────────────────────
def validate() -> None:
    """Erzwingt die frühe Auswertung aller bounded/numerischen Werte.

    Sammelt *alle* ungültigen Belegungen und meldet sie gebündelt, damit der
    Betreiber nicht Fehler für Fehler nachbessern muss. Wird einmalig in
    ``app.py`` nach ``load_dotenv()`` aufgerufen.
    """
    fehler: list[str] = []
    for getter in (port, llm_timeout, max_upload_bytes, max_tool_iterations,
                   max_medien_pro_anfrage, max_pdf_seiten,
                   kontext_token_budget, kontext_woertlich_turns,
                   max_feedback_bytes):
        try:
            getter()
        except ConfigError as exc:
            fehler.append(str(exc))
    if fehler:
        raise ConfigError(
            "Ungültige Konfiguration in der Umgebung/.env:\n  - "
            + "\n  - ".join(fehler)
        )
