/* GeoCebada: rutas de las seis ventanas dentro del mismo sitio.
   No altera datos, textos, gráficas ni métodos de cálculo de Heri. */
(function () {
  'use strict';
  const labels = Object.freeze({
    historia: '¿Cómo llegamos aquí?',
    calculo: '¿Cómo se calcula?',
    pruebas: '¿Qué muestran las pruebas?',
    hhi: 'El experimento sin HHI',
    parcelas: 'Las 59 parcelas',
    preguntas: 'Preguntas'
  });
  // Compatibilidad con enlaces antiguos a secciones de una sola página.
  const byAnchor = Object.freeze({
    pregunta:'historia',historia:'historia',arquitectura:'historia',componentes:'historia',
    'de-donde-sale':'calculo',
    significancia:'pruebas',evidencia:'pruebas',distribucion:'pruebas',
    'retirar-hhi':'hhi',
    cobertura:'parcelas',limites:'parcelas',
    'preguntas-tecnicas':'preguntas'
  });
  const params = new URLSearchParams(window.location.search);
  const requested = params.get('vista');
  const fragment = decodeURIComponent(window.location.hash.slice(1));
  const view = Object.hasOwn(labels,requested) ? requested
    : !requested && Object.hasOwn(byAnchor,fragment) ? byAnchor[fragment]
    : 'inicio';
  document.documentElement.dataset.geoVista = view;
  if (view !== 'inicio') {
    // No cargar los tres mapas ocultos en páginas que solo contienen investigación.
    // Los navegadores respetan loading=lazy para iframes ocultos.
    document.title = labels[view] + ' · GeoCebada';
  }
  document.addEventListener('DOMContentLoaded',function(){
    const heading=document.getElementById('geo-view-name');
    if (heading && labels[view]) heading.textContent=labels[view];
    document.querySelectorAll('#nav-links a').forEach(function(anchor){
      const target=new URL(anchor.href,window.location.href).searchParams.get('vista');
      if (target===view) anchor.setAttribute('aria-current','page');
      else anchor.removeAttribute('aria-current');
    });
  });
})();