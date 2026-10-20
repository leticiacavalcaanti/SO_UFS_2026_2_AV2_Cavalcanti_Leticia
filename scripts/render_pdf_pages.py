"""Renderiza páginas de um PDF em PNG para conferência visual (requer pymupdf).
uso: python render_pdf_pages.py arquivo.pdf pasta_saida 1,3,6"""
import sys

import fitz

doc = fitz.open(sys.argv[1])
pages = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else range(1, len(doc) + 1)
for p in pages:
    doc[p - 1].get_pixmap(dpi=70).save(f"{sys.argv[2]}/p{p}.png")
print("paginas no PDF:", len(doc))
