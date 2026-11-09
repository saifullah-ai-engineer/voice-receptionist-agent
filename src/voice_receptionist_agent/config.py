"""Business configuration.

An agency configures this agent for a client business by editing one
JSON file, not by editing code. Copy business.example.json to
business.json, fill in the client facts, and run the demo or the CLI
with --config business.json. If no config file is given, the built-in
example profile (a dental clinic) is used so the demo works out of the
box.

Every value is validated. A missing file, bad JSON, a missing field, a
wrong type, or an unknown key fails with a clear error naming the
problem, so a typo in the config never silently changes behaviour.
"""

import json
from pathlib import Path
from typing import Any, Dict

from .models import BusinessProfile

_FIELDS = {
    "name": str,
    "services": list,
    "hours": str,
    "price_note": str,
    "handoff_message": str,
    "phone": str,
}

_REQUIRED = tuple(_FIELDS)


def load_business_profile(path: str | Path) -> BusinessProfile:
    """Load and validate a business config file, return a BusinessProfile."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(
            f"Business config not found: {target}. "
            "Copy business.example.json to business.json and fill it in, "
            "or pass --config with the path to your config file."
        )
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Business config {target} is not valid JSON: {exc}. "
            "Check for a missing comma or quote."
        ) from exc
    return business_profile_from_dict(data, source=str(target))


def business_profile_from_dict(data: Dict[str, Any], source: str = "config") -> BusinessProfile:
    """Validate a parsed config dict and build a BusinessProfile from it."""
    if not isinstance(data, dict):
        raise ValueError(
            f"Business config {source} must be a JSON object with the fields "
            f"{', '.join(_REQUIRED)}, but it is a {type(data).__name__}."
        )
    unknown = sorted(set(data) - set(_FIELDS))
    if unknown:
        raise ValueError(
            f"Business config {source} has unknown field(s): {', '.join(unknown)}. "
            f"Allowed fields are: {', '.join(_REQUIRED)}. "
            "Check for a typo in the field name."
        )
    missing = [field for field in _REQUIRED if field not in data]
    if missing:
        raise ValueError(
            f"Business config {source} is missing required field(s): "
            f"{', '.join(missing)}."
        )
    for field, kind in _FIELDS.items():
        value = data[field]
        if not isinstance(value, kind):
            raise ValueError(
                f"Business config {source}: field '{field}' must be a "
                f"{kind.__name__}, but it is a {type(value).__name__}."
            )
        if kind is str and not value.strip():
            raise ValueError(
                f"Business config {source}: field '{field}' must not be empty."
            )
    services = data["services"]
    if not services:
        raise ValueError(
            f"Business config {source}: field 'services' must list at least "
            "one service the business offers."
        )
    cleaned = []
    for service in services:
        if not isinstance(service, str) or not service.strip():
            raise ValueError(
                f"Business config {source}: every service must be a "
                "non-empty string."
            )
        cleaned.append(service.strip())
    lowered = [service.lower() for service in cleaned]
    if len(set(lowered)) != len(lowered):
        raise ValueError(
            f"Business config {source}: field 'services' lists the same "
            "service more than once."
        )
    return BusinessProfile(
        name=data["name"].strip(),
        services=cleaned,
        hours=data["hours"].strip(),
        price_note=data["price_note"].strip(),
        handoff_message=data["handoff_message"].strip(),
        phone=data["phone"].strip(),
    )


def resolve_business_profile(explicit: str | Path | None = None) -> BusinessProfile:
    """Pick the business profile for a run.

    An explicit --config path wins. Otherwise a business.json in the
    current directory is used. Otherwise the built-in example profile
    is used so the demo works with no setup.
    """
    if explicit:
        return load_business_profile(explicit)
    local = Path("business.json")
    if local.is_file():
        return load_business_profile(local)
    return BusinessProfile()
