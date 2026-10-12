"""
Synthetic Traffic Generator & Automated Guided Presentation Sequence.
Generates realistic banking request flows across 3 Priority Tiers.
"""

import time
import threading
import random
from typing import Optional, Dict, Any
from simulation.request_queue import RequestItem
from simulation.congestion_controller import CongestionController


class TrafficGenerator:
    """
    Simulates variable load patterns and automated multi-stage demonstration.
    Pushes synthetic banking transactions into the CongestionController.
    """
    def __init__(self, controller: CongestionController):
        self.controller = controller
        self.is_running = False
        self.current_level = "IDLE"  # IDLE, LOW, MEDIUM, HIGH, EXTREME, FULL_DEMO
        self.target_rate = 0         # Target req/second
        self._thread: Optional[threading.Thread] = None
        self._demo_thread: Optional[threading.Thread] = None
        self.full_demo_active = False
        self.demo_stage = "IDLE"
        self.demo_progress = 0       # 0 - 100%
        self._stop_event = threading.Event()
        
        # Synthetic request templates across 3 Priority Levels:
        # Priority 1: HIGH (Time-sensitive Authorization, Security Token, Wire Transfer)
        # Priority 2: MEDIUM (Balance Inquiry, Card Validation, Standard Payment)
        # Priority 3: LOW (Mini-Statement, Historical Audit, Batch Query)
        self.synthetic_types = [
            ("BALANCE_INQUIRY", 2),
            ("CARD_VALIDATION", 2),
            ("PAYMENT_AUTH", 2),
            ("OTP_VERIFICATION", 1),
            ("WIRE_TRANSFER_AUTH", 1),
            ("MINI_STATEMENT", 3),
            ("ACCOUNT_LOOKUP", 3),
            ("HISTORICAL_REPORT", 3)
        ]

    def set_traffic_level(self, level: str) -> Dict[str, Any]:
        """
        Sets traffic generator to a fixed level: LOW, MEDIUM, HIGH, EXTREME.
        """
        level = level.upper()
        rate_map = {
            "LOW": 8,       # 5–10 req/sec (Within capacity: 20)
            "MEDIUM": 22,   # 18–25 req/sec (Just exceeds capacity: 20)
            "HIGH": 50,     # 45–60 req/sec (Heavy congestion)
            "EXTREME": 95   # 80–120 req/sec (Critical congestion, token bucket exhaustion & queue saturation)
        }
        
        if level not in rate_map:
            return {"success": False, "error": f"Invalid level '{level}'. Choose LOW, MEDIUM, HIGH, or EXTREME."}
            
        self.stop()
        self.current_level = level
        self.target_rate = rate_map[level]
        self.is_running = True
        self._stop_event.clear()
        
        self.controller.add_log(f"Traffic Generator started at {level} level (~{self.target_rate} req/s)", "INFO")
        
        self._thread = threading.Thread(target=self._traffic_worker, daemon=True)
        self._thread.start()
        
        return {"success": True, "level": self.current_level, "target_rate": self.target_rate}

    def _traffic_worker(self):
        """
        Emits synthetic requests according to self.target_rate.
        """
        while self.is_running and not self._stop_event.is_set():
            if self.target_rate <= 0:
                time.sleep(0.1)
                continue
                
            interval = 1.0 / float(self.target_rate)
            time.sleep(max(0.005, interval * random.uniform(0.85, 1.15)))
            
            if not self.is_running or self._stop_event.is_set():
                break
                
            req_type, priority = random.choice(self.synthetic_types)
            item = RequestItem(
                request_type=req_type,
                priority=priority,
                payload={"source": "SYNTHETIC_SIMULATOR", "account": f"SIM-{random.randint(1000, 9999)}"}
            )
            self.controller.submit_request(item)

    def start_full_demo(self) -> Dict[str, Any]:
        """
        One-Click Guided Presentation Mode:
        Executes a 35-second automated lifecycle demonstrating all congestion control algorithms:
        NORMAL TRAFFIC -> TRAFFIC INCREASING -> CONGESTION DETECTED -> TOKEN BUCKET ACTIVE -> 
        PRIORITY QUEUING -> CONTROLLED PROCESSING -> QUEUE DECREASING -> SYSTEM STABILIZED.
        """
        if self.full_demo_active:
            return {"success": False, "error": "Full Demo is already running."}
            
        self.stop()
        self.full_demo_active = True
        self.current_level = "FULL_DEMO"
        self._stop_event.clear()
        self.is_running = True
        
        self._demo_thread = threading.Thread(target=self._run_demo_sequence, daemon=True)
        self._demo_thread.start()
        
        return {"success": True, "message": "Full demonstration sequence launched."}

    def _run_demo_sequence(self):
        """
        Step-by-step presentation timeline showing real algorithm interplay.
        """
        stages = [
            ("STAGE 1: NORMAL TRAFFIC (Tokens Plentiful, cwnd in Slow Start)", 7, 5),
            ("STAGE 2: TRAFFIC INCREASING (Approaching Capacity 20 req/s)", 22, 5),
            ("STAGE 3: CONGESTION DETECTED (Token Bucket Draining)", 52, 6),
            ("STAGE 4: TOKEN BUCKET & PRIORITY QUEUE SATURATION (Reno Fast Retransmit)", 98, 7),
            ("STAGE 5: PRIORITY QUEUE BUFFERING & FIFO DISPATCH", 35, 5),
            ("STAGE 6: CONTROLLED DRAIN & RATE SHAPING (Token Refill)", 16, 5),
            ("STAGE 7: QUEUE SUBSIDING & CONGESTION AVOIDANCE", 6, 4),
            ("STAGE 8: SYSTEM NORMAL & FULLY RECOVERED", 4, 3)
        ]
        
        total_duration = sum(duration for _, _, duration in stages)
        elapsed_total = 0
        
        # Start background worker for generation
        self._thread = threading.Thread(target=self._traffic_worker, daemon=True)
        self._thread.start()
        
        self.controller.add_log("=== ONE-CLICK GUIDED DEMO SEQUENCE INITIALIZED ===", "INFO")
        
        for stage_name, rate, duration in stages:
            if self._stop_event.is_set():
                break
                
            self.demo_stage = stage_name
            self.target_rate = rate
            self.controller.add_log(f"{stage_name} [Target Rate: ~{rate} req/s]", "WARNING")
            
            # Step in 100ms slices for smooth progress bar animation
            steps = int(duration * 10)
            for _ in range(steps):
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)
                elapsed_total += 0.1
                self.demo_progress = min(100, int((elapsed_total / total_duration) * 100))
                
        self.target_rate = 0
        self.is_running = False
        self.full_demo_active = False
        self.demo_stage = "DEMO COMPLETE - ALL ALGORITHMS EXECUTED & STABILIZED"
        self.demo_progress = 100
        self.current_level = "IDLE"
        self.controller.add_log("=== ONE-CLICK GUIDED DEMO COMPLETED SUCCESSFULLY ===", "SUCCESS")

    def stop(self):
        """
        Halts traffic generator and demo thread.
        """
        self._stop_event.set()
        self.is_running = False
        self.full_demo_active = False
        self.target_rate = 0
        self.current_level = "IDLE"
        self.demo_stage = "IDLE"
        self.demo_progress = 0
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        if self._demo_thread and self._demo_thread.is_alive():
            self._demo_thread.join(timeout=0.2)

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "current_level": self.current_level,
            "target_rate": self.target_rate,
            "full_demo_active": self.full_demo_active,
            "demo_stage": self.demo_stage,
            "demo_progress": self.demo_progress
        }
