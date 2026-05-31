"""Anfrage-Protokoll als Markdown — Betreiber-/Debug-Log (PROJ-28).

Schreibt pro KI-/Fach-Anfrage einen Markdown-Abschnitt mit gesendeten Daten,
empfangener Antwort, KI-Entscheidung, Rolle und Token-Statistik. Alle Anfragen
desselben Vorgangs (``vid``) landen chronologisch in **einer** Datei; Anfragen
ohne zuordenbaren Vorgang in der Sammeldatei ``_ohne-vorgang.md``.

Eigenschaften (PROJ-28):
- **Rein additiv/beobachtend** — verändert keine fachliche Logik oder API-Antwort.
- **Best-effort, nicht-blockierend** — schlägt das Schreiben fehl, bleibt die
  HTTP-Antwort unberührt (Fehler wird nur intern auf stderr vermerkt).
- **Abschaltbar** über ``PROTOKOLL_ENABLED`` (default „an"; ``0`` = aus).
- **Rohdaten-Charakter** — die Logs können personenbezogene Daten enthalten.
  Verzeichnis ``webapp/protokolle/`` ist gitignored, wird nie über HTTP
  exponiert, nicht exportiert und fließt nicht ins Schwungrad (PROJ-23).

Token-Quelle: ``repair.ai`` (und ``multimodal``) melden die ``usage`` ihres
echten KI-Calls über :func:`merke_usage`; der Logger liest sie pro Request aus
einem ``contextvars``-Slot. Ohne KI-Call → „kein KI-Call (0 Token)".

Öffentliche API:
    reset_usage()                  → Usage-Slot zu Request-Beginn leeren
    merke_usage(model, usage)      → usage eines KI-Calls registrieren
    soll_protokollieren(endpoint)  → bool (Whitelist)
    rolle_fuer(endpoint)           → str  (Endpunkt→Rolle-Mapping)
    protokolliere(...)             → schreibt einen Abschnitt (best-effort)
"""

from __future__ import annotations

import contextvars
import json
import os
import re
import sys
import threading
from datetime import datetime

# protokolle/ liegt direkt in webapp/ (eine Ebene über repair/) — Layout,
# keine Deployment-Konfiguration (vgl. store.py DB_PATH / multimodal MEDIA_DIR).
PROTOKOLL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "protokolle"))

# Endpunkt (Flask view-Funktionsname) → protokollierte Rolle/Fach-Funktion.
# Nur diese POST-Endpunkte werden protokolliert; alle GET-/Sicht-Routen NICHT.
ENDPOINT_ROLLE: dict[str, str] = {
    "api_extrahieren": "aufnahme",         # POST /api/extrahieren       (PROJ-31)
    "api_recherche": "recherche",          # POST /api/recherche         (PROJ-16)
    "api_wissensbasis_entwurf": "wissensbasis",  # POST /api/wissensbasis/entwurf (PROJ-15)
    "api_bewertung_gesamt": "bewertung",   # POST /api/bewertung/gesamt  (PROJ-21)
    "api_lotse_route_post": "lotse",       # POST /api/lotse/route       (PROJ-18)
    "api_transkription": "transkription",  # POST /api/transkription     (PROJ-27)
    "api_chat": "lotse",                   # POST /api/chat (Orchestrator) (PROJ-35, R4)
}

# Erlaubtes vid-Alphabet = secrets.token_urlsafe (Path-Traversal-Schutz).
_VID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SAMMELDATEI = "_ohne-vorgang.md"
_ENTRIES_MARKER = "<!-- ENTRIES -->"

# Längen-Limits (Rohdaten kürzen, damit Logs nicht explodieren).
_MAX_FELD = 20000

# Pro-Request-Usage-Slot (thread-/kontext-sicher, auch ohne Flask-Kontext nutzbar).
_usage_var: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "protokoll_usage", default=None
)

# Serialisiert die read-modify-write-Zyklen (Aggregat-Kopf neu schreiben).
_lock = threading.Lock()


# ─── Steuerung / Whitelist ────────────────────────────────────────────────────


def _enabled() -> bool:
    """PROTOKOLL_ENABLED auswerten — default „an"; nur 0/false/no = aus."""
    val = (os.environ.get("PROTOKOLL_ENABLED") or "1").strip().lower()
    return val not in ("0", "false", "no", "off", "")


def soll_protokollieren(endpoint: str | None) -> bool:
    """True, wenn der Endpunkt auf der Whitelist steht und Logging an ist."""
    return bool(endpoint) and endpoint in ENDPOINT_ROLLE and _enabled()


def rolle_fuer(endpoint: str | None) -> str:
    return ENDPOINT_ROLLE.get(endpoint or "", "unbekannt")


# ─── Token-Usage ──────────────────────────────────────────────────────────────


def reset_usage() -> None:
    """Usage-Slot leeren (zu Request-Beginn aufrufen)."""
    _usage_var.set(None)


def merke_usage(model: str | None, usage) -> None:
    """Registriert die ``usage`` eines echten KI-Calls für diesen Request.

    ``usage`` ist das OpenAI-Usage-Objekt (Attribute prompt_tokens,
    completion_tokens, total_tokens) oder ein dict. Scheitert nie hart.
    """
    try:
        if usage is None:
            return
        prompt = int(_attr(usage, "prompt_tokens") or 0)
        completion = int(_attr(usage, "completion_tokens") or 0)
        total = int(_attr(usage, "total_tokens") or (prompt + completion))
        _usage_var.set({
            "model": model or "—",
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": total,
        })
    except Exception:  # noqa: BLE001 — Protokoll darf nie die Fachlogik stören
        pass


def _attr(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _konfiguriertes_modell() -> str:
    """Konfiguriertes Diagnose-Modell (für die Fallback-Token-Zeile)."""
    return os.environ.get("OPENAI_MODEL") or "—"


# ─── Schreiben ────────────────────────────────────────────────────────────────


def _safe_vid(vid) -> str | None:
    vid = (str(vid) if vid is not None else "").strip()
    if vid and _VID_RE.match(vid):
        return vid
    return None


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _kuerzen(text: str) -> str:
    if len(text) > _MAX_FELD:
        return text[:_MAX_FELD] + f"\n… [gekürzt, {len(text)} Zeichen gesamt]"
    return text


def _json_block(obj) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except Exception:  # noqa: BLE001
        return str(obj)


def _payload_markdown(payload: dict) -> str:
    """Formatiert die gesendeten Daten (json / multipart / raw / leer)."""
    kind = (payload or {}).get("kind")
    if kind == "json":
        return "```json\n" + _kuerzen(_json_block(payload.get("json"))) + "\n```"
    if kind == "multipart":
        zeilen = ["_multipart/form-data — nur Metadaten protokolliert (keine Rohbytes):_", ""]
        for f in payload.get("files", []):
            zeilen.append(
                f"- Datei `{f.get('field')}`: name=`{f.get('filename')}`, "
                f"mime=`{f.get('mimetype')}`, größe={f.get('size')} Bytes"
            )
        form = payload.get("form") or {}
        if form:
            zeilen.append("")
            zeilen.append("Formularfelder:")
            zeilen.append("```json\n" + _kuerzen(_json_block(form)) + "\n```")
        if len(zeilen) <= 2 and not form:
            zeilen.append("_(keine Dateien)_")
        return "\n".join(zeilen)
    if kind == "raw":
        txt = payload.get("text")
        kopf = f"_nicht-JSON-Body ({payload.get('size')} Bytes)_"
        if txt:
            return kopf + "\n\n```\n" + _kuerzen(txt) + "\n```"
        return kopf
    return "_(leerer Body)_"


def _entscheidung_markdown(response_json, request_payload: dict) -> str:
    """Liest die KI-Entscheidung lesbar aus der Antwort (best-effort)."""
    zeilen: list[str] = []
    r = response_json if isinstance(response_json, dict) else {}
    device = r.get("device") if isinstance(r.get("device"), dict) else {}

    source = r.get("source") or device.get("source")
    if source:
        zeilen.append(f"- **source:** `{source}`")

    recommend = r.get("recommend") or device.get("recommend")
    if recommend:
        zeilen.append(f"- **empfohlener Pfad (recommend):** `{recommend}`")

    accent = r.get("accentPath") or device.get("accentPath")
    if accent:
        zeilen.append(f"- **accentPath:** `{accent}`")

    # Ampel-Stufen (lights) — als kompakte Liste key:level
    lights = device.get("lights") or r.get("lights")
    if isinstance(lights, list) and lights:
        teile = []
        for li in lights:
            if isinstance(li, dict):
                teile.append(f"{li.get('key')}={li.get('level')}")
        if teile:
            zeilen.append("- **Ampel (lights):** " + ", ".join(teile))

    # Recherche-Herkunft/Konfidenz (PROJ-16)
    if r.get("herkunft"):
        zeilen.append(f"- **Herkunft (Recherche):** `{r.get('herkunft')}`")
    if r.get("konfidenz"):
        zeilen.append(f"- **Konfidenz:** `{r.get('konfidenz')}`")
    if r.get("quelle"):
        zeilen.append(f"- **Quelle:** {r.get('quelle')}")

    # Gesamt-Fazit (PROJ-21)
    gesamt = r.get("gesamtFazit")
    if isinstance(gesamt, dict) and gesamt:
        zeilen.append(f"- **Gesamt-Fazit (Mehrfachdefekt):** `{gesamt.get('ampel') or gesamt.get('empfehlung') or '—'}`")

    # Lotse-Routing (PROJ-18) — Ereignis aus Request, Zielrolle aus Antwort
    req = (request_payload or {}).get("json") if isinstance(request_payload, dict) else None
    if isinstance(req, dict) and req.get("ereignis"):
        ziel = req.get("ziel")
        zeilen.append(
            f"- **Lotse-Ereignis:** `{req.get('ereignis')}`"
            + (f" → `{ziel}`" if ziel else "")
        )
    if r.get("naechsteRolle"):
        zeilen.append(f"- **nächste Rolle:** `{r.get('naechsteRolle')}`")

    if not zeilen:
        return "_(keine klassifizierbare KI-Entscheidung)_"
    return "\n".join(zeilen)


def _token_markdown(response_json) -> tuple[str, int, str]:
    """Liefert (markdown, total_tokens, klassifikation `ai`|`fallback`)."""
    usage = _usage_var.get()
    r = response_json if isinstance(response_json, dict) else {}
    source = str(r.get("source") or "").lower()
    whisper = source == "whisper"  # Transkription-KI-Call (ohne Token-Statistik)

    if usage:
        total = int(usage.get("total_tokens") or 0)
        md = "\n".join([
            "- **Klassifikation:** ai",
            f"- **Modell:** `{usage.get('model')}`",
            f"- **Token gesamt:** {total}",
            f"- prompt_tokens: {usage.get('prompt_tokens')} · "
            f"completion_tokens: {usage.get('completion_tokens')} · "
            f"total_tokens: {total}",
        ])
        return md, total, "ai"

    if whisper:
        from . import config  # PROJ-30: konfiguriertes Whisper-Modell statt Literal
        md = "\n".join([
            "- **Klassifikation:** ai",
            f"- **Modell:** `{config.whisper_model()}`",
            "- **Token gesamt:** 0 _(KI-Call Whisper — keine Token-Statistik)_",
        ])
        return md, 0, "ai"

    md = "\n".join([
        "- **Klassifikation:** fallback",
        f"- **Modell:** `{_konfiguriertes_modell()}`",
        "- **Token gesamt:** 0 _(kein KI-Call)_",
    ])
    return md, 0, "fallback"


def _orchestrierung_markdown(turn_rollen, turn_tools) -> str:
    """PROJ-43: Ehrliche Rollen-/Tool-Ausweisung je Turn (Reihenfolge erhalten).

    ``turn_rollen``/``turn_tools`` sind die in DIESEM Turn tatsächlich geladenen
    Rollen bzw. ausgeführten Tools (aus ``orchestrator.run_turn``). Sind beide
    leer/None, kam keine Beobachtbarkeitsspur an — dann nichts ausweisen (der
    Aufrufer rendert den Abschnitt für solche Endpunkte gar nicht erst)."""
    rollen = [str(r) for r in (turn_rollen or []) if r]
    zeilen: list[str] = []
    if rollen:
        zeilen.append("- **Geladene Rollen:** " + " → ".join(f"`{r}`" for r in rollen))
    else:
        zeilen.append("- **Geladene Rollen:** _keine Rolle geladen (nur Lotse-Kontext)_")

    tools = turn_tools or []
    if tools:
        teile = []
        for t in tools:
            name = t.get("tool") if isinstance(t, dict) else str(t)
            ok = t.get("ok", True) if isinstance(t, dict) else True
            teile.append(f"`{name}`" + ("" if ok else " ⚠ fehlgeschlagen"))
        zeilen.append("- **Tool-Aufrufe:** " + ", ".join(teile))
    else:
        zeilen.append("- **Tool-Aufrufe:** _keine_")
    return "\n".join(zeilen)


def _entry_markdown(
    idx: int,
    *,
    method: str,
    path: str,
    ts: str,
    vid: str | None,
    rolle: str,
    request_payload: dict,
    response_json,
    status: int,
    turn_rollen=None,
    turn_tools=None,
    orchestrierung: bool = False,
) -> str:
    token_md, _total, _kl = _token_markdown(response_json)
    resp_block = "```json\n" + _kuerzen(_json_block(response_json)) + "\n```"
    # PROJ-43: Für den Orchestrator-Endpunkt (/api/chat) statt der vom Endpunkt
    # abgeleiteten Pauschal-Rolle die tatsächlichen Turn-Rollen ausweisen.
    if orchestrierung:
        rollen = [str(r) for r in (turn_rollen or []) if r]
        kopf_rolle = (" → ".join(rollen) if rollen else "nur Lotse-Kontext")
    else:
        kopf_rolle = rolle
    zeilen = [
        f"## {idx} · {ts} · Rolle `{kopf_rolle}`",
        "",
        "**Gesendet**",
        "",
        f"- **Methode/Pfad:** `{method} {path}`",
        f"- **Zeitstempel:** {ts}",
        f"- **Vorgang:** `{vid or '—'}`",
        "",
        "Request-Payload:",
        "",
        _payload_markdown(request_payload),
        "",
        "**Empfangen**",
        "",
        f"- **HTTP-Status:** {status}",
        "",
        "Response:",
        "",
        resp_block,
        "",
    ]
    if orchestrierung:
        zeilen += [
            "**Orchestrierung (Rollen & Tools)**",
            "",
            _orchestrierung_markdown(turn_rollen, turn_tools),
            "",
        ]
    zeilen += [
        "**KI-Entscheidung**",
        "",
        _entscheidung_markdown(response_json, request_payload),
        "",
        "**Token-Statistik**",
        "",
        token_md,
        "",
        "---",
        "",
    ]
    return "\n".join(zeilen)


def _header(vid: str | None, anzahl: int, total: int, ai_cnt: int, fb_cnt: int, ts: str) -> str:
    titel = f"Vorgang `{vid}`" if vid else "ohne zuordenbaren Vorgang"
    return "\n".join([
        f"# Anfrage-Protokoll — {titel}",
        "",
        "> Betreiber-/Debug-Log (PROJ-28). **Rohdaten** — nicht weitergeben, nicht",
        "> exportieren, gitignored. Kein Endnutzer-Dokument.",
        "",
        f"**Anfragen:** {anzahl} · **Total-Token:** {total} · "
        f"**KI-Calls (`ai`):** {ai_cnt} · **ohne KI (`fallback`):** {fb_cnt} · "
        f"**Aktualisiert:** {ts}",
        "",
        _ENTRIES_MARKER,
        "",
    ])


def _aggregat(entries_text: str) -> tuple[int, int, int, int]:
    """Zählt (anzahl, total_token, ai, fallback) aus dem bestehenden Entries-Block."""
    anzahl = len(re.findall(r"(?m)^## \d+ ·", entries_text))
    total = sum(int(n) for n in re.findall(r"(?m)^- \*\*Token gesamt:\*\* (\d+)", entries_text))
    ai_cnt = len(re.findall(r"(?m)^- \*\*Klassifikation:\*\* ai\b", entries_text))
    fb_cnt = len(re.findall(r"(?m)^- \*\*Klassifikation:\*\* fallback\b", entries_text))
    return anzahl, total, ai_cnt, fb_cnt


def protokolliere(
    *,
    method: str,
    path: str,
    endpoint: str | None,
    request_payload: dict,
    response_json,
    status: int,
    vid,
    turn_rollen=None,
    turn_tools=None,
) -> None:
    """Schreibt einen Protokoll-Abschnitt (best-effort, nicht-blockierend).

    Jeder Fehler wird verschluckt (nur stderr-Hinweis) — die HTTP-Antwort des
    Endpunkts bleibt davon unberührt (PROJ-28 Akzeptanzkriterium).

    ``turn_rollen``/``turn_tools`` (PROJ-43): die im Orchestrator-Turn tatsächlich
    geladenen Rollen bzw. ausgeführten Tools (nur für /api/chat). Sind sie gesetzt,
    weist der Eintrag sie ehrlich aus — statt der vom Endpunkt abgeleiteten
    Pauschal-Rolle „lotse". Für andere Endpunkte bleibt ``rolle_fuer`` der Fallback.
    """
    try:
        if not _enabled():
            return
        rolle = rolle_fuer(endpoint)
        # Orchestrierungs-Endpunkt (/api/chat): tatsächliche Turn-Rollen/Tools
        # ausweisen statt der irreführenden Endpunkt→Rolle-Pauschale (PROJ-43).
        orchestrierung = endpoint == "api_chat"
        safe = _safe_vid(vid)
        dateiname = f"{safe}.md" if safe else _SAMMELDATEI
        ts = _now_iso()

        with _lock:
            os.makedirs(PROTOKOLL_DIR, exist_ok=True)
            pfad = os.path.join(PROTOKOLL_DIR, dateiname)

            entries_text = ""
            if os.path.exists(pfad):
                with open(pfad, "r", encoding="utf-8") as fh:
                    bestehend = fh.read()
                if _ENTRIES_MARKER in bestehend:
                    entries_text = bestehend.split(_ENTRIES_MARKER, 1)[1].lstrip("\n")

            alt_anzahl, alt_total, alt_ai, alt_fb = _aggregat(entries_text)
            idx = alt_anzahl + 1

            neuer_eintrag = _entry_markdown(
                idx,
                method=method,
                path=path,
                ts=ts,
                vid=safe,
                rolle=rolle,
                request_payload=request_payload,
                response_json=response_json,
                status=status,
                turn_rollen=turn_rollen,
                turn_tools=turn_tools,
                orchestrierung=orchestrierung,
            )
            neue_entries = (entries_text + neuer_eintrag) if entries_text else neuer_eintrag

            neu_anzahl, neu_total, neu_ai, neu_fb = _aggregat(neue_entries)
            kopf = _header(safe, neu_anzahl, neu_total, neu_ai, neu_fb, ts)

            tmp = pfad + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(kopf + neue_entries)
            os.replace(tmp, pfad)  # atomar
    except Exception as exc:  # noqa: BLE001 — niemals die Fachantwort gefährden
        print(f"[protokoll_log] Schreiben fehlgeschlagen: {exc}", file=sys.stderr)
