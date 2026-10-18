import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from app.config import settings

async def fetch_sitemap(sitemap_url: Optional[str] = None) -> List[Dict[str, str]]:
    url = sitemap_url or settings.SITEMAP_URL
    headers = {"User-Agent": settings.USER_AGENT}
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return parse_sitemap_xml(resp.text)
    except Exception as e:
        print(f"[sitemap] Live fetch failed: {e}. Using fallback dataset.")

    # Fallback/sample sitemap entries matching our sample knowledge articles
    from ingestion.sample_articles import SAMPLE_ARTICLES
    return [{"url": a["url"], "lastmod": a["lastmod"]} for a in SAMPLE_ARTICLES]

def parse_sitemap_xml(xml_content: str) -> List[Dict[str, str]]:
    entries = []
    seen_urls = set()
    try:
        root = ET.fromstring(xml_content)
        # Handle default namespace if present
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}")[0] + "}"
        
        for url_tag in root.findall(f"{namespace}url"):
            loc = url_tag.find(f"{namespace}loc")
            lastmod = url_tag.find(f"{namespace}lastmod")
            
            if loc is not None and loc.text:
                u = loc.text.strip()
                if u not in seen_urls and u.startswith("http"):
                    seen_urls.add(u)
                    mod_text = lastmod.text.strip() if lastmod is not None and lastmod.text else ""
                    entries.append({"url": u, "lastmod": mod_text})
    except Exception as e:
        print(f"[sitemap] XML parse error: {e}")
    return entries
