"""Utilidades compartilhadas pelos scripts de experimento."""
import csv
import json
import os
import platform
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from genresearch.corpus import generate_docs  # noqa: E402
from genresearch.store import build_index  # noqa: E402

WORK = os.environ.get("GR_WORK", "/workdata")
RESULTS = os.environ.get("GR_RESULTS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"))


def ensure_index(n_docs, words=1000, dim=256, chunk=100, overlap=20):
    """Gera corpus sintético + índice (uma vez) e devolve (dir_do_índice, estatísticas)."""
    tag = f"{n_docs}_{words}_{dim}"
    docs, idx = os.path.join(WORK, f"docs_{tag}"), os.path.join(WORK, f"idx_{tag}")
    stats_path = os.path.join(idx, "stats.json")
    if not os.path.exists(stats_path):
        generate_docs(docs, n_docs, words)
        st = build_index(docs, idx, dim, chunk, overlap)
        with open(stats_path, "w") as f:
            json.dump(st, f)
    with open(stats_path) as f:
        return idx, json.load(f)


def env_info():
    def sh(cmd):
        try:
            return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            return ""
    import numpy
    return {
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version.split()[0], "numpy": numpy.__version__,
        "kernel": platform.release(), "machine": platform.machine(),
        "cpus": os.cpu_count(),
        "commit": sh("git -C . rev-parse --short HEAD") or "n/a",
    }


def out_path(*parts):
    p = os.path.join(RESULTS, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def append_rows(path, rows):
    new = not os.path.exists(path)
    keys = list(rows[0].keys())
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        if new:
            w.writeheader()
        w.writerows(rows)


def flat(d, prefix=""):
    """Achata dicionários aninhados (config.workers -> config_workers)."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flat(v, key + "_"))
        else:
            out[key] = v
    return out
