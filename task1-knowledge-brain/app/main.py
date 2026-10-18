from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import init_db, get_db_connection
from app.auth import verify_api_key
from app.schemas import (
    QueryRequest, QueryResponse, IngestionRunRequest, IngestionRunResponse,
    IngestionStatusResponse, EscalationCreate, EscalationResolveRequest,
    EscalationResponse, HealthResponse
)
from app.services import knowledge_service
from ingestion.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    init_db()
    # Check if articles exist; if not, seed initial knowledge base automatically
    conn = get_db_connection()
    count = conn.execute("SELECT count(*) as c FROM articles").fetchone()["c"]
    conn.close()
    if count == 0:
        print("[startup] Initializing Knowledge Base with 15 baseline articles...")
        await knowledge_service.run_ingestion(mode="sample", max_pages=15)
    
    # Start APScheduler
    try:
        start_scheduler()
    except Exception as e:
        print(f"[startup] Scheduler start note: {e}")

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Knowledge Brain REST API for Brilliant Directories technical consulting.",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    conn = get_db_connection()
    art_count = conn.execute("SELECT count(*) as c FROM articles WHERE active = 1").fetchone()["c"]
    conn.close()

    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        llm_provider=settings.LLM_PROVIDER,
        primary_model=settings.PRIMARY_MODEL,
        database="connected",
        vector_store="connected",
        indexed_articles=art_count,
        indexed_chunks=art_count * 4 # approx chunks
    )

@app.post("/v1/query", response_model=QueryResponse)
async def query_knowledge_base(
    req: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Query the knowledge base. Grounded in retrieved documentation.
    Returns status='insufficient_evidence' with an escalation ID if unsupported.
    """
    return await knowledge_service.answer_query(question=req.question, top_k=req.top_k)

@app.post("/v1/ingestion/run", response_model=IngestionRunResponse)
async def trigger_ingestion(
    req: IngestionRunRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Trigger full, incremental, or sample crawl & re-indexing.
    Runs asynchronously in the background.
    """
    background_tasks.add_task(knowledge_service.run_ingestion, mode=req.mode, max_pages=req.max_pages or 15)
    return IngestionRunResponse(
        job_id="job_bg_started",
        status="running",
        mode=req.mode,
        message=f"Ingestion job ({req.mode}) started in background."
    )

@app.get("/v1/ingestion/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(api_key: str = Depends(verify_api_key)):
    return knowledge_service.get_ingestion_status()

@app.post("/v1/escalations", response_model=dict)
async def create_escalation(
    req: EscalationCreate,
    api_key: str = Depends(verify_api_key)
):
    esc_id = knowledge_service._create_escalation(question=req.question, context=req.context)
    return {"id": esc_id, "status": "created"}

@app.get("/v1/escalations")
async def list_escalations(
    status: str = "open",
    api_key: str = Depends(verify_api_key)
):
    return knowledge_service.list_escalations(status=status)

@app.post("/v1/escalations/{esc_id}/resolve")
async def resolve_escalation(
    esc_id: str,
    req: EscalationResolveRequest,
    api_key: str = Depends(verify_api_key)
):
    result = knowledge_service.resolve_escalation(
        esc_id=esc_id,
        expert_answer=req.expert_answer,
        reviewer=req.reviewer,
        expires_at=req.expires_at
    )
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.T1_PORT, reload=True)
