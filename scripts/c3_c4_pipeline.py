"""C3 (concorrência e fila) e C4 (cache compartilhado) sobre o pipeline completo."""
import json
import os
import sys

from common import append_rows, ensure_index, env_info, flat, out_path
from genresearch.corpus import make_workload
from genresearch.server import Config, Server

REPS = int(os.environ.get("REPS", "3"))
N_REQ = int(os.environ.get("N_REQ", "400"))
LOGDIR = os.path.dirname(out_path("logs", "x"))


def run_one(tag, idx, cfg, workload, rep, extra):
    # log completo só na 1ª repetição (evita milhares de linhas redundantes no repositório)
    suffix = "_".join(str(v) for v in extra.values())
    cfg.log_path = os.path.join(LOGDIR, f"{tag}_{suffix}.log") if rep == 1 else None
    r = Server(idx, cfg).run(workload)
    row = {"exp": tag, "rep": rep, **extra, **flat({k: v for k, v in r.items() if k != "config"})}
    print(f"{tag} rep{rep} {extra} rps={r['throughput_rps']:.1f} p95={r['latency']['p95']*1000:.1f}ms "
          f"qmax={r['queue']['max_len']} util={r['utilization']:.2f} hit={r['cache']['hit_rate']:.2f} "
          f"lost={r['lost']} dup={r['duplicated']}", flush=True)
    return row


def c3():
    idx, st = ensure_index(2000)
    wl = make_workload(N_REQ, N_REQ, 0.0)         # consultas todas distintas, cache desligado
    rows = []
    qcaps = [int(x) for x in os.environ.get("C3_QCAPS", "4,64").split(",")]
    wlist = [int(x) for x in os.environ.get("C3_WORKERS", "1,2,4,8").split(",")]
    for qcap in qcaps:
        for w in wlist:
            for rep in range(1, REPS + 1):
                cfg = Config(workers=w, producers=2, queue_cap=qcap, cache_cap=0, gen_rounds=3000)
                rows.append(run_one("c3", idx, cfg, wl, rep, {"workers": w, "queue_cap": qcap}))
    append_rows(out_path(os.environ.get("C3_OUT", "c3_concurrency.csv")), rows)


def c4():
    idx, st = ensure_index(2000)
    scenarios = [
        ("distintas", dict(distinct=N_REQ, repeat_ratio=0.0, mode="exact")),
        ("repetidas50", dict(distinct=N_REQ, repeat_ratio=0.5, mode="exact")),
        ("repetidas90", dict(distinct=N_REQ, repeat_ratio=0.9, mode="exact")),
        ("parafrase50", dict(distinct=N_REQ, repeat_ratio=0.5, mode="para")),
    ]
    rows = []
    for name, kw in scenarios:
        wl = make_workload(N_REQ, **kw)
        for cap, pol in ((0, "lru"), (16, "lru"), (16, "fifo"), (64, "lru"), (512, "lru")):
            for rep in range(1, REPS + 1):
                cfg = Config(workers=2, producers=2, queue_cap=32, cache_cap=cap, cache_policy=pol, gen_rounds=3000)
                rows.append(run_one("c4", idx, cfg, wl, rep,
                                    {"scenario": name, "cache_cap": cap, "policy": pol}))
    append_rows(out_path("c4_cache.csv"), rows)


if __name__ == "__main__":
    todo = sys.argv[1:] or ["c3", "c4"]
    for name, fn, dest in (("c3", c3, "c3_concurrency.csv"), ("c4", c4, "c4_cache.csv")):
        if name in todo:
            dest = os.environ.get("C3_OUT", dest) if name == "c3" else dest
            if os.path.exists(out_path(dest)):
                os.remove(out_path(dest))
            fn()
