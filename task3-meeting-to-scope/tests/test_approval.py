import pytest
from app.schemas import Proposal, ScopeDocument
from scope_diff.approval import approval_manager

def test_unapproved_proposal_cannot_be_sent():
    scope = ScopeDocument(
        project_id="P1",
        project_name="Test",
        objective="Obj",
        agreed_requirements=[],
        deliverables=[],
        exclusions=[],
        assumptions=[],
        acceptance_criteria=[],
        client_duties=[],
        open_questions=[]
    )
    draft_prop = Proposal(
        proposal_id="PROP-1",
        project_id="P1",
        project_name="Test",
        client_name="Client",
        executive_summary="Summary",
        scope=scope,
        tasks=[],
        total_low_hours=10,
        total_likely_hours=15,
        total_high_hours=20,
        hourly_rate=125,
        currency="USD",
        total_likely_cost=1875,
        timeline="2 weeks",
        payment_terms="50/50",
        approval_status="draft"
    )

    # Attempt to send directly from draft must raise ValueError
    with pytest.raises(ValueError, match="BLOCKED BY SECURITY POLICY"):
        approval_manager.advance_status(draft_prop, "sent", "Reviewer")

    # Approving first works
    approved_prop = approval_manager.advance_status(draft_prop, "approved", "Lead Architect")
    assert approved_prop.approval_status == "approved"
    assert approved_prop.reviewer == "Lead Architect"

    # Now sending succeeds
    sent_prop = approval_manager.advance_status(approved_prop, "sent", "Lead Architect")
    assert sent_prop.approval_status == "sent"
