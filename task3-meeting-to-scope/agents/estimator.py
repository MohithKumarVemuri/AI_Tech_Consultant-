from typing import List, Dict, Any, Tuple
from app.schemas import Requirement, EstimationTask
from app.config import settings

class EstimationAgent:
    """
    Agent 4: Estimation Agent
    Breaks down requirements into engineering tasks with 3-point estimation
    (Low, Likely, High hours), assumptions, and dependencies.
    Python sums totals deterministically.
    """
    def estimate_requirements(self, requirements: List[Requirement]) -> Tuple[List[EstimationTask], float, float, float]:
        tasks: List[EstimationTask] = []

        for req in requirements:
            d_lower = req.description.lower()
            
            # Estimate based on feasibility and complexity
            if "search sidebar" in d_lower or "filters" in d_lower:
                tasks.append(EstimationTask(
                    task_id=f"TSK-{len(tasks)+1:02d}",
                    requirement_id=req.id,
                    title="Configure Custom Sidebar Search Module & Field Mapping",
                    low_hours=4.0,
                    likely_hours=6.5,
                    high_hours=10.0,
                    assumptions=["Standard Brilliant Directories post types"],
                    dependencies=[]
                ))
            elif "fax" in d_lower:
                tasks.append(EstimationTask(
                    task_id=f"TSK-{len(tasks)+1:02d}",
                    requirement_id=req.id,
                    title="Legacy Fax Number Field Implementation",
                    low_hours=1.5,
                    likely_hours=2.5,
                    high_hours=4.0,
                    assumptions=["Simple text field without OCR"],
                    dependencies=[]
                ))
            elif "taxonomy" in d_lower or "category" in d_lower:
                tasks.append(EstimationTask(
                    task_id=f"TSK-{len(tasks)+1:02d}",
                    requirement_id=req.id,
                    title="Setup 3-Level Category Hierarchy & Import Structure",
                    low_hours=3.0,
                    likely_hours=5.0,
                    high_hours=8.0,
                    assumptions=["Category taxonomy provided in spreadsheet"],
                    dependencies=[]
                ))
            elif "mobile" in d_lower or "smartphone" in d_lower or "responsive" in d_lower:
                tasks.append(EstimationTask(
                    task_id=f"TSK-{len(tasks)+1:02d}",
                    requirement_id=req.id,
                    title="Mobile Viewport CSS Optimization & Touch Tap Targets",
                    low_hours=5.0,
                    likely_hours=8.0,
                    high_hours=12.0,
                    assumptions=["Cross-browser mobile Safari and Chrome compatibility"],
                    dependencies=[]
                ))
            elif "geolocation" in d_lower or "radius search" in d_lower:
                tasks.append(EstimationTask(
                    task_id=f"TSK-{len(tasks)+1:02d}",
                    requirement_id=req.id,
                    title="Google Maps API Integration & 15-Mile Radius Search Setup",
                    low_hours=4.0,
                    likely_hours=7.0,
                    high_hours=11.0,
                    assumptions=["Valid Google Cloud account provided by client"],
                    dependencies=[]
                ))
            elif "stripe" in d_lower or "paypal" in d_lower or "billing" in d_lower:
                tasks.append(EstimationTask(
                    task_id=f"TSK-{len(tasks)+1:02d}",
                    requirement_id=req.id,
                    title="Payment Gateway Integration & Recurring Subscription Automation",
                    low_hours=4.0,
                    likely_hours=6.0,
                    high_hours=9.0,
                    assumptions=["Stripe account active with live webhooks"],
                    dependencies=[]
                ))
            else:
                tasks.append(EstimationTask(
                    task_id=f"TSK-{len(tasks)+1:02d}",
                    requirement_id=req.id,
                    title=f"Implementation: {req.description[:40]}...",
                    low_hours=3.0,
                    likely_hours=5.0,
                    high_hours=8.0,
                    assumptions=["Standard engineering workflow"],
                    dependencies=[]
                ))

        total_low = sum(t.low_hours for t in tasks)
        total_likely = sum(t.likely_hours for t in tasks)
        total_high = sum(t.high_hours for t in tasks)

        return tasks, total_low, total_likely, total_high

estimator_agent = EstimationAgent()
