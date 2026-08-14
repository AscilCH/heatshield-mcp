import time
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from collections import defaultdict

# 1. API KEY AUTHENTICATION
API_KEY_NAME = "X-API-Key"
VALID_API_KEY = "heatshield-demo-key" # In production, this would be an env var
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != VALID_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing API Key"
        )
# 2. IP RATE LIMITER (In-Memory Token Bucket / Window)
class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.ip_records = defaultdict(list)
        
    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean up old requests (older than 60 seconds)
        self.ip_records[client_ip] = [
            req_time for req_time in self.ip_records[client_ip] 
            if current_time - req_time < 60
        ]
        
        if len(self.ip_records[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute per IP."
            )
            
        self.ip_records[client_ip].append(current_time)
        return True

# 3. PROMPT GUARD CLASSIFIER & INTENT GATEWAY
class PromptGuard:
    """
    Multi-tier Prompt Security Gateway:
    1. Local heuristic and semantic pattern analysis for Prompt Injections & Jailbreaks.
    2. Off-topic domain boundary enforcement for dedicated civic heat-safety systems.
    3. Optional Meta-Llama/Prompt-Guard-86M Hugging Face Inference API integration.
    """
    
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s+prompt\s+(verbatim|leak|reveal|output)",
        r"output\s+(your\s+)?(entire\s+)?system\s+prompt",
        r"developer\s+mode\s+(enabled|on|activate)",
        r"dan\s+mode",
        r"jailbreak",
        r"override\s+(all\s+)?(safety|rules|instructions)",
        r"you\s+are\s+now\s+an?\s+(unrestricted|evil|unfiltered)",
        r"pretend\s+you\s+have\s+no\s+(rules|guidelines|restrictions)",
        r"repeat\s+the\s+words\s+above",
    ]

    OFF_TOPIC_TRIGGER_PATTERNS = [
        r"write\s+(me\s+)?a\s+(python|javascript|c\+\+|java|rust|go)\s+script",
        r"write\s+(me\s+)?a\s+poem",
        r"write\s+(me\s+)?a\s+story\s+about",
        r"tell\s+me\s+a\s+joke\s+about",
        r"how\s+to\s+make\s+(a\s+bomb|meth|drugs|weapons)",
        r"recipe\s+for\s+(lasagna|cake|cookies|pizza|pasta)",
        r"who\s+won\s+the\s+\d{4}\s+(world\s+cup|super\s+bowl|nba)",
    ]

    HEAT_DOMAIN_KEYWORDS = [
        "heat", "temperature", "weather", "forecast", "wbgt", "humidity", "uv",
        "sun", "cooling", "shelter", "walk", "route", "isochrone", "park",
        "sweat", "stroke", "exhaustion", "hydration", "water", "drought", "air quality",
        "aqi", "pm2.5", "ozone", "djerba", "sfax", "tunis", "paris", "tokyo", "cairo",
        "phoenix", "austin", "berlin", "midoun", "houmt souk", "death valley", "degrees",
        "celsius", "fahrenheit", "radiation", "work", "rest", "niosh", "osha", "who", "cdc"
    ]

    @classmethod
    async def evaluate(cls, text: str) -> dict:
        import re
        import os
        import httpx
        
        normalized = text.strip().lower()
        
        # 1. Tier 1: Local Pattern Match for Known Injections & Jailbreaks
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                return {
                    "is_safe": False,
                    "reason": "Direct Prompt Injection / Jailbreak Attempt",
                    "score": 0.98,
                    "source": "PromptGuard Local Classifier"
                }

        # 2. Tier 2: Off-Topic / General Assistant Guardrail
        for pattern in cls.OFF_TOPIC_TRIGGER_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                # Ensure it's not a heat query with embedded keywords
                has_heat_keyword = any(kw in normalized for kw in ["heat", "wbgt", "thermal", "temperature", "hydration", "weather"])
                if not has_heat_keyword:
                    return {
                        "is_safe": False,
                        "reason": "Off-Topic Request (Non-Heat Domain)",
                        "score": 0.92,
                        "source": "PromptGuard Domain Enforcer"
                    }

        # 3. Tier 3: Meta-Llama Prompt-Guard-86M via Hugging Face (if token present)
        hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        if hf_token:
            url = "https://api-inference.huggingface.co/models/meta-llama/Prompt-Guard-86M"
            headers = {"Authorization": f"Bearer {hf_token}"}
            payload = {"inputs": text}
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload, timeout=4.0)
                    if response.status_code == 200:
                        data = response.json()
                        scores = data[0] if isinstance(data, list) and isinstance(data[0], list) else data
                        for item in scores:
                            label = item.get("label", "").upper()
                            score = item.get("score", 0.0)
                            if label in ["LABEL_1", "INJECTION"] and score > 0.70:
                                return {"is_safe": False, "reason": "HuggingFace Prompt-Guard Injection Detection", "score": score, "source": "Meta-Llama/Prompt-Guard-86M"}
                            if label in ["LABEL_2", "JAILBREAK"] and score > 0.70:
                                return {"is_safe": False, "reason": "HuggingFace Prompt-Guard Jailbreak Detection", "score": score, "source": "Meta-Llama/Prompt-Guard-86M"}
            except Exception as e:
                print(f"[PROMPT GUARD] HF Inference API check skipped: {e}")

        return {"is_safe": True, "score": 0.05, "source": "PromptGuard Gateway"}


