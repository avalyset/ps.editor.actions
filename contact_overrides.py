"""Contact person for the product specification itself.

The contact shown under "Om spesifikasjonen" is the person responsible for the
*specification*, which is not necessarily the dataset contact registered in
Geonorge. The web app lets the user enter one manually; it is committed as a
separate overrides file next to psdata (``contact.overrides.json``) because
psdata is regenerated from Geonorge on every run.

Overrides file shape (v1)::

    {
      "version": 1,
      "contact": {
        "individualName": "Ola Nordmann",
        "organizationName": "Kartverket",
        "electronicMailAddress": "ola.nordmann@kartverket.no",
        "phone": "+47 32 11 80 00"
      }
    }

When the file is missing or has no non-blank fields, the first contact from the
Geonorge metadata (``identificationSection.contact[0]``) is used.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

__all__ = [
    "CONTACT_OVERRIDES_FILENAME",
    "load_contact_override",
    "resolve_specification_contact",
    "format_contact",
]

CONTACT_OVERRIDES_FILENAME = "contact.overrides.json"

_FIELDS = ("individualName", "organizationName", "electronicMailAddress", "phone")


def _clean(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def load_contact_override(path: str | Path) -> dict[str, str]:
    """Read the contact from an overrides file.

    Returns ``{}`` when the file is missing, unreadable or has no usable fields --
    a bad overrides file must never fail the generation.
    """
    file = Path(path)
    if not file.exists():
        return {}
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    contact = data.get("contact") if isinstance(data, Mapping) else None
    if not isinstance(contact, Mapping):
        return {}
    return {key: text for key in _FIELDS if (text := _clean(contact.get(key)))}


def resolve_specification_contact(
    psdata: Mapping[str, Any], override: Mapping[str, Any] | None
) -> dict[str, str]:
    """The manual contact when given, otherwise the first Geonorge contact."""
    if override:
        return dict(override)
    identification = psdata.get("identificationSection")
    contacts = identification.get("contact") if isinstance(identification, Mapping) else None
    first = contacts[0] if isinstance(contacts, list) and contacts else None
    if not isinstance(first, Mapping):
        return {}
    # Fallback keeps the previous output: organization and e-mail only.
    return {
        key: text
        for key in ("organizationName", "electronicMailAddress")
        if (text := _clean(first.get(key)))
    }


def format_contact(contact: Mapping[str, Any]) -> str:
    """One Markdown line: ``Navn, Organisasjon, [e-post](mailto:e-post), tlf. 123``."""
    parts = [
        text
        for key in ("individualName", "organizationName")
        if (text := _clean(contact.get(key)))
    ]
    email = _clean(contact.get("electronicMailAddress"))
    if email:
        parts.append(f"[{email}](mailto:{email})")
    phone = _clean(contact.get("phone"))
    if phone:
        parts.append(f"tlf. {phone}")
    return ", ".join(parts)
