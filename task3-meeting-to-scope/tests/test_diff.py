import json
from pathlib import Path
from agents.analyst import analyst_agent
from agents.scope import scope_agent
from agents.estimator import estimator_agent
from agents.proposal import proposal_agent
from scope_diff.diff_engine import diff_engine

def test_scope_diff_detects_additions_removals_and_out_of_scope():
    dir_path = Path(__file__).resolve().parent.parent / "transcripts"
    transcript_A = json.loads((dir_path / "transcript_A.json").read_text(encoding="utf-8"))
    transcript_C = json.loads((dir_path / "transcript_C.json").read_text(encoding="utf-8"))

    # Baseline A
    reqs_A = analyst_agent.analyze_transcript(transcript_A)
    scope_A = scope_agent.generate_scope("PRJ-ALPHA", "Apex", reqs_A)
    tasks_A, l, m, h = estimator_agent.estimate_requirements(reqs_A)
    baseline = proposal_agent.generate_proposal("PRJ-ALPHA", "Apex", "Dr. Vance", scope_A, tasks_A, l, m, h)
    baseline.approval_status = "approved"

    # Followup C
    reqs_C = analyst_agent.analyze_transcript(transcript_C)

    report, _, _ = diff_engine.compute_diff(baseline, reqs_C, followup_version=2)

    # Verifications
    # 1. Added geolocation
    assert any("geolocation" in a.description.lower() or "google maps" in a.description.lower() for a in report.added)
    # 2. Removed fax
    assert any("fax" in r.description.lower() for r in report.removed)
    # 3. Net hours difference computed
    assert report.net_hours_diff != 0.0
    # 4. Out-of-scope native mobile app caught
    # In transcript C, Dr. Vance asked for native apps
