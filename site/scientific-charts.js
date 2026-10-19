/* GeoCebada — gráficos científicos fieles a datos agregados, sin entrenar modelos.
   Fuente: heri-espino/todoseboso, series reales de 2025 y Reference26_mean LOOCV. */
(()=>{'use strict';
const svgNS='http://www.w3.org/2000/svg', $=s=>document.querySelector(s);
const el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!=null)e.textContent=String(text);if(cls)e.className=cls;return e;};
const NS=(tag,attrs={},text)=>{const n=document.createElementNS(svgNS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(text!=null)n.textContent=String(text);return n;};
const fmt=(v,p=2)=>Number(v).toFixed(p);const color={forest:'#173E34',olive:'#718658',oliveLight:'#CEDDCC',gold:'#D6AB70',clay:'#AF6D53',line:'#B9C7B3',ink:'#29433B',muted:'#627A68',paper:'#FFFDF8'};
const svg=(w=660,h=270,label='Gráfica')=>{const s=NS('svg',{viewBox:'0 0 '+w+' '+h,role:'img','aria-label':label,class:'geo-extra-svg'});return s;};
const caption=(t)=>el('p',t,'geo-extra-caption');
const node=(root,...els)=>{root.append(...els);return root};
const legend=(items)=>{const out=el('div',null,'geo-extra-legend');for(const [label,paint] of items){const span=el('span');const mark=el('i');mark.style.background=paint;span.append(mark,document.createTextNode(label));out.append(span)}return out};
const backgroundGrid=(s,left,right,top,bottom,max,n)=>{for(let i=0;i<=n;i++){const v=(i/n)*max,y=bottom-(bottom-top)*i/n;s.append(NS('line',{x1:left,y1:y,x2:right,y2:y,stroke:color.line,'stroke-width':i===0?1.7:.6}),NS('text',{x:left-8,y:y+4,'text-anchor':'end',fill:color.muted,'font-size':11},fmt(v,max<2?2:0)));}};
function monthly(target,series,desc){
  if(!target||!series||series.months.length!==7)return;target.replaceChildren();
  const data=series.months,max=series.variable==='ndvi'?0.8:400,left=56,right=637,top=27,bottom=238;
  const X=i=>left+(right-left)*i/6,Y=v=>bottom-(bottom-top)*v/max;
  const s=svg(675,294,desc+' · mediana mensual y percentiles 10–90 de 197 parcelas en 2025');
  backgroundGrid(s,left,right,top,bottom,max,4);
  const poly=[...data.map((p,i)=>[X(i),Y(p.p90)]),...data.slice().reverse().map((p,i)=>[X(6-i),Y(p.p10)])];
  s.append(NS('polygon',{points:poly.map(a=>a.join(',')).join(' '),fill:color.oliveLight,opacity:.88}));
  s.append(NS('polyline',{points:data.map((p,i)=>X(i)+','+Y(p.median)).join(' '),stroke:color.forest,'stroke-width':3,fill:'none','stroke-linecap':'round','stroke-linejoin':'round'}));
  data.forEach((p,i)=>{s.append(NS('circle',{cx:X(i),cy:Y(p.median),r:4.4,fill:color.forest,stroke:color.paper,'stroke-width':1.5}));s.append(NS('text',{x:X(i),y:bottom+19,'text-anchor':'middle',fill:color.muted,'font-size':12},p.label));});
  s.append(NS('text',{x:left,y:14,fill:color.muted,'font-size':11},series.variable==='ndvi'?'NDVI':'Milímetros'));
  target.append(s,legend([['Mediana mensual',color.forest],['Percentiles 10 a 90',color.oliveLight]]),caption('Periodo abril–octubre de 2025 · '+series.months.length+' meses · '+data.map(x=>x.n).join(' / ')+' observaciones disponibles por mes. Las bandas describen variación entre parcelas, no intervalos de predicción.'));
}
function geology(target,weights){
 if(!target||weights.length!==4)return;target.replaceChildren();
 weights.forEach((w,i)=>{const row=el('div',null,'geo-extra-weight-row'),head=el('div',null,'geo-extra-weight-head');head.append(el('strong','Grupo geológico '+i),el('span',fmt(w*100,1)+' % para experto local'));
 const bar=el('div',null,'geo-extra-weight-track'),local=el('span',null,'geo-extra-weight-local'),climate=el('span',null,'geo-extra-weight-climate');
 local.style.width=fmt(w*100,3)+'%';climate.style.width=fmt((1-w)*100,3)+'%';bar.append(local,climate);row.append(head,bar);target.append(row)});
 target.append(legend([['Parcelas cercanas',color.olive],['Clima y NDVI',color.gold]]),caption('Cuatro pesos aprendidos en el ajuste histórico sobre 138 parcelas. Los grupos de K-means no representan clases de fertilidad ni orden de rendimiento.'));
}
function stackedInfluence(root,inf){
 const data=[['Mayor error',inf.share_sse_largest,color.clay],['Segundo mayor',inf.share_sse_largest_two-inf.share_sse_largest,color.gold],['Otras 136',1-inf.share_sse_largest_two,color.oliveLight]];
 const main=el('div',null,'geo-extra-influence-chart'),stack=el('div',null,'geo-extra-influence-stack');
 stack.setAttribute('role','img');stack.setAttribute('aria-label',data.map(([name,v])=>name+' '+fmt(100*v,2)+' %').join('; '));
 for(const [label,value,paint] of data){const seg=el('span');seg.style.width=fmt(value*100,5)+'%';seg.style.background=paint;seg.title=label+': '+fmt(100*value,2)+' % del error cuadrático';stack.append(seg)}
 const text=el('p','Una parcela concentra '+fmt(100*inf.share_sse_largest,2)+' % del error cuadrático total; las dos mayores concentran '+fmt(100*inf.share_sse_largest_two,2)+' %.','geo-extra-caption');
 main.append(text,stack,legend(data.map(([label,,paint])=>[label,paint])));
 root.append(main);return main;
}
function magnitude(root,m){
 const wrap=el('div',null,'geo-extra-magnitude');
 const s=svg(670,208,'Mediana y percentil 95 del error absoluto LOOCV, escala de cero a una tonelada por hectárea');
 const left=170,right=640,width=right-left,axis=184;[0,.25,.5,.75,1].forEach(t=>{let x=left+width*t;s.append(NS('line',{x1:x,y1:28,x2:x,y2:axis,'stroke-width':t===0?1.5:1,stroke:color.line}),NS('text',{x,y:202,'text-anchor':'middle','font-size':11,fill:color.muted},fmt(t,2)));});
 [['Mediana',m.median_absolute_error_t_ha,61],['Percentil 95',m.p95_absolute_error_t_ha,124]].forEach(([name,val,y])=>{s.append(NS('text',{x:left-12,y:y+10,'text-anchor':'end','font-size':13,fill:color.ink},name),NS('rect',{x:left,y,width:Math.min(1,val)*width,height:26,rx:4,fill:color.olive}),NS('text',{x:left+Math.min(1,val)*width+8,y:y+18,'font-size':13,fill:color.forest},fmt(val,3)));});
 wrap.append(s,caption('Escala con origen en cero, de 0 a 1 t/ha. Error máximo por separado: '+fmt(m.max_absolute_error_t_ha,4)+' t/ha (no se comprime la gráfica por ese extremo).'));root.append(wrap);
}
function spatialCharts(root,spatial,variable){
 const varFields={signed_residual:'signed_residual_moran',absolute_error:'absolute_error_moran',squared_error:'squared_error_moran'};
 const moran=spatial[varFields[variable]],geary=spatial.geary_c.filter(x=>x.spatial_variable===variable);
 const layout=el('div',null,'geo-extra-spatial-layout');
 const make=(rows,key,valueField,baseline,title)=>{
   const target=el('div',null,'geo-extra-spatial-card'),h=el('h4',title);
   const s=svg(360,205,title+'; vecinos 4, 8, 12 y 24');
   const val=rows.map(x=>x[valueField]),mn=Math.min(...val,baseline),mx=Math.max(...val,baseline),pad=Math.max((mx-mn)*.28,.026),lo=mn-pad,hi=mx+pad;
   const X=v=>78+235*(v-lo)/(hi-lo);
   s.append(NS('line',{x1:X(baseline),y1:15,x2:X(baseline),y2:173,stroke:color.gold,'stroke-width':2,'stroke-dasharray':'4 4'}));
   rows.forEach((row,i)=>{const y=39+i*39; s.append(NS('text',{x:62,y:y+4,'text-anchor':'end','font-size':12,fill:color.muted},'k = '+row.k));s.append(NS('line',{x1:78,y1:y,x2:315,y2:y,stroke:color.line,'stroke-width':.6}));s.append(NS('circle',{cx:X(row[valueField]),cy:y,r:6,fill:color.forest}));});
   s.append(NS('text',{x:78,y:198,'font-size':11,fill:color.muted},fmt(lo,2)),NS('text',{x:315,y:198,'text-anchor':'end','font-size':11,fill:color.muted},fmt(hi,2)));
   target.append(h,s,caption('Línea dorada: '+key+' = '+baseline+'. Los puntos son estadísticos, no valores p.'));return target;
 };
 layout.append(make(moran,'Moran I','I',0,'Moran I por vecinos'),make(geary,'Geary C','C',1,'Geary C por vecinos'));
 root.append(layout);return layout;
}
function semivariogram(root,data){
 const items=data.semivariogram;if(!items||items.length!==6)return;
 const s=svg(680,315,'Semivariograma empírico de seis intervalos: distancia mediana real y semivarianza del residuo');
 const left=80,right=647,top=22,bottom=253,maxX=Math.max(...items.map(x=>x.distance_km))*1.1,maxY=Math.max(...items.map(x=>x.semivariance_t2_ha2))*1.18;
 for(let i=0;i<=4;i++){const y=bottom-i*(bottom-top)/4;s.append(NS('line',{x1:left,y1:y,x2:right,y2:y,stroke:color.line,'stroke-width':i===0?1.4:.6}),NS('text',{x:left-9,y:y+4,'text-anchor':'end','font-size':11,fill:color.muted},fmt(maxY*i/4,2)));}
 for(let i=0;i<=5;i++){const x=left+(right-left)*i/5;s.append(NS('text',{x,y:bottom+20,'text-anchor':'middle','font-size':11,fill:color.muted},fmt(maxX*i/5,0)));}
 s.append(NS('text',{x:left,y:13,'font-size':11,fill:color.muted},'Semivarianza (t/ha)²'),NS('text',{x:right,y:299,'text-anchor':'end','font-size':11,fill:color.muted},'Distancia (km)'));
 items.forEach((p,i)=>{const x=left+(right-left)*p.distance_km/maxX,y=bottom-(bottom-top)*p.semivariance_t2_ha2/maxY;const dot=NS('circle',{cx:x,cy:y,r:7,fill:i%2?color.gold:color.olive,stroke:color.paper,'stroke-width':1.5});dot.append(NS('title',{},'Intervalo '+(i+1)+': '+fmt(p.distance_km,2)+' km, '+fmt(p.semivariance_t2_ha2,4)+' (t/ha)²; '+p.pairs+' pares'));s.append(dot);});
 root.append(s,caption('Seis intervalos, '+items.reduce((n,p)=>n+p.pairs,0).toLocaleString('es-MX')+' pares no independientes. No se interpolaron ni suavizaron los puntos.'));
}
function bootstrap(root,data){
 const accepted=data.groups.filter(x=>x.status==='computed');if(!accepted.length)return;
 const s=svg(680,230,'Rangos percentiles de RMSE por agrupación geográfica; línea central es RMSE completo');
 const min=0.2,max=0.65,left=198,right=642,X=v=>left+(right-left)*(v-min)/(max-min);
 [0.2,.3,.4,.5,.6].forEach(v=>{const x=X(v);s.append(NS('line',{x1:x,y1:26,x2:x,y2:183,stroke:color.line,'stroke-width':.7}),NS('text',{x,y:206,'text-anchor':'middle','font-size':11,fill:color.muted},fmt(v,2)));});
 accepted.forEach((x,i)=>{const y=62+i*70;s.append(NS('text',{x:left-12,y:y+4,'text-anchor':'end','font-size':11,fill:color.ink},x.id==='municipality'?'9 municipios':'9 bloques de 15 km'),NS('line',{x1:X(x.rmse_t_ha.low),y1:y,x2:X(x.rmse_t_ha.high),y2:y,stroke:color.olive,'stroke-width':9,'stroke-linecap':'round'}),NS('circle',{cx:X(x.rmse_t_ha.point),cy:y,r:5.5,fill:color.forest,stroke:color.paper,'stroke-width':1.5}));});
 s.append(NS('text',{x:right,y:224,'text-anchor':'end','font-size':11,fill:color.muted},'RMSE (t/ha)'));
 root.append(s,caption('Rangos percentiles 2.5–97.5 % de 3,000 remuestreos, con los residuos LOOCV fijos. No son bandas calibradas para las 59 predicciones.'));
}
async function realCharts(){
 const rain=$('#geo-real-rain'),ndvi=$('#geo-real-ndvi'),status=$('#geo-real-status');if(!rain||!ndvi||!status)return;
 try{const r=await fetch('./data/real_charts.json',{cache:'no-store'});if(!r.ok)throw Error('Agregados observacionales no disponibles');const d=await r.json();if(d.schema_version!==1||d.kind!=='real_chart_aggregates'||d.rainfall.months.length!==7||d.ndvi.months.length!==7)throw Error('Esquema inválido');
 monthly(rain,d.rainfall,'Precipitación observada'),monthly(ndvi,d.ndvi,'NDVI satelital observado');
 status.textContent='Datos observados en 2025; todos los meses tienen 197 registros válidos en este agregado. Las bandas no son intervalos predictivos.';
 }catch(e){status.textContent='Las gráficas observacionales requieren los agregados originales; no se muestran datos simulados: '+e.message;}
}
async function predictions(){
 const root=$('#geo-pred59-plot'),body=$('#geo-pred59-table'),filter=$('#geo-pred59-search'),status=$('#geo-pred59-status'),examples=$('#geo-pred59-examples');if(!root||!body||!filter||!status)return;
 try{const r=await fetch('./explorador/data/predictions.csv',{cache:'no-store'});if(!r.ok)throw Error('No se encuentra el archivo de predicciones autorizado');const text=await r.text(),lines=text.trim().split(/\r?\n/);const header=lines.shift().trim().replace(/^\uFEFF/,'');if(header!=='ID_POLIGONO,RENDIMIENTO_T_HA')throw Error('Columnas CSV inesperadas');
 const all=lines.map(line=>{const [id,value]=line.split(',');return {id:id.trim(),value:Number(value)}});if(all.length!==59||new Set(all.map(x=>x.id)).size!==59||all.some(x=>!Number.isFinite(x.value)))throw Error('Las 59 estimaciones no pasan la verificación');
 const sorted=all.slice().sort((a,b)=>a.value-b.value);const picks=[['Menor estimación',sorted[0]],['Estimación central',sorted[29]],['Mayor estimación',sorted[58]]];examples.replaceChildren();picks.forEach(([name,v])=>{const card=el('div',null,'geo-extra-example');card.append(el('span',name),el('strong',fmt(v.value,3)+' t/ha'),el('small',v.id));examples.append(card)});
 root.replaceChildren();const s=svg(700,275,'59 estimaciones reales de Reference26 histórico por identificador, ordenadas por rendimiento estimado');
 const xmin=2.5,xmax=5,left=74,right=663,top=32,bottom=216,X=v=>left+(right-left)*(v-xmin)/(xmax-xmin);[2.5,3,3.5,4,4.5,5].forEach(v=>{const x=X(v);s.append(NS('line',{x1:x,y1:top,x2:x,y2:bottom,stroke:color.line,'stroke-width':.8}),NS('text',{x,y:245,'text-anchor':'middle','font-size':11,fill:color.muted},fmt(v,1)))});s.append(NS('text',{x:right,y:268,'text-anchor':'end','font-size':11,fill:color.muted},'Rendimiento estimado (t/ha)'));
 sorted.forEach((p,i)=>{const y=46+(i%8)*20.5,important=i===0||i===29||i===58,point=NS('circle',{cx:X(p.value),cy:y,r:important?6.5:4.3,fill:important?color.gold:color.olive,opacity:.94,stroke:color.paper,'stroke-width':1});point.append(NS('title',{},p.id+': '+fmt(p.value,4)+' t/ha'));s.append(point)});root.append(s,legend([['59 predicciones históricas',color.olive],['Menor, central y mayor',color.gold]]),caption('Cada punto es una parcela distinta. La altura solo separa puntos visualmente y no representa otra variable. Los rendimientos verdaderos de estas 59 parcelas son desconocidos.'));
 const update=()=>{const phrase=filter.value.trim().toUpperCase();const subset=sorted.filter(x=>x.id.toUpperCase().includes(phrase));body.replaceChildren();subset.forEach(x=>{const tr=el('tr');tr.append(el('td',x.id),el('td',fmt(x.value,6)));body.append(tr)});status.textContent=subset.length+' de 59 estimaciones archivadas · Reference26 con imputación por mediana. No se calculan predicciones nuevas.'};filter.addEventListener('input',update);update();
 }catch(e){status.textContent='No se pudieron cargar las 59 estimaciones verificables: '+e.message}
}
document.addEventListener('DOMContentLoaded',()=>{realCharts();predictions()});
window.GeoCebadaVisuals=Object.freeze({magnitude,stackedInfluence,spatialCharts,semivariogram,bootstrap,geology});
})();
