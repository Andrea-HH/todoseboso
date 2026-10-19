/* Explorador espacial GeoCebada: geometría auténtica local; sin fabricar localizaciones.
 * Los rendimientos de las 59 parcelas se leen de la tabla canónica de Local04D.
 */
(() => {
  'use strict';
  const STATES = ['Hidalgo', 'Puebla', 'Tlaxcala'];
  const BOUNDARIES = 'https://raw.githubusercontent.com/strotgen/mexico-leaflet/master/states.geojson';
  const $ = (id) => document.getElementById(id);
  const number = (value, places = 3) => Number(value).toLocaleString('es-MX', {minimumFractionDigits: places, maximumFractionDigits: places});
  const removeAccents = (s) => String(s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();
  const stateLabel = (s) => STATES.find(v => removeAccents(v) === removeAccents(s)) || null;
  const splitLabel = (value) => {
    const s = removeAccents(value).toUpperCase();
    return s === 'ENTRENAMIENTO' || s === 'PREDICCION' ? s : null;
  };
  const identify = (properties) => String(properties.ID_POLIGONO ?? properties.ID_POLIGON ?? '').trim().toUpperCase();
  const allowedGeometry = new Set(['Polygon', 'MultiPolygon']);

  function parseOfficialGeoJSON(doc) {
    if (!doc || doc.type !== 'FeatureCollection' || !Array.isArray(doc.features)) throw new Error('El archivo debe ser un GeoJSON FeatureCollection de parcelas.');
    // RFC 7946: geometría en lon/lat WGS84. Un CRS declarado distinto necesita reproyección antes de cargar.
    const crs = doc.crs?.properties?.name;
    if (crs && !/CRS84|EPSG(?::|::)4326|urn:ogc:def:crs:EPSG::4326/i.test(crs)) throw new Error('El GeoJSON no usa WGS84/EPSG:4326. Reproyecta antes de cargar.');
    if (!doc.features.length || doc.features.length > 250) throw new Error('Número inesperado de parcelas (se esperan hasta 197).');
    const ids = new Set(), features = [];
    for (const feature of doc.features) {
      if (feature.type !== 'Feature' || !allowedGeometry.has(feature.geometry?.type)) throw new Error('Las parcelas deben tener geometría Polygon o MultiPolygon.');
      const p = feature.properties || {}, id = identify(p);
      if (!/^AGC_\d+$/.test(id) || ids.has(id)) throw new Error('ID_POLIGON/ID_POLIGONO inválido o repetido: ' + (id || '(vacío)'));
      ids.add(id);
      const estado = stateLabel(p.Estado ?? p.estado);
      if (!estado) throw new Error(`La parcela ${id} no tiene un estado permitido (Hidalgo, Puebla o Tlaxcala).`);
      const split = splitLabel(p.CONJUNTO ?? p.conjunto);
      if (!split) throw new Error(`La parcela ${id} no tiene un CONJUNTO válido.`);
      const visit = (coords) => {
        if (typeof coords[0] === 'number') {
          const lon = coords[0], lat = coords[1];
          if (!Number.isFinite(lon) || !Number.isFinite(lat) || lon < -180 || lon > 180 || lat < -90 || lat > 90) throw new Error(`Coordenadas inválidas en ${id}.`);
          if (lon < -101 || lon > -95 || lat < 16 || lat > 23) throw new Error(`Las coordenadas de ${id} parecen no corresponder a la región: revisa el CRS.`);
        } else coords.forEach(visit);
      };
      visit(feature.geometry.coordinates);
      features.push({...feature, properties: {...p, ID_POLIGONO: id, Estado: estado, CONJUNTO: split}});
    }
    const train = features.filter(f => f.properties.CONJUNTO === 'ENTRENAMIENTO').length;
    const pred = features.length - train;
    if (features.length === 197 && (train !== 138 || pred !== 59)) throw new Error('La clasificación de las 197 parcelas no coincide con el desglose oficial 138/59.');
    return {type: 'FeatureCollection', features};
  }

  async function loadOfficialPredictions() {
    const res = await fetch('./data/predictions.csv', {cache:'no-store'});
    if (!res.ok) throw new Error('No se pudieron consultar las 59 predicciones.');
    const lines = (await res.text()).trim().split(/\r?\n/);
    if (lines.shift()?.replace(/^\uFEFF/, '').trim() !== 'ID_POLIGONO,RENDIMIENTO_T_HA') throw new Error('El CSV no coincide con el contrato de predicciones.');
    const map = new Map();
    for (const line of lines) {
      const [id, val] = line.trim().split(',');
      const n = Number(val);
      if (!/^AGC_\d+$/.test(id) || map.has(id) || !Number.isFinite(n) || n < 0) throw new Error('El archivo de predicciones contiene un registro inválido.');
      map.set(id, n);
    }
    if (map.size !== 59) throw new Error('Se esperaban exactamente 59 parcelas de predicción.');
    return map;
  }

  function recordsForMap(doc, predictions) {
    return doc.features.map(f => {
      const p = f.properties;
      const pred = predictions.get(p.ID_POLIGONO);
      if ((p.CONJUNTO === 'PREDICCION') !== (pred !== undefined)) throw new Error(`Conjunto de ${p.ID_POLIGONO} incompatible con las 59 predicciones finales.`);
      const rawArea = p['área_ha'] ?? p.area_ha ?? p.AREA_HA;
      const area = rawArea == null || rawArea === '' ? null : Number(rawArea);
      return {id:p.ID_POLIGONO, split:p.CONJUNTO, estado:p.Estado, municipio:String(p.Municipio ?? p.municipio ?? 'No disponible'), area:Number.isFinite(area) ? area : null, pred, feature:f};
    });
  }


  // El foco muestra exclusivamente el contorno sin sombrear la fotografía.
  function parcelVisualStyle(rec, included, selected, focused){
    const color=rec.split==='PREDICCION'?'#f0bc56':'#39b790';
    if(focused){
      return selected&&included
        ? {color,weight:4.5,opacity:1,fillColor:color,fillOpacity:0,interactive:true}
        : {color,weight:0,opacity:0,fillOpacity:0,interactive:false};
    }
    return {color,weight:selected?3.4:1.8,opacity:included?1:0,
      fillColor:color,fillOpacity:included?.11:0,interactive:included};
  }
  // Solo las columnas climáticas documentadas, sin acceder a rendimientos observados.
  const CLIMATE_FIELDS=[
    {key:'clim_official_2025__prec__season_sum',label:'Precipitación abr–oct',unit:'mm',source:'CHIRPS mensual'},
    {key:'clim_official_2025__tmin__season_mean',label:'Temperatura mínima media',unit:'°C',source:'CHIRTS-ERA5'},
    {key:'clim_official_2025__tmax__season_mean',label:'Temperatura máxima media',unit:'°C',source:'CHIRTS-ERA5'},
    {key:'chirps_daily_2025__season_sum',label:'Precipitación diaria acumulada',unit:'mm',source:'CHIRPS diario'},
    {key:'chirps_daily_2025__rain_days',label:'Días con lluvia',unit:'días',source:'CHIRPS diario'},
    {key:'chirps_daily_2025__max_dry_spell_days',label:'Racha seca máxima',unit:'días',source:'CHIRPS diario'},
    {key:'cem15__elevation__mean',label:'Elevación media',unit:'m s. n. m.',source:'INEGI CEM'}
  ];
  function parseClimateDataset(items){
    const rows=Array.isArray(items)?items:items?.rows;
    if(!Array.isArray(rows)||!rows.length||rows.length>250)
      throw new Error('Se requieren hasta 197 registros por parcela, en un CSV o JSON válido.');
    const out=new Map();let anyValue=false;
    for(const row of rows){
      const id=String(row.ID_POLIGONO??'').trim().toUpperCase();
      if(!/^AGC_\d+$/.test(id)||out.has(id))throw new Error('Identificador climático inválido o repetido: '+id);
      const values={};
      for(const f of CLIMATE_FIELDS){
        const raw=row[f.key];
        if(raw===null||raw===undefined||String(raw).trim()==='')continue;
        const value=Number(String(raw).trim());
        if(!Number.isFinite(value))continue;
        values[f.key]=value;anyValue=true;
      }
      out.set(id,values);
    }
    if(!anyValue)throw new Error('El archivo no tiene columnas climáticas compatibles con la tabla de características GeoCebada.');
    return out;
  }
  function parseClimateCSV(text){
    const lines=String(text).replace(/^\uFEFF/,'').split(/\r?\n/).filter(line=>line.trim());
    if(lines.length<2)throw new Error('El CSV climático está vacío.');
    function splitLine(line){
      const result=[];let value='',quoted=false;
      for(let i=0;i<line.length;i++){
        const char=line[i];
        if(char==='"'){
          if(quoted&&line[i+1]==='"'){value+='"';i++;}
          else quoted=!quoted;
        }else if(char===','&&!quoted){result.push(value);value='';}
        else value+=char;
      }
      result.push(value);
      return result;
    }
    const headers=splitLine(lines[0]).map(x=>x.trim());
    const wanted=['ID_POLIGONO',...CLIMATE_FIELDS.map(x=>x.key)];
    const positions=wanted.map(col=>headers.indexOf(col));
    if(positions[0]<0)throw new Error('El CSV necesita la columna ID_POLIGONO.');
    return parseClimateDataset(lines.slice(1).map(line=>{
      const cols=splitLine(line),row={};
      wanted.forEach((field,i)=>{if(positions[i]>=0)row[field]=cols[positions[i]]??'';});
      return row;
    }));
  }

  async function launchMap() {
    const notice = $('map-notice');
    const info = (message) => {notice.textContent=message;notice.hidden=false;};
    if (typeof window.L === 'undefined') {info('No se pudo abrir Leaflet. Verifica tu conexión a internet y recarga.');return;}
    const L = window.L;
    // El visor no debe capturar el scroll de toda la página ni salir de la región del reto.
    const regionBounds = L.latLngBounds([[17.2,-100.5],[22.0,-96.1]]);
    const map = L.map('parcel-map', {
      zoomControl:false, scrollWheelZoom:false, preferCanvas:true,
      zoomAnimation:false, fadeAnimation:false, inertia:false,
      minZoom:7, maxZoom:17, maxBounds:regionBounds, maxBoundsViscosity:1
    }).setView([19.73,-98.43],9);
    // Mantener + / − lejos de la barra fija inferior y del encabezado del mapa.
    L.control.zoom({
      position:'topright', zoomInTitle:'Acercar el mapa',
      zoomOutTitle:'Alejar el mapa'
    }).addTo(map);
    // Selección de un punto concreto: un clic solo acerca si el usuario activó el modo.
    const zoomAreaButton = $('map-zoom-area');
    const zoomGuideText = $('map-zoom-guide-text');
    let choosingZoomPoint = false;
    const setZoomChoice = (active) => {
      choosingZoomPoint = active;
      zoomAreaButton.setAttribute('aria-pressed', String(active));
      zoomAreaButton.textContent = active ? 'Cancelar elección' : 'Elegir zona ↗';
      zoomGuideText.textContent = active
        ? 'Haz clic donde quieres acercarte · Esc para cancelar'
        : 'Doble clic para acercar · usa + y − arriba a la derecha';
      map.getContainer().classList.toggle('zoom-pick-mode', active);
    };
    const focusZoomPoint = (latlng) => {
      if (!choosingZoomPoint) return false;
      setZoomChoice(false);
      map.setView(latlng, Math.min(map.getMaxZoom(), Math.max(map.getZoom() + 3, 13)), {animate:false});
      return true;
    };
    zoomAreaButton.addEventListener('click', () => setZoomChoice(!choosingZoomPoint));
    map.on('click', event => focusZoomPoint(event.latlng));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && choosingZoomPoint) setZoomChoice(false);
    });
    const tileOptions = {updateWhenIdle:true, updateWhenZooming:false, keepBuffer:1,
      detectRetina:false, maxZoom:17};
    const imagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      ...tileOptions, maxNativeZoom:17,
      attribution:'Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, y la comunidad GIS'
    });
    const streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      ...tileOptions, maxNativeZoom:17,
      attribution:'© OpenStreetMap contributors'
    });
    const toggleTiles = $('map-lite-toggle');
    const modeLabel = $('map-mode-label');
    let lightMode = false;
    let failedTiles = 0;
    const setLightMode = (enabled, automatic = false) => {
      if (lightMode === enabled) return;
      map.removeLayer(enabled ? imagery : streets);
      map.addLayer(enabled ? streets : imagery);
      lightMode = enabled;
      modeLabel.textContent = enabled ? 'Mapa ligero · OpenStreetMap' : 'Vista satelital · Esri';
      toggleTiles.textContent = enabled ? 'Ver satélite' : 'Mapa ligero';
      toggleTiles.setAttribute('aria-pressed', String(enabled));
      if (automatic) info('La capa satelital no respondió bien. Activamos el mapa ligero; puedes volver al satélite cuando quieras.');
    };
    imagery.on('tileerror', () => {
      failedTiles += 1;
      if (failedTiles >= 6 && !lightMode) setLightMode(true, true);
    });
    map.addLayer(imagery);
    toggleTiles.addEventListener('click', () => {
      failedTiles = 0;
      setLightMode(!lightMode);
    });
    const bounds = L.latLngBounds([[18.0,-99.9],[21.5,-97.0]]);
    const resetViewButton=$('map-reset-view');
    const stateStyles={Hidalgo:'#d8d78e',Puebla:'#a2c9ab',Tlaxcala:'#d9b17c'};
    fetch(BOUNDARIES).then(r=>{if(!r.ok)throw new Error('Límites estatales no disponibles.');return r.json();}).then(j=>{
      const selected=j.features.filter(f=>STATES.includes(f.properties?.state_name));
      if(selected.length!==3)return;
      L.geoJSON({type:'FeatureCollection',features:selected}, {
        interactive:false,style:f=>({color:stateStyles[f.properties.state_name],weight:1.8,fillOpacity:.04,dashArray:'6 5'})
      }).addTo(map);
    }).catch(()=>{});

    let predictions;
    try {predictions=await loadOfficialPredictions();}
    catch(e){info('Error en el CSV de predicciones: '+e.message);return;}

    let records=[...predictions].map(([id,pred])=>({id,pred,split:'PREDICCION',estado:null,municipio:null,area:null,feature:null})).sort((a,b)=>a.id.localeCompare(b.id));
    let hasGeometry=false, polygonLayers=null, layerById=new Map(), currentId=null, activeSplit='TODOS';
    let focusedOnly=false;
    const climateValues=new Map();
    const byId = new Map(records.map(r=>[r.id,r]));
    // Puntos extraídos de geometrías auténticas: nunca inventar coordenadas.
    const pinPane = map.createPane('parcel-pin-pane');
    pinPane.style.zIndex = '625';
    const pinRenderer = L.svg({pane:'parcel-pin-pane'});
    const pinLayers = L.layerGroup().addTo(map);
    const pinById = new Map();
    const pinsButton = $('map-toggle-pins');
    const emptyState = $('map-empty-state');
    const emptyNote = emptyState.querySelector('p');
    let pinsVisible = true;
    pinsButton.disabled = true; // Los pines no existen hasta cargar geometrías.
    pinsButton.setAttribute('aria-disabled','true');
    const state=$('map-state'), search=$('map-search'), select=$('map-parcel-select');
    state.disabled=true;
    state.title='Para filtrar por estado es necesario disponer de las ubicaciones geográficas.';
    const controls=[...document.querySelectorAll('[data-map-split]')];
    const match=(r)=>{
      if(activeSplit!=='TODOS'&&r.split!==activeSplit)return false;
      if(state.value!=='TODOS'&&r.estado!==state.value)return false;
      if(search.value.trim()&&!r.id.includes(search.value.trim().toUpperCase()))return false;
      return true;
    };

    const climateMetrics=$('map-climate-metrics'), climateStatus=$('map-climate-status');
    const updateClimate=(id)=>{
      climateMetrics.replaceChildren();
      const measures=id?climateValues.get(id):null;
      if(!id){climateStatus.textContent='Selecciona una parcela para consultar sus factores climáticos.';return;}
      if(!measures){climateStatus.textContent='Factores agroclimáticos no disponibles para '+id+' en esta sesión.';return;}
      let shown=0;
      for(const item of CLIMATE_FIELDS){
        const value=measures[item.key];
        if(value===undefined)continue;
        const card=document.createElement('div');card.className='geo-climate-metric';
        const label=document.createElement('span');label.textContent=item.label;
        const data=document.createElement('strong');data.textContent=number(value,item.unit==='días'?0:1)+' '+item.unit;
        const source=document.createElement('small');source.textContent=item.source+' · 2025';
        card.append(label,data,source);climateMetrics.append(card);shown++;
      }
      climateStatus.textContent=shown
        ? 'Valores extraídos de la tabla GeoCebada · abril–octubre de 2025. Son datos retrospectivos, no pronósticos.'
        : 'No hay mediciones agroclimáticas disponibles para esta parcela.';
    };
    const fillSelection=(r)=>{
      const el=$('map-selected-detail');el.replaceChildren();
      const label=document.createElement('span');label.textContent='PARCELA SELECCIONADA';
      const title=document.createElement('h3');title.textContent=r.id;
      const type=document.createElement('p');type.className='geo-detail-type';
      type.textContent=r.split==='PREDICCION'?'Predicción · Local04D':'Entrenamiento · parcela de referencia';
      el.append(label,title,type);
      const dl=document.createElement('dl');
      const info=[['Estado',r.estado||'No disponible'],
        ['Municipio',r.municipio||'No disponible'],
        ['Superficie',r.area===null?'No disponible':number(r.area,2)+' ha']];
      for(const [name,value] of info){
        const dt=document.createElement('dt'),dd=document.createElement('dd');
        dt.textContent=name;dd.textContent=value;dl.append(dt,dd);
      }
      el.append(dl);
      if(r.pred!==undefined){
        const block=document.createElement('div');block.className='geo-yield';
        const caption=document.createElement('span');caption.textContent='RENDIMIENTO ESTIMADO';
        const figure=document.createElement('strong');figure.textContent=number(r.pred)+' t/ha';
        const note=document.createElement('small');note.textContent='Estimación del modelo Local04D · no es rendimiento observado.';
        block.append(caption,figure,note);el.append(block);
      }else{
        const note=document.createElement('p');note.className='geo-yield-explain';
        note.textContent='Parcela de entrenamiento. Este visor no publica su rendimiento observado.';
        el.append(note);
      }
      updateClimate(r.id);
    };
    const refreshPins=()=>{
      pinById.forEach((marker,id)=>{
        const rec=byId.get(id);
        if(!rec)return;
        const show=pinsVisible && !focusedOnly && match(rec), mounted=pinLayers.hasLayer(marker);
        if(show && !mounted)pinLayers.addLayer(marker);
        else if(!show && mounted)pinLayers.removeLayer(marker);
        const selected=id===currentId;
        if(show && marker._pinSelected!==selected)
          marker.setStyle({radius:selected?9:6,weight:selected?3:2,fillOpacity:selected?1:.93});
        marker._pinSelected=selected;
      });
    };
    pinsButton.addEventListener('click',()=>{
      pinsVisible=!pinsVisible;
      pinsButton.setAttribute('aria-pressed',String(pinsVisible));
      pinsButton.textContent=pinsVisible?'Ocultar pines':'Mostrar pines';
      refreshPins();
    });
    const redraw=()=>{
      const visible=records.filter(match);
      $('map-visible-count').textContent=hasGeometry?`${visible.length} de ${records.length} parcelas georreferenciadas visibles`:`Ubicaciones geográficas no disponibles en esta sesión. Puedes consultar las 59 estimaciones por ID.`;
      if(hasGeometry){$('map-total').textContent=records.length;$('map-training').textContent=records.filter(x=>x.split==='ENTRENAMIENTO').length;$('map-prediction').textContent=records.filter(x=>x.split==='PREDICCION').length;}
      controls.forEach(btn=>{const yes=btn.dataset.mapSplit===activeSplit;btn.classList.toggle('active',yes);btn.setAttribute('aria-pressed',String(yes));});
      select.replaceChildren();const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=visible.length?'Selecciona una parcela...':'Sin coincidencias';select.append(placeholder);
      visible.sort((a,b)=>a.id.localeCompare(b.id)).forEach(r=>{const o=document.createElement('option');o.value=r.id;o.textContent=r.id+' · '+(r.split==='PREDICCION'?'por predecir':'entrenamiento');select.append(o);});
      if(visible.some(r=>r.id===currentId)) select.value=currentId;
      if(polygonLayers){
        polygonLayers.eachLayer(layer=>{
          const r=layer.record;
          const included=match(r);
          const selected=r.id===currentId;
          const visualKey=`${focusedOnly?1:0}:${included?1:0}:${selected?1:0}`;
          if(layer._geoStyleKey!==visualKey){
            layer._geoStyleKey=visualKey;
            const visual=parcelVisualStyle(r,included,selected,focusedOnly);
            layer.setStyle(visual);
            layer.options.interactive=visual.interactive;
            if(!visual.interactive)layer.closePopup();
          }
        });
        if(focusedOnly && currentId){
          const selectedLayer=layerById.get(currentId);
          if(selectedLayer)selectedLayer.bringToFront();
        }
      }
      resetViewButton.textContent=focusedOnly?'Ver todas las parcelas ↶':'Ver tres estados ↗';
      refreshPins();
    };
    const pick=(id)=>{
      const r=byId.get(id);if(!r)return;
      // Al seleccionar una parcela se mantiene solo su borde, sin relleno ni pines.
      currentId=id;focusedOnly=hasGeometry;
      fillSelection(r);redraw();
      const layer=layerById.get(id);
      if(layer && match(r)){map.fitBounds(layer.getBounds(),{maxZoom:14,padding:[50,50],animate:false});layer.bringToFront();}
      else if(!hasGeometry){info('Rendimiento disponible. La ubicación de esta parcela no está disponible en esta sesión.');}
    };
    resetViewButton.addEventListener('click',()=>{
      currentId=null;focusedOnly=false;activeSplit='TODOS';
      state.value='TODOS';search.value='';
      // Regresar al mapa completo siempre vuelve a activar los pines auténticos.
      pinsVisible=true;
      pinsButton.setAttribute('aria-pressed','true');
      pinsButton.textContent='Ocultar pines';
      if(choosingZoomPoint)setZoomChoice(false);
      $('map-selected-detail').replaceChildren();
      const detail=$('map-selected-detail');
      const heading=document.createElement('h3');heading.textContent='Selecciona una parcela';
      const hint=document.createElement('p');
      hint.textContent='Toca un pin verde o dorado para enfocar su contorno y consultar su ficha.';
      detail.append(heading,hint);
      updateClimate(null);
      redraw();
      const frame=polygonLayers?polygonLayers.getBounds():bounds;
      map.fitBounds(frame,{maxZoom:polygonLayers?12:9,padding:[38,38],animate:false});
    });
    select.addEventListener('change',()=>{if(select.value)pick(select.value)});
    let searchDelay;
    search.addEventListener('input',()=>{
      clearTimeout(searchDelay);
      searchDelay=setTimeout(redraw,160);
    });
    state.addEventListener('change',()=>{currentId=null;focusedOnly=false;updateClimate(null);redraw();});
    controls.forEach(btn=>btn.addEventListener('click',()=>{activeSplit=btn.dataset.mapSplit;currentId=null;focusedOnly=false;updateClimate(null);redraw();}));
    // Las mediciones locales se integran sin botones ni subida de datos a otros servicios.
    async function receiveClimateText(text,filename){
      const rows=filename.toLowerCase().endsWith('.json')
        ? parseClimateDataset(JSON.parse(text))
        : parseClimateCSV(text);
      climateValues.clear();
      rows.forEach((value,id)=>climateValues.set(id,value));
      updateClimate(currentId);
    }
    if(['localhost','127.0.0.1'].includes(window.location.hostname)){
      (async()=>{
        for(const name of ['clima_parcelas.json','parcel_features_competition.csv']){
          try{
            const res=await fetch('./data/private/'+name,{cache:'no-store'});
            if(!res.ok)continue;
            await receiveClimateText(await res.text(),name);
            break;
          }catch(e){console.warn('No se pudieron consultar factores locales de GeoCebada:',e);}
        }
      })();
    }
    updateClimate(null);

    function renderGeometry(raw){
      const doc=parseOfficialGeoJSON(raw);
      const mapped=recordsForMap(doc,predictions);
      // Reemplazar solo después de validar todos los registros.
      if(polygonLayers)map.removeLayer(polygonLayers);
      pinLayers.clearLayers();pinById.clear();layerById.clear();
      records=mapped;hasGeometry=true;currentId=null;focusedOnly=false;updateClimate(null);
      byId.clear();mapped.forEach(r=>byId.set(r.id,r));
      polygonLayers=L.geoJSON(doc,{
        style:f=>({
          color:f.properties.CONJUNTO==='PREDICCION'?'#eec475':'#6fe5bd',
          weight:2.2,fillColor:f.properties.CONJUNTO==='PREDICCION'?'#d4ab5b':'#1ca77a',
          fillOpacity:.24
        }),
        onEachFeature:(feature,layer)=>{
          const rec=byId.get(feature.properties.ID_POLIGONO);
          layer.record=rec;layerById.set(rec.id,layer);
          layer.on('click',event=>{
            if(focusZoomPoint(event.latlng))return;
            if(focusedOnly && rec.id!==currentId)return;
            if(match(rec))pick(rec.id);
          });
          layer.bindTooltip(rec.id+' · '+(rec.split==='PREDICCION'?'Predicción':'Entrenamiento'),{sticky:true,direction:'top'});
          // Los pines se crean después de añadir los polígonos al mapa.
          // getCenter() requiere que la capa ya tenga un mapa asociado.
        }
      }).addTo(map);

      // IMPORTANTE: Leaflet invoca onEachFeature ANTES de .addTo(map).
      // Polygon.getCenter() lanza "Must add layer to map before using getCenter()"
      // si se ejecuta dentro de onEachFeature. Ahora todas las capas están montadas.
      polygonLayers.eachLayer(layer=>{
        const rec=layer.record;
        if(!layer._map) throw new Error('La parcela debe añadirse al mapa antes de crear su pin.');
        const position=layer.getCenter();
        const predicted=rec.split==='PREDICCION';
        const pin=L.circleMarker(position,{
          renderer:pinRenderer,radius:6,color:'#ffffff',weight:2,
          fillColor:predicted?'#d7a647':'#15976e',
          fillOpacity:.93,interactive:true,bubblingMouseEvents:false
        });
        pin.bindTooltip(rec.id+' · '+(predicted?'Predicción':'Entrenamiento'),{direction:'top',offset:[0,-10]});
        pin.on('click',event=>{
          if(focusZoomPoint(event.latlng))return;
          if(match(rec))pick(rec.id);
        });
        pinById.set(rec.id,pin);
        pinLayers.addLayer(pin);
      });
      map.fitBounds(polygonLayers.getBounds(),{maxZoom:12,padding:[38,38],animate:false});
      notice.hidden=true;
      emptyState.hidden=true;
      state.disabled=false;
      state.removeAttribute('title');
      pinsButton.disabled=false;
      pinsButton.setAttribute('aria-disabled','false');
      pinsButton.textContent=pinsVisible?'Ocultar pines':'Mostrar pines';
      redraw();
    }
    notice.hidden=true;redraw();
    // Se usan las geometrías privadas locales cuando están disponibles en desarrollo.
    // Únicamente servidor de desarrollo local; jamás cargar geometría privada en GitHub Pages.
    if(['localhost','127.0.0.1'].includes(window.location.hostname)){
      fetch('./data/private/parcelas.geojson',{cache:'no-store'})
        .then(r=>r.ok?r.json():null)
        .then(doc=>{
          if(!doc||hasGeometry)return;
          try{renderGeometry(doc);}
          catch(e){
            emptyNote.textContent='No se pudo visualizar la capa geográfica de esta versión.';
            console.warn('GeoJSON local no válido:',e);
          }
        }).catch(()=>{});
    }
    setTimeout(()=>map.invalidateSize({pan:false,animate:false}),250);
  }
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>{launchMap().catch(e=>{const n=$('map-notice');n.textContent='No se pudo iniciar el mapa: '+e.message;n.hidden=false;console.error(e);});});
  if(typeof module!=='undefined'&&module.exports)module.exports={parseOfficialGeoJSON,recordsForMap,stateLabel,splitLabel,parcelVisualStyle,parseClimateDataset,parseClimateCSV};
})();
