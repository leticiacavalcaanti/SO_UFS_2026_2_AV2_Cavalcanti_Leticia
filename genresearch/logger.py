"""Logs de eventos. SafeLogger serializa a escrita com mutex; UnsafeLogger é só para a demonstração de corrida."""
import os
import threading
import time


class SafeLogger:
    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self._f = open(path or os.devnull, "a", encoding="utf-8")

    def log(self, event, **kv):
        line = f"{time.time():.6f} {event} " + " ".join(f"{k}={v}" for k, v in kv.items()) + "\n"
        with self._lock:
            self._f.write(line)

    def close(self):
        with self._lock:
            self._f.flush()
            self._f.close()


class UnsafeLogger(SafeLogger):
    """Escreve a linha em três partes, sem lock, cedendo a CPU entre elas (provoca log intercalado)."""

    def log(self, event, **kv):
        self._f.write(f"{time.time():.6f} ")
        time.sleep(0)
        self._f.write(f"{event} ")
        time.sleep(0)
        self._f.write(" ".join(f"{k}={v}" for k, v in kv.items()) + "\n")
