# Knowledge Brain (T1) API Documentation

This specification defines the versioned REST API for Task 1 (Knowledge Brain). Tasks T2 (Inbox Agent) and T3 (Meeting-to-Scope) interact with T1 **strictly via HTTP** using this contract.

Base URL: `http://localhost:8000/v1`  
Authentication: `X-API-Key: <KB_API_KEY>` header required on all requests.

---

## 1. Endpoints Overview

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| `GET` | `/v1/health` | Service health & vector store status | None |
| `POST` | `/v1/query` | Ask questions against crawled knowledge base & expert records | Required |
| `POST` | `/v1/ingestion/run` | Trigger incremental or full crawl & indexing | Required |
| `GET` | `/v1/ingestion/status` | Current ingestion pipeline metrics & status | Required |
| `POST` | `/v1/escalations` | Log unanswered query as human expert task | Required |
| `GET` | `/v1/escalations` | List open/resolved escalation tasks | Required |
| `POST` | `/v1/escalations/{id}/resolve` | Resolve escalation & save into knowledge base | Required |

---

## 2. Endpoint Details

### 2.1 Health Check
`GET /v1/health`

**Response:** `200 OK`
```json
{
  "status": "ok",
  "version": "1.0.0",
  "llm_provider": "claude",
  "primary_model": "claude-haiku-5-5",
  "database": "connected",
  "vector_store": "connected",
  "indexed_articles": 15,
  "indexed_chunks": 78
}
```

---

### 2.2 Query Knowledge Base
`POST /v1/query`

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: <KB_API_KEY>`

**Request Body:**
```json
{
  "question": "How do I configure recurring membership billing?",
  "top_k": 5,
  "require_images": false
}
```

**Response Body (Answered):**
```json
{
  "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "answered",
  "answer": "To configure recurring membership billing in Brilliant Directories: 1. Navigate to Finance > Membership Plans. 2. Edit the target plan and select the Billing tab. 3. Set Recurring Billing to Enabled and choose the monthly or annual payment frequency. 4. Connect your payment gateway under Settings > Payment Gateways.",
  "sources": [
    {
      "title": "Configuring Membership Plans & Recurring Billing",
      "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000012345",
      "score": 0.89,
      "image_refs": [
        "https://support.brilliantdirectories.com/images/billing-tab.png"
      ]
    }
  ],
  "needs_human": false,
  "escalation_id": null,
  "model": "claude-haiku-5-5",
  "prompt_version": "answer@v1"
}
```

**Response Body (Insufficient Evidence):**
```json
{
  "request_id": "c1a2e3f4-5678-90ab-cdef-1234567890ab",
  "status": "insufficient_evidence",
  "answer": null,
  "sources": [],
  "needs_human": true,
  "escalation_id": "esc_4f2b91c8",
  "model": "claude-haiku-5-5",
  "prompt_version": "answer@v1"
}
```

---

### 2.3 Run Ingestion
`POST /v1/ingestion/run`

**Request Body:**
```json
{
  "mode": "incremental", // "incremental" | "full" | "sample"
  "max_pages": 15
}
```

**Response Body:**
```json
{
  "job_id": "job_01h8a9x7",
  "status": "running",
  "mode": "incremental",
  "message": "Ingestion started in background"
}
```

---

### 2.4 Ingestion Status
`GET /v1/ingestion/status`

**Response Body:**
```json
{
  "added": 15,
  "updated": 2,
  "removed": 1,
  "failed": 0,
  "total_pages": 17,
  "last_run_at": "2026-10-17T12:00:00Z",
  "is_running": false
}
```

---

### 2.5 Escalations

#### Create Escalation
`POST /v1/escalations`
```json
{
  "question": "Can Brilliant Directories sync calendar events with Google Calendar two-way?",
  "context": "Customer requested via inbox inquiry #402",
  "suggested_tags": ["integrations", "google_calendar"]
}
```

#### List Escalations
`GET /v1/escalations?status=open`

#### Resolve Escalation
`POST /v1/escalations/{id}/resolve`
```json
{
  "expert_answer": "Two-way Google Calendar synchronization requires the Zapier integration add-on or a custom webhook connected to the Brilliant Directories API events endpoint.",
  "reviewer": "Tech Lead Sarah",
  "expires_at": null
}
```
*When resolved, the answer is saved as a versioned `expert_answers` record, indexed into vector + FTS retrieval with `source_type=expert`, and automatically made available for all future T1, T2, and T3 queries.*

---

## 3. Minimal Independent Client Example (Python)

```python
import httpx

KB_BASE_URL = "http://localhost:8000/v1"
KB_API_KEY = "kb_secret_dev_key_2026"

def ask_kb(question: str):
    headers = {"X-API-Key": KB_API_KEY}
    payload = {"question": question}
    
    with httpx.Client(base_url=KB_BASE_URL, headers=headers, timeout=30.0) as client:
        resp = client.post("/query", json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        if data["status"] == "answered":
            print(f"Answer: {data['answer']}")
            print(f"Sources: {[s['title'] for s in data['sources']]}")
        elif data["status"] == "insufficient_evidence":
            print(f"No answer found. Escalated to human: ID {data['escalation_id']}")
        return data

if __name__ == "__main__":
    ask_kb("How do I setup lead auto-matching?")
```
