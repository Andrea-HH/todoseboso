"""Validación pública de rendimiento observado vs. estimado en el explorador."""
import csv
import gzip
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "site" / "explorador" / "data"


def read_csv(filename):
    with (PUBLIC / filename).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fields = list(reader.fieldnames or [])
        records = list(reader)
    return fields, records


class PublicMapYieldData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.training_fields, cls.training = read_csv("training_yields.csv")
        cls.prediction_fields, cls.prediction = read_csv("predictions.csv")
        with gzip.open(PUBLIC / "mapa_publico.json.gz", "rt", encoding="utf-8") as source:
            package = json.load(source)
        cls.geometries = package["geometry"]["features"]

    def test_public_release_has_only_two_authorized_columns(self):
        expected = ["ID_POLIGONO", "RENDIMIENTO_T_HA"]
        self.assertEqual(self.training_fields, expected)
        self.assertEqual(self.prediction_fields, expected)
        self.assertEqual(len(self.training), 138)
        self.assertEqual(len(self.prediction), 59)

    def test_no_missing_invalid_or_duplicated_yields(self):
        for rows, expected_size in ((self.training, 138), (self.prediction, 59)):
            ids = [row["ID_POLIGONO"] for row in rows]
            self.assertEqual(len(ids), expected_size)
            self.assertEqual(len(set(ids)), expected_size)
            for row in rows:
                self.assertRegex(row["ID_POLIGONO"], r"^AGC_\d+$")
                self.assertGreater(float(row["RENDIMIENTO_T_HA"]), 0)

    def test_observed_and_predictions_are_disjoint_and_match_geometry(self):
        train = {row["ID_POLIGONO"] for row in self.training}
        prediction = {row["ID_POLIGONO"] for row in self.prediction}
        self.assertFalse(train.intersection(prediction))
        self.assertEqual(len(self.geometries), 197)
        geometries_train = {
            f["properties"]["ID_POLIGONO"] for f in self.geometries
            if f["properties"]["CONJUNTO"] == "ENTRENAMIENTO"
        }
        geometries_prediction = {
            f["properties"]["ID_POLIGONO"] for f in self.geometries
            if f["properties"]["CONJUNTO"] == "PREDICCION"
        }
        self.assertEqual(train, geometries_train)
        self.assertEqual(prediction, geometries_prediction)

    def test_observed_distribution_preserves_original_measurements(self):
        observed = [float(row["RENDIMIENTO_T_HA"]) for row in self.training]
        self.assertAlmostEqual(sum(observed) / 138, 3.9553623188405793, places=9)
        self.assertEqual(min(observed), 2.0)
        self.assertEqual(max(observed), 5.59)


if __name__ == "__main__":
    unittest.main()
