from typing import List, Dict, Any
from app.schemas import ScopeDocument, Requirement

class ScopeAgent:
    """
    Agent 3: Scope Agent
    Synthesizes agreed requirements into a formal Scope of Work (SOW):
    Objective, Deliverables, Exclusions, Assumptions, Acceptance Criteria,
    Client Duties, and Open Questions.
    """
    def generate_scope(self, project_id: str, project_name: str, requirements: List[Requirement]) -> ScopeDocument:
        deliverables = [
            f"Deliverable: {req.description}" for req in requirements
        ]
        exclusions = [
            "Native iOS / Android mobile applications distributed via Apple App Store or Google Play Store (Out-of-Scope).",
            "Third-party API subscription costs (Google Cloud Console, Twilio, Stripe transaction fees).",
            "Manual data entry for thousands of unformatted historical clinic records."
        ]
        assumptions = [
            "Brilliant Directories administrator login credentials provided at project kickoff.",
            "Client will provide valid Google Cloud Maps API keys with billing enabled.",
            "Work conducted during standard business hours with weekly milestone reviews."
        ]
        client_duties = [
            "Review and approve staging site changes within 48 business hours.",
            "Provide CSV export of category taxonomy.",
            "Supply Stripe account publishable and secret API keys."
        ]
        open_questions = [
            "Do any providers require multi-clinic sub-accounts under a single corporate billing invoice?",
            "What is the fallback behavior if a patient declines browser location permissions?"
        ]

        return ScopeDocument(
            project_id=project_id,
            project_name=project_name,
            objective=f"Modernize provider discovery, search experience, and mobile responsiveness for {project_name}.",
            agreed_requirements=requirements,
            deliverables=deliverables,
            exclusions=exclusions,
            assumptions=assumptions,
            acceptance_criteria=[
                "All acceptance criteria defined in individual requirement specifications pass testing.",
                "Mobile page speed score > 85 on Google PageSpeed Insights.",
                "Zero PHP or JavaScript console errors on provider search pages."
            ],
            client_duties=client_duties,
            open_questions=open_questions
        )

scope_agent = ScopeAgent()
