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
 // Tres referencias auténticas del CSV, sin gráficos ni fichas de parcelas individuales.
 const examples=get('pred59-examples');examples.replaceChildren();
 for(const [label,r] of [['Menor estimación',sorted[0]],['Estimación mediana',sorted[29]],['Mayor estimación',sorted[58]]]){
  const card=el('div','pred59-example pred59-example-static');
  card.append(el('span','pred59-eyebrow',label),
   el('strong','',fmt(r.value,3)+' t/ha'),
   el('span','',r.id),
   el('small','',haveGeography?r.state+' · '+r.municipality:'Rendimiento estimado'));
  examples.append(card);
 }
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