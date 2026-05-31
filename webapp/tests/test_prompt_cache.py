"""Guard-Test: Byte-Stabilität von system_prefix() und tools.specs() (PROJ-48).

Pinnt die SHA-256-Hashes der JSON-Repräsentation von system_prefix("de"),
system_prefix("en") und tools.specs() gegen gepinnte Erwartungswerte.

BEWUSSTE ÄNDERUNG ERLAUBT: Wer system_prefix() oder tools.specs() absichtlich
ändert (neues Feature, Rollenbeschreibung, Werkzeug-Anpassung), muss die drei
PIN-Konstanten in DIESEM Test im gleichen Commit aktualisieren. Der Test
verhindert nur UNBEABSICHTIGTEN Drift, der die Cache-Trefferquote zerstören
würde — er sperrt keine intentionalen Änderungen.

Lauffähig ohne pytest:
    python tests/test_prompt_cache.py   (standalone, __main__-Runner)
    python -m pytest tests/test_prompt_cache.py -q
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

_WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WEBAPP not in sys.path:
    sys.path.insert(0, _WEBAPP)

from repair import orchestrator, tools, kontext

# ─── Gepinnte SHA-256-Hashes (bei bewusster Änderung im gleichen Commit anpassen) ──
# Berechnet via: hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
_PIN_SYSTEM_PREFIX_DE = "6489bbfa468edd991829e32b1f10224688117f8fd0f619eeba5e807c1d19e96b"
_PIN_SYSTEM_PREFIX_EN = "5d7e619b476c8a83a8480ef38f77be47b2abb38947e29fea1d763001ef1692e3"
_PIN_TOOLS_SPECS      = "ed4e83ccac54d7c6caeb8af0e6da99a27d64b94549f3a63b382249b235207669"


def _hash(obj) -> str:
    """SHA-256 über deterministisches JSON (ensure_ascii=False, sort_keys=True)."""
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


# ─── Stabilitäts-Pins ─────────────────────────────────────────────────────────

def test_system_prefix_de_stabil() -> None:
    """system_prefix('de') darf sich nicht unbeabsichtigt ändern.

    BEWUSSTE ÄNDERUNG: _PIN_SYSTEM_PREFIX_DE im gleichen Commit aktualisieren.
    """
    aktuell = _hash(orchestrator.system_prefix("de"))
    assert aktuell == _PIN_SYSTEM_PREFIX_DE, (
        f"system_prefix('de') hat sich geändert — wenn beabsichtigt, "
        f"_PIN_SYSTEM_PREFIX_DE im selben Commit aktualisieren.\n"
        f"  erwartet: {_PIN_SYSTEM_PREFIX_DE}\n"
        f"  aktuell:  {aktuell}"
    )


def test_system_prefix_en_stabil() -> None:
    """system_prefix('en') darf sich nicht unbeabsichtigt ändern.

    BEWUSSTE ÄNDERUNG: _PIN_SYSTEM_PREFIX_EN im gleichen Commit aktualisieren.
    """
    aktuell = _hash(orchestrator.system_prefix("en"))
    assert aktuell == _PIN_SYSTEM_PREFIX_EN, (
        f"system_prefix('en') hat sich geändert — wenn beabsichtigt, "
        f"_PIN_SYSTEM_PREFIX_EN im selben Commit aktualisieren.\n"
        f"  erwartet: {_PIN_SYSTEM_PREFIX_EN}\n"
        f"  aktuell:  {aktuell}"
    )


def test_tools_specs_stabil() -> None:
    """tools.specs() darf sich nicht unbeabsichtigt ändern.

    BEWUSSTE ÄNDERUNG: _PIN_TOOLS_SPECS im gleichen Commit aktualisieren.
    """
    aktuell = _hash(tools.specs())
    assert aktuell == _PIN_TOOLS_SPECS, (
        f"tools.specs() hat sich geändert — wenn beabsichtigt, "
        f"_PIN_TOOLS_SPECS im selben Commit aktualisieren.\n"
        f"  erwartet: {_PIN_TOOLS_SPECS}\n"
        f"  aktuell:  {aktuell}"
    )


# ─── Präfix-Voranstellung durch sende_sicht ───────────────────────────────────

def test_sende_sicht_stellt_prefix_ungeaendert_voran() -> None:
    """sende_sicht() stellt system_prefix unverändert als Listen-Präfix voran.

    Prüft für de und en:
    - Keine Mutation: prefix-Objekt vor/nach dem Aufruf identisch.
    - Echtes Listen-Präfix: die ersten N Elemente der zurückgegebenen Liste
      sind byte-identisch mit dem prefix.
    - Keine Umordnung: Reihenfolge der prefix-Nachrichten bleibt erhalten.
    """
    for lang in ("de", "en"):
        prefix = orchestrator.system_prefix(lang)
        prefix_kopie = [dict(m) for m in prefix]  # Snapshot vor dem Aufruf
        state: dict = {"messages": [], "karten": [], "lang": lang}

        result = kontext.sende_sicht(prefix, state)

        # prefix selbst nicht mutiert
        assert prefix == prefix_kopie, (
            f"sende_sicht() hat das prefix-Objekt für lang={lang!r} mutiert"
        )

        n = len(prefix)
        assert len(result) >= n, (
            f"Ergebnis-Liste kürzer als prefix für lang={lang!r}: "
            f"erwartet >= {n}, erhalten {len(result)}"
        )

        for i in range(n):
            assert result[i] == prefix[i], (
                f"Präfix-Position {i} stimmt nicht überein (lang={lang!r}):\n"
                f"  erwartet: {prefix[i]}\n"
                f"  erhalten: {result[i]}"
            )


def test_sende_sicht_mit_nachrichten_prefix_voran() -> None:
    """sende_sicht() stellt Präfix auch bei bestehendem Verlauf voran."""
    prefix = orchestrator.system_prefix("de")
    state = {
        "messages": [
            {"role": "user", "content": "Toaster kaputt"},
            {"role": "assistant", "content": "Ich helfe gerne."},
        ],
        "karten": [],
        "lang": "de",
    }
    result = kontext.sende_sicht(prefix, state)
    n = len(prefix)
    assert result[:n] == prefix, (
        "Präfix steht nicht an erster Stelle, wenn Verlauf vorhanden ist"
    )


# ─── Determinismus ────────────────────────────────────────────────────────────

def test_system_prefix_deterministisch() -> None:
    """system_prefix() liefert bei mehreren Aufrufen byte-identische Listen."""
    for lang in ("de", "en"):
        a = orchestrator.system_prefix(lang)
        b = orchestrator.system_prefix(lang)
        assert a == b, f"system_prefix({lang!r}) ist nicht deterministisch"


def test_tools_specs_deterministisch() -> None:
    """tools.specs() liefert bei mehreren Aufrufen byte-identische Listen."""
    a = tools.specs()
    b = tools.specs()
    assert a == b, "tools.specs() ist nicht deterministisch"


# ─── Standalone-Runner ────────────────────────────────────────────────────────

def _run_standalone() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as exc:
            fails += 1
            print(f"  FAIL {t.__name__}\n       {exc}")
    print(f"\n{len(tests) - fails}/{len(tests)} Checks bestanden.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
