"""Armazenamento: vetores em .npy (float32, N x D) + metadados/textos em SQLite."""
import glob
import os
import sqlite3
import threading
import time

import numpy as np

from .embed import chunk_words, embed_tokens, tokenize


class IndexUnavailable(Exception):
    """Índice vetorial ausente ou ilegível."""


def build_index(docs_dir, out_dir, dim=256, chunk_size=100, overlap=20, logger=None):
    """Ingestão: lê documentos, fragmenta, vetoriza e persiste.

    Retorna estatísticas, inclusive o tempo de ingestão de cada documento.
    """
    os.makedirs(out_dir, exist_ok=True)
    db_path = os.path.join(out_dir, "meta.sqlite")
    vec_path = os.path.join(out_dir, "vectors.npy")
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, doc TEXT, ordem INTEGER, texto TEXT)")
    vecs, per_doc, corpus_bytes, cid = [], [], 0, 0
    t_all = time.perf_counter()
    for path in sorted(glob.glob(os.path.join(docs_dir, "*.txt"))):
        t0 = time.perf_counter()
        with open(path, encoding="utf-8") as f:
            text = f.read()
        corpus_bytes += len(text.encode("utf-8"))
        rows = []
        for ordem, piece in enumerate(chunk_words(tokenize(text), chunk_size, overlap)):
            rows.append((cid, os.path.basename(path), ordem, " ".join(piece)))
            vecs.append(embed_tokens(piece, dim))
            cid += 1
        con.executemany("INSERT INTO chunks VALUES (?,?,?,?)", rows)
        per_doc.append(time.perf_counter() - t0)
        if logger:
            logger.log("ingest", doc=os.path.basename(path), chunks=len(rows))
    con.commit()
    con.close()
    arr = np.vstack(vecs).astype(np.float32)
    np.save(vec_path, arr)
    return {
        "n_docs": len(per_doc), "n_chunks": cid, "dim": dim,
        "corpus_bytes": corpus_bytes,
        "vectors_bytes": os.path.getsize(vec_path),
        "sqlite_bytes": os.path.getsize(db_path),
        "ingest_total_s": time.perf_counter() - t_all,
        "ingest_per_doc_s": per_doc,
    }


class VectorStore:
    def __init__(self, index_dir, use_mmap=False):
        self.dir = index_dir
        self.use_mmap = use_mmap
        self.vectors = None
        self._tl = threading.local()
        self._open_lock = threading.Lock()

    @property
    def vec_path(self):
        return os.path.join(self.dir, "vectors.npy")

    @property
    def db_path(self):
        return os.path.join(self.dir, "meta.sqlite")

    def open(self):
        """Abre o índice. mmap: mapeia o arquivo (páginas sob demanda); senão lê tudo para a RAM."""
        with self._open_lock:
            if self.vectors is not None:
                return
            try:
                self.vectors = np.load(self.vec_path, mmap_mode="r" if self.use_mmap else None)
            except (FileNotFoundError, OSError, ValueError) as e:
                raise IndexUnavailable(str(e)) from e

    def search(self, q, k=5, block=32768):
        """Top-k por produto escalar, varrendo o índice em blocos (memória limitada)."""
        if self.vectors is None:
            self.open()
        v, n = self.vectors, self.vectors.shape[0]
        best_s = np.empty(0, np.float32)
        best_i = np.empty(0, np.int64)
        for s in range(0, n, block):
            sc = np.asarray(v[s:s + block]) @ q
            kk = min(k, len(sc))
            idx = np.argpartition(sc, -kk)[-kk:]
            best_s = np.concatenate([best_s, sc[idx]])
            best_i = np.concatenate([best_i, idx + s])
            if len(best_s) > k:
                keep = np.argpartition(best_s, -k)[-k:]
                best_s, best_i = best_s[keep], best_i[keep]
        order = np.argsort(-best_s)
        return best_i[order], best_s[order]

    def _con(self):
        con = getattr(self._tl, "con", None)
        if con is None:
            try:
                con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            except sqlite3.Error as e:
                raise IndexUnavailable(str(e)) from e
            self._tl.con = con
        return con

    def texts(self, ids):
        con = self._con()
        out = []
        for i in ids:
            r = con.execute("SELECT texto FROM chunks WHERE id=?", (int(i),)).fetchone()
            out.append(r[0] if r else "")
        return out
