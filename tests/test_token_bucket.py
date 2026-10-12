import pytest
import time
from simulation.token_bucket import TokenBucket


def test_token_bucket_initialization():
    tb = TokenBucket(capacity=30.0, refill_rate=10.0)
    state = tb.get_state()
    assert state["capacity"] == 30.0
    assert state["refill_rate"] == 10.0
    assert state["tokens"] == 30.0
    assert state["total_admitted"] == 0
    assert state["total_rejected"] == 0


def test_token_bucket_consumption_and_admission():
    tb = TokenBucket(capacity=10.0, refill_rate=0.0)  # No refill for deterministic test
    
    # Consume 1 token
    admitted, reason = tb.consume(1.0, current_time=time.time())
    assert admitted is True
    assert tb.tokens == 9.0
    assert tb.total_admitted == 1

    # Consume 9 more tokens
    for _ in range(9):
        admitted, _ = tb.consume(1.0, current_time=time.time())
        assert admitted is True
    
    assert tb.tokens == 0.0
    assert tb.total_admitted == 10

    # 11th request must be rejected
    admitted, reason = tb.consume(1.0, current_time=time.time())
    assert admitted is False
    assert tb.total_rejected == 1
    assert "Insufficient tokens" in reason


def test_token_bucket_refill_over_time():
    start_time = 1000.0
    tb = TokenBucket(capacity=20.0, refill_rate=10.0, initial_tokens=0.0)
    tb.last_refill_time = start_time
    
    # 1 second later -> +10 tokens
    tb.refill(current_time=start_time + 1.0)
    assert tb.tokens == 10.0

    # 2 seconds later -> +20 total tokens (capped at capacity 20)
    tb.refill(current_time=start_time + 3.0)
    assert tb.tokens == 20.0  # Capped at capacity 20.0


def test_token_bucket_dynamic_configure_and_reset():
    tb = TokenBucket(capacity=30.0, refill_rate=10.0)
    tb.consume(10.0)
    assert tb.tokens == 20.0

    tb.configure(capacity=50.0, refill_rate=25.0)
    assert tb.capacity == 50.0
    assert tb.refill_rate == 25.0

    tb.reset()
    assert tb.tokens == 50.0
    assert tb.total_admitted == 0
    assert tb.total_rejected == 0
