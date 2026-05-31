"""Vision-gestützte Extraktion & Diagnose-Anreicherung (PROJ-31).

Schließt die Lücke zwischen Medien-Aufnahme (PROJ-27) und Diagnose: beigefügte
Fotos und Dokumente werden von einem Vision-fähigen Modell ausgewertet.

Zweistufig (siehe ``features/PROJ-31``):

* **Stufe 1 — Extraktion:** :func:`extrahiere` liest aus den Medien strukturiert
  Gerätekategorie/Modell (Typenschild), sichtbare Schäden, Kaufdatum/Händler
  (Rechnung) und Hinweise (Anleitung). Das Ergebnis wird dem Nutzer auf einem
  Bestätigungs-Screen gezeigt und ist dort **editierbar/verwerfbar**, bevor die
  Diagnose läuft.
* **Stufe 2 — Diagnose:** :func:`baue_vision_kontext` speist die **bestätigten**
  Felder in den Diagnose-Prompt; :func:`bilder_aus_medien` liefert die Bild-Evidenz
  (Data-URLs) für den multimodalen Diagnose-Call. Die eigentliche Diagnose bleibt
  in :mod:`repair.ai` (Schema unverändert).

Backend ist durchgehend OpenAI (konsistent zu :func:`repair.ai._resolve_backend`).
Das Vision-Modell kommt aus ``VISION_MODEL`` (``.env``); ohne Override gilt das
Cloud-Diagnose-Modell (``OPENAI_MODEL`` / ``gpt-4o-…``, das ebenfalls Vision kann).

**Scheitert nie hart** (D15 „warnen statt sperren"): ohne Vision-Backend, bei
Timeout, ungültiger Antwort oder fehlgeschlagener PDF-Konvertierung gibt es ein
Degradations-Objekt mit Hinweis — der aufrufende Code fällt auf Text-Diagnose
zurück. Es werden nie rohe Datei-Bytes geloggt, nur Metadaten (PROJ-29).
"""

from __future__ import annotations

import json
import logging

from . import ai, config, multimodal
from .multimodal import BILD_MIMES

log = logging.getLogger(__name__)


# ─── Backend-Wahl (konsistent zu ai._resolve_backend) ────────────────────────


def _resolve_vision_backend():
    """Liefert ``(client, model)`` für die Vision-Auswertung — oder ``(None, None)``,
    wenn kein OpenAI-Backend konfiguriert/verfügbar ist.

    Backend wie bei der Text-Diagnose (OpenAI-Cloud). Das Modell wird auf das
    Vision-Modell umgestellt: ``VISION_MODEL`` (Override aus ``.env``) hat Vorrang,
    sonst gilt das Cloud-Diagnose-Modell (``OPENAI_MODEL`` / ``gpt-4o-…``, das
    ebenfalls Vision kann).
    """
    client, diag_model = ai._resolve_backend()
    if client is None:
        return None, None
    model = config.vision_model() or diag_model
    return client, model


def vision_verfuegbar() -> bool:
    """True, wenn ein Vision-Backend konfiguriert/erreichbar ist."""
    client, _ = _resolve_vision_backend()
    return client is not None


# ─── Medien → Bild-Data-URLs (inkl. PDF-Konvertierung) ───────────────────────


def _iter_medien(medien) -> list[dict]:
    """Normalisiert die Eingabe auf eine Liste von ``{id, art, mime}``-Dicts.

    Akzeptiert Strings (reine IDs) ebenso wie Dicts aus ``state.medien``.
    """
    out: list[dict] = []
    for m in medien or []:
        if isinstance(m, str):
            out.append({"id": m, "art": "foto", "mime": ""})
        elif isinstance(m, dict) and m.get("id"):
            out.append({
                "id": str(m.get("id")),
                "art": str(m.get("art") or "foto"),
                "mime": str(m.get("mime") or ""),
            })
    return out


def _pdf_zu_bildern(pdf_bytes: bytes, max_seiten: int) -> tuple[list[str], str]:
    """Wandelt ein PDF in Seiten-Data-URLs (PNG). Optional über PyMuPDF.

    Gibt ``(data_urls, hinweis)`` zurück. Fehlt PyMuPDF oder scheitert die
    Konvertierung, ist ``data_urls`` leer und ``hinweis`` erklärt das — **kein
    Crash** (Edge-Case „Modell unterstützt PDF nicht direkt").
    """
    try:
        import fitz  # PyMuPDF — optionales, lazy importiertes Wheel
    except Exception:
        return [], ("PDF konnte nicht ausgewertet werden (PDF-Unterstützung nicht "
                    "installiert). Bitte ein Foto des Dokuments beifügen.")

    import base64

    urls: list[str] = []
    hinweis = ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        log.warning("PDF konnte nicht geöffnet werden: %s", exc)
        return [], "PDF konnte nicht gelesen werden — bitte ein Foto des Dokuments beifügen."

    try:
        seiten_gesamt = doc.page_count
        for i in range(min(seiten_gesamt, max_seiten)):
            try:
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=150)
                png = pix.tobytes("png")
                b64 = base64.b64encode(png).decode("ascii")
                urls.append(f"data:image/png;base64,{b64}")
            except Exception as exc:
                log.warning("PDF-Seite %d konnte nicht gerendert werden: %s", i, exc)
        if seiten_gesamt > max_seiten:
            hinweis = (f"PDF hat {seiten_gesamt} Seiten — nur die ersten {max_seiten} "
                       f"wurden ausgewertet.")
    finally:
        try:
            doc.close()
        except Exception:
            pass

    if not urls and not hinweis:
        hinweis = "PDF enthielt keine auswertbaren Seiten."
    return urls, hinweis


def bilder_aus_medien(medien, max_pdf_seiten: int | None = None) -> tuple[list[str], list[str]]:
    """Lädt aus Medien (IDs oder ``state.medien``-Dicts) die Bild-Evidenz.

    Bilder (jpg/png/webp/gif) werden als Data-URL geladen; PDFs serverseitig in
    Seitenbilder gewandelt. Audio/Video werden für die Bildauswertung übersprungen.

    Gibt ``(data_urls, hinweise)`` zurück. ``hinweise`` sammelt nicht-blockierende
    Meldungen (z. B. PDF gekürzt, Konvertierung nicht verfügbar).
    """
    if max_pdf_seiten is None:
        max_pdf_seiten = config.max_pdf_seiten()

    urls: list[str] = []
    hinweise: list[str] = []

    for m in _iter_medien(medien):
        art = m["art"]
        if art in ("audio", "video"):
            continue  # für die Bildauswertung irrelevant
        geladen = multimodal.get_medium(m["id"])
        if geladen is None:
            continue
        data_bytes, content_type = geladen

        if content_type == "application/pdf":
            pdf_urls, hinweis = _pdf_zu_bildern(data_bytes, max_pdf_seiten)
            urls.extend(pdf_urls)
            if hinweis:
                hinweise.append(hinweis)
        elif content_type in BILD_MIMES:
            url = multimodal.get_medium_data_url(m["id"])
            if url:
                urls.append(url)
        # andere Typen: still überspringen
    return urls, hinweise


# ─── Stufe 1: Extraktion ──────────────────────────────────────────────────────

EXTRAKT_SYSTEM_PROMPT = """\
Du wertest Fotos und Dokumente eines defekten Geräts aus. Aus den Bildern \
extrahierst du NUR, was wirklich SICHTBAR ist — du erfindest nichts.

Gib GENAU EIN JSON-Objekt aus, sonst nichts:
{
  "kategorie": {"wert": "Gerätekategorie, z.B. Waschmaschine", "konfidenz": "hoch|mittel|niedrig", "erkannt": true},
  "modell":    {"wert": "Modell-/Typbezeichnung vom Typenschild", "konfidenz": "hoch|mittel|niedrig", "erkannt": true},
  "schaeden":  [ {"wert": "sichtbarer Schaden/Auffälligkeit", "konfidenz": "hoch|mittel|niedrig"} ],
  "kaufdatum": {"wert": "Kaufdatum von einer Rechnung (TT.MM.JJJJ)", "konfidenz": "hoch|mittel|niedrig", "erkannt": true},
  "haendler":  {"wert": "Händler/Verkäufer von einer Rechnung", "konfidenz": "hoch|mittel|niedrig", "erkannt": true},
  "hinweise":  [ "relevanter gerätespezifischer Hinweis aus einer Anleitung" ]
}

Regeln:
- Setze "erkannt": false und "wert": "", wenn etwas NICHT zuverlässig sichtbar \
ist (unscharf, zu dunkel, nicht im Bild). Rate NICHT.
- "schaeden" und "hinweise" sind Listen; leer lassen ([]), wenn nichts erkennbar ist.
- DATENSCHUTZ: Übernimm aus Dokumenten NUR die fachlich nötigen Felder \
(Kaufdatum, Händler, Modell). Übernimm KEINE Namen, Adressen, Kunden- oder \
Kontonummern oder sonstige persönliche Daten.
- Antworte auf Deutsch.
"""

_KONFIDENZ = {"hoch", "mittel", "niedrig"}

# Skalare (Einzelwert-)Felder mit ihren erkannt/wert/konfidenz-Strukturen.
_SKALAR_FELDER = ("kategorie", "modell", "kaufdatum", "haendler")


def leere_felder() -> dict:
    """Leeres, schema-konformes Feld-Objekt (nichts erkannt)."""
    return {
        "kategorie": {"wert": "", "konfidenz": "niedrig", "erkannt": False},
        "modell": {"wert": "", "konfidenz": "niedrig", "erkannt": False},
        "schaeden": [],
        "kaufdatum": {"wert": "", "konfidenz": "niedrig", "erkannt": False},
        "haendler": {"wert": "", "konfidenz": "niedrig", "erkannt": False},
        "hinweise": [],
    }


def _norm_konfidenz(value) -> str:
    v = str(value or "").strip().lower()
    return v if v in _KONFIDENZ else "mittel"


def _norm_skalar(raw) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    wert = str(raw.get("wert") or "").strip()
    erkannt = bool(raw.get("erkannt", False)) and bool(wert)
    return {
        "wert": wert if erkannt else "",
        "konfidenz": _norm_konfidenz(raw.get("konfidenz")),
        "erkannt": erkannt,
    }


def _norm_liste(raw, mit_konfidenz: bool) -> list:
    out: list = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if isinstance(item, dict):
            wert = str(item.get("wert") or "").strip()
            if not wert:
                continue
            if mit_konfidenz:
                out.append({"wert": wert, "konfidenz": _norm_konfidenz(item.get("konfidenz"))})
            else:
                out.append(wert)
        elif isinstance(item, str):
            wert = item.strip()
            if wert:
                out.append({"wert": wert, "konfidenz": "mittel"} if mit_konfidenz else wert)
    return out


def normalisiere_felder(raw) -> dict:
    """Macht aus einer (KI- oder Nutzer-)Roh-Struktur ein schema-konformes Feld-Objekt."""
    raw = raw if isinstance(raw, dict) else {}
    felder = leere_felder()
    for key in _SKALAR_FELDER:
        felder[key] = _norm_skalar(raw.get(key))
    felder["schaeden"] = _norm_liste(raw.get("schaeden"), mit_konfidenz=True)
    felder["hinweise"] = _norm_liste(raw.get("hinweise"), mit_konfidenz=False)
    return felder


def _nichts_erkannt(felder: dict) -> bool:
    """True, wenn kein einziges Feld zuverlässig erkannt wurde."""
    if any(felder.get(k, {}).get("erkannt") for k in _SKALAR_FELDER):
        return False
    return not felder.get("schaeden") and not felder.get("hinweise")


def extrahiere(medien, text: str = "", lang: str = "de") -> dict:
    """Stufe 1 — extrahiert strukturierte Felder aus den beigefügten Medien.

    Gibt immer ein vollständiges Objekt zurück (scheitert nie hart):
        {
          "felder": {kategorie, modell, schaeden[], kaufdatum, haendler, hinweise[]},
          "source": "vision" | "no_vision_backend" | "vision_error" | "keine_medien",
          "hinweis": "...",          # nicht-blockierender Hinweis (Degradation/PDF)
          "bildAnzahl": int,          # Anzahl an das Modell gegebener Bilder
          "nichtsErkannt": bool,      # für den „nichts erkannt"-Zustand im UI
        }
    """
    bilder, medien_hinweise = bilder_aus_medien(medien)
    hinweis = " ".join(medien_hinweise).strip()

    if not bilder:
        # Keine auswertbaren Bilder (z. B. nur Audio, oder PDF-Konvertierung fehlte).
        return {
            "felder": leere_felder(),
            "source": "keine_medien",
            "hinweis": hinweis or "Keine auswertbaren Bilder/Dokumente beigefügt.",
            "bildAnzahl": 0,
            "nichtsErkannt": True,
        }

    client, model = _resolve_vision_backend()
    if client is None:
        log.info("Vision-Extraktion: kein Vision-Backend → Degradation auf Text-Diagnose.")
        return {
            "felder": leere_felder(),
            "source": "no_vision_backend",
            "hinweis": ("Kein Vision-Backend konfiguriert — die Bilder konnten nicht "
                        "ausgewertet werden. Du kannst die Angaben unten manuell ergänzen "
                        "oder direkt mit der Text-Diagnose fortfahren."),
            "bildAnzahl": len(bilder),
            "nichtsErkannt": True,
        }

    timeout = config.llm_timeout()
    system_prompt = EXTRAKT_SYSTEM_PROMPT

    user_text = "Werte die beigefügten Bilder/Dokumente aus."
    if (text or "").strip():
        user_text += f"\n\nKontext des Nutzers (nur als Hilfe, nicht als Beleg): {text.strip()}"

    user_content = [{"type": "text", "text": user_text}]
    for url in bilder:
        user_content.append({"type": "image_url", "image_url": {"url": url}})

    log.info("Vision-Extraktion: Modell=%s, Bilder=%d", model, len(bilder))
    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            timeout=timeout,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        try:
            from . import protokoll_log
            protokoll_log.merke_usage(model, getattr(response, "usage", None))
        except Exception:
            pass
        content = response.choices[0].message.content
        if not content:
            raise ValueError("leere KI-Antwort")
        raw = json.loads(ai._clean_json_text(content))
        felder = normalisiere_felder(raw)
        nichts = _nichts_erkannt(felder)
        log.info("Vision-Extraktion erfolgreich: nichtsErkannt=%s", nichts)
        return {
            "felder": felder,
            "source": "vision",
            "hinweis": hinweis,
            "bildAnzahl": len(bilder),
            "nichtsErkannt": nichts,
        }
    except Exception as exc:
        log.warning("Vision-Extraktion fehlgeschlagen (%s: %s) → Degradation.",
                    type(exc).__name__, exc)
        return {
            "felder": leere_felder(),
            "source": "vision_error",
            "hinweis": ("Die Bildauswertung ist fehlgeschlagen. Du kannst die Angaben "
                        "unten manuell ergänzen oder mit der Text-Diagnose fortfahren."),
            "bildAnzahl": len(bilder),
            "nichtsErkannt": True,
        }


# ─── Stufe 2: bestätigte Felder → Diagnose-Kontext ───────────────────────────


def baue_vision_kontext(extraktion) -> str:
    """Formt die **bestätigten** Extraktionsfelder zu einem Prompt-Textblock.

    Nimmt entweder das ganze Extraktions-Objekt (mit ``felder``) oder direkt ein
    ``felder``-Dict. Es fließen ausschließlich die fachlichen Felder ein — kein
    roher Dokumenttext (PII-Leitplanke D10/PROJ-23). Gibt "" zurück, wenn nichts
    Verwertbares vorhanden ist (dann verhält sich die Diagnose wie ohne Bild).
    """
    if not isinstance(extraktion, dict):
        return ""
    felder = extraktion.get("felder") if isinstance(extraktion.get("felder"), dict) else extraktion
    if not isinstance(felder, dict):
        return ""

    zeilen: list[str] = []
    label = {
        "kategorie": "Gerätekategorie",
        "modell": "Modell",
        "kaufdatum": "Kaufdatum",
        "haendler": "Händler",
    }
    for key in _SKALAR_FELDER:
        feld = felder.get(key)
        if isinstance(feld, dict):
            wert = str(feld.get("wert") or "").strip()
            if wert:
                zeilen.append(f"- {label[key]}: {wert}")

    schaeden = [str(s.get("wert") if isinstance(s, dict) else s).strip()
                for s in (felder.get("schaeden") or [])]
    schaeden = [s for s in schaeden if s]
    if schaeden:
        zeilen.append("- Sichtbare Schäden: " + "; ".join(schaeden))

    hinweise = [str(hw.get("wert") if isinstance(hw, dict) else hw).strip()
                for hw in (felder.get("hinweise") or [])]
    hinweise = [hw for hw in hinweise if hw]
    if hinweise:
        zeilen.append("- Hinweise aus Dokumenten: " + "; ".join(hinweise))

    if not zeilen:
        return ""
    return ("Vom Nutzer bestätigte Erkenntnisse aus Fotos/Dokumenten "
            "(verbindlich, bei Widerspruch zur Textbeschreibung haben diese Vorrang):\n"
            + "\n".join(zeilen))
