"""Teste rápido de ponta a ponta."""
import json
from common import ensure_index
from genresearch.corpus import make_workload
from genresearch.server import Config, Server

idx, st = ensure_index(200)
print({k: v for k, v in st.items() if k != "ingest_per_doc_s"})
srv = Server(idx, Config(workers=2, cache_cap=32))
r = srv.run(make_workload(200, 50, 0.5))
print(json.dumps({k: r[k] for k in ("wall_s", "ok", "errors", "lost", "duplicated", "throughput_rps",
                                    "latency", "queue", "utilization", "cache", "os")}, indent=1, default=str))
