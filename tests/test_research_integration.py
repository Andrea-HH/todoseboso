"""Comprueba integridad: contenido Heri + portada Andrea + datos originales.

Esta batería no altera ni vuelve a entrenar ningún modelo.
"""
import csv
import io
import json
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
            self.assets.append(a["href"])
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
        for indicator in ("pred59-plot","pred59-examples","real-rainfall","real-ndvi",
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
        for id_ in ("ensamble","datos","variables","datos-reales","preparacion",
                    "arquitectura","geologia","faltantes","ajuste","resultados",
                    "pruebas","limites","preguntas","estadisticas-finales","predicciones-59"):
            self.assertIn("#"+id_,style)
        self.assertIn('html[data-research-vista="modelo"] #contenido>section#variables',style)
        self.assertNotIn('html[data-research-vista="sabemos"] #contenido>section#variables',style)
        self.assertIn('--cream:#FCF8F0',style)
        self.assertIn('.research-chapter-heading{background:#EFE4D3;',style)
        self.assertIn('html[data-research-vista] #research-chapter-heading{background-color:#EFE4D3!important}',style)
        self.assertIn('andrea-research.css?v=encabezado-20261019-2', (SOURCE/"investigacion.html").read_text(encoding="utf-8"))
        self.assertIn('background:#F5EBD7!important',style)
        self.assertNotIn('background:#EFE3D0',style)
        self.assertNotIn('html[data-research-vista] body{background:',style)
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
        self.assertIn("role','img'",prediction_js)
        original=(SITE/"index.html").read_text(encoding="utf-8")
        self.assertIn('id="geoc-andrea-hero-frame"',original)
        self.assertIn('id="geoc-andrea-controls-frame"',original)
        self.assertIn('id="geoc-andrea-panel-frame"',original)
        self.assertIn("fuente-heri/investigacion.html?vista=sabemos",original)
        self.assertIn("fuente-heri/investigacion.html?vista=modelo",original)
        self.assertIn("¿Qué sabemos?",original)
        self.assertIn('<span>SIGUIENTE TEMA</span><a href="./fuente-heri/investigacion.html?vista=sabemos">',original)
        self.assertIn("fuente-heri/investigacion.html?vista=resultados",original)

    def test_original_59_estimates_not_recomputed(self):
        csv_content=(SITE/"explorador/data/predictions.csv").read_text(encoding="utf-8")
        rows=list(csv.DictReader(io.StringIO(csv_content)))
        self.assertEqual(len(rows),59)
        ids=[r["ID_POLIGONO"] for r in rows]
        self.assertEqual(len(set(ids)),59)
        values=[float(r["RENDIMIENTO_T_HA"]) for r in rows]
        self.assertAlmostEqual(sum(values)/59,3.956432328667021,places=7)
        script=(SOURCE/"research-59-archive.js").read_text(encoding="utf-8")
        self.assertIn("../explorador/data/predictions.csv",script)
        self.assertIn("../explorador/data/mapa_publico.json.gz",script)
        self.assertIn("sin tabla duplicada",script)
        self.assertNotIn("pred59-detail",script)
        self.assertNotIn("pred59-rows",script)
        self.assertNotIn("pred59-state",script)
        self.assertNotIn("pred59-search",script)
        self.assertNotIn("Math.random(",script)
        self.assertNotIn("!window.GeoCebadaPredictions",script)

if __name__=="__main__":
    unittest.main()
