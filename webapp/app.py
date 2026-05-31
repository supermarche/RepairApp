"""Reparatur-Helfer — Flask-Backend (Stufe 3).

Routen (SPEC.md + STUFE1.md + STUFE2.md + STUFE3.md §2):
    GET  /                           → rendert templates/index.html
    GET  /api/devices                → alle Seed-Geräte als {id: device}
    GET  /api/device/<id>            → einzelnes device (404 wenn unbekannt)
    POST /api/vorgang                → optional {lang} → 200 {vorgang_id}  (PROJ-37)
    POST /api/chat                   → {vorgang_id, text} → {antwort_text, karten, abgebrochen}  (PROJ-37)
    POST /api/extrahieren            → {vorgangId?, medienIds?, text?, lang?} → {felder, source, …}  (PROJ-31)
    GET  /api/vorgang/<id>           → {id, state, created, updated} | 404
    PUT  /api/vorgang/<id>           → {state} → {id, state, created, updated} | 404
    GET  /api/foerderung             → {items: [...]}
    GET  /api/vorgang/<id>/export.txt → text/plain Protokoll
    GET  /v/<id>                     → Lese-Ansicht HTML (mit Print-Button)

    Stufe 2:
    GET  /api/anbieter               → PROJ-11
    GET  /api/entsorgung             → PROJ-12
    GET  /api/alternativen           → PROJ-13
    GET  /api/ersatzteile            → PROJ-14
    GET  /api/triage/universal       → PROJ-26

    Stufe 3:
    GET  /api/wissensbasis                       → PROJ-15
    GET  /api/wissensbasis/<id>                  → PROJ-15
    POST /api/wissensbasis/entwurf               → PROJ-15
    POST /api/wissensbasis/<id>/freigabe         → PROJ-15
    POST /api/wissensbasis/<id>/zurueckziehen    → PROJ-15
    POST /api/recherche                          → PROJ-16
    GET  /api/rueckruf                           → PROJ-19
    POST /api/bewertung/gesamt                   → PROJ-21
    GET  /api/consent/text                       → PROJ-22
    POST /api/vorgang/<vid>/consent              → PROJ-22
    GET  /api/schwungrad/grobgate                → PROJ-23
    POST /api/schwungrad/beitrag                 → PROJ-23
    POST /api/anonymisieren                      → PROJ-23
    POST /api/vorgang/<vid>/medien               → PROJ-27
    GET  /media/<mid>                            → PROJ-27
    POST /api/transkription                      → PROJ-27
    GET  /api/lotse/route                        → PROJ-18
    POST /api/lotse/route                        → PROJ-18

JSON immer mit ensure_ascii=False, damit Emojis & Umlaute erhalten bleiben.
Start: `python app.py` (debug, :5000) oder `flask --app app run`.
"""

from __future__ import annotations

import json
import logging
import os
import sys

from dotenv import load_dotenv
from flask import Flask, Response, g, got_request_exception, jsonify, render_template, request

from repair import (
    anbieter,
    anonymisierung,
    bewertung,
    config,
    consent,
    datenloeschung,
    entsorgung,
    ersatzteile,
    export,
    foerderung,
    logconf,
    lotse,
    multimodal,
    orchestrator,
    produktsuche,
    protokoll_log,
    recherche,
    schwungrad,
    store,
    triage,
    vision,
    wissensbasis,
)

load_dotenv()

# PROJ-30: Konfiguration ausschließlich aus der Umgebung/.env — beim Start
# einmalig validieren (Fail-fast bei syntaktisch ungültigen Werten, z. B.
# PORT=abc). Fehlende Variablen sind kein Fehler (Default-Pfad).
try:
    config.validate()
except config.ConfigError as exc:
    print(f"[Konfigurationsfehler] {exc}", file=sys.stderr)
    raise SystemExit(2)

# PROJ-29: zentrales Logging einmalig vor App-Start initialisieren (Datei +
# Konsole, tägliche Rotation, 14 Tage). LOG_LEVEL via .env, Default DEBUG.
logconf.setup_logging()
log = logging.getLogger("repair.app")

app = Flask(__name__)
# Emojis/Umlaute nicht escapen
app.config["JSON_AS_ASCII"] = False
app.json.ensure_ascii = False
# Request-Body-Limit (DoS-Schutz): Vorgangs-State ist klein — 1 MB genügt reichlich.
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

# ─── PROJ-28: Anfrage-Protokoll (Betreiber-/Debug-Log) ───────────────────────
# Rein additive Beobachtung: vor dem View den Usage-Slot leeren und die
# Request-Rohdaten erfassen (bevor der View den Body konsumiert), nach dem View
# einen Markdown-Abschnitt schreiben. Best-effort — stört nie die Fachantwort.
# Nur die in protokoll_log.ENDPOINT_ROLLE gewhitelisteten POST-Endpunkte; alle
# GET-/Sicht-Routen erzeugen kein Protokoll.


def _prot_capture_payload() -> dict:
    """Erfasst die gesendeten Daten request-sicher (json/multipart/raw/leer)."""
    body = request.get_json(silent=True)
    if body is not None:
        return {"kind": "json", "json": body}
    if request.files or request.form:
        files = []
        for field, f in request.files.items(multi=True):
            try:
                f.stream.seek(0, os.SEEK_END)
                size = f.stream.tell()
                f.stream.seek(0)
            except Exception:
                size = f.content_length or 0
            files.append({
                "field": field,
                "filename": f.filename,
                "mimetype": f.mimetype,
                "size": size,
            })
        return {"kind": "multipart", "files": files, "form": dict(request.form)}
    raw = request.get_data(cache=True)
    if raw:
        try:
            text = raw.decode("utf-8")
        except Exception:
            text = None
        return {"kind": "raw", "size": len(raw), "text": text}
    return {"kind": "empty"}


def _prot_extract_vid(payload: dict) -> str | None:
    """vid aus Pfad-Param <vid>, Body-Feld vorgangId/vorgang_id/v oder Query ?v= ableiten.

    ``/api/chat`` sendet snake_case ``vorgang_id`` (PROJ-37), die älteren Endpunkte
    camelCase ``vorgangId`` — beide Schreibweisen akzeptieren, sonst landet jeder
    Chat-Turn mangels erkannter vid in ``_ohne-vorgang.md``.
    """
    if request.view_args and request.view_args.get("vid"):
        return request.view_args.get("vid")
    body = payload.get("json") if isinstance(payload, dict) else None
    if isinstance(body, dict):
        v = body.get("vorgangId") or body.get("vorgang_id") or body.get("v")
        if v:
            return str(v)
    return request.args.get("v")


@app.before_request
def _prot_before():
    """Usage-Slot leeren und (nur für protokollierte Endpunkte) Rohdaten erfassen."""
    protokoll_log.reset_usage()
    g._prot = None
    if protokoll_log.soll_protokollieren(request.endpoint):
        try:
            payload = _prot_capture_payload()
            g._prot = {
                "payload": payload,
                "vid": _prot_extract_vid(payload),
                "method": request.method,
                "path": request.path,
                "endpoint": request.endpoint,
            }
        except Exception:
            g._prot = None


@app.after_request
def _prot_after(response):
    """Nach dem View den Protokoll-Abschnitt schreiben (best-effort)."""
    ctx = getattr(g, "_prot", None)
    if ctx:
        try:
            response_json = None
            if response.is_json:
                response_json = json.loads(response.get_data(as_text=True))
            protokoll_log.protokolliere(
                method=ctx["method"],
                path=ctx["path"],
                endpoint=ctx["endpoint"],
                request_payload=ctx["payload"],
                response_json=response_json,
                status=response.status_code,
                vid=ctx["vid"],
                # PROJ-43: vom Chat-Handler hinterlegte Turn-Beobachtbarkeit
                # (tatsächlich geladene Rollen / ausgeführte Tools dieses Turns).
                turn_rollen=ctx.get("turn_rollen"),
                turn_tools=ctx.get("turn_tools"),
            )
        except Exception:
            pass
    return response


# ─── PROJ-29: Zentrales Request-Logging & Exception-Erfassung ────────────────
# Eine zentrale Stelle statt pro-Route dupliziert. Status-Code bestimmt das
# Level: 2xx/3xx → INFO, 4xx → WARNING, 5xx → ERROR. Statische/Sicht-Routen
# bleiben dabei mit erfasst, sind aber am Pfad erkennbar.


@app.after_request
def _access_log_after(response):
    """Loggt jeden Request (Methode, Pfad, Status) auf passendem Level."""
    try:
        status = response.status_code
        if status >= 500:
            level = logging.ERROR
        elif status >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO
        log.log(
            level,
            "%s %s → %s (endpoint=%s)",
            request.method,
            request.path,
            status,
            request.endpoint or "—",
        )
    except Exception:  # noqa: BLE001 — Logging darf die Antwort nie gefährden
        pass
    return response


def _log_unhandled_exception(sender, exception, **extra):
    """Loggt jede unbehandelte Exception mit Stacktrace (verändert nichts am
    Fehlerverhalten der API — rein beobachtend über das Flask-Signal)."""
    try:
        log.exception(
            "Unbehandelte Exception bei %s %s",
            request.method,
            request.path,
            exc_info=exception,
        )
    except Exception:  # noqa: BLE001
        pass


got_request_exception.connect(_log_unhandled_exception, app)


# ─── Bestehende Endpunkte ─────────────────────────────────────────────────────


@app.get("/")
def index():
    """SPA-Shell ausliefern (Template gehört AGENT-B)."""
    return render_template("index.html")


def _json_error(msg: str, code: str, status: int):
    """Einheitliches Fehler-JSON {error, code} mit HTTP-Status (ensure_ascii=False)."""
    return app.response_class(
        json.dumps({"error": msg, "code": code}, ensure_ascii=False),
        status=status,
        mimetype="application/json",
    )


# ─── PROJ-31: Vision-Extraktion (Stufe 1) ─────────────────────────────────────


@app.post("/api/extrahieren")
def api_extrahieren():
    """PROJ-31 Stufe 1 — strukturierte Extraktion aus beigefügten Fotos/Dokumenten.

    Body: {vorgangId?, medienIds?, text?, lang?}
      - medienIds: explizite Medien-IDs; fehlen sie, werden die am Vorgang
        gespeicherten Medien (state.medien) ausgewertet.
    Antwort (immer HTTP 200, scheitert nie hart):
      {felder:{...}, source:"vision|no_vision_backend|vision_error|keine_medien",
       hinweis, bildAnzahl, nichtsErkannt}
    Die bestätigten/korrigierten Felder hält das Frontend im Vorgangs-State.
    """
    payload = request.get_json(silent=True) or {}
    vid = str(payload.get("vorgangId") or "").strip()
    text = str(payload.get("text") or "")
    lang = str(payload.get("lang") or request.args.get("lang") or "de").strip().lower()
    if lang not in ("de", "en"):
        lang = "de"

    medien_ids = payload.get("medienIds")
    medien: list = []
    if isinstance(medien_ids, list) and medien_ids:
        medien = [str(m) for m in medien_ids]
    elif vid:
        vorgang = store.get_vorgang(vid)
        if vorgang:
            state_medien = (vorgang.get("state") or {}).get("medien")
            if isinstance(state_medien, list):
                medien = state_medien

    medien = medien[: config.max_medien_pro_anfrage()]
    result = vision.extrahiere(medien, text=text, lang=lang)
    return jsonify(result)


# ─── PROJ-9 / PROJ-37: Vorgang-Persistenz + Chat-Flow ─────────────────────────


@app.post("/api/vorgang")
def api_vorgang_create():
    """Neuen Vorgang für den Chat-Flow anlegen (PROJ-37, harter Schnitt).

    Body optional: {"lang": "de"|"en"}  (Default "de", in state["lang"] abgelegt)
    Antwort 200: {"vorgang_id": "..."}  (bewusst 200, Abweichung von 201).
    """
    body = request.get_json(silent=True) or {}
    lang = str(body.get("lang") or "de").strip().lower()
    if lang not in ("de", "en"):
        lang = "de"
    v = store.create_vorgang(state={
        "messages": [],
        "karten": [],
        "geladene_rollen": [],
        "entscheidungsprotokoll": [],
        "lang": lang,
    })
    # vorgang_id in den state spiegeln, damit Tools sie kennen
    state = v["state"] if isinstance(v.get("state"), dict) else {}
    state["vorgang_id"] = v["id"]
    store.save_vorgang(v["id"], state)
    return app.response_class(
        json.dumps({"vorgang_id": v["id"]}, ensure_ascii=False),
        mimetype="application/json")


@app.post("/api/chat")
def api_chat():
    """Einen Chat-Turn über den Orchestrator ausführen (PROJ-37).

    Body: {"vorgang_id": "...", "text": "...", "medienIds"?: [...]}
      medienIds (PROJ-31, optional): am Vorgang beigefügte Foto-/Dokument-Medien;
      werden dem Vorgangs-Zustand zugefügt, der Orchestrator wertet sie bei Bedarf
      über das Tool `extrahiere_aus_medien` aus.
    Erfolg 200: {vorgang_id, antwort_text, karten, abgebrochen}
    Fehler: {error, code} — 400 (empty), 404 (no_vorgang), 503 (no_backend),
      502 (ai_error).
    """
    body = request.get_json(silent=True) or {}
    vid = (body.get("vorgang_id") or "").strip()
    text = (body.get("text") or "").strip()
    if not text:
        return _json_error("Bitte beschreibe zuerst, was kaputt ist.", "empty", 400)
    v = store.get_vorgang(vid)
    if v is None:
        return _json_error("Unbekannter Vorgang.", "no_vorgang", 404)
    state = v["state"] if isinstance(v.get("state"), dict) else {}
    state.setdefault("vorgang_id", vid)
    # PROJ-31: neu beigefügte Medien-IDs in den Vorgangs-Zustand übernehmen (dedup,
    # Reihenfolge erhalten) — der Orchestrator nutzt sie via extrahiere_aus_medien.
    neue_medien = body.get("medienIds")
    if isinstance(neue_medien, list) and neue_medien:
        bestehend = state.get("medien") if isinstance(state.get("medien"), list) else []
        zusammen = bestehend + [str(m) for m in neue_medien if str(m) not in bestehend]
        state["medien"] = zusammen
    result = orchestrator.run_turn(state, text)
    store.save_vorgang(vid, state)
    # PROJ-43: turn-lokale Beobachtbarkeit (geladene Rollen / ausgeführte Tools)
    # an den Protokoll-Kontext durchreichen. Diese Zusatz-Keys fließen NICHT in
    # die Client-Antwort (die wird unten explizit nur aus antwort_text/karten/
    # abgebrochen gebaut).
    if getattr(g, "_prot", None):
        g._prot["turn_rollen"] = result.get("_turn_rollen")
        g._prot["turn_tools"] = result.get("_turn_tools")
    if result.get("error"):
        code = result.get("code", "ai_error")
        status = {"no_backend": 503}.get(code, 502)
        return _json_error(result["error"], code, status)
    return app.response_class(
        json.dumps({"vorgang_id": vid,
                    "antwort_text": result["antwort_text"],
                    "karten": result["karten"],
                    "abgebrochen": result["abgebrochen"]},
                   ensure_ascii=False),
        mimetype="application/json")


@app.get("/api/vorgang/<vid>")
def api_vorgang_get(vid: str):
    """Vorgang laden.

    Antwort: {"id", "state", "created", "updated"} oder 404 {"error"}.
    """
    vorgang = store.get_vorgang(vid)
    if vorgang is None:
        return jsonify({"error": "Vorgang nicht gefunden", "id": vid}), 404
    return jsonify(vorgang)


@app.put("/api/vorgang/<vid>")
def api_vorgang_put(vid: str):
    """Vorgang-State überschreiben (last-write-wins).

    Body: {"state": {...}}
    Antwort: {"id", "state", "created", "updated"} oder 404 {"error"}.
    """
    payload = request.get_json(silent=True) or {}
    new_state = payload.get("state")
    if not isinstance(new_state, dict):
        new_state = {}
    vorgang = store.save_vorgang(vid, new_state)
    if vorgang is None:
        return jsonify({"error": "Vorgang nicht gefunden", "id": vid}), 404
    return jsonify(vorgang)


# ─── PROJ-6: Förderung ────────────────────────────────────────────────────────


@app.get("/api/foerderung")
def api_foerderung():
    """Kuratierte Reparatur-Förderungen mit berechnetem status.

    Antwort: {"items": [{bezeichnung, traeger, region, stand, gueltigBis,
                          quelle, beschreibung, status}, ...]}
    """
    items = foerderung.list_foerderungen()
    return jsonify({"items": items})


# ─── Stufe 2: Service-Endpunkte (PROJ-11/12/13/14/26) ────────────────────────
# Alle liefern HTTP 200 mit kuratiertem Seed, scheitern nie hart.
# Query-Parameter sind optional und filtern nur. Leertreffer → fallback:true.


def _q(name: str) -> str | None:
    """Liest einen optionalen Query-Parameter, "" → None."""
    val = (request.args.get(name) or "").strip()
    return val or None


@app.get("/api/anbieter")
def api_anbieter():
    """PROJ-11 — kuratierte Reparatur-Anbieter (Repair-Café/Werkstatt/Profi).

    Query optional: ?kat=&ort=. Leertreffer → fallback:true + ehrlicher Hinweis.
    """
    kat, ort = _q("kat"), _q("ort")
    items = anbieter.list_anbieter(kat=kat, ort=ort)
    fallback = not items
    hinweis = ""
    if fallback:
        hinweis = (
            "Für deinen Filter sind keine Anbieter in unseren Demodaten hinterlegt. "
            "Versuch es ohne Ort-Filter oder suche bundesweite Initiativen auf reparatur-initiativen.de."
        )
    return jsonify({"items": items, "fallback": fallback, "hinweis": hinweis})


@app.get("/api/entsorgung")
def api_entsorgung():
    """PROJ-12 — kuratierte Entsorgungs-/Recyclingwege mit Rohstoff-Hinweis.

    Query optional: ?kat=&ort=. Leertreffer → fallback:true + ehrlicher Hinweis.
    """
    kat, ort = _q("kat"), _q("ort")
    items = entsorgung.list_entsorgung(kat=kat, ort=ort)
    fallback = not items
    hinweis = ""
    if fallback:
        hinweis = (
            "Für deinen Filter sind keine Entsorgungsstellen hinterlegt. Elektrogeräte gehören "
            "nie in den Hausmüll — jeder kommunale Wertstoffhof und größere Händler (ElektroG) "
            "nehmen Altgeräte kostenlos zurück."
        )
    return jsonify({"items": items, "fallback": fallback, "hinweis": hinweis})


@app.get("/api/alternativen")
def api_alternativen():
    """PROJ-13 — Alternativgeräte/Neukauf mit ehrlichem Break-Even.

    Query optional: ?kat=. Leertreffer → fallback:true + ehrlicher Hinweis.
    """
    kat = _q("kat")
    items = produktsuche.list_alternativen(kat=kat)
    fallback = not items
    hinweis = ""
    if fallback:
        hinweis = (
            "Für diese Kategorie haben wir keine Alternativgeräte hinterlegt. "
            "Prüfe zuerst, ob sich eine Reparatur lohnt — das ist meist die nachhaltigere Wahl."
        )
    return jsonify({
        "items": items,
        "breakEven": produktsuche.breakeven_text(kat),
        "hinweis": hinweis,
        "fallback": fallback,
    })


@app.get("/api/ersatzteile")
def api_ersatzteile():
    """PROJ-14 — Ersatzteile, günstigste zuerst; Bestelloption nachgelagert (D8).

    Query optional: ?device=&defekt=. Leertreffer → fallback:true + Hinweis.
    """
    device, defekt = _q("device"), _q("defekt")
    items = ersatzteile.list_ersatzteile(device=device, defekt=defekt)
    fallback = not items
    hinweis = ""
    if fallback:
        hinweis = (
            "Zu diesem Gerät/Defekt sind keine Ersatzteile in unseren Demodaten hinterlegt. "
            "Frag beim Hersteller-Service nach der genauen Modell-/Ersatzteilnummer."
        )
    return jsonify({
        "items": items,
        "guenstigsteZuerst": True,
        "hinweis": hinweis,
        "fallback": fallback,
    })


@app.get("/api/triage/universal")
def api_triage_universal():
    """PROJ-26 — die 5 systematischen, gerätunabhängigen Triage-Fragen."""
    return jsonify({"fragen": triage.universal_fragen()})


# ─── Stufe 3: Wissensbasis (PROJ-15) ─────────────────────────────────────────


@app.get("/api/wissensbasis")
def api_wissensbasis_list():
    """PROJ-15 — Fehlerzustände auflisten.

    Query optional: ?status=geprueft|entwurf|alle (default geprueft) &kat=
    """
    status = (_q("status") or "geprueft").lower()
    kat = _q("kat")
    items = wissensbasis.list_fehlerzustaende(status=status, kat=kat)
    cnt = wissensbasis.counts()
    return jsonify({"items": items, "counts": cnt})


@app.get("/api/wissensbasis/<entry_id>")
def api_wissensbasis_get(entry_id: str):
    """PROJ-15 — einzelner Fehlerzustand oder 404."""
    entry = wissensbasis.get(entry_id)
    if entry is None:
        return jsonify({"error": "Eintrag nicht gefunden", "id": entry_id}), 404
    return jsonify(entry)


@app.post("/api/wissensbasis/entwurf")
def api_wissensbasis_entwurf():
    """PROJ-15 — KI-Entwurf anlegen.

    Body: {kategorie, symptom, lang?}
    → {item, source:"ai|fallback"}
    """
    payload = request.get_json(silent=True) or {}
    kat = str(payload.get("kategorie") or "sonstige").strip()
    symptom = str(payload.get("symptom") or "").strip()
    lang = str(payload.get("lang") or "de").strip().lower()
    if lang not in ("de", "en"):
        lang = "de"
    item = wissensbasis.entwurf_erzeugen(kat=kat, symptom=symptom, lang=lang)
    return jsonify({"item": item, "source": "fallback"})


@app.post("/api/wissensbasis/<entry_id>/freigabe")
def api_wissensbasis_freigabe(entry_id: str):
    """PROJ-15 — Entwurf freigeben.

    Body: {sicherheitBestaetigt:true, sicherheit:"gut|mittel|stop", komplexitaet?}
    → 200 wenn freigegeben, 409 wenn sicherheitBestaetigt fehlt/false.
    """
    payload = request.get_json(silent=True) or {}
    bestaetigt = bool(payload.get("sicherheitBestaetigt", False))
    sicherheit = str(payload.get("sicherheit") or "mittel").strip().lower()
    if sicherheit not in ("gut", "mittel", "stop"):
        sicherheit = "mittel"
    komplexitaet = payload.get("komplexitaet")
    if komplexitaet:
        komplexitaet = str(komplexitaet).strip().lower()
        if komplexitaet not in ("gut", "mittel", "stop"):
            komplexitaet = None

    if not bestaetigt:
        return jsonify({
            "error": "Freigabe erfordert sicherheitBestaetigt:true — menschliche Sicherheits-Bestätigung fehlt.",
            "id": entry_id,
        }), 409

    item = wissensbasis.freigeben(
        entry_id=entry_id,
        sicherheit=sicherheit,
        komplexitaet=komplexitaet,
        sicherheitBestaetigt=True,
    )
    if item is None:
        return jsonify({"error": "Eintrag nicht gefunden oder nicht freigebbar", "id": entry_id}), 404
    return jsonify(item)


@app.post("/api/wissensbasis/<entry_id>/zurueckziehen")
def api_wissensbasis_zurueckziehen(entry_id: str):
    """PROJ-15 — Eintrag auf entwurf-Status zurücksetzen."""
    item = wissensbasis.zurueckziehen(entry_id)
    if item is None:
        return jsonify({"error": "Eintrag nicht gefunden", "id": entry_id}), 404
    return jsonify(item)


# ─── Stufe 3: Recherche (PROJ-16) ────────────────────────────────────────────


@app.post("/api/recherche")
def api_recherche():
    """PROJ-16 — Wissensanfrage: kuratiert → KI-Fallback → Online.

    Body: {frage, kontext?, lang?}
    → {aussage, herkunft, quelle, konfidenz, widerspruch, online, nurDeutsch}
    """
    payload = request.get_json(silent=True) or {}
    frage = str(payload.get("frage") or "").strip()
    kontext = payload.get("kontext")
    lang = str(payload.get("lang") or request.args.get("lang") or "de").strip().lower()
    if lang not in ("de", "en"):
        lang = "de"
    if not frage:
        from repair.i18n import t
        return jsonify({
            "aussage": t("recherche.kein_treffer", lang),
            "herkunft": "ki-fallback",
            "quelle": "kein Suchbegriff",
            "konfidenz": "niedrig",
            "widerspruch": False,
            "online": False,
            "nurDeutsch": True,
        })
    result = recherche.recherche(frage=frage, kontext=kontext, lang=lang)
    return jsonify(result)


# ─── Stufe 3: Rückruf (PROJ-19) ──────────────────────────────────────────────


@app.get("/api/rueckruf")
def api_rueckruf():
    """PROJ-19 — Rückruf/Sicherheitsmangel-Check.

    Query optional: ?modell=&kat=
    → {hit, art, grund, quelle, stand, gueltigBis, vorgehen, modellUnsicher}
    """
    modell = _q("modell")
    kat = _q("kat")
    rueckruf_eintrag = wissensbasis.find_rueckruf(modell=modell, kat=kat)
    if rueckruf_eintrag is None:
        return jsonify({
            "hit": False,
            "art": "",
            "grund": "",
            "quelle": "",
            "stand": "",
            "gueltigBis": "",
            "vorgehen": "",
            "modellUnsicher": False,
        })
    return jsonify({
        "hit": True,
        "art": rueckruf_eintrag.get("art", "rueckruf"),
        "grund": rueckruf_eintrag.get("grund", ""),
        "quelle": rueckruf_eintrag.get("quelle", ""),
        "stand": rueckruf_eintrag.get("stand", ""),
        "gueltigBis": rueckruf_eintrag.get("gueltigBis", ""),
        "vorgehen": rueckruf_eintrag.get("vorgehen", ""),
        "modellUnsicher": bool(rueckruf_eintrag.get("modellUnsicher", False)),
    })


# ─── Stufe 3: Mehrfachdefekte (PROJ-21) ──────────────────────────────────────


@app.post("/api/bewertung/gesamt")
def api_bewertung_gesamt():
    """PROJ-21 — Gesamt-Fazit für Mehrfachdefekte.

    Body: {defekte:[{id, name, lights:[4], recommend}]}
    → {einzel:[...], gesamtFazit:{...}} | gesamtFazit:null wenn <2 Defekte
    """
    payload = request.get_json(silent=True) or {}
    defekte = payload.get("defekte")
    if not isinstance(defekte, list):
        defekte = []
    result = bewertung.gesamt_fazit(defekte)
    if result is None:
        return jsonify({"einzel": defekte, "gesamtFazit": None})
    return jsonify(result)


# ─── Stufe 3: Consent (PROJ-22) ──────────────────────────────────────────────


@app.get("/api/consent/text")
def api_consent_text():
    """PROJ-22 — Consent-Gate-Text in gewählter Sprache.

    Query optional: ?lang=de|en
    """
    lang = str(request.args.get("lang") or "de").strip().lower()
    if lang not in ("de", "en"):
        lang = "de"
    return jsonify(consent.consent_text(lang))


@app.post("/api/vorgang/<vid>/consent")
def api_vorgang_consent(vid: str):
    """PROJ-22 — Consent-Status im Vorgang setzen.

    Body: {status:"erteilt|abgelehnt|widerrufen"}
    Mergt nur consent={status,zeitpunkt} (Server-Zeit) — übrige Felder unberührt.
    Bei Widerruf: bereits erzeugten Schwungrad-Beitrag invalidieren.
    """
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status") or "").strip().lower()

    vorgang = consent.setze_consent(vid, status)
    if vorgang is None:
        return jsonify({"error": "Vorgang nicht gefunden oder ungültiger Status", "id": vid}), 404

    # Widerruf → Schwungrad-Beitrag invalidieren
    if status == "widerrufen":
        state = vorgang.get("state") or {}
        schwungrad_state = state.get("schwungrad") or {}
        beitrag_id = str(schwungrad_state.get("beitragId") or "")
        if beitrag_id:
            wissensbasis.invalidiere_entwurf(beitrag_id)

    return jsonify(vorgang)


# ─── Stufe 3: Schwungrad (PROJ-23) ────────────────────────────────────────────


@app.get("/api/schwungrad/grobgate")
def api_schwungrad_grobgate():
    """PROJ-23 — dokumentiertes Grob-Gate-Ergebnis."""
    return jsonify(schwungrad.grob_gate())


@app.post("/api/schwungrad/beitrag")
def api_schwungrad_beitrag():
    """PROJ-23 — anonymisierten Wissensbasis-Entwurf aus Vorgang erstellen.

    Body: {vorgangId}
    → {beitragId, ausgeschlossen:[...], ohneEinwilligung:bool}
    """
    payload = request.get_json(silent=True) or {}
    vid = str(payload.get("vorgangId") or "").strip()
    if not vid:
        return jsonify({"beitragId": "", "ausgeschlossen": [], "ohneEinwilligung": True})
    vorgang = store.get_vorgang(vid)
    if vorgang is None:
        return jsonify({"beitragId": "", "ausgeschlossen": [], "ohneEinwilligung": True})
    result = schwungrad.build_beitrag(vorgang)
    return jsonify(result)


@app.post("/api/anonymisieren")
def api_anonymisieren():
    """PROJ-23 — Text anonymisieren (Hilfs-Endpunkt).

    Body: {text}
    → {text, entfernt:["e-mail","telefon",…]}
    """
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text") or "")
    clean, entfernt = anonymisierung.anonymisiere_text(text)
    return jsonify({"text": clean, "entfernt": entfernt})


# ─── Stufe 3: Medien (PROJ-27) ────────────────────────────────────────────────


@app.post("/api/vorgang/<vid>/medien")
def api_vorgang_medien(vid: str):
    """PROJ-27 — Medium am Vorgang speichern.

    multipart (file) oder JSON (dataUrl, art).
    → {id, art, ref, hinweis} | {hinweis:"..."} bei Fehler
    """
    vorgang = store.get_vorgang(vid)
    if vorgang is None:
        return jsonify({"error": "Vorgang nicht gefunden", "id": vid}), 404

    art = "foto"
    data = None
    file_mime = ""

    # multipart/form-data
    if request.files:
        f = request.files.get("file")
        if f:
            data = f.read()
            file_mime = (f.content_type or "").lower()
            # Explizite Art aus dem Formular hat Vorrang (PROJ-31: „dokument").
            explicit = str(request.form.get("art") or "").strip().lower()
            if explicit in ("foto", "video", "audio", "dokument"):
                art = explicit
            elif "video" in file_mime:
                art = "video"
            elif "audio" in file_mime:
                art = "audio"
            elif "pdf" in file_mime:
                art = "dokument"
            else:
                art = "foto"
    else:
        payload = request.get_json(silent=True) or {}
        data = payload.get("dataUrl") or payload.get("data")
        art = str(payload.get("art") or "foto").strip().lower()

    result = multimodal.save_medium(data=data, art=art, mime=file_mime)
    if not result.get("id"):
        return jsonify(result)  # hinweis enthalten, 200

    # Vorgang aktualisieren: Medium in state.medien eintragen
    state = vorgang.get("state") or {}
    medien = state.get("medien") if isinstance(state.get("medien"), list) else []
    medien.append({
        "id": result["id"],
        "art": result["art"],
        "ref": result["ref"],
        "hinweis": result.get("hinweis", ""),
        "mime": result.get("mime", ""),
    })
    state["medien"] = medien
    store.save_vorgang(vid, state)

    return jsonify(result)


@app.get("/media/<mid>")
def api_media_get(mid: str):
    """PROJ-27 — gespeichertes Medium abrufen."""
    result = multimodal.get_medium(mid)
    if result is None:
        return jsonify({"error": "Medium nicht gefunden", "id": mid}), 404
    data_bytes, content_type = result
    return Response(data_bytes, content_type=content_type)


@app.post("/api/transkription")
def api_transkription():
    """PROJ-27 — Audio-Transkription (optional).

    Body: Rohdaten-Audio oder multipart.
    → {text, source:"whisper|hinweis", hinweis?}
    """
    audio_bytes = None
    if request.files:
        f = request.files.get("file") or request.files.get("audio")
        if f:
            audio_bytes = f.read()
    elif request.data:
        audio_bytes = request.data

    result = multimodal.transkribiere(audio_bytes)
    return jsonify(result)


# ─── Stufe 3: Lotse (PROJ-18) ────────────────────────────────────────────────


@app.get("/api/lotse/route")
def api_lotse_route_get():
    """PROJ-18 — nächste Rolle + Steueroptionen aus Vorgangsstand.

    Query: ?v=<vid>
    → {naechsteRolle, steueroptionen:[...], handoffGraph, abschnitt}
    Protokolliert keine Daten (read-only Sicht).
    """
    vid = request.args.get("v") or ""
    state: dict = {}
    if vid:
        vorgang = store.get_vorgang(vid)
        if vorgang:
            state = vorgang.get("state") or {}

    lang = str(state.get("lang") or request.args.get("lang") or "de").strip().lower()
    if lang not in ("de", "en"):
        lang = "de"

    naechste = lotse.naechste_rolle(state)
    optionen = lotse.steueroptionen(state, lang=lang)
    abschnitt = lotse.abschnitt_aus_state(state)

    return jsonify({
        "naechsteRolle": naechste,
        "steueroptionen": optionen,
        "handoffGraph": lotse.HANDOFF_GRAPH,
        "abschnitt": abschnitt,
    })


@app.post("/api/lotse/route")
def api_lotse_route_post():
    """PROJ-18 — Routing-/Abbruch-Entscheidung ins decisionLog eintragen.

    Body: {vorgangId, ereignis:"weiter|wechsel|abbruch|rolle-ergebnislos", ziel?}
    → {naechsteRolle, steueroptionen, vorgang}
    """
    payload = request.get_json(silent=True) or {}
    vid = str(payload.get("vorgangId") or "").strip()
    ereignis = str(payload.get("ereignis") or "weiter").strip().lower()
    ziel = payload.get("ziel")
    if ziel:
        ziel = str(ziel).strip()

    vorgang = None
    state: dict = {}
    if vid:
        vorgang = store.get_vorgang(vid)
        if vorgang:
            state = vorgang.get("state") or {}

    # Log-Eintrag in decisionLog
    log_eintrag = lotse.routing_log_eintrag(state, ereignis, ziel)
    decision_log = state.get("decisionLog") if isinstance(state.get("decisionLog"), list) else []
    decision_log.append(log_eintrag)
    state["decisionLog"] = decision_log

    if vid and vorgang:
        vorgang = store.save_vorgang(vid, state)
        state = (vorgang or {}).get("state") or state

    lang = str(state.get("lang") or "de").strip().lower()
    if lang not in ("de", "en"):
        lang = "de"

    naechste = lotse.naechste_rolle(state)
    optionen = lotse.steueroptionen(state, lang=lang)

    return jsonify({
        "naechsteRolle": naechste,
        "steueroptionen": optionen,
        "vorgang": vorgang,
    })


# ─── PROJ-10: Export ─────────────────────────────────────────────────────────


@app.get("/api/vorgang/<vid>/export.txt")
def api_vorgang_export_txt(vid: str):
    """Klartext-Protokoll des Vorgangs (text/plain, UTF-8).

    404 wenn Vorgang unbekannt.
    """
    vorgang = store.get_vorgang(vid)
    if vorgang is None:
        return jsonify({"error": "Vorgang nicht gefunden", "id": vid}), 404

    txt = export.render_txt(vorgang.get("state") or {}, vorgang)
    return Response(txt, content_type="text/plain; charset=utf-8")


@app.get("/v/<vid>")
def vorgang_view(vid: str):
    """Lese-Ansicht eines Vorgangs als standalone HTML.

    Enthält inline Print-CSS + window.print()-Button (→ PDF-Weg).
    Link gültig 30 Tage ab created; danach „nicht mehr verfügbar".
    404-ähnliches Verhalten bei unbekannter id (HTML-Seite mit Hinweis).
    """
    vorgang = store.get_vorgang(vid)
    if vorgang is None:
        # Kein harter 404, sondern freundlicher HTML-Hinweis (Demo läuft immer)
        html = export._expired_html(vid)
        return Response(html, content_type="text/html; charset=utf-8")

    html = export.render_html(vorgang.get("state") or {}, vorgang)
    return Response(html, content_type="text/html; charset=utf-8")


if __name__ == "__main__":
    # PROJ-30: Bind-Adresse, Port und Debug-Flag kommen aus der Umgebung/.env
    # (Defaults 127.0.0.1 / 5000 / an) — kein Hardcode mehr.
    app.run(host=config.host(), port=config.port(), debug=config.flask_debug())
