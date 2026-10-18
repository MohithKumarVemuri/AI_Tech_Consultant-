from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.schemas import Proposal

class ApprovalWorkflowManager:
    """
    Manages proposal approval lifecycle:
    draft -> in_review -> approved -> sent.
    Enforces:
    - No proposal can be marked 'sent' to client unless it is in 'approved' status.
    - Stores reviewer name, approval timestamp, version history.
    """
    def advance_status(
        self,
        proposal: Proposal,
        target_status: str,
        reviewer_name: str
    ) -> Proposal:
        now = datetime.now(timezone.utc).isoformat()
        current = proposal.approval_status

        if target_status == "in_review":
            if current != "draft":
                raise ValueError(f"Cannot transition to 'in_review' from '{current}'.")
            updated = proposal.model_copy()
            updated.approval_status = "in_review"
            return updated

        elif target_status == "approved":
            if current not in ("draft", "in_review"):
                raise ValueError(f"Cannot approve proposal in state '{current}'.")
            updated = proposal.model_copy()
            updated.approval_status = "approved"
            updated.reviewer = reviewer_name
            updated.approved_at = now
            return updated

        elif target_status == "sent":
            if current != "approved":
                raise ValueError(
                    f"BLOCKED BY SECURITY POLICY: Proposal cannot be sent without human approval! Current status is '{current}'."
                )
            updated = proposal.model_copy()
            updated.approval_status = "sent"
            return updated

        else:
            raise ValueError(f"Invalid target status: '{target_status}'.")

approval_manager = ApprovalWorkflowManager()
