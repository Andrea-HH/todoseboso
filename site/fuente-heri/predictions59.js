/* The 59 study-parcel predictions are not invented examples.
   This gallery is populated only AFTER the exact Reference26 JS runtime has
   passed its independent 59/59 Python numerical parity audit.
   All entries have unknown observed yield.
*/
"use strict";
(() => {
  const $ = (q) => document.querySelector(q);
  const make = (tag, className, value) => {
    const e = document.createElement(tag);
    if (className) e.className = className;
    if (value !== undefined) e.textContent = String(value);
    return e;
  };
  const f = (value, digits = 3) => Number(value).toFixed(digits);
  let all = [];
  let chosen = null;
  let geography = [];
  const root = $("#pred59-data");
  const status = $("#pred59-status");

  function prepare(runtime) {
    if (runtime?.model !== "Reference26" || runtime.existing_59?.length !== 59)
      throw Error("Las 59 parcelas deben provenir de Reference26 entrenado.");
    const ids = new Set();
    const data = runtime.existing_59.map((entry) => {
      if (typeof entry.id !== "string" || !entry.id.trim() || ids.has(entry.id))
        throw Error("Identificador de parcela ausente o repetido.");
      ids.add(entry.id);
      if (typeof entry.state !== "string" || !entry.state.trim() ||
          typeof entry.municipality !== "string" || !entry.municipality.trim())
        throw Error("Faltan las entidades geográficas originales.");
      const prediction = window.Reference26Browser.run(runtime,entry.x,entry.distances);
      if (!Number.isFinite(entry.expected) ||
          Math.abs(prediction.predicted_t_ha-entry.expected) > 1e-7)
        throw Error("Una predicción difiere del resultado original de Python.");
      return {
        id:entry.id, state:entry.state, municipality:entry.municipality,
        estimate:prediction.predicted_t_ha,
        r3:prediction.has_r3_support,
        climate:prediction.climate, expert:prediction.expert,
        localWeight:prediction.local_weight, geoGroup:prediction.geology_group,
        residual:prediction.residual_adjustment, x:entry.x
      };
    });
    const ordered=[...data].sort((a,b)=>a.estimate-b.estimate || a.id.localeCompare(b.id));
    const mean=data.reduce((sum,x)=>sum+x.estimate,0)/59;
    if (!Number.isFinite(runtime.aggregate_parity?.mean) ||
        Math.abs(mean-runtime.aggregate_parity.mean)>1e-7)
      throw Error("La media de las 59 estimaciones no coincide con el resultado original.");
    return data;
  }

  function createSummary() {
    const ordered=[...all].sort((a,b)=>a.estimate-b.estimate || a.id.localeCompare(b.id));
    const mean=all.reduce((acc,x)=>acc+x.estimate,0)/all.length;
    const info=[
      ["Parcelas por estimar","59","Sin rendimientos observados"],
      ["Media estimada",f(mean,4)+" t/ha","Media aritmética de las 59"],
      ["Menor estimación",f(ordered[0].estimate,3)+" t/ha","No implica una cosecha real baja"],
      ["Mayor estimación",f(ordered.at(-1).estimate,3)+" t/ha","No implica una cosecha real alta"]
    ];
    const holder=$("#pred59-summary");
    holder.replaceChildren();
    for(const [caption,value,desc] of info){
      const item=make("div","pred59-summary-item");
      item.append(make("span","",caption),make("strong","",value),make("small","",desc));
      holder.append(item);
    }
  }

  function select(id,scroll=false){
    const row=all.find(x=>x.id===id);
    if(!row)return;
    chosen=id;
    document.querySelectorAll("[data-pred59-id]").forEach(button=>{
      const selected=button.dataset.pred59Id===chosen;
      button.classList.toggle("active",selected);
      button.setAttribute("aria-pressed",String(selected));
    });
    document.querySelectorAll("[data-pred59-row-id]").forEach(tableRow=>{
      tableRow.classList.toggle("selected",tableRow.dataset.pred59RowId===chosen);
    });
    const detail=$("#pred59-detail");
    detail.replaceChildren();
    const head=make("div","pred59-detail-head");
    const label=make("div");
    label.append(make("span","pred59-eyebrow","PARCELA DEL ESTUDIO · COSECHA AÚN DESCONOCIDA"),
      make("h4","",row.id),make("p","",row.state+" · "+row.municipality));
    const yieldBox=make("div","pred59-yield");
    yieldBox.append(make("strong","",f(row.estimate,4)),make("span","","t/ha estimadas"));
    head.append(label,yieldBox);
    const explanation=make("p","pred59-detail-intro",
      "Este valor es una estimación de Reference26, no un dato de cosecha. Se obtuvo con los "+
      "138 rendimientos conocidos y las variables disponibles para esta parcela.");
    const grid=make("div","pred59-parts");
    for(const [labelText,value] of [
      ["Regresión climática",f(row.climate,3)+" t/ha"],
      ["Experto local",f(row.expert,3)+" t/ha"],
      ["Peso del componente local",f(row.localWeight*100,1)+" %"],
      ["Grupo geológico",String(row.geoGroup)],
      ["Ajuste residual",f(row.residual,3)+" t/ha"],
      ["Soporte del corrector",row.r3?"Completo":"Incompleto: se desactivó"]
    ]){
      const item=make("div","");item.append(make("span","",labelText),make("strong","",value));grid.append(item);
    }
    const note=make("p","pred59-detail-note",
      "La diferencia entre esta estimación y el rendimiento real no puede calcularse hasta conocer la cosecha de esta parcela.");
    detail.append(head,explanation,grid,note);
    if(scroll) detail.scrollIntoView({block:"nearest",behavior:"smooth"});
  }

  function viewButton(item,label,className){
    const button=make("button",className,label);
    button.type="button";
    button.dataset.pred59Id=item.id;
    button.setAttribute("aria-pressed",String(chosen===item.id));
    button.addEventListener("click",()=>select(item.id,true));
    return button;
  }

  function examples(){
    const ordered=[...all].sort((a,b)=>a.estimate-b.estimate || a.id.localeCompare(b.id));
    const picks=[
      ["Menor estimación",ordered[0]],
      ["Estimación mediana",ordered[29]],
      ["Mayor estimación",ordered[58]]
    ];
    const holder=$("#pred59-examples");holder.replaceChildren();
    for(const [title,item] of picks){
      const button=viewButton(item,undefined,"pred59-example");
      button.append(make("span","pred59-eyebrow",title),
        make("strong","",f(item.estimate,3)+" t/ha"),
        make("span","",item.id),
        make("small","",item.state+" · "+item.municipality),
        make("span","pred59-example-link","Ver cómo se obtuvo →"));
      holder.append(button);
    }
  }

  function chart(){
    const holder=$("#pred59-plot");holder.replaceChildren();
    const ordered=[...all].sort((a,b)=>a.estimate-b.estimate);
    const min=Math.floor(ordered[0].estimate*2)/2;
    const max=Math.ceil(ordered[ordered.length-1].estimate*2)/2;
    const upper=max>min?max:min+1;
    const offset=value=>2+(value-min)/(upper-min)*96;
    geography=[...new Set(all.map(x=>x.state))].sort((a,b)=>a.localeCompare(b,"es"));
    for(const [index,state] of geography.entries()){
      const parent=make("div","pred59-plot-row");
      const label=make("span","pred59-plot-state",state);
      const track=make("div","pred59-track");
      const samples=all.filter(x=>x.state===state).sort((a,b)=>a.estimate-b.estimate);
      samples.forEach((item,j)=>{
        const button=viewButton(item,"","pred59-dot tone-"+index%3);
        button.title=item.id+" · "+f(item.estimate,3)+" t/ha (estimación)";
        button.setAttribute("aria-label",button.title);
        button.style.left=f(offset(item.estimate),4)+"%";
        button.style.top=(14+(j%3)*19)+"px";
        track.append(button);
      });
      parent.append(label,track);
      holder.append(parent);
    }
    const axis=make("div","pred59-axis");
    axis.append(make("span","pred59-plot-state",""));
    const ticks=make("div","pred59-ticks");
    for(let i=0;i<=4;i++){
      const tick=make("span","",f(min+(upper-min)*i/4,2));
      tick.style.left=f(2+96*i/4,2)+"%";ticks.append(tick);
    }
    axis.append(ticks);holder.append(axis);
    holder.append(make("p","pred59-axis-name","Rendimiento estimado (toneladas por hectárea). Cada punto es una parcela, no una observación de cosecha."));
  }

  function rows(){
    const search=$("#pred59-search").value.trim().toLocaleLowerCase("es");
    const state=$("#pred59-state").value;
    const sort=$("#pred59-sort").value;
    const matched=all.filter(x=>
      (state==="all"||x.state===state) &&
      (!search||[x.id,x.municipality,x.state].some(t=>t.toLocaleLowerCase("es").includes(search)))
    );
    if(sort==="value-asc")matched.sort((a,b)=>a.estimate-b.estimate || a.id.localeCompare(b.id));
    else if(sort==="id-asc")matched.sort((a,b)=>a.id.localeCompare(b.id));
    else matched.sort((a,b)=>b.estimate-a.estimate || a.id.localeCompare(b.id));
    $("#pred59-count").textContent=matched.length+" de 59 parcelas mostradas";
    const body=$("#pred59-rows");body.replaceChildren();
    if(!matched.length){
      const tr=make("tr"),td=make("td","","No hay parcelas que coincidan con la búsqueda.");
      td.colSpan=5;tr.append(td);body.append(tr);return;
    }
    const values=all.map(x=>x.estimate),min=Math.min(...values),max=Math.max(...values);
    for(const item of matched){
      const tr=make("tr","");
      tr.dataset.pred59RowId=item.id;
      if(item.id===chosen)tr.classList.add("selected");
      const id=make("td","",item.id);
      const loc=make("td","");
      loc.append(make("strong","",item.state),make("small","",item.municipality));
      const metric=make("td","pred59-value-cell");
      const bar=make("span","pred59-meter");
      const fill=make("span");
      fill.style.width=f(12+88*(item.estimate-min)/(max-min||1),1)+"%";
      bar.append(fill);
      metric.append(make("strong","",f(item.estimate,3)+" t/ha"),bar);
      const support=make("td","",item.r3?"Aplicada":"No aplicada");
      const buttonCell=make("td");
      buttonCell.append(viewButton(item,"Ver detalle","pred59-row-button"));
      tr.append(id,loc,metric,support,buttonCell);body.append(tr);
    }
  }

  function exportCsv(){
    if(all.length!==59)return;
    const header=["ID_POLIGONO","Estado","Municipio","Reference26_estimado_t_ha","Correccion_R3"];
    const rows=all.map(x=>[x.id,x.state,x.municipality,f(x.estimate,6),x.r3?"aplicada":"no_aplicada"]);
    const safe=x=>{
      let value=String(x).replace(/[\r\n]+/g," ");
      if(/^[=+\-@\t]/.test(value))value="'"+value;
      return '"'+value.replace(/"/g,'""')+'"';
    };
    const csv="\uFEFF"+[header,...rows].map(row=>row.map(safe).join(",")).join("\r\n")+"\r\n";
    const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
    const anchor=make("a");
    anchor.href=url;anchor.download="reference26_59_estimaciones_no_observadas.csv";
    document.body.append(anchor);anchor.click();anchor.remove();URL.revokeObjectURL(url);
  }
  function render(runtime){
    // The caller has already verified 59/59 Python-JS parity. Recompute every
    // displayed value with the native JS engine, checking each again.
    const rows59=prepare(runtime);
    all=rows59;
    root.hidden=false;
    status.textContent="59 estimaciones individuales verificadas · Reference26 entrenado con 138 rendimientos. Las 59 cosechas reales siguen siendo desconocidas.";
    createSummary();examples();chart();
    const states=[...new Set(all.map(x=>x.state))].sort((a,b)=>a.localeCompare(b,"es"));
    const filter=$("#pred59-state");filter.replaceChildren();
    const first=make("option","","Todos los estados");first.value="all";filter.append(first);
    for(const state of states){const option=make("option","",state);option.value=state;filter.append(option);}
    $("#pred59-search").value="";
    $("#pred59-sort").value="value-desc";
    rows();
    selectedInitial();
  }
  function selectedInitial(){
    const sorted=[...all].sort((a,b)=>a.estimate-b.estimate);
    // Middle observed *prediction*, not median of known yields.
    select(sorted[29].id,false);
    rows();
  }
  function unavailable(message){
    all=[];chosen=null;root.hidden=true;
    status.textContent="Las 59 predicciones no están disponibles: "+message+
      " No se mostrarán cifras sin comprobar primero la coincidencia con Python.";
  }
  for(const name of ["pred59-search","pred59-state","pred59-sort"]){
    $("#"+name).addEventListener(name==="pred59-search"?"input":"change",rows);
  }
  $("#pred59-export").addEventListener("click",exportCsv);
  window.GeoCebadaPredictions=Object.freeze({prepare,render,unavailable});
})();