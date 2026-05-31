"""OpenAI-Backend-Auflösung für den LLM-Orchestrator.

Seit dem Stufe-4-Umbau (LLM-Orchestrierung, PROJ-32..37) gibt es **keine**
Single-Shot-``diagnose()`` und kein ``device``-Monolith-Objekt mehr — der
gesamte Reparatur-Flow läuft als orchestrierter Chat über
:mod:`repair.orchestrator` (Tool-Call-Schleife gegen die ChatGPT-API).

Dieses Modul liefert nur noch die **Backend-Auflösung**, die der Orchestrator
wiederverwendet:

  - :func:`_resolve_backend` — ``(client, model)`` aus ``OPENAI_API_KEY`` /
    ``OPENAI_MODEL`` (Default :data:`DEFAULT_OPENAI_MODEL`), oder
    ``(None, None)`` wenn kein Key gesetzt ist bzw. die ``openai``-Lib fehlt.

Ohne konfiguriertes Backend scheitert nichts hart: der Orchestrator übersetzt
``(None, None)`` in ein Fehler-Objekt (``code:"no_backend"``).
"""

from __future__ import annotations

import logging
import os
import re

log = logging.getLogger(__name__)

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

# Markdown-Code-Fence am Anfang (``` oder ```json …) bzw. am Ende.
_FENCE_OPEN = re.compile(r"^\s*```[ \t]*[A-Za-z0-9_+-]*[ \t]*\r?\n?")
_FENCE_CLOSE = re.compile(r"\r?\n?[ \t]*```[ \t]*$")


def _clean_json_text(content: str | None) -> str:
    """Bereinigt eine LLM-Antwort, sodass :func:`json.loads` sauber parst.

    Robust gegen:

    * reines JSON ohne Fences (unverändert durchgereicht),
    * ```` ```json … ```` / ```` ``` … ```` Code-Fences (werden entfernt),
    * Zusatztext vor/nach dem JSON-Objekt bzw. -Array (wird abgeschnitten),
    * leeren/``None``-Input (gibt dann ``""`` bzw. den Originalstring zurück —
      definiert, kein Crash; das nachgelagerte ``json.loads`` löst dann den
      regulären Degradationspfad aus).

    Es wird **kein** Inhalt erfunden: ist kein JSON-Klammerbereich auffindbar,
    wird der gefenste/getrimmte Text zurückgegeben (der Aufrufer behandelt ein
    anschließendes ``json.loads``-Scheitern als echte Degradation).
    """
    if not content:
        return content or ""

    text = content.strip()

    # Markdown-Code-Fences entfernen (öffnend + schließend), falls vorhanden.
    text = _FENCE_OPEN.sub("", text)
    text = _FENCE_CLOSE.sub("", text)
    text = text.strip()

    # Umgebenden Zusatztext abschneiden: erstes { … letztes } bzw. [ … ].
    start_obj, start_arr = text.find("{"), text.find("[")
    candidates = [i for i in (start_obj, start_arr) if i != -1]
    if candidates:
        start = min(candidates)
        opener = text[start]
        closer = "}" if opener == "{" else "]"
        end = text.rfind(closer)
        if end > start:
            text = text[start:end + 1]

    return text.strip()
# Der LLM-Timeout (LLM_TIMEOUT) wird zentral in repair/config.py verwaltet
# (config.DEFAULT_LLM_TIMEOUT) — kein zweiter Default hier (PROJ-30).


def _resolve_backend():
    """Liefert ``(client, model)`` — oder ``(None, None)``.

    OpenAI-Cloud via ``OPENAI_API_KEY``; Modell aus ``OPENAI_MODEL`` (Default
    ``gpt-4o-mini``). Gibt ``(None, None)`` zurück, wenn kein Key gesetzt ist
    oder die ``openai``-Lib fehlt → der Aufrufer liefert dann ``no_backend``.

    ``max_retries=0``: Ein Timeout soll sich nicht durch SDK-Retries
    vervielfachen — lieber einmal sauber scheitern.
    """
    try:
        from openai import OpenAI
    except Exception:
        return None, None

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None, None

    model = os.environ.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
    try:
        client = OpenAI(api_key=api_key, max_retries=0)
        return client, model
    except Exception:
        return None, None
