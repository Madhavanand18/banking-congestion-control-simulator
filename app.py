import os
import time
import uuid
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from simulation.congestion_controller import CongestionController
from simulation.traffic_generator import TrafficGenerator
from simulation.request_queue import RequestItem
import database

app = Flask(__name__)
app.secret_key = "nexabank-pbl-academic-simulation-secret-key-2026"

# Initialize SQLite database
database.init_db()

# Core Congestion Controller & Traffic Generator singletons
controller = CongestionController(capacity_per_second=20, max_queue_capacity=40)
traffic_gen = TrafficGenerator(controller)

# -------------------------------------------------------------
# Authentication & Session Helpers
# -------------------------------------------------------------
def is_authenticated():
    return session.get("logged_in") is True

@app.route("/")
def index():
    if is_authenticated():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")
            
        if username == "student" and password == "1234":
            session["logged_in"] = True
            session["username"] = "student"
            session["full_name"] = "Alex Student"
            flash("Welcome to NexaBank Portal!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials! Use demo login: student / 1234", "danger")
            return render_template("login.html")
            
    if is_authenticated():
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been safely logged out.", "info")
    return redirect(url_for("login"))

# -------------------------------------------------------------
# Frontend View Pages
# -------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if not is_authenticated():
        return redirect(url_for("login"))
    user = database.get_user_profile("student")
    recent_txs = database.get_recent_transactions(limit=6)
    stats = controller.get_statistics()
    return render_template("dashboard.html", user=user, recent_txs=recent_txs, stats=stats)

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if not is_authenticated():
        return redirect(url_for("login"))
    user = database.get_user_profile("student")
    return render_template("transfer.html", user=user)

@app.route("/transactions")
def transactions():
    if not is_authenticated():
        return redirect(url_for("login"))
    user = database.get_user_profile("student")
    all_txs = database.get_recent_transactions(limit=50)
    return render_template("transactions.html", user=user, transactions=all_txs)

@app.route("/network-monitor")
def network_monitor():
    if not is_authenticated():
        return redirect(url_for("login"))
    user = database.get_user_profile("student")
    stats = controller.get_statistics()
    sim_status = traffic_gen.get_status()
    return render_template("network_monitor.html", user=user, stats=stats, sim_status=sim_status)

@app.route("/analysis")
def analysis():
    if not is_authenticated():
        return redirect(url_for("login"))
    user = database.get_user_profile("student")
    benchmark_data = controller.run_comparative_benchmark(request_burst_size=150)
    return render_template("analysis.html", user=user, benchmark=benchmark_data)

@app.route("/algorithms")
def algorithms():
    """
    Dedicated Computer Networks Algorithms Laboratory View:
    Presents interactive tabs and live visualizations for:
    1. TCP Reno Congestion Control
    2. Priority Queue Scheduling
    3. Token Bucket Traffic Regulation
    4. CSMA/CD Medium Access Simulation
    """
    if not is_authenticated():
        return redirect(url_for("login"))
    user = database.get_user_profile("student")
    stats = controller.get_statistics()
    return render_template("algorithms.html", user=user, stats=stats)

# -------------------------------------------------------------
# REST API Endpoints for Live Simulation & Banking Requests
# -------------------------------------------------------------
@app.route("/api/network-stats")
def api_network_stats():
    stats = controller.get_statistics()
    stats["simulation"] = traffic_gen.get_status()
    return jsonify(stats)

@app.route("/api/simulation/start", methods=["POST"])
def api_sim_start():
    data = request.get_json() or {}
    level = data.get("level", "MEDIUM")
    
    if traffic_gen.is_running and traffic_gen.current_level == level.upper():
        return jsonify({"success": False, "error": f"Traffic simulator is already running at {level} level."}), 400
        
    result = traffic_gen.set_traffic_level(level)
    return jsonify(result)

@app.route("/api/simulation/stop", methods=["POST"])
def api_sim_stop():
    if not traffic_gen.is_running and not traffic_gen.full_demo_active:
        return jsonify({"success": False, "error": "Traffic simulator is not currently running."}), 400
        
    traffic_gen.stop()
    controller.add_log("Traffic generator stopped manually by user", "INFO")
    return jsonify({"success": True, "message": "Simulation stopped."})

@app.route("/api/simulation/reset", methods=["POST"])
def api_sim_reset():
    traffic_gen.stop()
    controller.reset_metrics()
    return jsonify({"success": True, "message": "Simulation counters, Priority Queue, and Token Bucket reset successfully."})

@app.route("/api/simulation/full-demo", methods=["POST"])
def api_sim_full_demo():
    result = traffic_gen.start_full_demo()
    return jsonify(result)

@app.route("/api/simulation/status")
def api_sim_status():
    return jsonify(traffic_gen.get_status())

@app.route("/api/transfer", methods=["POST"])
def api_transfer():
    """
    Submits a user wire transfer through the congestion control pipeline.
    Transfers have HIGH priority (priority=1), but are subject to queue buffering and rate limiting under critical stress.
    """
    if not is_authenticated():
        return jsonify({"success": False, "error": "Unauthorized. Please log in."}), 401
        
    data = request.get_json() or {}
    recipient = data.get("recipient", "").strip()
    account_dest = data.get("account_dest", "").strip()
    amount_str = data.get("amount", "")
    description = data.get("description", "Online Funds Transfer")

    # Validation
    if not recipient or not account_dest or not amount_str:
        return jsonify({"success": False, "error": "All transfer fields are required."}), 400
        
    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({"success": False, "error": "Transfer amount must be strictly greater than zero."}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid amount format. Please enter a valid number."}), 400

    user = database.get_user_profile("student")
    if not user or user["balance"] < amount:
        return jsonify({"success": False, "error": "Insufficient funds in your account for this transfer."}), 400

    # Create RequestItem with Priority 1 (High Priority for customer transactions)
    tx_code = f"TXN-{random.randint(1000, 9999)}"
    req_item = RequestItem(
        request_type="WIRE_TRANSFER",
        priority=1,
        payload={
            "tx_code": tx_code,
            "recipient": recipient,
            "account_dest": account_dest,
            "amount": amount,
            "description": description
        }
    )

    # Ingest through Congestion Controller (Token Bucket -> Priority Queue)
    result = controller.submit_request(req_item)
    network_status = controller.congestion_level

    if not result.get("accepted"):
        # Rate Limiter Rejected / Dropped due to severe buffer overflow or token exhaustion
        tx_status = "Failed"
        proc_time = 3200.0  # simulated timeout
        database.insert_transaction(tx_code, "Transfer", recipient, account_dest, 0.0, proc_time, network_status, tx_status)
        return jsonify({
            "success": False,
            "status": "Failed",
            "reason": result.get("reason", "Request dropped by rate limiter under severe congestion"),
            "network_status": network_status,
            "tx_code": tx_code,
            "processing_time_ms": proc_time
        }), 429

    # Determine simulated latency based on congestion level
    if network_status == "NORMAL":
        tx_status = "Completed"
        proc_time = round(random.uniform(42.0, 75.0), 1)
    elif network_status == "MODERATE":
        tx_status = "Completed"
        proc_time = round(random.uniform(140.0, 260.0), 1)
    elif network_status == "CONGESTED":
        tx_status = "Delayed"
        proc_time = round(random.uniform(480.0, 890.0), 1)
    else:  # CRITICAL
        tx_status = "Delayed"
        proc_time = round(random.uniform(1100.0, 1950.0), 1)

    # Record in database
    database.insert_transaction(tx_code, "Transfer", recipient, account_dest, amount, proc_time, network_status, tx_status)
    
    # Fetch updated balance
    updated_user = database.get_user_profile("student")
    
    controller.add_log(f"Transfer {tx_code} (₹{amount:,.2f}) processed with status: {tx_status} ({proc_time}ms)", "SUCCESS" if tx_status == "Completed" else "WARNING")

    return jsonify({
        "success": True,
        "status": tx_status,
        "tx_code": tx_code,
        "amount": amount,
        "recipient": recipient,
        "new_balance": updated_user["balance"] if updated_user else 0.0,
        "processing_time_ms": proc_time,
        "network_status": network_status,
        "queue_position": result.get("queue_position", 1),
        "priority": "HIGH (Priority 1)",
        "message": f"Transfer successfully routed via Priority Queue (FIFO tie-break) and marked as {tx_status}."
    })

@app.route("/api/transactions")
def api_transactions():
    txs = database.get_recent_transactions(limit=30)
    return jsonify(txs)

@app.route("/api/analysis/run-benchmark", methods=["POST"])
def api_run_benchmark():
    data = request.get_json() or {}
    burst_size = data.get("burst_size", 150)
    try:
        burst_size = int(burst_size)
        burst_size = max(50, min(burst_size, 500))
    except ValueError:
        burst_size = 150
        
    benchmark_data = controller.run_comparative_benchmark(request_burst_size=burst_size)
    controller.add_log(f"Comparative benchmark executed with {burst_size} synthetic burst requests", "INFO")
    return jsonify(benchmark_data)

# -------------------------------------------------------------
# REST API Endpoints for Individual Algorithms Control & State
# -------------------------------------------------------------
@app.route("/api/algorithms/summary")
def api_algorithms_summary():
    """Returns combined status of all 4 computer networks algorithms."""
    return jsonify({
        "tcp_reno": controller.tcp_reno.get_state(),
        "priority_queue": controller.queue.get_summary(),
        "token_bucket": controller.token_bucket.get_state(),
        "csma_cd": controller.csma_cd.get_state()
    })

# --- TCP Reno API ---
@app.route("/api/algorithms/tcp-reno/step", methods=["POST"])
def api_reno_step():
    state = controller.tcp_reno.step()
    return jsonify({"success": True, "state": state})

@app.route("/api/algorithms/tcp-reno/start", methods=["POST"])
def api_reno_start():
    controller.tcp_reno.start_auto_simulation()
    return jsonify({"success": True, "message": "TCP Reno auto-simulation started."})

@app.route("/api/algorithms/tcp-reno/stop", methods=["POST"])
def api_reno_stop():
    controller.tcp_reno.stop_auto_simulation()
    return jsonify({"success": True, "message": "TCP Reno auto-simulation stopped."})

@app.route("/api/algorithms/tcp-reno/triple-dup-ack", methods=["POST"])
def api_reno_triple_dup_ack():
    state = controller.tcp_reno.trigger_triple_dup_ack()
    return jsonify({"success": True, "message": "Triple Duplicate ACK triggered (Fast Retransmit & Fast Recovery).", "state": state})

@app.route("/api/algorithms/tcp-reno/timeout", methods=["POST"])
def api_reno_timeout():
    state = controller.tcp_reno.trigger_timeout()
    return jsonify({"success": True, "message": "Retransmission Timeout (RTO) triggered (cwnd collapsed to 1).", "state": state})

@app.route("/api/algorithms/tcp-reno/reset", methods=["POST"])
def api_reno_reset():
    controller.tcp_reno.reset()
    return jsonify({"success": True, "message": "TCP Reno simulation reset."})

@app.route("/api/algorithms/tcp-reno/configure", methods=["POST"])
def api_reno_configure():
    data = request.get_json() or {}
    controller.tcp_reno.configure(
        initial_cwnd=data.get("initial_cwnd"),
        ssthresh=data.get("ssthresh"),
        loss_rate=data.get("loss_rate"),
        speed=data.get("speed")
    )
    return jsonify({"success": True, "state": controller.tcp_reno.get_state()})

# --- Token Bucket API ---
@app.route("/api/algorithms/token-bucket/configure", methods=["POST"])
def api_token_bucket_configure():
    data = request.get_json() or {}
    controller.token_bucket.configure(
        capacity=data.get("capacity"),
        refill_rate=data.get("refill_rate")
    )
    return jsonify({"success": True, "state": controller.token_bucket.get_state()})

@app.route("/api/algorithms/token-bucket/reset", methods=["POST"])
def api_token_bucket_reset():
    controller.token_bucket.reset()
    return jsonify({"success": True, "message": "Token Bucket reset successfully."})

# --- Priority Queue API ---
@app.route("/api/algorithms/priority-queue/clear", methods=["POST"])
def api_priority_queue_clear():
    controller.queue.clear()
    return jsonify({"success": True, "message": "Priority Queue buffer cleared."})

# --- CSMA/CD API ---
@app.route("/api/algorithms/csma-cd/step", methods=["POST"])
def api_csma_step():
    state = controller.csma_cd.step_slot()
    return jsonify({"success": True, "state": state})

@app.route("/api/algorithms/csma-cd/start", methods=["POST"])
def api_csma_start():
    controller.csma_cd.start_auto_simulation()
    return jsonify({"success": True, "message": "CSMA/CD auto-slot simulation started."})

@app.route("/api/algorithms/csma-cd/stop", methods=["POST"])
def api_csma_stop():
    controller.csma_cd.stop_auto_simulation()
    return jsonify({"success": True, "message": "CSMA/CD simulation stopped."})

@app.route("/api/algorithms/csma-cd/inject", methods=["POST"])
def api_csma_inject():
    data = request.get_json() or {}
    station_id = data.get("station_id", "STA-A")
    count = int(data.get("count", 1))
    controller.csma_cd.inject_frames(station_id, count)
    return jsonify({"success": True, "state": controller.csma_cd.get_state()})

@app.route("/api/algorithms/csma-cd/collision-demo", methods=["POST"])
def api_csma_collision_demo():
    controller.csma_cd.trigger_collision_demo()
    return jsonify({"success": True, "message": "Collision scenario initiated: Frames queued at Station A and Station B.", "state": controller.csma_cd.get_state()})

@app.route("/api/algorithms/csma-cd/reset", methods=["POST"])
def api_csma_reset():
    controller.csma_cd.reset()
    return jsonify({"success": True, "message": "CSMA/CD simulation reset."})

@app.route("/api/algorithms/csma-cd/configure", methods=["POST"])
def api_csma_configure():
    data = request.get_json() or {}
    controller.csma_cd.configure(
        station_count=data.get("station_count"),
        max_retries=data.get("max_retries"),
        speed=data.get("speed")
    )
    return jsonify({"success": True, "state": controller.csma_cd.get_state()})

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
