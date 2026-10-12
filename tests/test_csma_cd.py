import pytest
from simulation.csma_cd import CSMACDSimulator


def test_csma_cd_initial_state():
    sim = CSMACDSimulator(station_count=4)
    state = sim.get_state()
    assert state["channel_state"] == CSMACDSimulator.CHANNEL_IDLE
    assert state["slot_number"] == 0
    assert len(state["stations"]) == 4
    assert state["total_collisions"] == 0
    assert state["successful_transmissions"] == 0


def test_csma_cd_single_station_successful_transmission():
    sim = CSMACDSimulator(station_count=3)
    
    # Inject 1 frame to Station A
    sim.inject_frames("STA-A", count=1)
    
    # Slot 1: Station senses idle channel and begins transmission
    sim.step_slot()
    assert sim.channel_state == CSMACDSimulator.CHANNEL_BUSY
    assert "STA-A" in sim.transmitting_stations
    assert sim.stations["STA-A"].state == "TRANSMITTING"

    # Slot 2: Transmission completes successfully without collision
    sim.step_slot()
    assert sim.channel_state == CSMACDSimulator.CHANNEL_IDLE
    assert sim.successful_transmissions == 1
    assert sim.stations["STA-A"].total_transmitted == 1
    assert sim.stations["STA-A"].frames_queued == 0


def test_csma_cd_collision_detection_and_binary_exponential_backoff():
    sim = CSMACDSimulator(station_count=3)
    
    # Simultaneously inject frames to Station A and Station B
    sim.inject_frames("STA-A", count=1)
    sim.inject_frames("STA-B", count=1)

    # Slot 1: Both sense channel idle and transmit simultaneously -> COLLISION!
    sim.step_slot()
    
    assert sim.channel_state == CSMACDSimulator.CHANNEL_COLLISION
    assert sim.total_collisions == 1
    assert "STA-A" in sim.transmitting_stations
    assert "STA-B" in sim.transmitting_stations
    
    # Both stations enter BACKOFF state with collision count k = 1
    assert sim.stations["STA-A"].state == "BACKOFF"
    assert sim.stations["STA-A"].current_retry_count == 1
    # For k=1, contention window W = 2^1 - 1 = 1 (backoff slots: 0 or 1)
    assert sim.stations["STA-A"].last_contention_window == 1
    assert sim.stations["STA-A"].last_backoff_selected in (0, 1)

    assert sim.stations["STA-B"].state == "BACKOFF"
    assert sim.stations["STA-B"].current_retry_count == 1
    assert sim.stations["STA-B"].last_contention_window == 1


def test_csma_cd_retry_limit_drop():
    sim = CSMACDSimulator(station_count=2, max_retries=3)
    
    # Force station A to exceed retry limit
    sim.inject_frames("STA-A", count=1)
    sim.stations["STA-A"].current_retry_count = 3  # Next collision will be k=4 > max_retries
    
    # Force collision with Station B
    sim.inject_frames("STA-B", count=1)
    sim.stations["STA-A"].state = "SENSING"
    sim.stations["STA-B"].state = "SENSING"
    
    sim.step_slot()
    # STA-A reaches retry limit -> frame dropped
    assert sim.stations["STA-A"].total_failed_retries == 1
    assert sim.total_dropped_frames >= 1


def test_csma_cd_reset():
    sim = CSMACDSimulator(station_count=4)
    sim.inject_frames("STA-A", 2)
    sim.step_slot()
    sim.reset()
    
    assert sim.slot_number == 0
    assert sim.channel_state == CSMACDSimulator.CHANNEL_IDLE
    assert sim.total_collisions == 0
    assert sim.successful_transmissions == 0
    assert sim.stations["STA-A"].frames_queued == 0
