"""Chunking e embeddings simulados (hashing trick).

O chunking por palavras com sobreposição segue a ideia do ChunkingService do
projeto glpimentor_servicoia (autoria própria). Os vetores são simulados: cada
token vira +1/-1 em uma posição derivada de crc32, depois normaliza-se (L2),
de modo que cosseno = produto escalar.
"""
import re
import zlib
from functools import lru_cache

import numpy as np

_TOKEN = re.compile(r"\w+", re.UNICODE)
STOP = {"de", "a", "o", "e", "do", "da", "em", "um", "uma", "para", "com"}


def tokenize(text):
    return _TOKEN.findall(text.lower())


def chunk_words(words, size=100, overlap=20):
    if size <= 0 or not (0 <= overlap < size):
        raise ValueError("chunk_size > 0 e 0 <= overlap < chunk_size")
    step = size - overlap
    out = []
    for start in range(0, max(len(words), 1), step):
        piece = words[start:start + size]
        if piece:
            out.append(piece)
        if start + size >= len(words):
            break
    return out


@lru_cache(maxsize=200_000)
def _slot(tok, dim):
    h = zlib.crc32(tok.encode("utf-8"))
    return h % dim, 1.0 if (h >> 16) & 1 else -1.0


def embed_tokens(tokens, dim=256):
    v = np.zeros(dim, dtype=np.float32)
    for t in tokens:
        i, s = _slot(t, dim)
        v[i] += s
    n = float(np.linalg.norm(v))
    return v / n if n else v


def embed_text(text, dim=256):
    return embed_tokens(tokenize(text), dim)


def cache_key(text):
    """Chave canônica: tokens únicos ordenados, sem stopwords (paráfrases por reordenação colidem)."""
    return " ".join(sorted({t for t in tokenize(text) if t not in STOP}))
