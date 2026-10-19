/* GeoCebada: carga por demanda de las secciones originales de Heri. */
(() => {'use strict';
const available=new Set(['recorrido','ensamble','datos','variables','preparacion','arquitectura','geologia','faltantes','ajuste','resultados','pruebas','limites','preguntas','estadisticas-finales','mapa-interactivo']);
document.querySelectorAll('details[data-geo-heri-section]').forEach(d=>{
 d.addEventListener('toggle',()=>{
   if(!d.open||d.querySelector('iframe'))return;
   const key=d.getAttribute('data-geo-heri-section');if(!available.has(key))return;
   const slot=d.querySelector('.geo-heri-frame-slot');if(!slot)return;
   const iframe=document.createElement('iframe');
   iframe.className='geo-heri-native-frame';
   iframe.title='Contenido original de Heri: '+key;
   iframe.src='./fuente-heri/index.html?seccion='+encodeURIComponent(key);
   iframe.loading='lazy';
   iframe.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
   slot.replaceChildren(iframe);
 });
});
window.addEventListener('message',event=>{
 if(event.origin!==location.origin||event.data?.type!=='geo-fuente-altura')return;
 const iframe=[...document.querySelectorAll('iframe.geo-heri-native-frame')].find(f=>f.contentWindow===event.source);
 if(!iframe||iframe.closest('details')?.getAttribute('data-geo-heri-section')!==event.data.section)return;
 const height=Number(event.data.height);
 if(Number.isFinite(height)&&height>0)iframe.style.height=Math.max(300,Math.min(24000,height))+'px';
});
})();
