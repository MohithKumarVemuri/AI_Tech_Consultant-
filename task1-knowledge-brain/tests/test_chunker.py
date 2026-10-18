import pytest
from retrieval.chunker import chunk_article

def test_chunk_article_heading_preservation():
    text = """
    # Introduction
    Welcome to Brilliant Directories setup.
    ## Step 1: Membership
    First navigate to finance and select membership plans.
    Keep recurring billing toggled to active.
    ## Step 2: Invoicing
    Review invoices weekly.
    """
    headings = ["Introduction", "Step 1: Membership", "Step 2: Invoicing"]
    chunks = chunk_article(
        article_id="art_123",
        title="Intro Guide",
        url="https://example.com/guide",
        parsed_text=text,
        headings=headings,
        images=[],
        target_tokens=30
    )

    assert len(chunks) >= 2
    for c in chunks:
        assert c["article_id"] == "art_123"
        assert c["chunk_id"].startswith("art_123:")
        assert "url" in c
