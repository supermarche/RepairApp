"""Karten-basierter Report-Renderer für PROJ-44 Service-Point-Übergabe.

Liest ausschließlich state["karten"] (Liste von {typ, daten}), state["lang"]
und state["medien"] — NICHT das alte device/diagnosis-Monolith-Modell aus
export.py (das bleibt für PROJ-10 unberührt).

Öffentliche API:
    VARIANTEN: dict[str, dict]      key → {label_de, label_en, dateiname}
    DEFAULT_VARIANTE = "uebergabe"
    varianten(lang) -> list[dict]   [{key, label, dateiname}]
    normalisiere_variante(v, lang)  → DEFAULT_VARIANTE bei unbekannt/leer/None
    sammle_report(state, meta)      → normalisierter Report-Dict
    render_markdown(state, meta, variante, lang) -> str
    render_text(state, meta, variante, lang)     -> str
    render_html(state, meta, variante, lang)     -> str   vollständiges HTML-Dokument
"""

from __future__ import annotations

import html as _html_mod
from typing import Any

# ─── Varianten-Konfiguration ──────────────────────────────────────────────────

VARIANTEN: dict[str, dict] = {
    "uebergabe": {
        "label_de": "Kurz-Übergabe (Annahmestelle / Repair Café)",
        "label_en": "Short Handover (Drop-off / Repair Café)",
        "dateiname": "reparatur-uebergabe",
    },
    "werkstatt": {
        "label_de": "Vollprotokoll Werkstatt",
        "label_en": "Full Workshop Protocol",
        "dateiname": "reparatur-werkstattprotokoll",
    },
    "eigenbeleg": {
        "label_de": "Eigen-Beleg (für mich)",
        "label_en": "Personal Copy",
        "dateiname": "reparatur-eigenbeleg",
    },
}

DEFAULT_VARIANTE = "uebergabe"

# Stabile Reihenfolge: Default zuerst, dann restliche in Definitions-Reihenfolge
_VARIANTEN_REIHENFOLGE = ["uebergabe", "werkstatt", "eigenbeleg"]


def varianten(lang: str = "de") -> list[dict]:
    """Gibt alle Varianten als [{key, label, dateiname}] zurück.

    Sprache: 'de' oder 'en' — Default zuerst, Reihenfolge stabil.
    """
    lang = _normalisiere_lang(lang)
    label_key = "label_de" if lang == "de" else "label_en"
    return [
        {
            "key": key,
            "label": VARIANTEN[key][label_key],
            "dateiname": VARIANTEN[key]["dateiname"],
        }
        for key in _VARIANTEN_REIHENFOLGE
        if key in VARIANTEN
    ]


def normalisiere_variante(v: str | None, lang: str = "de") -> str:
    """Gibt die normalisierte Variante zurück — unbekannt/leer/None → DEFAULT_VARIANTE.

    Schlägt NIE fehl.
    """
    if not v or not isinstance(v, str):
        return DEFAULT_VARIANTE
    v = v.strip()
    if v in VARIANTEN:
        return v
    return DEFAULT_VARIANTE


# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────


def _normalisiere_lang(lang: str | None) -> str:
    lang = (lang or "de").strip().lower()
    return lang if lang in ("de", "en") else "de"


def _s(val: Any, default: str = "noch nicht ermittelt") -> str:
    """Robuste String-Konvertierung; None/leer/'null'/'none' → default."""
    if val is None or val == "" or (isinstance(val, str) and val.lower() in ("null", "none")):
        return default
    return str(val).strip()


def _e(text: Any) -> str:
    """HTML-Escaping — echte Umlaute/Emojis bleiben erhalten (html.escape escapt die nicht)."""
    return _html_mod.escape(str(text))


def _ampel_symbol(level: str) -> str:
    """Liefert Emoji + Label für ampel-Level gruen/gelb/rot."""
    return {
        "gruen": "🟢 grün",
        "gelb":  "🟡 gelb",
        "rot":   "🔴 rot",
    }.get(level, f"❔ {level}")


def _ampel_html_badge(level: str) -> str:
    css = {
        "gruen": "background:#dcfce7;color:#166534",
        "gelb":  "background:#fef9c3;color:#854d0e",
        "rot":   "background:#fee2e2;color:#991b1b",
    }.get(level, "background:#f0f0f0;color:#444")
    label = {"gruen": "🟢 grün", "gelb": "🟡 gelb", "rot": "🔴 rot"}.get(level, level)
    return f'<span style="display:inline-block;padding:.1em .5em;border-radius:4px;font-size:.85rem;font-weight:600;{css}">{_e(label)}</span>'


def _empfehlung_label(empfehlung: str, lang: str = "de") -> str:
    labels_de = {
        "repair":     "Selbst reparieren",
        "pro":        "Fachwerkstatt / Profi",
        "neu":        "Neuanschaffung",
        "entsorgung": "Entsorgen",
    }
    labels_en = {
        "repair":     "Self-repair",
        "pro":        "Professional workshop",
        "neu":        "Buy new",
        "entsorgung": "Dispose",
    }
    labels = labels_de if lang == "de" else labels_en
    return labels.get(empfehlung, empfehlung)


def _hinweis_art_label(art: str, lang: str = "de") -> str:
    labels_de = {
        "garantie":      "Garantie/Gewährleistung",
        "rueckruf":      "Rückruf",
        "datenloeschung": "Datenlöschung vor Abgabe",
        "sicherheit":    "Sicherheitshinweis",
        "eigentum":      "Fremdgerät / Eigentum",
    }
    labels_en = {
        "garantie":      "Warranty",
        "rueckruf":      "Recall",
        "datenloeschung": "Data deletion before handover",
        "sicherheit":    "Safety notice",
        "eigentum":      "Third-party device / ownership",
    }
    labels = labels_de if lang == "de" else labels_en
    return labels.get(art, art)


def _trust_badge_text(trust: dict, lang: str = "de") -> str:
    """Gibt eine lesbare Trust-Kennzeichnung zurück, KI-Fallback wenn konfidenz==unklar."""
    if not isinstance(trust, dict):
        return ""
    konfidenz = trust.get("konfidenz", "")
    level = _s(trust.get("level"), "")
    quelle = _s(trust.get("quelle"), "")
    hinweis = _s(trust.get("hinweis"), "")

    dot = {"hoch": "🟢", "mittel": "🟡", "niedrig": "🔴"}.get(level, "❔")
    if lang == "de":
        parts = [f"{dot} Vertrauen: {level}"]
        if quelle:
            parts.append(f"Quelle: {quelle}")
        if konfidenz == "unklar":
            parts.append("⚠ KI-Fallback (nicht belegt)")
        elif konfidenz:
            parts.append(f"Konfidenz: {konfidenz}")
        if hinweis and hinweis != "noch nicht ermittelt":
            parts.append(hinweis)
    else:
        parts = [f"{dot} Trust: {level}"]
        if quelle:
            parts.append(f"Source: {quelle}")
        if konfidenz == "unklar":
            parts.append("⚠ AI fallback (unverified)")
        elif konfidenz:
            parts.append(f"Confidence: {konfidenz}")
        if hinweis and hinweis != "noch nicht ermittelt":
            parts.append(hinweis)
    return " · ".join(parts)


def _schwachstes_ampel_glied(levels: list[str]) -> str:
    """Gibt das schwächste Glied zurück: rot < gelb < gruen."""
    priority = {"rot": 0, "gelb": 1, "gruen": 2}
    if not levels:
        return "gruen"
    return min(levels, key=lambda lv: priority.get(lv, 99))


# ─── Datenbeschaffung ─────────────────────────────────────────────────────────


def sammle_report(state: dict, meta: dict) -> dict:
    """Extrahiert alle Report-relevanten Felder aus state["karten"].

    Quelle der Wahrheit: state["karten"] (Liste {typ, daten}).
    Gibt immer einen vollständigen Dict zurück — fehlende Felder → Defaults.
    Schlägt NIE hart fehl.
    """
    karten = state.get("karten") if isinstance(state.get("karten"), list) else []
    lang = _normalisiere_lang(state.get("lang"))
    medien = state.get("medien") if isinstance(state.get("medien"), list) else []

    # Karten nach Typ sammeln (mehrere pro Typ möglich, z. B. mehrere ampel)
    karten_by_typ: dict[str, list[dict]] = {}
    for k in karten:
        if not isinstance(k, dict):
            continue
        typ = k.get("typ", "")
        daten = k.get("daten")
        if not isinstance(daten, dict):
            continue
        karten_by_typ.setdefault(typ, []).append(daten)

    # ── aufnahme ──────────────────────────────────────────────────────────────
    aufnahme_list = karten_by_typ.get("aufnahme", [])
    aufnahme = aufnahme_list[0] if aufnahme_list else {}
    symptom = _s(aufnahme.get("symptom"), "")
    kategorie = _s(aufnahme.get("kategorie"), "")
    bedingungen = _s(aufnahme.get("bedingungen"), "")
    seit_wann = _s(aufnahme.get("seit_wann"), "")
    getestet = _s(aufnahme.get("getestet"), "")
    eigentum_obj = aufnahme.get("eigentum") if isinstance(aufnahme.get("eigentum"), dict) else {}
    ist_eigentuemer = eigentum_obj.get("ist_eigentuemer")  # bool oder None
    kostentraeger = _s(eigentum_obj.get("kostentraeger"), "")

    # ── diagnose ──────────────────────────────────────────────────────────────
    diagnose_list = karten_by_typ.get("diagnose", [])
    diagnose = diagnose_list[0] if diagnose_list else {}
    diagnose_kandidaten = diagnose.get("kandidaten") if isinstance(diagnose.get("kandidaten"), list) else []
    diagnose_unklar = bool(diagnose.get("unklar", False))
    diagnose_trust = diagnose.get("trust") if isinstance(diagnose.get("trust"), dict) else {}

    # ── ampel(n) ──────────────────────────────────────────────────────────────
    ampel_list = karten_by_typ.get("ampel", [])
    ampeln: list[dict] = []
    for a in ampel_list:
        if not isinstance(a, dict):
            continue
        achsen = a.get("achsen") if isinstance(a.get("achsen"), dict) else {}
        ampeln.append({
            "defekt": _s(a.get("defekt"), ""),
            "gesamt": _s(a.get("gesamt"), ""),
            "begruendung": _s(a.get("begruendung"), ""),
            "achsen": {
                "sicherheit":   _s(achsen.get("sicherheit"), ""),
                "komplexitaet": _s(achsen.get("komplexitaet"), ""),
                "kosten":       _s(achsen.get("kosten"), ""),
                "machbarkeit":  _s(achsen.get("machbarkeit"), ""),
            },
            "trust": a.get("trust") if isinstance(a.get("trust"), dict) else {},
        })

    # Gesamt-Ampel über alle Defekte: schwächstes Glied
    alle_gesamt_level = [a["gesamt"] for a in ampeln if a["gesamt"]]
    gesamt_ampel = _schwachstes_ampel_glied(alle_gesamt_level) if alle_gesamt_level else ""

    # ── vergleich ─────────────────────────────────────────────────────────────
    vergleich_list = karten_by_typ.get("vergleich", [])
    vergleich = vergleich_list[0] if vergleich_list else {}
    empfehlung = _s(vergleich.get("empfehlung"), "")
    vergleich_begruendung = _s(vergleich.get("begruendung"), "")
    vergleich_trust = vergleich.get("trust") if isinstance(vergleich.get("trust"), dict) else {}

    # ── schritte ──────────────────────────────────────────────────────────────
    schritte_list = karten_by_typ.get("schritte", [])
    alle_schritte: list[dict] = []
    garantie_hinweis = ""
    misserfolg_pfad = ""
    for s in schritte_list:
        if not isinstance(s, dict):
            continue
        schritte_raw = s.get("schritte") if isinstance(s.get("schritte"), list) else []
        for schritt in schritte_raw:
            if isinstance(schritt, dict):
                alle_schritte.append({
                    "titel":   _s(schritt.get("titel"), ""),
                    "safety":  bool(schritt.get("safety", False)),
                    "danger":  bool(schritt.get("danger", False)),
                    "handoff": bool(schritt.get("handoff", False)),
                })
        if not garantie_hinweis:
            garantie_hinweis = _s(s.get("garantie_hinweis"), "")
        if not misserfolg_pfad:
            misserfolg_pfad = _s(s.get("misserfolg_pfad"), "")

    # ── hinweise ──────────────────────────────────────────────────────────────
    hinweis_list = karten_by_typ.get("hinweis", [])
    hinweise: list[dict] = []
    for h in hinweis_list:
        if not isinstance(h, dict):
            continue
        hinweise.append({
            "art":    _s(h.get("art"), ""),
            "text":   _s(h.get("text"), ""),
            "schwere": _s(h.get("schwere"), "info"),
        })

    # Fremd / datentragend erkennen
    ist_fremd = (ist_eigentuemer is False)
    ist_datentragend = any(
        h["art"] == "datenloeschung" for h in hinweise
    )
    kritische_hinweise = [
        h for h in hinweise
        if h["art"] in ("eigentum", "datenloeschung") or h["schwere"] in ("kritisch", "warnung")
    ]

    # ── anbieter ──────────────────────────────────────────────────────────────
    anbieter_list_raw = karten_by_typ.get("anbieter", [])
    anbieter_eintraege: list[dict] = []
    for a in anbieter_list_raw:
        eintr = a.get("eintraege") if isinstance(a.get("eintraege"), list) else []
        anbieter_eintraege.extend(e for e in eintr if isinstance(e, dict))

    # ── ersatzteil ────────────────────────────────────────────────────────────
    ersatzteil_list_raw = karten_by_typ.get("ersatzteil", [])
    ersatzteil_eintraege: list[dict] = []
    affiliate_hinweis = ""
    for et in ersatzteil_list_raw:
        eintr = et.get("eintraege") if isinstance(et.get("eintraege"), list) else []
        ersatzteil_eintraege.extend(e for e in eintr if isinstance(e, dict))
        if not affiliate_hinweis:
            affiliate_hinweis = _s(et.get("affiliate_hinweis"), "")

    # ── erfolg ────────────────────────────────────────────────────────────────
    erfolg_list = karten_by_typ.get("erfolg", [])
    erfolg = erfolg_list[0] if erfolg_list else {}
    gespart_geld = _s(erfolg.get("gespart_geld"), "")
    gespart_co2 = _s(erfolg.get("gespart_co2"), "")
    mutmach_satz = _s(erfolg.get("mutmach_satz"), "")

    # ── Vollständigkeit ───────────────────────────────────────────────────────
    is_vollstaendig = bool(ampeln or vergleich or diagnose_kandidaten)

    # ── Meta ──────────────────────────────────────────────────────────────────
    vid = _s(meta.get("id"), "")
    created = _s(meta.get("created"), "")
    updated = _s(meta.get("updated"), "")

    return {
        # Meta
        "vid": vid,
        "created": created,
        "updated": updated,
        "lang": lang,
        "is_vollstaendig": is_vollstaendig,
        # Gerät / Aufnahme
        "symptom": symptom,
        "kategorie": kategorie,
        "bedingungen": bedingungen,
        "seit_wann": seit_wann,
        "getestet": getestet,
        # Eigentum
        "ist_eigentuemer": ist_eigentuemer,
        "kostentraeger": kostentraeger,
        "ist_fremd": ist_fremd,
        "ist_datentragend": ist_datentragend,
        # Diagnose
        "diagnose_kandidaten": diagnose_kandidaten,
        "diagnose_unklar": diagnose_unklar,
        "diagnose_trust": diagnose_trust,
        # Ampeln (eine oder mehrere)
        "ampeln": ampeln,
        "gesamt_ampel": gesamt_ampel,
        # Vergleich / Empfehlung
        "empfehlung": empfehlung,
        "vergleich_begruendung": vergleich_begruendung,
        "vergleich_trust": vergleich_trust,
        # Schritte
        "alle_schritte": alle_schritte,
        "garantie_hinweis": garantie_hinweis,
        "misserfolg_pfad": misserfolg_pfad,
        # Hinweise
        "hinweise": hinweise,
        "kritische_hinweise": kritische_hinweise,
        # Anbieter / Ersatzteile
        "anbieter_eintraege": anbieter_eintraege,
        "ersatzteil_eintraege": ersatzteil_eintraege,
        "affiliate_hinweis": affiliate_hinweis,
        # Erfolg
        "gespart_geld": gespart_geld,
        "gespart_co2": gespart_co2,
        "mutmach_satz": mutmach_satz,
        # Medien
        "medien": medien,
    }


# ─── Markdown-Renderer ────────────────────────────────────────────────────────


def render_markdown(
    state: dict,
    meta: dict,
    variante: str,
    lang: str = "de",
) -> str:
    """Rendert einen Report als Markdown-Dokument."""
    lang = _normalisiere_lang(state.get("lang") or lang)
    variante = normalisiere_variante(variante, lang)
    r = sammle_report(state, meta)

    variante_label = VARIANTEN[variante]["label_de" if lang == "de" else "label_en"]
    titel_map_de = {
        "uebergabe":  "Reparatur-Übergabe-Report",
        "werkstatt":  "Werkstatt-Protokoll",
        "eigenbeleg": "Reparatur-Eigenbeleg",
    }
    titel_map_en = {
        "uebergabe":  "Repair Handover Report",
        "werkstatt":  "Workshop Protocol",
        "eigenbeleg": "Repair Personal Copy",
    }
    titel = (titel_map_de if lang == "de" else titel_map_en).get(variante, variante_label)

    lines: list[str] = []

    # Kopf
    lines.append(f"# {titel}")
    lines.append("")
    if lang == "de":
        lines.append(f"**Variante:** {variante_label}  ")
        lines.append(f"**Vorgang-ID:** `{r['vid']}`  ")
        lines.append(f"**Erstellt:** {r['created']}  ")
        lines.append(f"**Zuletzt:** {r['updated']}")
    else:
        lines.append(f"**Variant:** {variante_label}  ")
        lines.append(f"**Case ID:** `{r['vid']}`  ")
        lines.append(f"**Created:** {r['created']}  ")
        lines.append(f"**Updated:** {r['updated']}")

    if not r["is_vollstaendig"]:
        if lang == "de":
            lines.append("")
            lines.append("> ⚠ **in Bearbeitung / unvollständig** — Diagnose/Ampel/Empfehlung noch ausstehend.")
        else:
            lines.append("")
            lines.append("> ⚠ **In progress / incomplete** — Diagnosis/traffic light/recommendation still pending.")

    lines.append("")

    # Kritische Hinweise immer ganz oben (alle Varianten)
    if r["kritische_hinweise"]:
        lines.append("---")
        lines.append("")
        if lang == "de":
            lines.append("## ⚠ Wichtige Hinweise")
        else:
            lines.append("## ⚠ Important Notes")
        lines.append("")
        for h in r["kritische_hinweise"]:
            art_label = _hinweis_art_label(h["art"], lang)
            schwere_icon = {"kritisch": "🔴", "warnung": "🟡", "info": "ℹ️"}.get(h["schwere"], "ℹ️")
            lines.append(f"**{schwere_icon} {art_label}:** {h['text']}")
            lines.append("")

    # Gerät / Symptom
    if lang == "de":
        lines.append("## Gerät & Symptom")
    else:
        lines.append("## Device & Symptom")
    lines.append("")
    if r["symptom"]:
        lines.append(f"**{'Symptom' if lang == 'de' else 'Symptom'}:** {r['symptom']}")
    else:
        lines.append("_noch nicht ermittelt_" if lang == "de" else "_not yet determined_")
    if r["kategorie"]:
        lines.append(f"**{'Kategorie' if lang == 'de' else 'Category'}:** {r['kategorie']}")
    if r["bedingungen"]:
        lines.append(f"**{'Bedingungen' if lang == 'de' else 'Conditions'}:** {r['bedingungen']}")
    if r["seit_wann"]:
        lines.append(f"**{'Seit wann' if lang == 'de' else 'Since when'}:** {r['seit_wann']}")
    if r["getestet"] and variante in ("werkstatt", "eigenbeleg"):
        lines.append(f"**{'Bereits getestet' if lang == 'de' else 'Already tested'}:** {r['getestet']}")
    lines.append("")

    # Eigentum / Kostenträger (jede Variante)
    if lang == "de":
        lines.append("## Eigentum / Kostenträger")
    else:
        lines.append("## Ownership / Responsible Party")
    lines.append("")
    if r["ist_eigentuemer"] is True:
        lines.append("Eigentümer/in: **eigenes Gerät**" if lang == "de" else "Owner: **own device**")
    elif r["ist_eigentuemer"] is False:
        lines.append("⚠ **Fremdgerät** — nicht im eigenen Eigentum" if lang == "de" else "⚠ **Third-party device** — not owned by user")
        if r["kostentraeger"]:
            lines.append(f"{'Kostenträger' if lang == 'de' else 'Responsible party'}: {r['kostentraeger']}")
    else:
        lines.append("_nicht angegeben_" if lang == "de" else "_not specified_")
    lines.append("")

    # Warn-Ampel
    if lang == "de":
        lines.append("## Warn-Ampel")
    else:
        lines.append("## Risk Assessment")
    lines.append("")
    if r["ampeln"]:
        mehrfach = len(r["ampeln"]) > 1
        for idx, ampel in enumerate(r["ampeln"]):
            if mehrfach:
                defekt_label = ampel["defekt"] or f"Defekt {idx + 1}"
                lines.append(f"### {defekt_label}")
            achsen = ampel["achsen"]
            if lang == "de":
                lines.append(f"| Achse | Level |")
                lines.append(f"|---|---|")
                lines.append(f"| Sicherheit | {_ampel_symbol(achsen['sicherheit'])} |")
                lines.append(f"| Komplexität | {_ampel_symbol(achsen['komplexitaet'])} |")
                lines.append(f"| Kosten | {_ampel_symbol(achsen['kosten'])} |")
                lines.append(f"| Machbarkeit | {_ampel_symbol(achsen['machbarkeit'])} |")
                lines.append(f"| **Gesamt** | **{_ampel_symbol(ampel['gesamt'])}** |")
            else:
                lines.append(f"| Dimension | Level |")
                lines.append(f"|---|---|")
                lines.append(f"| Safety | {_ampel_symbol(achsen['sicherheit'])} |")
                lines.append(f"| Complexity | {_ampel_symbol(achsen['komplexitaet'])} |")
                lines.append(f"| Cost | {_ampel_symbol(achsen['kosten'])} |")
                lines.append(f"| Feasibility | {_ampel_symbol(achsen['machbarkeit'])} |")
                lines.append(f"| **Overall** | **{_ampel_symbol(ampel['gesamt'])}** |")
            if ampel["begruendung"]:
                lines.append(f"_{ampel['begruendung']}_")
            # Trust
            trust_text = _trust_badge_text(ampel["trust"], lang)
            if trust_text:
                lines.append(f"> {trust_text}")
            lines.append("")
        if mehrfach and r["gesamt_ampel"]:
            if lang == "de":
                lines.append(f"**Gesamt (schwächstes Glied):** {_ampel_symbol(r['gesamt_ampel'])}")
            else:
                lines.append(f"**Overall (weakest link):** {_ampel_symbol(r['gesamt_ampel'])}")
            lines.append("")
    else:
        lines.append("_noch nicht ermittelt_" if lang == "de" else "_not yet determined_")
        lines.append("")

    # Empfehlung
    if lang == "de":
        lines.append("## Empfehlung")
    else:
        lines.append("## Recommendation")
    lines.append("")
    if r["empfehlung"]:
        lines.append(f"**{_empfehlung_label(r['empfehlung'], lang)}**")
        if r["vergleich_begruendung"]:
            lines.append(f"_{r['vergleich_begruendung']}_")
        trust_text = _trust_badge_text(r["vergleich_trust"], lang)
        if trust_text:
            lines.append(f"> {trust_text}")
    else:
        lines.append("_noch nicht ermittelt_" if lang == "de" else "_not yet determined_")
    lines.append("")

    # Diagnose (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["diagnose_kandidaten"]:
        if lang == "de":
            lines.append("## Diagnose-Kandidaten")
        else:
            lines.append("## Diagnosis Candidates")
        lines.append("")
        for k in r["diagnose_kandidaten"]:
            if not isinstance(k, dict):
                continue
            name = _s(k.get("name") or k.get("titel") or k.get("ursache"), "Unbekannte Ursache")
            lines.append(f"- **{name}**")
            beschreibung = _s(k.get("beschreibung") or k.get("beschr"), "")
            if beschreibung:
                lines.append(f"  {beschreibung}")
        if r["diagnose_unklar"]:
            if lang == "de":
                lines.append("")
                lines.append("⚠ Ursache konnte nicht eindeutig eingegrenzt werden.")
            else:
                lines.append("")
                lines.append("⚠ Cause could not be clearly identified.")
        trust_text = _trust_badge_text(r["diagnose_trust"], lang)
        if trust_text:
            lines.append(f"> {trust_text}")
        lines.append("")

    # Schritte (alle Varianten: getestete; werkstatt/eigenbeleg: alle)
    if r["alle_schritte"]:
        if variante == "uebergabe":
            getestete = [s for s in r["alle_schritte"] if s.get("handoff") or s.get("danger") or s.get("safety")]
            # bei uebergabe: zeige alle Schritte (auch nicht-markierte) — sie sind bereits gemacht
            anzeige_schritte = r["alle_schritte"]
            if lang == "de":
                lines.append("## Bereits getestete / durchgeführte Schritte")
            else:
                lines.append("## Already Tested / Completed Steps")
        else:
            anzeige_schritte = r["alle_schritte"]
            if lang == "de":
                lines.append("## Reparatur-Schritte")
            else:
                lines.append("## Repair Steps")
        lines.append("")
        for i, schritt in enumerate(anzeige_schritte, 1):
            flags = []
            if schritt["safety"]:
                flags.append("⚡ Sicherheit" if lang == "de" else "⚡ Safety")
            if schritt["danger"]:
                flags.append("⚠ Gefahr" if lang == "de" else "⚠ Danger")
            if schritt["handoff"]:
                flags.append("🔧 Übergabe empfohlen" if lang == "de" else "🔧 Handover recommended")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            lines.append(f"{i}. {schritt['titel']}{flag_str}")
        if r["garantie_hinweis"] and variante in ("werkstatt", "eigenbeleg"):
            lines.append(f"_{r['garantie_hinweis']}_")
        if r["misserfolg_pfad"] and variante in ("werkstatt", "eigenbeleg"):
            lines.append(f"_{r['misserfolg_pfad']}_")
        lines.append("")

    # Alle Hinweise (werkstatt/eigenbeleg zeigen alle; uebergabe zeigt nur kritische — oben bereits)
    restliche_hinweise = [h for h in r["hinweise"] if h not in r["kritische_hinweise"]]
    if variante in ("werkstatt", "eigenbeleg") and r["hinweise"]:
        if lang == "de":
            lines.append("## Hinweise")
        else:
            lines.append("## Notes")
        lines.append("")
        for h in r["hinweise"]:
            art_label = _hinweis_art_label(h["art"], lang)
            schwere_icon = {"kritisch": "🔴", "warnung": "🟡", "info": "ℹ️"}.get(h["schwere"], "ℹ️")
            lines.append(f"**{schwere_icon} {art_label}:** {h['text']}")
        lines.append("")
    elif variante == "uebergabe" and restliche_hinweise:
        if lang == "de":
            lines.append("## Hinweise")
        else:
            lines.append("## Notes")
        lines.append("")
        for h in restliche_hinweise:
            art_label = _hinweis_art_label(h["art"], lang)
            schwere_icon = {"kritisch": "🔴", "warnung": "🟡", "info": "ℹ️"}.get(h["schwere"], "ℹ️")
            lines.append(f"{schwere_icon} **{art_label}:** {h['text']}")
        lines.append("")

    # Anbieter (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["anbieter_eintraege"]:
        if lang == "de":
            lines.append("## Reparatur-Anbieter")
        else:
            lines.append("## Repair Service Providers")
        lines.append("")
        for a in r["anbieter_eintraege"]:
            name = _s(a.get("name"), "")
            if name:
                lines.append(f"- **{name}**")
                adresse = _s(a.get("adresse") or a.get("ort"), "")
                if adresse:
                    lines.append(f"  {adresse}")
        lines.append("")

    # Ersatzteile (werkstatt + eigenbeleg) inkl. Affiliate-Kennzeichnung
    if variante in ("werkstatt", "eigenbeleg") and r["ersatzteil_eintraege"]:
        if lang == "de":
            lines.append("## Ersatzteile")
        else:
            lines.append("## Spare Parts")
        lines.append("")
        if r["affiliate_hinweis"]:
            lines.append(f"> ⚠ {r['affiliate_hinweis']}")
        for et in r["ersatzteil_eintraege"]:
            teil = _s(et.get("teil") or et.get("name"), "")
            preis = _s(et.get("preis"), "")
            lines.append(f"- {teil}" + (f" — {preis}" if preis else ""))
        lines.append("")

    # Medien (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["medien"]:
        if lang == "de":
            lines.append("## Medien-Anhänge")
        else:
            lines.append("## Media Attachments")
        lines.append("")
        for m in r["medien"]:
            if not isinstance(m, dict):
                continue
            art = _s(m.get("art"), "?")
            ref = _s(m.get("ref") or m.get("id"), "—")
            hinweis = _s(m.get("hinweis"), "")
            lines.append(f"- {art}: `{ref}`" + (f" ({hinweis})" if hinweis else ""))
        lines.append("")

    # Erfolg (alle Varianten, nur wenn vorhanden)
    if r["mutmach_satz"] or r["gespart_geld"] or r["gespart_co2"]:
        lines.append("---")
        lines.append("")
        if r["mutmach_satz"]:
            lines.append(f"🎉 {r['mutmach_satz']}")
        if r["gespart_geld"]:
            lines.append(f"💰 {'Gespart' if lang == 'de' else 'Saved'}: {r['gespart_geld']}")
        if r["gespart_co2"]:
            lines.append(f"🌱 CO₂ {'eingespart' if lang == 'de' else 'saved'}: {r['gespart_co2']}")
        lines.append("")

    # Disclaimer
    lines.append("---")
    lines.append("")
    if lang == "de":
        lines.append(
            "_Dieser Report wurde automatisch vom Reparatur-Helfer erzeugt. "
            "Alle Schätzwerte sind unverbindlich. KI-Einschätzungen können Fehler enthalten. "
            "Für Sicherheitsentscheidungen immer Fachleute hinzuziehen._"
        )
    else:
        lines.append(
            "_This report was generated automatically by the Repair Helper. "
            "All estimates are non-binding. AI assessments may contain errors. "
            "Always consult professionals for safety-critical decisions._"
        )

    return "\n".join(lines)


# ─── Text-Renderer ────────────────────────────────────────────────────────────


def render_text(
    state: dict,
    meta: dict,
    variante: str,
    lang: str = "de",
) -> str:
    """Rendert einen Report als ASCII-Plaintext."""
    lang = _normalisiere_lang(state.get("lang") or lang)
    variante = normalisiere_variante(variante, lang)
    r = sammle_report(state, meta)

    variante_label = VARIANTEN[variante]["label_de" if lang == "de" else "label_en"]
    titel_map_de = {
        "uebergabe":  "REPARATUR-ÜBERGABE-REPORT",
        "werkstatt":  "WERKSTATT-PROTOKOLL",
        "eigenbeleg": "REPARATUR-EIGENBELEG",
    }
    titel_map_en = {
        "uebergabe":  "REPAIR HANDOVER REPORT",
        "werkstatt":  "WORKSHOP PROTOCOL",
        "eigenbeleg": "REPAIR PERSONAL COPY",
    }
    titel = (titel_map_de if lang == "de" else titel_map_en).get(variante, variante_label.upper())

    def sep(char: str = "─", width: int = 60) -> str:
        return char * width

    lines: list[str] = []

    # Kopf
    lines += [sep("═"), titel, sep("═")]
    lines.append(f"Variante   : {variante_label}")
    lines.append(f"Vorgang-ID : {r['vid']}")
    lines.append(f"{'Erstellt' if lang == 'de' else 'Created'}   : {r['created']}")
    lines.append(f"{'Zuletzt' if lang == 'de' else 'Updated'}    : {r['updated']}")

    if not r["is_vollstaendig"]:
        lines.append(
            "Status     : ⚠ IN BEARBEITUNG / UNVOLLSTÄNDIG"
            if lang == "de"
            else "Status     : ⚠ IN PROGRESS / INCOMPLETE"
        )

    lines += ["", sep()]

    # Kritische Hinweise
    if r["kritische_hinweise"]:
        lines += ["", "⚠ WICHTIGE HINWEISE" if lang == "de" else "⚠ IMPORTANT NOTES", sep("─", 30)]
        for h in r["kritische_hinweise"]:
            art_label = _hinweis_art_label(h["art"], lang)
            schwere_icon = {"kritisch": "🔴", "warnung": "🟡", "info": "ℹ️"}.get(h["schwere"], "ℹ️")
            lines.append(f"{schwere_icon} {art_label.upper()}: {h['text']}")

    # Gerät / Symptom
    lines += ["", "GERÄT & SYMPTOM" if lang == "de" else "DEVICE & SYMPTOM", sep("─", 30)]
    if r["symptom"]:
        lines.append(f"Symptom    : {r['symptom']}")
    else:
        lines.append("noch nicht ermittelt" if lang == "de" else "not yet determined")
    if r["kategorie"]:
        lines.append(f"{'Kategorie' if lang == 'de' else 'Category'}  : {r['kategorie']}")
    if r["bedingungen"]:
        lines.append(f"{'Bedingungen' if lang == 'de' else 'Conditions'}: {r['bedingungen']}")
    if r["seit_wann"]:
        lines.append(f"Seit wann  : {r['seit_wann']}")
    if r["getestet"] and variante in ("werkstatt", "eigenbeleg"):
        lines.append(f"{'Getestet' if lang == 'de' else 'Tested'}    : {r['getestet']}")

    # Eigentum
    lines += ["", "EIGENTUM / KOSTENTRÄGER" if lang == "de" else "OWNERSHIP / RESPONSIBLE PARTY", sep("─", 30)]
    if r["ist_eigentuemer"] is True:
        lines.append("Eigenes Gerät" if lang == "de" else "Own device")
    elif r["ist_eigentuemer"] is False:
        lines.append("⚠ FREMDGERÄT — nicht im eigenen Eigentum" if lang == "de" else "⚠ THIRD-PARTY DEVICE")
        if r["kostentraeger"]:
            lines.append(f"{'Kostenträger' if lang == 'de' else 'Responsible'}: {r['kostentraeger']}")
    else:
        lines.append("nicht angegeben" if lang == "de" else "not specified")

    # Warn-Ampel
    lines += ["", "WARN-AMPEL" if lang == "de" else "RISK ASSESSMENT", sep("─", 30)]
    if r["ampeln"]:
        mehrfach = len(r["ampeln"]) > 1
        for idx, ampel in enumerate(r["ampeln"]):
            if mehrfach:
                defekt_label = ampel["defekt"] or f"Defekt {idx + 1}"
                lines += [f"  [{defekt_label}]"]
            achsen = ampel["achsen"]
            if lang == "de":
                lines.append(f"  Sicherheit   : {_ampel_symbol(achsen['sicherheit'])}")
                lines.append(f"  Komplexität  : {_ampel_symbol(achsen['komplexitaet'])}")
                lines.append(f"  Kosten       : {_ampel_symbol(achsen['kosten'])}")
                lines.append(f"  Machbarkeit  : {_ampel_symbol(achsen['machbarkeit'])}")
                lines.append(f"  Gesamt       : {_ampel_symbol(ampel['gesamt'])}")
            else:
                lines.append(f"  Safety       : {_ampel_symbol(achsen['sicherheit'])}")
                lines.append(f"  Complexity   : {_ampel_symbol(achsen['komplexitaet'])}")
                lines.append(f"  Cost         : {_ampel_symbol(achsen['kosten'])}")
                lines.append(f"  Feasibility  : {_ampel_symbol(achsen['machbarkeit'])}")
                lines.append(f"  Overall      : {_ampel_symbol(ampel['gesamt'])}")
            if ampel["begruendung"]:
                lines.append(f"  Begründung   : {ampel['begruendung']}")
            trust_text = _trust_badge_text(ampel["trust"], lang)
            if trust_text:
                lines.append(f"  {trust_text}")
        if mehrfach and r["gesamt_ampel"]:
            lines.append(f"  => {'Gesamt (schwächstes Glied)' if lang == 'de' else 'Overall (weakest link)'}: {_ampel_symbol(r['gesamt_ampel'])}")
    else:
        lines.append("noch nicht ermittelt" if lang == "de" else "not yet determined")

    # Empfehlung
    lines += ["", "EMPFEHLUNG" if lang == "de" else "RECOMMENDATION", sep("─", 30)]
    if r["empfehlung"]:
        lines.append(f"=> {_empfehlung_label(r['empfehlung'], lang)}")
        if r["vergleich_begruendung"]:
            lines.append(f"   {r['vergleich_begruendung']}")
        trust_text = _trust_badge_text(r["vergleich_trust"], lang)
        if trust_text:
            lines.append(f"   {trust_text}")
    else:
        lines.append("noch nicht ermittelt" if lang == "de" else "not yet determined")

    # Diagnose (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["diagnose_kandidaten"]:
        lines += ["", "DIAGNOSE-KANDIDATEN" if lang == "de" else "DIAGNOSIS CANDIDATES", sep("─", 30)]
        for k in r["diagnose_kandidaten"]:
            if not isinstance(k, dict):
                continue
            name = _s(k.get("name") or k.get("titel") or k.get("ursache"), "Unbekannte Ursache")
            lines.append(f"• {name}")
            beschreibung = _s(k.get("beschreibung") or k.get("beschr"), "")
            if beschreibung:
                lines.append(f"  {beschreibung}")
        if r["diagnose_unklar"]:
            lines.append("⚠ Keine eindeutige Eingrenzung möglich" if lang == "de" else "⚠ Cause unclear")
        trust_text = _trust_badge_text(r["diagnose_trust"], lang)
        if trust_text:
            lines.append(trust_text)

    # Schritte
    if r["alle_schritte"]:
        if variante == "uebergabe":
            label = "BEREITS GETESTETE / DURCHGEFÜHRTE SCHRITTE" if lang == "de" else "ALREADY TESTED / COMPLETED STEPS"
        else:
            label = "REPARATUR-SCHRITTE" if lang == "de" else "REPAIR STEPS"
        lines += ["", label, sep("─", 30)]
        for i, schritt in enumerate(r["alle_schritte"], 1):
            flags = []
            if schritt["safety"]:
                flags.append("⚡")
            if schritt["danger"]:
                flags.append("⚠")
            if schritt["handoff"]:
                flags.append("🔧")
            flag_str = " ".join(flags)
            lines.append(f"{i}. {flag_str + ' ' if flag_str else ''}{schritt['titel']}")
        if r["garantie_hinweis"] and variante in ("werkstatt", "eigenbeleg"):
            lines.append(f"   Garantie: {r['garantie_hinweis']}")
        if r["misserfolg_pfad"] and variante in ("werkstatt", "eigenbeleg"):
            lines.append(f"   Bei Misserfolg: {r['misserfolg_pfad']}")

    # Alle Hinweise (werkstatt/eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["hinweise"]:
        lines += ["", "HINWEISE" if lang == "de" else "NOTES", sep("─", 30)]
        for h in r["hinweise"]:
            art_label = _hinweis_art_label(h["art"], lang)
            schwere_icon = {"kritisch": "🔴", "warnung": "🟡", "info": "ℹ️"}.get(h["schwere"], "ℹ️")
            lines.append(f"{schwere_icon} {art_label}: {h['text']}")

    # Anbieter (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["anbieter_eintraege"]:
        lines += ["", "REPARATUR-ANBIETER" if lang == "de" else "REPAIR PROVIDERS", sep("─", 30)]
        for a in r["anbieter_eintraege"]:
            name = _s(a.get("name"), "")
            if name:
                lines.append(f"• {name}")

    # Ersatzteile (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["ersatzteil_eintraege"]:
        lines += ["", "ERSATZTEILE" if lang == "de" else "SPARE PARTS", sep("─", 30)]
        if r["affiliate_hinweis"]:
            lines.append(f"⚠ {r['affiliate_hinweis']}")
        for et in r["ersatzteil_eintraege"]:
            teil = _s(et.get("teil") or et.get("name"), "")
            preis = _s(et.get("preis"), "")
            lines.append(f"• {teil}" + (f" — {preis}" if preis else ""))

    # Medien (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["medien"]:
        lines += ["", "MEDIEN-ANHÄNGE" if lang == "de" else "MEDIA ATTACHMENTS", sep("─", 30)]
        for m in r["medien"]:
            if not isinstance(m, dict):
                continue
            art = _s(m.get("art"), "?")
            ref = _s(m.get("ref") or m.get("id"), "—")
            hinweis = _s(m.get("hinweis"), "")
            lines.append(f"• {art}: {ref}" + (f" ({hinweis})" if hinweis else ""))

    # Erfolg
    if r["mutmach_satz"] or r["gespart_geld"] or r["gespart_co2"]:
        lines += ["", sep("─", 30)]
        if r["mutmach_satz"]:
            lines.append(f"🎉 {r['mutmach_satz']}")
        if r["gespart_geld"]:
            lines.append(f"💰 {'Gespart' if lang == 'de' else 'Saved'}: {r['gespart_geld']}")
        if r["gespart_co2"]:
            lines.append(f"🌱 CO₂: {r['gespart_co2']}")

    lines += [
        "",
        sep("═"),
        "Automatisch erzeugt vom Reparatur-Helfer. Alle Schätzwerte unverbindlich."
        if lang == "de"
        else "Automatically generated by the Repair Helper. All estimates non-binding.",
        "KI-Einschätzungen können Fehler enthalten. Bei Sicherheitsfragen Fachleute hinzuziehen."
        if lang == "de"
        else "AI assessments may contain errors. Consult professionals for safety decisions.",
        sep("═"),
    ]

    return "\n".join(lines)


# ─── HTML-Renderer ────────────────────────────────────────────────────────────

_REPORT_CSS = """
* { box-sizing: border-box; }
body {
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  max-width: 760px;
  margin: 0 auto;
  padding: 1.5rem 1.2rem;
  color: #1a1a1a;
  line-height: 1.6;
  font-size: 15px;
}
h1 {
  font-size: 1.5rem;
  border-bottom: 3px solid #ff5a1f;
  padding-bottom: .4rem;
  margin-top: 0;
  color: #1a1a1a;
}
h2 {
  font-size: .88rem;
  font-weight: 700;
  color: #555;
  text-transform: uppercase;
  letter-spacing: .07em;
  margin: 2rem 0 .5rem;
  border-bottom: 1px solid #e5e5e5;
  padding-bottom: .25rem;
}
h3 { font-size: 1rem; margin: 1rem 0 .4rem; color: #333; }
p, li { margin: .3rem 0; }
ul, ol { padding-left: 1.4rem; }
.meta { color: #777; font-size: .82rem; margin-bottom: 1.2rem; }
.meta code { background: #f4f4f4; padding: .1em .4em; border-radius: 3px; font-size: .9em; }
.badge {
  display: inline-block;
  padding: .1em .55em;
  border-radius: 4px;
  font-size: .78rem;
  font-weight: 600;
  margin-left: .4em;
  vertical-align: middle;
}
.badge-warn    { background: #fef9c3; color: #854d0e; }
.badge-error   { background: #fee2e2; color: #991b1b; }
.badge-ok      { background: #dcfce7; color: #166534; }
.alert-box {
  border-radius: 6px;
  padding: .6rem 1rem;
  margin: .8rem 0;
  font-size: .93rem;
}
.alert-kritisch { background: #fee2e2; border-left: 4px solid #dc2626; }
.alert-warnung  { background: #fef9c3; border-left: 4px solid #ca8a04; }
.alert-info     { background: #eff6ff; border-left: 4px solid #3b82f6; }
.alert-fremd    { background: #fff7ed; border-left: 4px solid #ea580c; }
.inprogress-box {
  background: #fef9c3;
  border: 1px solid #fde68a;
  border-radius: 6px;
  padding: .5rem 1rem;
  margin-bottom: 1.2rem;
  font-size: .92rem;
  color: #78350f;
}
table.ampel {
  border-collapse: collapse;
  width: 100%;
  margin: .4rem 0;
  font-size: .92rem;
}
table.ampel th {
  text-align: left;
  padding: .3rem .6rem;
  background: #f8f8f8;
  border: 1px solid #e5e5e5;
  font-weight: 600;
  font-size: .8rem;
  text-transform: uppercase;
  letter-spacing: .04em;
}
table.ampel td {
  padding: .3rem .6rem;
  border: 1px solid #e5e5e5;
}
table.ampel tr:last-child td { font-weight: 700; background: #f8f8f8; }
.level-gruen { color: #16a34a; font-weight: 600; }
.level-gelb  { color: #ca8a04; font-weight: 600; }
.level-rot   { color: #dc2626; font-weight: 600; }
.empfehlung-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  padding: .6rem 1rem;
  margin: .4rem 0;
  font-size: 1rem;
}
.trust-line {
  color: #666;
  font-size: .82rem;
  font-style: italic;
  margin-top: .3rem;
}
.disclaimer {
  color: #999;
  font-size: .78rem;
  margin-top: 2.5rem;
  border-top: 1px solid #e5e5e5;
  padding-top: .8rem;
}
.label { font-weight: 600; }
@media print {
  body { padding: 0; font-size: 12px; }
  h1 { font-size: 1.2rem; }
  h2 { font-size: .78rem; }
}
"""


def render_html(
    state: dict,
    meta: dict,
    variante: str,
    lang: str = "de",
) -> str:
    """Rendert ein vollständiges HTML-Dokument (<!DOCTYPE html>…) für PyMuPDF fitz.Story."""
    lang = _normalisiere_lang(state.get("lang") or lang)
    variante = normalisiere_variante(variante, lang)
    r = sammle_report(state, meta)

    variante_label = VARIANTEN[variante]["label_de" if lang == "de" else "label_en"]
    titel_map_de = {
        "uebergabe":  "Reparatur-Übergabe",
        "werkstatt":  "Werkstatt-Protokoll",
        "eigenbeleg": "Reparatur-Eigenbeleg",
    }
    titel_map_en = {
        "uebergabe":  "Repair Handover",
        "werkstatt":  "Workshop Protocol",
        "eigenbeleg": "Personal Copy",
    }
    titel = (titel_map_de if lang == "de" else titel_map_en).get(variante, variante_label)

    def section(heading: str, content: str) -> str:
        return f"<h2>{_e(heading)}</h2>\n{content}\n"

    parts: list[str] = []

    # Kopf
    inprogress_badge = ""
    if not r["is_vollstaendig"]:
        inprogress_badge = (
            ' <span class="badge badge-warn">in Bearbeitung</span>'
            if lang == "de"
            else ' <span class="badge badge-warn">In Progress</span>'
        )

    parts.append(f"<h1>{_e(titel)}{inprogress_badge}</h1>")
    parts.append(
        f'<p class="meta">'
        f'<span class="label">{"Variante" if lang == "de" else "Variant"}:</span> {_e(variante_label)} &nbsp;·&nbsp; '
        f'<span class="label">{"Vorgang-ID" if lang == "de" else "Case ID"}:</span> <code>{_e(r["vid"])}</code> &nbsp;·&nbsp; '
        f'<span class="label">{"Erstellt" if lang == "de" else "Created"}:</span> {_e(r["created"])} &nbsp;·&nbsp; '
        f'<span class="label">{"Zuletzt" if lang == "de" else "Updated"}:</span> {_e(r["updated"])}'
        f"</p>"
    )

    if not r["is_vollstaendig"]:
        msg = (
            "⚠ <strong>in Bearbeitung / unvollständig</strong> — Diagnose, Ampel oder Empfehlung fehlen noch."
            if lang == "de"
            else "⚠ <strong>In progress / incomplete</strong> — Diagnosis, risk assessment, or recommendation still pending."
        )
        parts.append(f'<div class="inprogress-box">{msg}</div>')

    # Kritische Hinweise immer oben
    if r["kritische_hinweise"]:
        crit_html = ""
        for h in r["kritische_hinweise"]:
            art_label = _e(_hinweis_art_label(h["art"], lang))
            schwere = h["schwere"]
            css_cls = f"alert-{schwere}" if schwere in ("kritisch", "warnung", "info") else "alert-info"
            if h["art"] in ("eigentum",):
                css_cls = "alert-fremd"
            schwere_icon = {"kritisch": "🔴", "warnung": "🟡", "info": "ℹ️"}.get(schwere, "ℹ️")
            crit_html += (
                f'<div class="alert-box {css_cls}">'
                f"<strong>{schwere_icon} {art_label}:</strong> {_e(h['text'])}"
                f"</div>"
            )
        heading = "⚠ Wichtige Hinweise" if lang == "de" else "⚠ Important Notes"
        parts.append(section(heading, crit_html))

    # Gerät / Symptom
    sym_content = ""
    if r["symptom"]:
        sym_content += f"<p><span class='label'>{'Symptom' if lang == 'de' else 'Symptom'}:</span> {_e(r['symptom'])}</p>"
    else:
        sym_content += f"<p><em>{'noch nicht ermittelt' if lang == 'de' else 'not yet determined'}</em></p>"
    if r["kategorie"]:
        sym_content += f"<p><span class='label'>{'Kategorie' if lang == 'de' else 'Category'}:</span> {_e(r['kategorie'])}</p>"
    if r["bedingungen"]:
        sym_content += f"<p><span class='label'>{'Bedingungen' if lang == 'de' else 'Conditions'}:</span> {_e(r['bedingungen'])}</p>"
    if r["seit_wann"]:
        sym_content += f"<p><span class='label'>{'Seit wann' if lang == 'de' else 'Since when'}:</span> {_e(r['seit_wann'])}</p>"
    if r["getestet"] and variante in ("werkstatt", "eigenbeleg"):
        sym_content += f"<p><span class='label'>{'Bereits getestet' if lang == 'de' else 'Already tested'}:</span> {_e(r['getestet'])}</p>"
    parts.append(section("Gerät & Symptom" if lang == "de" else "Device & Symptom", sym_content))

    # Eigentum / Kostenträger
    if r["ist_eigentuemer"] is True:
        eig_content = f"<p>{'Eigenes Gerät' if lang == 'de' else 'Own device'}</p>"
    elif r["ist_eigentuemer"] is False:
        warn_text = "⚠ <strong>Fremdgerät</strong> — nicht im eigenen Eigentum" if lang == "de" else "⚠ <strong>Third-party device</strong>"
        eig_content = f'<div class="alert-box alert-fremd">{warn_text}</div>'
        if r["kostentraeger"]:
            eig_content += f"<p><span class='label'>{'Kostenträger' if lang == 'de' else 'Responsible party'}:</span> {_e(r['kostentraeger'])}</p>"
    else:
        eig_content = f"<p><em>{'nicht angegeben' if lang == 'de' else 'not specified'}</em></p>"
    parts.append(section("Eigentum / Kostenträger" if lang == "de" else "Ownership / Responsible Party", eig_content))

    # Warn-Ampel
    if r["ampeln"]:
        ampel_html = ""
        mehrfach = len(r["ampeln"]) > 1
        for idx, ampel in enumerate(r["ampeln"]):
            if mehrfach:
                defekt_label = ampel["defekt"] or f"Defekt {idx + 1}"
                ampel_html += f"<h3>{_e(defekt_label)}</h3>"
            achsen = ampel["achsen"]
            if lang == "de":
                rows = [
                    ("Sicherheit",  achsen["sicherheit"]),
                    ("Komplexität", achsen["komplexitaet"]),
                    ("Kosten",      achsen["kosten"]),
                    ("Machbarkeit", achsen["machbarkeit"]),
                    ("Gesamt",      ampel["gesamt"]),
                ]
            else:
                rows = [
                    ("Safety",      achsen["sicherheit"]),
                    ("Complexity",  achsen["komplexitaet"]),
                    ("Cost",        achsen["kosten"]),
                    ("Feasibility", achsen["machbarkeit"]),
                    ("Overall",     ampel["gesamt"]),
                ]
            table_rows = ""
            for label_row, level in rows:
                css_cls = f"level-{level}" if level in ("gruen", "gelb", "rot") else ""
                symbol = _ampel_symbol(level)
                table_rows += f"<tr><td>{_e(label_row)}</td><td class='{css_cls}'>{_e(symbol)}</td></tr>"
            ampel_html += f'<table class="ampel"><tr><th>{"Achse" if lang == "de" else "Dimension"}</th><th>Level</th></tr>{table_rows}</table>'
            if ampel["begruendung"]:
                ampel_html += f"<p><em>{_e(ampel['begruendung'])}</em></p>"
            trust_text = _trust_badge_text(ampel["trust"], lang)
            if trust_text:
                ampel_html += f'<p class="trust-line">{_e(trust_text)}</p>'
        if mehrfach and r["gesamt_ampel"]:
            label_gesamt = "Gesamt (schwächstes Glied)" if lang == "de" else "Overall (weakest link)"
            css_cls = f"level-{r['gesamt_ampel']}"
            ampel_html += (
                f"<p><span class='label'>{_e(label_gesamt)}:</span> "
                f"<span class='{css_cls}'>{_e(_ampel_symbol(r['gesamt_ampel']))}</span></p>"
            )
    else:
        ampel_html = f"<p><em>{'noch nicht ermittelt' if lang == 'de' else 'not yet determined'}</em></p>"
    parts.append(section("Warn-Ampel" if lang == "de" else "Risk Assessment", ampel_html))

    # Empfehlung
    if r["empfehlung"]:
        empf_text = _empfehlung_label(r["empfehlung"], lang)
        empf_html = f'<div class="empfehlung-box"><strong>{_e(empf_text)}</strong>'
        if r["vergleich_begruendung"]:
            empf_html += f"<p>{_e(r['vergleich_begruendung'])}</p>"
        empf_html += "</div>"
        trust_text = _trust_badge_text(r["vergleich_trust"], lang)
        if trust_text:
            empf_html += f'<p class="trust-line">{_e(trust_text)}</p>'
    else:
        empf_html = f"<p><em>{'noch nicht ermittelt' if lang == 'de' else 'not yet determined'}</em></p>"
    parts.append(section("Empfehlung" if lang == "de" else "Recommendation", empf_html))

    # Diagnose (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["diagnose_kandidaten"]:
        diag_items = ""
        for k in r["diagnose_kandidaten"]:
            if not isinstance(k, dict):
                continue
            name = _s(k.get("name") or k.get("titel") or k.get("ursache"), "Unbekannte Ursache")
            beschreibung = _s(k.get("beschreibung") or k.get("beschr"), "")
            diag_items += f"<li><strong>{_e(name)}</strong>"
            if beschreibung:
                diag_items += f"<br><small>{_e(beschreibung)}</small>"
            diag_items += "</li>"
        diag_html = f"<ul>{diag_items}</ul>"
        if r["diagnose_unklar"]:
            diag_html += (
                f'<p><span class="badge badge-warn">{"⚠ Unklar" if lang == "de" else "⚠ Unclear"}</span> '
                + ("Keine eindeutige Eingrenzung möglich" if lang == "de" else "Cause could not be clearly identified")
                + "</p>"
            )
        trust_text = _trust_badge_text(r["diagnose_trust"], lang)
        if trust_text:
            diag_html += f'<p class="trust-line">{_e(trust_text)}</p>'
        parts.append(section("Diagnose-Kandidaten" if lang == "de" else "Diagnosis Candidates", diag_html))

    # Schritte
    if r["alle_schritte"]:
        if variante == "uebergabe":
            schritte_heading = "Bereits getestete / durchgeführte Schritte" if lang == "de" else "Already Tested / Completed Steps"
        else:
            schritte_heading = "Reparatur-Schritte" if lang == "de" else "Repair Steps"
        schritte_items = ""
        for schritt in r["alle_schritte"]:
            flags_html = ""
            if schritt["safety"]:
                flags_html += '<span class="badge badge-warn">⚡ Sicherheit</span> ' if lang == "de" else '<span class="badge badge-warn">⚡ Safety</span> '
            if schritt["danger"]:
                flags_html += '<span class="badge badge-error">⚠ Gefahr</span> ' if lang == "de" else '<span class="badge badge-error">⚠ Danger</span> '
            if schritt["handoff"]:
                flags_html += '<span class="badge" style="background:#f0f0f0;color:#444">🔧 Übergabe</span> ' if lang == "de" else '<span class="badge" style="background:#f0f0f0;color:#444">🔧 Handover</span> '
            schritte_items += f"<li>{_e(schritt['titel'])}{(' ' + flags_html) if flags_html else ''}</li>"
        schritte_html = f"<ol>{schritte_items}</ol>"
        if r["garantie_hinweis"] and variante in ("werkstatt", "eigenbeleg"):
            schritte_html += f"<p><em>{_e(r['garantie_hinweis'])}</em></p>"
        if r["misserfolg_pfad"] and variante in ("werkstatt", "eigenbeleg"):
            schritte_html += f"<p><em>{_e(r['misserfolg_pfad'])}</em></p>"
        parts.append(section(schritte_heading, schritte_html))

    # Alle Hinweise (werkstatt/eigenbeleg)
    restliche_hinweise = [h for h in r["hinweise"] if h not in r["kritische_hinweise"]]
    if variante in ("werkstatt", "eigenbeleg") and r["hinweise"]:
        hinweis_html = ""
        for h in r["hinweise"]:
            art_label = _e(_hinweis_art_label(h["art"], lang))
            schwere = h["schwere"]
            css_cls = f"alert-{schwere}" if schwere in ("kritisch", "warnung", "info") else "alert-info"
            schwere_icon = {"kritisch": "🔴", "warnung": "🟡", "info": "ℹ️"}.get(schwere, "ℹ️")
            hinweis_html += (
                f'<div class="alert-box {css_cls}">'
                f"<strong>{schwere_icon} {art_label}:</strong> {_e(h['text'])}"
                f"</div>"
            )
        parts.append(section("Hinweise" if lang == "de" else "Notes", hinweis_html))
    elif variante == "uebergabe" and restliche_hinweise:
        hinweis_html = ""
        for h in restliche_hinweise:
            art_label = _e(_hinweis_art_label(h["art"], lang))
            schwere_icon = {"kritisch": "🔴", "warnung": "🟡", "info": "ℹ️"}.get(h["schwere"], "ℹ️")
            hinweis_html += f"<p>{schwere_icon} <strong>{art_label}:</strong> {_e(h['text'])}</p>"
        parts.append(section("Hinweise" if lang == "de" else "Notes", hinweis_html))

    # Anbieter (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["anbieter_eintraege"]:
        anbieter_items = ""
        for a in r["anbieter_eintraege"]:
            name = _s(a.get("name"), "")
            if not name:
                continue
            anbieter_items += f"<li><strong>{_e(name)}</strong>"
            adresse = _s(a.get("adresse") or a.get("ort"), "")
            if adresse:
                anbieter_items += f"<br><small>{_e(adresse)}</small>"
            anbieter_items += "</li>"
        if anbieter_items:
            parts.append(section(
                "Reparatur-Anbieter" if lang == "de" else "Repair Service Providers",
                f"<ul>{anbieter_items}</ul>"
            ))

    # Ersatzteile (werkstatt + eigenbeleg) inkl. Affiliate
    if variante in ("werkstatt", "eigenbeleg") and r["ersatzteil_eintraege"]:
        et_html = ""
        if r["affiliate_hinweis"]:
            et_html += (
                f'<div class="alert-box alert-warnung">'
                f"⚠ {_e(r['affiliate_hinweis'])}"
                f"</div>"
            )
        et_items = ""
        for et in r["ersatzteil_eintraege"]:
            teil = _s(et.get("teil") or et.get("name"), "")
            preis = _s(et.get("preis"), "")
            et_items += f"<li>{_e(teil)}" + (f" — {_e(preis)}" if preis else "") + "</li>"
        et_html += f"<ul>{et_items}</ul>"
        parts.append(section("Ersatzteile" if lang == "de" else "Spare Parts", et_html))

    # Medien (werkstatt + eigenbeleg)
    if variante in ("werkstatt", "eigenbeleg") and r["medien"]:
        med_items = ""
        for m in r["medien"]:
            if not isinstance(m, dict):
                continue
            art = _e(_s(m.get("art"), "?"))
            ref = _e(_s(m.get("ref") or m.get("id"), "—"))
            hinweis = _s(m.get("hinweis"), "")
            med_items += (
                f"<li><span class='label'>{art}:</span> <code>{ref}</code>"
                + (f" <em>({_e(hinweis)})</em>" if hinweis else "")
                + "</li>"
            )
        parts.append(section(
            "Medien-Anhänge" if lang == "de" else "Media Attachments",
            f"<ul>{med_items}</ul>"
        ))

    # Erfolg
    if r["mutmach_satz"] or r["gespart_geld"] or r["gespart_co2"]:
        erfolg_html = ""
        if r["mutmach_satz"]:
            erfolg_html += f"<p>🎉 <strong>{_e(r['mutmach_satz'])}</strong></p>"
        if r["gespart_geld"]:
            erfolg_html += f"<p>💰 {'Gespart' if lang == 'de' else 'Saved'}: {_e(r['gespart_geld'])}</p>"
        if r["gespart_co2"]:
            erfolg_html += f"<p>🌱 CO₂: {_e(r['gespart_co2'])}</p>"
        parts.append(section("Erfolg" if lang == "de" else "Result", erfolg_html))

    # Disclaimer
    parts.append(
        '<p class="disclaimer">'
        + _e(
            "Dieser Report wurde automatisch vom Reparatur-Helfer erzeugt. "
            "Alle Schätzwerte sind unverbindlich. KI-Einschätzungen können Fehler enthalten. "
            "Für Sicherheitsentscheidungen immer Fachleute hinzuziehen."
            if lang == "de"
            else "This report was generated automatically by the Repair Helper. "
            "All estimates are non-binding. AI assessments may contain errors. "
            "Always consult professionals for safety-critical decisions."
        )
        + "</p>"
    )

    body = "\n".join(parts)
    doc_title = f"{titel} · {r['vid']}" if r["vid"] else titel
    return _wrap_html(doc_title, body)


def _wrap_html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{_e(title)}</title>
  <style>{_REPORT_CSS}</style>
</head>
<body>
{body}
</body>
</html>"""
