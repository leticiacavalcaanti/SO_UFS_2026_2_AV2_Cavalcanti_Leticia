"""Cache compartilhado de respostas (LRU ou FIFO) protegido por mutex."""
import threading
from collections import OrderedDict


class SharedCache:
    def __init__(self, capacity=128, policy="lru"):
        if policy not in ("lru", "fifo"):
            raise ValueError("policy deve ser 'lru' ou 'fifo'")
        self.capacity = capacity
        self.policy = policy
        self._d = OrderedDict()
        self._lock = threading.Lock()
        self.hits = self.misses = self.evictions = 0
        self.saved_s = 0.0

    def get(self, key):
        if self.capacity <= 0:
            with self._lock:
                self.misses += 1
            return None
        with self._lock:
            ent = self._d.get(key)
            if ent is None:
                self.misses += 1
                return None
            self.hits += 1
            self.saved_s += ent[1]
            if self.policy == "lru":
                self._d.move_to_end(key)
            return ent[0]

    def put(self, key, value, cost_s):
        """cost_s: tempo que a resposta custou para ser produzida (economizado a cada acerto)."""
        if self.capacity <= 0:
            return
        with self._lock:
            if key in self._d:
                self._d.move_to_end(key)
            self._d[key] = (value, cost_s)
            while len(self._d) > self.capacity:
                self._d.popitem(last=False)
                self.evictions += 1

    def stats(self):
        with self._lock:
            tot = self.hits + self.misses
            return {"hits": self.hits, "misses": self.misses,
                    "hit_rate": self.hits / tot if tot else 0.0,
                    "evictions": self.evictions, "size": len(self._d),
                    "capacity": self.capacity, "saved_s": self.saved_s}
