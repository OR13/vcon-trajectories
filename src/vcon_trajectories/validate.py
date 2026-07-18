"""Validate vCon objects against the IETF vCon JSON Schema (draft core-03, App. B).

Primary validation is JSON-Schema based (the authoritative artifact). A secondary
cross-check against the ``python-vcon`` reference implementation is available but
note that python-vcon only speaks vCon 0.0.2, while this project targets 0.4.0,
so it is used only to show the reference tool round-trips a downgraded copy.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from jsonschema import Draft7Validator, FormatChecker

_DEFAULT_SCHEMA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "schema",
    "vcon_json_schema.json",
)


def load_schema(path: str = _DEFAULT_SCHEMA) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_validator(schema: Optional[Dict[str, Any]] = None) -> Draft7Validator:
    if schema is None:
        schema = load_schema()
    return Draft7Validator(schema, format_checker=FormatChecker())


def validate_vcon(
    vcon: Dict[str, Any], validator: Optional[Draft7Validator] = None
) -> List[str]:
    """Return a list of human-readable schema errors (empty == valid)."""
    if validator is None:
        validator = make_validator()
    errors = []
    for e in sorted(validator.iter_errors(vcon), key=lambda x: list(x.path)):
        loc = "/".join(str(p) for p in e.path) or "<root>"
        errors.append(f"{loc}: {e.message}")
    return errors


def _quiet_pyvcon() -> None:
    """python-vcon emits INFO logs on import; keep our CLI output readable."""
    import logging

    for name in ("vcon", "root"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    logging.disable(logging.ERROR)


def pyvcon_available() -> bool:
    try:
        _quiet_pyvcon()
        import vcon  # noqa: F401
        return True
    except Exception:
        return False


def pyvcon_roundtrip(vcon_obj: Dict[str, Any]) -> str:
    """Cross-check with the python-vcon reference implementation.

    python-vcon only accepts vCon versions 0.0.1/0.0.2. We downgrade a *copy*'s
    version tag purely so the reference loader will parse it, demonstrating the
    reference tool round-trips the structure. Returns a status string.
    """
    try:
        import vcon as pyvcon
    except Exception as exc:  # pragma: no cover
        return f"skipped (python-vcon not importable: {exc})"

    downgraded = dict(vcon_obj)
    downgraded["vcon"] = "0.0.2"
    try:
        v = pyvcon.Vcon()
        v.loads(json.dumps(downgraded))
        parties = len(v.parties)
        dialogs = len(v.dialog)
        return f"ok (python-vcon parsed downgraded 0.0.2 copy: {parties} parties, {dialogs} dialogs)"
    except Exception as exc:
        return f"rejected by python-vcon: {exc}"
