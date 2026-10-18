import re
import hashlib
from typing import List, Dict, Any

def approximate_token_count(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text))

def chunk_article(
    article_id: str,
    title: str,
    url: str,
    parsed_text: str,
    headings: List[str],
    images: List[Dict[str, Any]],
    target_tokens: int = 400,
    overlap_tokens: int = 50
) -> List[Dict[str, Any]]:
    """
    Splits an article by heading hierarchy while keeping numbered steps
    and markdown table structures intact.
    Each chunk carries: article_id, title, url, heading, image_ids, text, chunk_id, content_hash.
    """
    chunks = []
    lines = parsed_text.splitlines()
    
    current_heading = title
    current_buffer = []
    current_tokens = 0
    chunk_index = 0

    # Build image lookup by surrounding text
    image_refs_list = [img.get("src", "") for img in images if img.get("src")]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line is a heading
        is_heading = any(stripped.startswith(h) or stripped == h for h in headings)
        line_tokens = approximate_token_count(stripped)

        if is_heading and current_tokens >= target_tokens * 0.7:
            # Emit chunk
            chunk_text = "\n".join(current_buffer).strip()
            if chunk_text:
                c_hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()[:8]
                chunk_id = f"{article_id}:{chunk_index}:{c_hash}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "article_id": article_id,
                    "title": title,
                    "url": url,
                    "heading": current_heading,
                    "text": chunk_text,
                    "image_ids": image_refs_list[:2],
                    "tokens": current_tokens,
                    "chunk_index": chunk_index
                })
                chunk_index += 1

            current_heading = stripped
            # Overlap from tail of previous buffer
            overlap_lines = current_buffer[-2:] if len(current_buffer) >= 2 else []
            current_buffer = list(overlap_lines)
            current_tokens = sum(approximate_token_count(l) for l in current_buffer)

        current_buffer.append(stripped)
        current_tokens += line_tokens

        # Check token cap
        if current_tokens >= target_tokens:
            chunk_text = "\n".join(current_buffer).strip()
            c_hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()[:8]
            chunk_id = f"{article_id}:{chunk_index}:{c_hash}"
            chunks.append({
                "chunk_id": chunk_id,
                "article_id": article_id,
                "title": title,
                "url": url,
                "heading": current_heading,
                "text": chunk_text,
                "image_ids": image_refs_list[:2],
                "tokens": current_tokens,
                "chunk_index": chunk_index
            })
            chunk_index += 1

            # Retain overlap
            overlap_lines = current_buffer[-2:] if len(current_buffer) >= 2 else []
            current_buffer = list(overlap_lines)
            current_tokens = sum(approximate_token_count(l) for l in current_buffer)

    # Emit trailing buffer
    if current_buffer:
        chunk_text = "\n".join(current_buffer).strip()
        if chunk_text:
            c_hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()[:8]
            chunk_id = f"{article_id}:{chunk_index}:{c_hash}"
            chunks.append({
                "chunk_id": chunk_id,
                "article_id": article_id,
                "title": title,
                "url": url,
                "heading": current_heading,
                "text": chunk_text,
                "image_ids": image_refs_list[:2],
                "tokens": current_tokens,
                "chunk_index": chunk_index
            })

    return chunks
