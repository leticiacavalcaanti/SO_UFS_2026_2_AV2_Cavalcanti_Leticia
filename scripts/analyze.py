"""Gera gráficos (results/fig_*.png) e tabelas (results/tabelas_resumo.md) a partir dos CSV brutos."""
import collections
import csv
import json
import os
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "..", "results")

# paleta categórica (ordem fixa) e tintas — tokens do tema claro do skill dataviz
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
    "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left", "legend.frameon": False,
})


def load(name):
    p = os.path.join(R, name)
    if not os.path.exists(p):
        return []
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    for r in rows:
        for k, v in r.items():
            try:
                r[k] = float(v)
            except (ValueError, TypeError):
                pass
    return rows


def grp(rows, *keys):
    g = collections.defaultdict(list)
    for r in rows:
        g[tuple(r[k] for k in keys)].append(r)
    return g


def mean_sd(rows, col):
    xs = [r[col] for r in rows]
    return st.mean(xs), (st.stdev(xs) if len(xs) > 1 else 0.0)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(R, name), dpi=170)
    plt.close(fig)


md = ["# Tabelas-resumo (geradas por scripts/analyze.py)\n"]


def table(title, header, rows):
    md.append(f"\n## {title}\n")
    md.append("| " + " | ".join(header) + " |")
    md.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        md.append("| " + " | ".join(str(x) for x in r) + " |")


# ------------------------------------------------------------------ C1/C2
def c1c2():
    rows = load("c1_c2_read_mmap.csv")
    if not rows:
        return
    g = grp(rows, "size_mb", "method", "pattern", "cache")
    out = []
    for k, v in sorted(g.items()):
        m = lambda c: mean_sd(v, c)[0]
        out.append([int(k[0]), k[1], k[2], k[3], f"{m('t_open_s')*1000:.3f}", f"{m('t_read_s')*1000:.1f}",
                    f"{(m('rss_after_kb')-m('rss_before_kb'))/1024:.0f}", f"{m('vsz_delta_kb')/1024:.0f}",
                    f"{m('majflt'):.0f}", f"{m('minflt'):.0f}", f"{m('read_bytes')/1048576:.0f}"])
    table("C1/C2 — leitura convencional x mmap (médias de 3 repetições)",
          ["MB", "método", "padrão", "cache", "abertura (ms)", "leitura (ms)", "ΔRSS (MB)", "ΔVSZ (MB)",
           "falhas maiores", "falhas menores", "lido do disco (MB)"], out)

    # figura: tempo de leitura sequencial (768 MB) frio/quente + ΔRSS
    big = max(r["size_mb"] for r in rows)
    meths = [("read_stream", "read() em blocos"), ("read_all", "read() tudo"), ("mmap", "mmap")]
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.4))
    for j, (state, ttl) in enumerate((("cold", "1ª execução (fria)"), ("warm", "2ª (quente)"))):
        for i, (m, lab) in enumerate(meths):
            v = g[(big, m, "seq", state)]
            mu, sd = mean_sd(v, "t_read_s")
            ax[j].bar(i, mu * 1000, 0.6, yerr=sd * 1000, color=C[i], capsize=3, label=lab)
        ax[j].set_xticks(range(3), ["read\nblocos", "read\ntudo", "mmap"])
        ax[j].set_title(f"Tempo — {ttl}")
        ax[j].set_ylabel("tempo (ms)")
    for i, (m, lab) in enumerate(meths):
        v = g[(big, m, "seq", "cold")]
        d = [(r["rss_after_kb"] - r["rss_before_kb"]) / 1024 for r in v]
        ax[2].bar(i, st.mean(d), 0.6, color=C[i])
    ax[2].set_xticks(range(3), ["read\nblocos", "read\ntudo", "mmap"])
    ax[2].set_title("Δ RSS após a leitura")
    fig.suptitle(f"Leitura sequencial de {int(big)} MB: read() em blocos, read() inteiro e mmap", x=0.01, ha="left", fontsize=10, color=INK2)
    ax[2].set_ylabel("MB")
    save(fig, "fig_c1c2_leitura.png")

    # figura: acesso aleatório frio — bytes lidos do disco e faltas maiores
    fig, ax = plt.subplots(1, 2, figsize=(8, 3.2))
    for i, (m, lab) in enumerate((("read_stream", "pread() 4 KiB"), ("mmap", "mmap"))):
        v = g[(big, m, "rand", "cold")]
        ax[0].bar(i, mean_sd(v, "read_bytes")[0] / 1048576, 0.6, color=C[i])
        ax[1].bar(i, mean_sd(v, "t_read_s")[0] * 1000, 0.6, color=C[i])
    for a, t, y in ((ax[0], "Lido do disco (3000 acessos de 4 KiB)", "MB"), (ax[1], "Tempo (frio)", "ms")):
        a.set_xticks([0, 1], ["pread()", "mmap"])
        a.set_title(t)
        a.set_ylabel(y)
    save(fig, "fig_c1c2_aleatorio.png")


# ------------------------------------------------------------------ C3
def c3():
    rows = load("c3_concurrency.csv")
    if not rows:
        return
    g = grp(rows, "queue_cap", "workers")
    out = []
    for k, v in sorted(g.items()):
        out.append([int(k[0]), int(k[1]), f"{mean_sd(v,'throughput_rps')[0]:.1f} ± {mean_sd(v,'throughput_rps')[1]:.1f}",
                    f"{mean_sd(v,'latency_median')[0]*1000:.1f}", f"{mean_sd(v,'latency_p95')[0]*1000:.1f}",
                    f"{mean_sd(v,'queue_avg_len')[0]:.1f}", f"{mean_sd(v,'queue_max_len')[0]:.0f}",
                    f"{mean_sd(v,'queue_wait_mean')[0]*1000:.1f}", f"{mean_sd(v,'utilization')[0]:.2f}",
                    f"{mean_sd(v,'queue_producer_block_s')[0]:.2f}",
                    f"{mean_sd(v,'os_rss_max_kb')[0]/1024:.0f}", f"{mean_sd(v,'os_threads_max')[0]:.0f}",
                    int(sum(r['lost'] for r in v)), int(sum(r['duplicated'] for r in v))])
    table("C3 — concorrência e fila (400 requisições distintas, cache desligado, 2 produtores)",
          ["fila", "workers", "vazão (req/s)", "latência mediana (ms)", "p95 (ms)", "fila média", "fila máx",
           "espera na fila média (ms)", "utilização", "produtor bloqueado (s)", "RSS máx (MB)", "threads máx",
           "perdidas", "duplicadas"], out)
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
    for i, qc in enumerate((4, 64)):
        ws = [1, 2, 4, 8]
        for a, col, scale, ttl, yl in ((ax[0], "throughput_rps", 1, "Vazão", "req/s"),
                                       (ax[1], "latency_p95", 1000, "Latência p95 (serviço)", "ms"),
                                       (ax[2], "queue_wait_mean", 1000, "Espera média na fila", "ms")):
            mus = [mean_sd(g[(qc, w)], col)[0] * scale for w in ws]
            sds = [mean_sd(g[(qc, w)], col)[1] * scale for w in ws]
            a.errorbar(ws, mus, yerr=sds, color=C[i], marker="o", ms=5, lw=2, capsize=3,
                       label=f"fila = {qc}")
            a.set_xscale("log", base=2)
            a.set_xticks(ws, [str(w) for w in ws])
            a.set_xlabel("trabalhadores (threads)")
            a.set_ylabel(yl)
            a.set_title(ttl)
    ax[0].legend()
    save(fig, "fig_c3_concorrencia.png")


# ------------------------------------------------------------------ C4
def c4():
    rows = load("c4_cache.csv")
    if not rows:
        return
    g = grp(rows, "scenario", "cache_cap", "policy")
    out = []
    for k, v in sorted(g.items()):
        out.append([k[0], int(k[1]), k[2], f"{mean_sd(v,'cache_hit_rate')[0]*100:.1f}",
                    f"{mean_sd(v,'cache_misses')[0]:.0f}", f"{mean_sd(v,'cache_evictions')[0]:.0f}",
                    f"{mean_sd(v,'cache_saved_s')[0]:.2f}",
                    f"{mean_sd(v,'wall_s')[0]:.2f} ± {mean_sd(v,'wall_s')[1]:.2f}",
                    f"{mean_sd(v,'throughput_rps')[0]:.1f}", f"{mean_sd(v,'latency_p95')[0]*1000:.1f}"])
    table("C4 — cache compartilhado (400 requisições, 2 workers)",
          ["cenário", "capacidade", "política", "acerto (%)", "erros (misses)", "substituições",
           "tempo economizado (s)", "tempo total (s)", "vazão (req/s)", "p95 (ms)"], out)
    scen = [("distintas", "tópicos distintos (sem repetição)"), ("repetidas50", "50% repetidas (texto idêntico)"),
            ("repetidas90", "90% repetidas"), ("parafrase50", "50% paráfrases (ordem/caixa)")]
    caps = [0, 16, 64, 512]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    w = 0.2
    for i, (s, lab) in enumerate(scen):
        hr = [mean_sd(g[(s, c, "lru")], "cache_hit_rate")[0] * 100 for c in caps]
        wl = [mean_sd(g[(s, c, "lru")], "wall_s")[0] for c in caps]
        ax[0].bar([j + (i - 1.5) * w for j in range(4)], hr, w - 0.02, color=C[i], label=lab)
        ax[1].plot(range(4), wl, color=C[i], marker="o", lw=2, label=lab)
    for a, t, y in ((ax[0], "Taxa de acerto (LRU)", "%"), (ax[1], "Tempo total da carga (LRU)", "s")):
        a.set_xticks(range(4), [f"{c}" for c in caps])
        a.set_xlabel("capacidade do cache (entradas)")
        a.set_title(t)
        a.set_ylabel(y)
    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=8)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(R, "fig_c4_cache.png"), dpi=170)
    plt.close(fig)


# ------------------------------------------------------------------ C5
def c5():
    rows = load("c5_scale.csv")
    if rows:
        g = grp(rows, "n_docs", "mmap", "ctx_bytes_limit")
        out = []
        for k, v in sorted(g.items()):
            out.append([int(k[0]), f"{v[0]['index_mb']:.0f}", "mmap" if k[1] in (1.0, "True") else "read",
                        int(k[2]), f"{mean_sd(v,'retrieval_median')[0]*1000:.2f}",
                        f"{mean_sd(v,'generation_median')[0]*1000:.1f}", f"{mean_sd(v,'latency_p95')[0]*1000:.1f}",
                        f"{mean_sd(v,'os_rss_max_kb')[0]/1024:.0f}", f"{mean_sd(v,'os_vsz_max_kb')[0]/1024:.0f}",
                        f"{mean_sd(v,'os_majflt')[0]:.0f}", f"{mean_sd(v,'os_minflt')[0]:.0f}",
                        f"{mean_sd(v,'os_read_bytes')[0]/1048576:.0f}", f"{mean_sd(v,'ctx_bytes_mean')[0]:.0f}"])
        table("C5a — crescimento do corpus e do contexto (1 worker, 150 consultas)",
              ["docs", "índice (MB)", "modo", "contexto máx (B)", "recuperação mediana (ms)",
               "geração mediana (ms)", "p95 total (ms)", "RSS máx (MB)", "VSZ máx (MB)", "falhas maiores",
               "falhas menores", "lido do disco (MB)", "contexto médio (B)"], out)
        fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
        docs = sorted({int(r["n_docs"]) for r in rows})
        for i, mm in enumerate((0.0, 1.0)):
            lab = "mmap" if mm else "read (índice na RAM)"
            sel = lambda d, c: mean_sd([r for r in rows if r["n_docs"] == d and r["mmap"] in (mm, bool(mm), str(bool(mm)))
                                        and r["ctx_bytes_limit"] == 2000], c)[0]
            idx_mb = [[r["index_mb"] for r in rows if r["n_docs"] == d][0] for d in docs]
            ax[0].plot(idx_mb, [sel(d, "retrieval_median") * 1000 for d in docs], color=C[i], marker="o", lw=2, label=lab)
            ax[1].plot(idx_mb, [sel(d, "os_rss_max_kb") / 1024 for d in docs], color=C[i], marker="o", lw=2, label=lab)
            ax[2].plot(idx_mb, [sel(d, "os_majflt") for d in docs], color=C[i], marker="o", lw=2, label=lab)
        for a, t, y in ((ax[0], "Recuperação (mediana)", "ms"), (ax[1], "RSS máximo do processo", "MB"),
                        (ax[2], "Faltas de página maiores", "contagem")):
            a.set_xlabel("tamanho do índice vetorial (MB)")
            a.set_title(t)
            a.set_ylabel(y)
        ax[0].legend()
        save(fig, "fig_c5_escala.png")

    # limites de memória (cgroup)
    summ = load("c5_limit_summary.csv")
    d = os.path.join(R, "c5_limit")
    if summ and os.path.isdir(d):
        out = []
        series = {}
        for r in summ:
            name = f"limit_{r['memory_limit']}_{r['mode']}_rep{int(r['rep'])}"
            ev = [json.loads(l) for l in open(os.path.join(d, name + ".jsonl"), encoding="utf-8")
                  if l.startswith("{")]
            q = [e for e in ev if e["event"] == "query"]
            done = [e for e in ev if e["event"] == "done"]
            opn = [e for e in ev if e["event"] == "open_done"]
            out.append([r["memory_limit"], r["mode"], int(r["rep"]), int(r["exit_code"]),
                        "SIM" if r["oom_killed"] in (True, "True", 1.0) else "não",
                        f"{opn[0]['t_s']:.2f}" if opn else "-", len(q),
                        f"{st.median([e['t_s'] for e in q])*1000:.0f}" if q else "-",
                        f"{max(e['rss_kb'] for e in q)/1024:.0f}" if q else "-",
                        f"{q[-1]['majflt']}" if q else "-", f"{q[-1]['read_bytes']/1048576:.0f}" if q else "-",
                        f"{max(e['swap_used_kb'] for e in q)/1024:.0f}" if q else "-"])
            if r["mode"] == "mmap" and int(r["rep"]) == 1 and q:
                series[r["memory_limit"]] = [e["t_s"] * 1000 for e in q]
        table("C5b — índice de 1024 MB sob limite de memória do cgroup (swap do contêiner desligado)",
              ["limite", "modo", "rep", "exit", "OOM kill", "abertura (s)", "consultas concluídas",
               "mediana consulta (ms)", "RSS máx (MB)", "falhas maiores", "lido do disco (MB)", "swap usado (MB)"], out)
        if series:
            fig, ax = plt.subplots(figsize=(6, 3.3))
            for i, (lim, ys) in enumerate(sorted(series.items(), reverse=True)):
                ax.plot(range(1, len(ys) + 1), ys, color=C[i], marker="o", lw=2, label=f"mmap, limite {lim}")
            ax.set_xlabel("consulta nº (varredura completa de 1024 MB)")
            ax.set_ylabel("latência (ms)")
            ax.set_title("Pressão de memória: mmap com índice > limite")
            ax.legend()
            save(fig, "fig_c5_limite.png")


# ------------------------------------------------------------------ C6
def c6():
    rows = load("c6_failures.csv")
    if not rows:
        return
    g = grp(rows, "scenario")
    out = []
    for k, v in g.items():
        out.append([k[0], f"{mean_sd(v,'requests_total')[0]:.0f}", f"{mean_sd(v,'ok')[0]:.0f}",
                    f"{mean_sd(v,'errors')[0]:.0f}", f"{mean_sd(v,'rejected')[0]:.0f}",
                    f"{mean_sd(v,'retries')[0]:.0f}", f"{sum(r['lost'] for r in v):.0f}",
                    f"{mean_sd(v,'wall_s')[0]:.2f}"])
    table("C6 — falhas controladas (média de 3 repetições)",
          ["cenário", "requisições", "ok", "erros", "rejeitadas", "retentativas", "perdidas (tot.)", "tempo (s)"], out)


# ------------------------------------------------------------------ D
def sync():
    d1 = load("d1_cache_race.csv")
    if d1:
        g = grp(d1, "mode")
        out = [[k[0], f"{mean_sd(v,'ops')[0]:.0f}", f"{mean_sd(v,'hits')[0]:.0f}", f"{mean_sd(v,'misses')[0]:.0f}",
                f"{mean_sd(v,'lost_updates')[0]:.0f}", f"{mean_sd(v,'computes')[0]:.0f}",
                f"{mean_sd(v,'duplicate_computes')[0]:.0f}", f"{mean_sd(v,'wall_s')[0]:.2f}"] for k, v in g.items()]
        table("D1 — cache compartilhado: corrida e correções (8 threads × 1500 ops, 40 chaves)",
              ["modo", "ops", "hits contados", "misses contados", "atualizações perdidas", "computações",
               "computações duplicadas", "tempo (s)"], out)
        fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.2))
        modes = [("unsafe", "sem proteção"), ("global_lock", "mutex global"), ("per_key", "lock por chave")]
        for i, (m, lab) in enumerate(modes):
            v = g[(m,)]
            ax[0].bar(i, mean_sd(v, "lost_updates")[0], 0.6, color=C[i])
            ax[1].bar(i, mean_sd(v, "duplicate_computes")[0], 0.6, color=C[i])
            ax[2].bar(i, mean_sd(v, "wall_s")[0], 0.6, color=C[i])
        for a, t, y in ((ax[0], "Atualizações perdidas (contadores)", "contagem"),
                        (ax[1], "Computações duplicadas", "contagem"), (ax[2], "Tempo total", "s")):
            a.set_xticks(range(3), [m[1].replace(" ", "\n") for m in modes])
            a.set_title(t)
            a.set_ylabel(y)
        save(fig, "fig_d1_corrida_cache.png")
    d2 = load("d2_log_race.csv")
    if d2:
        g = grp(d2, "logger")
        table("D2 — log concorrente", ["logger", "eventos", "linhas no arquivo", "linhas corrompidas (média)"],
              [[k[0], f"{mean_sd(v,'events_written')[0]:.0f}", f"{mean_sd(v,'lines_in_file')[0]:.0f}",
                f"{mean_sd(v,'corrupted_lines')[0]:.0f}"] for k, v in g.items()])
    d3 = load("d3_prodcons.csv")
    if d3:
        g = grp(d3, "scenario", "capacity")
        table("D3 — produtores/consumidores com buffer limitado (3 produtores × 500 itens, 2 consumidores)",
              ["cenário", "capacidade", "produzidos", "consumidos", "perdidos", "duplicados", "violações FIFO",
               "ocupação máx", "produtor bloqueado (s)", "consumidor esperou (s)", "tempo (s)"],
              [[k[0], int(k[1]), f"{mean_sd(v,'produced')[0]:.0f}", f"{mean_sd(v,'consumed')[0]:.0f}",
                f"{sum(r['lost'] for r in v):.0f}", f"{sum(r['duplicated'] for r in v):.0f}",
                f"{sum(r['fifo_violations'] for r in v):.0f}", f"{mean_sd(v,'max_len')[0]:.0f}",
                f"{mean_sd(v,'producer_block_s')[0]:.2f}", f"{mean_sd(v,'consumer_wait_s')[0]:.2f}",
                f"{mean_sd(v,'wall_s')[0]:.2f}"] for k, v in sorted(g.items())])
    d4 = load("d4_deadlock.csv")
    if d4:
        g = grp(d4, "mode")
        table("D4 — deadlock isolado em subprocesso", ["modo", "concluiu", "tempo (s)", "resultado"],
              [[k[0], "sim" if all(r["completed"] in (True, "True") for r in v) else "NÃO",
                f"{mean_sd(v,'elapsed_s')[0]:.2f}", v[0]["outcome"]] for k, v in g.items()])


if __name__ == "__main__":
    for f in (c1c2, c3, c4, c5, c6, sync):
        f()
    with open(os.path.join(R, "tabelas_resumo.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print("ok")
