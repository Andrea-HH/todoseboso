/* Gentle, progressive reveal. No content is removed, rewritten or
   hidden if JavaScript fails, IntersectionObserver is absent or reduced
   motion is requested. Reveal only once as the reader scrolls downward. */
"use strict";
(() => {
  const preference=window.matchMedia("(prefers-reduced-motion: reduce)");
  if(preference.matches || typeof IntersectionObserver!=="function") return;

  const selectors=[
    ".reading-guide-head", ".index-introduction", ".chapter-card",
    ".section > .shell > .section-heading",
    ".process-grid article", ".tech-intro article",
    ".ensemble-flow", ".ensemble-selector", ".model-visual",
    ".model-formula", ".loocv-panel", ".pred59-viz",
    ".pred59-summary", ".real-data-figure", ".collaborator-map-frame"
  ];
  const targets=[...new Set(document.querySelectorAll(selectors.join(",")))];
  let lastY=window.scrollY;
  let movingDown=true;
  const markVisible=(element,animate) => {
    element.classList.remove("scroll-reveal-pending");
    if(animate)element.classList.add("scroll-reveal-visible");
  };
  const observer=new IntersectionObserver(entries => {
    for(const entry of entries){
      if(!entry.isIntersecting)continue;
      markVisible(entry.target,movingDown);
      observer.unobserve(entry.target);
    }
  },{rootMargin:"0px 0px -28px 0px",threshold:0.08});

  for(const element of targets){
    // The first screen remains visible immediately, and hidden tabs are
    // never animated before their own JavaScript makes them accessible.
    if(!element.getClientRects().length ||
       element.getBoundingClientRect().top < window.innerHeight*0.91)continue;
    element.classList.add("scroll-reveal-pending");
    observer.observe(element);
  }
  window.addEventListener("scroll",() => {
    const next=window.scrollY;
    if(Math.abs(next-lastY)>3)movingDown=next>lastY;
    lastY=next;
  },{passive:true});
  // Keyboard and direct anchors must always be readable immediately.
  document.addEventListener("focusin",event => {
    const target=event.target.closest(".scroll-reveal-pending");
    if(target){markVisible(target,false);observer.unobserve(target);}
  });
  window.addEventListener("hashchange",() => {
    const id=decodeURIComponent(window.location.hash.slice(1));
    const target=id&&document.getElementById(id);
    if(!target)return;
    const pending=target.closest(".scroll-reveal-pending");
    if(pending){markVisible(pending,false);observer.unobserve(pending);}
  });
  // User preference can change while the page is already open.
  const cancel=() => {
    if(!preference.matches)return;
    observer.disconnect();
    for(const element of targets)markVisible(element,false);
  };
  if(preference.addEventListener)preference.addEventListener("change",cancel);
  else if(preference.addListener)preference.addListener(cancel);
})();
