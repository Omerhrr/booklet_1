"""
Rate Limiting Middleware
Implements rate limiting for authentication and sensitive endpoints
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe in-memory rate limiter using sliding window algorithm.
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Rate limit configurations
        self.limits = {
            # Authentication endpoints - strict limits
            '/api/v1/auth/login': (5, 60),      # 5 requests per 60 seconds
            '/api/v1/auth/signup': (3, 300),    # 3 requests per 5 minutes
            '/api/v1/auth/logout': (10, 60),    # 10 requests per 60 seconds
            
            # Password change - very strict
            '/api/v1/settings/users/change-password': (3, 300),  # 3 per 5 minutes
            
            # Sensitive write operations
            '/api/v1/sales/invoices': (30, 60),           # 30 per minute
            '/api/v1/purchases/bills': (30, 60),          # 30 per minute
            '/api/v1/banking/transfers': (10, 60),        # 10 per minute
            '/api/v1/banking/accounts': (20, 60),         # 20 per minute
            '/api/v1/accounting/journal-vouchers': (20, 60),  # 20 per minute
            
            # Default limit for all other endpoints
            'default': (100, 60),  # 100 requests per minute
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (when behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """
        Create a unique key for rate limiting.
        Combines IP address with user ID if authenticated.
        """
        ip = self._get_client_ip(request)
        
        # Try to get user info from Authorization header
        auth_header = request.headers.get("Authorization", "")
        user_id = "anonymous"
        
        if auth_header.startswith("Bearer "):
            # Use partial token hash for user identification (first 8 chars)
            token = auth_header[7:]
            if len(token) > 8:
                user_id = token[:8]
        
        return f"{ip}:{user_id}"
    
    def _cleanup_old_requests(self, key: str, window_seconds: int):
        """Remove requests outside the time window"""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        self._requests[key] = [
            timestamp for timestamp in self._requests[key]
            if timestamp > cutoff
        ]
    
    def is_allowed(self, request: Request) -> Tuple[bool, Optional[Dict]]:
        """
        Check if the request is allowed under rate limiting rules.
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        path = request.url.path
        method = request.method
        
        # Only rate limit write operations and auth endpoints
        if method in ['GET', 'HEAD', 'OPTIONS'] and not path.startswith('/api/v1/auth'):
            return True, None
        
        # Get the appropriate limit
        limit, window = self.limits.get(path, self.limits['default'])
        
        # Special handling for dynamic paths
        for pattern, (lim, win) in self.limits.items():
            if not pattern.endswith('/'):
                # Check if path starts with pattern (for parameterized routes)
                if path.startswith(pattern):
                    limit, window = lim, win
                    break
        
        key = f"{path}:{self._get_rate_limit_key(request)}"
        
        with self._lock:
            self._cleanup_old_requests(key, window)
            
            current_count = len(self._requests[key])
            
            if current_count >= limit:
                # Calculate retry-after
                oldest_request = min(self._requests[key]) if self._requests[key] else datetime.utcnow()
                retry_after = int((oldest_request + timedelta(seconds=window) - datetime.utcnow()).total_seconds())
                
                logger.warning(f"Rate limit exceeded for {key}: {current_count}/{limit} requests")
                
                return False, {
                    'limit': limit,
                    'remaining': 0,
                    'reset': retry_after,
                    'retry_after': max(1, retry_after)
                }
            
            # Record the request
            self._requests[key].append(datetime.utcnow())
            
            return True, {
                'limit': limit,
                'remaining': limit - current_count - 1,
                'reset': window
            }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for non-API routes
        if not request.url.path.startswith('/api/'):
            return await call_next(request)
        
        # Skip for health checks
        if request.url.path in ['/api/health', '/api/v1/health']:
            return await call_next(request)
        
        is_allowed, rate_info = self.rate_limiter.is_allowed(request)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    'detail': 'Too many requests. Please try again later.',
                    'retry_after': rate_info.get('retry_after', 60)
                },
                headers={
                    'Retry-After': str(rate_info.get('retry_after', 60)),
                    'X-RateLimit-Limit': str(rate_info.get('limit', 0)),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(rate_info.get('reset', 60))
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        if rate_info:
            response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
            response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
        
        return response


# Singleton instance
rate_limiter = RateLimiter()
