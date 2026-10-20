"""Parte D — sincronização: falhas controladas e correções.

D1  Cache compartilhado: contadores com atualização perdida + computação duplicada
    (sem proteção) -> mutex global -> lock por chave (single-flight). Mede correção e custo.
D2  Log: escrita concorrente intercalada (sem lock) vs SafeLogger (mutex).
D3  Produtor/consumidor: buffer limitado (empty/full/mutex) — sem perdas, sem duplicatas, FIFO.
D4  Deadlock (espera circular) em SUBPROCESSO, detectado por timeout, encerrado (kill) e
    corrigido por ordenação global de locks e por acquire com timeout + recuo.
As "janelas de corrida" são ampliadas com time.sleep(0) e sys.setswitchinterval(1e-6), o que força
trocas de thread nos pontos de leitura-modificação-escrita (injeção de falha controlada).
"""
import os
import re
import subprocess
import sys
import threading
import time

from common import append_rows, out_path
from genresearch.logger import SafeLogger, UnsafeLogger
from genresearch.sync import BoundedBuffer

REPS = int(os.environ.get("REPS", "3"))


# ---------------------------------------------------------------- D1
def cache_race(mode, threads=8, ops=1500, keys=40, compute_s=0.004):
    sys.setswitchinterval(1e-6)
    import itertools
    cache, st = {}, {"hits": 0, "misses": 0}
    truth = itertools.count()          # contador atômico (verdade-base): next() não perde incrementos
    g = threading.Lock()
    key_locks, kl_guard = {}, threading.Lock()

    def bump(name):
        v = st[name]
        time.sleep(0)          # janela da corrida: outra thread pode ler o mesmo valor
        st[name] = v + 1

    def compute(key):
        time.sleep(compute_s)  # custo da recuperação+geração
        next(truth)
        return key * 2

    def op(key):
        if mode == "unsafe":
            if key in cache:
                bump("hits")
            else:
                bump("misses")
                cache[key] = compute(key)
        elif mode == "global_lock":
            with g:
                if key in cache:
                    st["hits"] += 1
                else:
                    st["misses"] += 1
                    cache[key] = compute(key)      # computa segurando o lock global
        else:  # per_key (single-flight)
            with kl_guard:
                kl = key_locks.setdefault(key, threading.Lock())
            with kl:
                with g:
                    present = key in cache
                    if present:
                        st["hits"] += 1
                    else:
                        st["misses"] += 1
                if not present:
                    val = compute(key)
                    with g:
                        cache[key] = val

    def worker(seed):
        import random
        rng = random.Random(seed)
        for _ in range(ops):
            op(rng.randrange(keys))

    t0 = time.perf_counter()
    ts = [threading.Thread(target=worker, args=(i,)) for i in range(threads)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    wall = time.perf_counter() - t0
    total = threads * ops
    computes = next(truth)
    return {"mode": mode, "ops": total, "hits": st["hits"], "misses": st["misses"],
            "lost_updates": total - st["hits"] - st["misses"],
            "computes": computes, "distinct_keys": len(cache),
            "duplicate_computes": computes - len(cache), "wall_s": wall}


# ---------------------------------------------------------------- D2
LINE = re.compile(r"^\d+\.\d{6} \w+ qid=\d+ worker=\d+$")


def log_race(cls, threads=8, per=300):
    sys.setswitchinterval(1e-6)
    path = out_path("logs", f"d2_{cls.__name__}.log")
    if os.path.exists(path):
        os.remove(path)
    lg = cls(path)

    def w(i):
        for j in range(per):
            lg.log("query", qid=j, worker=i)

    ts = [threading.Thread(target=w, args=(i,)) for i in range(threads)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    lg.close()
    with open(path) as f:
        lines = f.read().splitlines()
    bad = sum(1 for l in lines if not LINE.match(l))
    return {"logger": cls.__name__, "events_written": threads * per, "lines_in_file": len(lines),
            "corrupted_lines": bad}


# ---------------------------------------------------------------- D3
def prod_cons(cap, producers=3, consumers=2, per=500, slow=0.0002, pslow=0.0):
    buf = BoundedBuffer(cap)
    consumed, lock = [], threading.Lock()
    cons_wait = [0.0]

    def prod(p):
        for i in range(per):
            if pslow:
                time.sleep(pslow)
            buf.put((p, i))

    def cons():
        while True:
            t = time.perf_counter()
            got = buf.get()
            w = time.perf_counter() - t
            item, _ = got
            if item is None:
                return
            if slow:
                time.sleep(slow)
            with lock:
                consumed.append(item)
                cons_wait[0] += w

    pt = [threading.Thread(target=prod, args=(p,)) for p in range(producers)]
    ct = [threading.Thread(target=cons) for _ in range(consumers)]
    t0 = time.perf_counter()
    [t.start() for t in pt + ct]
    [t.join() for t in pt]
    for _ in ct:
        buf.put(None)
    [t.join() for t in ct]
    wall = time.perf_counter() - t0
    expect = {(p, i) for p in range(producers) for i in range(per)}
    s = buf.stats()
    # ordem por produtor: itens de um mesmo produtor saem da fila em ordem crescente
    # (o log de consumo pode intercalar entre consumidores; a ordem de DESENFILEIRAR é a FIFO verificada)
    return {"capacity": cap, "produced": producers * per, "consumed": len(consumed),
            "lost": len(expect - set(consumed)), "duplicated": len(consumed) - len(set(consumed)),
            "fifo_violations": s["fifo_violations"], "max_len": s["max_len"],
            "producer_block_s": s["producer_block_s"], "consumer_wait_s": cons_wait[0], "wall_s": wall}


# ---------------------------------------------------------------- D4
def deadlock_child(mode):
    A, B = threading.Lock(), threading.Lock()
    bar = threading.Barrier(2)
    done = []

    def circular(first, second, name):
        with first:
            bar.wait()                 # garante que cada thread já segura 1 lock
            with second:               # espera circular: T1 A->B, T2 B->A
                done.append(name)

    def ordered(first, second, name):
        lo, hi = (A, B)                # correção: ordem global (A antes de B) para todas as threads
        with lo:
            with hi:
                done.append(name)

    def backoff(first, second, name):
        used_barrier = False
        while True:
            with first:
                if not used_barrier:
                    used_barrier = True
                    try:
                        bar.wait(timeout=1)
                    except threading.BrokenBarrierError:
                        pass
                if second.acquire(timeout=0.2):   # desiste se não conseguir; libera 'first' e recua
                    try:
                        done.append(name)
                        return
                    finally:
                        second.release()
            time.sleep(0.05 if name == "T1" else 0.11)   # recuo assimétrico evita livelock

    fn = {"deadlock": circular, "ordered": ordered, "timeout": backoff}[mode]
    th = [threading.Thread(target=fn, args=(A, B, "T1")), threading.Thread(target=fn, args=(B, A, "T2"))]
    [x.start() for x in th]
    [x.join() for x in th]
    print("COMPLETED", ",".join(sorted(done)), flush=True)


def thread_states(pid):
    out = []
    for tid in sorted(os.listdir(f"/proc/{pid}/task")):
        try:
            st = open(f"/proc/{pid}/task/{tid}/status").read()
            state = re.search(r"State:\s+(\S+ \(\w+\))", st).group(1)
            wchan = open(f"/proc/{pid}/task/{tid}/wchan").read().strip() or "-"
            out.append(f"tid={tid} state={state} wchan={wchan}")
        except OSError:
            pass
    return out


def deadlock(mode, timeout=3.0):
    p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child", mode],
                         stdout=subprocess.PIPE, text=True)
    t0 = time.time()
    states = []
    while time.time() - t0 < timeout and p.poll() is None:
        time.sleep(0.1)
    if p.poll() is None:
        states = thread_states(p.pid)
        p.kill()                          # mecanismo de encerramento
        p.wait()
        return {"mode": mode, "completed": False, "outcome": "DEADLOCK detectado por timeout; processo encerrado (kill)",
                "elapsed_s": time.time() - t0, "thread_states": " | ".join(states)}
    return {"mode": mode, "completed": True, "outcome": p.stdout.read().strip(),
            "elapsed_s": time.time() - t0, "thread_states": ""}


def main():
    d1, d2, d3, d4 = [], [], [], []
    for rep in range(1, REPS + 1):
        for m in ("unsafe", "global_lock", "per_key"):
            r = cache_race(m)
            d1.append({"rep": rep, **r})
            print("D1", rep, r, flush=True)
        for c in (UnsafeLogger, SafeLogger):
            r = log_race(c)
            d2.append({"rep": rep, **r})
            print("D2", rep, r, flush=True)
        for scen, kw in (("consumidor_lento", dict(slow=0.0004, pslow=0.0)),
                         ("produtor_lento", dict(slow=0.0, pslow=0.0008))):
            for cap in (1, 4, 64):
                r = prod_cons(cap, **kw)
                d3.append({"rep": rep, "scenario": scen, **r})
                print("D3", rep, scen, r, flush=True)
        for m in ("deadlock", "ordered", "timeout"):
            r = deadlock(m)
            d4.append({"rep": rep, **r})
            print("D4", rep, r, flush=True)
    for name, rows in (("d1_cache_race", d1), ("d2_log_race", d2), ("d3_prodcons", d3), ("d4_deadlock", d4)):
        p = out_path(f"{name}.csv")
        if os.path.exists(p):
            os.remove(p)
        append_rows(p, rows)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--child":
        deadlock_child(sys.argv[2])
    else:
        main()
