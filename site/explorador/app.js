/* GeoCebada — frontend independiente, sin reentrenamiento.
 * Datos y estimaciones canónicos: heri-espino/GeoC.
 * Para nuevas parcelas solo preparamos registros VALIDADOS: no inferimos rendimientos.
 */
'use strict';
const $ = id => document.getElementById(id);
const ALLOWED_STATES = Object.freeze(['Hidalgo', 'Puebla', 'Tlaxcala']);
// Fuente de geometría externa: strotgen/mexico-leaflet/states.geojson.
// Se descarga para COMPROBACIÓN TERRITORIAL: NO se transmiten las coordenadas ingresadas.
// Si el servicio falla, no se permite registrar la parcela (fail closed).
const STATES_GEOJSON_URL = 'https://raw.githubusercontent.com/strotgen/mexico-leaflet/master/states.geojson';
let boundaryPromise = null;
let validatedRequest = null;
const nfmt = (value, decimals = 3) => Number(value).toLocaleString('es-MX', {minimumFractionDigits:decimals, maximumFractionDigits:decimals});

function parseCSV(text) {
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(c==='"') {if(quoted && text[i+1]==='"'){cell+='"';i++;} else quoted=!quoted;}
    else if(c===','&&!quoted){row.push(cell);cell='';}
    else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);cell='';if(row.some(Boolean))rows.push(row);row=[];}
    else cell+=c;
  }
  row.push(cell);if(row.some(Boolean))rows.push(row);
  if(quoted)throw new Error('CSV con comillas sin cerrar.');
  const headers=(rows.shift()||[]).map(v=>v.replace(/^\uFEFF/,'').trim());
  if(!headers.length||new Set(headers).size!==headers.length||headers.some(h=>!h)) throw new Error('Encabezados CSV inválidos.');
  return rows.map(cells=>Object.fromEntries(headers.map((header,i)=>[header,cells[i]??''])));
}
async function csv(name){const r=await fetch('./data/'+name,{cache:'no-store'});if(!r.ok)throw new Error('No se pudo cargar '+name+' (HTTP '+r.status+').');return parseCSV(await r.text());}
function node(tag,cls,content){const el=document.createElement(tag);if(cls)el.className=cls;if(content!==undefined)el.textContent=content;return el;}

function setupMobileNavigation(){
  const toggle=$('mobile-toggle'), nav=$('site-nav');
  toggle.addEventListener('click',()=>{
    const open=nav.classList.toggle('is-open');toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-label',open?'Cerrar menú':'Abrir menú');
  });
  nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('is-open');toggle.setAttribute('aria-expanded','false');}));
  // El desplegable de Investigación funciona con teclado, clic y celular.
  const research=nav.querySelector('.nav-research');
  if(research){
    document.addEventListener('click',event=>{
      if(research.open && !research.contains(event.target))research.open=false;
    });
    document.addEventListener('keydown',event=>{
      if(event.key==='Escape' && research.open){
        research.open=false;
        research.querySelector('summary')?.focus();
      }
    });
    toggle.addEventListener('click',()=>{
      if(!nav.classList.contains('is-open'))research.open=false;
    });
  }
}

function showPredictions(records){
  const select=$('parcel-select'),search=$('parcel-search'),table=$('predictions-table');
  select.replaceChildren();
  records.forEach(r=>{const option=node('option','',r.id);option.value=r.id;select.append(option);});
  const values=records.map(r=>r.y).sort((a,b)=>a-b);
  const min=values[0],max=values.at(-1),mean=values.reduce((a,b)=>a+b,0)/values.length;
  const median=values[Math.floor(values.length/2)];
  $('predictions-mean').textContent=nfmt(mean)+' t/ha';
  $('predictions-median').textContent=nfmt(median)+' t/ha';
  $('predictions-min').textContent=nfmt(min)+' t/ha';
  $('predictions-max').textContent=nfmt(max)+' t/ha';
  $('hist-min').textContent=nfmt(min,2);$('hist-max').textContent=nfmt(max,2);
  const binCount=12,bins=Array(binCount).fill(0),width=(max-min)/binCount||1;
  records.forEach(r=>bins[Math.min(binCount-1,Math.floor((r.y-min)/width))]++);
  const hist=$('histogram');hist.replaceChildren();
  const top=Math.max(...bins);
  bins.forEach((amount,i)=>{const bar=node('span','hist-bar');bar.style.height=(100*amount/top)+'%';bar.title=`Intervalo ${i+1}: ${amount} parcelas`;hist.append(bar);});

  let selectedId=records[0].id;
  function selectRow(id){
    const r=records.find(x=>x.id===id);if(!r)return;
    selectedId=r.id;select.value=r.id;
    $('prediction-value').textContent=nfmt(r.y);
    $('prediction-id').textContent='ID_POLIGONO: '+r.id;
    const index=Math.min(binCount-1,Math.floor((r.y-min)/width));
    [...hist.children].forEach((bar,i)=>bar.classList.toggle('is-selected',i===index));
    [...table.children].forEach(tr=>tr.classList.toggle('is-selected',tr.dataset.id===id));
  }
  function renderTable(term=''){
    const found=records.filter(r=>r.id.includes(term.toUpperCase().trim()));
    const frag=document.createDocumentFragment();
    for(const r of found){
      const tr=node('tr');tr.dataset.id=r.id;
      tr.append(node('td','',r.id),node('td','',nfmt(r.y)),node('td','','Predicción'));
      tr.tabIndex=0;
      const pick=()=>{search.value=r.id;renderTable(r.id);selectRow(r.id);};
      tr.addEventListener('click',pick);
      tr.addEventListener('keydown',event=>{if(event.key==='Enter')pick();});
      frag.append(tr);
    }
    if(!found.length){const tr=node('tr'),td=node('td','','No se encontraron parcelas.');td.colSpan=3;tr.append(td);frag.append(tr);}
    table.replaceChildren(frag);
    $('table-count').textContent=found.length+' de 59 registros';
    selectRow(selectedId);
  }
  select.addEventListener('change',()=>{search.value=select.value;renderTable(select.value);selectRow(select.value);});
  search.addEventListener('input',()=>{
    const term=search.value.trim().toUpperCase();renderTable(term);
    const exact=records.find(r=>r.id===term);if(exact)selectRow(exact.id);
  });
  $('reset-filter').addEventListener('click',()=>{search.value='';renderTable();selectRow(records[0].id);});
  renderTable();selectRow(selectedId);
  $('data-status').textContent='59 estimaciones verificadas. Valores finales del modelo seleccionado, no rendimientos observados.';
}
function drawComparison(target,records,names,highlight){
  const el=$(target);el.replaceChildren();
  const selected=names.map(n=>records.find(r=>r.model===n));
  if(selected.some(x=>!x)){el.append(node('p','help-text','No se encontraron todos los modelos esperados.'));return;}
  const highest=Math.max(...selected.map(r=>Number(r.rmse_pooled)));
  selected.forEach((r,i)=>{
    const value=Number(r.rmse_pooled),item=node('div','bar-entry'+(r.model===highlight?' is-winner':''));
    const top=node('div','bar-entry-top');
    top.append(node('span','',r.model===highlight?names[i].replace('_frozen','')+' · seleccionado':names[i].replace('_nested',' (ajustado)').replace('_frozen',' (fijo)')),
      node('strong','',nfmt(value,6)));
    const track=node('div','bar-track'),fill=node('div','bar-fill');
    fill.style.width=(100*value/highest).toFixed(2)+'%';track.append(fill);item.append(top,track);el.append(item);
  });
}

// El punto está en [longitud, latitud]. Algoritmo ray casting con soporte Polygon/MultiPolygon y huecos.
function insideRing(longitude,latitude,ring){
  let inside=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++){
    const [xi,yi]=ring[i],[xj,yj]=ring[j];
    const intersects=(yi>latitude)!==(yj>latitude) && longitude<((xj-xi)*(latitude-yi))/(yj-yi)+xi;
    if(intersects)inside=!inside;
  }
  return inside;
}
function insidePolygon(longitude,latitude,polygon){
  return polygon.length>0 && insideRing(longitude,latitude,polygon[0]) && !polygon.slice(1).some(ring=>insideRing(longitude,latitude,ring));
}
function locationIsInGeometry(longitude,latitude,geometry){
  if(geometry?.type==='Polygon')return insidePolygon(longitude,latitude,geometry.coordinates);
  if(geometry?.type==='MultiPolygon')return geometry.coordinates.some(p=>insidePolygon(longitude,latitude,p));
  return false;
}
async function getStateBoundaries(){
  if(!boundaryPromise){
    boundaryPromise=fetch(STATES_GEOJSON_URL,{mode:'cors'}).then(async response=>{
      if(!response.ok)throw new Error('No se pudieron consultar límites estatales.');
      const doc=await response.json();
      if(doc.type!=='FeatureCollection'||!Array.isArray(doc.features)) throw new Error('Los límites estatales tienen formato inesperado.');
      const byName={};
      for(const f of doc.features){const state=f.properties?.state_name; if(ALLOWED_STATES.includes(state))byName[state]=f.geometry;}
      if(ALLOWED_STATES.some(state=>!byName[state]))throw new Error('Los datos cartográficos están incompletos.');
      return byName;
    }).catch(error=>{boundaryPromise=null;throw error;});
  }
  return boundaryPromise;
}
function showFeedback(message,type='error'){
  const el=$('form-feedback');el.textContent=message;el.className='form-feedback '+type;
}
function numberValue(id,{optional=false,min=-Infinity,max=Infinity}={}){
  const input=$(id),value=input.value.trim();
  if(optional&&!value)return null;
  if(!value)throw new Error('Completa el campo «'+input.labels?.[0]?.textContent.trim()+'».');
  const n=Number(value);
  if(!Number.isFinite(n)||n<min||n>max)throw new Error('Valor fuera de rango: '+input.labels?.[0]?.textContent.trim()+'.');
  return n;
}
async function readFeatureFile(){
  const file=$('feature-file').files?.[0];
  if(!file)return null;
  if(file.size>128*1024)throw new Error('El archivo de características debe ser menor o igual a 128 KB.');
  const extension=file.name.split('.').pop().toLowerCase();
  if(!['csv','json'].includes(extension))throw new Error('Adjunta únicamente archivos .csv o .json.');
  const source=await file.text();let record;
  if(extension==='csv'){
    const rows=parseCSV(source);if(rows.length!==1)throw new Error('El CSV de características debe tener exactamente una fila de datos.');
    record=rows[0];
  }else{
    const data=JSON.parse(source);
    record=Array.isArray(data)?data.length===1?data[0]:null:data;
    if(!record||Array.isArray(record)||typeof record!=='object')throw new Error('El JSON debe contener un objeto o una lista con un solo objeto.');
  }
  if(Object.keys(record).length>3000)throw new Error('El archivo tiene demasiadas columnas para esta versión.');
  $('feature-feedback').textContent='Características locales leídas: '+Object.keys(record).length+' campos de '+file.name+'.';
  return {filename:file.name,fields:record};
}
function downloadJSON(payload){
  const blob=new Blob([JSON.stringify(payload,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const anchor=node('a');anchor.href=url;anchor.download='geocebada_registro_'+payload.parcela.id_poligono.replace(/[^\w-]/g,'_')+'.json';
  document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function setupNewParcelForm(){
  const form=$('new-parcel-form'),button=$('download-request'),state=$('new-state');
  // Defensa ante cambios manuales en el DOM y scripts de terceros.
  [...state.options].forEach(option=>{if(option.value && !ALLOWED_STATES.includes(option.value))option.remove();});
  const resetDownload=()=>{validatedRequest=null;button.hidden=true;};
  form.addEventListener('input',()=>{resetDownload();showFeedback('','');});
  form.addEventListener('change',()=>{resetDownload();showFeedback('','');});
  form.addEventListener('reset',()=>{resetDownload();$('feature-feedback').textContent='Opcional: una fila con características. Hasta 128 KB. No se envía a ningún servidor.';showFeedback('','');});
  button.addEventListener('click',()=>{if(validatedRequest)downloadJSON(validatedRequest);});
  form.addEventListener('submit',async event=>{
    event.preventDefault();resetDownload();
    const submit=form.querySelector('[type="submit"]');
    if(!form.reportValidity()) {showFeedback('Revisa los campos obligatorios y sus rangos antes de continuar.');return;}
    const estado=state.value;
    if(!ALLOWED_STATES.includes(estado)){showFeedback('Fuera del área del proyecto: solo se permiten Hidalgo, Puebla y Tlaxcala.');return;}
    submit.disabled=true;submit.textContent='Validando coordenadas…';showFeedback('Consultando límites estatales para verificar la ubicación.','info');
    try{
      const id=$('new-id').value.trim().toUpperCase();
      if(!/^[A-Z0-9_-]{3,64}$/.test(id))throw new Error('Utiliza un identificador de 3 a 64 caracteres: letras, números, guiones o guion bajo.');
      const municipio=$('new-municipality').value.trim();
      if(municipio.length<2)throw new Error('Escribe un municipio válido.');
      const superficie_ha=numberValue('new-area',{min:0.000001});
      const latitud=numberValue('new-lat',{min:-90,max:90});
      const longitud=numberValue('new-lon',{min:-180,max:180});
      const boundaries=await getStateBoundaries();
      const matched=ALLOWED_STATES.filter(s=>locationIsInGeometry(longitud,latitud,boundaries[s]));
      if(!matched.includes(estado)){
        const detail=matched.length?`Las coordenadas parecen corresponder a ${matched.join(' o ')}, no a ${estado}.`:'Las coordenadas están fuera de Hidalgo, Puebla y Tlaxcala, según los límites de referencia.';
        throw new Error('Registro rechazado. '+detail+' Corrige la ubicación o el estado.');
      }
      const optional={
        ndvi_promedio:numberValue('new-ndvi',{optional:true,min:-1,max:1}),
        precipitacion_acumulada_mm:numberValue('new-rain',{optional:true,min:0}),
        temperatura_media_c:numberValue('new-temp',{optional:true,min:-100,max:70}),
        elevacion_m:numberValue('new-elevation',{optional:true,min:-500,max:10000})
      };
      const features=await readFeatureFile();
      // Las características adjuntas pueden contener columnas adicionales, pero no alteran el estado verificado.
      validatedRequest={
        tipo:'solicitud_de_estudio_sin_prediccion',
        modelo_referencia:'Local04D — alcance actual: 59 objetivos fijos de FIRA',
        unidad:'toneladas por hectarea',
        parcela:{id_poligono:id,estado,municipio,superficie_ha,latitud,longitud,ciclo: $('new-cycle').value,modalidad:$('new-water').value||null,...optional},
        validacion:{estados_permitidos:[...ALLOWED_STATES],geografia:'ubicacion dentro del poligono de referencia del estado seleccionado',coordenadas:'EPSG:4326 WGS84',fuente_geometria:STATES_GEOJSON_URL,estado_verificado:true},
        caracteristicas_adicionales:features,
        prediccion:null,
        motivo_sin_prediccion:'El pipeline Local04D no tiene una API verificada para nuevas parcelas arbitrarias.'
      };
      button.hidden=false;showFeedback('Ubicación validada: '+estado+'. Registro preparado correctamente. Puedes descargar el JSON. Aún no se calculó ningún rendimiento para esta nueva parcela.','success');
    }catch(error){resetDownload();showFeedback(error.message||'No fue posible comprobar la parcela. Intenta de nuevo.');}
    finally{submit.disabled=false;submit.innerHTML='Validar y preparar solicitud <span aria-hidden="true">↗</span>';}
  });
}

async function start(){
  // La navegación compartida funciona en todas las páginas.
  setupMobileNavigation();
  if($('new-parcel-form'))setupNewParcelForm();
  const hasDashboard=Boolean($('predictions-table'));
  const hasValidation=Boolean($('chart07')&&$('chart08'));
  if(!hasDashboard&&!hasValidation)return;
  try{
    const [p,m07,m08]=await Promise.all([csv('predictions.csv'),csv('checkpoint07_summary.csv'),csv('checkpoint08_summary.csv')]);
    const records=p.map(row=>({id:String(row.ID_POLIGONO||'').trim(),y:Number(row.RENDIMIENTO_T_HA)})).sort((a,b)=>a.id.localeCompare(b.id,'es'));
    if(records.length!==59||new Set(records.map(r=>r.id)).size!==59||records.some(r=>!/^AGC_\d+$/.test(r.id)||!Number.isFinite(r.y)||r.y<0))
      throw new Error('El CSV de predicciones no contiene exactamente 59 parcelas válidas.');
    if(m07.length!==13||m08.length!==3||
      Math.abs(Number(m07.find(r=>r.model==='Local04D')?.rmse_pooled)-0.49574142871073495)>1e-10||
      Math.abs(Number(m08.find(r=>r.model==='Local04D_frozen')?.rmse_pooled)-0.4819355585746856)>1e-10)
      throw new Error('Las métricas no coinciden con el repositorio fuente.');
    if(hasDashboard)showPredictions(records);
    if(hasValidation){
      drawComparison('chart07',m07,['Local04D','Local07','Prithvi07','catboost'],'Local04D');
      drawComparison('chart08',m08,['Local04D_frozen','Local04D_nested','Local07_nested'],'Local04D_frozen');
    }
  }catch(error){
    console.error(error);
    if($('data-status'))$('data-status').textContent='Error al cargar datos: '+error.message+' Usa un servidor local.';
    if($('predictions-table')){
      const tr=node('tr'),td=node('td','','Error de carga.');td.colSpan=3;tr.append(td);$('predictions-table').replaceChildren(tr);
    }
    if($('chart07'))$('chart07').textContent='No se pudo cargar la validación.';
    if($('chart08'))$('chart08').textContent='No se pudo cargar la validación.';
  }
}
if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',start);
// Exponer solo funciones puras para pruebas Node; no altera la web.
if(typeof module!=='undefined'&&module.exports)module.exports={parseCSV,insideRing,insidePolygon,locationIsInGeometry,ALLOWED_STATES};
