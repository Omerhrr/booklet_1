"""
Rate Limiting Middleware
Implements rate limiting for authentication and sensitive endpoints
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple, Optional
import sqlite3
import os
import threading
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe SQLite-backed rate limiter using sliding window algorithm.
    """

    def __init__(self):
        self._lock = threading.Lock()
        db_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ),
            "rate_limits.db",
        )
        self._db_path = db_path
        self._init_db()

        self.limits = {
            "/api/v1/auth/login": (5, 60),
            "/api/v1/auth/signup": (3, 300),
            "/api/v1/auth/logout": (10, 60),
            "/api/v1/saas/auth/login": (5, 60),
            "/api/v1/saas/auth/verify-token": (10, 60),
            "/api/v1/saas/register": (3, 300),
            "/api/v1/settings/users/change-password": (3, 300),
            "/api/v1/sales/invoices": (30, 60),
            "/api/v1/purchases/bills": (30, 60),
            "/api/v1/banking/transfers": (10, 60),
            "/api/v1/banking/accounts": (20, 60),
            "/api/v1/accounting/journal-vouchers": (20, 60),
            "default": (100, 60),
        }

    def _get_conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rate_limit_entries (
                key TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ix_rl_key ON rate_limit_entries(key)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_rl_timestamp ON rate_limit_entries(timestamp)"
        )
        conn.commit()
        conn.close()

    def _cleanup_old_requests(self, key: str, window_seconds: int):
        import time

        cutoff = time.time() - window_seconds
        conn = self._get_conn()
        conn.execute(
            "DELETE FROM rate_limit_entries WHERE key = ? AND timestamp < ?",
            (key, cutoff),
        )
        conn.commit()
        conn.close()

    def _cleanup_all_expired(self):
        import time

        cutoff = time.time() - 3600
        conn = self._get_conn()
        conn.execute("DELETE FROM rate_limit_entries WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()

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

    def is_allowed(self, request: Request) -> Tuple[bool, Optional[Dict]]:
        import time

        path = request.url.path
        method = request.method

        if method in ["GET", "HEAD", "OPTIONS"] and not path.startswith("/api/v1/auth"):
            return True, None

        limit, window = self.limits.get(path, self.limits["default"])

        for pattern, (lim, win) in self.limits.items():
            if not pattern.endswith("/"):
                if path.startswith(pattern):
                    limit, window = lim, win
                    break

        key = f"{path}:{self._get_rate_limit_key(request)}"
        now = time.time()

        with self._lock:
            self._cleanup_old_requests(key, window)

            conn = self._get_conn()
            current_count = conn.execute(
                "SELECT COUNT(*) FROM rate_limit_entries WHERE key = ?", (key,)
            ).fetchone()[0]

            if current_count >= limit:
                oldest = conn.execute(
                    "SELECT MIN(timestamp) FROM rate_limit_entries WHERE key = ?",
                    (key,),
                ).fetchone()[0]
                conn.close()
                retry_after = max(1, int(oldest + window - now))
                logger.warning(
                    f"Rate limit exceeded for {key}: {current_count}/{limit}"
                )

                if hash(key) % 100 == 0:
                    self._cleanup_all_expired()

                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": retry_after,
                    "retry_after": retry_after,
                }

            conn.execute(
                "INSERT INTO rate_limit_entries (key, timestamp) VALUES (?, ?)",
                (key, now),
            )
            conn.commit()
            conn.close()

            if hash(key) % 100 == 0:
                self._cleanup_all_expired()

            return True, {
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset": window,
            }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for non-API routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Skip for health checks
        if request.url.path in ["/api/health", "/api/v1/health"]:
            return await call_next(request)

        is_allowed, rate_info = self.rate_limiter.is_allowed(request)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": rate_info.get("retry_after", 60),
                },
                headers={
                    "Retry-After": str(rate_info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info.get("reset", 60)),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to response
        if rate_info:
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

        return response


# Singleton instance
rate_limiter = RateLimiter()
