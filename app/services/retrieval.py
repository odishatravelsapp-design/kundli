"""Tiny dependency-free BM25 retrieval over the bundled knowledge base.

This is the free "ML" retrieval layer: when an LLM is configured we use it
for RAG grounding; without an LLM the top passages are appended to the
rule-based report directly.
"""
from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path

KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge.json"
_token = re.compile(r"[a-z]+")


def _tokens(text: str) -> list[str]:
    return _token.findall(text.lower())


@lru_cache
def _index():
    docs = json.loads(KB_PATH.read_text(encoding="utf-8"))
    corpus = [_tokens(d["text"] + " " + " ".join(d.get("tags", [])))
              for d in docs]
    df: dict[str, int] = {}
    for toks in corpus:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    avgdl = sum(len(t) for t in corpus) / max(1, len(corpus))
    return docs, corpus, df, avgdl


def retrieve(query: str, k: int = 6) -> list[dict]:
    docs, corpus, df, avgdl = _index()
    n = len(docs)
    q = _tokens(query)
    k1, b = 1.5, 0.75
    scores = []
    for i, toks in enumerate(corpus):
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        for t in q:
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (
                tf[t] + k1 * (1 - b + b * len(toks) / avgdl))
        scores.append((s, i))
    scores.sort(reverse=True)
    return [docs[i] for s, i in scores[:k] if s > 0]
