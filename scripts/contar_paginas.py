"""Conta as páginas de um PDF e informa em que página começa o Anexo A (requer pymupdf).
uso: python contar_paginas.py report/relatorio.pdf"""
import sys

import pymupdf

d = pymupdf.open(sys.argv[1])
print("paginas:", len(d))
for i, p in enumerate(d):
    if "Anexo A" in p.get_text() and i > 2:
        print("Anexo A na pagina", i + 1, "-> corpo (com capa e rosto):", i, "paginas")
        break
