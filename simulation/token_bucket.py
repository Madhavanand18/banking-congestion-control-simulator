"""
Token Bucket Algorithm Implementation for NexaBank Traffic Regulation.
Layer: Application / Network Traffic Shaping & Rate Limiting.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from collections import deque


class TokenBucket:
    """
    Classic Token Bucket Algorithm for traffic policing and rate limiting.
    
    Principles:
    - Tokens are added to the bucket at a constant rate: `refill_rate` (tokens/second).
    - The bucket has a maximum capacity: `capacity` (burst limit).
    - Arriving requests require `cost` tokens (default: 1 token) to be admitted.
    - If tokens >= cost: request admitted, tokens deducted.
    - If tokens < cost: request rejected (or deferred / dropped with HTTP 429).
    """

    def __init__(self, capacity: float = 30.0, refill_rate: float = 10.0, initial_tokens: Optional[float] = None):
        self.capacity: float = float(capacity)
        self.refill_rate: float = float(refill_rate)
        self.tokens: float = float(initial_tokens) if initial_tokens is not None else float(capacity)
        self.last_refill_time: float = time.time()
        self._lock = threading.RLock()

        # Cumulative Metrics
        self.total_admitted: int = 0
        self.total_rejected: int = 0
        self.total_tokens_consumed: int = 0
        self.total_tokens_refilled: float = 0.0

        # Event trace log (limited history)
        self.event_logs: deque = deque(maxlen=50)

        # Time-series history for visualization
        self.history: deque = deque(maxlen=45)

        self._add_log(f"Bucket initialized: Capacity={self.capacity} tokens, Refill Rate={self.refill_rate} tokens/s, Tokens={self.tokens:.1f}", "INFO")

    def _add_log(self, message: str, level: str = "INFO"):
        timestamp_str = time.strftime("%H:%M:%S")
        self.event_logs.append({
            "time": timestamp_str,
            "message": message,
            "level": level,
            "algorithm": "TOKEN BUCKET"
        })

    def refill(self, current_time: Optional[float] = None) -> float:
        """
        Refills tokens based on elapsed monotonic / simulated time.
        Returns the number of tokens added in this step.
        """
        now = current_time if current_time is not None else time.time()
        elapsed = now - self.last_refill_time
        if elapsed <= 0:
            return 0.0

        tokens_to_add = elapsed * self.refill_rate
        old_tokens = self.tokens
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        actual_added = self.tokens - old_tokens
        self.last_refill_time = now

        if actual_added > 0.05:
            self.total_tokens_refilled += actual_added

        return actual_added

    def consume(self, tokens_required: float = 1.0, current_time: Optional[float] = None, request_id: str = "") -> (bool, str):
        """
        Attempts to consume tokens for an arriving request.
        Returns: (admitted: bool, reason: str)
        """
        with self._lock:
            # 1. Refill tokens for elapsed time
            added = self.refill(current_time)
            
            # 2. Check token availability
            if self.tokens >= tokens_required:
                self.tokens -= tokens_required
                self.total_admitted += 1
                self.total_tokens_consumed += int(tokens_required)
                req_info = f" [Req: {request_id}]" if request_id else ""
                if self.total_admitted % 5 == 1 or self.tokens < (self.capacity * 0.25):
                    self._add_log(f"Request admitted{req_info}. Tokens remaining: {self.tokens:.1f}/{self.capacity}", "SUCCESS")
                return True, "Token consumed - Request admitted"
            else:
                self.total_rejected += 1
                req_info = f" [Req: {request_id}]" if request_id else ""
                self._add_log(f"Request rejected{req_info}: Insufficient tokens ({self.tokens:.1f} < {tokens_required:.1f})", "DANGER")
                return False, f"Rate limited: Insufficient tokens in bucket ({self.tokens:.1f} available, {tokens_required:.1f} required)"

    def configure(self, capacity: Optional[float] = None, refill_rate: Optional[float] = None):
        """Updates parameters dynamically."""
        with self._lock:
            self.refill()
            if capacity is not None and capacity > 0:
                self.capacity = float(capacity)
                self.tokens = min(self.tokens, self.capacity)
            if refill_rate is not None and refill_rate > 0:
                self.refill_rate = float(refill_rate)
            self._add_log(f"Bucket parameters updated: Capacity={self.capacity}, Refill Rate={self.refill_rate} tok/s", "INFO")

    def reset(self, initial_tokens: Optional[float] = None):
        """Resets bucket state and counters."""
        with self._lock:
            self.tokens = float(initial_tokens) if initial_tokens is not None else self.capacity
            self.last_refill_time = time.time()
            self.total_admitted = 0
            self.total_rejected = 0
            self.total_tokens_consumed = 0
            self.total_tokens_refilled = 0.0
            self.event_logs.clear()
            self.history.clear()
            self._add_log("Token Bucket reset to initial state.", "INFO")

    def record_snapshot(self):
        """Records a time point for charts."""
        with self._lock:
            self.refill()
            self.history.append({
                "time": time.strftime("%H:%M:%S"),
                "tokens": round(self.tokens, 1),
                "capacity": self.capacity,
                "admitted": self.total_admitted,
                "rejected": self.total_rejected
            })

    def get_state(self) -> Dict[str, Any]:
        """Returns full state dictionary for UI."""
        with self._lock:
            self.refill()
            return {
                "algorithm": "Token Bucket Traffic Regulator",
                "source_module": "simulation/token_bucket.py",
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
                "tokens": round(self.tokens, 2),
                "fill_percentage": round((self.tokens / self.capacity) * 100, 1) if self.capacity > 0 else 0,
                "total_admitted": self.total_admitted,
                "total_rejected": self.total_rejected,
                "total_tokens_consumed": self.total_tokens_consumed,
                "event_logs": list(self.event_logs),
                "history": list(self.history)
            }
