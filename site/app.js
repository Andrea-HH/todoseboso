/* Small, accessible teaching demos. No analytics, external JS or predictions. */
"use strict";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const navigation = $("#nav-links");
const menu = $("#menu-toggle");
menu.addEventListener("click", () => {
  const expanded = menu.getAttribute("aria-expanded") === "true";
  menu.setAttribute("aria-expanded", String(!expanded));
  navigation.classList.toggle("open", !expanded);
});
$$("#nav-links a").forEach((link) => link.addEventListener("click", () => {
  navigation.classList.remove("open");
  menu.setAttribute("aria-expanded", "false");
}));

let progressQueued = false;
window.addEventListener("scroll", () => {
  if (progressQueued) return;
  progressQueued = true;
  requestAnimationFrame(() => {
    const total = document.documentElement.scrollHeight - window.innerHeight;
    $("#read-progress").style.width = total > 0 ? `${Math.max(0, Math.min(100, 100 * scrollY / total))}%` : "0%";
    progressQueued = false;
  });
}, { passive: true });

// Two synthetic rainfall patterns have identical total rainfall (210 mm).
const RAIN = {
  uniform: [30, 30, 30, 30, 30, 30, 30],
  concentrated: [10, 10, 10, 20, 140, 10, 10]
};
function showRainfall(kind) {
  const values = RAIN[kind];
  if (!values) return;
  const sum = values.reduce((a, b) => a + b, 0);
  const early = values.slice(0, 3).reduce((a, b) => a + b, 0) / sum;
  const hhi = values.reduce((acc, v) => acc + (v / sum) ** 2, 0);
  $$("#rain-bars .bar").forEach((bar, i) => bar.style.setProperty("--height", `${values[i] / 150 * 100}%`));
  $("#rain-total").textContent = `${sum} mm`;
  $("#rain-early").textContent = `${(early * 100).toFixed(1)} %`;
  $("#rain-hhi").textContent = hhi.toFixed(3);
  $("#rain-bars").setAttribute("aria-label", `Lluvia simulada de abril a octubre: ${values.join(", ")} mm`);
  $$("[data-rain]").forEach((button) => {
    const active = button.dataset.rain === kind;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}
$$("[data-rain]").forEach(button => button.addEventListener("click", () => showRainfall(button.dataset.rain)));
showRainfall("uniform");

// Deterministic, fictional points. Nearest points are chosen by 2D screen distance.
const svgNS = "http://www.w3.org/2000/svg";
const points = Array.from({length: 38}, (_, i) => {
  const theta = i * 2.399963229728653;
  const radius = 39 + 141 * Math.sqrt((i + 0.5) / 38);
  const x = 230 + radius * Math.cos(theta) * 1.07;
  const y = 207 + radius * Math.sin(theta) * 0.95;
  return { x, y, radius, i };
}).sort((a, b) => a.radius - b.radius);
function svgElement(tag, attrs) {
  const element = document.createElementNS(svgNS, tag);
  for (const [name, value] of Object.entries(attrs)) element.setAttribute(name, String(value));
  return element;
}
function showNeighbors(k) {
  const lines = $("#neighbor-connections"), dots = $("#neighbor-points");
  lines.replaceChildren(); dots.replaceChildren();
  points.forEach((point, i) => {
    const selected = i < k;
    if (selected) lines.appendChild(svgElement("line", {
      x1: 230, y1: 207, x2: point.x, y2: point.y,
      stroke: "#8dbb91", "stroke-opacity": "0.40", "stroke-width": "1.1"
    }));
    dots.appendChild(svgElement("circle", {
      cx: point.x, cy: point.y, r: selected ? 5.3 : 4.3,
      fill: selected ? "#42845e" : "#b9cab8",
      "fill-opacity": selected ? 1 : .85
    }));
  });
  $("#neighbor-k-value").textContent = String(k);
  $("#neighbor-svg").setAttribute("aria-label", `Diagrama ficticio: una consulta central y ${k} vecinos más cercanos seleccionados de 38 puntos`);
}
$("#neighbor-k").addEventListener("input", (event) => showNeighbors(Number(event.target.value)));
showNeighbors(24);

const LABELS = {
  "Reference26": ["Reference26", "Champion de referencia"],
  "Compact14": ["Compact14", "Champion compacto"],
  "B1": ["B1", "Sensibilidad"],
  "L40": ["Local04D / L40", "Referencia GeoC"],
  "CT3": ["C-T3", "Núcleo global"]
};
const ORDER = ["Reference26", "Compact14", "B1", "L40", "CT3"];
let protocols = null;
function setProtocol(id) {
  if (!protocols) return;
  const info = protocols.find((item) => item.id === id);
  if (!info) return;
  $$("[data-protocol]").forEach((button) => {
    const active = button.dataset.protocol === id;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  $("#protocol-caption").textContent = info.description;
  const chart = $("#results-chart");
  chart.replaceChildren();
  // A common 0-to-1 t/ha scale makes cross-protocol changes visually honest.
  ORDER.forEach((name) => {
    const metric = info.results.find((item) => item.id === name);
    if (!metric) throw Error("Falta el modelo " + name);
    const row = document.createElement("div");
    row.className = `result-row ${name === "Reference26" || name === "Compact14" ? "champion" : name === "L40" ? "reference" : ""}`;
    const label = document.createElement("div"); label.className = "result-label";
    const title = document.createElement("span"); title.textContent = LABELS[name][0];
    const sub = document.createElement("small"); sub.textContent = LABELS[name][1];
    label.append(title, sub);
    const track = document.createElement("div"); track.className = "result-track";
    const fill = document.createElement("span"); fill.className = "result-fill";
    fill.style.width = `${Math.min(100, metric.rmse * 100).toFixed(3)}%`;
    track.append(fill);
    const value = document.createElement("span"); value.className = "result-value";
    value.textContent = metric.rmse.toFixed(4);
    row.setAttribute("aria-label", `${LABELS[name][0]}, RMSE ${metric.rmse.toFixed(4)} toneladas por hectárea`);
    row.append(label, track, value); chart.append(row);
  });
}
$$("[data-protocol]").forEach((button) => button.addEventListener("click", () => setProtocol(button.dataset.protocol)));
(async function loadEvidence() {
  try {
    const response = await fetch("./data/results.json", {cache: "no-store"});
    if (!response.ok) throw Error("No se encontró el archivo de métricas");
    const data = await response.json();
    if (data.schema_version !== 1 || !Array.isArray(data.protocols) || data.protocols.length !== 5) throw Error("Esquema inesperado");
    for (const protocol of data.protocols) {
      if (ORDER.some((name) => !protocol.results.some((row) => row.id === name && Number.isFinite(row.rmse) && row.rmse > 0))) throw Error("Resultados incompletos");
    }
    protocols = data.protocols;
    setProtocol("fresh_97_41");
  } catch (error) {
    console.error("Datos de evaluación no disponibles:", error);
    $("#protocol-caption").textContent = "No se pudieron cargar los resultados. Consulta las fuentes en GitHub.";
    $("#results-chart").textContent = "Las métricas están disponibles en los resultados versionados del repositorio.";
  }
})();