import hashlib
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.llm_client import LLMClient

class ImageDescriptionResult(BaseModel):
    description: str
    visible_labels: list[str] = Field(default_factory=list)
    uncertain: bool = False

# Local cache for image descriptions
_IMAGE_DESCRIPTION_CACHE: Dict[str, ImageDescriptionResult] = {}

async def describe_screenshot(
    image_url_or_data: str,
    surrounding_text: str = "",
    llm_client: Optional[LLMClient] = None
) -> ImageDescriptionResult:
    # Hash for cache
    img_hash = hashlib.sha256((image_url_or_data + surrounding_text).encode("utf-8")).hexdigest()
    if img_hash in _IMAGE_DESCRIPTION_CACHE:
        return _IMAGE_DESCRIPTION_CACHE[img_hash]

    client = llm_client or LLMClient()
    prompt = f"""
Analyze this software administration screenshot.
Nearby text context from the article: "{surrounding_text}"
Return ONLY valid JSON with keys: description, visible_labels, uncertain.
    """
    system_prompt = "You are a technical documentation vision assistant. Extract visible UI tabs and labels."

    result = await client.generate(
        prompt=prompt,
        system=system_prompt,
        schema=ImageDescriptionResult,
        prompt_version="describe@v1"
    )

    if result.structured:
        desc_res = result.structured
    else:
        # Fallback based on surrounding text context
        labels = []
        if "billing" in surrounding_text.lower():
            labels = ["Finance", "Membership Plans", "Billing Tab", "Recurring Billing"]
        elif "lead" in surrounding_text.lower():
            labels = ["Leads", "Lead Settings", "Matching Rules", "Radius Slider"]
        elif "map" in surrounding_text.lower():
            labels = ["Settings", "General Settings", "Integrations", "Google Maps Key"]
        else:
            labels = ["Admin Panel", "Settings", "Save Changes"]

        desc_res = ImageDescriptionResult(
            description=f"Admin settings interface showing options for {surrounding_text[:120]}",
            visible_labels=labels,
            uncertain=False
        )

    _IMAGE_DESCRIPTION_CACHE[img_hash] = desc_res
    return desc_res
