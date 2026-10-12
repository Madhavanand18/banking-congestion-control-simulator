# VIVA EXAMINATION PREPARATION GUIDE
## Efficient Network Traffic Handling for Online Banking Applications through Congestion Control Techniques

---

### **Q1: What is network congestion?**
**Answer:** Network congestion occurs when the volume of incoming transaction requests exceeds the processing or transmission capacity of the system (network bandwidth, server CPU, or database connections), leading to queuing delays, packet/request drops, and performance degradation.

---

### **Q2: What is congestion control?**
**Answer:** Congestion control is a set of techniques used to monitor network load, detect when capacity is being overwhelmed, and actively shape or throttle incoming traffic to prevent system collapse and maintain stable operation.

---

### **Q3: What is the difference between Flow Control and Congestion Control?**
**Answer:**
- **Flow Control:** Prevents a fast sender from overwhelming a single slow receiver (end-to-end between client and server).
- **Congestion Control:** Prevents the aggregate traffic from all senders from overwhelming the intermediate network infrastructure or shared server resources.

---

### **Q4: Why is this an application-level simulation rather than a TCP packet-level simulation?**
**Answer:** In banking, the bottleneck is rarely raw network bandwidth—it is application worker threads and database locks. Layer 4 TCP congestion control treats all packets identically, whereas application-level control (Layer 7) can understand request semantics, allowing us to prioritize a critical money transfer over a non-critical balance inquiry.

---

### **Q5: Why was TCP congestion control not directly implemented in this project?**
**Answer:** TCP congestion control (like Reno, Cubic, or BBR) operates inside the operating system kernel and modulates packet window sizes. It cannot inspect HTTP payloads, authenticate user sessions, or enforce banking business rules. Application-level congestion control directly controls HTTP request admission and queue dispatching.

---

### **Q6: What is Rate Limiting?**
**Answer:** Rate limiting is a traffic-shaping technique that caps the maximum number of requests accepted by a server within a specified time window (e.g., 20 requests per second) to prevent resource exhaustion.

---

### **Q7: What is Request Queuing?**
**Answer:** Request queuing buffers incoming requests in a temporary memory structure when arrival rates temporarily exceed processing capacity, enabling the server to process them steadily without immediate failure.

---

### **Q8: What is Latency?**
**Answer:** Latency is the total elapsed time between a client initiating a banking request and receiving the complete server response. It equals **Queue Wait Time + Execution Service Time**.

---

### **Q9: What is Throughput?**
**Answer:** Throughput is the number of banking requests successfully processed and committed by the system per unit of time (measured here in requests per second, req/s).

---

### **Q10: What is Request Loss?**
**Answer:** Request loss occurs when requests are discarded or rejected—either intentionally by the rate limiter to protect the system (load shedding via HTTP 429), or unintentionally due to queue buffer overflows and server crashes.

---

### **Q11: What is a Timeout and why does it occur during congestion?**
**Answer:** A timeout occurs when a client or gateway stops waiting for a response after a pre-set deadline (e.g., 5 seconds) because the server was bogged down handling a massive queue of requests.

---

### **Q12: What is a "Retry Storm"?**
**Answer:** When requests time out due to server overload, users or automated client apps immediately retry their requests. This multiplies the existing load, making congestion exponentially worse. Rate limiting prevents retry storms by returning quick, polite rejections instead of hanging connections.

---

### **Q13: How does Congestion Detection work in NexaBank?**
**Answer:** The system calculates the incoming request rate over a sliding 1-second window and measures the current queue size. It compares these against fixed thresholds to classify system health into **NORMAL**, **MODERATE**, **CONGESTED**, or **CRITICAL**.

---

### **Q14: Explain the project architecture in simple terms.**
**Answer:** A request flows through 6 stages:
`User Request → Traffic Monitor (measures rate) → Congestion Detector (assesses state) → Rate Limiter (admits or sheds) → Request Queue (prioritizes) → Processing Server (executes at 20 req/s) → Client Response`.

---

### **Q15: How does the priority queue work in NexaBank?**
**Answer:** Customer wire transfers are tagged with **Priority 1 (High)**, while synthetic balance inquiries receive Priority 2 or 3. When the server processes requests, it always empties Priority 1 items before touching lower-priority items. Within the same priority tier, requests follow FIFO (First-In, First-Out).

---

### **Q16: What happens during EXTREME traffic (e.g., 95 req/s)?**
**Answer:**
1. Congestion status switches to **CRITICAL**.
2. The rate limiter activates aggressive load shedding, dropping ~70% of synthetic inquiries.
3. Priority 1 customer transfers continue to be admitted into the priority queue.
4. The server drains requests at its maximum steady throughput of 20 req/s with bounded latency, avoiding a system crash.

---

### **Q17: What does the "Run Full Demo" feature do?**
**Answer:** It runs an automated 8-stage presentation sequence over ~38 seconds, showing examiners the entire lifecycle: Normal traffic $\rightarrow$ Traffic increase $\rightarrow$ Congestion detection $\rightarrow$ Rate limiter activation $\rightarrow$ Queue buffering $\rightarrow$ Controlled drain $\rightarrow$ System recovery back to normal.

---

### **Q18: Why did you choose Python and Flask?**
**Answer:** Python offers clean multi-threading and rapid prototyping, while Flask provides a lightweight, transparent WSGI web server without unnecessary framework overhead, making routing, session handling, and REST APIs straightforward to demonstrate.

---

### **Q19: Why did you choose SQLite?**
**Answer:** SQLite is an embedded, zero-configuration relational database engine stored in a single file (`database.db`). It eliminates external database server dependencies while supporting full SQL transactions and ACID compliance.

---

### **Q20: Why Vanilla JavaScript instead of heavy frameworks like React?**
**Answer:** Vanilla JavaScript runs natively in any browser with zero build steps or npm installations. It easily performs asynchronous polling via the modern `fetch()` API and manipulates the DOM smoothly.

---

### **Q21: Why Chart.js?**
**Answer:** Chart.js is a high-performance, canvas-based JavaScript charting library. It efficiently renders real-time streaming line and bar graphs with minimal CPU overhead.

---

### **Q22: How does the Analysis page demonstrate the value of congestion control?**
**Answer:** It runs an empirical burst benchmark (e.g., 150 requests) comparing an uncontrolled system against NexaBank. The uncontrolled system experiences thread starvation, huge latency (~2,800ms), and timeouts, whereas the controlled system bounds latency to ~210ms and ensures high-priority transactions complete.

---

### **Q23: What are the main limitations of this simulation?**
**Answer:**
1. It runs on a single machine rather than across a distributed cluster of servers.
2. Latency is simulated mathematically rather than through genuine distributed database locks.
3. The queue resides in volatile RAM and is not persisted to disk.

---

### **Q24: How would this be improved for a real production banking system?**
**Answer:**
1. Use distributed message brokers like **RabbitMQ** or **Apache Kafka** for persistent queuing.
2. Implement distributed rate limiters using **Redis** token buckets across API gateways.
3. Add machine-learning models to predict traffic surges before they occur.

---

### **Q25: What is the single most important takeaway from this project?**
**Answer:** Unregulated web systems crash under traffic surges. By placing an **Application-Level Congestion Controller** with rate limiting and priority queuing in front of core banking services, we preserve system stability, bound response latency, and ensure that critical customer financial transactions always succeed.
