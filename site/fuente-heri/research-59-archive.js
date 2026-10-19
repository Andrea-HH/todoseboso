/* Adaptación de la visualización original "59 predicciones" de Heri.
 * Usa exclusivamente el CSV histórico autorizado y geometrías públicas originales.
 * No simula un runtime de ML, ninguna contribución ni un intervalo de confianza.
 * Si alguna vez está disponible el runtime con paridad 59/59, no interviene.
 */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const make=(tag,cls,content)=>{
  const e=document.createElement(tag);if(cls)e.className=cls;
  if(content!==undefined)e.textContent=String(content);return e;
};
const fmt=(n,d=3)=>Number(n).toFixed(d);
const meanRef=3.956432328667021;
async function records(){
 const response=await fetch("../explorador/data/predictions.csv",{cache:"no-store"});
 if(!response.ok)throw Error("El CSV histórico autorizado no está disponible.");
 const lines=(await response.text()).trim().split(/\r?\n/).map(s=>s.replace(/^\uFEFF/,"").trim());
 if(lines.shift()!=="ID_POLIGONO,RENDIMIENTO_T_HA")throw Error("El encabezado no corresponde al archivo histórico.");
 const records=lines.map(l=>{
   const values=l.split(",");
   if(values.length!==2||!values[1].trim())throw Error("Formato de una fila incompatible.");
   return {id:values[0],estimate:Number(values[1]),state:"No disponible",municipality:"No disponible"};
 });
 const ids=new Set(records.map(r=>r.id));
 if(records.length!==59||ids.size!==59||records.some(r=>!/^AGC_\d+$/.test(r.id)||!Number.isFinite(r.estimate)||r.estimate<=0))
   throw Error("No coinciden los 59 identificadores y sus cifras.");
 const mean=records.reduce((s,r)=>s+r.estimate,0)/59;
 if(Math.abs(mean-meanRef)>1e-7)throw Error("La media no coincide con el resultado histórico archivado.");
 return records;
}
async function attachLocations(rows){
 if(typeof DecompressionStream==="undefined")return false;
 const response=await fetch("../explorador/data/mapa_publico.json.gz",{cache:"no-store"});
 if(!response.ok||!response.body)return false;
 const payload=JSON.parse(await new Response(response.body.pipeThrough(new DecompressionStream("gzip"))).text());
 if(payload.schema!=="geocebada-map-public-1"||payload.geometry?.type!=="FeatureCollection"||
    payload.geometry.features?.length!==197)throw Error("El mapa público no coincide con el conjunto original.");
 const dict=new Map();
 const counts={Hidalgo:0,Puebla:0,Tlaxcala:0};
 for(const f of payload.geometry.features){
   const p=f.properties||{},id=String(p.ID_POLIGONO||p.ID_POLIGON||"").trim().toUpperCase();
   const state=String(p.Estado||p.estado||"").trim();
   const partition=String(p.CONJUNTO||p.conjunto||"").trim().toUpperCase();
   if(!/^AGC_\d+$/.test(id)||dict.has(id)||!Object.hasOwn(counts,state)||
      !["PREDICCION","ENTRENAMIENTO"].includes(partition))throw Error("Los metadatos públicos presentan identificadores repetidos o incompletos.");
   dict.set(id,{state,municipality:String(p.Municipio||p.municipio||"").trim(),partition});
   if(partition==="PREDICCION")counts[state]++;
 }
 if(counts.Hidalgo!==15||counts.Puebla!==29||counts.Tlaxcala!==15||rows.some(r=>dict.get(r.id)?.partition!=="PREDICCION"))throw Error("Los estados y las predicciones no corresponden al mismo universo.");
 for(const r of rows){const match=dict.get(r.id);r.state=match.state;r.municipality=match.municipality||"No disponible";}
 return true;
}
async function init(){
 const data=$("pred59-data"),status=$("pred59-status");
 if(!data||!status||!window.GeoCebadaPredictions)return;
 // No reemplazar las cifras que pudiera haber verificado el runtime exacto.
 if(!data.hidden)return;
 let all;
 try{all=await records();}
 catch(e){status.textContent="Las 59 estimaciones no se muestran: "+e.message;return;}
 let mapped=false;
 try{mapped=await attachLocations(all);}catch(e){console.warn("Metadatos de origen no verificados:",e.message);}
 const ordered=[...all].sort((a,b)=>a.estimate-b.estimate||a.id.localeCompare(b.id));
 let chosen=ordered[29].id;
 const stateList=mapped?["Hidalgo","Puebla","Tlaxcala"]:["No disponible"];
 const filter=$("pred59-state");
 filter.replaceChildren();
 const o=make("option","","Todos los estados");o.value="all";filter.append(o);
 stateList.forEach(x=>{const op=make("option","",x);op.value=x;filter.append(op)});
 const select=(id,scroll=false)=>{
  const r=all.find(x=>x.id===id);if(!r)return;chosen=id;
  document.querySelectorAll("[data-pred59-id]").forEach(b=>{const selected=b.dataset.pred59Id===id;b.classList.toggle("active",selected);b.setAttribute("aria-pressed",String(selected));});
  document.querySelectorAll("[data-pred59-row-id]").forEach(row=>row.classList.toggle("selected",row.dataset.pred59RowId===id));
  const target=$("pred59-detail");target.replaceChildren();
  const head=make("div","pred59-detail-head"),label=make("div");
  label.append(make("span","pred59-eyebrow","PARCELA DEL ESTUDIO · COSECHA AÚN DESCONOCIDA"),
               make("h4","",r.id),make("p","",mapped?r.state+" · "+r.municipality:"Estado y municipio disponibles en el explorador de Inicio"));
  const value=make("div","pred59-yield");
  value.append(make("strong","",fmt(r.estimate,4)),make("span","","t/ha estimadas"));
  head.append(label,value);
  target.append(head,make("p","pred59-detail-intro","Rendimiento estimado por Reference26 histórico con imputación por mediana. No es una cosecha medida."),
        make("p","pred59-detail-note","No está publicado aquí el desglose individual de regresión climática, Ridge local, peso geológico y corrección R3. Se omite en lugar de completar cifras inexistentes."),
        make("p","pred59-detail-note","El error de esta estimación no puede calcularse hasta conocer la cosecha real."));
  if(scroll)target.scrollIntoView({block:"nearest",behavior:"smooth"});
 };
 const button=(r,cls,txt)=>{
  const b=make("button",cls,txt);b.type="button";b.dataset.pred59Id=r.id;b.setAttribute("aria-pressed",String(r.id===chosen));b.addEventListener("click",()=>select(r.id,true));return b;
 };
 const mean=all.reduce((s,r)=>s+r.estimate,0)/all.length;
 const stats=[["Parcelas por estimar","59","Cosechas observadas desconocidas"],
 ["Media estimada",fmt(mean,4)+" t/ha","Media aritmética de los 59 valores"],
 ["Menor estimación",fmt(ordered[0].estimate,3)+" t/ha",ordered[0].id],
 ["Mayor estimación",fmt(ordered[58].estimate,3)+" t/ha",ordered[58].id]];
 $("pred59-summary").replaceChildren();
 stats.forEach(([caption,value,description])=>{
  const card=make("div","pred59-summary-item");
  card.append(make("span","",caption),make("strong","",value),make("small","",description));$("pred59-summary").append(card);
 });
 $("pred59-examples").replaceChildren();
 [["Menor estimación",ordered[0]],["Estimación mediana",ordered[29]],["Mayor estimación",ordered[58]]].forEach(([text,r])=>{
  const b=button(r,"pred59-example");
  b.append(make("span","pred59-eyebrow",text),make("strong","",fmt(r.estimate,3)+" t/ha"),
    make("span","",r.id),make("small","",mapped?r.state+" · "+r.municipality:"Sin metadatos de municipio"),
    make("span","pred59-example-link","Ver estimación →"));
  $("pred59-examples").append(b);
 });
 // Representación idéntica a Heri: tres franjas por estado, eje t/ha y puntos seleccionables.
 const plot=$("pred59-plot");plot.replaceChildren();
 const min=Math.floor(ordered[0].estimate*2)/2,max=Math.ceil(ordered[58].estimate*2)/2;
 const upper=max>min?max:min+1;
 const offset=v=>2+(v-min)/(upper-min)*96;
 for(const [index,state] of stateList.entries()){
  const band=make("div","pred59-plot-row"),label=make("span","pred59-plot-state",state),track=make("div","pred59-track");
  const samples=all.filter(r=>r.state===state).sort((a,b)=>a.estimate-b.estimate);
  samples.forEach((r,j)=>{
    const b=button(r,"pred59-dot tone-"+(index%3),"");
    b.title=r.id+" · "+fmt(r.estimate,3)+" t/ha (estimación)";
    b.setAttribute("aria-label",b.title);
    b.style.left=fmt(offset(r.estimate),4)+"%";
    b.style.top=(14+j%3*19)+"px";
    track.append(b);
  });
  band.append(label,track);plot.append(band);
 }
 const axis=make("div","pred59-axis");axis.append(make("span","pred59-plot-state",""));
 const ticks=make("div","pred59-ticks");
 for(let i=0;i<=4;i++){
  const tick=make("span","",fmt(min+(upper-min)*i/4,2));
  tick.style.left=fmt(2+i*24,2)+"%";ticks.append(tick);
 }
 axis.append(ticks);plot.append(axis);
 plot.append(make("p","pred59-axis-name","Rendimiento estimado (toneladas por hectárea). Cada punto es una parcela; no es una observación de cosecha."));
 const repaint=()=>{
  const search=$("pred59-search").value.trim().toLocaleLowerCase("es");
  const state=filter.value,sort=$("pred59-sort").value;
  const matched=all.filter(r=>(state==="all"||r.state===state)&&
    (!search||[r.id,r.state,r.municipality].some(v=>v.toLocaleLowerCase("es").includes(search))));
  matched.sort((a,b)=>sort==="value-asc"?a.estimate-b.estimate:sort==="id-asc"?a.id.localeCompare(b.id):b.estimate-a.estimate);
  $("pred59-count").textContent=matched.length+" de 59 parcelas mostradas";
  const body=$("pred59-rows");body.replaceChildren();
  if(!matched.length){
    const tr=make("tr"),td=make("td","","No hay parcelas que coincidan con la búsqueda.");td.colSpan=5;tr.append(td);body.append(tr);return;
  }
  for(const r of matched){
    const tr=make("tr");tr.dataset.pred59RowId=r.id;if(chosen===r.id)tr.classList.add("selected");
    const geo=make("td");geo.append(make("strong","",mapped?r.state:"No disponible"),make("small","",mapped?r.municipality:""));
    const val=make("td","pred59-value-cell");val.append(make("strong","",fmt(r.estimate,3)+" t/ha"));
    const support=make("td","","No publicado en el CSV");
    const action=make("td");action.append(button(r,"pred59-row-button","Ver estimación"));
    tr.append(make("td","",r.id),geo,val,support,action);body.append(tr);
  }
 };
 $("pred59-search").addEventListener("input",repaint);
 filter.addEventListener("change",repaint);
 $("pred59-sort").addEventListener("change",repaint);
 $("pred59-export").addEventListener("click",()=>{
  // Entregar el CSV original, no derivar columnas que no están verificadas.
  const a=make("a");a.href="../explorador/data/predictions.csv";a.download="reference26_59_estimaciones_originales.csv";
  document.body.append(a);a.click();a.remove();
 });
 data.hidden=false;
 status.textContent=mapped?
   "59 estimaciones de Reference26 histórico: ID, rendimiento y ubicación contrastados con los archivos públicos autorizados. Los rendimientos reales de esas parcelas siguen desconocidos.":
   "59 estimaciones de Reference26 histórico: valores e identificadores contrastados con el CSV original. El estado y municipio no se pudieron verificar en este navegador.";
 select(chosen);repaint();
}
document.addEventListener("DOMContentLoaded",()=>{
 const v=document.documentElement.dataset.researchVista;
 if(v==="resultados")init().catch(e=>{const target=$("pred59-status");if(target)target.textContent="Las 59 estimaciones no pudieron cargarse: "+e.message});
});
})();