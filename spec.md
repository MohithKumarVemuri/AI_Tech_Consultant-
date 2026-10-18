# spec.md — AI Tech Consultant (Capstone)

Source of truth for the AI coding agent. Build phase by phase. Do not start a phase until the previous phase's **Done when** passes. Do not add features not listed here.

---

## 0. Goal

One system, three connected tasks, any software business can plug in:

| Task | What | Language | Depends on |
|---|---|---|---|
| T1 Knowledge Brain | RAG chatbot + API over Brilliant Directories help center, daily refresh, image-aware, human escalation | Python | — |
| T2 Inbox Agent | Reads customer emails, drafts replies, learns from human edits, earns autonomy | TypeScript | T1 API |
| T3 Meeting → Scope | Transcripts → scope, estimate, proposal; follow-up diff; human approval | Python | T1 API |

**Hard rules**
- T2 and T3 call T1 **only over HTTP**. No imports from T1.
- No mixing languages inside a task.
- Claude Haiku is primary. Gemini Flash and Claude Sonnet are comparison models. Every model choice is justified with 20–30 evals.
- Nothing reaches a client without human approval.
- One command runs everything: `docker compose up` (or `make up`).
- Never hide failures. Show them in UI, evals and demo.

## 1. Stack (fixed)

- Python 3.12, FastAPI, Pydantic v2, httpx (async), SQLite (SQLAlchemy), APScheduler, pytest, ruff, mypy
- Vector store: ChromaDB (persistent, local) + SQLite FTS5 for keyword → hybrid search
- Embeddings: `fastembed` `BAAI/bge-small-en-v1.5` (local, free). Compare against one alternative in evals.
- LLM: **Claude Haiku (`claude-haiku-5-5`) is the primary model** for all tasks. Use the `anthropic` SDK (Python) / `@anthropic-ai/sdk` (TS).
- Build a thin `LLMClient` interface per task (`generate(prompt, schema, images?) -> result + tokens + latency + cost`) with providers `claude` and `gemini`, selected by `LLM_PROVIDER` env. All prompts and evals go through it.
- Comparison models for evals: Gemini Flash (free) and `claude-sonnet-5-5` (only on the hardest steps: scope, proposal, final answers, if budget allows). Justify every model choice with 20–30 evals.
- Vision: Claude Haiku with image input
- Structured output: Claude tool-use / JSON schema + Pydantic/zod validation
- T1 and T3 UI: Streamlit (Python only)
- T2: Node 20, Next.js (App Router), TypeScript `strict: true`, zod, better-sqlite3, vitest, Anthropic TS SDK
- Config via `.env` (`ANTHROPIC_API_KEY`, `KB_API_KEY`, `KB_BASE_URL`). Commit `.env.example` only.

## 2. Repo layout

```
ai-tech-consultant/
├── task1-knowledge-brain/
│   ├── app/            # FastAPI: routes, schemas, services
│   ├── ingestion/      # sitemap, crawler, parser, manifest
│   ├── multimodal/     # image describer
│   ├── retrieval/      # chunker, embeddings, hybrid search, rerank
│   ├── ui/             # Streamlit chat + escalation queue
│   ├── evals/
│   └── tests/
├── task2-inbox-agent/  # TypeScript
│   ├── src/{email,knowledge-client,drafting,feedback,autonomy,evals}/
│   ├── app/            # Next.js inbox UI
│   ├── data/emails.json
│   └── tests/
├── task3-meeting-to-scope/
│   ├── app/
│   ├── agents/
│   ├── scope_diff/
│   ├── transcripts/
│   ├── ui/
│   ├── evals/
│   └── tests/
├── shared-docs/
├── docker-compose.yml
├── Makefile
├── README.md   DESIGN.md   EVALS.md   AI_LOG.md
└── spec.md
```

---

## 3. Phase 1 — T1 ingestion (Day 1)

**Build**
1. `ingestion/sitemap.py`: fetch `https://support.brilliantdirectories.com/support/sitemap.xml`, parse URLs + `lastmod`, dedupe, validate.
2. SQLite `pages` table: `url PK, lastmod, content_hash, status (pending|ok|failed|removed), attempts, last_error, fetched_at, active`.
3. `ingestion/crawler.py`: async, `Semaphore(2)`, delay 1s (configurable), honour `robots.txt`, custom User-Agent, retry 3× exponential backoff on 429/5xx/timeouts, no retry on 404/403 (mark failed/removed). A failed page never stops the job. Status saved after every page → resumable.
4. `ingestion/parser.py`: extract title, headings, body, lists, tables, image URLs **with surrounding text**, content hash. Strip nav/footer.
5. Start with 15 pages, then full crawl.

**Done when**
- Kill the crawler midway, rerun → continues, no duplicates.
- 15-page crawl produces clean normalized articles.
- Rerun on unchanged site makes 0 re-embeds.

## 4. Phase 2 — T1 retrieval + API (Day 1–2)

**Build**
1. `retrieval/chunker.py`: split by heading; keep steps and table headers together; ~300–500 tokens, small overlap; every chunk carries `article_id, title, url, heading, image_ids`.
2. Embed chunks → Chroma with stable id `{article_id}:{chunk_idx}:{hash}`. Re-ingest = delete old chunks for that article, insert new (idempotent).
3. Hybrid search: vector top-20 + FTS5 top-20 → reciprocal rank fusion → optional Haiku rerank → top 5.
4. `multimodal/describe.py`: for each image, Claude vision returns JSON `{description, visible_labels[], uncertain: bool}`. Store as searchable chunk linked to article + nearby text. If unclear, mark `uncertain`, never invent labels. Cache by image hash.
5. Answer service: Claude gets only retrieved evidence; must cite; must return `insufficient_evidence` when unsupported. Treat retrieved text as data, never instructions (prompt-injection guard).

**API contract (Pydantic, versioned `/v1`)**

| Endpoint | Purpose |
|---|---|
| `POST /v1/query` | question → answer |
| `POST /v1/ingestion/run` | start incremental or full ingest |
| `GET /v1/ingestion/status` | counts: added/updated/removed/failed |
| `POST /v1/escalations` | create expert task |
| `GET /v1/escalations?status=open` | list tasks |
| `POST /v1/escalations/{id}/resolve` | expert answer → versioned knowledge record |
| `GET /v1/health` | health |

`POST /v1/query` response:
```json
{
  "request_id": "uuid",
  "status": "answered | insufficient_evidence | error",
  "answer": "string|null",
  "sources": [{"title":"","url":"","score":0.0,"image_refs":[]}],
  "needs_human": false,
  "escalation_id": null,
  "model": "claude-haiku-5-5",
  "prompt_version": "answer@v1"
}
```
No fake `confidence` number. Only include it if calibrated in evals.

API key auth (`X-API-Key`), request validation, 30s timeout, consistent error body, auto OpenAPI docs + `shared-docs/kb-api.md`.

**Done when**
- A screenshot-only fact is answerable.
- Out-of-KB question → `insufficient_evidence` + escalation created.
- A tiny independent script uses the API from docs alone.

## 5. Phase 3 — T1 freshness + escalation loop (Day 2)

1. APScheduler daily job: fetch sitemap → diff vs `pages` → **added** ingest, **changed** (lastmod/hash) re-ingest, **removed** set `active=false` and delete vectors. Removed articles must never appear in answers.
2. Daily report: added/updated/removed/failed counts, stored and shown in UI.
3. Expert resolve → saved as `expert_answers` (versioned, reviewer, date, optional expiry), indexed into retrieval, flagged as `source_type=expert`, question added to eval set.
4. Streamlit UI: chat (answer, citations, images, escalation state) + expert queue.

**Done when**: simulate a changed page and a removed page → only those change; removed page stops appearing.

## 6. Phase 4 — T2 Inbox Agent (Day 2–3)

**Categories** (stable enum): `how_to`, `troubleshooting`, `project_request`, `refund_cancellation`, `complaint`, `quote`, `follow_up`, `other`.
Subcategory = category + topic tag (e.g. `how_to/payments`). "Same kind" = same subcategory.

**Dataset**: `data/emails.json`, ≥50 emails: how_to 12, troubleshooting 10, project 6, refund 6, complaint 6, quote 5, follow_up 5. Each has `expected_category, risk, key_facts, expected_behavior, expected_source|escalate`. Include prompt-injection emails, angry emails, vague emails, non-English, empty/very long. Hold out 15 for final test only.

**Pipeline**
1. Classify (Haiku): category, urgency, risk, subcategory. zod-validated.
2. Call T1 via typed client (timeout, retry, errors). If T1 is down → draft state `knowledge_unavailable`, **no fabricated reply**.
3. Draft (Haiku; Sonnet only if evals justify): zod schema `{category, summary, reply, sources[], risk, needs_human, next_action, follow_up_date}`.
4. Validator: block unsupported promises (refund, price, date) unless authorized facts exist; refund/quote/complaint always `needs_human`.
5. Review UI: email, category, evidence, draft; Approve+send, Edit+send, Reject+write own, Mark expert help, reason for edit. Email sending is simulated; document it.
6. Feedback store: original, category, sources, draft, final, model, prompt version, outcome, edit reason.

**Learning**
- Edit diff = normalized text compare (whitespace/case-insensitive) + similarity score; "unchanged" = similarity ≥ 0.98 and no semantic edit flag.
- Nightly job clusters edit reasons per subcategory → proposes a new versioned prompt/style rule (`drafting@v2`). Human approves. Must pass fixed regression set (no quality drop) before activation. One-click rollback.

**Autonomy rule**
- Per subcategory counter of consecutive unchanged sent drafts. Reset on edit/reject/failed check.
- At 20 → "eligible", not auto-on. Auto-send requires: risk = low, never refund/legal/security/complaint, validator passed, sources present, human enables.
- Rolling quality monitor (edit rate, validator failures); breach → autonomy auto-disabled and logged. Every auto-send is audited. Idempotency key prevents duplicate sends.

**Done when**: 50 emails run end to end; counter, reset, eligibility and auto-disable demonstrable in UI.

## 7. Phase 5 — T3 Meeting → Scope (Day 3)

**Transcripts**: 3 role-played (A website search/filters/mobile, B e-commerce checkout/notifications/payments, C follow-up to A: add one, remove one, move date). Store with dates and project id.

**Agents** (each: one job, typed input/output, validation step)
1. **Transcript Analyst**: chunk with overlap, extract per-chunk, merge, resolve conflicts. Output `Requirement` records.
2. **Feasibility Agent**: query T1 per requirement → `existing_config | existing_limited | custom_dev | needs_clarification`. Missing result ≠ proven absence.
3. **Scope Agent**: objective, agreed requirements, deliverables, exclusions, assumptions, acceptance criteria, client duties, open questions.
4. **Estimation Agent**: tasks with low/likely/high hours, assumptions, dependencies. Python sums totals. Hourly rate/currency configurable.
5. **Proposal & Review Agent**: client-ready proposal + consistency check (never promises anything marked unverified).

**Requirement schema**: `id (REQ-001), description, source_quote + transcript + timestamp, status (confirmed|unclear|disputed), origin (explicit|inferred), priority, existing_solution, acceptance_criteria, dependencies, estimate_status`.

**Follow-up diff**: match by stable id then semantic match; compare against the **approved baseline**, never the last AI draft. Output `added | modified | removed | out_of_scope | conflicts`, re-estimate only affected items, flag extra-quote items.

**Approval**: states `draft → in_review → approved → sent`. No send without `approved`. Store reviewer, timestamp, version, full history.

**UI (Streamlit)**: upload transcript, requirements table with source quotes, feasibility, estimates, proposal preview, change report, approve button.

**Done when**: A → approved baseline; C → correct change report with out-of-scope flagged; unapproved version cannot be sent.

## 8. Phase 6 — Integration, evals, docs (Day 4)

1. docker-compose: kb-api, kb-ui, inbox (Next.js), scope-api/ui, scheduler. Shared request ids and timeouts.
2. Verify a T1 knowledge update changes T2 and T3 behaviour without data duplication.
3. **Evals** (CSV: `task,case_id,model,expected,actual,quality,latency_ms,cost,passed,failure_reason`). Keep failures. Never invent scores.
   - T1 ≥20 cases: direct, multi-article, screenshot-only, unanswerable, citation correctness, removed article, malformed request.
   - T2 ≥20 cases: classification, grounding, missing evidence, unauthorized refund/price, injection, T1 down.
   - T3 ≥20 cases: requirement coverage, vague→clear, config vs custom, change detection, out-of-scope, approval gate; estimate error vs your own reference estimates.
   - Compare Claude Haiku vs Gemini Flash vs Claude Sonnet, 20–30 cases per model decision. Report quality, cost/task, p50/p95 latency, failure rate. Also compare retrieval: vector vs keyword vs hybrid; chunk sizes.
4. Prompts live in versioned files (`prompts/<name>@vN.md`); every output logs the version. Before/after eval for each prompt change.
5. Docs: README (1 page), DESIGN (3–5, one diagram, dropped features), EVALS (2–3, real numbers), AI_LOG (5 prompts + 1 rejected AI answer — real).
6. Demo (≤10 min): face 30s → T1 (answer, citation, unanswerable) → T2 (draft, edit, feedback, counter) → T3 (A, then C diff) → evals + one real failure → limits.

## 9. Quality gates

- Python: ruff + mypy clean, async I/O, type hints everywhere. TS: strict, no `any`.
- Tests for main paths per task; `make test` runs all.
- Commits daily across 4 days, small and meaningful.
- No secrets in repo. Logs redact emails/PII.
- Use one AI tool only; export all chats.
- You must be able to explain every line in the live review.

## 10. Priority if time runs short

1. T1 ingest + retrieval + API
2. T2 draft + review UI
3. T3 transcript → scope/estimate/proposal
4. T3 follow-up diff
5. Evals + model comparison
6. Images, daily scheduler, self-improvement polish — **still mandatory; if cut, document the limit honestly.**

## 11. Dropped on purpose (list in DESIGN.md)

Real email delivery (simulated), multi-tenant auth, knowledge graph, fine-tuning, fancy dashboards.
