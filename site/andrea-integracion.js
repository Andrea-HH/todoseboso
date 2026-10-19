/* Integración editorial GeoCebada: sólo lee registros y agregados ya publicados.
 * Nunca estima rendimientos, no reconstruye residuos privados.
 * Mantiene dos recetas distintas: las 59 históricas (mediana) y LOOCV (media).
 */
(function () {
'use strict';
const $=id=>document.getElementById(id);
const element=(tag,cls,txt)=>{
  const e=document.createElement(tag);
  if(cls)e.className=cls;
  if(txt!==undefined)e.textContent=String(txt);
  return e;
};
const fmt=(v,n=3)=>Number(v).toLocaleString('es-MX',{minimumFractionDigits:n,maximumFractionDigits:n});
const svgNS='http://www.w3.org/2000/svg';
const svgEl=(tag,attrs={},txt)=>{
  const s=document.createElementNS(svgNS,tag);
  Object.entries(attrs).forEach(([k,v])=>s.setAttribute(k,v));
  if(txt!==undefined)s.textContent=String(txt);
  return s;
};
const note=(target,text)=>target.append(element('p','geo-integracion-aviso',text));
const loadJson=url=>fetch(url,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('No se pudo leer '+url);return r.json()});
function plot(target,rows,config){
  target.replaceChildren();
  const w=620,h=260,L=61,R=19,T=20,B=48;
  const X=x=>L+(x-config.xmin)/(config.xmax-config.xmin)*(w-L-R);
  const Y=y=>h-B-(y-config.ymin)/(config.ymax-config.ymin)*(h-T-B);
  const svg=svgEl('svg',{viewBox:'0 0 '+w+' '+h,role:'img','aria-label':config.label});
  for(let i=0;i<=4;i++){
    let val=config.ymin+(config.ymax-config.ymin)*i/4,py=Y(val);
    svg.append(svgEl('line',{x1:L,x2:w-R,y1:py,y2:py,class:'geo-rejilla'}));
    svg.append(svgEl('text',{x:L-8,y:py+4,'text-anchor':'end'},fmt(val,config.decimals??2)));
  }
  svg.append(svgEl('line',{x1:L,x2:w-R,y1:h-B,y2:h-B,class:'geo-eje'}));
  if(config.labels){
    config.labels.forEach((name,i)=>{
      const x=X(rows[i].x);
      svg.append(svgEl('text',{x,y:h-B+23,'text-anchor':'middle'},name));
    });
  }else for(let i=0;i<=4;i++){
    const value=config.xmin+(config.xmax-config.xmin)*i/4;
    svg.append(svgEl('text',{x:X(value),y:h-B+23,'text-anchor':'middle'},fmt(value,config.xDecimals??0)));
  }
  if(config.zero!==undefined&&config.zero>=config.ymin&&config.zero<=config.ymax)
    svg.append(svgEl('line',{x1:L,y1:Y(config.zero),x2:w-R,y2:Y(config.zero),class:'geo-referencia'}));
  if(config.band){
    for(let i=0;i<rows.length;i++){
      const r=rows[i];
      if(!Number.isFinite(r.lo)||!Number.isFinite(r.hi))continue;
      svg.append(svgEl('line',{x1:X(r.x),x2:X(r.x),y1:Y(r.lo),y2:Y(r.hi),class:'geo-rango'}));
    }
  }
  const poly=rows.map(r=>X(r.x)+','+Y(r.y)).join(' ');
  svg.append(svgEl('polyline',{points:poly,class:'geo-curva'}));
  rows.forEach(r=>{
    const circle=svgEl('circle',{cx:X(r.x),cy:Y(r.y),r:4.3,class:'geo-punto'});
    circle.append(svgEl('title',{},(r.label||fmt(r.x,1))+': '+fmt(r.y,config.decimals??3)+(config.unit||'')));
    svg.append(circle);
  });
  target.append(svg);
}
function stat(label,value,context){
  const card=element('div','geo-dato');
  card.append(element('span','',label),element('strong','',value),element('small','',context));
  return card;
}
async function showObservations(){
  const rain=$('geo-lluvia-real'),ndvi=$('geo-ndvi-real');
  if(!rain&&!ndvi)return;
  try{
    const data=await loadJson('./data/real_charts.json');
    for(const [root,key,unit,dec] of [[rain,'rainfall','mm por mes',0],[ndvi,'ndvi','NDVI',2]]){
      if(!root)continue;
      const months=data[key].months;
      if(months.length!==7||months.some(m=>![m.median,m.p10,m.p90].every(Number.isFinite)))throw Error('Agregados mensuales incompletos');
      const max=Math.max(...months.map(m=>m.p90));
      const min=key==='ndvi'?0:0;
      const rows=months.map((m,i)=>({x:i,y:m.median,lo:m.p10,hi:m.p90,label:m.label}));
      plot(root,rows,{xmin:0,xmax:6,ymin:min,ymax:key==='ndvi'?0.8:Math.ceil(max/50)*50,labels:months.map(m=>m.label),band:true,decimals:dec,unit:' '+unit,label:'Mediana y rango de percentiles 10 a 90 por mes de '+key+' de 197 parcelas'});
      note(root,'Cada punto es la mediana mensual; la franja representa los percentiles 10–90. Son mediciones de 2025 entre las 197 parcelas, no predicciones ni valores simulados.');
    }
  }catch(e){[rain,ndvi].filter(Boolean).forEach(root=>note(root,'No se pudieron cargar los agregados observados: '+e.message));}
}

function showModelPreview(sorted,mean){
  const summary=$('geo-modelo-resumen'),examples=$('geo-modelo-ejemplos');
  if(!summary||!examples)return;
  summary.replaceChildren(
    stat('PARCELAS DE REFERENCIA','138','Cosechas conocidas utilizadas por el modelo'),
    stat('PARCELAS ESTIMADAS','59','No conocemos sus cosechas'),
    stat('PROMEDIO ESTIMADO',fmt(mean,3)+' t/ha','Promedio de las 59 estimaciones históricas')
  );
  examples.replaceChildren();
  for(const [label,r] of [['La menor estimación',sorted[0]],['La estimación central',sorted[29]],['La mayor estimación',sorted[58]]]){
    const card=element('article','geo-ejemplo');
    card.append(element('span','',label),element('strong','',fmt(r.value,3)+' t/ha'),element('small','',r.id+' · Predicción, no cosecha observada'));
    examples.append(card);
  }
}
async function addPublicGeography(rows){
  if(!('DecompressionStream' in window))throw Error('El navegador no admite la descompresión de la capa pública.');
  const res=await fetch('./explorador/data/mapa_publico.json.gz',{cache:'no-store'});
  if(!res.ok||!res.body)throw Error('La capa pública del mapa no se pudo consultar.');
  const doc=JSON.parse(await new Response(res.body.pipeThrough(new DecompressionStream('gzip'))).text());
  if(doc.schema!=='geocebada-map-public-1'||!Array.isArray(doc.geometry?.features)||doc.geometry.features.length!==197)
    throw Error('Los metadatos geográficos no corresponden a las 197 parcelas.');
  const byId=new Map();
  const counts={Hidalgo:0,Puebla:0,Tlaxcala:0};
  for(const feature of doc.geometry.features){
    const p=feature.properties||{},id=String(p.ID_POLIGONO||p.ID_POLIGON||'').trim().toUpperCase();
    const state=String(p.Estado||p.estado||'').trim();
    const split=String(p.CONJUNTO||p.conjunto||'').trim().toUpperCase();
    if(!/^AGC_\d+$/.test(id)||byId.has(id)||!Object.hasOwn(counts,state)||!['PREDICCION','ENTRENAMIENTO'].includes(split))
      throw Error('La capa contiene identificadores, estados o conjuntos inconsistentes.');
    const municipality=String(p.Municipio||p.municipio||'').trim();
    byId.set(id,{state,municipality,split});
    if(split==='PREDICCION')counts[state]++;
  }
  if(byId.size!==197||counts.Hidalgo!==15||counts.Puebla!==29||counts.Tlaxcala!==15)
    throw Error('La distribución geográfica no coincide con los resultados archivados.');
  if(rows.some(r=>byId.get(r.id)?.split!=='PREDICCION'))throw Error('Las 59 parcelas no coinciden con la capa pública.');
  for(const row of rows){
    const loc=byId.get(row.id);row.state=loc.state;row.municipality=loc.municipality||'No disponible';
  }
}
async function showPredictions(){
  const summary=$('geo-59-resumen'),chart=$('geo-59-grafica'),table=$('geo-59-tabla'),examples=$('geo-59-ejemplos');
  const search=$('geo-59-buscar'),order=$('geo-59-orden'),stateFilter=$('geo-59-estado'),detail=$('geo-59-detalle');
  if(!summary||!chart||!table)return;
  try{
    const response=await fetch('./explorador/data/predictions.csv',{cache:'no-store'});
    if(!response.ok)throw Error('CSV no disponible');
    const lines=(await response.text()).trim().split(/\r?\n/).map(x=>x.trim());
    if(lines[0]!=='ID_POLIGONO,RENDIMIENTO_T_HA')throw Error('Encabezado distinto del archivo autorizado');
    const data=lines.slice(1).filter(Boolean).map(line=>{
      const parts=line.split(',');
      if(parts.length!==2||!parts[1].trim())throw Error('Fila del CSV con formato incorrecto');
      return {id:parts[0],value:Number(parts[1]),state:null,municipality:null};
    });
    const ids=new Set(data.map(d=>d.id));
    if(data.length!==59||ids.size!==59||data.some(d=>!/^AGC_\d+$/.test(d.id)||!Number.isFinite(d.value)||d.value<=0))
      throw Error('La lista de 59 ID y rendimientos no supera la validación');
    const mean=data.reduce((sum,d)=>sum+d.value,0)/data.length;
    if(Math.abs(mean-3.956432328667021)>1e-7)throw Error('La media no coincide con el expediente archivado');
    const sorted=[...data].sort((a,b)=>a.value-b.value);
    summary.replaceChildren();
    summary.append(
      stat('PARCELAS ESTIMADAS','59','Sin cosechas observadas para estas parcelas'),
      stat('PROMEDIO',fmt(mean,3)+' t/ha','Media aritmética de las estimaciones'),
      stat('MÍNIMO',fmt(sorted[0].value,3)+' t/ha',sorted[0].id),
      stat('MÁXIMO',fmt(sorted[58].value,3)+' t/ha',sorted[58].id)
    );
    showModelPreview(sorted,mean);
    examples.replaceChildren();
    [['Menor',sorted[0]],['Mediana',sorted[29]],['Mayor',sorted[58]]].forEach(([title,row])=>{
      const c=element('div','geo-ejemplo');
      c.append(element('span','',title+' estimación'),element('strong','',fmt(row.value,3)+' t/ha'),element('small','',row.id));
      examples.append(c);
    });
    let selectedId=sorted[29].id;
    function choose(id,focus=false){
      const row=data.find(x=>x.id===id);if(!row)return;
      selectedId=id;
      detail.replaceChildren();
      detail.append(element('span','geo-59-etiqueta','PARCELA DEL ESTUDIO · COSECHA AÚN DESCONOCIDA'));
      detail.append(element('h3','',row.id+' · '+fmt(row.value,4)+' t/ha estimadas'));
      detail.append(element('p','',row.state?row.state+' · '+row.municipality:'Información geográfica en el mapa de Inicio'));
      detail.append(element('p','', 'Esta cifra procede de Reference26 histórico y no representa una cosecha comprobada. Las contribuciones individuales de clima, vecinos, geología y corrección no están publicadas en el CSV de 59 estimaciones.'));
      const link=element('a','source-link','Consultar las parcelas en el mapa ↗');
      link.href='./index.html#mapa-interactivo';detail.append(link);
      table.querySelectorAll('tbody tr').forEach(tr=>tr.classList.toggle('geo-seleccionada',tr.dataset.parcelId===id));
      chart.querySelectorAll('circle[data-parcel-id]').forEach(c=>c.classList.toggle('geo-seleccionada',c.dataset.parcelId===id));
      if(focus)detail.scrollIntoView({block:'nearest',behavior:'smooth'});
    }
    function paintChart(){
      chart.replaceChildren();
      const allStates=data.every(d=>d.state);
      const svg=svgEl('svg',{viewBox:'0 0 660 260',role:'img','aria-label':'Diagrama de dispersión de los 59 rendimientos estimados en t/ha'+(allStates?', agrupados por estado':'')});
      const low=Math.floor(sorted[0].value*2)/2, high=Math.ceil(sorted[58].value*2)/2;
      const L=92,R=24,W=660, X=v=>L+(v-low)/(high-low)*(W-L-R);
      const baseline=218, states=['Hidalgo','Puebla','Tlaxcala'];
      for(let i=0;i<=5;i++){
        const x=L+(W-L-R)*i/5;
        svg.append(svgEl('line',{x1:x,y1:20,x2:x,y2:baseline,class:'geo-rejilla'}));
        svg.append(svgEl('text',{x,y:245,'text-anchor':'middle'},fmt(low+(high-low)*i/5,2)));
      }
      if(allStates){
        const ys={Hidalgo:45,Puebla:116,Tlaxcala:187};
        for(const state of states)svg.append(svgEl('text',{x:8,y:ys[state]+3},state));
        data.forEach((row,i)=>{
          // La dispersión vertical mínima sólo evita superposición de los puntos.
          const offset=((Number(row.id.slice(4))%7)-3)*3.4;
          const circle=svgEl('circle',{cx:X(row.value),cy:ys[row.state]+offset,r:5,class:'geo-punto geo-pred-'+row.state.toLowerCase(),tabindex:'0',role:'button','aria-label':row.id+', '+fmt(row.value,4)+' toneladas por hectárea estimadas', 'data-parcel-id':row.id});
          circle.append(svgEl('title',{},row.id+' · '+row.state+' · '+fmt(row.value,4)+' t/ha'));
          circle.addEventListener('click',()=>choose(row.id,true));
          circle.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(row.id,true)}});
          svg.append(circle);
        });
      }else sorted.forEach((row,i)=>{
        const y=24+(i%11)*16;
        const circle=svgEl('circle',{cx:X(row.value),cy:y,r:4.7,class:'geo-punto',tabindex:'0',role:'button','aria-label':row.id+', '+fmt(row.value,4)+' toneladas por hectárea estimadas','data-parcel-id':row.id});
        circle.append(svgEl('title',{},row.id+' · '+fmt(row.value,4)+' t/ha'));
        circle.addEventListener('click',()=>choose(row.id,true));
        circle.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(row.id,true)}});
        svg.append(circle);
      });
      chart.append(svg);
      note(chart,allStates?'Las filas agrupan parcelas por estado y cada círculo es una predicción seleccionable. La variación vertical pequeña sólo evita superposiciones: no mide rendimiento ni incertidumbre.':'Un círculo por parcela. La altura es únicamente una separación visual; no representa una segunda variable.');
      chart.querySelectorAll('circle[data-parcel-id]').forEach(c=>c.classList.toggle('geo-seleccionada',c.dataset.parcelId===selectedId));
    }
    const tbody=table.querySelector('tbody');
    const repaint=()=>{
      const query=(search?.value||'').trim().toLocaleLowerCase('es');
      const state=stateFilter?.value||'all',how=order?.value||'id';
      const visible=data.filter(d=>(d.id.toLocaleLowerCase('es').includes(query)||d.municipality?.toLocaleLowerCase('es').includes(query)||d.state?.toLocaleLowerCase('es').includes(query))&&(state==='all'||d.state===state))
        .sort((a,b)=>how==='asc'?a.value-b.value:how==='desc'?b.value-a.value:a.id.localeCompare(b.id));
      tbody.replaceChildren();
      visible.forEach(row=>{
        const tr=element('tr');tr.dataset.parcelId=row.id;tr.classList.toggle('geo-seleccionada',row.id===selectedId);
        const action=element('button','geo-ver-pred','Ver detalle');action.type='button';
        action.addEventListener('click',()=>choose(row.id,true));
        const cell=element('td');cell.append(action);
        tr.append(element('td','',row.id),element('td','',row.state?row.state+' · '+row.municipality:'Consultar en mapa'),
          element('td','',fmt(row.value,4)),cell);
        tbody.append(tr);
      });
      if(!visible.length){const tr=element('tr'),td=element('td','','No se encontraron parcelas con esos filtros.');td.colSpan=4;tr.append(td);tbody.append(tr)}
      const count=$('geo-59-cuenta');if(count)count.textContent='Se muestran '+visible.length+' de 59 parcelas.';
    };
    search?.addEventListener('input',repaint);
    stateFilter?.addEventListener('change',repaint);
    order?.addEventListener('change',repaint);
    paintChart();repaint();choose(selectedId);
    try{
      await addPublicGeography(data);
      stateFilter?.replaceChildren();
      for(const name of ['Todos los estados','Hidalgo','Puebla','Tlaxcala']){
        const option=element('option','',name);option.value=name==='Todos los estados'?'all':name;
        stateFilter?.append(option);
      }
      paintChart();repaint();choose(selectedId);
    }catch(error){
      if(stateFilter){stateFilter.disabled=true;stateFilter.title='No se pudieron validar los metadatos de estados';}
      note(chart,'El filtro geográfico no se activó: '+error.message+' Las 59 cifras del CSV siguen disponibles por ID.');
    }
  }catch(e){
    note(summary,'No se pudo mostrar la tabla de 59 estimaciones verificadas: '+e.message);
    const model=$('geo-modelo-resumen');if(model)note(model,'Las estimaciones no se pudieron comprobar: '+e.message);
  }
}
function drawMoran(target,arr,metric,title){
  const rows=arr.map(r=>({x:r.k,y:r[metric],label:'k='+r.k}));
  const values=rows.map(r=>r.y).concat(metric==='C'?[1]:[0]);
  const min=Math.min(...values),max=Math.max(...values),span=Math.max(.06,max-min);
  plot(target,rows,{xmin:4,xmax:24,ymin:min-span*.25,ymax:max+span*.25,zero:metric==='C'?1:0,xDecimals:0,decimals:3,label:title});
}

function detailTable(parent,title,headers,records){
 const d=element('details');d.append(element('summary','',title));
 const wrap=element('div','geo-tabla-wrap'),t=element('table'),thead=element('thead'),tr=element('tr');
 headers.forEach(header=>tr.append(element('th','',header)));
 thead.append(tr);t.append(thead);
 const body=element('tbody');
 records.forEach(row=>{const r=element('tr');row.forEach(value=>r.append(element('td','',value)));body.append(r)});
 t.append(body);wrap.append(t);d.append(wrap);parent.append(d);
}
async function showResiduals(){
 const main=$('geo-residuos-datos'),tabs=$('geo-residuos-pestanas'),panels=$('geo-residuos-paneles');
 if(!main||!tabs||!panels)return;
 try{
  const data=await loadJson('./data/reference26_residuals.json');
  if(data.model!=='Reference26_mean'||data.n_labeled!==138)throw Error('El diagnóstico no corresponde a la evaluación prevista');
  const m=data.metrics;
  main.replaceChildren(stat('RMSE',fmt(m.rmse_t_ha,4)+' t/ha','138 predicciones LOOCV'),
                     stat('MAE',fmt(m.mae_t_ha,4)+' t/ha','Error absoluto medio'),
                     stat('R²',fmt(m.r2_cv,4),'Evaluación dejando una parcela fuera'),
                     stat('SESGO',fmt(m.bias_t_ha,4)+' t/ha','Media de errores con signo'));
  const views=[
    ['magnitud','Tamaño del error'],
    ['influencia','Casos influyentes'],
    ['pruebas','Pruebas estadísticas'],
    ['moran','Moran I'],
    ['geary','Geary C'],
    ['semivariograma','Distancia'],
    ['bootstrap','Robustez territorial']
  ];
  tabs.replaceChildren();panels.replaceChildren();
  const show=id=>{
    tabs.querySelectorAll('button').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===id)));
    panels.querySelectorAll('[data-panel]').forEach(p=>p.hidden=p.dataset.panel!==id);
  };
  const addView=(id,name,render)=>{
    const b=element('button','',name);b.type='button';b.dataset.tab=id;b.setAttribute('aria-selected','false');b.addEventListener('click',()=>show(id));tabs.append(b);
    const panel=element('div');panel.dataset.panel=id;panel.hidden=true;
    const card=element('div','geo-grafica');panel.append(card);panels.append(panel);render(card,panel);
  };
  addView('magnitud','Tamaño del error',(box)=>{
    box.append(element('h3','','¿Qué tan grandes son las equivocaciones?'));
    const grid=element('div','geo-datos-clave');
    grid.append(stat('ERROR ABSOLUTO MEDIANO',fmt(m.median_absolute_error_t_ha,3)+' t/ha','La mitad de los errores absolutos es menor'),
      stat('PERCENTIL 95',fmt(m.p95_absolute_error_t_ha,3)+' t/ha','Percentil 95 de los errores absolutos'),
      stat('MÁXIMO',fmt(m.max_absolute_error_t_ha,3)+' t/ha','Mayor error absoluto observado'),
      stat('WAPE',fmt(m.wape_pct,2)+' %','Error absoluto como proporción de cosechas totales'));
    box.append(grid);
    note(box,'Resumen calculado en las 138 exclusiones LOOCV. No equivale a un margen de error garantizado para las 59 predicciones.');
  });
  addView('influencia','Casos influyentes',(box)=>{
    const i=data.influence;
    box.append(element('h3','','¿Unas pocas parcelas dominan el error?'));
    for(const [label,number] of [['RMSE completo',i.full_rmse_t_ha],['Sin el error más grande',i.rmse_without_largest_t_ha],['Sin los dos errores mayores',i.rmse_without_largest_two_t_ha]]){
      const line=element('p');line.textContent=label+': '+fmt(number,4)+' t/ha';box.append(line);
      const track=element('div','geo-tech-track');const fill=element('span','geo-tech-fill');fill.style.width=100*number/i.full_rmse_t_ha+'%';track.append(fill);box.append(track);
    }
    note(box,'El mayor error acumula '+fmt(100*i.share_sse_largest,2)+' % de los errores cuadrados; los dos mayores, '+fmt(100*i.share_sse_largest_two,2)+' %. Estos escenarios eliminan errores guardados: NO se reentrena el modelo.');
  });
  addView('pruebas','Pruebas estadísticas',(box)=>{
    const n=data.diagnostics.normality,v=data.diagnostics.variance;
    box.append(element('h3','','¿Se comportan los errores como una distribución normal?'));
    const grid=element('div','geo-datos-clave');
    grid.append(stat('SHAPIRO W',fmt(n.shapiro_w,4),'p = '+n.shapiro_p.toExponential(2)),
      stat('D’AGOSTINO', 'p = '+vfmt(n.dagostino_p),'Contraste de normalidad'),
      stat('KOENKER–BP','p = '+fmt(v.koenker_bp_p,4),'Prueba de dispersión variable'),
      stat('BROWN–FORSYTHE','p = '+fmt(v.brown_forsythe_p,4),'Prueba de dispersión por grupos'));
    box.append(grid);
    note(box,'La prueba Anderson–Darling también rechaza normalidad al 5 %. Los contrastes de normalidad rechazan la hipótesis de normalidad. No rechazar las pruebas de heterocedasticidad no demuestra varianza constante. Los valores p son exploratorios porque las particiones LOOCV comparten entrenamientos.');
  });
  addView('moran','Moran I',(box)=>{
    box.append(element('h3','','¿Los errores parecidos están cerca?'));
    const target=element('div');box.append(target);
    drawMoran(target,data.spatial.signed_residual_moran,'I','Moran I de los errores con signo para vecinos k = 4, 8, 12 y 24');
    note(box,'Referencia: I = 0. Los valores p ajustados por Holm de esta serie son '+data.spatial.signed_residual_moran.map(x=>fmt(x.p_holm_all,3)).join(' / ')+'. La falta de significación no prueba independencia espacial.');
    const all=[
      ['Error con signo',data.spatial.signed_residual_moran],
      ['Error absoluto',data.spatial.absolute_error_moran],
      ['Error al cuadrado',data.spatial.squared_error_moran]
    ];
    detailTable(box,'Ver los 12 resultados de Moran y sus valores p',
      ['Medida','Vecinos k','I','p (dos colas)','p Holm','p FDR–BH'],
      all.flatMap(([name,rows])=>rows.map(r=>[name,r.k,fmt(r.I,5),fmt(r.p_two_sided,4),fmt(r.p_holm_all,4),fmt(r.p_fdr_bh_all,4)])));
  });
  addView('geary','Geary C',(box)=>{
    box.append(element('h3','','¿Hay similitud espacial de los residuos?'));
    const target=element('div');box.append(target);
    drawMoran(target,data.spatial.geary_c.filter(x=>x.spatial_variable==='signed_residual'),'C','Geary C de los errores con signo para vecinos k = 4, 8, 12 y 24');
    note(box,'Referencia aproximada: C = 1. Se trata de una prueba espacial exploratoria sobre las exclusiones LOOCV.');
    const names={signed_residual:'Error con signo',absolute_error:'Error absoluto',squared_error:'Error al cuadrado'};
    detailTable(box,'Ver los 12 resultados de Geary y sus valores p',
      ['Medida','Vecinos k','C','p (dos colas)','p Holm','p FDR–BH'],
      data.spatial.geary_c.map(r=>[names[r.spatial_variable]||r.spatial_variable,r.k,fmt(r.C,5),fmt(r.p_two_sided,4),fmt(r.p_holm_all,4),fmt(r.p_fdr_bh_all,4)]));
  });
  addView('semivariograma','Distancia',(box)=>{
    box.append(element('h3','','¿Cómo cambia la diferencia de errores con la distancia?'));
    const target=element('div');box.append(target);
    const rows=data.spatial.semivariogram.map(x=>({x:x.distance_km,y:x.semivariance_t2_ha2,label:fmt(x.distance_km,1)+' km, '+x.pairs+' pares'}));
    plot(target,rows,{xmin:0,xmax:Math.ceil(Math.max(...rows.map(x=>x.x))/10)*10,ymin:0,ymax:.38,xDecimals:0,decimals:3,label:'Semivariograma empírico de 138 residuos LOOCV'});
    note(box,'Cada punto representa pares de parcelas agrupados por distancia. Es un diagnóstico descriptivo, no un semivariograma teórico ajustado. Unidad vertical: (t/ha)².');
    detailTable(box,'Ver distancias, pares y semivarianzas de los 6 intervalos',
      ['Intervalo','Pares','Distancia media (km)','Mín. (km)','Máx. (km)','Semivarianza (t/ha)²'],
      data.spatial.semivariogram.map(r=>[r.bin,r.pairs,fmt(r.distance_km,3),fmt(r.distance_min_km,3),fmt(r.distance_max_km,3),fmt(r.semivariance_t2_ha2,5)]));
  });
  addView('bootstrap','Robustez territorial',(box)=>{
    box.append(element('h3','','¿Cuánto cambia el RMSE al remuestrear zonas?'));
    const computed=data.spatial_bootstrap.groups.filter(g=>g.status==='computed');
    computed.forEach(g=>{
      const r=g.rmse_t_ha,row=element('div','geo-banda');
      const name=g.id==='municipality'?'Municipios':'Bloques de 15 km desplazados';
      row.append(element('strong','',name+' ('+g.n_groups+' grupos)'));
      const track=element('div','geo-banda-track');
      const band=element('div','geo-banda-rango');band.style.setProperty('--desde',String(r.low/0.7*100)+'%');band.style.setProperty('--hasta',String((r.high-r.low)/0.7*100)+'%');
      const val=element('div','geo-banda-valor');val.style.setProperty('--valor',String(r.point/0.7*100)+'%');
      track.append(band,val);row.append(track,element('span','',fmt(r.low,3)+' – '+fmt(r.high,3)));box.append(row);
    });
    note(box,fmt(data.spatial_bootstrap.replicates,0)+' réplicas archivadas. Rango exploratorio de percentiles 2.5–97.5, no cobertura calibrada. Las cuadrículas con menos de 8 grupos no se calcularon.');
    detailTable(box,'Ver todas las configuraciones, incluidas las no calculadas',
      ['Configuración','Grupos','Estado','Límite inferior','Límite superior'],
      data.spatial_bootstrap.groups.map(g=>[
        g.id==='municipality'?'Municipios':g.label,
        g.n_groups,
        g.status==='computed'?'Calculado':'No calculado: menos de 8 grupos',
        g.rmse_t_ha?fmt(g.rmse_t_ha.low,5):'—',
        g.rmse_t_ha?fmt(g.rmse_t_ha.high,5):'—'
      ]));
  });
  const detail=element('details');const summary=element('summary','','Ver valores y procedencia del diagnóstico');
  detail.append(summary);
  const pre=element('p','','Modelo Reference26 con imputación por media durante cada entrenamiento. Las 138 etiquetas se excluyeron una a una; las 59 predicciones históricas usan mediana y no deben interpretarse como resultados de este LOOCV.');
  detail.append(pre);
  const link=element('a','', 'Abrir resultados técnicos documentados ↗');
  link.href=data.sources.interpretation;link.target='_blank';link.rel='noopener noreferrer';detail.append(link);
  panels.after(detail);
  show('magnitud');
 }catch(e){note(main,'No se pudieron cargar los diagnósticos archivados: '+e.message);}
}
function vfmt(v){return v<0.0001?Number(v).toExponential(2):fmt(v,4)}
document.addEventListener('DOMContentLoaded',()=>{showObservations();showPredictions();showResiduals()});
})();
