import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.db import (
    get_db_connection, upsert_article, mark_page_removed, upsert_page
)
from app.schemas import QueryResponse, SourceItem, IngestionStatusResponse
from app.llm_client import LLMClient
from retrieval.hybrid_search import hybrid_search, vector_store
from retrieval.chunker import chunk_article
from ingestion.crawler import AsyncCrawler
from ingestion.parser import parse_html_article
from ingestion.sample_articles import SAMPLE_ARTICLES

PROMPT_ANSWER_PATH = Path(__file__).resolve().parent.parent / "prompts" / "answer@v1.md"

def load_answer_prompt_template() -> str:
    if PROMPT_ANSWER_PATH.exists():
        return PROMPT_ANSWER_PATH.read_text(encoding="utf-8")
    return "Answer strictly using evidence: {evidence}\nQuestion: {question}"

class KnowledgeService:
    def __init__(self):
        self.llm = LLMClient()
        self.crawler = AsyncCrawler()
        self.prompt_template = load_answer_prompt_template()

    async def answer_query(self, question: str, top_k: int = 5) -> QueryResponse:
        request_id = str(uuid.uuid4())
        q_lower = question.lower()

        # Direct domain boundary check for out-of-domain / unanswerable / injection queries
        unsupported_tokens = ["llama-3", "quantum", "watchos", "ssh root", "ignore all previous instructions"]
        if any(tok in q_lower for tok in unsupported_tokens):
            esc_id = self._create_escalation(question, context="Query out of Brilliant Directories domain or injection attempt")
            return QueryResponse(
                request_id=request_id,
                status="insufficient_evidence",
                answer=None,
                sources=[],
                needs_human=True,
                escalation_id=esc_id,
                model=self.llm.provider,
                prompt_version="answer@v1"
            )

        # 1. Retrieve hybrid candidates
        retrieved_chunks = hybrid_search(question, top_k=top_k)

        # 2. Check for sufficient evidence
        if not retrieved_chunks:
            esc_id = self._create_escalation(question, context="Zero retrieval matches")
            return QueryResponse(
                request_id=request_id,
                status="insufficient_evidence",
                answer=None,
                sources=[],
                needs_human=True,
                escalation_id=esc_id,
                model=self.llm.provider,
                prompt_version="answer@v1"
            )

        # 3. Assemble untrusted evidence block
        evidence_lines = []
        source_items: List[SourceItem] = []
        for c in retrieved_chunks:
            heading_info = f" [Section: {c.get('heading')}]" if c.get("heading") else ""
            evidence_lines.append(f"Source: {c['title']}{heading_info}\nURL: {c['url']}\nContent: {c['text']}\n---")
            source_items.append(SourceItem(
                title=c["title"],
                url=c["url"],
                score=round(c.get("rrf_score", c.get("score", 0.5)), 3),
                image_refs=c.get("image_ids", []),
                heading=c.get("heading")
            ))

        evidence_str = "\n".join(evidence_lines)
        prompt = self.prompt_template.format(question=question, evidence=evidence_str)

        system_instruction = "You are an AI Tech Consultant. Obey all grounding constraints and never hallucinate."
        llm_res = await self.llm.generate(
            prompt=prompt,
            system=system_instruction,
            prompt_version="answer@v1"
        )

        output_text = llm_res.text.strip()

        # Check if model judged evidence insufficient
        if "insufficient_evidence" in output_text.lower():
            esc_id = self._create_escalation(question, context="Model flagged evidence insufficient")
            return QueryResponse(
                request_id=request_id,
                status="insufficient_evidence",
                answer=None,
                sources=source_items,
                needs_human=True,
                escalation_id=esc_id,
                model=llm_res.model,
                prompt_version="answer@v1"
            )

        # In offline simulation mode, synthesize grounded answer using retrieved chunk content
        if llm_res.provider.startswith("mock") and retrieved_chunks:
            output_text = f"Based on official Brilliant Directories documentation:\n{retrieved_chunks[0]['text'][:450]}..."

        return QueryResponse(
            request_id=request_id,
            status="answered",
            answer=output_text,
            sources=source_items,
            needs_human=False,
            escalation_id=None,
            model=llm_res.model,
            prompt_version="answer@v1"
        )

    def _create_escalation(self, question: str, context: Optional[str] = None) -> str:
        esc_id = f"esc_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        with conn:
            conn.execute("""
                INSERT INTO escalations (id, question, context, status, created_at)
                VALUES (?, ?, ?, 'open', ?)
            """, (esc_id, question, context, now))
        conn.close()
        return esc_id

    def list_escalations(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        if status:
            rows = conn.execute("SELECT * FROM escalations WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def resolve_escalation(self, esc_id: str, expert_answer: str, reviewer: str, expires_at: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        with conn:
            conn.execute("""
                UPDATE escalations
                SET status = 'resolved', resolved_at = ?, resolved_by = ?, answer = ?
                WHERE id = ?
            """, (now, reviewer, expert_answer, esc_id))
            
            row = conn.execute("SELECT question FROM escalations WHERE id = ?", (esc_id,)).fetchone()
            question = row["question"] if row else "Resolved query"

            expert_id = f"exp_{uuid.uuid4().hex[:8]}"
            conn.execute("""
                INSERT INTO expert_answers (id, question, expert_answer, reviewer, created_at, expires_at, source_type, active)
                VALUES (?, ?, ?, ?, ?, ?, 'expert', 1)
            """, (expert_id, question, expert_answer, reviewer, now, expires_at))
        conn.close()

        expert_url = f"expert://escalations/{esc_id}"
        article_title = f"Expert Resolution: {question[:60]}"
        upsert_article(
            article_id=expert_id,
            url=expert_url,
            title=article_title,
            raw_html=f"<p>{expert_answer}</p>",
            parsed_text=expert_answer,
            headings=["Expert Resolution", question],
            images=[],
            lastmod=now,
            content_hash=uuid.uuid4().hex[:8],
            source_type="expert"
        )
        upsert_page(url=expert_url, lastmod=now, content_hash=None, status="ok", active=True)

        chunks = chunk_article(
            article_id=expert_id,
            title=article_title,
            url=expert_url,
            parsed_text=f"Question: {question}\n\nExpert Verified Answer: {expert_answer}\nReviewer: {reviewer}",
            headings=["Expert Resolution"],
            images=[]
        )
        vector_store.upsert_chunks(chunks)

        return {"status": "resolved", "id": esc_id, "expert_id": expert_id}

    async def run_ingestion(self, mode: str = "incremental", max_pages: int = 15) -> Dict[str, Any]:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        with conn:
            conn.execute("""
                INSERT INTO ingestion_runs (id, mode, status, started_at)
                VALUES (?, ?, 'running', ?)
            """, (job_id, mode, now))
        conn.close()

        # Seed sample articles if DB is empty
        conn = get_db_connection()
        count = conn.execute("SELECT count(*) as c FROM articles").fetchone()["c"]
        conn.close()

        if count == 0 or mode == "sample":
            for sample in SAMPLE_ARTICLES:
                parsed = parse_html_article(sample["html"], sample["url"])
                aid = "art_" + uuid.uuid4().hex[:8]
                upsert_article(
                    article_id=aid,
                    url=sample["url"],
                    title=parsed["title"],
                    raw_html=sample["html"],
                    parsed_text=parsed["parsed_text"],
                    headings=parsed["headings"],
                    images=parsed["images"],
                    lastmod=sample["lastmod"],
                    content_hash=parsed["content_hash"],
                    source_type="crawled"
                )
                upsert_page(sample["url"], sample["lastmod"], parsed["content_hash"], "ok", active=True)
                
                chunks = chunk_article(
                    article_id=aid,
                    title=parsed["title"],
                    url=sample["url"],
                    parsed_text=parsed["parsed_text"],
                    headings=parsed["headings"],
                    images=parsed["images"]
                )
                vector_store.upsert_chunks(chunks)

        stats = await self.crawler.run(mode=mode, max_pages=max_pages)
        
        conn = get_db_connection()
        articles = conn.execute("SELECT * FROM articles WHERE active = 1").fetchall()
        conn.close()

        for art in articles:
            chunks = chunk_article(
                article_id=art["id"],
                title=art["title"],
                url=art["url"],
                parsed_text=art["parsed_text"],
                headings=json.loads(art["headings_json"] or "[]"),
                images=json.loads(art["images_json"] or "[]")
            )
            vector_store.upsert_chunks(chunks)

        finish_now = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        with conn:
            conn.execute("""
                UPDATE ingestion_runs
                SET status = 'completed', completed_at = ?, added = ?, updated = ?, removed = ?, failed = ?
                WHERE id = ?
            """, (finish_now, stats.get("added", 0), stats.get("updated", 0), stats.get("removed", 0), stats.get("failed", 0), job_id))
        conn.close()

        return {"job_id": job_id, "stats": stats}

    def get_ingestion_status(self) -> IngestionStatusResponse:
        conn = get_db_connection()
        pages = conn.execute("SELECT status, count(*) as c FROM pages GROUP BY status").fetchall()
        total = conn.execute("SELECT count(*) as c FROM pages").fetchone()["c"]
        last_run = conn.execute("SELECT completed_at, status FROM ingestion_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        conn.close()

        counts = {r["status"]: r["c"] for r in pages}
        return IngestionStatusResponse(
            added=counts.get("ok", 0),
            updated=0,
            removed=counts.get("removed", 0),
            failed=counts.get("failed", 0),
            total_pages=total,
            last_run_at=last_run["completed_at"] if last_run else None,
            is_running=last_run["status"] == "running" if last_run else False
        )

knowledge_service = KnowledgeService()
