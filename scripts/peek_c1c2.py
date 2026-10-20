"""Resumo rápido (médias) do C1/C2 no terminal."""
import collections
import csv
import os
import statistics as st

here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(here, "..", "results", "c1_c2_read_mmap.csv"))))
g = collections.defaultdict(list)
for r in rows:
    g[(int(r["size_mb"]), r["method"], r["pattern"], r["cache"])].append(r)
for k, v in sorted(g.items()):
    f = lambda c: st.mean(float(x[c]) for x in v)
    print(k, "open_ms=%.3f read_ms=%.1f rss+MB=%.0f vszMB=%.0f maj=%.0f min=%.0f io_MB=%.0f" % (
        f("t_open_s") * 1000, f("t_read_s") * 1000, (f("rss_after_kb") - f("rss_before_kb")) / 1024,
        f("vsz_delta_kb") / 1024, f("majflt"), f("minflt"), f("read_bytes") / 1048576))
