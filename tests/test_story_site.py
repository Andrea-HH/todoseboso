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
        self.assertIn("LOOCV", html)
        self.assertIn("imputación por media", html)
        self.assertIn("predicciones históricas", html)
        self.assertIn("Clima, vecinos y geología", (SITE / "app.js").read_text(encoding="utf-8"))
        self.assertIn("Clima y vecinos, sin geología", html)
        self.assertNotIn("outputs/", html)
        self.assertNotIn("train138.parquet", html)

    def test_reference26_enrichment_is_documented(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        for anchor in ("variables-detalle", "preparacion-datos", "entrenamiento-modelo",
                       "datos-faltantes", "diagnostico-residuos", "predicciones-detalle"):
            self.assertIn('id="' + anchor + '"', html)
        import json
        inventory = json.loads((SITE / "data/reference26_features.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(len(g["features"]) for g in inventory["features"]), 26)
        residuals = json.loads((SITE / "data/reference26_residuals.json").read_text(encoding="utf-8"))
        self.assertEqual(residuals["protocol"]["imputation"], "mean_training_only")
        self.assertEqual(residuals["n_labeled"], 138)
        original = (SITE / "fuente-heri/index.html").read_text(encoding="utf-8")
        self.assertIn('id="estadisticas-finales"', original)
        self.assertIn('id="pred59-plot"', original)
        self.assertIn('id="real-rainfall"', original)
        self.assertIn('reference26_residuals.js', original)
        self.assertNotIn('scientific-charts.js', html)
        # La documentación de Heri permanece archivada, pero la presentación
        # de resultados se integra en las secciones de Andrea.
        self.assertNotIn("FUENTE ORIGINAL · CONTENIDO ÍNTEGRO", html)
        self.assertNotIn("data-geo-heri-section=", html)
        self.assertNotIn("geo-heri-disclosure", html)
        self.assertNotIn("geo-fuente-embed.js", html)
        for anchor in ("datos-reales", "geo-lluvia-real", "geo-ndvi-real",
                       "geo-59-grafica", "geo-59-tabla",
                       "geo-residuos-paneles"):
            self.assertIn('id="' + anchor + '"', html)
        self.assertIn("andrea-integracion.js", html)
        self.assertIn("andrea-integracion.css", html)
        script = (SITE / "andrea-integracion.js").read_text(encoding="utf-8")
        self.assertIn("data/reference26_residuals.json", script)
        self.assertIn("explorador/data/predictions.csv", script)
        self.assertIn("data/real_charts.json", script)
        # La vista sigue siendo la de Andrea: no hay controles nuevos sin datos.
        self.assertNotIn('id="geo-modelo-ejemplo"', html)
        self.assertNotIn('id="geo-59-estado"', html)
        self.assertNotIn('id="geo-59-detalle"', html)
        self.assertIn('id="geo-geologia-pesos"', html)
        self.assertIn("fuente-heri/data/model.json", script)
        archived = json.loads((SITE / "fuente-heri/data/model.json").read_text(encoding="utf-8"))
        final = archived["final_fit"]
        self.assertEqual(final["geologic_groups"], 4)
        self.assertEqual(final["local_neighbors"], 24)
        self.assertEqual(len(final["cluster_weights"]), 4)
        self.assertTrue(all(0 <= x <= 1 for x in final["cluster_weights"]))
        csv = (SITE / "explorador/data/predictions.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(csv), 60)  # encabezado más 59 estimaciones originales

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
        self.assertIn("Las ubicaciones del dibujo son inventadas", html)
        self.assertIn("números inventados", html)
        self.assertIn("uniform: [30, 30, 30, 30, 30, 30, 30]", js)
        self.assertIn("showNeighbors(24)", js)
        self.assertIn("aria-pressed", js)
        self.assertIn("prefers-reduced-motion", (SITE / "styles.css").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()