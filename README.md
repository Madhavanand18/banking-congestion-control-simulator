# NexaBank: Real-Time Congestion Monitor & Traffic Simulator

> **Academic Project Title:** Efficient Network Traffic Handling for Online Banking Applications through Congestion Control & Networking Algorithms  
> **Notice:** This application is an **educational Computer Networks simulation**, NOT a real banking system. It models network algorithms in software for laboratory and viva demonstrations without controlling OS kernel sockets or physical Ethernet transceivers.

---

## 1. Project Overview
NexaBank is an educational Computer Networks simulation application designed for college Project-Based Learning (PBL) and laboratory demonstrations. It demonstrates four fundamental networking algorithms operating in real time:

1. **TCP Reno Congestion Control** (`simulation/tcp_reno.py`): Slow Start, Congestion Avoidance (AIMD), Fast Retransmit, Fast Recovery, and Timeout handling.
2. **Priority Queue Scheduling** (`simulation/request_queue.py`): 3-Tier priority request scheduling (HIGH > MEDIUM > LOW) with strict FIFO tie-breaking and bounded buffer capacity.
3. **Token Bucket Traffic Regulation** (`simulation/token_bucket.py`): Monotonic time-based token generation, burst absorption, and HTTP 429 rate limiting.
4. **CSMA/CD Shared Medium Simulation** (`simulation/csma_cd.py`): 1-Persistent carrier sensing, collision detection, jam signal broadcasting, and Binary Exponential Backoff (BEB).

---

## 2. Algorithms Implemented & Source Code

| Algorithm | OSI Layer | Source File | Core Mechanism | Observable Demonstration |
|---|---|---|---|---|
| **TCP Reno** | Layer 4 (Transport) | `simulation/tcp_reno.py` | Slow Start ($cwnd \times 2$), AIMD Congestion Avoidance ($cwnd + 1$), Multiplicative Decrease ($ssthresh = cwnd/2$) | Live cwnd vs ssthresh chart, Fast Recovery on 3-Dup-ACKs, cwnd collapse on Timeout |
| **Priority Queue** | Layer 7 (Application) | `simulation/request_queue.py` | Strict Priority (HIGH > MED > LOW), FIFO arrival tie-breaking, bounded buffer (40) | High-value transfers prioritized; live queue table showing WAITING $\rightarrow$ PROCESSING $\rightarrow$ COMPLETED |
| **Token Bucket** | Layer 7 (Traffic Shaper) | `simulation/token_bucket.py` | Monotonic token refill ($tokens = \min(Cap, tokens + \Delta t \times Rate)$), cost deduction | Animated token tank, burst absorption, rejection counter under traffic surges |
| **CSMA/CD** | Layer 2 (Data Link) | `simulation/csma_cd.py` | 1-Persistent Carrier Sense, Collision Detection, Jam Signal, Binary Exponential Backoff: $r \in [0, 2^{\min(k, 10)} - 1]$ | Visual shared bus diagram, simultaneous collision demo, BEB calculation table |

---

## 3. Technology Stack
- **Backend:** Python 3, Flask, Werkzeug
- **Database:** SQLite 3 (`database.db`)
- **Frontend:** HTML5, Vanilla CSS3 (Custom Dark Navy Theme, Glassmorphism, Responsive), JavaScript ES6+
- **Charts:** Chart.js v4 (CDN)
- **Testing Framework:** Pytest (`tests/`)

---

## 4. Installation & Quick Start

### Step 1: Open Terminal in Project Directory
```powershell
cd "c:\Users\koluk\OneDrive\Documents\CN PBL"
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run Automated Test Suite
```powershell
python -m pytest -v
```

### Step 4: Run the Web Application
```powershell
python app.py
```

### Step 5: Open in Your Web Browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 5. Demo Credentials
- **Username:** `student`
- **Password:** `1234`

---

## 6. Main Pages & Navigation
1. **Login (`/login`):** Authentication with quick demo login credentials.
2. **Dashboard (`/dashboard`):** Real-time account overview, active network status pill, and recent transaction audit records.
3. **Transfer Money (`/transfer`):** Submit high-priority funds transfers (Priority 1) through the rate limiter and priority queue.
4. **Transactions Ledger (`/transactions`):** Full transaction history with execution latencies and network states.
5. **Network Monitor (`/network-monitor`):** Real-time monitoring center with 4 live charts, architecture pipeline flow, traffic generators (LOW, MEDIUM, HIGH, EXTREME), and the One-Click Automated Full Demo.
6. **Algorithms Lab (`/algorithms`):** Dedicated laboratory section featuring interactive tabs and parameter controls for TCP Reno, Priority Queue, Token Bucket, and CSMA/CD.
7. **Congestion Analysis (`/analysis`):** Comparative benchmark experiment (Without vs With Congestion Control) and theory guide.

---

## 7. How to Demonstrate to Faculty / Examiners

### Demonstration A: One-Click Full Demo (Network Monitor)
1. Go to **Network Monitor** (`/network-monitor`).
2. Click **"RUN FULL DEMO"**.
3. Watch the 8-stage automated lifecycle:
   - Traffic ramps up from 7 to 98 req/s.
   - Token Bucket empties, rate limiting low-priority traffic.
   - Priority Queue buffers high/medium priority requests.
   - TCP Reno receives coupled loss signals, reducing its sending window.
   - Traffic subsides; queue drains smoothly at 20 req/s, and system stabilizes.

### Demonstration B: Individual Algorithm Demonstrations (Algorithms Lab)
1. Go to **Algorithms Lab** (`/algorithms`).
2. **TCP Reno Tab:**
   - Click **"Step 1 Round (RTT)"** to watch exponential growth during Slow Start.
   - When $cwnd \ge ssthresh$, observe linear growth in Congestion Avoidance.
   - Click **"Trigger 3 Duplicate ACKs"** to show Fast Retransmit ($ssthresh = cwnd/2$, $cwnd = ssthresh + 3$, Fast Recovery).
   - Click **"Trigger Timeout"** to show severe congestion recovery ($cwnd = 1$, Slow Start).
3. **Priority Queue Tab:**
   - Observe real-time dispatch order (HIGH requests served before MEDIUM and LOW).
   - Verify FIFO arrival order within the same priority tier.
4. **Token Bucket Tab:**
   - Observe animated Token Tank fill level ($tokens / capacity$).
   - Adjust capacity and refill rate presets to demonstrate burst regulation.
5. **CSMA/CD Tab:**
   - Click **"Inject Simultaneous Collision (STA-A & STA-B)"**.
   - Observe collision detection on the shared bus line and Jam Signal broadcast.
   - Inspect the **Binary Exponential Backoff (BEB) Trace** table showing collision attempt $k$, contention window $[0..2^k-1]$, and randomized backoff slots $r$.

---

## 8. Academic Scope & Educational Model Distinction
- **Educational Simulation:** All algorithms execute genuine networking logic in Python source code.
- **Scope Distinction:** The project simulates network protocol behaviors programmatically. It does not capture raw kernel packets or drive physical half-duplex Ethernet hardware.
