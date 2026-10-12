"""
TCP Reno Congestion Control Simulation.
Layer: Layer 4 (Transport Layer).
Algorithms: Slow Start, Congestion Avoidance, Fast Retransmit, Fast Recovery (RFC 5681).
"""

import time
import threading
import random
from collections import deque
from typing import Dict, Any, List, Optional


class TCPRenoSimulator:
    """
    Standard Educational TCP Reno Congestion Control State Machine.
    
    Principles:
    1. SLOW START:
       - Begins at `initial_cwnd` (default 1 or 2 MSS).
       - While cwnd < ssthresh, cwnd increases exponentially per round (doubles per RTT or +1 per ACK).
       - Transition to Congestion Avoidance when cwnd >= ssthresh.
       
    2. CONGESTION AVOIDANCE (AIMD - Additive Increase):
       - When cwnd >= ssthresh, cwnd grows linearly (+1 MSS per RTT).
       
    3. TRIPLE DUPLICATE ACK (Fast Retransmit & Fast Recovery):
       - ssthresh is set to max(2, cwnd // 2).
       - cwnd is set to ssthresh + 3 (inflated for segments in transit).
       - State switches to FAST_RECOVERY.
       - Upon receiving a fresh ACK: cwnd = ssthresh, state returns to CONGESTION_AVOIDANCE.
       
    4. TIMEOUT (Severe Loss):
       - ssthresh is set to max(2, cwnd // 2).
       - cwnd collapses to 1 MSS (loss of ACK clocking).
       - State resets to SLOW_START.
    """

    STATE_SLOW_START = "SLOW_START"
    STATE_CONGESTION_AVOIDANCE = "CONGESTION_AVOIDANCE"
    STATE_FAST_RECOVERY = "FAST_RECOVERY"

    def __init__(self, initial_cwnd: float = 1.0, initial_ssthresh: float = 16.0, mss_bytes: int = 1024, rtt_ms: float = 50.0):
        self.initial_cwnd = float(initial_cwnd)
        self.initial_ssthresh = float(initial_ssthresh)
        self.mss_bytes = int(mss_bytes)
        self.rtt_ms = float(rtt_ms)

        # Core State Variables
        self.cwnd: float = self.initial_cwnd
        self.ssthresh: float = self.initial_ssthresh
        self.state: str = self.STATE_SLOW_START
        self.round: int = 0
        self.duplicate_acks: int = 0

        # Loss & Transmission Statistics
        self.total_rounds: int = 0
        self.total_loss_events: int = 0
        self.total_timeouts: int = 0
        self.total_fast_retransmits: int = 0
        self.total_retransmissions: int = 0
        self.total_acked_segments: int = 0

        # Automatic Simulation Thread Control
        self.is_running: bool = False
        self._lock = threading.RLock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.step_delay_sec: float = 0.8  # Speed for visual observation

        # Loss configuration
        self.simulated_loss_rate: float = 0.0  # Probability of random loss per round

        # Event trace logs
        self.event_logs: deque = deque(maxlen=60)
        
        # Historical metrics for Chart.js
        self.history: deque = deque(maxlen=45)

        self._add_log(f"TCP Reno initialized: Initial cwnd={self.cwnd:.1f} MSS, ssthresh={self.ssthresh:.1f} MSS, MSS={self.mss_bytes} B", "INFO")
        self._add_log("State: SLOW START (Exponential Growth phase)", "INFO")
        self.record_snapshot()

    def _add_log(self, message: str, level: str = "INFO"):
        timestamp_str = time.strftime("%H:%M:%S")
        self.event_logs.append({
            "time": timestamp_str,
            "round": self.round,
            "message": f"[TCP RENO] {message}",
            "level": level,
            "algorithm": "TCP RENO"
        })

    def record_snapshot(self):
        """Captures a snapshot point for charts."""
        throughput_est = round((self.cwnd * self.mss_bytes * 8) / (self.rtt_ms / 1000.0) / 1000.0, 1) # kbps
        self.history.append({
            "round": self.round,
            "time": time.strftime("%H:%M:%S"),
            "cwnd": round(self.cwnd, 2),
            "ssthresh": round(self.ssthresh, 2),
            "state": self.state,
            "throughput_kbps": throughput_est,
            "sending_rate_req_s": round(self.cwnd * (1000.0 / self.rtt_ms) / 10.0, 1) # Coupled application equivalent
        })

    def step(self) -> Dict[str, Any]:
        """
        Executes one discrete Transmission Round (1 RTT) of TCP Reno algorithm.
        """
        with self._lock:
            self.round += 1
            self.total_rounds += 1
            old_cwnd = self.cwnd
            old_state = self.state

            # 1. Check for random simulated packet loss if configured
            if self.simulated_loss_rate > 0 and random.random() < self.simulated_loss_rate:
                # 70% triple duplicate ACK, 30% timeout
                if random.random() < 0.70:
                    self._handle_triple_dup_ack_internal()
                else:
                    self._handle_timeout_internal()
                self.record_snapshot()
                return self.get_state()

            # 2. Normal ACK Arrival Processing per State
            if self.state == self.STATE_SLOW_START:
                # In Slow Start: cwnd grows exponentially per round (+1 per ACK, doubling per round)
                # Cap round increase to cwnd
                growth = self.cwnd
                self.cwnd += growth
                self.total_acked_segments += int(self.cwnd)
                self._add_log(f"Round {self.round}: cwnd doubled from {old_cwnd:.1f} to {self.cwnd:.1f} MSS (Slow Start Exponential)", "INFO")

                # Check if threshold reached
                if self.cwnd >= self.ssthresh:
                    self.state = self.STATE_CONGESTION_AVOIDANCE
                    self._add_log(f"cwnd ({self.cwnd:.1f}) reached ssthresh ({self.ssthresh:.1f}). State: CONGESTION AVOIDANCE (Linear AIMD)", "WARNING")

            elif self.state == self.STATE_CONGESTION_AVOIDANCE:
                # In Congestion Avoidance: Additive Increase (+1 MSS per RTT)
                self.cwnd += 1.0
                self.total_acked_segments += int(self.cwnd)
                self._add_log(f"Round {self.round}: Additive Increase (+1 MSS). cwnd: {old_cwnd:.1f} -> {self.cwnd:.1f} MSS", "INFO")

            elif self.state == self.STATE_FAST_RECOVERY:
                # In Fast Recovery: New ACK received -> exit fast recovery, set cwnd = ssthresh
                self.cwnd = self.ssthresh
                self.state = self.STATE_CONGESTION_AVOIDANCE
                self.total_acked_segments += int(self.cwnd)
                self._add_log(f"Round {self.round}: Fresh ACK received. Exiting Fast Recovery. cwnd deflated to ssthresh={self.ssthresh:.1f} MSS. State: CONGESTION AVOIDANCE", "SUCCESS")

            self.record_snapshot()
            return self.get_state()

    def trigger_triple_dup_ack(self) -> Dict[str, Any]:
        """
        Manually triggers a 3-Duplicate-ACK packet loss event.
        Executes Fast Retransmit + Fast Recovery.
        """
        with self._lock:
            self.round += 1
            self.total_rounds += 1
            self._handle_triple_dup_ack_internal()
            self.record_snapshot()
            return self.get_state()

    def _handle_triple_dup_ack_internal(self):
        old_cwnd = self.cwnd
        self.total_loss_events += 1
        self.total_fast_retransmits += 1
        self.total_retransmissions += 1

        # Multiplicative Decrease
        self.ssthresh = max(2.0, float(int(self.cwnd // 2)))
        self.cwnd = self.ssthresh + 3.0  # Fast Recovery window inflation
        self.state = self.STATE_FAST_RECOVERY

        self._add_log(f"Packet loss detected: 3 Duplicate ACKs received! Fast Retransmit triggered for lost segment.", "DANGER")
        self._add_log(f"Multiplicative Decrease: ssthresh = cwnd/2 = {self.ssthresh:.1f} MSS", "WARNING")
        self._add_log(f"State: FAST RECOVERY. cwnd inflated to ssthresh+3 = {self.cwnd:.1f} MSS (old cwnd was {old_cwnd:.1f})", "WARNING")

    def trigger_timeout(self) -> Dict[str, Any]:
        """
        Manually triggers a Retransmission Timeout (RTO) event.
        Severe congestion loss -> drops cwnd to 1, resets to Slow Start.
        """
        with self._lock:
            self.round += 1
            self.total_rounds += 1
            self._handle_timeout_internal()
            self.record_snapshot()
            return self.get_state()

    def _handle_timeout_internal(self):
        old_cwnd = self.cwnd
        self.total_loss_events += 1
        self.total_timeouts += 1
        self.total_retransmissions += 1

        # Multiplicative decrease of ssthresh and reset cwnd to 1
        self.ssthresh = max(2.0, float(int(self.cwnd // 2)))
        self.cwnd = 1.0
        self.state = self.STATE_SLOW_START

        self._add_log(f"RETRANSMISSION TIMEOUT (RTO) expired! Severe packet loss detected.", "DANGER")
        self._add_log(f"ssthresh reduced to max(2, cwnd/2) = {self.ssthresh:.1f} MSS. cwnd collapsed from {old_cwnd:.1f} to 1.0 MSS.", "DANGER")
        self._add_log("State reset to: SLOW START (Re-establishing ACK clock)", "INFO")

    def start_auto_simulation(self):
        """Starts background auto-stepper."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_auto_loop, daemon=True)
        self._thread.start()
        self._add_log("TCP Reno auto-simulation running.", "INFO")

    def stop_auto_simulation(self):
        """Pauses/stops auto-stepper."""
        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        self._add_log("TCP Reno auto-simulation paused/stopped.", "INFO")

    def _run_auto_loop(self):
        while self.is_running and not self._stop_event.is_set():
            time.sleep(self.step_delay_sec)
            if not self.is_running or self._stop_event.is_set():
                break
            # Automatically introduce occasional loss under heavy window to simulate realistic network capacity boundary
            if self.cwnd > 28.0 and random.random() < 0.35:
                self.trigger_triple_dup_ack()
            else:
                self.step()

    def configure(self, initial_cwnd: Optional[float] = None, ssthresh: Optional[float] = None, loss_rate: Optional[float] = None, speed: Optional[float] = None):
        """Configures simulation parameters."""
        with self._lock:
            if initial_cwnd is not None and initial_cwnd > 0:
                self.cwnd = float(initial_cwnd)
            if ssthresh is not None and ssthresh > 0:
                self.ssthresh = float(ssthresh)
            if loss_rate is not None:
                self.simulated_loss_rate = max(0.0, min(1.0, float(loss_rate)))
            if speed is not None and speed > 0.05:
                self.step_delay_sec = float(speed)
            self._add_log(f"Parameters updated: cwnd={self.cwnd:.1f}, ssthresh={self.ssthresh:.1f}, loss_rate={self.simulated_loss_rate:.2f}", "INFO")

    def reset(self):
        """Resets Reno simulation state."""
        self.stop_auto_simulation()
        with self._lock:
            self.cwnd = self.initial_cwnd
            self.ssthresh = self.initial_ssthresh
            self.state = self.STATE_SLOW_START
            self.round = 0
            self.duplicate_acks = 0
            self.total_rounds = 0
            self.total_loss_events = 0
            self.total_timeouts = 0
            self.total_fast_retransmits = 0
            self.total_retransmissions = 0
            self.total_acked_segments = 0
            self.event_logs.clear()
            self.history.clear()
            self._add_log("TCP Reno simulation reset to initial state.", "INFO")
            self.record_snapshot()

    def get_modeled_sending_limit(self) -> float:
        """
        Coupling helper: Maps current cwnd to simulated client request rate limit.
        1 segment ~ 1 concurrent request.
        """
        with self._lock:
            # e.g., cwnd segments per RTT (50ms) -> (cwnd / 0.05) scaled to app requests
            return max(2.0, self.cwnd * 2.0)

    def get_state(self) -> Dict[str, Any]:
        """Returns full state representation."""
        with self._lock:
            throughput_est_kbps = round((self.cwnd * self.mss_bytes * 8) / (self.rtt_ms / 1000.0) / 1000.0, 1)
            return {
                "algorithm": "TCP Reno Congestion Control",
                "source_module": "simulation/tcp_reno.py",
                "state": self.state,
                "cwnd": round(self.cwnd, 2),
                "ssthresh": round(self.ssthresh, 2),
                "mss_bytes": self.mss_bytes,
                "rtt_ms": self.rtt_ms,
                "round": self.round,
                "total_rounds": self.total_rounds,
                "total_loss_events": self.total_loss_events,
                "total_timeouts": self.total_timeouts,
                "total_fast_retransmits": self.total_fast_retransmits,
                "total_retransmissions": self.total_retransmissions,
                "total_acked_segments": self.total_acked_segments,
                "throughput_estimate_kbps": throughput_est_kbps,
                "modeled_sending_limit": round(self.get_modeled_sending_limit(), 1),
                "is_running": self.is_running,
                "simulated_loss_rate": self.simulated_loss_rate,
                "history": list(self.history),
                "event_logs": list(self.event_logs)
            }
