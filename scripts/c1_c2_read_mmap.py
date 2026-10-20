"""C1 (leitura convencional) vs C2 (mmap) + Parte E (memória virtual e armazenamento).

Para cada tamanho de arquivo, método e padrão de acesso: execução FRIA (páginas do
arquivo despejadas do cache com posix_fadvise(DONTNEED)) e execução QUENTE
(segunda execução, páginas já no cache de páginas). 3 repetições.
"""
import mmap
import os
import random
import sys
import time
import zlib

from common import WORK, append_rows, env_info, out_path
from genresearch import proc

SIZES_MB = [int(x) for x in os.environ.get("C12_SIZES", "16,128,768").split(",")]
REPS = int(os.environ.get("REPS", "3"))
N_RAND = 3000
CHUNK = 1 << 20


def make_file(path, mb):
    if os.path.exists(path) and os.path.getsize(path) == mb << 20:
        return
    with open(path, "wb") as f:
        for _ in range(mb):
            f.write(os.urandom(CHUNK))
        f.flush()
        os.fsync(f.fileno())


def evict(path):
    os.sync()
    fd = os.open(path, os.O_RDONLY)
    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    os.close(fd)


def run_case(path, method, pattern, offs):
    size = os.path.getsize(path)
    s0 = proc.snapshot()
    t0 = time.perf_counter()
    fd = os.open(path, os.O_RDONLY)
    mm = mmap.mmap(fd, 0, access=mmap.ACCESS_READ) if method == "mmap" else None
    t_open = time.perf_counter() - t0
    t1 = time.perf_counter()
    acc, keep = 0, None
    if method == "read_stream" and pattern == "seq":
        while True:
            b = os.read(fd, CHUNK)
            if not b:
                break
            acc = zlib.crc32(b, acc)
    elif method == "read_all":
        with os.fdopen(os.dup(fd), "rb") as f:
            keep = f.read()
        for o in range(0, size, CHUNK):
            acc = zlib.crc32(keep[o:o + CHUNK], acc)
    elif method == "read_stream":
        for o in offs:
            acc = zlib.crc32(os.pread(fd, 4096, o), acc)
    elif method == "mmap" and pattern == "seq":
        for o in range(0, size, CHUNK):
            acc = zlib.crc32(mm[o:o + CHUNK], acc)
    else:
        for o in offs:
            acc = zlib.crc32(mm[o:o + 4096], acc)
    t_read = time.perf_counter() - t1
    s1 = proc.snapshot()          # medido com o mapeamento/buffer ainda vivo
    if mm:
        mm.close()
    os.close(fd)
    del keep
    d = proc.delta(s0, s1)
    return {
        "t_open_s": t_open, "t_read_s": t_read,
        "rss_before_kb": s0["rss_kb"], "rss_after_kb": s1["rss_kb"],
        "vsz_delta_kb": s1["vsz_kb"] - s0["vsz_kb"],
        "minflt": d["minflt"], "majflt": d["majflt"],
        "read_bytes": d["read_bytes"], "syscr": d["syscr"],
        "cached_delta_kb": s1["cached_kb"] - s0["cached_kb"],
        "mb_per_s": (size / 1048576) / t_read if pattern == "seq" and t_read else 0.0,
        "checksum": acc,
    }


def main():
    env = env_info()
    dest = out_path("c1_c2_read_mmap.csv")
    if os.path.exists(dest):
        os.remove(dest)
    rows = []
    cases = [("read_stream", "seq"), ("read_all", "seq"), ("mmap", "seq"),
             ("read_stream", "rand"), ("mmap", "rand")]
    for mb in SIZES_MB:
        path = os.path.join(WORK, f"bigfile_{mb}.bin")
        make_file(path, mb)
        size = os.path.getsize(path)
        for rep in range(1, REPS + 1):
            rng = random.Random(rep)
            offs = [rng.randrange(0, size - 4096) for _ in range(N_RAND)]
            for method, pattern in cases:
                for state in ("cold", "warm"):
                    if state == "cold":
                        evict(path)
                    r = run_case(path, method, pattern, offs)
                    row = {"size_mb": mb, "method": method, "pattern": pattern, "cache": state,
                           "rep": rep, **r, "date_utc": env["date_utc"]}
                    rows.append(row)
                    print(f"{mb:4d}MB {method:11s} {pattern:4s} {state} rep{rep} "
                          f"open={r['t_open_s']*1000:.2f}ms read={r['t_read_s']*1000:.1f}ms "
                          f"rss+={(r['rss_after_kb']-r['rss_before_kb'])//1024}MB "
                          f"maj={r['majflt']} min={r['minflt']} io={r['read_bytes']>>20}MB", flush=True)
    append_rows(dest, rows)
    # consistência: mesmo checksum entre métodos sequenciais do mesmo arquivo/rep
    bad = 0
    for mb in SIZES_MB:
        for rep in range(1, REPS + 1):
            cs = {r["checksum"] for r in rows if r["size_mb"] == mb and r["rep"] == rep and r["pattern"] == "seq"}
            bad += len(cs) != 1
    print("checksums divergentes:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
