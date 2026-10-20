#!/usr/bin/env python3
"""Gera report/relatorio.docx no modelo usado nas atividades do Prof. Glauco Carneiro (UFS).

Modelo reproduzido: A4, margens 2,54 cm, Times New Roman 12, espaçamento 1,5, texto justificado
com recuo de 1,27 cm, capa + folha de rosto (brasão, instituição, autor, título em itálico 18 pt,
cidade/ano), títulos numerados em negrito, blocos de código com fundo escuro e as seções finais
"Materiais", "Participação" e "Apoio na elaboração do conteúdo escrito".

Requer python-docx.  Uso (na raiz do repositório):  python scripts/gerar_docx.py
"""
import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "results")
LOGO = os.path.join(ROOT, "report", "assets", "logo_ufs.png")
OUT = os.path.join(ROOT, "report", "relatorio.docx")

AUTOR = "LETICIA DA MATA CAVALCANTI"
TITULO = ("Atividade 2 (AV2) – Memória, armazenamento, sincronização e desempenho de aplicações "
          "de IA generativa: o GenResearch-Servidor")
REPO = "https://github.com/leticiacavalcaanti/SO_UFS_2026_2_AV2_Cavalcanti_Leticia"
VIDEO = "https://drive.google.com/file/d/1ZTenxEhflYIi4mIGWAJvMkZqFxuyeKsG/view?usp=sharing"
FONT = "Times New Roman"
MONO = "Courier New"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2.54)
sec.different_first_page_header_footer = True


# ------------------------------------------------------------------ utilidades
def set_fonts(rpr_owner, name=FONT):
    rpr = rpr_owner.get_or_add_rPr() if hasattr(rpr_owner, "get_or_add_rPr") else rpr_owner
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in list(rf.attrib):
        del rf.attrib[a]
    for a in ("ascii", "hAnsi", "eastAsia", "cs"):
        rf.set(qn("w:" + a), name)


def style_font(style, size, bold=False, italic=False, color=RGBColor(0, 0, 0)):
    style.font.name = FONT
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.italic = italic
    style.font.color.rgb = color
    set_fonts(style.element.get_or_add_rPr() if style.element.rPr is None else style.element.rPr)


style_font(doc.styles["Normal"], 12)
for nm, sz in (("Heading 1", 14), ("Heading 2", 12)):
    st = doc.styles[nm]
    style_font(st, sz, bold=True)
    st.paragraph_format.keep_with_next = True
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.line_spacing = 1.5
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
doc.styles["Heading 1"].paragraph_format.left_indent = Cm(1.27)
doc.styles["Heading 1"].paragraph_format.first_line_indent = Cm(-0.63)
doc.styles["Heading 2"].paragraph_format.left_indent = Cm(1.27)


def run(p, text, size=None, bold=False, italic=False, color=None, font=None, underline=False):
    r = p.add_run(text)
    set_fonts(r._r.get_or_add_rPr(), font or FONT)
    if size:
        r.font.size = Pt(size)
    r.font.bold = bold or None
    r.font.italic = italic or None
    r.font.underline = underline or None
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    return r


def rich(p, text, size=None, color=None, base_bold=False):
    """**negrito**, *itálico*, `código`."""
    for part in re.split(r"(\*\*.+?\*\*|\*[^*]+?\*|`.+?`)", text):
        if not part:
            continue
        if part.startswith("**"):
            run(p, part[2:-2], size, bold=True, color=color)
        elif part.startswith("`"):
            run(p, part[1:-1], (size or 12) - 1, bold=base_bold, font=MONO, color=color)
        elif part.startswith("*"):
            run(p, part[1:-1], size, italic=True, bold=base_bold, color=color)
        else:
            run(p, part, size, bold=base_bold, color=color)


def para(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, first=1.27, line=1.5, before=3, after=3, size=None,
         left=None, keep_next=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.line_spacing = line
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if first:
        pf.first_line_indent = Cm(first)
    if left is not None:
        pf.left_indent = Cm(left)
    pf.keep_with_next = keep_next
    if text:
        rich(p, text, size)
    return p


def h1(text):
    p = doc.add_paragraph(style="Heading 1")
    rich(p, text, 14, base_bold=True)
    return p


def h2(text):
    p = doc.add_paragraph(style="Heading 2")
    rich(p, text, 12, base_bold=True)
    return p


def bullets(items, size=None, level_left=1.9):
    for it in items:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.line_spacing = 1.5
        pf.space_before = pf.space_after = Pt(0)
        pf.left_indent = Cm(level_left)
        pf.first_line_indent = Cm(-0.63)
        run(p, "•\t", size)
        rich(p, it, size)
        pf.tab_stops.add_tab_stop(Cm(level_left))


def shade(el_pr, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    el_pr.append(shd)


KW = {"def", "if", "not", "return", "with", "while", "for", "in", "else", "elif", "None", "True", "False", "self", "import", "from", "class"}


def code(lines, size=8.5):
    """Bloco de código com fundo escuro (como no modelo)."""
    for i, ln in enumerate(lines):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.line_spacing = 1.0
        pf.space_before = Pt(6) if i == 0 else Pt(0)
        pf.space_after = Pt(6) if i == len(lines) - 1 else Pt(0)
        pf.left_indent = Cm(1.27)
        pf.keep_together = True
        pf.keep_with_next = i < len(lines) - 1
        shade(p._p.get_or_add_pPr(), "1F1F1F")
        body, _, com = ln.partition("  #")
        for tok in re.split(r"(\s+|[().,:\[\]=]+)", body):
            if tok:
                run(p, tok, size, color="569CD6" if tok in KW else "CCCCCC", font=MONO)
        if com or ln.strip().startswith("#"):
            if ln.strip().startswith("#"):
                run(p, "", size)
            run(p, ("  #" + com) if com else "", size, color="6AA84F", font=MONO)


def cell_shade(cell, fill):
    shade(cell._tc.get_or_add_tcPr(), fill)


def table(rows, widths, size=9.5, header=True, align_first_left=True):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Cm(widths[j])
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(1)
            curto = len(re.sub(r"[*`]", "", str(val))) <= 16
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (j > 0 and curto) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.keep_with_next = (i < len(rows) - 1) and (len(rows) <= 4 or i == 0)
            rich(p, str(val), size, base_bold=(header and i == 0))
            if header and i == 0:
                cell_shade(c, "D9D9D9")
    # repetir cabeçalho e evitar quebra de linha no meio
    for k, r in enumerate(t.rows):
        trpr = r._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
        if header and k == 0:
            trpr.append(OxmlElement("w:tblHeader"))   # repete o cabeçalho se a tabela quebrar
    gap = doc.add_paragraph()
    gap.paragraph_format.space_after = Pt(2)
    gap.paragraph_format.line_spacing = 0.6
    return t


FIG = {"n": 0}


def figure(fname, width_cm, caption):
    FIG["n"] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(os.path.join(RES, fname), width=Cm(width_cm))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)
    c.paragraph_format.line_spacing = 1.0
    run(c, f"Figura {FIG['n']} – {caption}", 10)


def hyperlink(p, url, text):
    part = doc.part
    rid = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    set_fonts(rpr)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rpr.append(u)
    col = OxmlElement("w:color")
    col.set(qn("w:val"), "0563C1")
    rpr.append(col)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    r.append(t)
    h.append(r)
    p._p.append(h)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def center(text, size=12, bold=False, italic=False, before=0, after=0, line=1.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = line
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(before), Pt(after)
    if text:
        run(p, text, size, bold=bold, italic=italic)
    return p


# ------------------------------------------------------------------ rodapé com nº de página
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
for kind, txt in (("begin", None), (None, " PAGE "), ("end", None)):
    r = fp.add_run()
    set_fonts(r._r.get_or_add_rPr())
    r.font.size = Pt(10)
    if kind:
        f = OxmlElement("w:fldChar")
        f.set(qn("w:fldCharType"), kind)
        r._r.append(f)
    else:
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = txt
        r._r.append(it)


# ------------------------------------------------------------------ capa e folha de rosto
def topo():
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(LOGO, width=Cm(2.6))
    center("UNIVERSIDADE FEDERAL DE SERGIPE", before=8)
    center("")
    center(AUTOR)
    center("")


topo()
center("")
center("")
center(TITULO, size=18, italic=True, before=70, line=1.25)
center("SÃO CRISTÓVÃO - SE", before=185)
center("2026")
page_break()

topo()
center(TITULO, size=18, italic=True, before=40, line=1.25)
for _ in range(2):
    center("")
rp = para("Atividade apresentada à disciplina de Sistemas Operacionais como requisito para obtenção de nota.",
          first=0.0, left=7.6)
center("")
pp = center("Prof. Dr.: Glauco de Figueiredo Carneiro")
pp.paragraph_format.left_indent = Cm(7.6)
center("SÃO CRISTÓVÃO - SE", before=135)
center("2026")
page_break()

# ================================================================== CORPO
h1("1.  Tabela de contribuição individual")
table([["Integrante", "Contribuição", "Participação"],
       ["Leticia da Mata Cavalcanti",
        "Definição do recorte; implementação do serviço e dos experimentos; execução; análise; relatório; slides; vídeo.",
        "100%"]], [4.2, 9.4, 2.4])

h1("2.  Introdução e problema")
para("Aplicações de IA generativa e de RAG (*retrieval-augmented generation*) são, para o sistema operacional (SO), "
     "cargas que combinam arquivos grandes (corpus, índices, *embeddings*, *checkpoints*), memória virtual e cache de "
     "páginas, filas e caches compartilhados por várias threads e escrita concorrente em logs. Este trabalho implementa "
     "o **GenResearch-Servidor**, um serviço RAG simplificado, e o usa como carga para observar como o SO administra "
     "esses recursos e quais custos surgem.")
h2("Pergunta norteadora")
para("*Como memória principal, memória virtual, armazenamento, caches, filas compartilhadas e mecanismos de "
     "sincronização afetam o desempenho, a estabilidade e a correção de uma aplicação de IA generativa ou de RAG?*")
h2("Recorte experimental")
para("O foco é o SO, não a qualidade do texto (enunciado, §1). Por isso os *embeddings* e a geração são **simulados**, "
     "o que o enunciado admite (Parte B: “embeddings reais ou vetores simulados”; “gerar por modelo local ou simular "
     "custo computacional”). A simulação preserva o perfil de recursos (espera de serviço externo, CPU proporcional ao "
     "contexto, varredura real do índice) e torna tudo reprodutível sem baixar modelo. O corpus é sintético. O recorte "
     "cobre as configurações C1–C6 e a Parte D (opções 1 e 2, log concorrente e deadlock isolado). A ideia de "
     "*chunking* por palavras com sobreposição e de cosseno sobre vetores normalizados vem de um serviço RAG anterior "
     "da autora, reescrito aqui sem dependência dele.")

h1("3.  Ambiente")
table([["Item", "Valor"],
       ["Hospedeiro / Linux", "Windows 11, Docker Desktop 28.3.2 (WSL2); **contêiner** Debian GNU/Linux 13, kernel 6.6.87.2-microsoft-standard-WSL2"],
       ["CPU", "Intel Core i5-10210U, 4 CPUs lógicas (2 núcleos × 2 threads)"],
       ["RAM / swap / página", "5,8 GiB / 1,0 GiB (VM) / 4 KiB; sem GPU"],
       ["Linguagem e bibliotecas", "Python 3.12, numpy 2.1.3, matplotlib 3.9.2, SQLite; data das execuções: 18/10/2026"]],
      [4.0, 12.0])
para("Os comandos e saídas completas (`uname`, `lscpu`, `free`, `/proc/meminfo`, `lsblk`, `df`, `swapon`, `vmstat`, "
     "`iostat`) estão em `results/env/`. **MemFree** é a RAM totalmente ociosa; **MemAvailable** estima o que pode ser "
     "dado a novos processos sem *swap*, incluindo cache de páginas e *slabs* reclamáveis; o **cache de páginas** guarda "
     "arquivos já lidos e não é memória desperdiçada (a 2ª leitura evita o disco, §9, e ele é devolvido sob pressão); o "
     "**swap** recebe páginas anônimas expulsas da RAM. Para datasets, índices, *embeddings* e *checkpoints*: a 1ª leitura "
     "paga E/S, as seguintes não, e um arquivo maior que a memória disponível não cabe todo no cache.")

h1("4.  Arquitetura")
code(["2 produtores --put--> BoundedBuffer(empty/full/mutex) --get--> N threads",
      "worker: cache --miss--> embedding --> varredura do índice (read | mmap)",
      "        --> SQLite --> contexto limitado --> geração simulada --> cache",
      "logs (mutex) | métricas: /proc, getrusage, cgroup v2"], size=8)
bullets(["**Ingestão** (`store.build_index`): lê `.txt`, fragmenta em trechos de 100 palavras (20 de sobreposição), gera "
         "vetores float32 de 256 dimensões e grava `vectors.npy` e `meta.sqlite`.",
         "**Recuperação:** top-k (k = 5) por produto escalar, em blocos de 32.768 linhas, igual para índice na RAM "
         "(`np.load`) ou mapeado (`mmap_mode=\"r\"`); contexto limitado em bytes (≈ tokens × 4).",
         "**Geração simulada:** `sleep` de 20 ms (serviço externo) mais SHA-256 repetido sobre o contexto (CPU).",
         "**Trabalhadores = threads:** a carga é mista (o `sleep`, o `matmul` do numpy e o `hashlib` liberam o GIL); "
         "processos custariam cópia do índice e IPC. A escolha foi testada em §10.1."])

h1("5.  Dados, corpus, embeddings, índice e cache")
para("O corpus (`corpus.py`, semente fixa) tem 12 tópicos; 70% das palavras de cada documento vêm do vocabulário do "
     "tópico e 30% do global, de modo que consultas de um tópico recuperam trechos dele. Nada é real ou pessoal. O "
     "**cache compartilhado** é LRU ou FIFO, com chave canônica (palavras únicas ordenadas, sem *stopwords*), protegido "
     "por mutex, e registra acertos, erros, substituições e o tempo economizado.", before=3)
table([["Documentos", "Trechos", "Corpus (texto)", "vectors.npy"],
       ["500", "6.500", "≈ 4 MB", "6,4 MB"], ["2.000 (C3, C4, C6)", "26.000", "≈ 17 MB", "25 MB"],
       ["8.000", "104.000", "≈ 68 MB", "102 MB"], ["24.000", "312.000", "≈ 200 MB", "305 MB"]],
      [4.5, 3.2, 4.0, 3.8])

h1("6.  Processos, threads, filas e recursos compartilhados")
para("Há um processo Python com 2 threads produtoras, N trabalhadoras e a thread principal; o numpy cria ainda um "
     "*pool* de threads do OpenBLAS (§10.1). Os recursos compartilhados e sua proteção:", keep_next=True)
table([["Recurso", "Risco sem proteção", "Proteção"],
       ["Fila de requisições", "perda, duplicação, estouro", "`BoundedBuffer`: semáforos `empty`/`full` + mutex; FIFO verificado"],
       ["Cache de respostas", "atualização perdida, computação duplicada", "`Lock` na estrutura e nos contadores"],
       ["Arquivo de log", "linhas intercaladas", "`Lock` em `SafeLogger`"],
       ["Conexão SQLite", "uso entre threads", "uma conexão somente-leitura por thread"],
       ["Índice vetorial", "–", "somente leitura após a ingestão"]], [3.4, 5.0, 7.6])

h1("7.  Estratégia de sincronização")
para("Adotei semáforos contadores (`empty`, `full`) mais mutex no buffer limitado (Opção 1); mutex global e lock por "
     "chave (*single-flight*) no cache (Opção 2); mutex no log; ordenação global de locks e `acquire` com *timeout* e "
     "recuo para o deadlock. O trecho abaixo mostra o produtor do buffer:", keep_next=True)
code(["def put(self, item, timeout=None):",
      "    if not self._empty.acquire(timeout=timeout):  # há vaga? (empty)",
      "        return False                              # cheia: rejeita",
      "    with self._mutex:                             # protege o deque",
      "        self._buf.append((self._seq, now(), item))",
      "        self._seq += 1",
      "    self._full.release()                          # sinaliza item (full)",
      "    return True"], size=8)
para("Os semáforos ficam **fora** da seção crítica: se o produtor pegasse o mutex antes de `empty` com o buffer cheio, "
     "ficaria bloqueado segurando o mutex e o consumidor não conseguiria liberar espaço (deadlock).", first=0)

h1("8.  Metodologia")
para("Cada configuração foi repetida **3 vezes**, com o mesmo corpus e a mesma aplicação em cada comparação. Fatores "
     "variados: workers (1, 2, 4, 8), capacidade da fila (4, 64), tamanho do corpus (6 a 305 MB de índice), contexto "
     "(500, 2.000, 8.000 B), capacidade (0–512) e política (LRU/FIFO) do cache, `mmap`, padrão de leitura, estado do "
     "cache de páginas e limite de memória (cgroup). Métricas: latência (média, mediana, p95), vazão, RSS/VSZ, "
     "`MemAvailable`, faltas de página, bytes lidos, fila, utilização, acertos/erros, perdas/duplicações. O estado "
     "“frio” usa `posix_fadvise(DONTNEED)` antes de cada execução (frio na VM Linux; o Windows ainda pode cachear o "
     "disco virtual). Comandos: `python scripts/run_all.py`; dados brutos em `results/`; tabelas completas no Anexo A.")

h1("9.  Resultados: memória, armazenamento, paginação e E/S")
h2("9.1  C1 × C2 – `read()` convencional × `mmap` (Parte E)")
para("Arquivo aleatório de 16, 128 e 768 MB; leitura sequencial em blocos de 1 MiB (`read` em blocos, `read` do "
     "arquivo inteiro, `mmap`) e 3.000 acessos de 4 KiB; execução fria e quente. Valores para 768 MB (média de 3):",
     keep_next=True)
table([["Método / padrão", "Cache", "Leitura (ms)", "ΔRSS (MB)", "Faltas maiores", "Lido do disco (MB)"],
       ["`read` em blocos, seq.", "fria", "755", "0", "0", "768"],
       ["`read` em blocos, seq.", "quente", "331", "0", "0", "0"],
       ["`read` tudo, seq.", "fria", "1.369", "768", "0", "768"],
       ["`mmap`, seq.", "fria", "1.064", "768", "6.146", "768"],
       ["`mmap`, seq.", "quente", "322", "768", "0", "0"],
       ["`pread` 4 KiB, aleat.", "fria", "637", "0", "0", "**23**"],
       ["`mmap`, aleat.", "fria", "1.410", "165", "2.441", "**287**"]], [4.2, 1.7, 2.3, 2.1, 2.5, 3.2])
figure("fig_c1c2_leitura.png", 11.5, "Leitura sequencial de 768 MB (média ± desvio-padrão): tempo frio, quente e ΔRSS.")
bullets(["A 2ª execução foi 2,1–3,3× mais rápida e não leu nada do disco: é o **cache de páginas**.",
         "O `mmap` abre em ~20–40 µs (mapeia, não lê) e o VSZ sobe 768 MB na abertura, mas o RSS só cresce ao tocar as "
         "páginas (**VSZ ≠ memória física**); `read()` não gera faltas maiores, o `mmap` gerou 6.146 (≈ 125 KiB cada, "
         "leitura antecipada).",
         "`read` do arquivo inteiro é o pior caso (2× mais lento, +768 MB de RSS): é o que ocorre ao carregar um "
         "*checkpoint* inteiro. No acesso aleatório frio o `mmap` leu **287 MB** para ~12 MB úteis (12×), contra 23 MB do "
         "`pread`, e foi 2,2× mais lento."])

h2("9.2  C5 – pressão de memória")
para("**(a) Corpus e contexto** (1 trabalhador, processo novo por configuração, 1ª leitura fria; dados em "
     "`results/c5_scale.csv`): a recuperação cresce **linearmente** com o índice (0,8 ms a 6 MB; ≈ 21 ms a 305 MB; ≈ 70 "
     "µs/MB, varredura O(N)) e o RSS o acompanha (44 → 344 MB). `read` e `mmap` têm RSS e latência iguais em regime "
     "estacionário; muda *quando* o custo é pago (`read` na abertura; `mmap` em 2.474 faltas maiores na 1ª consulta, a "
     "305 MB). A geração cresce com o contexto (≈ 20 ms com 500 B; ≈ 100–120 ms com 8.000 B) e, com limite de 500 B, "
     "quase nenhum trecho (~700 B) cabe: o limite de contexto trunca informação.")
para("**(b) Índice maior que o limite de memória** (cgroup, swap do contêiner desligado): índice sintético de 1.024 MB, "
     "15 consultas de varredura completa, cache de páginas despejado antes de cada execução.", keep_next=True)
table([["Limite", "Modo", "Resultado (3 de 3 repetições)", "Mediana/consulta", "Faltas maiores", "Lido do disco"],
       ["2.048 MB", "`read`", "conclui 15/15", "70–103 ms", "0", "1,0 GB"],
       ["2.048 MB", "`mmap`", "conclui 15/15", "89–153 ms", "≈ 8.300", "1,0 GB"],
       ["**384 MB**", "**`read`**", "**morto pelo OOM killer (exit 137)**", "–", "–", "–"],
       ["**384 MB**", "**`mmap`**", "**conclui 15/15, RSS ≈ 399 MB**", "**1,2–1,6 s**", "**≈ 125.000**", "**≈ 15,3 GB**"]],
      [2.0, 1.6, 5.0, 2.8, 2.4, 2.2])
figure("fig_c5_limite.png", 8.5, "Latência por consulta com `mmap` e índice de 1 GB: limite de 2 GB × 384 MB.")
para("Com 384 MB, `read` precisa de ~1 GB de memória **anônima** (irreclamável sem swap) e o kernel mata o processo. O "
     "`mmap` usa páginas de **arquivo** (limpas, reclamáveis): o kernel as descarta e relê, então o processo sobrevive, "
     "mas com *thrashing*: cada varredura de 1 GB excede o cache (≈ 384 MB), que nunca retém o que a próxima varredura "
     "precisa, e todas as 15 relêem do disco (≈ 15 × 1.024 MB = 15,3 GB), com consultas 13–17× mais lentas. **O swap não "
     "foi exercitado** (`--memory-swap` igual a `--memory`); a paginação observada é de arquivo, não de swap.", first=0)

h1("10.  Resultados: concorrência, cache e correção")
h2("10.1  C3 – concorrência e fila")
para("400 consultas distintas, cache desligado, 2 produtores, 2.000 documentos (média ± desvio de 3 repetições):",
     keep_next=True)
table([["Fila", "Workers", "Vazão (req/s)", "p95 do serviço (ms)", "Espera na fila (ms)", "Fila média / máx"],
       ["4", "1 / 2 / 4 / 8", "25,3 / 36,5 / 43,1 / 46,0", "51 / 73 / 138 / 274", "157 / 106 / 87 / 76", "≈ 3,0–3,5 / 4"],
       ["64", "1 / 2 / 4 / 8", "25,4 / 39,4 / 47,0 / 43,6 (±6,0)", "51 / 67 / 126 / 292", "2.341 / 1.483 / 1.248 / 1.340", "≈ 58 / 64"]],
      [1.2, 2.4, 4.4, 3.2, 3.2, 2.2], size=9)
figure("fig_c3_concorrencia.png", 12.5, "Vazão, p95 do serviço e espera na fila × número de trabalhadores (filas de 4 e 64).")
bullets(["**A concorrência aumentou a vazão, com retorno decrescente:** 4 workers = 1,7–1,85× a de 1; com 8, sem ganho "
         "(47,0 → 43,6 req/s) e p95 ~5× pior: com 4 CPUs lógicas (2 núcleos físicos) e parte do trabalho sob o GIL, "
         "mais threads só trazem disputa e trocas de contexto.",
         "**Fila maior não aumenta vazão, aumenta latência:** a fila ficou quase sempre cheia (58 de 64); espera de "
         "1,2–2,3 s (fila 64) contra ~0,1 s (fila 4), como prevê a lei de Little. O limite dá *backpressure*. "
         "**Correção:** 0 perdidas, 0 duplicadas e 0 violações de FIFO.",
         "**Hipótese testada:** em `ps -L` havia 3 threads a ~82% de CPU quase sem trocas voluntárias (espera ativa do "
         "OpenBLAS?). Com `OPENBLAS_NUM_THREADS=1` a vazão subiu ≈ 10–15% com 1–2 workers, mas a saturação acima de 2 "
         "persistiu: a causa total não foi isolada."])

h2("10.2  C4 – cache compartilhado")
para("400 requisições, 2 workers (cenários: consultas distintas, 50%/90% de repetição exata e 50% de paráfrases):",
     keep_next=True)
table([["Cenário (LRU)", "Capacidade", "Acerto", "Erros", "Tempo economizado", "Tempo total"],
       ["distintas", "512", "0%", "400", "0 s", "11,3 ± 1,0 s"],
       ["repetidas 50%", "512", "44,7%", "221", "9,3 s", "5,7 s (sem cache: 12,0 s)"],
       ["repetidas 90%", "16 / 64", "74,0% / 89,2%", "104 / 43", "16,2 / 19,2 s", "2,7 / 1,25 s (sem cache: 9,9 s)"],
       ["paráfrase 50%", "512", "50,9%", "196", "10,9 s", "5,2 s"]], [3.0, 2.2, 2.7, 1.8, 3.2, 4.6], size=9)
figure("fig_c4_cache.png", 11.5, "Taxa de acerto e tempo total × capacidade do cache, por cenário (LRU).")
para("O cache reduziu tempo e operações de recuperação **quando há repetição** (89,2% de acerto com 90% de repetição: "
     "9,9 s → 1,25 s, ≈ 8×); com consultas distintas o acerto é 0% e só há custo. LRU e FIFO empataram (74,0% × 73,7%): "
     "as repetições foram uniformes. Com o cache desligado o mesmo trabalho levou de 9,9 a 12,9 s (± 2,7 s), então "
     "diferenças < ~25% não são significativas aqui.", first=0)

h2("10.3  C6 – falhas controladas")
table([["Cenário", "Resultado (média de 3)"],
       ["Arquivo/índice ausente", "40 requisições → 40 erros controlados, 80 retentativas; o processo não caiu"],
       ["Índice indisponível por 0,6 s", "120/120 concluídas com sucesso após retentativas com recuo (2,2 s)"],
       ["Fila saturada, produtor com *timeout*", "8 concluídas, **112 rejeitadas** (93%) e registradas; 0 perdas silenciosas"],
       ["Fila saturada, produtor bloqueia", "120/120 concluídas em 4,0 s (*backpressure*)"],
       ["Serviço externo falhando 30%", "sem retentativa: 41 erros (34%); com até 3: 1 erro, 55 retentativas, +88% de tempo"],
       ["Limite de memória", "§9.2(b): `read` morto por OOM (exit 137); `mmap` sobrevive com *thrashing*"]], [5.2, 10.8], size=9)

h2("10.4  Parte D – sincronização, falhas demonstradas e correções")
para("As janelas de corrida foram ampliadas **de propósito** (`sleep(0)` entre leitura e escrita e "
     "`sys.setswitchinterval(1e-6)`): injeção de falha controlada; no código “natural” a corrida seria bem mais rara.",
     keep_next=True)
table([["D1 – cache (8 threads × 1.500 ops)", "Atualizações perdidas", "Computações (ideal 40)", "Tempo"],
       ["sem proteção", "**10.334 de 12.000 (86%)**", "62 (**22 duplicadas**)", "0,36 s"],
       ["mutex global", "0", "40", "0,68 s"], ["lock por chave (*single-flight*)", "0", "40", "0,56 s"]],
      [5.8, 4.2, 3.8, 2.2], size=9)
bullets(["**D1:** `hits += 1` (ler–somar–escrever) perde atualizações e duas threads calculam a mesma chave; o lock por "
         "chave corrige e é ~18% mais rápido que o global (chaves distintas computam em paralelo).",
         "**D2 – log:** sem lock, **1.817 de 2.400 linhas (76%)** saíram corrompidas; com mutex, 0.",
         "**D3 – produtor/consumidor** (capacidades 1, 4, 64; 18 execuções): 0 perdidos, 0 duplicados, 0 violações de FIFO; "
         "com consumidor lento o produtor bloqueia ≈ 1,2 s; com produtor lento os consumidores esperam ≈ 1,0 s.",
         "**D4 – deadlock** (A→B / B→A, em subprocesso): 3/3 não terminaram; após 3 s o pai o classificou como deadlock "
         "(threads em `futex_wait_queue`) e o encerrou (`kill`). Correções: **ordenação global de locks** (0,30 s) e "
         "**`acquire` com timeout + recuo** (0,60 s). *Starvation* não foi demonstrada."])
para("**Evidências de SO** (`results/evidence/`: `ps -L`, `/proc/<pid>/status`, `pidstat -t`, `vmstat`, `iostat`, "
     "`strace -c -f`): com 4 trabalhadores havia 11 threads; **`futex` respondeu por 70% do tempo em syscalls** (3.919 "
     "chamadas), seguido de `clock_nanosleep` (16%). Para o mesmo arquivo de 16 MB, `read` aparece como sequência de "
     "`read(...)` e `mmap` como um único `mmap(NULL, 16777216, PROT_READ, MAP_SHARED, ...)`: a leitura passa a ocorrer "
     "por faltas de página.", first=0)

h1("11.  Relação com Sistemas Operacionais e IA generativa")
bullets(["**Memória virtual e cache de páginas:** carregar *embeddings*/*checkpoints* com `read()` exige memória anônima "
         "do tamanho do arquivo (OOM se não couber); `mmap` evita a cópia e funciona acima da RAM, mas vira *thrashing* "
         "se o conjunto de trabalho não cabe no cache. A 1ª carga é fria; as seguintes, quentes.",
         "**RAG:** a busca por força bruta é O(N); índices aproximados (HNSW, IVF) reduzem esse custo e o limite de "
         "contexto é limite de custo e de qualidade. Fila limitada dá *backpressure* e cache de resposta só paga com repetição.",
         "**Concorrência:** a vazão satura por GIL/CPU; em inferência real a contenção seria por GPU e memória do dispositivo."])

h1("12.  Limitações")
bullets(["Contêiner sobre WSL2 sobre Windows: “frio” é frio no cache de páginas da VM; 2 núcleos físicos e ruído do "
         "hospedeiro (9,9–12,9 s para trabalho equivalente no C4).",
         "Embeddings e geração simulados: sem GPU, VRAM, KV-cache ou pesos; **não generaliza** para modelos maiores, "
         "múltiplas GPUs ou ambientes distribuídos (dominam a transferência host↔dispositivo, a memória da GPU e a rede).",
         "Corpus pequeno (≤ 305 MB de índice); taxas de corrida (86%, 76%) valem para janelas ampliadas; swap e "
         "starvation não testados; causa total da saturação com > 2 workers não isolada; 3 repetições."])

h1("13.  Conclusão")
para("O serviço mostrou, com evidências reprodutíveis, que: (i) o cache de páginas explica a diferença entre a 1ª e a "
     "2ª leitura, e carregar tudo com `read()` é o caminho mais caro em memória; (ii) `mmap` troca RAM anônima por "
     "paginação sob demanda: permite operar um índice de 1 GB com 384 MB, onde `read` é morto por OOM, ao custo de "
     "*thrashing* (~15× mais lento, 15 GB lidos); (iii) mais threads não significam mais vazão (saturação em 2–4 workers, "
     "piora do p95 com 8) e filas grandes viram latência; (iv) o cache só compensa com repetição, mas então reduz o tempo "
     "em ≈ 8×; (v) sem exclusão mútua o cache e o log ficam incorretos (86% de atualizações perdidas, 76% de linhas "
     "corrompidas) e a ordem de aquisição de locks pode causar deadlock, evitável por ordenação global ou *timeouts*.")

h1("14.  Referências")
refs = [
    "[1] MAZIERO, Carlos A. *Sistemas Operacionais: Conceitos e Mecanismos*. Curitiba: DInf-UFPR, 2019. Caps. 2, 4, 5 e 6, e slides sobre comunicação e coordenação entre tarefas.",
    "[2] SILBERSCHATZ, A.; GALVIN, P.; GAGNE, G. *Sistemas Operacionais: Conceitos e Aplicações*. Campus, 2001.",
    "[3] TANENBAUM, A. *Sistemas Operacionais Modernos*. 2. ed. Pearson, 2003.",
    "[4] LEWIS, P. et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS*, 2020. Disponível em: https://arxiv.org/abs/2005.11401.",
    "[5] LINUX. *man 2 mmap*, *man 2 posix_fadvise*, *man 5 proc*, *man 2 getrusage*, *man 7 cgroups* e documentação do cgroup v2 (`memory.max`, `memory.events`, `memory.stat`).",
    "[6] PYTHON SOFTWARE FOUNDATION. Documentação de `threading`, `mmap` e `sqlite3`; NUMPY. `numpy.load` com `mmap_mode`.",
    "[7] CARNEIRO, G. F. *Sistemas Operacionais como Infraestrutura para IA Generativa* (slides da aula de 26/08/2026). UFS, 2026.",
]
for r_ in refs:
    para(r_, first=0, size=11, line=1.15, after=3)

h1("15.  Materiais")
p = para("GitHub: ", first=0, line=1.5)
hyperlink(p, REPO, REPO)
p = para("Link do vídeo: ", first=0, line=1.5)
hyperlink(p, VIDEO, VIDEO)
para("Commit da entrega: `6a4bcad` (experimentos); evidências, logs e dados brutos em `results/`; instruções de "
     "reprodução no `README.md` (`python scripts/run_all.py`).", first=0)

h1("16.  Participação nas tarefas")
para("Leticia Cavalcanti – trabalho individual: definição do recorte, desenvolvimento do código-fonte do serviço e dos "
     "experimentos, execução e coleta das evidências, análise dos resultados, elaboração do relatório, dos slides e do vídeo.",
     first=0)

h1("17.  Apoio na elaboração do conteúdo escrito")
para("Durante o desenvolvimento deste trabalho foi utilizado o Claude Code (Anthropic, modelo Claude Sonnet 5.5, nível de raciocínio medium) como "
     "ferramenta de apoio para:", first=0, keep_next=True)
bullets(["Estruturar o repositório e redigir o código do serviço e dos scripts de experimento, executados e conferidos "
         "no ambiente da discente (os números do relatório vêm de `results/`).",
         "Apoiar a análise dos resultados, a redação do relatório e dos slides, e a explicação de conceitos de SO.",
         "Corrigir problemas metodológicos identificados durante a revisão dos resultados (cache de páginas no C5, RSS "
         "contaminado, contagem de retentativas); o detalhamento está em `declaracao_uso_ia.md`."])

# ================================================================== ANEXO A
new = doc.add_section(WD_SECTION.NEW_PAGE)
new.orientation = 1
new.page_width, new.page_height = Cm(29.7), Cm(21.0)
new.left_margin = new.right_margin = Cm(2.0)
new.top_margin = new.bottom_margin = Cm(2.0)
new.different_first_page_header_footer = False
h1("Anexo A – Tabelas completas dos experimentos")
para("Geradas por `scripts/analyze.py` a partir dos dados brutos (`results/*.csv`). Médias de 3 repetições.", first=0, size=10)


def anexo():
    path = os.path.join(RES, "tabelas_resumo.md")
    txt = open(path, encoding="utf-8").read()
    for blk in re.split(r"\n## ", txt)[1:]:
        title, _, rest = blk.partition("\n")
        rows = [ln for ln in rest.splitlines() if ln.startswith("|")]
        rows = [r for i, r in enumerate(rows) if i != 1]
        cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
        if not cells:
            continue
        n = len(cells[0])
        usable = 25.5
        first = 2.6 if n > 8 else 3.4
        w = [first] + [(usable - first) / (n - 1)] * (n - 1)
        h2(title)
        table(cells, w, size=7 if n > 9 else 8)


anexo()
doc.core_properties.author = "Leticia da Mata Cavalcanti"
doc.core_properties.title = TITULO
doc.save(OUT)
print("salvo:", OUT)
