#!/usr/bin/env python3
"""Audit the public interpretation snapshot against upstream aggregate CSVs.

No private rows, hidden yields, saved models, licensed images or fitted pipelines.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SOURCES = (
    "results/core4_relevance/v1/metrics.csv",
    "results/reference26_component_evidence/v1/architecture_metrics.csv",
    "results/reference26_component_evidence/v1/component_weights.csv",
)
EXPECTED_PROT = ("random", "climate_profile", "municipality", "spatial")
MODELS = (
    "FULL4", "DROP_compact_precip_total", "DROP_compact_early_fraction",
    "DROP_compact_concentration_hhi", "DROP_S2_ndvi_month_05",
)


def read(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def single(rows: list[dict[str, str]], *, experiment: str, protocol: str) -> dict[str, str]:
    found = [r for r in rows if r["experiment"] == experiment and r["protocol"] == protocol]
    if len(found) != 1:
        raise AssertionError("Missing or duplicate source: " + experiment + " / " + protocol)
    return found[0]


def main() -> None:
    out = SITE / "data/evidence.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert tuple(data["source_files"]) == SOURCES
    assert len(data["protocols"]) == 4
    ablations, architecture, weights = (read(p) for p in SOURCES)
    assert tuple(p["id"] for p in data["protocols"]) == EXPECTED_PROT
    for protocol in data["protocols"]:
        name = protocol["id"]
        assert tuple(x["id"] for x in protocol["core4_ablations"]) == MODELS
        for entry in protocol["core4_ablations"]:
            source = single(ablations, experiment=entry["id"], protocol=name)
            assert math.isclose(entry["rmse"], float(source["rmse"]), abs_tol=1e-12)
        r3 = protocol["reference26_r3"]
        without = single(architecture, experiment="FULL7_ON_RAW_BASE", protocol=name)
        with_r3 = single(architecture, experiment="FULL7_ON_RAW_MASK", protocol=name)
        assert math.isclose(r3["without_r3"], float(without["rmse"]), abs_tol=1e-12)
        assert math.isclose(r3["with_r3"], float(with_r3["rmse"]), abs_tol=1e-12)
        weight = single(weights, experiment="FULL7_ON_RAW_MASK", protocol=name)
        assert math.isclose(protocol["expert_weight"], float(weight["expert_weight"]), abs_tol=1e-12)
        assert 0 <= protocol["expert_weight"] <= 1

    html = (SITE / "index.html").read_text(encoding="utf-8")
    js = (SITE / "app.js").read_text(encoding="utf-8")
    assert "id=\"componentes\"" in html
    for item in ("ablation-chart", "r3-comparison", "expert-weights"):
        assert "id=\"" + item + "\"" in html
    assert "./data/evidence.json" in js
    assert "Ninguna retirada individual" in html
    assert "ID_POLIGONO" not in out.read_text(encoding="utf-8")
    print("Public interpretation snapshot PASS: matched three upstream CSVs, four protocols.")


if __name__ == "__main__":
    main()
