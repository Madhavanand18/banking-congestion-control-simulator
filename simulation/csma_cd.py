"""
CSMA/CD (Carrier Sense Multiple Access with Collision Detection) Simulation.
Layer: Layer 2 (Data Link Layer / IEEE 802.3 Ethernet Shared Medium).
Algorithm: 1-Persistent CSMA/CD with Truncated Binary Exponential Backoff (BEB).
"""

import time
import random
import threading
from collections import deque
from typing import Dict, Any, List, Optional


class Station:
    """
    Represents an Ethernet Host / Node attached to the shared coaxial bus.
    """
    def __init__(self, station_id: str, name: str):
        self.station_id: str = station_id
        self.name: str = name
        self.frames_queued: int = 0
        self.state: str = "IDLE"  # IDLE, SENSING, TRANSMITTING, COLLISION, BACKOFF
        self.current_retry_count: int = 0
        self.backoff_slots_remaining: int = 0
        self.last_contention_window: int = 0
        self.last_backoff_selected: int = 0
        
        # Cumulative Stats
        self.total_transmitted: int = 0
        self.total_collisions: int = 0
        self.total_failed_retries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id": self.station_id,
            "name": self.name,
            "frames_queued": self.frames_queued,
            "state": self.state,
            "current_retry_count": self.current_retry_count,
            "backoff_slots_remaining": self.backoff_slots_remaining,
            "last_contention_window": self.last_contention_window,
            "last_backoff_selected": self.last_backoff_selected,
            "total_transmitted": self.total_transmitted,
            "total_collisions": self.total_collisions,
            "total_failed_retries": self.total_failed_retries
        }


class CSMACDSimulator:
    """
    Educational Discrete Slot Simulation of Half-Duplex Shared Ethernet Medium.
    
    CSMA/CD Mechanism:
    1. Carrier Sense: Listen before talk. If channel is BUSY, defer until IDLE.
    2. Transmission: If channel is IDLE, start frame transmission.
    3. Collision Detection: If another station transmits at the same slot, a COLLISION occurs.
    4. Jam Signal: Broadcast jam signal to notify all stations.
    5. Binary Exponential Backoff:
       - Attempt k (1 <= k <= 16, capped at 10 for window size).
       - Max slot range R = 2^min(k, 10) - 1.
       - Pick random r in [0, R].
       - Wait r slots before re-sensing channel.
    6. Retry Limit: If k > 16 (or configured max 10/16), drop frame (Network failure).
    """

    CHANNEL_IDLE = "IDLE"
    CHANNEL_BUSY = "BUSY"
    CHANNEL_COLLISION = "COLLISION"

    def __init__(self, station_count: int = 4, max_retries: int = 10):
        self.max_retries = max_retries
        self.slot_number: int = 0
        self.channel_state: str = self.CHANNEL_IDLE
        self.transmitting_stations: List[str] = []
        
        # Initialize Stations
        self.stations: Dict[str, Station] = {}
        self._init_stations(station_count)

        # Global Simulation Metrics
        self.total_attempts: int = 0
        self.successful_transmissions: int = 0
        self.total_collisions: int = 0
        self.total_retransmissions: int = 0
        self.total_dropped_frames: int = 0

        # Backoff Calculation History Table for Educational Visibility
        self.backoff_history: deque = deque(maxlen=20)
        
        # Timeline Event Log
        self.event_logs: deque = deque(maxlen=60)
        
        # Auto-simulation thread controls
        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.step_delay_sec: float = 0.9
        self._lock = threading.RLock()

        self._add_log("CSMA/CD Bus initialized. Medium: Shared Half-Duplex Ethernet (10BASE5 / 10BASE2)", "INFO")
        self._add_log(f"Configured {len(self.stations)} Stations. Algorithm: 1-Persistent CSMA/CD + Binary Exponential Backoff (Max Retries: {self.max_retries})", "INFO")

    def _init_stations(self, count: int):
        self.stations.clear()
        names = ["Station A (Client 1)", "Station B (Client 2)", "Station C (Server 1)", "Station D (Gateway)", "Station E (Host 5)"]
        for i in range(min(count, len(names))):
            s_id = f"STA-{chr(65+i)}"
            self.stations[s_id] = Station(s_id, names[i])

    def _add_log(self, message: str, level: str = "INFO", station_id: str = ""):
        timestamp_str = time.strftime("%H:%M:%S")
        prefix = f"[{station_id}] " if station_id else ""
        self.event_logs.append({
            "slot": self.slot_number,
            "time": timestamp_str,
            "message": f"[CSMA/CD] {prefix}{message}",
            "level": level,
            "algorithm": "CSMA/CD"
        })

    def inject_frames(self, station_id: str, count: int = 1):
        """Adds frames to a specific station's queue."""
        with self._lock:
            if station_id in self.stations:
                self.stations[station_id].frames_queued += count
                self._add_log(f"Injected {count} frame(s) into queue (Total queued: {self.stations[station_id].frames_queued})", "INFO", station_id)

    def trigger_collision_demo(self):
        """
        Inbuilt Educational Demo: Injects frames into Station A and Station B simultaneously to guarantee a collision.
        """
        with self._lock:
            sta_keys = list(self.stations.keys())
            if len(sta_keys) >= 2:
                s1, s2 = sta_keys[0], sta_keys[1]
                self.stations[s1].frames_queued += 1
                self.stations[s2].frames_queued += 1
                self._add_log(f"Collision Scenario Triggered: Simultaneous frames queued at {s1} and {s2}!", "WARNING")

    def step_slot(self) -> Dict[str, Any]:
        """
        Advances discrete simulation by 1 slot time (51.2 microseconds in standard 10Mbps Ethernet).
        Executes Carrier Sensing -> Contention -> Collision Detection -> Backoff update.
        """
        with self._lock:
            self.slot_number += 1
            
            # Step 1: Handle Stations in Backoff Countdown
            stations_ready_to_transmit = []
            
            for s_id, sta in self.stations.items():
                if sta.state == "BACKOFF":
                    if sta.backoff_slots_remaining > 0:
                        sta.backoff_slots_remaining -= 1
                    
                    if sta.backoff_slots_remaining == 0:
                        sta.state = "SENSING"
                        self._add_log(f"Backoff countdown complete. Ready to re-sense channel.", "INFO", s_id)
                elif sta.state in ("IDLE", "COLLISION") and sta.frames_queued > 0:
                    sta.state = "SENSING"

            # Step 2: Carrier Sensing (1-Persistent)
            # All stations in SENSING state check channel
            for s_id, sta in self.stations.items():
                if sta.state == "SENSING":
                    # Channel was idle previous slot -> attempt transmission in this slot
                    stations_ready_to_transmit.append(s_id)

            # Step 3: Medium Contention & Transmission Arbitration
            if len(stations_ready_to_transmit) == 0:
                # Channel is IDLE
                self.channel_state = self.CHANNEL_IDLE
                self.transmitting_stations.clear()
                # Update any station currently in TRANSMITTING state to COMPLETED
                for s_id, sta in self.stations.items():
                    if sta.state == "TRANSMITTING":
                        # Finished transmission without collision
                        sta.frames_queued = max(0, sta.frames_queued - 1)
                        sta.total_transmitted += 1
                        sta.current_retry_count = 0
                        sta.state = "IDLE" if sta.frames_queued == 0 else "SENSING"
                        self.successful_transmissions += 1
                        self._add_log(f"Frame transmitted successfully! (ACK received, slot completed)", "SUCCESS", s_id)

            elif len(stations_ready_to_transmit) == 1:
                # Single station transmits -> SUCCESSFUL TRANSMISSION IN PROGRESS
                s_id = stations_ready_to_transmit[0]
                sta = self.stations[s_id]
                self.channel_state = self.CHANNEL_BUSY
                self.transmitting_stations = [s_id]
                self.total_attempts += 1
                sta.state = "TRANSMITTING"
                
                # Check if this was a retransmission
                if sta.current_retry_count > 0:
                    self.total_retransmissions += 1
                    self._add_log(f"Retransmission attempt {sta.current_retry_count} transmitting frame...", "WARNING", s_id)
                else:
                    self._add_log(f"Channel sensed IDLE. Transmitting frame on bus...", "INFO", s_id)

            else:
                # MULTIPLE STATIONS TRANSMIT SIMULTANEOUSLY -> COLLISION DETECTED!
                self.channel_state = self.CHANNEL_COLLISION
                self.transmitting_stations = list(stations_ready_to_transmit)
                self.total_collisions += 1
                self.total_attempts += len(stations_ready_to_transmit)
                
                colliding_names = ", ".join(stations_ready_to_transmit)
                self._add_log(f"COLLISION DETECTED! Stations ({colliding_names}) transmitted simultaneously in Slot {self.slot_number}!", "DANGER")
                self._add_log("Broadcasting 32-bit JAM SIGNAL across medium to notify all stations...", "WARNING")

                # Apply Binary Exponential Backoff (BEB) to each colliding station
                for s_id in stations_ready_to_transmit:
                    sta = self.stations[s_id]
                    sta.total_collisions += 1
                    sta.current_retry_count += 1
                    k = sta.current_retry_count

                    if k > self.max_retries:
                        # Retry limit reached -> Drop frame
                        sta.frames_queued = max(0, sta.frames_queued - 1)
                        sta.total_failed_retries += 1
                        sta.current_retry_count = 0
                        sta.state = "IDLE"
                        self.total_dropped_frames += 1
                        self._add_log(f"RETRY LIMIT REACHED ({self.max_retries} attempts)! Frame dropped by MAC layer.", "DANGER", s_id)
                    else:
                        # Calculate Contention Window: W = 2^min(k, 10) - 1
                        bounded_k = min(k, 10)
                        contention_window = (2 ** bounded_k) - 1
                        selected_slot = random.randint(0, contention_window)
                        
                        sta.last_contention_window = contention_window
                        sta.last_backoff_selected = selected_slot
                        sta.backoff_slots_remaining = selected_slot
                        sta.state = "BACKOFF"

                        # Record for visual BEB table
                        self.backoff_history.appendleft({
                            "slot": self.slot_number,
                            "station_id": s_id,
                            "retry_k": k,
                            "formula": f"2^min({k},10)-1 = [0..{contention_window}]",
                            "contention_window": contention_window,
                            "backoff_selected": selected_slot
                        })

                        self._add_log(f"Binary Exponential Backoff: Attempt k={k}. Range: [0..{contention_window}]. Selected r={selected_slot} slot(s) delay.", "WARNING", s_id)

            return self.get_state()

    def start_auto_simulation(self):
        """Starts background slot ticker."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_auto_loop, daemon=True)
        self._thread.start()
        self._add_log("CSMA/CD auto-slot scheduler started.", "INFO")

    def stop_auto_simulation(self):
        """Pauses/stops auto-slot ticker."""
        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        self._add_log("CSMA/CD auto-slot scheduler stopped.", "INFO")

    def _run_auto_loop(self):
        while self.is_running and not self._stop_event.is_set():
            time.sleep(self.step_delay_sec)
            if not self.is_running or self._stop_event.is_set():
                break
            # Randomly generate occasional organic frames if queues empty
            all_empty = all(sta.frames_queued == 0 and sta.state == "IDLE" for sta in self.stations.values())
            if all_empty and random.random() < 0.35:
                random_sta = random.choice(list(self.stations.keys()))
                self.stations[random_sta].frames_queued += 1
                
            self.step_slot()

    def configure(self, station_count: Optional[int] = None, max_retries: Optional[int] = None, speed: Optional[float] = None):
        """Updates parameters dynamically."""
        with self._lock:
            if station_count is not None and 2 <= station_count <= 5:
                self._init_stations(station_count)
            if max_retries is not None and max_retries >= 3:
                self.max_retries = int(max_retries)
            if speed is not None and speed > 0.05:
                self.step_delay_sec = float(speed)
            self._add_log(f"Parameters updated: Stations={len(self.stations)}, Max Retries={self.max_retries}, Speed={self.step_delay_sec}s/slot", "INFO")

    def reset(self):
        """Resets CSMA/CD simulator to initial state."""
        self.stop_auto_simulation()
        with self._lock:
            self.slot_number = 0
            self.channel_state = self.CHANNEL_IDLE
            self.transmitting_stations.clear()
            self.total_attempts = 0
            self.successful_transmissions = 0
            self.total_collisions = 0
            self.total_retransmissions = 0
            self.total_dropped_frames = 0
            self.backoff_history.clear()
            self.event_logs.clear()
            self._init_stations(len(self.stations) or 4)
            self._add_log("CSMA/CD simulation reset to initial state.", "INFO")

    def get_state(self) -> Dict[str, Any]:
        """Returns full state representation."""
        with self._lock:
            station_list = [sta.to_dict() for sta in self.stations.values()]
            channel_utilization = round((self.successful_transmissions / max(1, self.slot_number)) * 100, 1)
            
            return {
                "algorithm": "CSMA/CD with Binary Exponential Backoff",
                "source_module": "simulation/csma_cd.py",
                "slot_number": self.slot_number,
                "channel_state": self.channel_state,
                "transmitting_stations": list(self.transmitting_stations),
                "total_attempts": self.total_attempts,
                "successful_transmissions": self.successful_transmissions,
                "total_collisions": self.total_collisions,
                "total_retransmissions": self.total_retransmissions,
                "total_dropped_frames": self.total_dropped_frames,
                "channel_utilization_percent": min(100.0, channel_utilization),
                "max_retries": self.max_retries,
                "is_running": self.is_running,
                "stations": station_list,
                "backoff_history": list(self.backoff_history),
                "event_logs": list(self.event_logs)
            }
