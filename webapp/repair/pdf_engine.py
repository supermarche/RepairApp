"""PDF-Engine für den Service-Point-Übergabe-Report (PROJ-44).

Kapselt die serverseitige HTML→PDF-Konvertierung via PyMuPDF (``fitz.Story``).
PyMuPDF ist ein reines Wheel (keine System-Abhängigkeit) und bereits als
Dependency in ``requirements.txt`` eingetragen (v1.27.2).

Lazy/robustes Import-Muster: das Modul bleibt importierbar, auch wenn PyMuPDF
fehlt (dann ist :func:`verfuegbar` ``False`` und :func:`html_zu_pdf` wirft
:exc:`PdfNichtVerfuegbar`). Scheitert das Rendern, wird die ursprüngliche
Ausnahme als Kontext weitergegeben — nie ein roher Crash.

Konfiguration:
    ``REPORT_PDF_ENABLED`` — Default ``1`` (an). Setze ``0``/``false``/``False``
    in ``.env``, um die PDF-Erzeugung zu deaktivieren (z. B. für Staging-
    Umgebungen ohne PyMuPDF-Wheel oder für Testläufe). Getter:
    ``config.report_pdf_enabled()``.
"""

from __future__ import annotations

import io
import logging

from . import config

log = logging.getLogger(__name__)

# ── Optionaler PyMuPDF-Import (lazy, beim Modulload versucht) ────────────────
try:
    import fitz as _fitz  # type: ignore[import]
    _FITZ_AVAILABLE = True
except Exception:
    _fitz = None  # type: ignore[assignment]
    _FITZ_AVAILABLE = False


class PdfNichtVerfuegbar(RuntimeError):
    """PDF-Erzeugung nicht möglich — fehlendes Modul, Konfiguration oder Render-Fehler.

    Wird vom Route-Handler in HTTP 503 ``{error, code:"pdf_unavailable"}``
    übersetzt (kein Crash, ehrliche Degradation D3).
    """


def verfuegbar() -> bool:
    """``True`` nur wenn PyMuPDF importierbar UND ``REPORT_PDF_ENABLED`` aktiv ist.

    Wirft nie eine Exception — Fehler führen zu ``False``.
    """
    try:
        return _FITZ_AVAILABLE and config.report_pdf_enabled()
    except Exception:
        return False


def html_zu_pdf(html: str) -> bytes:
    """Rendert ein vollständiges HTML-Dokument zu PDF-Bytes (A4, 36 pt Rand).

    Nutzt ``fitz.Story`` (PyMuPDF) für das In-Process-Rendering — keine
    externen Prozesse, kein Netz. Das HTML kann eine ``<style>``-Sektion
    enthalten; sie wird direkt durch die Story-Engine ausgewertet.

    Args:
        html: Vollständiges HTML-Dokument (inkl. ``<html>``/``<body>``-Tags
              und ggf. ``<style>``). Echte Umlaute/Emojis — kein ASCII-Escaping.

    Returns:
        PDF-Datei als ``bytes`` (beginnt mit ``b"%PDF"``).

    Raises:
        PdfNichtVerfuegbar: wenn PyMuPDF nicht installiert ist, per Konfiguration
            deaktiviert wurde oder das Rendering technisch scheitert.
    """
    if not verfuegbar():
        grund = (
            "PyMuPDF (fitz) ist nicht installiert."
            if not _FITZ_AVAILABLE
            else "PDF-Erzeugung ist per Konfiguration (REPORT_PDF_ENABLED=0) deaktiviert."
        )
        raise PdfNichtVerfuegbar(
            f"PDF-Erzeugung ist derzeit nicht verfügbar: {grund} "
            "Bitte den Markdown- oder Text-Download verwenden."
        )

    try:
        story = _fitz.Story(html=html)
        buf = io.BytesIO()
        writer = _fitz.DocumentWriter(buf)
        mediabox = _fitz.paper_rect("a4")
        where = mediabox + (36, 36, -36, -36)  # 36 pt Rand rundum
        more = 1
        while more:
            dev = writer.begin_page(mediabox)
            more, _ = story.place(where)
            story.draw(dev)
            writer.end_page()
        writer.close()
        return buf.getvalue()
    except Exception as exc:
        log.warning("PDF-Rendering fehlgeschlagen (%s: %s)", type(exc).__name__, exc)
        raise PdfNichtVerfuegbar(
            f"PDF konnte nicht erzeugt werden (technischer Fehler: {exc}). "
            "Bitte den Markdown- oder Text-Download verwenden."
        ) from exc
