"""Regression tests for GeoCebada's five static views, links and 18 FAQs."""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

SITE = Path(__file__).resolve().parents[1] / "site"
PAGES = ("inicio", "modelo", "resultados", "confianza", "preguntas")
GROUPS = {
    "modelo": ("narrative", "rain-section", "neighbor-section", "architecture", "understanding"),
    "resultados": ("comparison", "significance", "new-evidence", "hhi-study", "alternative", "distribution-section"),
    "confianza": ("delivery", "limits"),
    "preguntas": ("technical-questions",),
}

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.repeated, self.sections = set(), [], []
        self.anchors, self.links, self.tocs, self.nexts = [], [], [], []
        self.faqs = self.iframes = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        ident = d.get("id")
        if ident:
            if ident in self.ids:
                self.repeated.append(ident)
            self.ids.add(ident)
        if tag == "section":
            self.sections.append(d.get("class", ""))
        if tag == "iframe":
            self.iframes += 1
        if tag == "details" and d.get("id") != "nav-dropdown" and "geo-tech-" not in d.get("class", ""):
            self.faqs += 1
        if tag == "nav":
            if "geo-subnav" in d.get("class", ""):
                self.tocs.append(d.get("data-geo-page"))
            if "geo-chapter-end" in d.get("class", ""):
                self.nexts.append(d.get("data-geo-page"))
        if tag == "a":
            dest = d.get("href", "")
            if dest.startswith("#"):
                self.anchors.append(dest[1:])
            if dest.startswith("./index.html"):
                parsed = urlsplit(dest)
                page = parse_qs(parsed.query).get("vista", ["inicio"])[0]
                self.links.append((page, parsed.fragment))


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (SITE / "index.html").read_text(encoding="utf-8")
        cls.css = (SITE / "styles.css").read_text(encoding="utf-8")
        cls.router = (SITE / "view-router.js").read_text(encoding="utf-8")
        cls.page = Reader()
        cls.page.feed(cls.html)

    def test_all_sections_visible_on_their_respective_pages(self):
        self.assertEqual(len(self.page.sections), 22)
        self.assertEqual(len(set(self.page.sections)), 22)
        for page, sections in GROUPS.items():
            for section in sections:
                name = section if section == "stat-band" else "section " + section
                self.assertIn(name, self.page.sections)
                self.assertIn(
                    'html[data-geo-vista="' + page + '"] #contenido > section.' + section,
                    self.css
                )
        additions = {"modelo": ("geo-tech-variables", "geo-tech-preparation", "geo-tech-training", "geo-tech-missing"), "resultados": ("geo-tech-residuals", "geo-extra-predictions")}
        ext = (SITE / "technical-details.css").read_text(encoding="utf-8")
        for page, new_sections in additions.items():
            for section in new_sections:
                self.assertIn("section geo-tech-section " + section, self.page.sections)
                self.assertIn('html[data-geo-vista="' + page + '"] #contenido > section.' + section, ext)
        for section in ("hero", "geoc-andrea-map"):
            self.assertIn(section, self.page.sections)
            self.assertIn('html[data-geo-vista="inicio"] #contenido > section.' + section, self.css)

    def test_no_invalid_internal_links_or_duplicate_ids(self):
        self.assertFalse(self.page.repeated, self.page.repeated)
        for target in self.page.anchors:
            self.assertIn(target, self.page.ids)
        for page, fragment in self.page.links:
            self.assertIn(page, PAGES)
            if fragment:
                self.assertIn(fragment, self.page.ids)
        for page in PAGES[1:]:
            self.assertIn('href="./index.html?vista=' + page + '"', self.html)

    def test_legacy_page_urls_still_resolve(self):
        for old, new in (
            ("problema", "inicio"), ("historia", "modelo"), ("calculo", "modelo"),
            ("pruebas", "resultados"), ("hhi", "resultados"),
            ("parcelas", "confianza")
        ):
            self.assertIn(old + ":'" + new + "'", self.router)
        self.assertIn('src="./view-router.js"', self.html)

    def test_eighteen_questions_in_four_groups(self):
        self.assertEqual(self.page.faqs, 18)
        for label in (
            "Consultar parcelas", "Entender el modelo",
            "Interpretar los resultados", "Validación y rigor"
        ):
            self.assertIn(">" + label + "</h3>", self.html)
        self.assertEqual(self.page.tocs, ["modelo", "resultados", "confianza"])
        self.assertEqual(sorted(self.page.nexts), sorted(PAGES))
        self.assertEqual(self.page.iframes, 3)

    def test_comparisons_appear_before_technical_tests(self):
        seq = self.page.sections
        self.assertLess(seq.index("section comparison"), seq.index("section significance"))
        self.assertLess(seq.index("section new-evidence"), seq.index("section hhi-study"))
        self.assertLess(seq.index("section delivery"), seq.index("section limits"))

if __name__ == "__main__":
    unittest.main()
