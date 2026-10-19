/* Historia documentada de un solo modelo. No se ajustan coeficientes en el navegador. */
"use strict";
(() => {
  const $ = (q) => document.querySelector(q);
  const $$ = (q) => [...document.querySelectorAll(q)];
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const fmt = (n, decimals = 2) => Number(n).toFixed(decimals);
  const activeButtons = (selector, attribute, selected) => {
    $$(selector).forEach((button) => {
      const on = button.dataset[attribute] === String(selected);
      button.classList.toggle("active", on);
      button.setAttribute("aria-pressed", String(on));
    });
  };
  const featureTabs = $$("[data-feature]");
  let model = null, selectedCluster = 0;
  const showFeatures = (id) => {
    if (!model) return;
    const block = model.features.find((x) => x.key === id);
    if (!block) return;
    $("#feature-title").textContent = block.title;
    $("#feature-why").textContent = block.why;
    const table = $("#feature-rows");
    table.replaceChildren();
    for(const item of block.features) {
      const row = el("tr");
      const title = el("td");
      title.append(el("strong", "", item.number + ". " + item.name), el("code", "", item.code));
      row.append(title, el("td", "", item.how), el("td", "", item.interpret));
      table.append(row);
    }
    activeButtons("[data-feature]", "feature", id);
  };
  featureTabs.forEach((button) =>
    button.addEventListener("click", () => showFeatures(button.dataset.feature)));

  function drawClusters() {
    const root = $("#cluster-list");
    root.replaceChildren();
    model.final_fit.cluster_weights.forEach((weight, index) => {
      const button = el("button", "cluster-choice" + (index === selectedCluster ? " active" : ""));
      button.type = "button";
      button.setAttribute("aria-pressed", String(index === selectedCluster));
      button.setAttribute("aria-label", "Grupo geológico " + index +
        ", peso de experto local " + fmt(100 * weight, 1) + " %");
      const label = el("span", "cluster-description");
      label.append(el("strong", "", "Grupo geológico " + index),
        el("small", "", "Peso para las parcelas cercanas"));
      const meter = el("div", "cluster-meter");
      const fill = el("span", "");
      fill.style.width = 100 * weight + "%";
      meter.append(fill);
      const value = el("strong", "cluster-weight", fmt(weight * 100, 1) + " %");
      button.append(label, meter, value);
      button.addEventListener("click", () => {
        selectedCluster = index;
        drawClusters();
      });
      root.append(button);
    });
  }

  let research = null;
  function showIntervals(level) {
    if (!research) return;
    activeButtons("[data-level]", "level", level);
    window.GeoCharts.intervals($("#interval-results"),
      research.intervals.filter(x => x.level === Number(level) &&
        (x.model === "Reference26" || x.model === "Compact14")),
      Number(level));
  }
  $$("[data-level]").forEach((button) =>
    button.addEventListener("click", () => showIntervals(button.dataset.level)));

  function showFigures(evidence, results, newResearch, distributions) {
    const ids = ["fresh_97_41", "random", "climate_profile", "municipality", "spatial"];
    const labels = {
      fresh_97_41: ["16 pruebas de 97/41", "97 para entrenar, 41 para evaluar"],
      random: ["Parcelas aleatorias", "Se separan al azar en varias repeticiones"],
      climate_profile: ["Perfiles climáticos", "Se retienen grupos de clima"],
      municipality: ["Municipios completos", "Se retienen municipios completos"],
      spatial: ["Bloques geográficos", "Se retienen zonas geográficas"]
    };
    const performance = ids.map(id => {
      const protocol = results.protocols.find(x => x.id === id);
      const row = protocol && protocol.results.find(x => x.id === "Reference26");
      if (!row || !Number.isFinite(row.rmse)) throw Error("No hay RMSE del modelo en " + id);
      return {id, label: labels[id][0], description: labels[id][1],
        rmse: row.rmse, r2: row.r2, mae: row.mae};
    });
    // This separately reported aggregate has no archived per-parcel validation
    // predictions and cannot supply a source-backed MAE.
    const loo = model.loocv;
    if (loo && loo.folds === 138 && loo.training_labels_per_fold === 137 &&
        Number.isFinite(loo.rmse_t_ha) && Number.isFinite(loo.r2_approx)) {
      performance.unshift({
        id: "leave_one_out",
        label: "138 parcelas, una por turno",
        description: "137 para entrenar; 1 para evaluar",
        rmse: loo.rmse_t_ha, r2: loo.r2_approx, mae: null,
        provenance: "Resultado comunicado por el equipo, sin predicciones individuales públicas."
      });
    }
    window.GeoCharts.performance($("#performance-chart"), performance);
    const names = {
      random: "Parcelas aleatorias", climate_profile: "Perfiles climáticos",
      municipality: "Municipios completos", spatial: "Bloques geográficos"
    };
    const components = evidence.protocols.map(p => ({
      id:p.id,label:names[p.id],
      without:p.reference26_r3.without_r3,with:p.reference26_r3.with_r3,
      weight:p.expert_weight
    }));
    window.GeoCharts.r3($("#r3-comparison"), components);
    window.GeoCharts.expertWeights($("#expert-weights"), components);
    window.GeoCharts.coefficients($("#association-chart"), newResearch.associations);
    const sensitivity = newResearch.protocols.map(p => ({
      ...p,label:names[p.id]
    }));
    window.GeoCharts.forest($("#hhi-forest"), sensitivity, "spatial");
    window.GeoCharts.parcelCounts($("#parcel-coverage"), distributions.rows);
    window.GeoCharts.distribution($("#distribution-quantiles"), distributions.rows);
    research = newResearch;
    showIntervals("0.9");
  }
  (async () => {
    try {
      const sources = ["model.json", "evidence.json", "results.json",
        "new_research.json", "distribution.json"];
      const entries = await Promise.all(sources.map(async file => {
        const res = await fetch("./data/" + file, {cache:"no-store"});
        if (!res.ok) throw Error("No se pudo leer " + file);
        return res.json();
      }));
      const [m, evidence, results, newResearch, distributions] = entries;
      if(m.schema_version !== 1 || m.features.length !== 5 ||
        m.features.reduce((sum, group) => sum + group.features.length, 0) !== 26 ||
        m.final_fit.cluster_weights.length !== 4 ||
        evidence.protocols.length !== 4 || results.protocols.length !== 5 ||
        newResearch.protocols.length !== 4 || distributions.rows.length !== 8) {
        throw Error("El esquema de entradas y resultados no coincide con la documentación");
      }
      model = m;
      showFeatures("clima");
      drawClusters();
      showFigures(evidence, results, newResearch, distributions);
    } catch (error) {
      console.error("Error al cargar el modelo documentado:", error);
      for (const id of ["feature-rows", "cluster-list", "parcel-coverage", "performance-chart",
        "r3-comparison", "expert-weights", "association-chart", "hhi-forest",
        "interval-results", "distribution-quantiles"]) {
        const target = $("#" + id);
        if (target) target.textContent =
          "No se cargaron los datos de esta gráfica. Puedes consultar las tablas originales del repositorio.";
      }
    }
  })();
})();