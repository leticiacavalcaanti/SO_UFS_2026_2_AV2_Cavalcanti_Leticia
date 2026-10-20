"""Leitura de métricas do SO via /proc, getrusage e cgroup v2 (Linux)."""
import os
import resource
import threading
import time

PAGE = os.sysconf("SC_PAGE_SIZE")


def _kv(path):
    d = {}
    try:
        with open(path) as f:
            for line in f:
                k, _, v = line.partition(":")
                d[k.strip()] = v.strip()
    except OSError:
        pass
    return d


def _kb(d, key):
    try:
        return int(d.get(key, "0 kB").split()[0])
    except ValueError:
        return 0


def meminfo():
    m = _kv("/proc/meminfo")
    return {
        "mem_total_kb": _kb(m, "MemTotal"),
        "mem_free_kb": _kb(m, "MemFree"),
        "mem_available_kb": _kb(m, "MemAvailable"),
        "cached_kb": _kb(m, "Cached"),
        "swap_total_kb": _kb(m, "SwapTotal"),
        "swap_free_kb": _kb(m, "SwapFree"),
    }


def self_status():
    s = _kv("/proc/self/status")
    return {
        "rss_kb": _kb(s, "VmRSS"),
        "vsz_kb": _kb(s, "VmSize"),
        "hwm_kb": _kb(s, "VmHWM"),
        "threads": int(s.get("Threads", "0") or 0),
    }


def faults():
    ru = resource.getrusage(resource.RUSAGE_SELF)
    return {"minflt": ru.ru_minflt, "majflt": ru.ru_majflt,
            "inblock": ru.ru_inblock, "oublock": ru.ru_oublock}


def io_counters():
    d = _kv("/proc/self/io")
    out = {}
    for k in ("rchar", "wchar", "syscr", "syscw", "read_bytes", "write_bytes"):
        try:
            out[k] = int(d.get(k, "0"))
        except ValueError:
            out[k] = 0
    return out


def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def cgroup():
    """Contadores do cgroup v2 do contêiner (limite, uso, OOM, faltas de página)."""
    base = "/sys/fs/cgroup/"
    cur, mx = _read(base + "memory.current"), _read(base + "memory.max")
    stat, ev = {}, {}
    for line in (_read(base + "memory.stat") or "").splitlines():
        k, _, v = line.partition(" ")
        stat[k] = int(v)
    for line in (_read(base + "memory.events") or "").splitlines():
        k, _, v = line.partition(" ")
        ev[k] = int(v)
    return {
        "cg_current": int(cur) if cur and cur.isdigit() else 0,
        "cg_max": int(mx) if mx and mx.isdigit() else -1,
        "cg_pgfault": stat.get("pgfault", 0),
        "cg_pgmajfault": stat.get("pgmajfault", 0),
        "cg_file": stat.get("file", 0),
        "cg_anon": stat.get("anon", 0),
        "cg_oom_kill": ev.get("oom_kill", 0),
    }


def snapshot():
    d = {"t": time.time()}
    for part in (meminfo(), self_status(), faults(), io_counters(), cgroup()):
        d.update(part)
    return d


class Sampler(threading.Thread):
    """Amostra RSS/VSZ/MemAvailable periodicamente; guarda picos e mínimos."""

    def __init__(self, interval=0.05):
        super().__init__(daemon=True)
        self.interval = interval
        self.samples = []
        self._stop_evt = threading.Event()

    def run(self):
        while not self._stop_evt.is_set():
            self.samples.append(snapshot())
            self._stop_evt.wait(self.interval)

    def stop(self):
        self._stop_evt.set()
        self.join()
        self.samples.append(snapshot())

    def summary(self):
        s = self.samples
        return {
            "rss_max_kb": max(x["rss_kb"] for x in s),
            "vsz_max_kb": max(x["vsz_kb"] for x in s),
            "mem_available_min_kb": min(x["mem_available_kb"] for x in s),
            "swap_used_max_kb": max(x["swap_total_kb"] - x["swap_free_kb"] for x in s),
            "cached_max_kb": max(x["cached_kb"] for x in s),
            "threads_max": max(x["threads"] for x in s),
        }


def delta(a, b, keys=("minflt", "majflt", "read_bytes", "write_bytes",
                      "rchar", "wchar", "syscr", "syscw", "cg_pgfault",
                      "cg_pgmajfault", "cg_oom_kill")):
    return {k: b[k] - a[k] for k in keys}


def summarize(xs):
    """Média, mediana e p95 (interpolação linear) de uma lista de valores."""
    if not xs:
        return {"n": 0, "mean": 0.0, "median": 0.0, "p95": 0.0}
    s = sorted(xs)
    n = len(s)
    pos = 0.95 * (n - 1)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    p95 = s[lo] + (s[hi] - s[lo]) * (pos - lo)
    mid = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"n": n, "mean": sum(s) / n, "median": mid, "p95": p95}
