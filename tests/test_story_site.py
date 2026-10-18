"""Lightweight public website checks; no ML, rasters or private bundle needed."""
import json
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class AuditHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.anchors = []
        self.assets = []
        self.lang = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise AssertionError("Duplicate HTML ID: " + attrs["id"])
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.anchors.append(attrs["href"][1:])
        if tag == "script" and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("href", "").startswith("./"):
            self.assets.append(attrs["href"])


class StorySiteTest(unittest.TestCase):
    def test_html_anchors_and_assets(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        parser = AuditHTML()
        parser.feed(html)
        self.assertEqual(parser.lang, "es")
        self.assertIn("contenido", parser.ids)
        self.assertIn("arquitectura", parser.ids)
        self.assertIn("evidencia", parser.ids)
        for anchor in parser.anchors:
            self.assertIn(anchor, parser.ids)
        for asset in parser.assets:
            self.assertTrue((SITE / asset).is_file(), asset)
        self.assertIn("simulación educativa", html)
        self.assertIn("no es", html.lower())
        self.assertNotIn("outputs/", html)
        self.assertNotIn("train138.parquet", html)

    def test_protocol_comparison_is_sourced(self):
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/sync_story_data.py"), "--check"],
            check=True, capture_output=True, text=True,
        )
        data = json.loads((SITE / "data/results.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(len(data["protocols"]), 5)
        expected = {"Reference26", "Compact14", "B1", "CT3", "L40"}
        for protocol in data["protocols"]:
            self.assertEqual({row["id"] for row in protocol["results"]}, expected)
            self.assertTrue(all(0 < row["rmse"] < 2 for row in protocol["results"]))
        fresh = next(p for p in data["protocols"] if p["id"] == "fresh_97_41")
        reference = next(row for row in fresh["results"] if row["id"] == "Reference26")
        self.assertAlmostEqual(reference["rmse"], .4624789693727327)
        self.assertAlmostEqual(reference["r2"], .6971349735771638)

    def test_illustrations_are_explicitly_synthetic(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertIn("Puntos ficticios", html)
        self.assertIn("valores inventados", html)
        self.assertIn("uniform: [30, 30, 30, 30, 30, 30, 30]", js)
        self.assertIn("showNeighbors(24)", js)
        self.assertIn("aria-pressed", js)
        self.assertIn("prefers-reduced-motion", (SITE / "styles.css").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()