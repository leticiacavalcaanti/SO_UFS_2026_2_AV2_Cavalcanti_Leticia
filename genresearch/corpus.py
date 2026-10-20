"""Corpus sintético determinístico (nenhum dado real ou pessoal).

Cada documento pertence a um tópico; 70% das palavras vêm do vocabulário do
tópico e 30% do vocabulário global. Assim consultas geradas a partir de um
tópico recuperam, de fato, trechos daquele tópico.
"""
import json
import os
import random

SYLL = ["ba", "ce", "di", "fo", "gu", "ha", "je", "ki", "lo", "mu", "na", "pe",
        "qui", "ro", "su", "ta", "ve", "xo", "zi", "bra", "tre", "pla", "cro", "gli"]
N_TOPICS = 12
GLOBAL_WORDS = 1500
TOPIC_WORDS = 120


def _word(rng):
    return "".join(rng.choice(SYLL) for _ in range(rng.randint(2, 4)))


class Vocab:
    def __init__(self, seed=42):
        rng = random.Random(seed)
        seen = set()
        pool = []
        while len(pool) < GLOBAL_WORDS + N_TOPICS * TOPIC_WORDS:
            w = _word(rng)
            if w not in seen:
                seen.add(w)
                pool.append(w)
        self.global_words = pool[:GLOBAL_WORDS]
        rest = pool[GLOBAL_WORDS:]
        self.topics = [rest[i * TOPIC_WORDS:(i + 1) * TOPIC_WORDS] for i in range(N_TOPICS)]


def generate_docs(out_dir, n_docs, words_per_doc=1000, seed=42):
    """Grava n_docs arquivos .txt em out_dir. Retorna bytes totais."""
    os.makedirs(out_dir, exist_ok=True)
    v = Vocab(seed)
    rng = random.Random(seed + 1)
    total = 0
    for i in range(n_docs):
        topic = i % N_TOPICS
        words = [rng.choice(v.topics[topic]) if rng.random() < 0.7
                 else rng.choice(v.global_words) for _ in range(words_per_doc)]
        lines = [" ".join(words[j:j + 12]) + "." for j in range(0, len(words), 12)]
        text = "\n".join(lines) + "\n"
        with open(os.path.join(out_dir, f"doc_{i:06d}_t{topic:02d}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
        total += len(text.encode("utf-8"))
    with open(os.path.join(out_dir, "MANIFEST.json"), "w") as f:
        json.dump({"n_docs": n_docs, "words_per_doc": words_per_doc, "seed": seed}, f)
    return total


def make_queries(n, seed=7, vocab_seed=42, words=6):
    """Consultas distintas: cada uma sorteia um tópico e `words` palavras dele."""
    v = Vocab(vocab_seed)
    rng = random.Random(seed)
    out = []
    for i in range(n):
        t = rng.randrange(N_TOPICS)
        out.append((i, " ".join(rng.sample(v.topics[t], words)), t))
    return out


def paraphrase(text, rng):
    """Mesma consulta com ordem das palavras alterada e caixa diferente."""
    w = text.split()
    rng.shuffle(w)
    return " ".join(x.upper() if rng.random() < 0.3 else x for x in w)


def make_workload(n, distinct, repeat_ratio, seed=11, mode="exact"):
    """Sequência de n consultas.

    repeat_ratio: probabilidade de repetir uma consulta já emitida.
    mode='exact' repete o texto idêntico; 'para' repete reordenado (mesmo
    significado, texto diferente); consultas novas vêm do pool de `distinct`.
    """
    pool = make_queries(distinct, seed=seed)
    rng = random.Random(seed + 100)
    seen, seq, nxt = [], [], 0
    for qid in range(n):
        if seen and rng.random() < repeat_ratio:
            txt = rng.choice(seen)
            if mode == "para":
                txt = paraphrase(txt, rng)
        else:
            txt = pool[nxt % len(pool)][1]
            nxt += 1
            seen.append(txt)
        seq.append((qid, txt))
    return seq
