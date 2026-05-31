"""Tests für repair/report.py (PROJ-44).

Läuft OHNE Server und OHNE OpenAI-Backend.
Nutzt repair.cards.validate() um valide Karten zu erzeugen.
"""
import sys
import os

# sicherstellen, dass das webapp-Verzeichnis im sys.path ist
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from repair import cards
from repair import report


# ─── Hilfsfunktionen für Test-State-Aufbau ────────────────────────────────────

_TRUST_HOCH = {
    "level": "hoch",
    "quelle": "KI-Diagnose",
    "konfidenz": "hoch",
    "hinweis": "Verlässliche Einschätzung",
}

_TRUST_UNKLAR = {
    "level": "niedrig",
    "quelle": "KI-Fallback",
    "konfidenz": "unklar",
    "hinweis": "Nicht belegte KI-Einschätzung",
}

_TRUST_MITTEL = {
    "level": "mittel",
    "quelle": "KI-Analyse",
    "konfidenz": "mittel",
    "hinweis": "Mittelgute Datengrundlage",
}


def _karte(typ: str, daten: dict) -> dict:
    return cards.validate(typ, daten)


def _meta(vid: str = "V-TEST-001") -> dict:
    return {
        "id": vid,
        "created": "2026-05-31T10:00:00",
        "updated": "2026-05-31T11:30:00",
    }


def _state_vollstaendig() -> dict:
    """Vollständiger State mit allen relevanten Karten."""
    return {
        "lang": "de",
        "karten": [
            _karte("aufnahme", {
                "symptom": "Gerät startet nicht mehr",
                "kategorie": "Haushaltsgeräte",
                "bedingungen": "Nach Sturz",
                "seit_wann": "Gestern",
                "getestet": "Neustart versucht, Kabel geprüft",
                "eigentum": {
                    "ist_eigentuemer": True,
                    "kostentraeger": "",
                },
            }),
            _karte("diagnose", {
                "kandidaten": [
                    {"name": "Defektes Netzteil", "beschreibung": "Spannung am Eingang fehlt"},
                    {"name": "Kurzschluss auf Platine"},
                ],
                "unklar": False,
                "trust": _TRUST_HOCH,
            }),
            _karte("ampel", {
                "achsen": {
                    "sicherheit":   "gruen",
                    "komplexitaet": "gelb",
                    "kosten":       "gelb",
                    "machbarkeit":  "gruen",
                },
                "gesamt": "gelb",
                "begruendung": "Mittlere Komplexität, sicher durchführbar",
                "trust": _TRUST_HOCH,
            }),
            _karte("vergleich", {
                "empfehlung": "repair",
                "begruendung": "Reparatur lohnt sich — Teile verfügbar",
                "trust": _TRUST_HOCH,
            }),
        ],
    }


def _state_fremdgeraet() -> dict:
    """State mit fremdem Gerät und Datenlöschungs-Hinweis."""
    return {
        "lang": "de",
        "karten": [
            _karte("aufnahme", {
                "symptom": "Display kaputt",
                "eigentum": {
                    "ist_eigentuemer": False,
                    "kostentraeger": "Arbeitgeber",
                },
            }),
            _karte("hinweis", {
                "art": "eigentum",
                "text": "Gerät gehört einem Dritten — Zustimmung einholen.",
                "schwere": "warnung",
            }),
            _karte("hinweis", {
                "art": "datenloeschung",
                "text": "Daten vor Abgabe sichern und löschen!",
                "schwere": "kritisch",
            }),
            _karte("ampel", {
                "achsen": {
                    "sicherheit":   "gruen",
                    "komplexitaet": "rot",
                    "kosten":       "rot",
                    "machbarkeit":  "gelb",
                },
                "gesamt": "rot",
                "begruendung": "Display-Tausch ist komplex und teuer",
                "trust": _TRUST_MITTEL,
            }),
            _karte("vergleich", {
                "empfehlung": "pro",
                "begruendung": "Fachwerkstatt empfohlen",
                "trust": _TRUST_MITTEL,
            }),
        ],
    }


def _state_leer() -> dict:
    """Komplett leerer State — kein Vorgang begonnen."""
    return {"lang": "de", "karten": []}


def _state_mehrfachdefekte() -> dict:
    """State mit zwei Defekten (2 ampel-Karten)."""
    return {
        "lang": "de",
        "karten": [
            _karte("aufnahme", {
                "symptom": "Gerät heiß, Lüfter laut",
                "eigentum": {"ist_eigentuemer": True, "kostentraeger": ""},
            }),
            _karte("ampel", {
                "defekt": "Überhitzung",
                "achsen": {
                    "sicherheit":   "gelb",
                    "komplexitaet": "gruen",
                    "kosten":       "gruen",
                    "machbarkeit":  "gruen",
                },
                "gesamt": "gelb",
                "begruendung": "Lüfter reinigen ausreichend",
                "trust": _TRUST_HOCH,
            }),
            _karte("ampel", {
                "defekt": "Defekter Lüfter",
                "achsen": {
                    "sicherheit":   "rot",
                    "komplexitaet": "rot",
                    "kosten":       "gelb",
                    "machbarkeit":  "gelb",
                },
                "gesamt": "rot",
                "begruendung": "Austausch riskant ohne Fachkenntnisse",
                "trust": _TRUST_MITTEL,
            }),
            _karte("vergleich", {
                "empfehlung": "pro",
                "begruendung": "Wegen Lüfter-Defekt Profi empfohlen",
                "trust": _TRUST_MITTEL,
            }),
        ],
    }


def _state_ki_fallback() -> dict:
    """State mit unklar-Konfidenz (KI-Fallback)."""
    return {
        "lang": "de",
        "karten": [
            _karte("aufnahme", {
                "symptom": "Unbekanntes Problem",
            }),
            _karte("ampel", {
                "achsen": {
                    "sicherheit":   "gruen",
                    "komplexitaet": "gelb",
                    "kosten":       "gelb",
                    "machbarkeit":  "gruen",
                },
                "gesamt": "gelb",
                "begruendung": "Unsichere Datenbasis",
                "trust": _TRUST_UNKLAR,
            }),
            _karte("vergleich", {
                "empfehlung": "repair",
                "begruendung": "Versuchsweise Reparatur",
                "trust": _TRUST_UNKLAR,
            }),
        ],
    }


def _state_werkstatt_voll() -> dict:
    """Vollständiger State für werkstatt-Variante mit Anbieter, Ersatzteile, Medien, Erfolg."""
    return {
        "lang": "de",
        "medien": [
            {"art": "foto", "ref": "media/abc123.jpg", "hinweis": "Foto des Defekts"},
        ],
        "karten": [
            _karte("aufnahme", {
                "symptom": "Toaster heizt nicht mehr",
                "kategorie": "Haushaltsgeräte",
                "getestet": "Steckdose geprüft",
                "eigentum": {"ist_eigentuemer": True, "kostentraeger": ""},
            }),
            _karte("diagnose", {
                "kandidaten": [{"name": "Heizelement defekt"}],
                "unklar": False,
                "trust": _TRUST_HOCH,
            }),
            _karte("ampel", {
                "achsen": {
                    "sicherheit":   "rot",
                    "komplexitaet": "gelb",
                    "kosten":       "gruen",
                    "machbarkeit":  "gelb",
                },
                "gesamt": "rot",
                "begruendung": "Netzspannung — Vorsicht!",
                "trust": _TRUST_HOCH,
            }),
            _karte("vergleich", {
                "empfehlung": "pro",
                "begruendung": "Wegen Sicherheits-rot: Profi empfohlen",
                "trust": _TRUST_HOCH,
            }),
            _karte("schritte", {
                "schritte": [
                    {"titel": "Stecker ziehen", "safety": True, "danger": False, "handoff": False},
                    {"titel": "Gehäuse öffnen", "safety": False, "danger": False, "handoff": False},
                    {"titel": "Heizelement prüfen", "safety": False, "danger": True, "handoff": True},
                ],
                "garantie_hinweis": "Garantie bei Öffnen erlischt.",
                "misserfolg_pfad": "Bei Misserfolg: Profi hinzuziehen.",
                "trust": _TRUST_HOCH,
            }),
            _karte("hinweis", {
                "art": "sicherheit",
                "text": "Netzspannung! Stecker vor Öffnen ziehen.",
                "schwere": "kritisch",
            }),
            _karte("anbieter", {
                "eintraege": [
                    {"name": "Repair Café Mitte", "adresse": "Hauptstr. 1", "ort": "Berlin"},
                ],
            }),
            _karte("ersatzteil", {
                "eintraege": [
                    {"teil": "Heizelement 230V", "preis": "12,50 €"},
                ],
                "affiliate_hinweis": "Partnerlink — Provision möglich",
            }),
            _karte("erfolg", {
                "gespart_geld": "ca. 40 €",
                "gespart_co2": "ca. 2 kg CO₂",
                "mutmach_satz": "Gut gemacht — Reparatur erfolgreich!",
            }),
        ],
    }


# ─── Tests: sammle_report ─────────────────────────────────────────────────────

class TestSammleReport:
    def test_extrahiert_symptom(self):
        r = report.sammle_report(_state_vollstaendig(), _meta())
        assert r["symptom"] == "Gerät startet nicht mehr"

    def test_extrahiert_kategorie(self):
        r = report.sammle_report(_state_vollstaendig(), _meta())
        assert r["kategorie"] == "Haushaltsgeräte"

    def test_extrahiert_ampel_achsen(self):
        r = report.sammle_report(_state_vollstaendig(), _meta())
        assert len(r["ampeln"]) == 1
        assert r["ampeln"][0]["achsen"]["sicherheit"] == "gruen"
        assert r["ampeln"][0]["achsen"]["komplexitaet"] == "gelb"
        assert r["ampeln"][0]["gesamt"] == "gelb"

    def test_extrahiert_empfehlung(self):
        r = report.sammle_report(_state_vollstaendig(), _meta())
        assert r["empfehlung"] == "repair"
        assert "lohnt" in r["vergleich_begruendung"]

    def test_extrahiert_eigentum_eigentuemer(self):
        r = report.sammle_report(_state_vollstaendig(), _meta())
        assert r["ist_eigentuemer"] is True
        assert r["ist_fremd"] is False

    def test_extrahiert_eigentum_fremd(self):
        r = report.sammle_report(_state_fremdgeraet(), _meta())
        assert r["ist_eigentuemer"] is False
        assert r["ist_fremd"] is True
        assert r["kostentraeger"] == "Arbeitgeber"

    def test_meta_felder(self):
        r = report.sammle_report(_state_vollstaendig(), _meta("MEIN-VORGANG"))
        assert r["vid"] == "MEIN-VORGANG"
        assert "2026" in r["created"]

    def test_vollstaendig_flag_gesetzt(self):
        r = report.sammle_report(_state_vollstaendig(), _meta())
        assert r["is_vollstaendig"] is True

    def test_leer_ist_unvollstaendig(self):
        r = report.sammle_report(_state_leer(), _meta())
        assert r["is_vollstaendig"] is False

    def test_hinweise_werden_gesammelt(self):
        r = report.sammle_report(_state_fremdgeraet(), _meta())
        arten = [h["art"] for h in r["hinweise"]]
        assert "eigentum" in arten
        assert "datenloeschung" in arten

    def test_kritische_hinweise_enthalten_fremd_und_daten(self):
        r = report.sammle_report(_state_fremdgeraet(), _meta())
        krit_arten = [h["art"] for h in r["kritische_hinweise"]]
        assert "eigentum" in krit_arten
        assert "datenloeschung" in krit_arten

    def test_ist_datentragend_bei_datenloeschungs_hinweis(self):
        r = report.sammle_report(_state_fremdgeraet(), _meta())
        assert r["ist_datentragend"] is True

    def test_mehrfachdefekte_zwei_ampeln(self):
        r = report.sammle_report(_state_mehrfachdefekte(), _meta())
        assert len(r["ampeln"]) == 2
        defekte_namen = [a["defekt"] for a in r["ampeln"]]
        assert "Überhitzung" in defekte_namen
        assert "Defekter Lüfter" in defekte_namen

    def test_gesamt_ampel_schwächstes_glied(self):
        r = report.sammle_report(_state_mehrfachdefekte(), _meta())
        # Eine ampel gelb, eine rot → Gesamt rot
        assert r["gesamt_ampel"] == "rot"

    def test_medien_werden_durchgereicht(self):
        r = report.sammle_report(_state_werkstatt_voll(), _meta())
        assert len(r["medien"]) == 1
        assert r["medien"][0]["art"] == "foto"

    def test_leerer_state_kein_crash(self):
        r = report.sammle_report({}, {})
        assert r["symptom"] == ""
        assert r["is_vollstaendig"] is False

    def test_ungueltige_karten_kein_crash(self):
        state = {"karten": [None, "nicht-dict", {"typ": "aufnahme"}, 42]}
        r = report.sammle_report(state, _meta())
        assert isinstance(r, dict)

    def test_trust_wird_extrahiert(self):
        r = report.sammle_report(_state_vollstaendig(), _meta())
        assert r["ampeln"][0]["trust"]["level"] == "hoch"
        assert r["vergleich_trust"]["konfidenz"] == "hoch"

    def test_anbieter_eintraege(self):
        r = report.sammle_report(_state_werkstatt_voll(), _meta())
        assert len(r["anbieter_eintraege"]) >= 1
        assert r["anbieter_eintraege"][0]["name"] == "Repair Café Mitte"

    def test_ersatzteil_eintraege_und_affiliate(self):
        r = report.sammle_report(_state_werkstatt_voll(), _meta())
        assert len(r["ersatzteil_eintraege"]) >= 1
        assert "Provision" in r["affiliate_hinweis"]


# ─── Tests: normalisiere_variante ─────────────────────────────────────────────

class TestNormalisiereVariante:
    def test_bekannte_variante_bleibt(self):
        assert report.normalisiere_variante("werkstatt") == "werkstatt"
        assert report.normalisiere_variante("eigenbeleg") == "eigenbeleg"
        assert report.normalisiere_variante("uebergabe") == "uebergabe"

    def test_unbekannte_variante_zu_default(self):
        assert report.normalisiere_variante("xyz") == report.DEFAULT_VARIANTE
        assert report.normalisiere_variante("WERKSTATT") == report.DEFAULT_VARIANTE  # case-sensitive

    def test_none_zu_default(self):
        assert report.normalisiere_variante(None) == report.DEFAULT_VARIANTE

    def test_leer_zu_default(self):
        assert report.normalisiere_variante("") == report.DEFAULT_VARIANTE
        assert report.normalisiere_variante("   ") == report.DEFAULT_VARIANTE

    def test_default_ist_uebergabe(self):
        assert report.DEFAULT_VARIANTE == "uebergabe"


# ─── Tests: varianten() ───────────────────────────────────────────────────────

class TestVarianten:
    def test_gibt_liste_zurueck(self):
        v = report.varianten()
        assert isinstance(v, list)
        assert len(v) >= 2

    def test_default_zuerst(self):
        v = report.varianten()
        assert v[0]["key"] == report.DEFAULT_VARIANTE

    def test_enthaelt_pflicht_varianten(self):
        keys = [v["key"] for v in report.varianten()]
        assert "uebergabe" in keys
        assert "werkstatt" in keys

    def test_enthaelt_dateiname(self):
        for v in report.varianten():
            assert "dateiname" in v
            assert v["dateiname"]

    def test_deutsch_label(self):
        v = report.varianten("de")
        labels = [e["label"] for e in v]
        # Deutsches Label für uebergabe enthält "Übergabe"
        uebergabe = next(e for e in v if e["key"] == "uebergabe")
        assert "bergabe" in uebergabe["label"]  # Ü wird in verschiedenen Encodings manchmal unterschiedlich

    def test_englisch_label(self):
        v = report.varianten("en")
        uebergabe = next(e for e in v if e["key"] == "uebergabe")
        assert "Handover" in uebergabe["label"] or "handover" in uebergabe["label"].lower()

    def test_stabile_reihenfolge(self):
        v1 = report.varianten("de")
        v2 = report.varianten("de")
        assert [e["key"] for e in v1] == [e["key"] for e in v2]


# ─── Tests: render_markdown ───────────────────────────────────────────────────

class TestRenderMarkdown:
    def test_uebergabe_kein_crash(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "uebergabe")
        assert isinstance(out, str)
        assert len(out) > 100

    def test_werkstatt_kein_crash(self):
        out = report.render_markdown(_state_werkstatt_voll(), _meta(), "werkstatt")
        assert isinstance(out, str)

    def test_eigenbeleg_kein_crash(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "eigenbeleg")
        assert isinstance(out, str)

    def test_uebergabe_enthaelt_symptom(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "uebergabe")
        assert "Gerät startet nicht mehr" in out

    def test_uebergabe_enthaelt_ampel_level(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "uebergabe")
        # gelb sollte als Text oder Emoji auftauchen
        assert "gelb" in out or "🟡" in out

    def test_uebergabe_enthaelt_empfehlung(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "uebergabe")
        assert "Selbst reparieren" in out or "repair" in out.lower()

    def test_uebergabe_enthaelt_trust(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "uebergabe")
        assert "hoch" in out or "Vertrauen" in out

    def test_uebergabe_keine_affiliate_eintraege(self):
        # uebergabe-Variante: Ersatzteile/Affiliate dürfen nicht erscheinen
        out = report.render_markdown(_state_werkstatt_voll(), _meta(), "uebergabe")
        assert "Partnerlink" not in out
        assert "Heizelement 230V" not in out

    def test_werkstatt_enthaelt_affiliate(self):
        out = report.render_markdown(_state_werkstatt_voll(), _meta(), "werkstatt")
        assert "Partnerlink" in out or "Provision" in out

    def test_werkstatt_enthaelt_diagnose_kandidaten(self):
        out = report.render_markdown(_state_werkstatt_voll(), _meta(), "werkstatt")
        assert "Heizelement defekt" in out

    def test_werkstatt_enthaelt_medien(self):
        out = report.render_markdown(_state_werkstatt_voll(), _meta(), "werkstatt")
        assert "foto" in out or "media/abc123" in out

    def test_unvollstaendig_marker(self):
        out = report.render_markdown(_state_leer(), _meta(), "uebergabe")
        assert "unvollständig" in out or "in Bearbeitung" in out or "Bearbeitung" in out

    def test_mehrfachdefekte_beide_gelistet(self):
        out = report.render_markdown(_state_mehrfachdefekte(), _meta(), "uebergabe")
        assert "Überhitzung" in out
        assert "Lüfter" in out

    def test_mehrfachdefekte_gesamt(self):
        out = report.render_markdown(_state_mehrfachdefekte(), _meta(), "uebergabe")
        assert "schwächstes" in out or "Gesamt" in out

    def test_fremd_hervorgehoben(self):
        out = report.render_markdown(_state_fremdgeraet(), _meta(), "uebergabe")
        assert "Fremd" in out or "fremd" in out or "eigentum" in out.lower()

    def test_ki_fallback_kennzeichnung(self):
        out = report.render_markdown(_state_ki_fallback(), _meta(), "uebergabe")
        assert "Fallback" in out or "fallback" in out or "nicht belegt" in out

    def test_echte_umlaute(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "uebergabe")
        # Darf kein ASCII-Escaping enthalten (ä für ä etc.)
        assert "\\u00" not in out
        # Echte Umlaute müssen vorhanden sein
        assert "ä" in out or "ü" in out or "ö" in out or "Ü" in out

    def test_disclaimer_vorhanden(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "uebergabe")
        assert "KI" in out and ("Fehler" in out or "unverbindlich" in out)

    def test_vorgang_id_im_output(self):
        out = report.render_markdown(_state_vollstaendig(), _meta("TEST-999"), "uebergabe")
        assert "TEST-999" in out

    def test_unbekannte_variante_faellt_auf_uebergabe_zurueck(self):
        out = report.render_markdown(_state_vollstaendig(), _meta(), "unbekannt_xyz")
        assert isinstance(out, str)
        assert len(out) > 50


# ─── Tests: render_text ───────────────────────────────────────────────────────

class TestRenderText:
    def test_alle_varianten_kein_crash(self):
        for v in ["uebergabe", "werkstatt", "eigenbeleg"]:
            out = report.render_text(_state_vollstaendig(), _meta(), v)
            assert isinstance(out, str)

    def test_leer_kein_crash(self):
        out = report.render_text(_state_leer(), _meta(), "uebergabe")
        assert isinstance(out, str)

    def test_unvollstaendig_marker(self):
        out = report.render_text(_state_leer(), _meta(), "uebergabe")
        assert "UNVOLLSTÄNDIG" in out or "unvollständig" in out or "IN BEARBEITUNG" in out

    def test_enthaelt_symptom(self):
        out = report.render_text(_state_vollstaendig(), _meta(), "uebergabe")
        assert "Gerät startet nicht mehr" in out

    def test_enthaelt_ampel(self):
        out = report.render_text(_state_vollstaendig(), _meta(), "uebergabe")
        assert "grün" in out or "gruen" in out or "🟢" in out
        assert "gelb" in out or "🟡" in out

    def test_echte_umlaute(self):
        out = report.render_text(_state_vollstaendig(), _meta(), "uebergabe")
        assert "\\u00" not in out
        assert "ä" in out or "ü" in out or "ö" in out or "Ü" in out or "ß" in out

    def test_disclaimer_vorhanden(self):
        out = report.render_text(_state_vollstaendig(), _meta(), "uebergabe")
        assert "KI" in out

    def test_fremd_hervorgehoben(self):
        out = report.render_text(_state_fremdgeraet(), _meta(), "uebergabe")
        assert "FREMD" in out or "Fremd" in out or "Dritte" in out

    def test_mehrfachdefekte_beide_gelistet(self):
        out = report.render_text(_state_mehrfachdefekte(), _meta(), "uebergabe")
        assert "Überhitzung" in out
        assert "Lüfter" in out


# ─── Tests: render_html ───────────────────────────────────────────────────────

class TestRenderHtml:
    def test_alle_varianten_kein_crash(self):
        for v in ["uebergabe", "werkstatt", "eigenbeleg"]:
            out = report.render_html(_state_vollstaendig(), _meta(), v)
            assert isinstance(out, str)

    def test_vollstaendiges_html_dokument(self):
        out = report.render_html(_state_vollstaendig(), _meta(), "uebergabe")
        assert out.startswith("<!DOCTYPE html>")
        assert "<html" in out
        assert "</html>" in out
        assert "<head>" in out
        assert "<body>" in out

    def test_inline_style(self):
        out = report.render_html(_state_vollstaendig(), _meta(), "uebergabe")
        assert "<style>" in out

    def test_leer_kein_crash(self):
        out = report.render_html(_state_leer(), _meta(), "uebergabe")
        assert "<!DOCTYPE html>" in out

    def test_unvollstaendig_marker(self):
        out = report.render_html(_state_leer(), _meta(), "uebergabe")
        assert "Bearbeitung" in out or "unvollständig" in out

    def test_symptom_im_html(self):
        out = report.render_html(_state_vollstaendig(), _meta(), "uebergabe")
        assert "Gerät startet nicht mehr" in out

    def test_ampel_level_im_html(self):
        out = report.render_html(_state_vollstaendig(), _meta(), "uebergabe")
        assert "gelb" in out or "🟡" in out

    def test_empfehlung_im_html(self):
        out = report.render_html(_state_vollstaendig(), _meta(), "uebergabe")
        assert "Selbst reparieren" in out

    def test_trust_im_html(self):
        out = report.render_html(_state_vollstaendig(), _meta(), "uebergabe")
        assert "hoch" in out or "Vertrauen" in out

    def test_ki_fallback_kennzeichnung(self):
        out = report.render_html(_state_ki_fallback(), _meta(), "uebergabe")
        assert "Fallback" in out or "nicht belegt" in out

    def test_fremd_hervorgehoben(self):
        out = report.render_html(_state_fremdgeraet(), _meta(), "uebergabe")
        assert "Fremd" in out or "fremd" in out or "Dritte" in out.lower()

    def test_html_escaping_aktiv(self):
        # XSS-Test: Benutzereingabe mit < und > darf nicht ungescaped im HTML landen
        state = {
            "lang": "de",
            "karten": [
                _karte("aufnahme", {
                    "symptom": "<script>alert('xss')</script>",
                }),
            ],
        }
        out = report.render_html(state, _meta(), "uebergabe")
        assert "<script>alert" not in out
        assert "&lt;script&gt;" in out or "&#" in out or "&lt;" in out

    def test_echte_umlaute_in_html(self):
        out = report.render_html(_state_vollstaendig(), _meta(), "uebergabe")
        # html.escape escapt keine Umlaute — echte Umlaute müssen vorhanden sein
        assert "\\u00" not in out
        assert "ä" in out or "ü" in out or "ö" in out or "Ü" in out

    def test_disclaimer_vorhanden(self):
        out = report.render_html(_state_vollstaendig(), _meta(), "uebergabe")
        assert "KI" in out and ("Fehler" in out or "unverbindlich" in out)

    def test_werkstatt_enthaelt_affiliate(self):
        out = report.render_html(_state_werkstatt_voll(), _meta(), "werkstatt")
        assert "Provision" in out or "Partnerlink" in out

    def test_werkstatt_enthaelt_medien(self):
        out = report.render_html(_state_werkstatt_voll(), _meta(), "werkstatt")
        assert "foto" in out or "abc123" in out

    def test_mehrfachdefekte_beide_gelistet(self):
        out = report.render_html(_state_mehrfachdefekte(), _meta(), "uebergabe")
        assert "Überhitzung" in out
        assert "Lüfter" in out

    def test_mehrfachdefekte_gesamt(self):
        out = report.render_html(_state_mehrfachdefekte(), _meta(), "uebergabe")
        assert "schwächstes" in out or "Gesamt" in out

    def test_vorgang_id_im_html(self):
        out = report.render_html(_state_vollstaendig(), _meta("PROJ44-TEST"), "uebergabe")
        assert "PROJ44-TEST" in out


# ─── Tests: Sprache ───────────────────────────────────────────────────────────

class TestSprache:
    def test_state_lang_hat_vorrang(self):
        """state['lang'] überschreibt den lang-Parameter."""
        state = dict(_state_vollstaendig())
        state["lang"] = "en"
        out = report.render_markdown(state, _meta(), "uebergabe", lang="de")
        # Englischer Titel sollte erscheinen
        assert "Handover" in out or "Report" in out

    def test_englisch_render_markdown(self):
        state = dict(_state_vollstaendig())
        state["lang"] = "en"
        out = report.render_markdown(state, _meta(), "uebergabe")
        assert "Symptom" in out
        assert "Recommendation" in out or "recommendation" in out.lower()

    def test_englisch_render_text(self):
        state = dict(_state_vollstaendig())
        state["lang"] = "en"
        out = report.render_text(state, _meta(), "uebergabe")
        assert "HANDOVER" in out or "REPORT" in out

    def test_englisch_render_html(self):
        state = dict(_state_vollstaendig())
        state["lang"] = "en"
        out = report.render_html(state, _meta(), "uebergabe")
        assert "Recommendation" in out or "Risk Assessment" in out


# ─── Tests: Keine harten Fehler bei Randfällen ────────────────────────────────

class TestRobustheit:
    def test_keine_karten_key(self):
        """State ohne 'karten'-Key."""
        state = {"lang": "de"}
        for variante in ["uebergabe", "werkstatt", "eigenbeleg"]:
            assert isinstance(report.render_markdown(state, _meta(), variante), str)
            assert isinstance(report.render_text(state, _meta(), variante), str)
            assert isinstance(report.render_html(state, _meta(), variante), str)

    def test_leere_meta(self):
        for variante in ["uebergabe", "werkstatt"]:
            assert isinstance(report.render_markdown(_state_vollstaendig(), {}, variante), str)
            assert isinstance(report.render_html(_state_vollstaendig(), {}, variante), str)

    def test_karten_mit_fehlenden_pflichtfeldern(self):
        """Karten mit minimalen Daten dürfen nicht crashen."""
        state = {
            "lang": "de",
            "karten": [
                # aufnahme ohne eigentum-Objekt
                {"typ": "aufnahme", "daten": {"symptom": "Test"}},
            ],
        }
        r = report.sammle_report(state, _meta())
        assert r["ist_eigentuemer"] is None

    def test_none_state_kein_crash(self):
        # Auch ohne karten[] muss es laufen
        for fn in [report.render_markdown, report.render_text, report.render_html]:
            out = fn({}, {}, "uebergabe")
            assert isinstance(out, str)

    def test_ampel_ohne_defekt_feld(self):
        state = {
            "lang": "de",
            "karten": [
                _karte("ampel", {
                    "achsen": {
                        "sicherheit": "gruen", "komplexitaet": "gruen",
                        "kosten": "gruen", "machbarkeit": "gruen",
                    },
                    "gesamt": "gruen",
                    "begruendung": "Alles gut",
                    "trust": _TRUST_HOCH,
                }),
            ],
        }
        r = report.sammle_report(state, _meta())
        assert r["ampeln"][0]["defekt"] == ""

    def test_erfolg_karte_kein_crash(self):
        state = {
            "lang": "de",
            "karten": [_karte("erfolg", {"mutmach_satz": "Super gemacht!"})],
        }
        for fn in [report.render_markdown, report.render_text, report.render_html]:
            out = fn(state, _meta(), "uebergabe")
            assert "Super gemacht" in out

    def test_schwungrad_ampel_alle_gleich(self):
        """schwächstes Glied: alle grün → gesamt grün."""
        levels = ["gruen", "gruen", "gruen"]
        assert report._schwachstes_ampel_glied(levels) == "gruen"

    def test_schwungrad_ampel_einer_rot(self):
        levels = ["gruen", "gelb", "rot"]
        assert report._schwachstes_ampel_glied(levels) == "rot"

    def test_schwungrad_ampel_leer(self):
        assert report._schwachstes_ampel_glied([]) == "gruen"
