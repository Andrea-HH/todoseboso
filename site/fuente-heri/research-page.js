/* Navegación de capítulos. Los datos y las gráficas originales no se alteran. */
(function(){
  "use strict";
  const supported=["sabemos","modelo","resultados","confianza","preguntas"];
  const params=new URLSearchParams(window.location.search);
  let view=params.get("vista");
  if(!supported.includes(view))view="modelo";
  document.documentElement.dataset.researchVista=view;
  document.documentElement.lang="es";
  document.title=({sabemos:"¿Qué sabemos?",modelo:"¿Cómo funciona el modelo?",resultados:"Resultados",confianza:"¿Qué tanta confianza merece?",preguntas:"Preguntas frecuentes"})[view]+" · GeoCebada";
  const crossSection={
    datos:"sabemos","datos-reales":"sabemos",auditoria:"sabemos",preparacion:"sabemos",variables:"modelo",
    ensamble:"modelo",arquitectura:"modelo",geologia:"modelo",faltantes:"modelo",ajuste:"modelo",
    "predicciones-59":"resultados",resultados:"resultados",pruebas:"resultados",
    "estadisticas-finales":"confianza",limites:"confianza",preguntas:"preguntas"
  };
  function groupFor(id){
    if(id.startsWith("pred59-"))return "resultados";
    if(id.startsWith("r26-"))return "confianza";
    if(crossSection[id])return crossSection[id];
    const target=document.getElementById(id);
    if(!target)return null;
    const section=target.closest("main > section");
    return section?.id?crossSection[section.id]||null:null;
  }
  function routeHash(){
    const id=decodeURIComponent(location.hash.slice(1));
    if(!id)return;
    if(id==="mapa-interactivo"){location.replace("../index.html#mapa-interactivo");return;}
    if(id==="recorrido"){location.replace("./investigacion.html?vista=sabemos#datos");return;}
    const group=groupFor(id);
    if(group&&group!==view){
      location.replace("./investigacion.html?vista="+group+"#"+encodeURIComponent(id));return;
    }
    const node=document.getElementById(id);
    if(node)requestAnimationFrame(()=>node.scrollIntoView({block:"start",behavior:"instant"}));
  }
  document.addEventListener("DOMContentLoaded",()=>{
    document.querySelectorAll(".andrea-nav-items a").forEach(a=>{
      try{
        const url=new URL(a.href,location.href);
        if(url.searchParams.get("vista")===view)a.setAttribute("aria-current","page");
      }catch{}
    });
    const menu=document.getElementById("andrea-nav-dropdown");
    document.addEventListener("click",e=>{
      if(menu?.open&&!menu.contains(e.target))menu.open=false;
      if(e.target.closest(".andrea-nav-items a"))menu.open=false;
    });
    document.addEventListener("keydown",e=>{if(e.key==="Escape"&&menu){menu.open=false;menu.querySelector("summary")?.focus()}});
    routeHash();
  });
  window.addEventListener("hashchange",routeHash);
})();