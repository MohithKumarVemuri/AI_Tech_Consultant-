import json
from pathlib import Path
from agents.analyst import analyst_agent

def test_transcript_analyst_extracts_requirements():
    transcripts_path = Path(__file__).resolve().parent.parent / "transcripts" / "transcript_A.json"
    transcript_data = json.loads(transcripts_path.read_text(encoding="utf-8"))
    
    reqs = analyst_agent.analyze_transcript(transcript_data)
    assert len(reqs) >= 3
    
    req_texts = [r.description.lower() for r in reqs]
    assert any("search sidebar" in t for t in req_texts)
    assert any("category" in t or "taxonomy" in t for t in req_texts)
    assert any("mobile" in t for t in req_texts)
    
    # Check quotes and timestamps
    for r in reqs:
        assert r.source_quote != ""
        assert r.timestamp != ""
