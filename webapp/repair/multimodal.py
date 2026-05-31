"""Multimodaler Medien-Store (PROJ-27).

Speichert Fotos, Videos, Audio in webapp/media/ (gitignored).

Öffentliche API:
    save_medium(data, art, mime)→ {id, art, ref, hinweis, mime}
    get_medium(id)              → (bytes, content_type) | None
    get_medium_data_url(id)     → "data:<mime>;base64,…" | None   (für Vision, PROJ-31)
    transkribiere(audio_bytes)  → {text, source:"whisper|hinweis", hinweis?}

Typ/Größen-Limit: konfigurierbar über ``MAX_UPLOAD_BYTES`` (Default 10 MB).
Scheitert nie hart.
"""

from __future__ import annotations

import base64
import logging
import os
import secrets

from . import config

log = logging.getLogger(__name__)

# Medien-Verzeichnis: webapp/media/ (eine Ebene über repair/) — layout-abgeleitet,
# bewusst keine .env-Konfiguration (PROJ-30).
MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "media"))

_MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "application/pdf": ".pdf",
}

_EXT_TO_MIME: dict[str, str] = {v: k for k, v in _MIME_TO_EXT.items()}

# „dokument" (PROJ-31): Bild ODER PDF, das als Beleg ausgewertet wird (Typenschild,
# Rechnung, Anleitung). Bild-Dokumente teilen sich den Bild-MIME-Pfad mit „foto".
_ERLAUBTE_ARTEN = frozenset(["foto", "video", "audio", "dokument"])

# Bild-MIME-Typen, die ein Vision-Modell direkt verarbeiten kann.
BILD_MIMES = frozenset(["image/jpeg", "image/png", "image/webp", "image/gif"])


def _ensure_media_dir() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)


def save_medium(data: bytes | str | None, art: str = "foto", mime: str | None = None) -> dict:
    """Speichert ein Medium auf Disk und gibt {id, art, ref, hinweis, mime} zurück.

    ``data`` kann Bytes oder Data-URL (base64) sein. ``mime`` erlaubt es dem
    Aufrufer, beim Bytes-Pfad den echten Typ mitzugeben (z. B. ``application/pdf``
    aus einem multipart-Upload) — sonst gilt für rohe Bytes ``image/jpeg``.
    Scheitert nie hart — bei Fehler kommt ein freundlicher Hinweis.
    """
    try:
        _ensure_media_dir()
    except Exception:
        return {"id": "", "art": art, "ref": "", "hinweis": "Medien-Verzeichnis konnte nicht erstellt werden.", "mime": ""}

    art = (art or "foto").strip().lower()
    if art not in _ERLAUBTE_ARTEN:
        art = "foto"

    # Data-URL entpacken
    content_type = "image/jpeg"
    raw_bytes = b""

    if isinstance(data, str) and data.startswith("data:"):
        # data:image/jpeg;base64,...
        try:
            header, b64 = data.split(",", 1)
            mime_part = header.split(";")[0].replace("data:", "").strip()
            if mime_part in _MIME_TO_EXT:
                content_type = mime_part
            raw_bytes = base64.b64decode(b64.strip())
        except Exception:
            return {"id": "", "art": art, "ref": "", "hinweis": "Data-URL konnte nicht dekodiert werden.", "mime": ""}
    elif isinstance(data, bytes):
        raw_bytes = data
        mime = (mime or "").strip().lower()
        if mime in _MIME_TO_EXT:
            content_type = mime
    else:
        return {"id": "", "art": art, "ref": "", "hinweis": "Kein Medium übergeben.", "mime": ""}

    # Größen-Check — Limit aus .env (MAX_UPLOAD_BYTES), Default 10 MB (PROJ-30)
    max_bytes = config.max_upload_bytes()
    if len(raw_bytes) > max_bytes:
        mb = max_bytes / (1024 * 1024)
        return {"id": "", "art": art, "ref": "", "hinweis": f"Medium zu groß (max. {mb:.0f} MB).", "mime": ""}

    if not raw_bytes:
        return {"id": "", "art": art, "ref": "", "hinweis": "Medium ist leer.", "mime": ""}

    # Datei schreiben
    mid = secrets.token_urlsafe(12)
    ext = _MIME_TO_EXT.get(content_type, ".bin")
    filename = f"{mid}{ext}"
    filepath = os.path.join(MEDIA_DIR, filename)

    try:
        with open(filepath, "wb") as f:
            f.write(raw_bytes)
    except Exception as exc:
        log.warning("Medium-Speichern fehlgeschlagen (art=%s, %d Bytes): %s", art, len(raw_bytes), exc)
        return {"id": "", "art": art, "ref": "", "hinweis": f"Speichern fehlgeschlagen: {exc}"}

    # Nur Metadaten loggen — niemals die rohen Datei-Bytes.
    log.info("Medium gespeichert: id=%s art=%s typ=%s größe=%d Bytes",
             mid, art, content_type, len(raw_bytes))
    return {
        "id": mid,
        "art": art,
        "ref": f"/media/{mid}",
        "hinweis": "",
        "mime": content_type,
    }


def get_medium(mid: str) -> tuple[bytes, str] | None:
    """Lädt ein Medium von Disk.

    Gibt (bytes, content_type) zurück oder None wenn nicht gefunden.
    """
    mid = (mid or "").strip()
    if not mid or "/" in mid or ".." in mid:
        return None

    if not os.path.isdir(MEDIA_DIR):
        return None

    # Datei mit passender Extension suchen
    for filename in os.listdir(MEDIA_DIR):
        stem = os.path.splitext(filename)[0]
        if stem == mid:
            ext = os.path.splitext(filename)[1]
            content_type = _EXT_TO_MIME.get(ext, "application/octet-stream")
            filepath = os.path.join(MEDIA_DIR, filename)
            try:
                with open(filepath, "rb") as f:
                    return f.read(), content_type
            except Exception:
                return None
    return None


def get_medium_data_url(mid: str) -> str | None:
    """Lädt ein Medium und gibt es als base64-Data-URL zurück (für Vision, PROJ-31).

    Gibt None zurück, wenn das Medium nicht existiert oder nicht gelesen werden kann.
    Loggt nur die Medien-ID/Größe, nie die Bytes (PROJ-29).
    """
    result = get_medium(mid)
    if result is None:
        return None
    data_bytes, content_type = result
    try:
        b64 = base64.b64encode(data_bytes).decode("ascii")
    except Exception:
        return None
    log.debug("Medium als Data-URL aufbereitet: id=%s typ=%s größe=%d Bytes",
              mid, content_type, len(data_bytes))
    return f"data:{content_type};base64,{b64}"


def transkribiere(audio_bytes: bytes | None = None, lang: str = "de") -> dict:
    """Optionale Audio-Transkription via Whisper (falls Key gesetzt).

    ``lang`` wählt die Transkriptionssprache (``"de"`` oder ``"en"``); alles
    andere/leer/None wird auf ``"de"`` normalisiert.  Die Rückgabe-Form ist
    unverändert: ``{text, source:"whisper"}`` bei Erfolg, sonst
    ``{text:"", source:"hinweis", hinweis:"..."}``.  Scheitert nie hart.
    """
    # Sprach-Normalisierung: nur de/en zulässig, alles andere → de
    if not lang or lang not in ("de", "en"):
        lang = "de"

    if not audio_bytes:
        return {
            "text": "",
            "source": "hinweis",
            "hinweis": "Kein Audio übergeben — bitte Browser-Spracherkennung verwenden.",
        }

    # Whisper-Key prüfen
    whisper_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not whisper_key:
        return {
            "text": "",
            "source": "hinweis",
            "hinweis": "Keine Transkription verfügbar (kein OpenAI-Key). Bitte Browser-Spracherkennung verwenden.",
        }

    # Whisper via OpenAI-API
    try:
        from openai import OpenAI
        import tempfile

        client = OpenAI(api_key=whisper_key, max_retries=0)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model=config.whisper_model(),
                    file=f,
                    language=lang,
                )
            log.info("Transkription erfolgreich: source=whisper lang=%s (%d Bytes Audio)",
                     lang, len(audio_bytes))
            return {"text": result.text or "", "source": "whisper"}
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception as exc:
        log.warning("Transkription fehlgeschlagen: %s", exc)
        return {
            "text": "",
            "source": "hinweis",
            "hinweis": f"Transkription nicht verfügbar ({exc}). Bitte Text eingeben.",
        }
