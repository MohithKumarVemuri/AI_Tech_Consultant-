import asyncio
import time
import httpx
import uuid
from typing import Dict, Any, List, Optional
from urllib.robotparser import RobotFileParser
from app.config import settings
from app.db import (
    get_db_connection, upsert_page, upsert_article, mark_page_removed
)
from ingestion.parser import parse_html_article
from ingestion.sitemap import fetch_sitemap
from ingestion.sample_articles import SAMPLE_ARTICLES

class AsyncCrawler:
    def __init__(
        self,
        max_concurrent: Optional[int] = None,
        delay_seconds: Optional[float] = None
    ):
        self.semaphore = asyncio.Semaphore(max_concurrent or settings.CRAWL_MAX_CONCURRENT)
        self.delay = delay_seconds or settings.CRAWL_DELAY_SECONDS
        self.user_agent = settings.USER_AGENT
        self.robot_parser = RobotFileParser()
        self._robots_loaded = False

    async def _init_robots(self):
        if self._robots_loaded:
            return
        robots_url = "https://support.brilliantdirectories.com/robots.txt"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(robots_url, headers={"User-Agent": self.user_agent})
                if resp.status_code == 200:
                    self.robot_parser.parse(resp.text.splitlines())
        except Exception:
            pass
        self._robots_loaded = True

    def is_allowed(self, url: str) -> bool:
        if not self._robots_loaded:
            return True
        try:
            return self.robot_parser.can_fetch(self.user_agent, url)
        except Exception:
            return True

    async def fetch_page_with_retry(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        """
        Retries 3x with exponential backoff on 429/5xx/timeout.
        No retry on 404/403 (immediately mark failed/removed).
        """
        # If url is in our local sample dataset, return immediately
        for sample in SAMPLE_ARTICLES:
            if sample["url"] == url:
                return {"status": "ok", "html": sample["html"], "error": None}

        backoff = 1.0
        for attempt in range(1, 4):
            try:
                resp = await client.get(url, headers={"User-Agent": self.user_agent})
                if resp.status_code == 200:
                    return {"status": "ok", "html": resp.text, "error": None}
                elif resp.status_code in (404, 410):
                    return {"status": "removed", "html": None, "error": f"HTTP {resp.status_code}"}
                elif resp.status_code == 403:
                    return {"status": "failed", "html": None, "error": "HTTP 403 Forbidden"}
                elif resp.status_code in (429, 500, 502, 503, 504):
                    if attempt == 3:
                        return {"status": "failed", "html": None, "error": f"HTTP {resp.status_code} after 3 retries"}
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                else:
                    return {"status": "failed", "html": None, "error": f"HTTP {resp.status_code}"}
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt == 3:
                    return {"status": "failed", "html": None, "error": f"Network error: {str(e)}"}
                await asyncio.sleep(backoff)
                backoff *= 2.0
            except Exception as e:
                return {"status": "failed", "html": None, "error": str(e)}

        return {"status": "failed", "html": None, "error": "Exhausted retries"}

    async def crawl_url(self, client: httpx.AsyncClient, url_entry: Dict[str, str], stats: Dict[str, int]):
        url = url_entry["url"]
        lastmod = url_entry.get("lastmod")

        async with self.semaphore:
            # Check existing page record in DB
            conn = get_db_connection()
            row = conn.execute("SELECT content_hash, status, active FROM pages WHERE url = ?", (url,)).fetchone()
            existing_hash = row["content_hash"] if row else None
            existing_status = row["status"] if row else None
            conn.close()

            if not self.is_allowed(url):
                upsert_page(url, lastmod, existing_hash, status="failed", last_error="Disallowed by robots.txt")
                stats["failed"] += 1
                return

            await asyncio.sleep(self.delay)
            res = await self.fetch_page_with_retry(client, url)

            if res["status"] == "ok" and res["html"]:
                parsed = parse_html_article(res["html"], url)
                new_hash = parsed["content_hash"]

                # Check if unchanged
                if existing_hash == new_hash and existing_status == "ok":
                    # Unchanged site makes 0 re-embeds!
                    upsert_page(url, lastmod, new_hash, status="ok", attempts=1, active=True)
                    return

                # Added or Updated
                article_id = "art_" + hashlib_id(url)
                upsert_article(
                    article_id=article_id,
                    url=url,
                    title=parsed["title"],
                    raw_html=res["html"],
                    parsed_text=parsed["parsed_text"],
                    headings=parsed["headings"],
                    images=parsed["images"],
                    lastmod=lastmod,
                    content_hash=new_hash,
                    source_type="crawled"
                )
                upsert_page(url, lastmod, new_hash, status="ok", attempts=1, active=True)

                if existing_hash is None:
                    stats["added"] += 1
                else:
                    stats["updated"] += 1

            elif res["status"] == "removed":
                mark_page_removed(url)
                stats["removed"] += 1
            else:
                upsert_page(url, lastmod, existing_hash, status="failed", attempts=1, last_error=res["error"])
                stats["failed"] += 1

    async def run(self, mode: str = "incremental", max_pages: int = 15) -> Dict[str, Any]:
        await self._init_robots()
        sitemap_entries = await fetch_sitemap()
        if max_pages and len(sitemap_entries) > max_pages:
            sitemap_entries = sitemap_entries[:max_pages]

        stats = {"added": 0, "updated": 0, "removed": 0, "failed": 0, "total": len(sitemap_entries)}

        # Detect removed pages in incremental mode
        if mode == "incremental":
            current_sitemap_urls = set(e["url"] for e in sitemap_entries)
            conn = get_db_connection()
            db_pages = conn.execute("SELECT url FROM pages WHERE active = 1").fetchall()
            conn.close()
            for r in db_pages:
                if r["url"] not in current_sitemap_urls and not r["url"].startswith("expert:"):
                    mark_page_removed(r["url"])
                    stats["removed"] += 1

        async with httpx.AsyncClient(timeout=20.0) as client:
            tasks = [self.crawl_url(client, entry, stats) for entry in sitemap_entries]
            await asyncio.gather(*tasks, return_exceptions=True)

        return stats

def hashlib_id(text: str) -> str:
    import hashlib
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
