/* Visualización pública de la entrega final GeoC: 59 estimaciones y 7 estrategias.
   Se conserva el nombre del archivo para compatibilidad con la integración existente.
   Las 59 cosechas observadas no se conocen; no se recalculan las predicciones. */
(function () {
"use strict";
const get=id=>document.getElementById(id);
const el=(tag,cls,txt)=>{
  const node=document.createElement(tag);
  if(cls)node.className=cls;
  if(txt!==undefined)node.textContent=String(txt);
  return node;
};
const fmt=(v,d=3)=>Number(v).toLocaleString("es-MX",{minimumFractionDigits:d,maximumFractionDigits:d});
const EXPECTED="robust26_3_neighbors_supported_0p25";
async function readText(path) {
  const response=await fetch(path,{cache:"no-store"});
  if(!response.ok)throw Error("No fue posible leer "+path+" ("+response.status+")");
  return response.text();
}
async function readFinal() {
  const [rawMeta,csv]=await Promise.all([
    readText("./data/final_model.json"),readText("./data/submission59_final.csv")
  ]);
  const meta=JSON.parse(rawMeta);
  if(meta.schema_version!==1||meta.final_fit_selected!==EXPECTED||
     meta.train_labels!==138||meta.unknown_labels!==59||
     !Array.isArray(meta.loocv)||meta.loocv.length!==7)
    throw Error("La ficha del experimento final no tiene la configuración esperada");
  const lines=csv.trim().split(/\r?\n/).map(x=>x.replace(/^\uFEFF/,"").trim());
  if(lines.shift()!=="ID_POLIGONO,RENDIMIENTO_T_HA")
    throw Error("El CSV final no contiene las columnas publicadas");
  const entries=lines.map(line=>{
    const fields=line.split(",");
    if(fields.length!==2)throw Error("Fila incompleta de predicciones finales");
    return {id:fields[0],value:Number(fields[1]),state:"",municipality:""};
  });
  if(entries.length!==59||new Set(entries.map(x=>x.id)).size!==59||
    entries.some(x=>!/^AGC_\d+$/.test(x.id)||!Number.isFinite(x.value)||x.value<=0))
    throw Error("Los 59 identificadores y rendimientos no están completos");
  const sorted=entries.map(x=>x.value).sort((a,b)=>a-b);
  const aggregate=meta.prediction59_aggregate;
  for(const [key,value] of Object.entries({
    selected_mean:sorted.reduce((sum,v)=>sum+v,0)/59,
    selected_median:sorted[29],selected_min:sorted[0],selected_max:sorted[58]
  })){
    if(!Number.isFinite(aggregate?.[key])||Math.abs(aggregate[key]-value)>1e-8)
      throw Error("El estadístico "+key+" difiere de la entrega GeoC");
  }
  if(aggregate.n!==59||Object.values(meta.selection_4fold_counts||{}).reduce((a,b)=>a+b,0)!==138)
    throw Error("El número de predicciones o elecciones LOOCV no coincide");
  for(const row of meta.loocv){
    if(!["rmse","mae","r2","bias"].every(k=>Number.isFinite(row[k])))
      throw Error("Métricas incompletas en "+row.name);
  }
  return {meta,entries};
}
async function addGeography(entries){
  if(typeof DecompressionStream==="undefined")return false;
  const response=await fetch("../explorador/data/mapa_publico.json.gz",{cache:"no-store"});
  if(!response.ok||!response.body)return false;
  const geodata=JSON.parse(await new Response(response.body.pipeThrough(new DecompressionStream("gzip"))).text());
  if(geodata.schema!=="geocebada-map-public-1"||
      geodata.geometry?.type!=="FeatureCollection"||
      geodata.geometry.features?.length!==197)
    throw Error("Geografía no verificable");
  const places=new Map(),count={Hidalgo:0,Puebla:0,Tlaxcala:0};
  for(const feature of geodata.geometry.features){
    const p=feature.properties||{};
    const id=String(p.ID_POLIGONO||p.ID_POLIGON||"").trim().toUpperCase();
    const state=String(p.Estado||p.estado||"").trim();
    const split=String(p.CONJUNTO||p.conjunto||"").trim().toUpperCase();
    if(!/^AGC_\d+$/.test(id)||places.has(id)||
       !Object.hasOwn(count,state)||!["ENTRENAMIENTO","PREDICCION"].includes(split))
      throw Error("Metadatos geográficos inconsistentes");
    places.set(id,{state,split,municipality:String(p.Municipio||p.municipio||"").trim()});
    if(split==="PREDICCION")count[state]++;
  }
  if(count.Hidalgo!==15||count.Puebla!==29||count.Tlaxcala!==15||
     entries.some(x=>places.get(x.id)?.split!=="PREDICCION"))
    throw Error("El conjunto de predicción no coincide con el mapa");
  for(const item of entries){
    item.state=places.get(item.id).state;
    item.municipality=places.get(item.id).municipality;
  }
  return true;
}
function render59(entries,haveGeography){
  const ordered=[...entries].sort((a,b)=>a.value-b.value||a.id.localeCompare(b.id));
  const average=entries.reduce((a,b)=>a+b.value,0)/59;
  const summary=get("pred59-summary"); summary.replaceChildren();
  const cells=[
    ["Parcelas estimadas","59","Cosechas de las 59 aún desconocidas"],
    ["Media",fmt(average,4)+" t/ha","Media de las predicciones finales"],
    ["Mínimo",fmt(ordered[0].value,3)+" t/ha","Estimación, no cosecha medida"],
    ["Máximo",fmt(ordered[58].value,3)+" t/ha","Estimación, no cosecha medida"]
  ];
  for(const [label,val,note] of cells){
    const card=el("div","pred59-summary-item");
    card.append(el("span","",label),el("strong","",val),el("small","",note));
    summary.append(card);
  }
  const examples=get("pred59-examples");examples.replaceChildren();
  for(const [label,entry] of [
    ["Menor estimación",ordered[0]],["Estimación mediana",ordered[29]],["Mayor estimación",ordered[58]]
  ]){
    const box=el("div","pred59-example pred59-example-static");
    box.append(el("span","pred59-eyebrow",label),
       el("strong","",fmt(entry.value,3)+" t/ha"),
       el("span","",entry.id),
       el("small","",haveGeography?entry.state+
          (entry.municipality?" · "+entry.municipality:""):"Parcela del reto"));
    examples.append(box);
  }
  const chart=get("final59-distribution");
  if(chart){
    chart.replaceChildren();
    const buckets=Array.from({length:10},()=>0);
    for(const entry of entries){
      const index=Math.floor((entry.value-2.5)/.25);
      if(index<0||index>=10)throw Error("Predicción fuera de los intervalos publicados");
      buckets[index]++;
    }
    if(buckets.reduce((a,b)=>a+b,0)!==59)throw Error("El histograma no cubre 59 parcelas");
    const columns=el("div","final59-bars");
    const max=Math.max(...buckets,1);
    buckets.forEach((count,i)=>{
      const base=2.5+i*.25;
      const column=el("div","final59-column");
      column.setAttribute("aria-label",fmt(base,2)+" t/ha: "+count+" parcelas");
      const countLabel=el("strong","",count);
      const track=el("span","final59-column-track");
      const bar=el("span","final59-column-fill");
      bar.style.height=(count/max*100)+"%";
      track.append(bar);
      column.append(countLabel,track,el("small","",fmt(base,2)));
      columns.append(column);
    });
    chart.append(columns);
    chart.append(el("p","final59-caption","59 predicciones verificadas · ancho de intervalo 0.25 t/ha"));
  }
}
const METRICS=[
  {id:"rmse",label:"RMSE",unit:" t/ha",digits:6,hint:"Menor RMSE es mejor."},
  {id:"mae",label:"MAE",unit:" t/ha",digits:6,hint:"Menor MAE es mejor."},
  {id:"r2",label:"R²",unit:"",digits:6,hint:"Mayor R² predictivo es mejor.",reverse:true},
  {id:"bias",label:"Sesgo",unit:" t/ha",digits:6,hint:"Sesgo de predicción menos observación: más cerca de cero es preferible."},
  {id:"mse",label:"MSE",unit:" (t/ha)²",digits:6,hint:"MSE ≈ RMSE²; derivación de cifras publicadas."},
  {id:"l1",label:"L1",unit:" t/ha",digits:4,hint:"L1 ≈ MAE × 138; valor aproximado por redondeo."},
  {id:"l2",label:"L2",unit:" t/ha",digits:4,hint:"L2 ≈ RMSE × √138; valor aproximado por redondeo."}
];
function metricVal(row,key){
  if(key==="mse")return row.rmse*row.rmse;
  if(key==="l1")return row.mae*138;
  if(key==="l2")return row.rmse*Math.sqrt(138);
  return row[key];
}
function renderStrategies(model){
  const buttons=get("final-metric-buttons"),target=get("final-strategies");
  if(!buttons||!target)return;
  buttons.replaceChildren();
  let selected="rmse";
  const draw=()=>{
    const spec=METRICS.find(m=>m.id===selected);
    for(const b of buttons.querySelectorAll("button"))b.setAttribute("aria-pressed",String(b.dataset.metric===selected));
    const list=[...model.loocv].sort((a,b)=>{
      const x=metricVal(a,selected),y=metricVal(b,selected);
      if(spec.reverse)return y-x;
      if(selected==="bias")return Math.abs(x)-Math.abs(y);
      return x-y;
    });
    const values=list.map(item=>selected==="bias"?Math.abs(metricVal(item,selected)):metricVal(item,selected));
    const high=Math.max(...values),low=Math.min(...values);
    const rows=el("div","final-strategy-list");
    list.forEach((item,i)=>{
      const value=metricVal(item,selected);
      const score=selected==="bias"?Math.abs(value):value;
      const pct=(high===low?75:16+80*((score-low)/(high-low)));
      const row=el("div","final-strategy-row");
      const heading=el("div","final-strategy-heading");
      heading.append(el("strong","",item.name),el("span","",fmt(value,spec.digits)+spec.unit));
      const track=el("span","final-strategy-track");
      const fill=el("span","final-strategy-fill "+(item.kind==="conditional_nested"?"nested":item.kind==="base"?"base":"fixed"));
      fill.style.width=pct+"%";track.append(fill);
      const note=el("small","",item.kind==="conditional_nested"?"Selección interna en cada fold":item.kind==="base"?"Ensamble original, sin corrección":"Corrección fija, evaluada retrospectivamente");
      row.append(heading,track,note);rows.append(row);
    });
    target.replaceChildren(rows);
    get("final-metric-footnote").textContent=spec.hint+" Las barras comparan solo el rango de siete estrategias (escala relativa, no eje desde cero). "+
      "Las alternativas fijas se eligieron tras revisar los mismos datos.";
  };
  for(const m of METRICS){
    const b=el("button","",m.label);b.type="button";b.dataset.metric=m.id;
    b.setAttribute("aria-pressed",String(m.id===selected));
    b.addEventListener("click",()=>{selected=m.id;draw()});
    buttons.append(b);
  }
  draw();
}
function renderSelections(meta){
  const target=get("final-selection-bars");if(!target)return;
  target.replaceChildren();
  const specs=[
    ["robust26_3_neighbors_supported_0p25","Vecinos robustos (3; 25 %)"],
    ["pca8_3_neighbors_supported_0p25","PCA8 (3; 25 %)"],
    ["no_correction","Sin corrección"]
  ];
  const box=el("div","final-selection-list");
  for(const [key,label] of specs){
    const amount=meta.selection_4fold_counts[key];
    if(!Number.isInteger(amount))throw Error("Selección interna desconocida: "+key);
    const line=el("div","final-selection-row");
    const heading=el("div","final-strategy-heading");
    heading.append(el("strong","",label),el("span","",amount+" / 138"));
    const track=el("span","final-strategy-track"),bar=el("span","final-strategy-fill");
    bar.style.width=(amount/138*100)+"%";track.append(bar);
    line.append(heading,track);box.append(line);
  }
  target.append(box);
}
async function init(){
  if(document.documentElement.dataset.researchVista!=="resultados")return;
  const status=get("pred59-status");
  try{
    const {meta,entries}=await readFinal();
    let geography=false;
    try{geography=await addGeography(entries)}
    catch(err){console.warn("Los estados no se mostrarán sin verificar:",err.message)}
    render59(entries,geography);
    renderStrategies(meta);
    renderSelections(meta);
    get("pred59-data").hidden=false;
    status.textContent="59 estimaciones finales verificadas contra el CSV y agregados de GeoC. "+
      (geography?"Estados contrastados con el mapa. ":"")+
      "Las 59 cosechas reales siguen siendo desconocidas.";
  }catch(err){
    if(status)status.textContent="No se pudieron verificar las predicciones definitivas: "+err.message;
    const strategies=get("final-strategies");
    if(strategies)strategies.textContent="No se pudieron verificar las siete estrategias: "+err.message;
    console.error(err);
  }
}
document.addEventListener("DOMContentLoaded",init);
})();