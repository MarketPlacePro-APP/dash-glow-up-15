#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.tlwb_semantic_fingerprint import fingerprint


class SemanticFingerprintTests(unittest.TestCase):
    def fixture(self) -> Path:
        temp = Path(tempfile.mkdtemp())
        (temp / "src").mkdir()
        (temp / "api").mkdir()
        (temp / "data").mkdir()
        (temp / "package.json").write_text('{"name":"test"}\n')
        (temp / "vercel.json").write_text('{"rewrites":[]}\n')
        (temp / "middleware.ts").write_text('export default 1;\n')
        (temp / "index.html").write_text('<html></html>\n')
        (temp / "src" / "data.ts").write_text('export const sourceUpdatedAt = "2026-08-14T10:00:00-06:00";\nexport const value = 42;\n')
        (temp / "data" / "source_health.json").write_text(json.dumps({"generated_at": "2026-08-14T10:00:00-06:00", "rows": [{"status": "green", "value": 42}]}) + "\n")
        return temp

    def test_volatile_check_timestamps_do_not_change_fingerprint(self):
        root = self.fixture()
        before, _ = fingerprint(root)
        (root / "src" / "data.ts").write_text('export const sourceUpdatedAt = "2026-08-14T11:00:00-06:00";\nexport const value = 42;\n')
        (root / "data" / "source_health.json").write_text(json.dumps({"generated_at": "2026-08-14T11:00:00-06:00", "rows": [{"status": "green", "value": 42}]}) + "\n")
        after, _ = fingerprint(root)
        self.assertEqual(before, after)

    def test_material_data_and_code_changes_change_fingerprint(self):
        root = self.fixture()
        before, _ = fingerprint(root)
        (root / "src" / "data.ts").write_text('export const sourceUpdatedAt = "2026-08-14T10:00:00-06:00";\nexport const value = 43;\n')
        after, _ = fingerprint(root)
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
