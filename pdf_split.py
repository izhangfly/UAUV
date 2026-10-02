#!/usr/bin/env python3
"""Split a PDF into sub-PDFs of <=N pages each, so nougat only ever loads a small file.
Usage: python3 pdf_split.py <in.pdf> <outdir> <pages_per_split>
Writes <outdir>/000000.pdf, 000015.pdf, ... (named by 0-based start page)."""
import sys, os
import pypdfium2 as pdfium

src_path, outdir, split = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.makedirs(outdir, exist_ok=True)
src = pdfium.PdfDocument(src_path)
n = len(src)
count = 0
for start in range(0, n, split):
    end = min(start + split, n)
    dst = pdfium.PdfDocument.new()
    dst.import_pages(src, list(range(start, end)))
    with open(os.path.join(outdir, "%06d.pdf" % start), "wb") as f:
        dst.save(f)
    dst.close()
    count += 1
src.close()
print("split %s (%d pages) -> %d sub-pdfs of <=%d pages" % (os.path.basename(src_path), n, count, split))
