#!/usr/bin/env python3
"""Render nougat .mmd OCR files to viewable HTML with MathJax (formulae rendered).
Stdlib only, tiny memory use. Run:  python3 view_ocr.py
Then open:  refs/ocr/html/index.html  (double-click or `open refs/ocr/html/index.html`).

Note on formulae: nougat emits real LaTeX (\\[ ... \\], \\( ... \\), $...$), which MathJax
renders faithfully. Tables (\\begin{tabular}) and a few odd symbols may not render perfectly —
that is a nougat/MathJax limitation, not a data problem; the source .mmd still has the raw LaTeX.
"""
import os, glob, re

OCR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs", "ocr")
HDIR = os.path.join(OCR, "html")
os.makedirs(HDIR, exist_ok=True)

HEAD = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],
displayMath:[['$$','$$'],['\\\\[','\\\\]']],tags:'ams',
processEscapes:true}},options:{{ignoreHtmlClass:'nohl',processHtmlClass:'ml'}}}};</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>body{{max-width:920px;margin:2em auto;padding:0 1.2em;
font:16px/1.65 -apple-system,BlinkMacSystemFont,system-ui,sans-serif;color:#1a1a1a}}
h1,h2,h3{{line-height:1.25;border-bottom:1px solid #e2e2e2;padding-bottom:.2em}}
a{{color:#0b5cad}} .src{{color:#888;font-size:.85em}}
div.blk{{margin:.7em 0}}</style></head><body class="ml">"""
FOOT = "</body></html>"


def render(text):
    parts = []
    for blk in re.split(r"\n\s*\n", text):
        b = blk.rstrip()
        if not b:
            continue
        m = re.match(r"^(#{1,6})\s*(.*)$", b.strip())
        if m:
            lv = min(len(m.group(1)), 3)
            parts.append("<h%d>%s</h%d>" % (lv, m.group(2), lv))
        else:
            parts.append('<div class="blk">' + b.replace("\n", "<br>") + "</div>")
    return "\n".join(parts)


def main():
    files = sorted(glob.glob(os.path.join(OCR, "*.mmd")))
    links = []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        with open(f, encoding="utf-8", errors="replace") as fh:
            txt = fh.read()
        body = (HEAD.format(title=name)
                + "<p class='src'><a href='index.html'>&larr; all OCR files</a></p>"
                + "<h1>%s</h1>" % name + render(txt) + FOOT)
        with open(os.path.join(HDIR, name + ".html"), "w", encoding="utf-8") as fh:
            fh.write(body)
        links.append((name, name + ".html"))
    idx = (HEAD.format(title="OCR results")
           + "<h1>OCR results &mdash; math-rendered</h1>"
           + "<p class='src'>Rendered from <code>refs/ocr/*.mmd</code> via MathJax.</p><ul>"
           + "".join("<li><a href='%s'>%s</a></li>" % (u, n) for n, u in links)
           + "</ul>" + FOOT)
    with open(os.path.join(HDIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(idx)
    print("Rendered %d file(s) -> %s" % (len(files), os.path.join(HDIR, "index.html")))


if __name__ == "__main__":
    main()
