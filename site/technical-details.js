/* Única interacción editorial nueva: la tabla de las 26 entradas técnicas publicadas por Heri. */
(() => {'use strict';
const target=document.getElementById('geo-tech-features');
if(!target)return;
function node(tag,text){const e=document.createElement(tag);if(text!=null)e.textContent=String(text);return e}
function table(group){
 const wrap=node('div');wrap.className='geo-tech-table-wrap';const grid=node('table');grid.className='geo-tech-table';
 const head=node('thead'),tr=node('tr');
 ['Variable e identificador','Cómo se obtiene','Cómo interpretarla'].forEach(s=>tr.append(node('th',s)));
 head.append(tr);grid.append(head);const body=node('tbody');
 group.features.forEach(item=>{const row=node('tr');[item.number+'. '+item.name+' · '+item.code,item.how,item.interpret].forEach(x=>row.append(node('td',x)));body.append(row)});
 grid.append(body);wrap.append(grid);return wrap;
}
fetch('./data/reference26_features.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('archivo de variables no disponible');return r.json()}).then(data=>{
 if(data.schema_version!==1||data.features.length!==5||data.features.reduce((n,g)=>n+g.features.length,0)!==26)throw Error('datos incompatibles');
 target.replaceChildren();data.features.forEach((g,i)=>{const detail=node('details');if(i===0)detail.open=true;detail.append(node('summary',g.count+' · '+g.title),node('p',g.why),table(g));target.append(detail)});
}).catch(err=>target.replaceChildren(node('p','El inventario no se pudo cargar: '+err.message+'. Comprueba los archivos técnicos disponibles desde el enlace de procedencia.')));
})();
