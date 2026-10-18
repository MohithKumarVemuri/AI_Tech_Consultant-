from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

class Requirement(BaseModel):
    id: str # REQ-001
    description: str
    source_quote: str
    transcript_id: str
    timestamp: str
    status: Literal["confirmed", "unclear", "disputed"] = "confirmed"
    origin: Literal["explicit", "inferred"] = "explicit"
    priority: Literal["high", "medium", "low"] = "high"
    existing_solution: Optional[str] = None # Filled by Feasibility Agent
    feasibility_status: Literal["existing_config", "existing_limited", "custom_dev", "needs_clarification"] = "existing_config"
    acceptance_criteria: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    estimate_status: Literal["pending", "estimated"] = "pending"

class FeasibilityReport(BaseModel):
    requirement_id: str
    status: Literal["existing_config", "existing_limited", "custom_dev", "needs_clarification"]
    confidence: float
    kb_sources: List[str] = Field(default_factory=list)
    rationale: str

class EstimationTask(BaseModel):
    task_id: str
    requirement_id: str
    title: str
    low_hours: float
    likely_hours: float
    high_hours: float
    assumptions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

class ScopeDocument(BaseModel):
    project_id: str
    project_name: str
    objective: str
    agreed_requirements: List[Requirement]
    deliverables: List[str]
    exclusions: List[str]
    assumptions: List[str]
    acceptance_criteria: List[str]
    client_duties: List[str]
    open_questions: List[str]

class Proposal(BaseModel):
    proposal_id: str
    project_id: str
    project_name: str
    client_name: str
    executive_summary: str
    scope: ScopeDocument
    tasks: List[EstimationTask]
    total_low_hours: float
    total_likely_hours: float
    total_high_hours: float
    hourly_rate: float
    currency: str
    total_likely_cost: float
    timeline: str
    payment_terms: str
    approval_status: Literal["draft", "in_review", "approved", "sent"] = "draft"
    reviewer: Optional[str] = None
    approved_at: Optional[str] = None
    version: int = 1

class DiffItem(BaseModel):
    item_id: str
    change_type: Literal["added", "modified", "removed", "out_of_scope", "conflicts"]
    description: str
    detail: str
    hours_impact: float = 0.0

class ScopeDiffReport(BaseModel):
    project_id: str
    baseline_version: int
    followup_version: int
    added: List[DiffItem] = Field(default_factory=list)
    modified: List[DiffItem] = Field(default_factory=list)
    removed: List[DiffItem] = Field(default_factory=list)
    out_of_scope: List[DiffItem] = Field(default_factory=list)
    conflicts: List[DiffItem] = Field(default_factory=list)
    net_hours_diff: float = 0.0
    net_cost_diff: float = 0.0
    notes: str = ""
