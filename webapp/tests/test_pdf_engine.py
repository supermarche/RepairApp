"""Tests für repair/pdf_engine.py (PROJ-44).

Abdeckung:
- verfuegbar() ist True in der Default-Umgebung (fitz installiert, ENV ungesetzt).
- html_zu_pdf(<HTML mit Umlauten/Emojis>) → nicht-leere bytes, beginnen mit b"%PDF".
- Mit REPORT_PDF_ENABLED="0": verfuegbar() False, html_zu_pdf raises PdfNichtVerfuegbar.
- config.report_pdf_enabled()-Parsing: "0"/"false"/"" → False; ungesetzt/"1"/"true" → True.

Lauf ohne Server (kein Flask, kein OpenAI):
    .venv/bin/python -m pytest tests/test_pdf_engine.py -q
"""

from __future__ import annotations

import os
import sys

# Sicherstellen, dass das webapp-Paket importierbar ist (auch ohne Install).
WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WEBAPP not in sys.path:
    sys.path.insert(0, WEBAPP)

import pytest

from repair import config
from repair.pdf_engine import PdfNichtVerfuegbar, html_zu_pdf, verfuegbar

# Ein einfaches HTML-Dokument mit Umlauten und Emojis zum Testen.
_TEST_HTML = """\
<html>
<head><style>body { font-family: sans-serif; }</style></head>
<body>
  <h1>Reparatur-Übergabe 🔧</h1>
  <p>Gerät: Waschmaschine — Symptom: Dreht nicht mehr</p>
  <ul>
    <li>Sicherheit: 🟢 Grün (alles in Ordnung)</li>
    <li>Aufwand: 🟡 Gelb (mittel)</li>
    <li>Kosten: Ö/Ü/Ä günstig</li>
  </ul>
</body>
</html>"""


# ── verfuegbar() ──────────────────────────────────────────────────────────────

def test_verfuegbar_default(monkeypatch):
    """In der Default-Umgebung (fitz installiert, ENV ungesetzt) ist verfuegbar() True."""
    monkeypatch.delenv("REPORT_PDF_ENABLED", raising=False)
    assert verfuegbar() is True


def test_verfuegbar_false_wenn_deaktiviert(monkeypatch):
    """verfuegbar() ist False, wenn REPORT_PDF_ENABLED=0."""
    monkeypatch.setenv("REPORT_PDF_ENABLED", "0")
    assert verfuegbar() is False


def test_verfuegbar_false_bei_false_string(monkeypatch):
    """verfuegbar() ist False, wenn REPORT_PDF_ENABLED=false."""
    monkeypatch.setenv("REPORT_PDF_ENABLED", "false")
    assert verfuegbar() is False


# ── html_zu_pdf() ─────────────────────────────────────────────────────────────

def test_html_zu_pdf_liefert_pdf_bytes(monkeypatch):
    """html_zu_pdf() liefert nicht-leere bytes, die mit b'%PDF' beginnen."""
    monkeypatch.delenv("REPORT_PDF_ENABLED", raising=False)
    result = html_zu_pdf(_TEST_HTML)
    assert isinstance(result, bytes), "Ergebnis muss bytes sein"
    assert len(result) > 0, "Ergebnis darf nicht leer sein"
    assert result[:4] == b"%PDF", f"Ergebnis muss mit b'%PDF' beginnen, beginnt mit {result[:10]!r}"


def test_html_zu_pdf_mit_umlauten_und_emojis(monkeypatch):
    """html_zu_pdf() verarbeitet Umlaute und Emojis ohne Exception."""
    monkeypatch.delenv("REPORT_PDF_ENABLED", raising=False)
    html_mit_sonderzeichen = (
        "<html><body>"
        "<h1>Übergabe-Protokoll für Öfen & Äpfel 🛠️</h1>"
        "<p>Straße, Größe, Höhe — alles kein Problem.</p>"
        "</body></html>"
    )
    result = html_zu_pdf(html_mit_sonderzeichen)
    assert result[:4] == b"%PDF"


def test_html_zu_pdf_wirft_wenn_deaktiviert(monkeypatch):
    """html_zu_pdf() wirft PdfNichtVerfuegbar, wenn REPORT_PDF_ENABLED=0."""
    monkeypatch.setenv("REPORT_PDF_ENABLED", "0")
    with pytest.raises(PdfNichtVerfuegbar):
        html_zu_pdf(_TEST_HTML)


def test_html_zu_pdf_wirft_wenn_false(monkeypatch):
    """html_zu_pdf() wirft PdfNichtVerfuegbar, wenn REPORT_PDF_ENABLED=False."""
    monkeypatch.setenv("REPORT_PDF_ENABLED", "False")
    with pytest.raises(PdfNichtVerfuegbar):
        html_zu_pdf(_TEST_HTML)


def test_pdf_nicht_verfuegbar_ist_runtime_error():
    """PdfNichtVerfuegbar ist eine RuntimeError-Subklasse."""
    exc = PdfNichtVerfuegbar("Test-Fehler")
    assert isinstance(exc, RuntimeError)


# ── config.report_pdf_enabled() ───────────────────────────────────────────────

@pytest.mark.parametrize("value,expected", [
    ("0", False),
    ("false", False),
    ("False", False),
    ("", False),
    ("1", True),
    ("true", True),
    ("True", True),
    ("yes", True),    # alles außer den vier Off-Werten → True (tolerant)
])
def test_report_pdf_enabled_parsing(monkeypatch, value, expected):
    """config.report_pdf_enabled() parst verschiedene Werte tolerant."""
    if value == "":
        # Leerer Wert: os.environ.get liefert "" wenn gesetzt aber leer
        monkeypatch.setenv("REPORT_PDF_ENABLED", "")
    else:
        monkeypatch.setenv("REPORT_PDF_ENABLED", value)
    assert config.report_pdf_enabled() is expected, (
        f"REPORT_PDF_ENABLED={value!r} → erwartet {expected}, "
        f"erhalten {config.report_pdf_enabled()}"
    )


def test_report_pdf_enabled_default_ist_true(monkeypatch):
    """config.report_pdf_enabled() ist True, wenn REPORT_PDF_ENABLED nicht gesetzt ist."""
    monkeypatch.delenv("REPORT_PDF_ENABLED", raising=False)
    assert config.report_pdf_enabled() is True
