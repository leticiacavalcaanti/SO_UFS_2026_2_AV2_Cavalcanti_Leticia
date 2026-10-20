#!/usr/bin/env python3
"""Converte um .md em .html e .pdf (Edge/Chrome headless).

    python scripts/gerar_pdf.py report/relatorio.md "Relatório Técnico — AV2"
    python scripts/gerar_pdf.py report/apresentacao.md "Apresentação — AV2" --slides
Imagens relativas (../results/fig_*.png) são resolvidas a partir da pasta do .md.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

CSS = """
<style>
@page { size: A4; margin: 16mm 14mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.38; color: #1a1a1a; font-size: 10.2pt; }
h1 { font-size: 1.6em; color: #0b3d91; border-bottom: 2px solid #0b3d91; padding-bottom: 4px; }
h2 { font-size: 1.22em; color: #0b3d91; margin-top: 1.3em; border-bottom: 1px solid #ccc; padding-bottom: 3px; page-break-after: avoid; }
h3 { font-size: 1.05em; color: #0b3d91; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: .7em 0; font-size: .8em; page-break-inside: avoid; }
th, td { border: 1px solid #999; padding: 3px 5px; text-align: left; }
th { background: #eef2fb; }
code { background: #f2f2f2; padding: 0 3px; border-radius: 3px; font-size: .9em; }
pre { background: #f2f2f2; padding: 8px; font-size: .78em; white-space: pre-wrap; page-break-inside: avoid; }
blockquote { border-left: 4px solid #0b3d91; margin: .8em 0; padding: .1em .9em; background: #f7f9fd; }
img { max-width: 100%; display: block; margin: .6em auto; page-break-inside: avoid; }
p.fig { font-size: .85em; color: #52514e; text-align: center; margin-top: -.2em; }
a { color: #0b3d91; }
</style>
"""

SLIDES = """
<style>
@page { size: 297mm 167mm; margin: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; color: #1a1a1a; }
hr { page-break-after: always; border: 0; height: 0; margin: 0; }
section, .slide { }
h1 { font-size: 30pt; color: #0b3d91; margin: 14mm 14mm 4mm; }
h2 { font-size: 24pt; color: #0b3d91; margin: 10mm 14mm 3mm; }
p, ul, ol, table, pre, blockquote { margin-left: 14mm; margin-right: 14mm; font-size: 14pt; }
li { margin: 1.5mm 0; }
table { border-collapse: collapse; font-size: 11pt; } th, td { border: 1px solid #999; padding: 3px 6px; } th { background: #eef2fb; }
img { max-height: 105mm; max-width: 250mm; display: block; margin: 2mm auto; }
code { background: #f2f2f2; padding: 0 3px; }
</style>
"""


def find_browser():
    for c in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        if Path(c).exists():
            return c
    return shutil.which("msedge") or shutil.which("chrome") or shutil.which("chromium")


def main():
    src = Path(sys.argv[1])
    title = sys.argv[2]
    slides = "--slides" in sys.argv
    text = src.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"])
    html = src.with_suffix(".html")
    html.write_text(f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>{title}</title>"
                    f"{SLIDES if slides else CSS}</head><body>{body}</body></html>", encoding="utf-8")
    pdf = src.with_suffix(".pdf")
    browser = find_browser()
    if not browser:
        print(f"Sem navegador Chromium: abra {html} e use Imprimir > Salvar como PDF.")
        return
    with tempfile.TemporaryDirectory(prefix="print-") as prof:
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-sandbox", f"--user-data-dir={prof}",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf.resolve()}",
                        f"file:///{html.resolve().as_posix()}"], check=True, timeout=120)
    print("PDF:", pdf)


if __name__ == "__main__":
    main()
