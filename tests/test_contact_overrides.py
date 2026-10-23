"""Tests for the manually entered specification contact."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from contact_overrides import (  # noqa: E402
    format_contact,
    load_contact_override,
    resolve_specification_contact,
)
from scripts.assemble_product_spec import _write_specification_contact  # noqa: E402

PSDATA = {
    "identificationSection": {
        "contact": [
            {
                "organizationName": "Kartverket",
                "electronicMailAddress": "post@kartverket.no",
                "individualName": "Metadata-kontakt",
                "role": "owner",
            }
        ]
    }
}


class ContactOverridesTest(unittest.TestCase):
    def test_missing_file_gives_empty_override(self) -> None:
        self.assertEqual(load_contact_override(Path("does-not-exist.json")), {})

    def test_invalid_json_gives_empty_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contact.overrides.json"
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(load_contact_override(path), {})

    def test_blank_fields_are_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contact.overrides.json"
            path.write_text(
                json.dumps({"version": 1, "contact": {"individualName": " Ola ", "phone": "  "}}),
                encoding="utf-8",
            )
            self.assertEqual(load_contact_override(path), {"individualName": "Ola"})

    def test_override_wins_over_metadata(self) -> None:
        override = {"individualName": "Ola Nordmann", "electronicMailAddress": "ola@example.no"}
        self.assertEqual(resolve_specification_contact(PSDATA, override), override)

    def test_falls_back_to_first_metadata_contact(self) -> None:
        self.assertEqual(
            resolve_specification_contact(PSDATA, {}),
            {"organizationName": "Kartverket", "electronicMailAddress": "post@kartverket.no"},
        )

    def test_format_contact(self) -> None:
        self.assertEqual(
            format_contact(
                {
                    "individualName": "Ola Nordmann",
                    "organizationName": "Kartverket",
                    "electronicMailAddress": "ola@example.no",
                    "phone": "123 45 678",
                }
            ),
            "Ola Nordmann, Kartverket, [ola@example.no](mailto:ola@example.no), tlf. 123 45 678",
        )
        self.assertEqual(format_contact({}), "")

    def test_assemble_writes_specification_contact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp)
            psdata_path = spec_dir / "psdata_test.json"
            psdata_path.write_text(json.dumps(PSDATA), encoding="utf-8")

            _write_specification_contact(psdata_path)
            fallback = json.loads(psdata_path.read_text(encoding="utf-8"))
            self.assertEqual(
                fallback["specificationContact"],
                "Kartverket, [post@kartverket.no](mailto:post@kartverket.no)",
            )

            (spec_dir / "contact.overrides.json").write_text(
                json.dumps({"version": 1, "contact": {"individualName": "Kari Nordmann"}}),
                encoding="utf-8",
            )
            _write_specification_contact(psdata_path)
            overridden = json.loads(psdata_path.read_text(encoding="utf-8"))
            self.assertEqual(overridden["specificationContact"], "Kari Nordmann")


if __name__ == "__main__":
    unittest.main()
