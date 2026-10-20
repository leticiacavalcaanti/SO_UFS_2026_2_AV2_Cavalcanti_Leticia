"""C6 — falhas controladas: arquivo ausente, índice indisponível (e recuperação),
fila saturada, falha do serviço externo (com e sem retentativas).
(O cenário "limite de memória" está em c5_pressure.py limit, via cgroup.)"""
import os
import shutil
import threading

from common import WORK, append_rows, ensure_index, flat, out_path
from genresearch.corpus import make_workload
from genresearch.server import Config, Server

REPS = int(os.environ.get("REPS", "3"))
LOGDIR = os.path.dirname(out_path("logs", "x"))


def summarize(name, rep, r, extra=None):
    row = {"scenario": name, "rep": rep, **(extra or {}),
           **flat({k: r[k] for k in ("requests_total", "submitted", "rejected", "processed", "ok", "errors",
                                     "retries", "lost", "duplicated", "wall_s", "throughput_rps",
                                     "latency", "queue", "cache")})}
    print(f"{name} rep{rep}: ok={r['ok']} err={r['errors']} rejected={r['rejected']} "
          f"retries={r['retries']} lost={r['lost']} wall={r['wall_s']:.2f}s", flush=True)
    return row


def main():
    idx, st = ensure_index(500)
    rows = []
    wl = make_workload(120, 120, 0.0)
    for rep in range(1, REPS + 1):
        lp = lambda n: os.path.join(LOGDIR, f"c6_{n}.log") if rep == 1 else None

        # 1) arquivo/índice ausente: erro controlado, sem derrubar o processo
        r = Server(os.path.join(WORK, "nao_existe"),
                   Config(workers=2, retries=2, retry_backoff_s=0.01, cache_cap=0, log_path=lp("ausente"))).run(wl[:40])
        rows.append(summarize("arquivo_ausente", rep, r))

        # 2) índice indisponível por ~0,6 s e depois restaurado (recuperação por retentativa)
        tmp = os.path.join(WORK, f"idx_tmp_{rep}")
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(idx, tmp)
        vp = os.path.join(tmp, "vectors.npy")
        os.rename(vp, vp + ".bak")
        threading.Timer(0.6, lambda: os.rename(vp + ".bak", vp)).start()
        r = Server(tmp, Config(workers=2, retries=10, retry_backoff_s=0.05, cache_cap=0,
                               log_path=lp("indice_indisponivel"))).run(wl)
        rows.append(summarize("indice_indisponivel_recupera", rep, r))
        shutil.rmtree(tmp, ignore_errors=True)

        # 3) fila saturada: com timeout o produtor REJEITA; sem timeout ele BLOQUEIA (sem perdas)
        for label, to in (("rejeita", 0.005), ("bloqueia", None)):
            r = Server(idx, Config(workers=1, producers=4, queue_cap=2, put_timeout_s=to, cache_cap=0,
                                   gen_sleep_ms=30, log_path=lp("fila_" + label))).run(wl)
            rows.append(summarize("fila_saturada_" + label, rep, r))

        # 4) serviço externo falhando 30% das vezes: sem e com retentativas
        for tries in (0, 3):
            r = Server(idx, Config(workers=2, fail_prob=0.3, retries=tries, retry_backoff_s=0.01,
                                   cache_cap=0, log_path=lp(f"servico_retries{tries}"))).run(wl)
            rows.append(summarize(f"servico_externo_falha30_retries{tries}", rep, r))
    p = out_path("c6_failures.csv")
    if os.path.exists(p):
        os.remove(p)
    append_rows(p, rows)


if __name__ == "__main__":
    main()
