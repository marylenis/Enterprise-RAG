import time
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import threading
from fastapi import Request, HTTPException
from src.cache_manager import CacheManager


class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

        # Rate limiting configuration
        self.rate_limits = {
            "default": {"requests": 100, "window": 3600},  # 100 requests/hour
            "premium": {"requests": 1000, "window": 3600},  # 1000 requests/hour
            "trial": {"requests": 20, "window": 3600},  # 20 requests/hour
        }

    def is_allowed(self, client_id: str, tier: str = "default") -> Dict[str, Any]:
        """Check if request is allowed based on rate limits"""
        with self.lock:
            limits = self.rate_limits.get(tier, self.rate_limits["default"])
            now = time.time()
            window_start = now - limits["window"]

            # Clean old requests
            self.requests[client_id] = [
                req_time
                for req_time in self.requests[client_id]
                if req_time > window_start
            ]

            # Check if under limit
            current_requests = len(self.requests[client_id])

            if current_requests >= limits["requests"]:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": int(min(self.requests[client_id]) + limits["window"]),
                    "limit": limits["requests"],
                }

            # Add current request
            self.requests[client_id].append(now)

            return {
                "allowed": True,
                "remaining": limits["requests"] - current_requests - 1,
                "reset_time": int(now + limits["window"]),
                "limit": limits["requests"],
            }

    def get_usage_stats(self, client_id: str) -> Dict[str, Any]:
        """Get current usage statistics for a client"""
        with self.lock:
            now = time.time()
            requests = self.requests.get(client_id, [])

            if not requests:
                return {"current_usage": 0, "total_requests": 0}

            # Calculate usage in different windows
            hour_ago = now - 3600
            day_ago = now - 86400

            hourly_usage = len([req for req in requests if req > hour_ago])
            daily_usage = len([req for req in requests if req > day_ago])

            return {
                "current_usage": hourly_usage,
                "daily_usage": daily_usage,
                "total_requests": len(requests),
                "first_request": datetime.fromtimestamp(min(requests)).isoformat(),
                "last_request": datetime.fromtimestamp(max(requests)).isoformat(),
            }


class TokenManager:
    def __init__(self):
        self.token_usage = defaultdict(list)
        self.lock = threading.Lock()

        # Token limits (in tokens)
        self.token_limits = {
            "default": {"daily_limit": 50000, "request_limit": 2000},
            "premium": {"daily_limit": 500000, "request_limit": 10000},
            "trial": {"daily_limit": 5000, "request_limit": 500},
        }

    def track_tokens(
        self, client_id: str, tokens_used: int, tier: str = "default"
    ) -> Dict[str, Any]:
        """Track token usage and check limits"""
        with self.lock:
            limits = self.token_limits.get(tier, self.token_limits["default"])
            now = time.time()
            day_ago = now - 86400

            # Clean old entries
            self.token_usage[client_id] = [
                (timestamp, tokens)
                for timestamp, tokens in self.token_usage[client_id]
                if timestamp > day_ago
            ]

            # Calculate current daily usage
            daily_usage = sum(tokens for _, tokens in self.token_usage[client_id])

            # Check daily limit
            if daily_usage + tokens_used > limits["daily_limit"]:
                return {
                    "allowed": False,
                    "reason": "daily_limit_exceeded",
                    "daily_used": daily_usage,
                    "daily_limit": limits["daily_limit"],
                    "tokens_requested": tokens_used,
                }

            # Check request limit
            if tokens_used > limits["request_limit"]:
                return {
                    "allowed": False,
                    "reason": "request_limit_exceeded",
                    "request_limit": limits["request_limit"],
                    "tokens_requested": tokens_used,
                }

            # Track usage
            self.token_usage[client_id].append((now, tokens_used))

            return {
                "allowed": True,
                "daily_used": daily_usage + tokens_used,
                "daily_limit": limits["daily_limit"],
                "daily_remaining": limits["daily_limit"] - daily_usage - tokens_used,
                "tokens_used": tokens_used,
            }

    def get_token_stats(self, client_id: str) -> Dict[str, Any]:
        """Get token usage statistics"""
        with self.lock:
            usage = self.token_usage.get(client_id, [])

            if not usage:
                return {"daily_usage": 0, "total_tokens": 0}

            now = time.time()
            day_ago = now - 86400

            daily_usage = sum(
                tokens for timestamp, tokens in usage if timestamp > day_ago
            )
            total_tokens = sum(tokens for _, tokens in usage)

            return {
                "daily_usage": daily_usage,
                "total_tokens": total_tokens,
                "request_count": len(usage),
                "avg_tokens_per_request": total_tokens / len(usage) if usage else 0,
            }


class CostOptimizer:
    def __init__(self):
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiter()
        self.token_manager = TokenManager()

        # Cost tracking
        self.costs = defaultdict(float)
        self.lock = threading.Lock()

        # Pricing (per 1K tokens)
        self.pricing = {
            "input_tokens": 0.001,  # $0.001 per 1K input tokens
            "output_tokens": 0.003,  # $0.003 per 1K output tokens
            "cache_hit": 0.0001,  # $0.0001 per cache hit
        }

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4

    def calculate_cost(
        self, input_tokens: int, output_tokens: int, cache_hit: bool = False
    ) -> float:
        """Calculate cost for a request"""
        cost = (input_tokens * self.pricing["input_tokens"] / 1000) + (
            output_tokens * self.pricing["output_tokens"] / 1000
        )

        if cache_hit:
            cost += self.pricing["cache_hit"]

        return cost

    def track_request_cost(
        self,
        client_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_hit: bool = False,
    ) -> Dict[str, Any]:
        """Track cost for a specific request"""
        with self.lock:
            cost = self.calculate_cost(input_tokens, output_tokens, cache_hit)
            self.costs[client_id] += cost

            return {
                "request_cost": cost,
                "total_client_cost": self.costs[client_id],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_hit": cache_hit,
            }

    def get_cost_stats(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cost statistics"""
        with self.lock:
            if client_id:
                return {
                    "client_id": client_id,
                    "total_cost": self.costs.get(client_id, 0.0),
                }

            # Global stats
            total_cost = sum(self.costs.values())
            return {
                "total_cost": total_cost,
                "active_clients": len(self.costs),
                "avg_cost_per_client": total_cost / len(self.costs)
                if self.costs
                else 0,
            }


# Middleware for FastAPI
class CostControlMiddleware:
    def __init__(self, app, cost_optimizer: CostOptimizer):
        self.app = app
        self.cost_optimizer = cost_optimizer

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Extract client info (simplified - in production use proper auth)
            client_id = request.client.host
            tier = request.headers.get("X-API-Tier", "default")

            # Check rate limiting
            rate_check = self.cost_optimizer.rate_limiter.is_allowed(client_id, tier)
            if not rate_check["allowed"]:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 429,
                        "headers": [[b"content-type", b"application/json"]],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": json.dumps(
                            {
                                "error": "Rate limit exceeded",
                                "reset_time": rate_check["reset_time"],
                            }
                        ).encode(),
                    }
                )
                return

            # Add rate limit headers
            scope["rate_limit_info"] = rate_check

        await self.app(scope, receive, send)
