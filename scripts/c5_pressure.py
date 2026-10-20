"""C5 — pressão de memória.

Modo 'scale'  : cresce o corpus (docs) e o contexto; compara índice lido para a RAM (read)
                versus mapeado (mmap); registra RSS, VSZ, faltas de página, latência.
Modo 'limit'  : índice sintético MAIOR que o limite de memória do contêiner (cgroup);
                executado por run_all.py com `docker run --memory=... --memory-swap=...`.
                read -> esperado: OOM kill (C6 limite de memória); mmap -> sobrevive paginando.
"""
import json
import os
import sys
import time

import numpy as np

from common import WORK, append_rows, ensure_index, env_info, flat, out_path
from genresearch import proc
from genresearch.corpus import make_workload
from genresearch.server import Config, Server
from genresearch.store import VectorStore

REPS = int(os.environ.get("REPS", "3"))


def evict(path):
    """Despeja as páginas (limpas) do arquivo do cache de páginas: a próxima leitura é "fria"."""
    os.sync()
    fd = os.open(path, os.O_RDONLY)
    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    os.close(fd)


def one(n_docs, use_mmap, ctx):
    """UMA configuração em processo limpo (RSS/VSZ/faltas sem contaminação de execuções anteriores)."""
    idx, st = ensure_index_readonly(n_docs)
    wl = make_workload(150, 150, 0.0)
    cfg = Config(workers=1, producers=1, cache_cap=0, use_mmap=use_mmap, ctx_max_bytes=ctx,
                 k=max(5, ctx // 400), gen_rounds=3000)
    r = Server(idx, cfg).run(wl)
    row = {"n_docs": n_docs, "n_chunks": st["n_chunks"], "index_mb": st["vectors_bytes"] / 1048576,
           "mmap": use_mmap, "ctx_bytes_limit": ctx,
           **flat({k: r[k] for k in ("wall_s", "throughput_rps", "latency", "retrieval", "generation",
                                      "ctx_bytes_mean", "os")})}
    print("ROW " + json.dumps(row), flush=True)


def ensure_index_readonly(n_docs, words=1000, dim=256):
    tag = f"{n_docs}_{words}_{dim}"
    idx = os.path.join(WORK, f"idx_{tag}")
    with open(os.path.join(idx, "stats.json")) as f:
        return idx, json.load(f)


def scale():
    """Pai: constrói os índices (uma vez) e lança cada configuração em um subprocesso novo."""
    import subprocess
    path = out_path("c5_scale.csv")
    if os.path.exists(path):
        os.remove(path)
    rows = []
    for n_docs in (500, 2000, 8000, 24000):
        idx, st = ensure_index(n_docs)
        vp = os.path.join(idx, "vectors.npy")
        for use_mmap in (False, True):
            for ctx in (500, 2000, 8000):
                for rep in range(1, REPS + 1):
                    evict(vp)                       # 1ª consulta de cada execução lê do "disco"
                    p = subprocess.run([sys.executable, os.path.abspath(__file__), "one", str(n_docs),
                                        "1" if use_mmap else "0", str(ctx)],
                                       capture_output=True, text=True, check=True)
                    row = json.loads([l for l in p.stdout.splitlines() if l.startswith("ROW ")][0][4:])
                    row["rep"] = rep
                    rows.append(row)
                    print(f"docs={n_docs} chunks={st['n_chunks']} mmap={use_mmap} ctx={ctx} rep{rep} "
                          f"retr_med={row['retrieval_median']*1000:.2f}ms rss={row['os_rss_max_kb']//1024}MB "
                          f"min={row['os_minflt']} maj={row['os_majflt']} io={row['os_read_bytes']>>20}MB", flush=True)
    append_rows(path, rows)


def make_synthetic_index(mb, dim=256):
    d = os.path.join(WORK, f"synth_{mb}")
    vp = os.path.join(d, "vectors.npy")
    n = (mb << 20) // (dim * 4)
    if os.path.exists(vp) and np.load(vp, mmap_mode="r").shape[0] == n:
        return d, n
    os.makedirs(d, exist_ok=True)
    mm = np.lib.format.open_memmap(vp, mode="w+", dtype=np.float32, shape=(n, dim))
    rng = np.random.default_rng(0)
    for s in range(0, n, 50000):
        blk = rng.standard_normal((min(50000, n - s), dim)).astype(np.float32)
        blk /= np.linalg.norm(blk, axis=1, keepdims=True)
        mm[s:s + len(blk)] = blk
    mm.flush()
    del mm
    return d, n


def limit(mb, mode, queries=15):
    """Executa DENTRO de um contêiner com limite de memória. Imprime uma linha JSON por consulta."""
    d, n = make_synthetic_index(mb)
    evict(os.path.join(d, "vectors.npy"))   # páginas passam a ser carregadas (e cobradas) NESTE cgroup
    st = VectorStore(d, use_mmap=(mode == "mmap"))
    rng = np.random.default_rng(1)
    s0 = proc.snapshot()
    sam = proc.Sampler(0.05)
    sam.start()
    t0 = time.perf_counter()
    print(json.dumps({"event": "open_start", "mode": mode, "index_mb": mb}), flush=True)
    st.open()
    print(json.dumps({"event": "open_done", "t_s": time.perf_counter() - t0, "cg": proc.cgroup()}), flush=True)
    lat = []
    for i in range(queries):
        q = rng.standard_normal(256).astype(np.float32)
        q /= np.linalg.norm(q)
        t = time.perf_counter()
        st.search(q, 5)
        lat.append(time.perf_counter() - t)
        s = proc.snapshot()
        print(json.dumps({"event": "query", "i": i, "t_s": lat[-1], "rss_kb": s["rss_kb"],
                          "majflt": s["majflt"] - s0["majflt"], "minflt": s["minflt"] - s0["minflt"],
                          "cg_current": s["cg_current"], "cg_file": s["cg_file"], "cg_anon": s["cg_anon"],
                          "swap_used_kb": s["swap_total_kb"] - s["swap_free_kb"],
                          "read_bytes": s["read_bytes"] - s0["read_bytes"]}), flush=True)
    sam.stop()
    print(json.dumps({"event": "done", "lat": proc.summarize(lat), "summary": sam.summary(),
                      "cg": proc.cgroup()}), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "scale":
        scale()
    elif sys.argv[1] == "one":
        one(int(sys.argv[2]), sys.argv[3] == "1", int(sys.argv[4]))
    elif sys.argv[1] == "limit":
        limit(int(sys.argv[2]), sys.argv[3])
    elif sys.argv[1] == "prepare":
        make_synthetic_index(int(sys.argv[2]))
