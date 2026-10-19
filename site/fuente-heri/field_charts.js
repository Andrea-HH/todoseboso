/* Optional, source-backed charts. No raw data or invented fallback values. */
"use strict";
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const labels = {precipitation:"Lluvia mensual", ndvi:"NDVI satelital"};
  const unit = {precipitation:"mm", ndvi:"NDVI"};
  const months = ["Abr","May","Jun","Jul","Ago","Sep","Oct"];
  const byId = id => document.getElementById(id);
  const svg = (tag, attributes = {}, label) => {
    const node = document.createElementNS(NS, tag);
    for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, String(value));
    if (label !== undefined) node.textContent = label;
    return node;
  };
  const text = (canvas, value, x, y, options = {}) => canvas.appendChild(svg("text",{
    x,y,fill:options.color || "#254c3f","font-size":options.size || 13,
    "font-family":"system-ui, sans-serif","text-anchor":options.anchor || "start"
  },value));
  const finite = Number.isFinite;
  function validate(series, name) {
    if (!series || series.year !== 2025 || series.months?.length !== 7 ||
        series.variable !== name) throw Error("Serie de 2025 incompleta: "+name);
    series.months.forEach((r,i) => {
      if (r.month !== i+4 || !Number.isInteger(r.n) || r.n<1 || r.n>197 ||
          ![r.mean,r.p10,r.median,r.p90].every(finite) ||
          r.p10>r.median || r.median>r.p90 ||
          (name==="precipitation" && r.p10<0) ||
          (name==="ndvi" && (r.p10< -1 || r.p90>1))) {
        throw Error("Valor inválido en mes "+(i+4)+" de "+name);
      }
    });
  }
  function drawMonthly(target, series) {
    const rainfall=series.variable==="precipitation", title=labels[series.variable];
    const width=1000, height=330, left=91, right=942, top=35, bottom=265;
    const all=series.months.flatMap(x=>[x.p10,x.p90]);
    const low=rainfall?0:Math.min(-.1,Math.floor(Math.min(...all)*10)/10);
    const high=rainfall?Math.max(10,Math.ceil(Math.max(...all)*1.1/20)*20):
      Math.min(1,Math.max(.7,Math.ceil(Math.max(...all)*10)/10));
    const xAt=i=>left+46+(right-left-92)*i/6;
    const yAt=v=>bottom-(v-low)/(high-low)*(bottom-top);
    const canvas=svg("svg",{viewBox:"0 0 "+width+" "+height,role:"img",
      "aria-label":title+" de 2025, mediana y rango percentil 10 a 90"});
    canvas.classList.add("research-svg");
    canvas.style.minWidth="600px";
    canvas.appendChild(svg("title",{},title+" real, abril a octubre de 2025"));
    for(let j=0;j<=4;j++){
      const v=low+(high-low)*j/4,y=yAt(v);
      canvas.appendChild(svg("line",{x1:left,y1:y,x2:right,y2:y,stroke:"#d7dfd4"}));
      text(canvas,rainfall?v.toFixed(0):v.toFixed(2),left-16,y+5,{anchor:"end",size:12});
    }
    const path=series.months.map((r,i)=>(i?"L":"M")+xAt(i)+","+yAt(r.median)).join(" ");
    canvas.appendChild(svg("path",{d:path,stroke:"#39765e","stroke-width":3,
      fill:"none","stroke-linejoin":"round"}));
    const note=document.createElement("p");
    note.className="figure-reading";
    note.setAttribute("aria-live","polite");
    note.textContent="Selecciona un punto o utiliza Tab para consultar las estadísticas originales.";
    series.months.forEach((r,i)=>{
      const x=xAt(i), detail=months[i]+": "+r.n+" parcelas con datos; mediana "+
        r.median.toFixed(rainfall?1:3)+" "+unit[series.variable]+
        "; media "+r.mean.toFixed(rainfall?1:3)+"; percentiles 10–90 ["+
        r.p10.toFixed(rainfall?1:3)+", "+r.p90.toFixed(rainfall?1:3)+"].";
      canvas.appendChild(svg("line",{x1:x,y1:yAt(r.p10),x2:x,y2:yAt(r.p90),
        stroke:"#dfb977","stroke-width":8,"stroke-linecap":"round"}));
      const mark=svg("circle",{cx:x,cy:yAt(r.median),r:8,fill:"#39765e",
        stroke:"#fffef9","stroke-width":2,role:"img",tabindex:0,"aria-label":detail});
      mark.appendChild(svg("title",{},detail));
      for(const event of ["focus","mouseenter"])
        mark.addEventListener(event,()=>note.textContent=detail);
      canvas.appendChild(mark);
      text(canvas,months[i],x,bottom+28,{anchor:"middle",size:13});
    });
    target.replaceChildren();
    const wrap=document.createElement("div");
    wrap.className="figure-scroll";
    wrap.appendChild(canvas);
    target.append(wrap,note);
  }
  function drawResiduals(target, models) {
    if (!Array.isArray(models) || !models.length) {
      target.textContent="Todavía no se han proporcionado las 138 predicciones individuales LOOCV. No se infieren residuos a partir del RMSE.";
      return;
    }
    const table=document.createElement("table");
    table.className="real-model-metrics";
    const head=document.createElement("thead");
    const header=document.createElement("tr");
    for(const field of ["Modelo","RMSE LOOCV","MAE","Sesgo","Error absoluto máximo","R²"]){
      const th=document.createElement("th");th.textContent=field;header.appendChild(th);
    }
    head.appendChild(header);table.appendChild(head);
    const body=document.createElement("tbody");
    for(const item of models){
      if(item.n!==138 || item.validation!=="LOOCV")throw Error("Invalid LOOCV input");
      const m=item.metrics;
      if(![m.rmse,m.mae,m.bias,m.max_absolute_error].every(finite))
        throw Error("Incomplete LOOCV metrics");
      const tr=document.createElement("tr");
      for(const value of [item.model,m.rmse.toFixed(4),m.mae.toFixed(4),
                          m.bias.toFixed(4),m.max_absolute_error.toFixed(4),
                          m.r2==null?"undefined":m.r2.toFixed(4)]){
        const td=document.createElement("td");td.textContent=value;tr.appendChild(td);
      }
      body.appendChild(tr);
    }
    table.appendChild(body);
    const small=document.createElement("p");
    small.className="figure-axis-note";
    small.textContent="138 predicciones reservadas por modelo, con 137 etiquetas de entrenamiento en cada ajuste. "+
      "Sesgo = predicción menos observación; no se utilizan las 59 cosechas desconocidas.";
    target.replaceChildren(table,small);
  }
  async function main(){
    const rain=byId("real-rainfall"), ndvi=byId("real-ndvi"),
          validation=byId("real-loocv"),status=byId("real-chart-status");
    if(!rain||!ndvi||!validation||!status)return;
    const response=await fetch("./data/real_charts.json",{cache:"no-store"});
    if(response.status===404){
      status.textContent="Las mediciones de 2025 todavía no están exportadas. "+
        "El programa local de extracción está disponible; no se muestran gráficas sintéticas.";
      return;
    }
    if(!response.ok)throw Error("Cannot load aggregated source data");
    const data=await response.json();
    if(data.schema_version!==1 || data.kind!=="real_chart_aggregates")
      throw Error("Unexpected chart export schema");
    validate(data.rainfall,"precipitation");
    validate(data.ndvi,"ndvi");
    drawMonthly(rain,data.rainfall);
    drawMonthly(ndvi,data.ndvi);
    drawResiduals(validation,data.loocv_models);
    status.textContent="Datos originales de 2025: precipitación mensual y NDVI "+
      "de las parcelas del estudio (la cobertura se informa por mes). "+
      "Las bandas de percentiles muestran variación entre parcelas, no intervalos predictivos.";
  }
  main().catch(error=>{
    const status=byId("real-chart-status");
    if(status)status.textContent="No se pudo verificar el archivo de datos reales; no se muestran gráficas.";
    console.error("Real chart data verification failed:",error);
  });
})();
