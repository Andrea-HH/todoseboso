/* Public browser runner: show only frozen Reference26 estimates after
 * numerical parity against the 59 original Python predictions. */
"use strict";
(() => {
  async function initialize(){
    try{
      const response=await fetch("./data/reference26_runtime.json",{cache:"no-store"});
      if(!response.ok)throw Error("El archivo de Reference26 verificado no está disponible.");
      const data=await response.json();
      const parity=window.Reference26Browser.parity(data,1e-7);
      if(parity.tested!==59)throw Error("La comprobación no cubre las 59 parcelas.");
      window.GeoCebadaPredictions.render(data);
      window.GeoCebadaEnsemble.registerReference(data);
    }catch(error){
      window.GeoCebadaPredictions.unavailable(error.message);
      window.GeoCebadaEnsemble.rejectReference(error.message);
      console.error("Estimaciones archivadas no disponibles:",error);
    }
  }
  initialize();
})();
