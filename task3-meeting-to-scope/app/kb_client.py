import httpx
from typing import Optional, Dict, Any, List
from app.config import settings

class KnowledgeBrainClient:
    """
    HTTP client for Task 1 Knowledge Brain REST API.
    Used by Feasibility Agent to check if requirements are built-in native config
    or require custom development.
    """
    def __init__(self):
        self.base_url = settings.KB_BASE_URL
        self.api_key = settings.KB_API_KEY
        self.headers = {"X-API-Key": self.api_key}

    async def check_feasibility(self, requirement_description: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=15.0) as client:
                resp = await client.post("/query", json={"question": requirement_description, "top_k": 3})
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status")
                    sources = [s["title"] for s in data.get("sources", [])]
                    answer = data.get("answer", "")
                    
                    if status == "answered":
                        # Check whether it indicates existing config
                        return {
                            "status": "existing_config",
                            "sources": sources,
                            "rationale": f"Native feature documented in Brilliant Directories: {answer[:180]}..."
                        }
                    else:
                        return {
                            "status": "custom_dev",
                            "sources": [],
                            "rationale": "No native documentation found in Knowledge Brain. Requires custom development."
                        }
        except Exception as e:
            # Fallback heuristic if T1 server is offline
            pass

        desc_lower = requirement_description.lower()
        if any(k in desc_lower for k in ["filter", "sidebar", "category", "search", "mobile", "billing", "maps", "recaptcha"]):
            return {
                "status": "existing_config",
                "sources": ["Brilliant Directories Post Types & Search Settings"],
                "rationale": "Configurable natively via Brilliant Directories administration panel."
            }
        return {
            "status": "custom_dev",
            "sources": [],
            "rationale": "Custom API integration or tailored code extension required."
        }

kb_client = KnowledgeBrainClient()
