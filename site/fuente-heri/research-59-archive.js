/* Archivo histórico Reference26: gráfico de Heri sin tabla duplicada.
   CSV auténtico, valores desconocidos nunca representados como observaciones.
   Las 59 estimaciones originales no se reentrenan ni recalculan. */
(function(){
"use strict";
const get=id=>document.getElementById(id);
const el=(tag,cls,value)=>{
 const node=document.createElement(tag);
 if(cls)node.className=cls;
 if(value!==undefined)node.textContent=String(value);
 return node;
};
const fmt=(v,d=3)=>Number(v).toLocaleString('es-MX',{minimumFractionDigits:d,maximumFractionDigits:d});
async function readPredictions(){
 const res=await fetch('../explorador/data/predictions.csv',{cache:'no-store'});
 if(!res.ok)throw Error('No se puede acceder a las 59 estimaciones originales');
 const lines=(await res.text()).trim().split(/\r?\n/).map(x=>x.replace(/^\uFEFF/,'').trim());
 if(lines.shift()!=='ID_POLIGONO,RENDIMIENTO_T_HA')throw Error('El CSV no cumple el formato autorizado');
 const records=lines.map(line=>{
  const values=line.split(',');
  if(values.length!==2||!values[1].trim())throw Error('Hay una fila incompleta en el CSV');
  return {id:values[0],value:Number(values[1]),state:null,municipality:null};
 });
 if(records.length!==59||new Set(records.map(x=>x.id)).size!==59||
    records.some(x=>!/^AGC_\d+$/.test(x.id)||!Number.isFinite(x.value)||x.value<=0))
    throw Error('Los 59 valores y sus identificadores no pasaron la comprobación');
 const mean=records.reduce((sum,x)=>sum+x.value,0)/records.length;
 if(Math.abs(mean-3.956432328667021)>1e-7)throw Error('La media no coincide con la cifra histórica documentada');
 return records;
}
async function addGeography(records){
 if(typeof DecompressionStream==='undefined')return false;
 const res=await fetch('../explorador/data/mapa_publico.json.gz',{cache:'no-store'});
 if(!res.ok||!res.body)return false;
 const obj=JSON.parse(await new Response(res.body.pipeThrough(new DecompressionStream('gzip'))).text());
 if(obj.schema!=='geocebada-map-public-1'||obj.geometry?.type!=='FeatureCollection'||obj.geometry.features?.length!==197)
   throw Error('Metadatos geográficos no reconocidos');
 const counts={Hidalgo:0,Puebla:0,Tlaxcala:0},byId=new Map();
 for(const f of obj.geometry.features){
   const props=f.properties||{},id=String(props.ID_POLIGONO||props.ID_POLIGON||'').trim().toUpperCase();
   const state=String(props.Estado||props.estado||'').trim(),split=String(props.CONJUNTO||props.conjunto||'').trim().toUpperCase();
   if(!/^AGC_\d+$/.test(id)||byId.has(id)||!Object.hasOwn(counts,state)||!['PREDICCION','ENTRENAMIENTO'].includes(split))
     throw Error('Geografía inconsistente o duplicada');
   byId.set(id,{state,split,municipality:String(props.Municipio||props.municipio||'').trim()});
   if(split==='PREDICCION')counts[state]++;
 }
 if(counts.Hidalgo!==15||counts.Puebla!==29||counts.Tlaxcala!==15||records.some(r=>byId.get(r.id)?.split!=='PREDICCION'))
   throw Error('Los estados no coinciden con las 59 predicciones originales');
 for(const r of records){
  const metadata=byId.get(r.id);r.state=metadata.state;r.municipality=metadata.municipality||'No disponible';
 }
 return true;
}
async function init(){
 const root=get('pred59-data'),status=get('pred59-status');
 if(!root||!status)return;
 const all=await readPredictions();
 let haveGeography=false;
 try{haveGeography=await addGeography(all)}catch(e){console.warn('No se mostrarán estados sin comprobar:',e.message)}
 const sorted=[...all].sort((a,b)=>a.value-b.value||a.id.localeCompare(b.id));
 const stats=get('pred59-summary');stats.replaceChildren();
 const items=[
  ['Parcelas estimadas','59','Sin cosechas reales verificadas'],
  ['Promedio',fmt(all.reduce((sum,r)=>sum+r.value,0)/59,4)+' t/ha','Estimaciones históricas por mediana'],
  ['Valor mínimo',fmt(sorted[0].value,3)+' t/ha',sorted[0].id],
  ['Valor máximo',fmt(sorted[58].value,3)+' t/ha',sorted[58].id]
 ];
 for(const [label,value,extra] of items){
  const card=el('div','pred59-summary-item');
  card.append(el('span','',label),el('strong','',value),el('small','',extra));stats.append(card);
 }
 let chosen=sorted[29].id;
 const detail=get('pred59-detail');
 const choose=id=>{
  const row=all.find(r=>r.id===id);
  if(!row)return;
  chosen=id;
  const loc=haveGeography?row.state+(row.municipality?' · '+row.municipality:''):'Ubicación no verificada para esta gráfica';
  detail.replaceChildren();
  const headline=el('div','pred59-detail-head');
  const title=el('div');
  title.append(el('span','pred59-eyebrow','ESTIMACIÓN HISTÓRICA · COSECHA NO OBSERVADA'),el('h4','',row.id),el('p','',loc));
  const val=el('div','pred59-yield');val.append(el('strong','',fmt(row.value,4)),el('span','','t/ha estimadas'));
  headline.append(title,val);
  detail.append(headline,el('p','pred59-detail-note','El desglose individual de clima, vecinos, geología y corrección no está en el CSV. El error de esta parcela no puede determinarse sin conocer su cosecha real.'));
  document.querySelectorAll('[data-pred59-id]').forEach(b=>{
   const active=b.dataset.pred59Id===id;
   b.classList.toggle('active',active);
   b.setAttribute('aria-pressed',String(active));
  });
 };
 const makeButton=(r,cls)=>{
  const b=el('button',cls);b.type='button';b.dataset.pred59Id=r.id;
  b.title=r.id+' · '+fmt(r.value,4)+' t/ha (estimado)';
  b.setAttribute('aria-label',b.title);
  b.addEventListener('click',()=>choose(r.id));
  return b;
 };
 const examples=get('pred59-examples');examples.replaceChildren();
 for(const [label,r] of [['Menor estimación',sorted[0]],['Estimación mediana',sorted[29]],['Mayor estimación',sorted[58]]]){
  const card=makeButton(r,'pred59-example');
  card.append(el('span','pred59-eyebrow',label),
   el('strong','',fmt(r.value,3)+' t/ha'),
   el('span','',r.id),el('small','',haveGeography?r.state+' · '+r.municipality:'Rendimiento estimado'),
   el('span','pred59-example-link','Ver estimación →'));
  examples.append(card);
 }
 const plot=get('pred59-plot');plot.replaceChildren();
 const minimum=Math.floor(sorted[0].value*2)/2,maximum=Math.ceil(sorted[58].value*2)/2;
 const upper=maximum>minimum?maximum:minimum+1;
 const offset=value=>2+(value-minimum)/(upper-minimum)*96;
 const groups=haveGeography?['Hidalgo','Puebla','Tlaxcala']:['Las 59 parcelas'];
 for(const [i,state] of groups.entries()){
  const row=el('div','pred59-plot-row'),label=el('span','pred59-plot-state',state);
  const track=el('div','pred59-track');
  const matches=all.filter(r=>!haveGeography||r.state===state).sort((a,b)=>a.value-b.value);
  matches.forEach((r,j)=>{
   const dot=makeButton(r,'pred59-dot tone-'+i%3);
   dot.style.left=fmt(offset(r.value),4)+'%';
   dot.style.top=(14+(j%3)*19)+'px';
   track.append(dot);
  });
  row.append(label,track);plot.append(row);
 }
 const axis=el('div','pred59-axis');axis.append(el('span','pred59-plot-state',''));
 const ticks=el('div','pred59-ticks');
 for(let i=0;i<=4;i++){
  const tick=el('span','',fmt(minimum+(upper-minimum)*i/4,2));
  tick.style.left=fmt(2+i*24,1)+'%';ticks.append(tick);
 }
 axis.append(ticks);plot.append(axis);
 plot.append(el('p','pred59-axis-name','Rendimiento estimado (t/ha). Cada punto representa una de las 59 parcelas sin rendimiento observado.'));
 choose(chosen);
 root.hidden=false;
 status.textContent=haveGeography?
  '59 estimaciones y estados verificados contra los datos públicos autorizados. Ninguna representa una cosecha observada.':
  '59 estimaciones verificadas contra el CSV original. La agrupación por estado no se pudo comprobar en este navegador.';
}
document.addEventListener('DOMContentLoaded',()=>{
 if(document.documentElement.dataset.researchVista!=='resultados')return;
 init().catch(e=>{
  const status=get('pred59-status');
  if(status)status.textContent='No es posible mostrar cifras sin validar: '+e.message;
 });
});
})();