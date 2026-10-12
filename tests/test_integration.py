import pytest
import json
from app import app, controller, traffic_gen


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["username"] = "student"
            sess["full_name"] = "Alex Student"
        yield client


def test_network_stats_endpoint(client):
    res = client.get("/api/network-stats")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "incoming_rate" in data
    assert "processing_rate" in data
    assert "queue_length" in data
    assert "token_bucket" in data
    assert "tcp_reno" in data
    assert "csma_cd" in data


def test_algorithms_summary_endpoint(client):
    res = client.get("/api/algorithms/summary")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "tcp_reno" in data
    assert "priority_queue" in data
    assert "token_bucket" in data
    assert "csma_cd" in data
    assert data["tcp_reno"]["algorithm"] == "TCP Reno Congestion Control"


def test_algorithms_lab_view_page(client):
    res = client.get("/algorithms")
    assert res.status_code == 200
    assert b"Computer Networks Algorithms Laboratory" in res.data
    assert b"TCP Reno Congestion Control" in res.data
    assert b"Priority Queue Scheduler" in res.data
    assert b"Token Bucket Regulator" in res.data
    assert b"CSMA/CD Medium Access" in res.data


def test_traffic_generator_level_control(client):
    # Start LOW traffic
    res = client.post("/api/simulation/start", json={"level": "LOW"})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["success"] is True

    # Check status
    res_status = client.get("/api/simulation/status")
    status_data = json.loads(res_status.data)
    assert status_data["is_running"] is True
    assert status_data["current_level"] == "LOW"

    # Stop simulation
    res_stop = client.post("/api/simulation/stop")
    assert res_stop.status_code == 200


def test_transfer_routes_through_priority_queue(client):
    res = client.post("/api/transfer", json={
        "recipient": "Test Faculty Demo",
        "account_dest": "TEST0001234",
        "amount": "500",
        "description": "Integration Test Transfer"
    })
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["success"] is True
    assert "tx_code" in data
    assert data["priority"] == "HIGH (Priority 1)"


def test_tcp_reno_api_triggers(client):
    # Step Reno via API
    res_step = client.post("/api/algorithms/tcp-reno/step")
    assert res_step.status_code == 200
    
    # Trigger 3 Dup ACK via API
    res_dup = client.post("/api/algorithms/tcp-reno/triple-dup-ack")
    assert res_dup.status_code == 200
    data = json.loads(res_dup.data)
    assert data["state"]["state"] == "FAST_RECOVERY"

    # Trigger Timeout via API
    res_to = client.post("/api/algorithms/tcp-reno/timeout")
    assert res_to.status_code == 200
    data_to = json.loads(res_to.data)
    assert data_to["state"]["state"] == "SLOW_START"


def test_csma_cd_api_collision_demo(client):
    res = client.post("/api/algorithms/csma-cd/collision-demo")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["success"] is True
