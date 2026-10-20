"""Buffer limitado produtor/consumidor com semáforos empty/full e mutex."""
import threading
import time
from collections import deque


class BoundedBuffer:
    """empty = vagas livres, full = itens disponíveis, mutex protege a estrutura.

    put(): bloqueia (ou expira com timeout) quando o buffer está cheio.
    get(): bloqueia (ou expira com timeout) quando está vazio.
    Atribui número de sequência sob o mutex e verifica a ordem FIFO na saída.
    """

    def __init__(self, capacity):
        self.capacity = capacity
        self._buf = deque()
        self._empty = threading.Semaphore(capacity)
        self._full = threading.Semaphore(0)
        self._mutex = threading.Lock()
        self._seq = 0
        self._last_out = -1
        self.fifo_violations = 0
        self.put_ok = self.put_rejected = self.got = 0
        self.max_len = 0
        self._len_sum = 0
        self._len_n = 0
        self.put_block_s = 0.0

    def put(self, item, timeout=None):
        t0 = time.perf_counter()
        if not self._empty.acquire(timeout=timeout):
            with self._mutex:
                self.put_rejected += 1
            return False
        waited = time.perf_counter() - t0
        with self._mutex:
            self._buf.append((self._seq, time.perf_counter(), item))
            self._seq += 1
            self.put_ok += 1
            self.put_block_s += waited
            n = len(self._buf)
            self.max_len = max(self.max_len, n)
            self._len_sum += n
            self._len_n += 1
        self._full.release()
        return True

    def get(self, timeout=None):
        """Retorna (item, espera_na_fila_s) ou None se expirar."""
        if not self._full.acquire(timeout=timeout):
            return None
        with self._mutex:
            seq, t_in, item = self._buf.popleft()
            if seq < self._last_out:
                self.fifo_violations += 1
            self._last_out = seq
            self.got += 1
            self._len_sum += len(self._buf)
            self._len_n += 1
        self._empty.release()
        return item, time.perf_counter() - t_in

    def stats(self):
        with self._mutex:
            return {"capacity": self.capacity, "max_len": self.max_len,
                    "avg_len": self._len_sum / self._len_n if self._len_n else 0.0,
                    "put_ok": self.put_ok, "put_rejected": self.put_rejected,
                    "got": self.got, "producer_block_s": self.put_block_s,
                    "fifo_violations": self.fifo_violations}
