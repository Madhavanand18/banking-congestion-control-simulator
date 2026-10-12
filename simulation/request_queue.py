"""
Priority Queue Scheduling Implementation for NexaBank Request Processing.
Layer: Application / Transport Dispatch Queue.
Algorithm: Strict Priority Queue with FIFO Tie-Breaking.
"""

import time
import uuid
import threading
from collections import deque
from typing import Optional, List, Dict, Any


class RequestItem:
    """
    Represents an application-level banking request within the simulation.
    Priorities:
      - 1: HIGH   (Customer Wire Transfers, OTP/Authentication, Real-time Authorizations)
      - 2: MEDIUM (Balance Inquiries, Card Validations, Standard Transactions)
      - 3: LOW    (Statement Generation, Historical Reports, Batch Operations)
    """
    def __init__(self, request_type: str, priority: int = 2, payload: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        self.request_id: str = request_id or f"REQ-{str(uuid.uuid4())[:6].upper()}"
        self.request_type: str = request_type
        self.priority: int = priority          # 1 = High, 2 = Medium, 3 = Low
        self.arrival_time: float = time.time()
        self.timestamp: float = self.arrival_time
        self.payload: Dict[str, Any] = payload or {}
        self.status: str = "WAITING"           # WAITING -> PROCESSING -> COMPLETED / DELAYED / DROPPED
        self.wait_time_ms: float = 0.0
        self.service_time_ms: float = 0.0
        self.completion_time: Optional[float] = None
        self.drop_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        priority_label = "HIGH" if self.priority == 1 else ("MEDIUM" if self.priority == 2 else "LOW")
        return {
            "request_id": self.request_id,
            "request_type": self.request_type,
            "priority": self.priority,
            "priority_label": priority_label,
            "arrival_time": time.strftime("%H:%M:%S", time.localtime(self.arrival_time)),
            "status": self.status,
            "wait_time_ms": round(self.wait_time_ms, 2),
            "service_time_ms": round(self.service_time_ms, 2),
            "total_latency_ms": round(self.wait_time_ms + self.service_time_ms, 2),
            "drop_reason": self.drop_reason,
            "payload": self.payload
        }


class RequestQueue:
    """
    Thread-safe Priority Request Queue with maximum buffer capacity.
    
    Scheduling Policy:
    - Strict Priority: Always schedule HIGH (priority=1) requests before MEDIUM (priority=2),
      and MEDIUM requests before LOW (priority=3).
    - FIFO Tie-Breaking: Within the same priority level, requests are strictly served in
      arrival order (First-In, First-Out).
    - Bounded Buffer: Max capacity (default 40 items). Overflow requests are dropped.
    """
    def __init__(self, max_capacity: int = 40):
        self.max_capacity: int = max_capacity
        self._lock = threading.RLock()
        
        # Priority tiers
        self._high_queue: List[RequestItem] = []
        self._medium_queue: List[RequestItem] = []
        self._low_queue: List[RequestItem] = []
        
        # Processing tracking & history
        self.currently_processing: List[RequestItem] = []
        self.recently_completed: deque = deque(maxlen=25)
        self.recently_dropped: deque = deque(maxlen=25)
        
        # Scheduling Metrics
        self.completed_high: int = 0
        self.completed_medium: int = 0
        self.completed_low: int = 0
        self.total_enqueued: int = 0
        self.total_dropped: int = 0
        self.max_observed_queue: int = 0
        self.total_waiting_time_ms: float = 0.0
        self.completed_count: int = 0

        # Event trace logs
        self.event_logs: deque = deque(maxlen=50)
        self._add_log(f"Priority Queue Initialized: Capacity={self.max_capacity}, Rule=Strict Priority (HIGH > MEDIUM > LOW with FIFO)", "INFO")

    def _add_log(self, message: str, level: str = "INFO"):
        timestamp_str = time.strftime("%H:%M:%S")
        self.event_logs.append({
            "time": timestamp_str,
            "message": message,
            "level": level,
            "algorithm": "PRIORITY QUEUE"
        })

    def enqueue(self, item: RequestItem) -> (bool, str):
        """
        Inserts request into the appropriate priority queue tier.
        """
        with self._lock:
            current_total = len(self._high_queue) + len(self._medium_queue) + len(self._low_queue)
            if current_total >= self.max_capacity:
                item.status = "DROPPED"
                item.drop_reason = "Queue Buffer Overflow (Capacity 40 Exceeded)"
                self.total_dropped += 1
                self.recently_dropped.append(item)
                self._add_log(f"Buffer Overflow: Dropped {item.request_id} ({item.request_type}, Priority {item.priority})", "DANGER")
                return False, "Queue capacity reached (Buffer Overflow)"

            item.status = "WAITING"
            if item.priority == 1:
                self._high_queue.append(item)
                p_label = "HIGH"
            elif item.priority == 2:
                self._medium_queue.append(item)
                p_label = "MEDIUM"
            else:
                self._low_queue.append(item)
                p_label = "LOW"

            self.total_enqueued += 1
            new_total = current_total + 1
            if new_total > self.max_observed_queue:
                self.max_observed_queue = new_total

            if self.total_enqueued % 5 == 1 or new_total >= (self.max_capacity * 0.75):
                self._add_log(f"Enqueued {item.request_id} with {p_label} priority (Queue depth: {new_total}/{self.max_capacity})", "INFO")

            return True, "Enqueued successfully"

    def dequeue(self) -> Optional[RequestItem]:
        """
        Selects next request according to strict priority rule (HIGH -> MEDIUM -> LOW),
        preserving FIFO order within each tier.
        """
        with self._lock:
            item = None
            if self._high_queue:
                item = self._high_queue.pop(0)
            elif self._medium_queue:
                item = self._medium_queue.pop(0)
            elif self._low_queue:
                item = self._low_queue.pop(0)

            if item:
                item.status = "PROCESSING"
                item.wait_time_ms = max(0.0, (time.time() - item.arrival_time) * 1000.0)
                self.currently_processing.append(item)
                # Keep active processing list clean
                if len(self.currently_processing) > 10:
                    self.currently_processing.pop(0)
                return item

            return None

    def record_completion(self, item: RequestItem, service_time_ms: float):
        """
        Updates metrics upon request execution completion.
        """
        with self._lock:
            item.service_time_ms = service_time_ms
            item.completion_time = time.time()
            item.status = "COMPLETED"
            
            # Remove from currently_processing if present
            self.currently_processing = [it for it in self.currently_processing if it.request_id != item.request_id]
            self.recently_completed.append(item)

            self.completed_count += 1
            self.total_waiting_time_ms += item.wait_time_ms

            if item.priority == 1:
                self.completed_high += 1
            elif item.priority == 2:
                self.completed_medium += 1
            else:
                self.completed_low += 1

    def size(self) -> int:
        with self._lock:
            return len(self._high_queue) + len(self._medium_queue) + len(self._low_queue)

    def is_full(self) -> bool:
        with self._lock:
            return (len(self._high_queue) + len(self._medium_queue) + len(self._low_queue)) >= self.max_capacity

    def clear(self):
        with self._lock:
            self._high_queue.clear()
            self._medium_queue.clear()
            self._low_queue.clear()
            self.currently_processing.clear()
            self.recently_completed.clear()
            self.recently_dropped.clear()
            self.completed_high = 0
            self.completed_medium = 0
            self.completed_low = 0
            self.total_enqueued = 0
            self.total_dropped = 0
            self.max_observed_queue = 0
            self.total_waiting_time_ms = 0.0
            self.completed_count = 0
            self.event_logs.clear()
            self._add_log("Priority Queue cleared and metrics reset.", "INFO")

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._high_queue) + len(self._medium_queue) + len(self._low_queue)
            avg_wait = round(self.total_waiting_time_ms / self.completed_count, 1) if self.completed_count > 0 else 0.0
            
            # Active waiting items (up to 15)
            active_waiting = [item.to_dict() for item in (self._high_queue + self._medium_queue + self._low_queue)[:15]]
            recent_done = [item.to_dict() for item in list(self.recently_completed)[-10:]]
            recent_drop = [item.to_dict() for item in list(self.recently_dropped)[-5:]]

            return {
                "algorithm": "Priority Queue Scheduler with FIFO Tie-Breaking",
                "source_module": "simulation/request_queue.py",
                "total_size": total,
                "max_capacity": self.max_capacity,
                "high_priority_count": len(self._high_queue),
                "normal_priority_count": len(self._medium_queue),
                "low_priority_count": len(self._low_queue),
                "completed_high": self.completed_high,
                "completed_medium": self.completed_medium,
                "completed_low": self.completed_low,
                "total_completed": self.completed_count,
                "total_dropped": self.total_dropped,
                "avg_waiting_time_ms": avg_wait,
                "max_observed_queue": self.max_observed_queue,
                "utilization_percent": round((total / self.max_capacity) * 100, 1) if self.max_capacity > 0 else 0,
                "active_items": active_waiting,
                "completed_items": recent_done,
                "dropped_items": recent_drop,
                "event_logs": list(self.event_logs)
            }
