"""Feedback-Persistenz — lokale Speicherung von Nutzer-Anmerkungen (PROJ-46).

Tabelle: feedback(id TEXT PRIMARY KEY, vorgang_id TEXT NOT NULL,
                   text TEXT NOT NULL, screen TEXT, letzte_antwort TEXT,
                   created TEXT NOT NULL)
Datei:   webapp/feedback.db  (in .gitignore — nicht einchecken)

Verbindung wird pro Operation geöffnet und sauber geschlossen (thread-safe,
analog store.py). Append-only: mehrere Feedbacks je Vorgang erlaubt (kein
Überschreiben). id = secrets.token_urlsafe(12), created = ISO 8601 UTC.

Öffentliche API:
    speichere(vorgang_id, text, *, screen=None, letzte_antwort=None) -> dict
        → {id, vorgang_id, created}
"""

from __future__ import annotations

import logging
import os
import secrets
import sqlite3
from datetime import datetime, timezone

log = logging.getLogger(__name__)

# feedback.db liegt direkt in webapp/ (eine Ebene über repair/) — Layout,
# keine Deployment-Konfiguration (vgl. store.py DB_PATH).
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "feedback.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (
    id             TEXT PRIMARY KEY,
    vorgang_id     TEXT NOT NULL,
    text           TEXT NOT NULL,
    screen         TEXT,
    letzte_antwort TEXT,
    created        TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    """Öffnet Verbindung, legt Tabelle an (idempotent)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def speichere(
    vorgang_id: str,
    text: str,
    *,
    screen: str | None = None,
    letzte_antwort: str | None = None,
) -> dict:
    """Speichert einen Feedback-Eintrag und liefert {id, vorgang_id, created}.

    Append-only — mehrere Feedbacks je Vorgang möglich, kein Überschreiben.
    Logging auf INFO-Level OHNE PII (nur feedback_id + vorgang_id + Textlänge,
    nicht der Freitext selbst — PII-Leitlinie PROJ-29).
    """
    fid = secrets.token_urlsafe(12)
    now = _now()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO feedback (id, vorgang_id, text, screen, letzte_antwort, created)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (fid, vorgang_id, text, screen, letzte_antwort, now),
        )
        conn.commit()
    finally:
        conn.close()
    log.info(
        "Feedback gespeichert: feedback_id=%s vorgang_id=%s textlaenge=%d",
        fid, vorgang_id, len(text.encode("utf-8")),
    )
    return {"id": fid, "vorgang_id": vorgang_id, "created": now}
