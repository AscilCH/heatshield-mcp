import time
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from collections import defaultdict
import re
from transformers import pipeline

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
    return api_key_header

# 2. IP RATE LIMITER (In-Memory Token Bucket / Window)
class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
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

# 3. AI-POWERED PROMPT INJECTION GUARDRAILS
class PromptGuard:
    _classifier = None
    
    @classmethod
    def get_classifier(cls):
        if cls._classifier is None:
            print("Loading ProtectAI Prompt Injection Classifier (DeBERTa-v3)...")
            cls._classifier = pipeline(
                "text-classification", 
                model="protectai/deberta-v3-base-prompt-injection-v2",
                device="cpu"
            )
            print("PromptGuard AI Model Loaded.")
        return cls._classifier

    @classmethod
    def scan(cls, message: str) -> None:
        """
        Scans a user message for malicious prompt injection attempts using a local Hugging Face model.
        Raises an HTTPException if a threat is detected.
        """
        classifier = cls.get_classifier()
        result = classifier(message)
        
        if result and len(result) > 0:
            prediction = result[0]
            # The model outputs 'INJECTION' or 'SAFE'
            if prediction['label'] == 'INJECTION' and prediction['score'] > 0.75:
                print(f"PROMPTGUARD AI ALERT: Blocked semantic injection attempt! Confidence: {prediction['score']:.2f}")
                raise HTTPException(
                    status_code=400,
                    detail="Security Alert: Malicious prompt injection attempt detected and blocked by AI PromptGuard."
                )

# 4. TOPIC GUARD (Semantic Relevance Guardrail)
class TopicGuard:
    _classifier = None
    
    @classmethod
    def get_classifier(cls):
        if cls._classifier is None:
            print("Loading TopicGuard Semantic Classifier (distilbert-base-uncased-mnli)...")
            cls._classifier = pipeline(
                "zero-shot-classification", 
                model="typeform/distilbert-base-uncased-mnli",
                device="cpu"
            )
            print("TopicGuard AI Model Loaded.")
        return cls._classifier

    @classmethod
    def scan(cls, message: str) -> None:
        """
        Scans a user message to ensure it is relevant to the HeatShield domain.
        Raises an HTTPException if the query is strictly off-topic.
        """
        classifier = cls.get_classifier()
        candidate_labels = [
            "urban heat wave and weather safety", 
            "casual greeting or conversational pleasantry", 
            "off-topic programming or general trivia"
        ]
        
        result = classifier(message, candidate_labels=candidate_labels)
        
        if result and len(result['labels']) > 0:
            top_label = result['labels'][0]
            top_score = result['scores'][0]
            
            if top_label == "off-topic programming or general trivia" and top_score > 0.6:
                print(f"TOPICGUARD AI ALERT: Blocked off-topic query! Confidence: {top_score:.2f}")
                raise HTTPException(
                    status_code=400,
                    detail="Off-topic query blocked by TopicGuard. I am only authorized to assist with urban heat, weather, and emergency safety."
                )
