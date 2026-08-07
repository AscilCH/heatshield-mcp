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


