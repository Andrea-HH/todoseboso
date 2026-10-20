"""Comprueba integridad: contenido Heri + portada Andrea + datos originales.

Esta batería no altera ni vuelve a entrenar ningún modelo.
"""
import csv
import io
import json
import re
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
SOURCE=SITE/"fuente-heri"

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.assets=[]
        self.links=[]
        self.sections=[]
    def handle_starttag(self,tag,attributes):
        a=dict(attributes)
        if a.get("id"):
            self.ids.append(a["id"])
            if tag=="section":
                self.sections.append(a["id"])
        if tag=="script" and a.get("src"):
            self.assets.append(a["src"])
        if tag=="link" and a.get("href","").startswith("./"):
            self.assets.append(a["href"].split("?",1)[0])
        if tag=="a" and a.get("href","").startswith("./investigacion.html?"):
            self.links.append(a["href"])

class ResearchIntegrityTest(unittest.TestCase):
    def test_full_original_sections_and_figures_are_preserved(self):
        original=Document()
        research=Document()
        original.feed((SOURCE/"index.html").read_text(encoding="utf-8"))
        research.feed((SOURCE/"investigacion.html").read_text(encoding="utf-8"))
        self.assertEqual((set(original.sections)-{"mapa-interactivo","recorrido"})|{"datos-reales","predicciones-59"},set(research.sections))
        self.assertEqual(len(original.sections),len(research.sections))
        for indicator in ("pred59-summary","pred59-examples","real-rainfall","real-ndvi",
                          "cluster-list","feature-rows","performance-chart",
                          "r3-comparison","association-chart","distribution-quantiles",
                          "r26-moran-chart","r26-geary-chart","r26-variogram-chart",
                          "r26-bootstrap-chart"):
            self.assertIn(indicator,research.ids)
        self.assertEqual(len(research.ids),len(set(research.ids)))
        for relative in research.assets:
            self.assertTrue((SOURCE/relative).is_file(),relative)
        text=(SOURCE/"investigacion.html").read_text(encoding="utf-8")
        self.assertNotIn("FUENTE ORIGINAL · CONTENIDO ÍNTEGRO",text)
        self.assertNotIn("geo-heri-disclosure",text)
        self.assertNotIn("browser_inference.js",text)
        self.assertIn("research-59-archive.js",text)
        self.assertNotIn("predictions59.js",text)
        self.assertNotIn('id="recorrido"',text)
        self.assertNotIn("ÍNDICE DE LA INVESTIGACIÓN",text)
        self.assertIn('data-research-intro="sabemos"',text)
        self.assertIn('id="datos-reales"',text)
        self.assertIn('href="./investigacion.html?vista=sabemos"',text)
        self.assertNotIn('class="hero model-hero"',text)
        self.assertNotIn('id="mapa-interactivo"',text)
        self.assertNotIn("native_map.js",text)
        self.assertIn('class="research-original-diagram"',text)
        self.assertIn("24 parcelas cercanas",text)
        self.assertIn('href="../assets/favicon-trigo.png"',text)
        self.assertNotIn('class="pred59-explorer"',text)
        self.assertNotIn('id="pred59-rows"',text)
        self.assertNotIn('id="pred59-detail"',text)
        self.assertNotIn('id="pred59-plot"',text)
        self.assertNotIn('class="pred59-viz"',text)
        self.assertNotIn("¿Cómo se distribuyen las estimaciones?",text)
        self.assertNotIn('id="pred59-search"',text)
        self.assertNotIn('id="pred59-state"',text)
        self.assertNotIn("Consultar las 59 predicciones",text)
        self.assertEqual(text.count('id="predicciones-59"'),1)
        for plot in ("parcel-coverage","real-rainfall","real-ndvi",
                     "performance-chart","association-chart","r3-comparison",
                     "distribution-quantiles","r26-moran-chart","r26-geary-chart",
                     "r26-variogram-chart","r26-bootstrap-chart"):
            self.assertEqual(text.count('id="'+plot+'"'),1,plot)

    def test_routes_cover_all_original_chapters(self):
        style=(SOURCE/"andrea-research.css").read_text(encoding="utf-8")
        for item in ("sabemos","modelo","resultados","confianza","preguntas"):
            self.assertIn('data-research-vista="'+item+'"',style)
        for id_ in ("ensamble","datos","auditoria","variables","datos-reales","preparacion",
                    "arquitectura","geologia","faltantes","ajuste","resultados",
                    "pruebas","limites","preguntas","estadisticas-finales","predicciones-59"):
            self.assertIn("#"+id_,style)
        self.assertIn('html[data-research-vista="modelo"] #contenido>section#variables',style)
        self.assertNotIn('html[data-research-vista="sabemos"] #contenido>section#variables',style)
        # Colores muestreados directamente de las dos imágenes enviadas.
        self.assertIn('--geo-header:#F3EBD9;--geo-alternate:#FBF8F1',style)
        self.assertIn('--cream:#FBF8F1',style)
        self.assertIn('.research-chapter-heading{background:var(--geo-header);',style)
        self.assertIn('html[data-research-vista] #research-chapter-heading{background-color:var(--geo-header)!important}',style)
        self.assertIn('alternancia-uniforme-20261019-1611',(SOURCE/"investigacion.html").read_text(encoding="utf-8"))
        self.assertIn('#research-chapter-heading.research-chapter-heading{background:#F3EBD9!important;', (SOURCE/"investigacion.html").read_text(encoding="utf-8"))
        self.assertNotIn('background:#F5EBD7!important',style)
        self.assertNotIn('nth-of-type(even){background:',style)
        self.assertNotIn('html[data-research-vista] body{background:',style)
        # La alternancia debe respetar cada página visible, no el orden de
        # secciones ocultas en el documento común.
        backgrounds = style.split('/* Alternancia validada con las dos muestras exactas de la usuaria. */')[1]
        light, dark = backgrounds.split('{background:var(--geo-alternate)!important}',1)
        dark = dark.split('{background:var(--geo-header)!important}',1)[0]
        order = {
            "sabemos": ("datos","preparacion","datos-reales"),
            "modelo": ("ensamble","variables","arquitectura","geologia","faltantes","ajuste"),
            "resultados": ("predicciones-59","resultados","pruebas"),
            "confianza": ("limites","estadisticas-finales"),
            "preguntas": ("preguntas",)
        }
        pattern=r'html\[data-research-vista="([^"]+)"\] #contenido > section#([\w-]+)'
        light_pairs=set(re.findall(pattern,light))
        dark_pairs=set(re.findall(pattern,dark))
        for vista, ids in order.items():
            for number,id_ in enumerate(ids):
                pair=(vista,id_)
                self.assertIn(pair,light_pairs if number % 2 == 0 else dark_pairs)
                self.assertNotIn(pair,dark_pairs if number % 2 == 0 else light_pairs)

        research=(SOURCE/"investigacion.html").read_text(encoding="utf-8")
        self.assertIn('vista=modelo#variables',research)
        self.assertNotIn('vista=sabemos#variables',research)
        routes=[
            ("sabemos","modelo"),
            ("modelo","resultados"),
            ("resultados","confianza"),
            ("confianza","preguntas"),
        ]
        for current,next_view in routes:
            self.assertIn(
                f'<div data-next-view="{current}"><span>SIGUIENTE PÁGINA</span>'
                f'<a href="./investigacion.html?vista={next_view}">',
                research)
        self.assertIn(
            '<div data-next-view="preguntas"><span>SIGUIENTE PÁGINA</span>'
            '<a href="../index.html">',research)
        self.assertEqual(research.count('SIGUIENTE PÁGINA'),5)
        self.assertNotIn('id="pred59-detail"',research)
        prediction_js=(SOURCE/"research-59-archive.js").read_text(encoding="utf-8")
        self.assertNotIn("get('pred59-detail')",prediction_js)
        self.assertIn("pred59-summary",research)
        self.assertNotIn("pred59-plot",prediction_js)
        original=(SITE/"index.html").read_text(encoding="utf-8")
        self.assertIn('id="geoc-andrea-hero-frame"',original)
        self.assertIn('id="geoc-andrea-controls-frame"',original)
        self.assertIn('id="geoc-andrea-panel-frame"',original)
        self.assertIn('id="geo-paleta-portada"',original)
        self.assertIn('section.hero {\n      background: #F3EBD9 !important;',original)
        self.assertIn('section.geoc-andrea-map {\n      background: #F3EBD9 !important;',original)
        research_html=(SOURCE/"investigacion.html").read_text(encoding="utf-8")
        self.assertIn('id="geo-header-color"',research_html)
        for view,ids in order.items():
            for i,id_ in enumerate(ids):
                fragment=f'html[data-research-vista="{view}"] #contenido > section#{id_}'
                desired='#FBF8F1' if i%2==0 else '#F3EBD9'
                color_rule=research_html.split(fragment)[1].split('}',1)[0]
                # La regla final puede agrupar varios selectores.
                self.assertIn(desired,color_rule)
        self.assertIn("fuente-heri/investigacion.html?vista=sabemos",original)
        self.assertIn("fuente-heri/investigacion.html?vista=modelo",original)
        self.assertIn("¿Qué sabemos?",original)
        self.assertIn('<span>SIGUIENTE TEMA</span><a href="./fuente-heri/investigacion.html?vista=sabemos">',original)
        self.assertIn("fuente-heri/investigacion.html?vista=resultados",original)

    def test_public_dataset_audit_is_integrated_without_duplication(self):
        research=(SOURCE/"investigacion.html").read_text(encoding="utf-8")
        stylesheet=(SOURCE/"andrea-research.css").read_text(encoding="utf-8")
        router=(SOURCE/"research-page.js").read_text(encoding="utf-8")
        document=Document()
        document.feed(research)
        for key in ("auditoria","preparacion","datos-reales","real-rainfall","real-ndvi"):
            self.assertEqual(document.ids.count(key),1,key)
        self.assertEqual(document.sections.count("preparacion"),1)
        self.assertLess(research.index('id="datos"'),research.index('id="auditoria"'))
        self.assertLess(research.index('id="auditoria"'),research.index('id="preparacion"'))
        self.assertLess(research.index('id="preparacion"'),research.index('id="datos-reales"'))
        self.assertIn('vista=sabemos#preparacion',research)
        self.assertNotIn('vista=modelo#preparacion',research)
        self.assertIn('preparacion:"sabemos"',router)
        self.assertIn('auditoria:"sabemos"',router)
        self.assertIn('html[data-research-vista="sabemos"] #contenido>section#preparacion',stylesheet)
        self.assertNotIn('html[data-research-vista="modelo"] #contenido>section#preparacion',stylesheet)
        self.assertIn('AUDITORÍA DEL CONJUNTO DE DATOS',research)
        self.assertIn('medias calculadas únicamente con el entrenamiento',research)
        self.assertNotIn('sustituyen por medianas del',research)
        self.assertIn('reference26_selected_statistical_audit.json',research)
        for file in ("real_charts.json","final_model.json","reference26_residuals.json","submission59_final.csv"):
            self.assertTrue((SOURCE/"data"/file).is_file(),file)
        chart=json.loads((SOURCE/"data/real_charts.json").read_text(encoding="utf-8"))
        for kind in ("rainfall","ndvi"):
            self.assertEqual([r["month"] for r in chart[kind]["months"]],list(range(4,11)))
            self.assertEqual([r["n"] for r in chart[kind]["months"]],[197]*7)
        residual=json.loads((SOURCE/"data/reference26_residuals.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(residual["diagnostics"]["normality"]["shapiro_p"],1.401988e-7,places=12)
        self.assertAlmostEqual(residual["diagnostics"]["variance"]["koenker_bp_p"],0.400797,places=6)

    def test_historical_59_is_preserved_and_final_59_is_verified(self):
        csv_content=(SITE/"explorador/data/predictions.csv").read_text(encoding="utf-8")
        rows=list(csv.DictReader(io.StringIO(csv_content)))
        self.assertEqual(len(rows),59)
        ids=[r["ID_POLIGONO"] for r in rows]
        self.assertEqual(len(set(ids)),59)
        values=[float(r["RENDIMIENTO_T_HA"]) for r in rows]
        self.assertAlmostEqual(sum(values)/59,3.956432328667021,places=7)
        # El archivo histórico sigue disponible pero ya no se presenta como entrega final.
        script=(SOURCE/"research-59-archive.js").read_text(encoding="utf-8")
        final_csv=(SOURCE/"data/submission59_final.csv").read_text(encoding="utf-8")
        final_rows=list(csv.DictReader(io.StringIO(final_csv)))
        self.assertEqual(len(final_rows),59)
        self.assertEqual(set(ids),{r["ID_POLIGONO"] for r in final_rows})
        final_values=sorted(float(r["RENDIMIENTO_T_HA"]) for r in final_rows)
        meta=json.loads((SOURCE/"data/final_model.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["final_fit_selected"],"robust26_3_neighbors_supported_0p25")
        aggregate=meta["prediction59_aggregate"]
        self.assertAlmostEqual(sum(final_values)/59,aggregate["selected_mean"],places=8)
        self.assertAlmostEqual(final_values[0],aggregate["selected_min"],places=8)
        self.assertAlmostEqual(final_values[29],aggregate["selected_median"],places=8)
        self.assertAlmostEqual(final_values[-1],aggregate["selected_max"],places=8)
        self.assertAlmostEqual(sum(final_values)/59,3.9572238505778996,places=8)
        self.assertEqual(len(meta["loocv"]),7)
        self.assertEqual(sum(meta["selection_4fold_counts"].values()),138)
        self.assertIn('readText("./data/submission59_final.csv")',script)
        self.assertIn('readText("./data/final_model.json")',script)
        self.assertIn("../explorador/data/mapa_publico.json.gz",script)
        self.assertIn("final-strategies",script)
        result_html=(SOURCE/"investigacion.html").read_text(encoding="utf-8")
        self.assertIn("PREDICCIONES FINALES · 59 PARCELAS",result_html)
        self.assertIn("RESULTADOS DEFINITIVOS DEL EXPERIMENTO · 138 LOOCV",result_html)
        self.assertIn("0.462418",result_html)
        self.assertIn("0.462892",result_html)
        self.assertIn("0.331956",result_html)
        self.assertIn('id="final59-distribution"',result_html)
        self.assertEqual(result_html.count('id="final-strategies"'),1)
        self.assertEqual(result_html.count('id="pred59-summary"'),1)
        self.assertNotIn("pred59-detail",script)
        self.assertNotIn("pred59-rows",script)
        self.assertNotIn("pred59-state",script)
        self.assertNotIn("pred59-plot",script)
        self.assertNotIn("pred59-search",script)
        self.assertNotIn("Math.random(",script)
        self.assertNotIn("!window.GeoCebadaPredictions",script)

if __name__=="__main__":
    unittest.main()
