import os
import json
from typing import List, Dict, Any, Optional
from app.config import settings
from app.db import search_fts5, get_db_connection
from retrieval.embeddings import embedding_service
from retrieval.chunker import chunk_article

class VectorStoreManager:
    def __init__(self):
        self.client = None
        self.collection = None
        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            self.collection = self.client.get_or_create_collection(
                name="knowledge_brain_chunks",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            # In-memory fallback if chromadb persistent storage hits filesystem issue
            self.collection = None

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        
        # Extract article_id to delete old chunks first (idempotent per spec)
        article_ids = list(set(c["article_id"] for c in chunks))
        for aid in article_ids:
            self.delete_article_chunks(aid)

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [
            {
                "article_id": c["article_id"],
                "title": c["title"],
                "url": c["url"],
                "heading": c.get("heading", ""),
                "image_ids": json.dumps(c.get("image_ids", [])),
                "chunk_index": c.get("chunk_index", 0)
            }
            for c in chunks
        ]
        embeddings = embedding_service.embed_documents(texts)

        if self.collection:
            try:
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
            except Exception as e:
                print(f"[vector_store] Chroma upsert warning: {e}")

    def delete_article_chunks(self, article_id: str):
        if self.collection:
            try:
                self.collection.delete(where={"article_id": article_id})
            except Exception:
                pass

    def search_vector(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.collection:
            return []
        try:
            q_emb = embedding_service.embed_query(query)
            results = self.collection.query(
                query_embeddings=[q_emb],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            hits = []
            if results and results["ids"] and len(results["ids"][0]) > 0:
                for idx in range(len(results["ids"][0])):
                    doc = results["documents"][0][idx]
                    meta = results["metadatas"][0][idx]
                    dist = results["distances"][0][idx] if "distances" in results else 0.5
                    score = 1.0 - max(0.0, min(1.0, dist)) # cosine similarity approx
                    hits.append({
                        "article_id": meta["article_id"],
                        "title": meta["title"],
                        "url": meta["url"],
                        "heading": meta.get("heading", ""),
                        "text": doc,
                        "score": score,
                        "image_ids": json.loads(meta.get("image_ids", "[]"))
                    })
            return hits
        except Exception as e:
            return []

vector_store = VectorStoreManager()

def hybrid_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Executes hybrid search combining ChromaDB vector similarity (top 20)
    and SQLite FTS5 BM25 keyword matching (top 20) using Reciprocal Rank Fusion (RRF).
    RRF formula: score = sum( 1.0 / (60 + rank) )
    """
    vector_results = vector_store.search_vector(query, top_k=20)
    fts_results = search_fts5(query, top_k=20)

    rrf_scores: Dict[str, float] = {}
    doc_registry: Dict[str, Dict[str, Any]] = {}

    # Process vector ranks
    for rank, item in enumerate(vector_results, 1):
        key = item["url"] + "::" + item.get("heading", "")
        rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (60.0 + rank))
        if key not in doc_registry:
            doc_registry[key] = item

    # Process FTS5 keyword ranks
    for rank, item in enumerate(fts_results, 1):
        key = item["url"] + "::"
        rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (60.0 + rank))
        if key not in doc_registry:
            doc_registry[key] = {
                "article_id": item["article_id"],
                "title": item["title"],
                "url": item["url"],
                "heading": item["title"],
                "text": item.get("parsed_text", "")[:600],
                "score": 0.5,
                "image_ids": []
            }

    # Sort by RRF score descending
    sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)
    final_results = []
    
    # Check that removed articles never appear in answers
    conn = get_db_connection()
    active_rows = conn.execute("SELECT url FROM pages WHERE active = 1").fetchall()
    active_urls = set(r["url"] for r in active_rows)
    conn.close()

    for k in sorted_keys:
        item = doc_registry[k]
        if item["url"] in active_urls or item["url"].startswith("expert:"):
            # Attach normalized RRF score
            item_copy = dict(item)
            item_copy["rrf_score"] = rrf_scores[k]
            final_results.append(item_copy)
        if len(final_results) >= top_k:
            break

    return final_results
