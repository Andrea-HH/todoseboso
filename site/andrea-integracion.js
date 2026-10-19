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
async function showPredictions(){
  const summary=$('geo-59-resumen'),chart=$('geo-59-grafica'),table=$('geo-59-tabla'),examples=$('geo-59-ejemplos'),search=$('geo-59-buscar'),order=$('geo-59-orden');
  if(!summary||!chart||!table)return;
  try{
    const response=await fetch('./explorador/data/predictions.csv',{cache:'no-store'});
    if(!response.ok)throw Error('CSV no disponible');
    const lines=(await response.text()).trim().split(/\r?\n/).map(x=>x.trim());
    if(lines[0]!=='ID_POLIGONO,RENDIMIENTO_T_HA')throw Error('Encabezado distinto del archivo autorizado');
    const data=lines.slice(1).filter(Boolean).map(line=>{
      const parts=line.split(',');
      return {id:parts[0],value:Number(parts[1])};
    });
    const ids=new Set(data.map(d=>d.id));
    if(data.length!==59||ids.size!==59||data.some(d=>!/^AGC_\d+$/.test(d.id)||!Number.isFinite(d.value)))throw Error('La lista de 59 ID y rendimientos no supera la validación');
    const mean=data.reduce((s,d)=>s+d.value,0)/data.length;
    if(Math.abs(mean-3.956432328667021)>1e-7)throw Error('La media no coincide con el expediente archivado');
    const sorted=[...data].sort((a,b)=>a.value-b.value);
    summary.replaceChildren();
    summary.append(
      stat('PARCELAS ESTIMADAS','59','Sin cosechas observadas para estas parcelas'),
      stat('PROMEDIO',fmt(mean,3)+' t/ha','Media aritmética de las estimaciones'),
      stat('MÍNIMO',fmt(sorted[0].value,3)+' t/ha',sorted[0].id),
      stat('MÁXIMO',fmt(sorted[58].value,3)+' t/ha',sorted[58].id)
    );
    examples.replaceChildren();
    [['Menor',sorted[0]],['Mediana',sorted[29]],['Mayor',sorted[58]]].forEach(([title,row])=>{
      const c=element('div','geo-ejemplo');
      c.append(element('span','',title+' estimación'),element('strong','',fmt(row.value,3)+' t/ha'),element('small','',row.id));
      examples.append(c);
    });
    const svg=svgEl('svg',{viewBox:'0 0 620 230',role:'img','aria-label':'Los 59 rendimientos estimados ordenados de menor a mayor; cada punto corresponde a una parcela'});
    const low=Math.floor(sorted[0].value*2)/2, high=Math.ceil(sorted[58].value*2)/2;
    const X=v=>45+(v-low)/(high-low)*545;
    for(let i=0;i<=4;i++){
      const x=45+(545*i/4);
      svg.append(svgEl('line',{x1:x,y1:22,x2:x,y2:192,class:'geo-rejilla'}));
      svg.append(svgEl('text',{x,y:212,'text-anchor':'middle'},fmt(low+(high-low)*i/4,2)));
    }
    sorted.forEach((r,i)=>{
      const y=30+(i%10)*16;
      const circle=svgEl('circle',{cx:X(r.value),cy:y,r:4.7,class:'geo-punto'});
      circle.append(svgEl('title',{},r.id+' · '+fmt(r.value,4)+' t/ha'));
      svg.append(circle);
    });
    chart.replaceChildren(svg);
    note(chart,'Cada círculo representa una parcela; el eje horizontal es t/ha. La altura sólo separa visualmente los puntos: no representa otra variable.');
    const tbody=table.querySelector('tbody');
    const repaint=()=>{
      const query=(search?.value||'').trim().toUpperCase();
      const how=order?.value||'id';
      const visible=data.filter(d=>d.id.includes(query)).sort((a,b)=>how==='asc'?a.value-b.value:how==='desc'?b.value-a.value:a.id.localeCompare(b.id));
      tbody.replaceChildren();
      visible.forEach(row=>{
        const tr=element('tr');
        tr.append(element('td','',row.id),element('td','',fmt(row.value,4)),element('td','','Estimación, cosecha no observada'));
        tbody.append(tr);
      });
      const count=$('geo-59-cuenta');if(count)count.textContent='Se muestran '+visible.length+' de 59 parcelas.';
    };
    search?.addEventListener('input',repaint);
    order?.addEventListener('change',repaint);
    repaint();
  }catch(e){note(summary,'No se pudo mostrar la tabla de 59 estimaciones verificadas: '+e.message);}
}
function drawMoran(target,arr,metric,title){
  const rows=arr.map(r=>({x:r.k,y:r[metric],label:'k='+r.k}));
  const values=rows.map(r=>r.y).concat(metric==='C'?[1]:[0]);
  const min=Math.min(...values),max=Math.max(...values),span=Math.max(.06,max-min);
  plot(target,rows,{xmin:4,xmax:24,ymin:min-span*.25,ymax:max+span*.25,zero:metric==='C'?1:0,xDecimals:0,decimals:3,label:title});
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
    note(box,'Los contrastes de normalidad rechazan la hipótesis de normalidad. No rechazar las pruebas de heterocedasticidad no demuestra varianza constante. Los valores p son exploratorios porque las particiones LOOCV comparten entrenamientos.');
  });
  addView('moran','Moran I',(box)=>{
    box.append(element('h3','','¿Los errores parecidos están cerca?'));
    const target=element('div');box.append(target);
    drawMoran(target,data.spatial.signed_residual_moran,'I','Moran I de los errores con signo para vecinos k = 4, 8, 12 y 24');
    note(box,'Referencia: I = 0. Los valores p ajustados por Holm de esta serie son '+data.spatial.signed_residual_moran.map(x=>fmt(x.p_holm_all,3)).join(' / ')+'. La falta de significación no prueba independencia espacial.');
  });
  addView('geary','Geary C',(box)=>{
    box.append(element('h3','','¿Hay similitud espacial de los residuos?'));
    const target=element('div');box.append(target);
    drawMoran(target,data.spatial.geary_c.filter(x=>x.spatial_variable==='signed_residual'),'C','Geary C de los errores con signo para vecinos k = 4, 8, 12 y 24');
    note(box,'Referencia aproximada: C = 1. Se trata de una prueba espacial exploratoria sobre las exclusiones LOOCV.');
  });
  addView('semivariograma','Distancia',(box)=>{
    box.append(element('h3','','¿Cómo cambia la diferencia de errores con la distancia?'));
    const target=element('div');box.append(target);
    const rows=data.spatial.semivariogram.map(x=>({x:x.distance_km,y:x.semivariance_t2_ha2,label:fmt(x.distance_km,1)+' km, '+x.pairs+' pares'}));
    plot(target,rows,{xmin:0,xmax:Math.ceil(Math.max(...rows.map(x=>x.x))/10)*10,ymin:0,ymax:.38,xDecimals:0,decimals:3,label:'Semivariograma empírico de 138 residuos LOOCV'});
    note(box,'Cada punto representa pares de parcelas agrupados por distancia. Es un diagnóstico descriptivo, no un semivariograma teórico ajustado. Unidad vertical: (t/ha)².');
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
