#!/usr/bin/env python3
"""Check public explanatory figures against frozen upstream research aggregates."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site/data/new_research.json"


def csv_rows(name):
    with (ROOT / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def one(rows, **where):
    found = [r for r in rows if all(r.get(k) == str(v) for k, v in where.items())]
    assert len(found) == 1, (where, len(found))
    return found[0]


def close(actual, expected):
    assert math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-11), (
        actual, expected,
    )


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    assert d["schema_version"] == 1
    protocols = d["protocols"]
    assert [p["id"] for p in protocols] == [
        "random", "climate_profile", "municipality", "spatial"
    ]
    metrics = csv_rows("results/four_final_checks/v1/sensitivity_metrics.csv")
    paired = csv_rows("results/four_final_checks/v1/sensitivity_paired_tests.csv")
    for p in protocols:
        pid = p["id"]
        close(p["reference26"], one(metrics, experiment="Reference26", protocol=pid)["rmse"])
        close(p["without_hhi"], one(metrics, experiment="Reference25_NoHHI", protocol=pid)["rmse"])
        test = one(paired, protocol=pid)
        close(p["delta"], test["delta_rmse_NoHHI_minus26"])
        close(p["ci95"][0], test["low95_fixed_oof"])
        close(p["ci95"][1], test["high95_fixed_oof"])
        close(p["p_holm"], test["p_holm4"])
        assert p["groups"] == int(test["groups"])
        assert p["ci95"][0] < 0 < p["ci95"][1], "Do not claim significance"

    associations = csv_rows("results/core4_relevance/v1/association_tests.csv")
    coefficients = csv_rows("results/core4_relevance/v1/association_coefficients.csv")
    assert len(d["associations"]) == 4
    for item in d["associations"]:
        coef = one(coefficients, feature=item["id"], model="CORE4_PLUS_STATE")
        test = one(associations, model="CORE4_PLUS_STATE", hypothesis=item["id"] + " coefficient=0")
        close(item["coefficient_per_SD"], coef["coefficient_per_SD"])
        close(item["p_holm"], test["p_holm_family13"])
    assert d["associations"][2]["p_holm"] > 0.05

    audit = json.loads((ROOT / "results/reference26_component_evidence/v1/audit.json").read_text())
    assert d["architecture_tests"] == audit["archived_families"]
    assert sum(v["tests"] for v in d["architecture_tests"].values()) == 952
    assert sum(v["significant_holm"] for v in d["architecture_tests"].values()) == 0
    core = json.loads((ROOT / "results/core4_relevance/v1/audit.json").read_text())
    assert d["core4_audit"] == core

    support = one(csv_rows("results/four_final_checks/v1/support_summary.csv"), region="all")
    for key, source_key in {
        "n": "n", "any_flag": "any_flag", "missing_r3": "missing_R3",
        "outside_geography": "geo_above_training_q95",
        "outside_climate": "core4_above_training_q95",
        "outside_local": "local7_above_training_q95",
    }.items():
        assert d["support"][key] == int(support[source_key])

    interval = csv_rows("results/four_final_checks/v1/interval_metrics.csv")
    assert len(d["intervals"]) == 4
    for row in d["intervals"]:
        src = one(interval, model=row["model"], protocol="random",
                  strategy="parcel_split", level=row["level"])
        close(row["coverage"], src["coverage"])
        close(row["width"], src["mean_width_finite"])
        close(row["finite_fraction"], src["finite_fraction"])

    # Do not accidentally publish observed yields, polygon IDs, or fake accuracy.
    data_text = DATA.read_text(encoding="utf-8")
    assert "ID_POLIGONO" not in data_text and "train138.parquet" not in data_text
    html = (ROOT / "site/index.html").read_text(encoding="utf-8")
    js = (ROOT / "site/preguntas.js").read_text(encoding="utf-8")
    css = (ROOT / "site/preguntas.css").read_text(encoding="utf-8")
    for section in ["significancia", "retirar-hhi", "intervalos", "cobertura"]:
        assert f'id="{section}"' in html
    assert "new_research.json" in js and "p_holm" in js
    assert "prefers-reduced-motion" in css
    print("PASS: evidence, Holm p-values, intervals, HHI and support match upstream sources")


if __name__ == "__main__":
    main()
