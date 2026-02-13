import redis.asyncio as redis
from fastapi import Request, HTTPException
from src.config import settings

# Create Redis connection
redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

async def rate_limiter(request: Request):
    # FIX: Handle cases where request.client is None (e.g., during tests)
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"rate_limit:{client_ip}"
    
    # Simple fixed window: 10 requests per 60 seconds
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, 60)
        
        if current > 10:
            raise HTTPException(
                status_code=429, 
                detail="Too Many Requests", 
                headers={"X-RateLimit-Limit": "10", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "60"}
            )
    except redis.ConnectionError:
        # If Redis is down, we fail open (allow request) or log error
        pass