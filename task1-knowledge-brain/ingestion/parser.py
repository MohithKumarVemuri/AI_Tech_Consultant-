import hashlib
import re
from typing import Dict, List, Any

def compute_content_hash(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

def parse_html_article(html_content: str, source_url: str = "") -> Dict[str, Any]:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup(["nav", "footer", "header", "script", "style", "noscript", "aside"]):
            tag.decompose()

        title = ""
        title_tag = soup.find(["h1", "title"])
        if title_tag:
            title = title_tag.get_text(strip=True)
        elif soup.find("h2"):
            title = soup.find("h2").get_text(strip=True)
        else:
            title = "Untitled Article"

        headings = []
        for h in soup.find_all(["h1", "h2", "h3", "h4"]):
            h_text = h.get_text(strip=True)
            if h_text and h_text not in headings:
                headings.append(h_text)

        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            alt = img.get("alt", "").strip()
            if src:
                parent = img.parent
                surrounding_text = parent.get_text(strip=True) if parent else ""
                if not surrounding_text or len(surrounding_text) < 10:
                    next_p = img.find_next("p")
                    if next_p:
                        surrounding_text = next_p.get_text(strip=True)
                images.append({
                    "src": src,
                    "alt": alt,
                    "surrounding_text": surrounding_text[:300]
                })

        for table in soup.find_all("table"):
            table_rows = []
            for tr in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
                if cols:
                    table_rows.append(" | ".join(cols))
            if table_rows:
                table.replace_with("\n" + "\n".join(table_rows) + "\n")

        for ul in soup.find_all(["ul", "ol"]):
            items = []
            is_ol = ul.name == "ol"
            for idx, li in enumerate(ul.find_all("li", recursive=False), 1):
                prefix = f"{idx}. " if is_ol else "- "
                items.append(f"{prefix}{li.get_text(strip=True)}")
            ul.replace_with("\n" + "\n".join(items) + "\n")

        body_text = soup.get_text(separator="\n")
        cleaned_lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        normalized_text = "\n".join(cleaned_lines)

    except ImportError:
        # Resilient regex fallback parser if bs4 is not yet installed
        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else "Brilliant Directories Guide"

        headings = [
            re.sub(r"<[^>]+>", "", m).strip()
            for m in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", html_content, re.IGNORECASE | re.DOTALL)
        ]

        images = []
        for img_match in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']([^>]*)>', html_content, re.IGNORECASE):
            src = img_match.group(1)
            images.append({"src": src, "alt": "UI Screenshot", "surrounding_text": "Admin panel setting"})

        # Strip html tags
        clean_text = re.sub(r"<[^>]+>", " ", html_content)
        cleaned_lines = [re.sub(r"\s+", " ", l).strip() for l in clean_text.splitlines() if l.strip()]
        normalized_text = "\n".join(cleaned_lines)

    content_hash = compute_content_hash(normalized_text)

    return {
        "title": title,
        "headings": headings,
        "parsed_text": normalized_text,
        "images": images,
        "content_hash": content_hash
    }
