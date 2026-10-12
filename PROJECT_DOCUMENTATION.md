# NexaBank: Project Documentation & Implementation Record

## 1. Project Title
**"Efficient Network Traffic Handling for Online Banking Applications through Congestion Control Techniques"**

---

## 2. Project Objective
To design, implement, and analyze an **application-level simulation** of an online banking system ("NexaBank") that demonstrates how software-level congestion control techniques (traffic monitoring, threshold-based congestion detection, admission rate-limiting, and priority request queuing) prevent server starvation, bound transaction latency, and preserve high-priority financial operations under heavy request surges.

---

## 3. Problem Statement
Online banking platforms experience severe, unpredictable traffic bursts during peak events (salary deposits, flash sales, festive shopping, and dividend payouts). When incoming web requests exceed database pool limits and application thread capacity:
1. Conventional unregulated web servers experience thread exhaustion, socket starvation, and cascading 504 Gateway Timeouts.
2. High-value customer transactions (wire transfers, loan payments) are dropped indiscriminately alongside low-value background polling (balance inquiries, account lookups).
3. Frustrated users trigger rapid manual retries ("retry storms"), further multiplying traffic and causing complete service collapse.

TCP-level flow control (Layer 4) only regulates raw packet transmission windows and cannot differentiate between a high-stakes \$10,000 wire transfer and an automated page reload. Therefore, **Application-Level Congestion Control (Layer 7)** is required.

---

## 4. Technology Stack Actually Used

| Layer | Technology | Details |
|---|---|---|
| **Backend Runtime** | Python 3.x | Core application programming language |
| **Web Framework** | Flask (v2.3+) | Lightweight WSGI web framework, session management, REST APIs |
| **Storage / Database** | SQLite 3 | Embedded relational database (`database.db`) |
| **Frontend Markup** | HTML5 | Semantic structure across 6 templates |
| **Frontend Styling** | Custom CSS3 | Modern dark-navy fintech theme, CSS Grid & Flexbox, responsive |
| **Frontend Scripting**| Vanilla JavaScript (ES6+) | Asynchronous `fetch()` polling, DOM updates, event handling |
| **Data Visualization**| Chart.js (v4.4 via CDN) | Dynamic time-series line and bar charts (4 real-time monitors) |
| **Iconography** | FontAwesome 6 (CDN) | Modern interface icons |
| **Fonts** | Google Fonts | Inter (UI) and JetBrains Mono (monospace metrics & code) |

---

## 5. Complete Project Folder Structure

```
nexabank-pbl/
├── app.py                      # Flask entry point, routes, sessions, REST API endpoints
├── database.py                 # SQLite database initialization, schemas, and helper queries
├── requirements.txt            # Python dependencies (Flask, Werkzeug)
├── README.md                   # Concise setup guide and overview
├── PROJECT_DOCUMENTATION.md    # Exhaustive factual technical reference for PBL writing
├── PBL_REPORT.md               # Formal college project report template
├── VIVA.md                     # 25 concise viva examination questions & answers
├── database.db                 # SQLite database file (created upon first run)
├── templates/
│   ├── base.html               # Shared layout (sidebar, topbar, live status indicator)
│   ├── login.html              # Modern login page with demo credential hints
│   ├── dashboard.html          # Account summary, live metric cards, quick shortcuts
│   ├── transfer.html           # Funds transfer form with real-time congestion feedback
│   ├── transactions.html       # Transaction history ledger with latency & congestion audit
│   ├── network_monitor.html    # Centerpiece: live charts, architecture flow, simulator panel, event log
│   └── analysis.html           # Empirical comparative analysis (Without vs With Congestion Control)
├── static/
│   ├── css/
│   │   └── style.css           # Fintech theme: dark navy, emerald/amber/orange/red status colors
│   └── js/
│       ├── network.js          # Core poller: updates cards, pipeline nodes, logs every 1000ms
│       ├── charts.js           # Chart.js initialization and rolling update logic
│       └── dashboard.js        # Dashboard helper scripts
└── simulation/
    ├── request_queue.py        # Priority Request Queue with maximum buffer capacity (40 items)
    ├── congestion_controller.py # Core traffic monitor, rate limiter, congestion detector, scheduler
    └── traffic_generator.py    # Multi-level synthetic load generator and automated Full Demo runner
```

---

## 6. Purpose of Every Important File

- **`app.py`**: Initializes the Flask server, wires up URL endpoints, enforces authentication decorators, routes transfer operations through the simulation pipeline, and dispatches JSON telemetry for the frontend.
- **`database.py`**: Manages SQLite connections, creates `users`, `transactions`, and `network_logs` tables, seeds initial account balance (₹85,450.00) and historical transaction rows.
- **`simulation/request_queue.py`**: Implements `RequestItem` and `RequestQueue`. Enforces maximum buffer limits (40 items) and prioritizes Priority 1 (Customer Transfers) over Priority 2/3 (synthetic inquiries).
- **`simulation/congestion_controller.py`**: The brain of the project. Maintains background execution loops (10 ticks/second), measures 1-second rolling arrival/processing rates, computes average latency, detects congestion state transitions, executes rate-limiting load shedding, and produces comparative benchmark analytics.
- **`simulation/traffic_generator.py`**: Generates synthetic load at LOW, MEDIUM, HIGH, and EXTREME intensities, and coordinates the 8-stage automated "Run Full Demo" presentation sequence.
- **`static/js/network.js`**: Executes periodic asynchronous HTTP GET requests to `/api/network-stats`, synchronizing all open UI widgets without full page reloads.
- **`static/js/charts.js`**: Renders 4 synchronized Chart.js graphs displaying rolling time-series traffic, queue length, response times, and dropped requests.

---

## 7. Database Tables and Schemas

### 1. `users` Table
Stores simulated customer authentication and account balance.
- `id` (INTEGER, Primary Key, Auto-increment)
- `username` (TEXT, Unique, NOT NULL) &mdash; default: `'student'`
- `password` (TEXT, NOT NULL) &mdash; default: `'1234'`
- `full_name` (TEXT, NOT NULL) &mdash; `'Alex Student'`
- `account_number` (TEXT, NOT NULL) &mdash; `'XXXX XXXX 4821'`
- `balance` (REAL, NOT NULL) &mdash; ₹85,450.00

### 2. `transactions` Table
Stores completed and delayed customer wire transfers with diagnostic congestion metrics.
- `id` (INTEGER, Primary Key, Auto-increment)
- `tx_id` (TEXT, Unique, NOT NULL) &mdash; e.g., `'TXN-7192'`
- `timestamp` (TEXT, NOT NULL) &mdash; Formatted `YYYY-MM-DD HH:MM:SS`
- `tx_type` (TEXT, NOT NULL) &mdash; `'Transfer'`, `'Salary Credit'`, `'Utility Bill'`
- `recipient` (TEXT, NOT NULL)
- `account_dest` (TEXT, NOT NULL)
- `amount` (REAL, NOT NULL)
- `processing_time_ms` (REAL, NOT NULL) &mdash; Server latency logged at moment of execution
- `network_status` (TEXT, NOT NULL) &mdash; `'NORMAL'`, `'MODERATE'`, `'CONGESTED'`, `'CRITICAL'`
- `status` (TEXT, NOT NULL) &mdash; `'Completed'`, `'Delayed'`, `'Queued'`, `'Failed'`

### 3. `network_logs` Table
- `id` (INTEGER, Primary Key)
- `timestamp` (TEXT)
- `incoming_rate` (REAL)
- `processing_rate` (REAL)
- `queue_length` (INTEGER)
- `congestion_level` (TEXT)
- `event_text` (TEXT)

---

## 8. Flask Routes and REST API Endpoints

### Frontend Page Routes
| Route | Method | Access | Description |
|---|---|---|---|
| `/` | GET | Public | Redirects to `/dashboard` if logged in, else `/login` |
| `/login` | GET, POST | Public | Validates session login credentials (`student`/`1234`) |
| `/logout` | GET | Authenticated | Clears user session and redirects to login |
| `/dashboard` | GET | Authenticated | Renders account overview, dynamic metric cards, and recent history |
| `/transfer` | GET, POST | Authenticated | Renders interactive funds transfer form |
| `/transactions`| GET | Authenticated | Renders complete audited transaction ledger |
| `/network-monitor`| GET| Authenticated | Centerpiece network traffic monitor with charts and simulator |
| `/analysis` | GET | Authenticated | Comparative analysis: Without vs With Congestion Control |

### REST API Endpoints (JSON)
| Endpoint | Method | Payload / Params | Return Data | Description |
|---|---|---|---|---|
| `/api/network-stats` | GET | None | Rates, queue length, latency, logs, Chart.js history | Polled every 1000ms by `network.js` |
| `/api/simulation/start` | POST | `{"level": "LOW"|"MEDIUM"|"HIGH"|"EXTREME"}` | `{"success": true, "level": ..., "target_rate": ...}` | Starts synthetic traffic generator at target rate |
| `/api/simulation/stop` | POST | None | `{"success": true, "message": "Simulation stopped."}` | Halts active synthetic traffic generation |
| `/api/simulation/reset` | POST | None | `{"success": true, "message": "Counters reset."}` | Clears queue, counters, and event histories |
| `/api/simulation/full-demo`| POST | None | `{"success": true, "message": "Demo launched."}` | Triggers 8-stage automated presentation sequence |
| `/api/simulation/status` | GET | None | Stage name, running flag, demo progress (0-100%) | Polled to update demo progress bar |
| `/api/transfer` | POST | `{"recipient", "account_dest", "amount", "description"}` | `{"success": true, "status": "Completed"|"Delayed", "latency": ...}` | Submits high-priority transfer to congestion controller |
| `/api/transactions` | GET | None | JSON array of last 30 database transactions | Transaction history retrieval |
| `/api/analysis/run-benchmark`| POST | `{"burst_size": 150}` | Comparative telemetry dict (With vs Without control) | Executes empirical burst comparison test |

---

## 9. Congestion Control Algorithm & Architecture

```
USER
  │
  ▼
[ Banking Request ] ─── (Priority 1: Customer Transfer | Priority 2/3: Background Inquiries)
  │
  ▼
[ Traffic Monitor ] ─── (Counts incoming requests / sec in 1.0s rolling windows)
  │
  ▼
[ Congestion Detector ] ── (Evaluates incoming rate vs 20 req/s capacity & queue size)
  │
  ▼
[ Rate Limiter ] ─── (NORMAL: Admit all | CONGESTED: Shed 30% low priority | CRITICAL: Shed 70% low priority)
  │
  ▼
[ Request Queue ] ── (Thread-safe Priority Queue: P1 High > P2 Normal > P3 Low; Max buffer: 40)
  │
  ▼
[ Processing Server ] ── (Leaky-bucket scheduler: Drains at steady capacity: 20 req/sec)
  │
  ▼
[ Banking Response ] ── (Returns HTTP status, simulated latency, ledger commitment)
```

### Detection Thresholds (Configurable in `simulation/congestion_controller.py`)
- **Server Capacity:** Fixed at **20 requests/second** (simulates processing throughput of application workers and database connections).
- **Buffer Capacity:** Fixed at **40 requests** (prevents unbounded memory consumption).
- **NORMAL:** Incoming rate $\le 20 \text{ req/s}$ and Queue size $\le 5$.
- **MODERATE:** Incoming rate $> 20 \text{ req/s}$ and $\le 36 \text{ req/s}$, or Queue size $> 5$.
- **CONGESTED:** Incoming rate $> 36 \text{ req/s}$ and $\le 60 \text{ req/s}$, or Queue size $> 16$.
- **CRITICAL:** Incoming rate $> 60 \text{ req/s}$, or Queue size $> 30$.

### Rate Limiting & Load Shedding Logic
1. **Priority 1 (Customer Transfers):** Guaranteed admission into the queue unless the queue has hit its hard ceiling (40 items).
2. **Priority 2 & 3 (Background Synthetic Traffic):**
   - Under **CONGESTED** conditions, the rate limiter probabilistically sheds 30% of incoming synthetic inquiries.
   - Under **CRITICAL** conditions, the rate limiter aggressively sheds 70% of synthetic traffic.
   - If the queue is 100% saturated ($\ge 40$), all non-priority requests are immediately rejected with simulated HTTP 429 ("Too Many Requests").

### Queue Scheduling Logic
- Thread-safe using `threading.Lock`.
- Drains in ticks of 100ms (10 times per second).
- Up to 2 requests per 100ms are dequeued ($\approx 20 \text{ req/s}$).
- Higher priority buckets are completely drained before lower priority buckets.
- Within the same priority tier, strict FIFO ordering applies.

---

## 10. Automated "Run Full Demo" Sequence
The presentation feature executes an 8-stage lifecycle over approximately 38 seconds:
1. **Stage 1 &mdash; NORMAL TRAFFIC:** Injects ~7 req/s for 5s (System status: NORMAL, Green).
2. **Stage 2 &mdash; TRAFFIC INCREASING:** Injects ~22 req/s for 5s (System status: MODERATE, Yellow).
3. **Stage 3 &mdash; CONGESTION DETECTED:** Injects ~52 req/s for 6s (System status: CONGESTED, Orange).
4. **Stage 4 &mdash; SEVERE CONGESTION & RATE LIMITER ACTIVE:** Injects ~98 req/s for 7s (System status: CRITICAL, Red; rate limiter sheds excess).
5. **Stage 5 &mdash; REQUESTS BUFFERED IN PRIORITY QUEUE:** Injects ~35 req/s for 5s (Buffer absorbs load).
6. **Stage 6 &mdash; CONTROLLED PROCESSING & RATE SHAPING:** Throttles to ~16 req/s for 6s (Steady 20 req/s capacity drain).
7. **Stage 7 &mdash; QUEUE SUBSIDING & DRAINING:** Drops to ~6 req/s for 5s (Queue drains to zero).
8. **Stage 8 &mdash; SYSTEM RECOVERED & NORMAL:** Drops to ~4 req/s for 3s (Green, stable baseline restored).

---

## 11. How Frontend Communicates with Backend
1. **Polling Architecture:** `static/js/network.js` issues a `GET /api/network-stats` request every 1000 milliseconds.
2. **Real-Time DOM Updates:** The returned JSON updates status pills, metric numbers, and terminal lines directly via DOM manipulation (`textContent` and `style`).
3. **Chart Updates:** Chart.js instances receive the 45-point `history` array and update using `chart.update('none')` for smooth, non-blocking rendering.
4. **Transfer Actions:** Transfer submissions use `fetch('/api/transfer', { method: 'POST' })`, returning immediately with latency and queue position calculations.
5. **Benchmark Invocations:** The Analysis page triggers `POST /api/analysis/run-benchmark` with custom burst sizes, receiving back side-by-side empirical metrics.

---

## 12. Security Measures Implemented
- Session-based authentication stored in signed client cookies via Flask `secret_key`.
- Parameterized SQL queries throughout `database.py` to prevent SQL Injection (`cursor.execute(..., (params,))`).
- Server-side input validation on funds transfers (verifying positive amounts, sufficient balance, non-empty fields).
- Graceful error responses (HTTP 400 for bad parameters, HTTP 401 for unauthorized calls, HTTP 429 for rate-limited traffic).

---

## 13. Limitations of the Simulation
- Single-node architecture: Emulated in a single multi-threaded Python process rather than distributed Kubernetes clusters.
- Simulated latency: Service execution time is simulated via micro-delays rather than genuine distributed database queries.
- Academic simulation: Financial transactions are simulated tokens, not connected to banking networks (NPCI, SWIFT, Fedwire).
- In-memory queue: The priority request queue resides in RAM; uncommitted items would not survive a hard process crash.

---

## 14. What Was Intentionally NOT Implemented
- Real banking credentials, real payment gateways (Stripe/Razorpay), and actual money handling.
- TCP/IP packet-level kernel congestion control algorithms (Reno, Cubic, BBR).
- Heavyweight external databases (PostgreSQL, MongoDB) or container engines (Docker, Kubernetes).
- Complex frontend frameworks (React, Next.js, Angular) to ensure 100% native browser portability.

---

## 15. Exact Commands to Run the Project

```bash
# 1. Open Terminal in the project root directory
cd "c:\Madhav Project"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Flask web server
python app.py

# 4. Open in web browser
# Navigate to: http://127.0.0.1:5000
```

### Demo Credentials
- **Username:** `student`
- **Password:** `1234`
