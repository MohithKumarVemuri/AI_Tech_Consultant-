from typing import List
from app.schemas import Requirement
from app.kb_client import kb_client

class FeasibilityAgent:
    """
    Agent 2: Feasibility Agent
    Queries Task 1 Knowledge Brain over HTTP for each requirement to classify:
    - existing_config: Standard native settings in Brilliant Directories
    - existing_limited: Native feature exists but requires partial custom tweak
    - custom_dev: True custom backend / frontend extension needed
    - needs_clarification: Missing details prevent classification
    """
    async def evaluate_requirements(self, requirements: List[Requirement]) -> List[Requirement]:
        evaluated = []
        for req in requirements:
            kb_res = await kb_client.check_feasibility(req.description)
            
            # Map into requirement
            updated = req.model_copy()
            updated.feasibility_status = kb_res.get("status", "existing_config")
            sources_str = ", ".join(kb_res.get("sources", [])) if kb_res.get("sources") else "Custom logic"
            updated.existing_solution = f"{kb_res.get('rationale')} [Ref: {sources_str}]"
            evaluated.append(updated)

        return evaluated

feasibility_agent = FeasibilityAgent()
