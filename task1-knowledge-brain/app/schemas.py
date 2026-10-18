from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

class SourceItem(BaseModel):
    title: str
    url: str
    score: float
    image_refs: List[str] = Field(default_factory=list)
    heading: Optional[str] = None

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    require_images: bool = False

class QueryResponse(BaseModel):
    request_id: str
    status: Literal["answered", "insufficient_evidence", "error"]
    answer: Optional[str] = None
    sources: List[SourceItem] = Field(default_factory=list)
    needs_human: bool = False
    escalation_id: Optional[str] = None
    model: str = "claude-haiku-5-5"
    prompt_version: str = "answer@v1"

class IngestionRunRequest(BaseModel):
    mode: Literal["incremental", "full", "sample"] = "incremental"
    max_pages: Optional[int] = 15

class IngestionRunResponse(BaseModel):
    job_id: str
    status: str
    mode: str
    message: str

class IngestionStatusResponse(BaseModel):
    added: int
    updated: int
    removed: int
    failed: int
    total_pages: int
    last_run_at: Optional[str] = None
    is_running: bool = False

class EscalationCreate(BaseModel):
    question: str
    context: Optional[str] = None
    suggested_tags: List[str] = Field(default_factory=list)

class EscalationResolveRequest(BaseModel):
    expert_answer: str
    reviewer: str
    expires_at: Optional[str] = None

class EscalationResponse(BaseModel):
    id: str
    question: str
    context: Optional[str] = None
    status: str
    created_at: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    answer: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str
    primary_model: str
    database: str
    vector_store: str
    indexed_articles: int
    indexed_chunks: int
