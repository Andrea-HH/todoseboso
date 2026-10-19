/* Native GeoCebada geographic viewer. Independent presentation, grounded in
 * Andrea-HH's authorized published parcel data; no iframe or copied UI.
 * Polygon geometry and observed/predicted values are never synthesized. */
"use strict";
(() => {
  const root=document.getElementById("geoc-native-map");
  if(!root)return;
  const upstream="https://raw.githubusercontent.com/Andrea-HH/todoseboso/95f942177d47f48bb966417ea9d19cf25fff4ced/site/explorador/data/";
  const byId=id=>document.getElementById(id);
  const state=byId("geo-state");
  const parcel=byId("geo-parcel");
  const status=byId("geo-status");
  const details=byId("geo-details");
  const visible=byId("geo-visible");
  const legend=byId("geo-legend");
  const buttons=[...root.querySelectorAll("[data-geo-base]")];
  let map=null,tiles=null,base="light",records=[],shown=[],polygons=null,pins=null;
  let selected=null,pinMap=new Map(),polygonMap=new Map();
  const titles={
    "clim_official_2025__prec__season_sum":["Precipitación de abril a octubre","mm"],
    "clim_official_2025__tmin__season_mean":["Temperatura mínima media","°C"],
    "clim_official_2025__tmax__season_mean":["Temperatura máxima media","°C"],
    "chirps_daily_2025__season_sum":["Precipitación diaria acumulada","mm"],
    "chirps_daily_2025__rain_days":["Días con precipitación","días"],
    "chirps_daily_2025__max_dry_spell_days":["Racha seca máxima","días"],
    "cem15__elevation__mean":["Elevación media","m s. n. m."]
  };
  const norm=v=>String(v??"").trim().toUpperCase();
  const val=(v,places=2)=>Number(v).toLocaleString("es-MX",{maximumFractionDigits:places,minimumFractionDigits:places});
  const say=(message,bad=false)=>{status.textContent=message;status.dataset.error=String(bad);};
  const el=(tag,cls,textValue)=>{
    const n=document.createElement(tag);
    if(cls)n.className=cls;
    if(textValue!==undefined)n.textContent=textValue;
    return n;
  };
  const fetchData=async path=>{
    const r=await fetch(upstream+path,{cache:"force-cache"});
    if(!r.ok)throw Error("No se pudo leer "+path+" ("+r.status+").");
    return r;
  };
  const csv=async (path,expected)=>{
    const text=await (await fetchData(path)).text();
    const lines=text.trim().split(/\r?\n/);
    if(lines.shift()?.replace(/^\uFEFF/,"").trim()!=="ID_POLIGONO,RENDIMIENTO_T_HA")
      throw Error("Encabezados inválidos en "+path);
    const result=new Map();
    for(const row of lines){
      const fields=row.trim().split(",");
      if(fields.length!==2)throw Error("Fila incompleta en "+path);
      const [id,v]=fields,n=Number(v);
      if(!/^AGC_\d+$/.test(id)||result.has(id)||v.trim()===""||!Number.isFinite(n)||n<0)
        throw Error("Rendimiento o identificador inválido en "+path);
      result.set(id,n);
    }
    if(result.size!==expected)throw Error("Se esperaban "+expected+" registros en "+path);
    return result;
  };
  const openGeoJSON=async ()=>{
    if(typeof DecompressionStream==="undefined")
      throw Error("El navegador no permite descomprimir datos geográficos.");
    const response=await fetchData("mapa_publico.json.gz");
    if(!response.body)throw Error("No se recibió la capa geográfica.");
    const body=response.body.pipeThrough(new DecompressionStream("gzip"));
    const dataset=JSON.parse(await new Response(body).text());
    if(dataset.schema!=="geocebada-map-public-1"||
      dataset.geometry?.type!=="FeatureCollection"||
      !Array.isArray(dataset.geometry.features)||
      dataset.geometry.features.length!==197)
      throw Error("La capa no contiene las 197 geometrías verificadas.");
    if(!Array.isArray(dataset.climate)||dataset.climate.length!==197)
      throw Error("La capa climática no contiene las 197 parcelas.");
    return dataset;
  };
  const loadLeaflet=()=>new Promise((resolve,reject)=>{
    if(window.L?.map){resolve(window.L);return;}
    const script=document.createElement("script");
    script.src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.async=true;
    script.onload=()=>window.L?.map?resolve(window.L):reject(Error("Leaflet no está disponible."));
    script.onerror=()=>reject(Error("No se pudo cargar la biblioteca del mapa."));
    document.head.appendChild(script);
  });
  const labelMap=()=>({
    light:window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
      maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}),
    satellite:window.L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",{
      maxZoom:18,attribution:"Tiles &copy; Esri, Maxar, Earthstar Geographics"})
  });
  const color=r=>r.split==="PREDICCION"?"#a68b62":"#637a6b";
  const styleOf=r=>({
    color:selected===r.id?"#263a32":color(r),
    weight:selected===r.id?3.5:1.8,fillColor:color(r),
    fillOpacity:selected===r.id?0.32:0.09
  });
  const markerStyle=r=>({
    radius:selected===r.id?8:5.2,
    color:"#fff",weight:2.1,fillColor:color(r),fillOpacity:0.95
  });
  const included=r=>state.value==="all"||r.state===state.value;
  const clear=(target)=>target.replaceChildren();
  function renderDetails(){
    clear(details);
    const r=records.find(item=>item.id===selected);
    if(!r){
      details.append(el("p","geo-muted","Seleccione una parcela para consultar su ubicación, el rendimiento reportado o la estimación archivada, y las variables ambientales disponibles."));
      return;
    }
    details.append(el("p","geo-article-tag",r.split==="ENTRENAMIENTO"?"RENDIMIENTO REPORTADO":"ESTIMACIÓN ARCHIVADA"),
      el("h4","",r.id));
    const dl=el("dl","geo-values");
    const datum=(term,value)=>{
      dl.append(el("dt","",term),el("dd","",value));
    };
    datum("Estado",r.state);
    datum("Municipio",r.municipio);
    datum("Conjunto",r.split==="ENTRENAMIENTO"?"Entrenamiento":"Por estimar");
    datum("Superficie",r.area!=null?val(r.area)+" ha":"No disponible");
    datum("Rendimiento",r.value!=null?val(r.value,3)+" t/ha":"No disponible");
    details.append(dl);
    if(r.split==="PREDICCION")
      details.append(el("p","geo-muted","Estimación de Reference26 archivada por el equipo; no corresponde a una cosecha observada ni necesariamente al próximo ajuste."));
    else details.append(el("p","geo-muted","Rendimiento de entrenamiento reportado; puede contener incertidumbre de registro."));
    const fields=el("dl","geo-climate-values");
    let count=0;
    for(const [name,[label,unit]] of Object.entries(titles)){
      const n=Number(r.climate[name]);
      if(r.climate[name]!==null&&r.climate[name]!==undefined&&Number.isFinite(n)){
        fields.append(el("dt","",label),el("dd","",val(n)+" "+unit));count++;
      }
    }
    if(count){details.append(el("h5","","Indicadores ambientales"),fields);}
  }
  function refresh(){
    shown=records.filter(included);
    const ids=new Set(shown.map(r=>r.id));
    if(selected&&!ids.has(selected))selected=null;
    clear(parcel);
    parcel.append(el("option","","Seleccionar parcela"));
    parcel.firstChild.value="";
    for(const r of shown){
      const option=el("option","",r.id+" · "+r.state);
      option.value=r.id;parcel.append(option);
    }
    parcel.value=selected||"";
    visible.textContent=shown.length+" de 197 parcelas visibles";
    for(const r of records){
      const enabled=ids.has(r.id);
      const polygon=polygonMap.get(r.id);
      const marker=pinMap.get(r.id);
      // Remove excluded layers entirely: visually transparent polygons should
      // not intercept clicks or keyboard focus in a filtered geographic view.
      if(polygon){
        if(enabled){
          if(!polygons.hasLayer(polygon))polygons.addLayer(polygon);
          polygon.setStyle(styleOf(r));
        }else if(polygons.hasLayer(polygon))polygons.removeLayer(polygon);
      }
      if(marker){
        if(enabled){
          if(!pins.hasLayer(marker))pins.addLayer(marker);
          marker.setStyle(markerStyle(r));
        }else if(pins.hasLayer(marker))pins.removeLayer(marker);
      }
    }
    renderDetails();
  }
  function choose(id){
    const r=records.find(row=>row.id===id&&included(row));
    if(!r)return;
    selected=id;
    refresh();
    const layer=polygonMap.get(id);
    if(layer)map.flyTo(layer.getBounds().getCenter(),Math.max(13,map.getZoom()),{duration:0.65});
  }
  async function start(){
    say("Cargando geometrías y datos de las 197 parcelas…");
    const [L,dataset,pred,actual]=await Promise.all([
      loadLeaflet(),openGeoJSON(),csv("predictions.csv",59),csv("training_yields.csv",138)]);
    const features=dataset.geometry.features;
    const climate=new Map(dataset.climate.map(row=>[norm(row.ID_POLIGONO),row]));
    if(climate.size!==197)throw Error("La capa climática contiene IDs repetidos.");
    const used=new Set();
    for(const f of features){
      const p=f.properties||{},id=norm(p.ID_POLIGONO||p.ID_POLIGON);
      const split=norm(p.CONJUNTO||p.conjunto);
      const st=String(p.Estado||p.estado||"").trim();
      if(!/^AGC_\d+$/.test(id)||used.has(id)||
        !["Hidalgo","Puebla","Tlaxcala"].includes(st)||
        !["ENTRENAMIENTO","PREDICCION"].includes(split)||
        !["Polygon","MultiPolygon"].includes(f.geometry?.type))
        throw Error("La capa contiene una parcela duplicada o inválida.");
      used.add(id);
      const observed=actual.get(id),estimated=pred.get(id);
      if((split==="ENTRENAMIENTO")!==(observed!==undefined)||
         (split==="PREDICCION")!==(estimated!==undefined)||
         !climate.has(id))throw Error("Los datos de una parcela no concuerdan entre fuentes.");
      const a=p["área_ha"]??p.area_ha??p.AREA_HA;
      records.push({id,split,state:st,municipio:String(p.Municipio||p.municipio||"No disponible"),
        area:a==null||a===""?null:Number(a),value:split==="PREDICCION"?estimated:observed,
        climate:climate.get(id),geometry:f});
    }
    if(records.filter(x=>x.split==="ENTRENAMIENTO").length!==138||
       records.filter(x=>x.split==="PREDICCION").length!==59)
      throw Error("La división 138/59 no coincide con la fuente publicada.");
    map=L.map("geo-leaflet-map",{zoomControl:true,scrollWheelZoom:false,attributionControl:true});
    const types=labelMap();
    tiles=types.light.addTo(map);
    const bounds=L.latLngBounds([]);
    const groups=L.featureGroup().addTo(map);
    polygons=groups;
    pins=L.layerGroup().addTo(map);
    for(const r of records){
      const layer=L.geoJSON(r.geometry,{style:styleOf(r)});
      layer.addTo(groups);
      layer.eachLayer(p=>{
        p.on("click",()=>choose(r.id));
        p.bindTooltip(r.id+" · "+r.state);
      });
      polygonMap.set(r.id,layer);
      const center=layer.getBounds().getCenter();
      if(!Number.isFinite(center.lat)||!Number.isFinite(center.lng)||
          center.lat<16||center.lat>23||center.lng< -101||center.lng> -95)
        throw Error("Coordenadas incompatibles con la región.");
      bounds.extend(layer.getBounds());
      const pin=L.circleMarker(center,markerStyle(r)).addTo(pins);
      pin.on("click",()=>choose(r.id));
      pin.bindTooltip(r.id,{direction:"top"});
      pinMap.set(r.id,pin);
    }
    map.fitBounds(bounds.pad(0.08),{animate:false});
    const layers=types;
    const chooseBasemap=name=>{
      if(name===base)return;
      map.removeLayer(tiles);
      tiles=layers[name].addTo(map);
      base=name;
      for(const b of buttons){
        const active=b.dataset.geoBase===name;
        b.setAttribute("aria-pressed",String(active));
      }
    };
    buttons.forEach(button=>button.addEventListener("click",()=>chooseBasemap(button.dataset.geoBase)));
    byId("geo-reset").addEventListener("click",()=>{
      selected=null;state.value="all";refresh();map.fitBounds(bounds.pad(0.08));
    });
    state.addEventListener("change",()=>{
      refresh();
      const selectedBounds=L.latLngBounds([]);
      shown.forEach(r=>selectedBounds.extend(polygonMap.get(r.id).getBounds()));
      if(selectedBounds.isValid())map.fitBounds(selectedBounds.pad(.12));
    });
    parcel.addEventListener("change",()=>parcel.value?choose(parcel.value):((selected=null),refresh()));
    state.disabled=false;parcel.disabled=false;
    refresh();
    legend.textContent="Verde grisáceo: entrenamiento · Arena: parcelas por estimar";
    say("197 polígonos georreferenciados · 138 observados · 59 por estimar.");
    window.setTimeout(()=>map.invalidateSize({animate:false}),160);
  }
  start().catch(error=>{
    say("El visor no pudo cargar los datos originales: "+error.message,true);
    details.textContent="La información original sigue disponible en el mapa de Andrea-HH, mediante el enlace «Abrir versión original».";
    console.error("GeoCebada visor:",error);
  });
})();
