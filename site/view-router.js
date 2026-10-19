/* GeoCebada · cinco vistas centradas en preguntas reales del visitante.
   Los datos, gráficos y secciones históricas originales permanecen intactos. */
(function () {
  'use strict';
  const labels = Object.freeze({
    modelo: '¿Cómo funciona el modelo?',
    resultados: 'Resultados',
    confianza: '¿Qué tanta confianza merece?',
    preguntas: 'Preguntas frecuentes'
  });
  const aliases = Object.freeze({
    problema:'inicio',historia:'modelo',calculo:'modelo',pruebas:'resultados',
    hhi:'resultados',parcelas:'confianza'
  });
  const byAnchor = Object.freeze({
    'mapa-interactivo':'inicio',
    universo:'inicio',pregunta:'inicio',
    historia:'modelo','variables-detalle':'modelo','preparacion-datos':'modelo',lluvia:'modelo',vecinos:'modelo',arquitectura:'modelo','entrenamiento-modelo':'modelo','datos-faltantes':'modelo',
    'de-donde-sale':'modelo',
    evidencia:'resultados',significancia:'resultados',componentes:'resultados',
    'retirar-hhi':'resultados','modelo-compacto':'resultados',distribucion:'resultados','diagnostico-residuos':'resultados',
    cobertura:'confianza',limites:'confianza',
    'preguntas-tecnicas':'preguntas',
    'faq-consulta':'preguntas','faq-modelo':'preguntas',
    'faq-resultados':'preguntas','faq-validacion':'preguntas'
  });
  const search=new URLSearchParams(window.location.search);
  const requested=search.get('vista');
  const fragment=decodeURIComponent(window.location.hash.slice(1));
  const view=requested && Object.hasOwn(labels,requested) ? requested
    : requested && Object.hasOwn(aliases,requested) ? aliases[requested]
    : !requested && Object.hasOwn(byAnchor,fragment) ? byAnchor[fragment]
    : 'inicio';
  document.documentElement.dataset.geoVista=view;
  if(view!=='inicio') document.title=labels[view]+' · GeoCebada';
  document.addEventListener('DOMContentLoaded',function(){
    const heading=document.getElementById('geo-view-name');
    if(heading && labels[view]) heading.textContent=labels[view];
    document.querySelectorAll('#nav-links a').forEach(function(anchor){
      const link=new URL(anchor.href,window.location.href);
      const target=link.searchParams.get('vista')||'inicio';
      if(target===view) anchor.setAttribute('aria-current','page');
      else anchor.removeAttribute('aria-current');
    });
    // Restituye la posición al ancla incluso con CSS de rutas cargado inicialmente.
    if(fragment){
      const section=document.getElementById(fragment);
      if(section) requestAnimationFrame(()=>section.scrollIntoView({block:'start'}));
    }
  });
})();