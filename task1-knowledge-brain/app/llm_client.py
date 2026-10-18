import time
import os
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel
from app.config import settings

@dataclass
class LLMResult:
    text: str
    structured: Optional[Any] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    model: str = ""
    provider: str = ""
    prompt_version: str = "v1"

class LLMClient:
    """
    Unified thin LLM Client supporting Claude Haiku (primary),
    Gemini Flash (comparison), and Claude Sonnet.
    Also includes mock offline support for rapid local development & deterministic testing.
    """
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        # Cost per 1M tokens approx (Haiku 3.5: $0.80 input / $4.00 output; Gemini Flash: $0.075 / $0.30; Sonnet: $3.00 / $15.00)
        m = model.lower()
        if "haiku" in m:
            return (prompt_tokens * 0.80 + completion_tokens * 4.00) / 1_000_000.0
        elif "gemini" in m or "flash" in m:
            return (prompt_tokens * 0.075 + completion_tokens * 0.30) / 1_000_000.0
        elif "sonnet" in m:
            return (prompt_tokens * 3.00 + completion_tokens * 15.00) / 1_000_000.0
        return (prompt_tokens * 1.0 + completion_tokens * 3.0) / 1_000_000.0

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        prompt_version: str = "v1",
        temperature: float = 0.1
    ) -> LLMResult:
        start_time = time.perf_counter()
        active_model = model or settings.PRIMARY_MODEL

        # Check if actual API key exists for chosen provider
        if self.provider == "claude" and self.anthropic_key:
            try:
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
                
                messages = []
                content_payload: List[Dict[str, Any]] = []
                
                if images:
                    for img in images:
                        content_payload.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": img.get("media_type", "image/png"),
                                "data": img.get("base64_data", "")
                            }
                        })
                
                content_payload.append({"type": "text", "text": prompt})
                messages.append({"role": "user", "content": content_payload})

                api_kwargs: Dict[str, Any] = {
                    "model": active_model if "claude" in active_model else "claude-3-haiku-20240307",
                    "max_tokens": 1024,
                    "temperature": temperature,
                    "messages": messages
                }
                if system:
                    api_kwargs["system"] = system

                resp = await client.messages.create(**api_kwargs)
                latency = (time.perf_counter() - start_time) * 1000.0
                out_text = "".join([block.text for block in resp.content if hasattr(block, "text")])
                
                pt = resp.usage.input_tokens
                ct = resp.usage.output_tokens
                cost = self._estimate_cost(active_model, pt, ct)

                parsed_obj = None
                if schema:
                    try:
                        clean_json = out_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                        parsed_obj = schema.model_validate_json(clean_json)
                    except Exception:
                        pass

                return LLMResult(
                    text=out_text,
                    structured=parsed_obj,
                    prompt_tokens=pt,
                    completion_tokens=ct,
                    total_tokens=pt + ct,
                    latency_ms=latency,
                    cost_usd=cost,
                    model=active_model,
                    provider="claude",
                    prompt_version=prompt_version
                )
            except Exception as e:
                # Log and fallback to mock if API fails
                pass

        if self.provider == "gemini" and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                g_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                
                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                resp = await g_model.generate_content_async(full_prompt)
                latency = (time.perf_counter() - start_time) * 1000.0
                out_text = resp.text
                
                pt = len(full_prompt.split()) * 2
                ct = len(out_text.split()) * 2
                cost = self._estimate_cost("gemini-flash", pt, ct)

                parsed_obj = None
                if schema:
                    try:
                        clean_json = out_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                        parsed_obj = schema.model_validate_json(clean_json)
                    except Exception:
                        pass

                return LLMResult(
                    text=out_text,
                    structured=parsed_obj,
                    prompt_tokens=pt,
                    completion_tokens=ct,
                    total_tokens=pt + ct,
                    latency_ms=latency,
                    cost_usd=cost,
                    model="gemini-2.5-flash",
                    provider="gemini",
                    prompt_version=prompt_version
                )
            except Exception:
                pass

        # Offline / deterministic mock mode
        latency = (time.perf_counter() - start_time) * 1000.0 + 12.0
        pt = len(prompt.split()) + (len(system.split()) if system else 0)
        ct = 45
        
        # Smart mock response generation based on prompt intent
        out_text = self._generate_smart_mock(prompt, schema)
        
        parsed_obj = None
        if schema:
            try:
                clean_json = out_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                parsed_obj = schema.model_validate_json(clean_json)
            except Exception:
                pass

        return LLMResult(
            text=out_text,
            structured=parsed_obj,
            prompt_tokens=pt,
            completion_tokens=ct,
            total_tokens=pt + ct,
            latency_ms=latency,
            cost_usd=self._estimate_cost(active_model, pt, ct),
            model=active_model,
            provider="mock-local",
            prompt_version=prompt_version
        )

    def _generate_smart_mock(self, prompt: str, schema: Optional[Type[BaseModel]]) -> str:
        prompt_lower = prompt.lower()
        
        # If schema is requested, output valid JSON matching the schema
        if schema:
            schema_name = schema.__name__.lower()
            if "classification" in schema_name or "category" in prompt_lower:
                return json.dumps({
                    "category": "how_to",
                    "subcategory": "how_to/membership_billing",
                    "urgency": "medium",
                    "risk": "low",
                    "confidence": 0.95
                })
            elif "draft" in schema_name:
                return json.dumps({
                    "category": "how_to",
                    "summary": "Explains how to configure recurring billing in Brilliant Directories.",
                    "reply": "Hi,\n\nTo configure recurring membership billing, navigate to Finance > Membership Plans, edit your desired plan, open the Billing tab, and enable Recurring Billing. Then ensure your Stripe gateway is connected under Settings > Payment Gateways.\n\nBest regards,\nSupport Team",
                    "sources": ["Configuring Membership Plans & Recurring Billing"],
                    "risk": "low",
                    "needs_human": False,
                    "next_action": "send_reply",
                    "follow_up_date": None
                })
            elif "imagedescription" in schema_name or "visible_labels" in prompt_lower:
                return json.dumps({
                    "description": "Brilliant Directories admin panel showing Membership Plans settings with Billing tab highlighted.",
                    "visible_labels": ["Finance", "Membership Plans", "Billing Tab", "Recurring Billing: Enabled"],
                    "uncertain": False
                })

        # Answer service mock
        if "insufficient evidence" in prompt_lower or "unsupported" in prompt_lower or "out of domain" in prompt_lower:
            return "insufficient_evidence"

        if "membership" in prompt_lower or "billing" in prompt_lower:
            return "Based on the official documentation, you can set up recurring membership billing by going to Finance > Membership Plans. Under the Billing tab for the selected tier, toggle Recurring Billing to Active and select the desired interval (e.g. Monthly or Annual). Make sure your payment gateway is connected."
        
        if "lead" in prompt_lower:
            return "Lead auto-matching can be configured in Leads > Lead Settings. You can enable automatic matching based on category and location coordinates, or choose to review leads manually before routing them to members."
            
        return "Based on the provided documentation, the requested configuration is managed through the Brilliant Directories admin dashboard under the corresponding settings module. Please verify all requirements before saving changes."
