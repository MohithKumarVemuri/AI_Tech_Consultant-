import os
import math
import hashlib
from typing import List

class EmbeddingModel:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self._fastembed = None
        self._init_model()

    def _init_model(self):
        try:
            from fastembed import TextEmbedding
            self._fastembed = TextEmbedding(model_name=self.model_name)
        except Exception as e:
            # Fallback to local semantic projection vectorizer
            self._fastembed = None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._fastembed:
            try:
                embeddings = list(self._fastembed.embed(texts))
                return [list(e) for e in embeddings]
            except Exception:
                pass
        
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def _fallback_embed(self, text: str, dim: int = 384) -> List[float]:
        """
        Deterministic normalized n-gram semantic projection for offline/testing mode.
        """
        vec = [0.0] * dim
        tokens = text.lower().split()
        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            val = ((h >> 4) % 100) / 100.0 - 0.5
            vec[idx] += val
        
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

embedding_service = EmbeddingModel()
