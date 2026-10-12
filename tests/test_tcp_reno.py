import pytest
from simulation.tcp_reno import TCPRenoSimulator


def test_tcp_reno_initial_state():
    sim = TCPRenoSimulator(initial_cwnd=2.0, initial_ssthresh=16.0)
    state = sim.get_state()
    assert state["cwnd"] == 2.0
    assert state["ssthresh"] == 16.0
    assert state["state"] == TCPRenoSimulator.STATE_SLOW_START
    assert state["round"] == 0
    assert state["total_loss_events"] == 0


def test_tcp_reno_slow_start_growth():
    sim = TCPRenoSimulator(initial_cwnd=2.0, initial_ssthresh=16.0)
    # Round 1: cwnd doubles from 2.0 to 4.0
    sim.step()
    assert sim.cwnd == 4.0
    assert sim.state == TCPRenoSimulator.STATE_SLOW_START

    # Round 2: cwnd doubles from 4.0 to 8.0
    sim.step()
    assert sim.cwnd == 8.0
    assert sim.state == TCPRenoSimulator.STATE_SLOW_START

    # Round 3: cwnd doubles from 8.0 to 16.0 (reaches ssthresh)
    sim.step()
    assert sim.cwnd == 16.0
    assert sim.state == TCPRenoSimulator.STATE_CONGESTION_AVOIDANCE


def test_tcp_reno_congestion_avoidance_linear_growth():
    sim = TCPRenoSimulator(initial_cwnd=16.0, initial_ssthresh=16.0)
    sim.state = TCPRenoSimulator.STATE_CONGESTION_AVOIDANCE
    
    # Additive Increase: +1 MSS per RTT
    sim.step()
    assert sim.cwnd == 17.0
    sim.step()
    assert sim.cwnd == 18.0
    assert sim.state == TCPRenoSimulator.STATE_CONGESTION_AVOIDANCE


def test_tcp_reno_triple_dup_ack_fast_retransmit_fast_recovery():
    sim = TCPRenoSimulator(initial_cwnd=20.0, initial_ssthresh=16.0)
    sim.state = TCPRenoSimulator.STATE_CONGESTION_AVOIDANCE
    
    # Trigger 3 Duplicate ACKs
    sim.trigger_triple_dup_ack()
    
    # Multiplicative decrease: ssthresh = max(2, cwnd // 2) = 10.0
    assert sim.ssthresh == 10.0
    # Fast Recovery window inflation: cwnd = ssthresh + 3 = 13.0
    assert sim.cwnd == 13.0
    assert sim.state == TCPRenoSimulator.STATE_FAST_RECOVERY
    assert sim.total_fast_retransmits == 1
    assert sim.total_loss_events == 1

    # On next round (fresh ACK received in Fast Recovery):
    sim.step()
    assert sim.cwnd == 10.0  # Deflates to ssthresh
    assert sim.state == TCPRenoSimulator.STATE_CONGESTION_AVOIDANCE


def test_tcp_reno_timeout_handling():
    sim = TCPRenoSimulator(initial_cwnd=18.0, initial_ssthresh=16.0)
    sim.state = TCPRenoSimulator.STATE_CONGESTION_AVOIDANCE
    
    # Trigger Retransmission Timeout (RTO)
    sim.trigger_timeout()
    
    # ssthresh = max(2, 18//2) = 9.0
    assert sim.ssthresh == 9.0
    # cwnd collapses to 1 MSS
    assert sim.cwnd == 1.0
    # Resets to Slow Start
    assert sim.state == TCPRenoSimulator.STATE_SLOW_START
    assert sim.total_timeouts == 1
    assert sim.total_loss_events == 1


def test_tcp_reno_reset():
    sim = TCPRenoSimulator(initial_cwnd=2.0, initial_ssthresh=16.0)
    sim.step()
    sim.step()
    sim.trigger_triple_dup_ack()
    
    sim.reset()
    assert sim.cwnd == 2.0
    assert sim.ssthresh == 16.0
    assert sim.state == TCPRenoSimulator.STATE_SLOW_START
    assert sim.round == 0
    assert sim.total_loss_events == 0
