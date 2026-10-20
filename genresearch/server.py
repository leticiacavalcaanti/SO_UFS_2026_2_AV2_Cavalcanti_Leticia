"""GenResearch-Servidor: produtores -> fila limitada -> trabalhadores (threads).

Cada trabalhador faz: cache -> embedding da consulta -> recuperação (varredura
do índice) -> montagem de contexto limitado -> geração simulada -> cache.

Por que threads: a carga é mista. A recuperação (numpy matmul), o hash da
geração (hashlib com buffers grandes) e a espera pelo "serviço externo de
geração" (sleep) liberam o GIL; processos custariam cópia do índice e IPC.
"""
import hashlib
import random
import threading
import time
from dataclasses import asdict, dataclass

from . import proc
from .cache import SharedCache
from .embed import cache_key, embed_text
from .logger import SafeLogger
from .store import IndexUnavailable, VectorStore
from .sync import BoundedBuffer


class ExternalServiceError(Exception):
    """Falha simulada do serviço externo de geração."""


@dataclass
class Config:
    workers: int = 2
    producers: int = 2
    queue_cap: int = 32
    cache_cap: int = 128
    cache_policy: str = "lru"
    use_mmap: bool = False
    k: int = 5
    ctx_max_bytes: int = 2000      # limite do contexto (~ctx/4 tokens)
    gen_sleep_ms: float = 20.0     # latência simulada do modelo/serviço
    gen_rounds: int = 300          # CPU simulada: passes de sha256 sobre o contexto
    dim: int = 256
    fail_prob: float = 0.0         # falha do serviço externo (C6)
    retries: int = 3
    retry_backoff_s: float = 0.05
    put_timeout_s: float = None    # None = produtor bloqueia; número = rejeita se a fila ficar cheia
    arrival_gap_ms: float = 0.0    # intervalo entre envios de cada produtor
    log_path: str = None


class Server:
    def __init__(self, index_dir, cfg: Config):
        self.cfg = cfg
        self.store = VectorStore(index_dir, use_mmap=cfg.use_mmap)
        self.cache = SharedCache(cfg.cache_cap, cfg.cache_policy)
        self.log = SafeLogger(cfg.log_path)
        self._rng = random.Random(1234)
        self._rng_lock = threading.Lock()

    # ---- etapas ----------------------------------------------------------
    def _retrying(self, fn, exc, rec):
        """Executa fn com retentativas e recuo linear; conta as retentativas em rec (mesmo se falhar no fim)."""
        n = 0
        while True:
            try:
                return fn()
            except exc as e:
                if n >= self.cfg.retries:
                    raise
                n += 1
                rec["retries"] += 1
                self.log.log("retry", reason=type(e).__name__, n=n)
                time.sleep(self.cfg.retry_backoff_s * n)

    def _generate(self, ctx):
        c = self.cfg
        if c.fail_prob:
            with self._rng_lock:
                fail = self._rng.random() < c.fail_prob
            if fail:
                raise ExternalServiceError("serviço de geração indisponível")
        time.sleep(c.gen_sleep_ms / 1000.0)
        b = ctx.encode("utf-8")
        h = hashlib.sha256()
        for _ in range(c.gen_rounds):
            h.update(b)
        return f"[resposta simulada] {ctx[:60]}... #{h.hexdigest()[:8]}"

    def handle(self, qid, text):
        c = self.cfg
        t0 = time.perf_counter()
        rec = {"qid": qid, "ok": False, "cache_hit": False, "retries": 0,
               "t_retr": 0.0, "t_gen": 0.0, "ctx_bytes": 0, "ctx_chunks": 0}
        key = cache_key(text)
        cached = self.cache.get(key)
        if cached is not None:
            rec.update(ok=True, cache_hit=True)
            self.log.log("cache", qid=qid, result="hit")
            rec["t_total"] = time.perf_counter() - t0
            return rec
        self.log.log("cache", qid=qid, result="miss")
        try:
            tr = time.perf_counter()

            def retrieve():
                q = embed_text(text, c.dim)
                ids, _ = self.store.search(q, c.k)
                return self.store.texts(ids)

            rows = self._retrying(retrieve, IndexUnavailable, rec)
            ctx = ""
            used = 0
            for r in rows:
                if len(ctx) + len(r) > c.ctx_max_bytes:
                    break
                ctx += r + "\n"
                used += 1
            rec["t_retr"] = time.perf_counter() - tr
            rec.update(ctx_bytes=len(ctx), ctx_chunks=used)
            self.log.log("retrieve", qid=qid, chunks=used, ctx_bytes=len(ctx),
                         approx_tokens=len(ctx) // 4)
            tg = time.perf_counter()
            ans = self._retrying(lambda: self._generate(ctx), ExternalServiceError, rec)
            rec["t_gen"] = time.perf_counter() - tg
            self.log.log("generate", qid=qid, ms=f"{rec['t_gen'] * 1000:.2f}", answer=ans[-9:])
            self.cache.put(key, ans, rec["t_retr"] + rec["t_gen"])
            rec["ok"] = True
        except (IndexUnavailable, ExternalServiceError) as e:
            rec["error"] = type(e).__name__
            self.log.log("fail", qid=qid, error=type(e).__name__)
        rec["t_total"] = time.perf_counter() - t0
        return rec

    # ---- execução --------------------------------------------------------
    def run(self, workload, before_start=None):
        """workload: lista de (qid, texto). Retorna dicionário com todas as métricas."""
        c = self.cfg
        buf = BoundedBuffer(c.queue_cap)
        results, busy = [], [0.0] * c.workers
        waits = []
        res_lock = threading.Lock()
        submitted, rejected = [], []
        sub_lock = threading.Lock()

        def worker(wid):
            while True:
                got = buf.get()
                item, wait = got
                if item is None:
                    return
                qid, text = item
                t = time.perf_counter()
                rec = self.handle(qid, text)
                busy[wid] += time.perf_counter() - t
                rec["queue_wait"] = wait
                with res_lock:
                    results.append(rec)
                    waits.append(wait)

        def producer(pid, items):
            for qid, text in items:
                if buf.put((qid, text), timeout=c.put_timeout_s):
                    with sub_lock:
                        submitted.append(qid)
                else:
                    with sub_lock:
                        rejected.append(qid)
                    self.log.log("fail", qid=qid, error="queue_full")
                if c.arrival_gap_ms:
                    time.sleep(c.arrival_gap_ms / 1000.0)

        self.log.log("start", workers=c.workers, producers=c.producers, queue=c.queue_cap)
        if before_start:
            before_start(self)
        sampler = proc.Sampler(0.05)
        s0 = proc.snapshot()
        sampler.start()
        t_start = time.perf_counter()
        ws = [threading.Thread(target=worker, args=(i,), name=f"worker-{i}") for i in range(c.workers)]
        ps = [threading.Thread(target=producer, args=(i, workload[i::c.producers]),
                               name=f"producer-{i}") for i in range(c.producers)]
        for t in ws + ps:
            t.start()
        for t in ps:
            t.join()
        for _ in ws:
            buf.put(None)
        for t in ws:
            t.join()
        wall = time.perf_counter() - t_start
        sampler.stop()
        s1 = proc.snapshot()
        self.log.log("shutdown", requests=len(results), wall_s=f"{wall:.3f}")
        self.log.close()

        done = [r["qid"] for r in results]
        lost = sorted(set(submitted) - set(done))
        dup = len(done) - len(set(done))
        ok = [r for r in results if r["ok"]]
        miss = [r for r in ok if not r["cache_hit"]]
        out = {
            "config": asdict(c),
            "wall_s": wall,
            "requests_total": len(workload),
            "submitted": len(submitted),
            "rejected": len(rejected),
            "processed": len(results),
            "ok": len(ok),
            "errors": len(results) - len(ok),
            "retries": sum(r["retries"] for r in results),
            "lost": len(lost),
            "duplicated": dup,
            "throughput_rps": len(results) / wall if wall else 0.0,
            "latency": proc.summarize([r["t_total"] for r in results]),
            "e2e_latency": proc.summarize([r["t_total"] + r["queue_wait"] for r in results]),
            "retrieval": proc.summarize([r["t_retr"] for r in miss]),
            "generation": proc.summarize([r["t_gen"] for r in miss]),
            "queue_wait": proc.summarize(waits),
            "queue": buf.stats(),
            "utilization": sum(busy) / (c.workers * wall) if wall else 0.0,
            "ctx_bytes_mean": (sum(r["ctx_bytes"] for r in miss) / len(miss)) if miss else 0.0,
            "ctx_chunks_mean": (sum(r["ctx_chunks"] for r in miss) / len(miss)) if miss else 0.0,
            "cache": self.cache.stats(),
            "os": {**proc.delta(s0, s1), **sampler.summary()},
        }
        return out
