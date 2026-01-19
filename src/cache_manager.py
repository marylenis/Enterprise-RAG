import redis
import json
import hashlib
import redis
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os


# Global embedding model constant
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
        )
        self.default_ttl = int(os.getenv("CACHE_TTL", 3600))  # 1 hour default

    def _generate_query_hash(self, query: str, engine_type: str = "hybrid") -> str:
        """Generate consistent hash for query caching"""
        content = f"{query}:{engine_type}:{EMBEDDING_MODEL}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_cached_response(
        self, query: str, engine_type: str = "hybrid"
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if available"""
        try:
            query_hash = self._generate_query_hash(query, engine_type)
            cached_data = self.redis_client.get(f"query:{query_hash}")

            if cached_data:
                data = json.loads(cached_data)
                # Update access statistics
                self.redis_client.incr(f"stats:{query_hash}:accesses")
                return data

        except Exception as e:
            print(f"Cache retrieval error: {e}")

        return None

    def cache_response(
        self,
        query: str,
        response: Dict[str, Any],
        engine_type: str = "hybrid",
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache query response with metadata"""
        try:
            query_hash = self._generate_query_hash(query, engine_type)
            ttl = ttl or self.default_ttl

            # Add metadata
            cache_data = {
                **response,
                "cached_at": datetime.utcnow().isoformat(),
                "query_hash": query_hash,
                "engine_type": engine_type,
            }

            # Store response
            self.redis_client.setex(f"query:{query_hash}", ttl, json.dumps(cache_data))

            # Initialize statistics
            self.redis_client.setex(f"stats:{query_hash}:accesses", ttl, "1")

            return True

        except Exception as e:
            print(f"Cache storage error: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            # Get total cached queries
            total_cached = len(self.redis_client.keys("query:*"))

            # Get total accesses
            access_keys = self.redis_client.keys("stats:*:accesses")
            total_accesses = sum(
                int(self.redis_client.get(key) or 0) for key in access_keys
            )

            # Calculate hit rate
            hit_rate = (
                (total_accesses / max(total_cached, 1)) * 100 if total_cached > 0 else 0
            )

            return {
                "total_cached_queries": total_cached,
                "total_accesses": total_accesses,
                "hit_rate_percent": round(hit_rate, 2),
                "redis_connected": self.redis_client.ping(),
            }

        except Exception as e:
            return {"error": str(e), "redis_connected": False}

    def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries, optionally by pattern"""
        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
            else:
                keys = self.redis_client.keys("query:*") + self.redis_client.keys(
                    "stats:*"
                )

            if keys:
                return self.redis_client.delete(*keys)
            return 0

        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return 0

    def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        try:
            # Redis automatically handles expired keys
            # This is a manual cleanup for any orphaned stats
            query_keys = set(self.redis_client.keys("query:*"))
            stat_keys = set(self.redis_client.keys("stats:*"))

            orphaned_stats = []
            for stat_key in stat_keys:
                query_hash = stat_key.split(":")[1]
                if f"query:{query_hash}" not in query_keys:
                    orphaned_stats.append(stat_key)

            if orphaned_stats:
                return self.redis_client.delete(*orphaned_stats)
            return 0

        except Exception as e:
            print(f"Cache cleanup error: {e}")
            return 0
