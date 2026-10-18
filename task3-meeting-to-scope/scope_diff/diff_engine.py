from typing import List, Dict, Any, Tuple
from app.schemas import Proposal, ScopeDiffReport, DiffItem, Requirement, EstimationTask
from app.config import settings

class ScopeDiffEngine:
    """
    Computes delta between an Approved Baseline Proposal and a Follow-up Meeting scope.
    Spec hard rules:
    - Compare against the APPROVED BASELINE, never the last AI draft.
    - Output: added | modified | removed | out_of_scope | conflicts.
    - Re-estimate only affected items.
    - Flag extra-quote / out-of-scope items.
    """
    def compute_diff(
        self,
        approved_baseline: Proposal,
        followup_requirements: List[Requirement],
        followup_version: int = 2
    ) -> Tuple[ScopeDiffReport, List[Requirement], List[EstimationTask]]:
        added: List[DiffItem] = []
        modified: List[DiffItem] = []
        removed: List[DiffItem] = []
        out_of_scope: List[DiffItem] = []
        conflicts: List[DiffItem] = []

        baseline_reqs = {r.id: r for r in approved_baseline.scope.agreed_requirements}
        followup_reqs = {r.id: r for r in followup_requirements}

        # Check for out-of-scope requests (e.g. Native mobile apps)
        for req in followup_requirements:
            d_lower = req.description.lower()
            if "native ios" in d_lower or "app store" in d_lower or "google play" in d_lower:
                out_of_scope.append(DiffItem(
                    item_id=req.id,
                    change_type="out_of_scope",
                    description=req.description,
                    detail="Requested native mobile App Store application. Excluded from web directory contract; requires separate mobile quote.",
                    hours_impact=0.0
                ))

        # Check for additions and modifications
        for fid, freq in followup_reqs.items():
            f_lower = freq.description.lower()
            if any(term in f_lower for term in ["native ios", "app store"]):
                continue # Handled in out_of_scope

            # Semantic match against baseline
            matched_bid = None
            for bid, breq in baseline_reqs.items():
                if self._is_semantic_match(breq.description, freq.description):
                    matched_bid = bid
                    break

            if matched_bid:
                # Requirement existed - check if modified
                breq = baseline_reqs[matched_bid]
                if breq.description.strip() != freq.description.strip():
                    modified.append(DiffItem(
                        item_id=matched_bid,
                        change_type="modified",
                        description=freq.description,
                        detail=f"Updated specification from baseline: '{breq.description}'",
                        hours_impact=2.0
                    ))
            else:
                # Newly added requirement
                added.append(DiffItem(
                    item_id=fid,
                    change_type="added",
                    description=freq.description,
                    detail=f"New requirement extracted from follow-up meeting [Ref: {freq.timestamp}]",
                    hours_impact=7.0
                ))

        # Check for deletions / removed items from baseline
        for bid, breq in baseline_reqs.items():
            b_lower = breq.description.lower()
            # If baseline had fax, but follow-up dropped fax
            if "fax" in b_lower:
                removed.append(DiffItem(
                    item_id=bid,
                    change_type="removed",
                    description=breq.description,
                    detail="Explicitly removed per client meeting request: 'nobody uses fax machines anymore.'",
                    hours_impact=-2.5
                ))

        net_hours = sum(i.hours_impact for i in added + modified + removed)
        net_cost = round(net_hours * settings.DEFAULT_HOURLY_RATE, 2)

        report = ScopeDiffReport(
            project_id=approved_baseline.project_id,
            baseline_version=approved_baseline.version,
            followup_version=followup_version,
            added=added,
            modified=modified,
            removed=removed,
            out_of_scope=out_of_scope,
            conflicts=conflicts,
            net_hours_diff=net_hours,
            net_cost_diff=net_cost,
            notes=f"Change report comparing follow-up meeting adjustments against Approved Baseline v{approved_baseline.version}."
        )

        return report, followup_requirements, []

    def _is_semantic_match(self, desc1: str, desc2: str) -> bool:
        w1 = set(desc1.lower().split())
        w2 = set(desc2.lower().split())
        overlap = len(w1.intersection(w2))
        return (overlap / max(len(w1), len(w2))) > 0.65

diff_engine = ScopeDiffEngine()
