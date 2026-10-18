# Decisium — AI Technical Consultant Suite (Capstone)

An enterprise multi-agent consulting platform built for software businesses and SaaS ecosystems (specifically optimized for **Brilliant Directories**). The platform connects three critical business workflows into a unified, safety-guarded architecture:

| Task | Module | Tech Stack | Purpose |
|---|---|---|---|
| **Task 1** | **Knowledge Brain** | Python 3.11+, FastAPI, ChromaDB, SQLite FTS5, Streamlit | Grounded RAG search engine, crawler, image-aware retrieval, daily freshness sync & expert escalation queue. |
| **Task 2** | **Inbox Agent** | TypeScript, Next.js 14, Tailwind CSS, Zod | Customer email triaging, grounded draft generation, safety validator, human review workspace & earned autonomy. |
| **Task 3** | **Meeting → Scope** | Python 3.11+, Streamlit, Pydantic | 5-agent pipeline converting meeting transcripts into formal SOWs, 3-point estimates, follow-up diff reports & approval gates. |

---

## 🏗️ Architecture & Hard Rules

- **Strict HTTP Isolation**: Task 2 (TypeScript) and Task 3 (Python) interact with Task 1 **strictly over HTTP** (`/v1/query`). Zero code imports across task boundaries.
- **Human Approval Mandatory**: No client email or project scope proposal can ever be dispatched without explicit human review and approval.
- **Deterministic Offline Capability**: Runs seamlessly offline with built-in mock simulation, or connects to live Claude Haiku / Gemini Flash via API keys.

---

## ⚡ Quickstart

### Option A: One Command (Docker Compose)
If you have Docker installed:
```bash
docker compose up --build
```
This boots all 4 services simultaneously:
- **T1 REST API:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **T1 Knowledge Chat UI:** [http://localhost:8501](http://localhost:8501)
- **T2 Inbox Agent:** [http://localhost:3000](http://localhost:3000)
- **T3 Meeting Scope UI:** [http://localhost:8502](http://localhost:8502)

---

### Option B: One-Click Native Run on Windows
Double-click `run_all.bat` or run the PowerShell script:
```powershell
.\run_all.ps1
```

---

### Option C: Manual Step-by-Step Local Setup

#### Prerequisites
- **Python 3.11+** (`python --version`)
- **Node.js 18+ or 20+** (`node --version`)
- **npm** (`npm --version`)

#### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Add your `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`. If left blank, the suite runs in deterministic high-speed simulation mode.

---

#### 2. Start Task 1: Knowledge Brain (FastAPI Backend + Streamlit UI)

In Terminal 1 (FastAPI Backend):
```bash
cd task1-knowledge-brain
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```
*API is live at [http://localhost:8000/docs](http://localhost:8000/docs). On first boot, it automatically seeds 15 baseline Brilliant Directories support articles into SQLite and ChromaDB.*

In Terminal 2 (Knowledge Brain Streamlit UI):
```bash
cd task1-knowledge-brain
streamlit run ui/streamlit_app.py --server.port 8501
```
*UI is live at [http://localhost:8501](http://localhost:8501).*

---

#### 3. Start Task 2: Inbox Agent (Next.js Dashboard)

In Terminal 3:
```bash
cd task2-inbox-agent
npm install
npm run dev
```
*Inbox Agent dashboard is live at [http://localhost:3000](http://localhost:3000).*

---

#### 4. Start Task 3: Meeting-to-Scope (Streamlit UI)

In Terminal 4:
```bash
cd task3-meeting-to-scope
pip install -r requirements.txt
streamlit run ui/streamlit_app.py --server.port 8502
```
*Meeting-to-Scope studio is live at [http://localhost:8502](http://localhost:8502).*

---

## 🧪 Running Automated Tests

Run the full test suite across all 3 tasks:

### Via Makefile:
```bash
make test
```

### Or Manually per Task:
```bash
# Task 1 Tests (Crawler, Parser, Chunker, API, Escalations)
cd task1-knowledge-brain && pytest tests/ -v

# Task 2 Tests (Classifier, Validator, Autonomy, Diff)
cd task2-inbox-agent && npm test

# Task 3 Tests (Analyst, Scope Diff, Approval Gate)
cd task3-meeting-to-scope && pytest tests/ -v
```

---

## 📊 Running Evaluation Benchmarks

Run the evaluation runners producing `t1_evals.csv`, `t2_evals.csv`, and `t3_evals.csv`:

```bash
# Task 1 Evals (21 test cases)
cd task1-knowledge-brain && python evals/eval_runner.py

# Task 2 Evals (25 test cases)
cd task2-inbox-agent && npm run evals

# Task 3 Evals (20 test cases)
cd task3-meeting-to-scope && python evals/eval_runner.py
```

---

## 🔍 Step-by-Step Feature Verification

### 1. Task 1 Verification
1. Open [http://localhost:8501](http://localhost:8501).
2. Ask: `"How do I configure recurring membership billing?"`
   - Notice the grounded answer citing **Finance > Membership Plans > Billing tab** with screenshot references and confidence scores.
3. Ask an unsupported question: `"Can Brilliant Directories run quantum computer algorithms?"`
   - Notice the status **Insufficient Evidence** and automatic creation of an **Escalation Task**.
4. Click the **Expert Escalation Queue** tab, type an answer, and resolve it.
   - The expert answer is immediately indexed and searchable!

### 2. Task 2 Verification
1. Open [http://localhost:3000](http://localhost:3000).
2. Click through the 50 categorized emails in the left pane.
3. Select email `em_004` (Angry user demanding $99 refund):
   - Notice the red **Safety Policy Guardrails Triggered** banner. The validator strictly blocked unilateral financial promises and enforced human review.
4. Edit the response, provide an edit reason, and click **Edit & Send**.
   - Notice the similarity diff calculated and the feedback logged.
5. Click **Autonomy Monitor** tab to observe the consecutive unchanged counter.

### 3. Task 3 Verification
1. Open [http://localhost:8502](http://localhost:8502).
2. Select **Transcript A** and click **Run 5-Agent Analysis Pipeline**.
   - Requirements, feasibility statuses, and 3-point estimates are calculated.
3. Under the **Human Approval** tab, click **Approve Proposal (Set Baseline)**.
4. Select **Transcript C** (the follow-up meeting) and run analysis.
5. Click the **Follow-up Diff Report** tab:
   - Notice **Geolocation Radius Search** detected as **Added**.
   - Notice **Legacy Fax Filter** detected as **Removed**.
   - Notice **Native iOS/Android App Store** detected and flagged as **Out-of-Scope**!
6. Click **Simulate Dispatch to Client** on an unapproved draft:
   - Notice the system blocks unapproved transmissions with a security exception.

---

## 📁 Repository Layout

```
ai-tech-consultant/
├── spec.md                     # Source of truth specification
├── README.md                   # You are here
├── DESIGN.md                   # In-depth architectural design & diagrams
├── EVALS.md                    # Model benchmarks (Claude Haiku vs Gemini Flash vs Sonnet)
├── AI_LOG.md                   # 5 prompt templates & real rejected answer audit
├── docker-compose.yml          # Container orchestration
├── Makefile                    # Build, test, and evals commands
├── run_all.bat                 # Windows one-click runner
├── run_all.ps1                 # PowerShell one-click runner
├── shared-docs/
│   └── kb-api.md               # OpenAPI specification & client guide
├── task1-knowledge-brain/      # Python FastAPI + Streamlit RAG engine
├── task2-inbox-agent/          # TypeScript Next.js Triaging & Autonomy agent
└── task3-meeting-to-scope/     # Python Streamlit SOW, Estimation & Diff suite
```
