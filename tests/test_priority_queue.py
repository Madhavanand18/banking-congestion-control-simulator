import pytest
import time
from simulation.request_queue import RequestQueue, RequestItem


def test_priority_ordering_high_before_medium_before_low():
    queue = RequestQueue(max_capacity=10)
    
    # Enqueue low, medium, high in arbitrary arrival order
    item_low = RequestItem(request_type="STATEMENT", priority=3, request_id="LOW-1")
    item_med = RequestItem(request_type="INQUIRY", priority=2, request_id="MED-1")
    item_high = RequestItem(request_type="TRANSFER", priority=1, request_id="HIGH-1")

    queue.enqueue(item_low)
    queue.enqueue(item_med)
    queue.enqueue(item_high)

    # Dequeue must return HIGH first, then MEDIUM, then LOW
    out1 = queue.dequeue()
    assert out1 is not None
    assert out1.request_id == "HIGH-1"
    assert out1.priority == 1
    assert out1.status == "PROCESSING"

    out2 = queue.dequeue()
    assert out2 is not None
    assert out2.request_id == "MED-1"
    assert out2.priority == 2

    out3 = queue.dequeue()
    assert out3 is not None
    assert out3.request_id == "LOW-1"
    assert out3.priority == 3

    assert queue.dequeue() is None


def test_fifo_tie_breaking_within_same_priority():
    queue = RequestQueue(max_capacity=10)
    
    # Enqueue 3 High Priority requests at different times
    h1 = RequestItem(request_type="TRANSFER", priority=1, request_id="H-1")
    h2 = RequestItem(request_type="AUTH", priority=1, request_id="H-2")
    h3 = RequestItem(request_type="PAYMENT", priority=1, request_id="H-3")

    queue.enqueue(h1)
    queue.enqueue(h2)
    queue.enqueue(h3)

    # Must dequeue in strict FIFO arrival order
    assert queue.dequeue().request_id == "H-1"
    assert queue.dequeue().request_id == "H-2"
    assert queue.dequeue().request_id == "H-3"


def test_queue_capacity_limit_buffer_overflow():
    queue = RequestQueue(max_capacity=3)
    
    res1, _ = queue.enqueue(RequestItem("A", priority=2, request_id="1"))
    res2, _ = queue.enqueue(RequestItem("B", priority=2, request_id="2"))
    res3, _ = queue.enqueue(RequestItem("C", priority=2, request_id="3"))
    
    assert res1 is True
    assert res2 is True
    assert res3 is True
    assert queue.is_full() is True
    assert queue.size() == 3

    # 4th item must be rejected (Buffer Overflow)
    overflow_item = RequestItem("D", priority=2, request_id="4")
    res4, reason = queue.enqueue(overflow_item)
    assert res4 is False
    assert overflow_item.status == "DROPPED"
    assert queue.total_dropped == 1


def test_completion_metrics_recording():
    queue = RequestQueue(max_capacity=10)
    
    h_item = RequestItem("TRANSFER", priority=1, request_id="H-100")
    m_item = RequestItem("INQUIRY", priority=2, request_id="M-100")
    l_item = RequestItem("REPORT", priority=3, request_id="L-100")

    queue.enqueue(h_item)
    queue.enqueue(m_item)
    queue.enqueue(l_item)

    # Process and record completion
    item1 = queue.dequeue()
    queue.record_completion(item1, service_time_ms=50.0)

    item2 = queue.dequeue()
    queue.record_completion(item2, service_time_ms=45.0)

    item3 = queue.dequeue()
    queue.record_completion(item3, service_time_ms=60.0)

    summary = queue.get_summary()
    assert summary["completed_high"] == 1
    assert summary["completed_medium"] == 1
    assert summary["completed_low"] == 1
    assert summary["total_completed"] == 3
    assert summary["total_size"] == 0
