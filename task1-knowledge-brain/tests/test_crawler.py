import pytest
from ingestion.parser import parse_html_article, compute_content_hash
from ingestion.crawler import AsyncCrawler
from ingestion.sample_articles import SAMPLE_ARTICLES

def test_parser_extracts_headings_and_tables():
    sample = SAMPLE_ARTICLES[0]
    parsed = parse_html_article(sample["html"], sample["url"])
    
    assert "Configuring Membership Plans" in parsed["title"]
    assert len(parsed["headings"]) >= 2
    assert "Prerequisites" in parsed["headings"]
    assert "Enable Free Trial" in parsed["parsed_text"]
    assert len(parsed["images"]) >= 1
    assert parsed["images"][0]["src"].endswith(".png")

def test_hash_consistency():
    text1 = "This is a test article for Brilliant Directories."
    text2 = "This is   a test article for Brilliant Directories.  "
    assert compute_content_hash(text1) == compute_content_hash(text2)

@pytest.mark.asyncio
async def test_crawler_unchanged_detection():
    crawler = AsyncCrawler()
    # Mock crawl sample
    stats = await crawler.run(mode="sample", max_pages=3)
    assert stats["total"] >= 1
