import os
import random
import time

from prometheus_client import Gauge, Summary, start_http_server

# --- Metric definitions ------------------------------------------------------
total_deliveries = Gauge("total_deliveries", "Total number of deliveries")
pending_deliveries = Gauge("pending_deliveries", "Number of pending deliveries")
on_the_way_deliveries = Gauge("on_the_way_deliveries", "Number of deliveries on the way")
# Summary exposes average_delivery_time_sum and average_delivery_time_count
average_delivery_time = Summary("average_delivery_time", "Delivery time in seconds")

# --- Scenarios ---------------------------------------------------------------
# normal:   every value stays BELOW the alert thresholds (pending > 10, avg > 30)
# incident: every value stays ABOVE them, so both alerts must fire
SCENARIOS = {
    "normal":   {"pending": (2, 9),    "avg_time": (15.0, 28.0)},
    "incident": {"pending": (50, 100), "avg_time": (35.0, 60.0)},
}

SCENARIO = os.getenv("SCENARIO", "normal")
if SCENARIO not in SCENARIOS:
    raise SystemExit(f"Unknown SCENARIO={SCENARIO!r}; expected one of {list(SCENARIOS)}")
RANGES = SCENARIOS[SCENARIO]


def simulate_delivery():
    pending = random.randint(*RANGES["pending"])
    on_the_way = random.randint(5, 20)
    delivered = random.randint(30, 70)
    avg_time = random.uniform(*RANGES["avg_time"])

    total = pending + on_the_way + delivered

    print(f"[DEBUG] total={total} pending={pending} "
          f"on_the_way={on_the_way} delivery_time={avg_time:.2f}s")

    total_deliveries.set(total)
    pending_deliveries.set(pending)
    on_the_way_deliveries.set(on_the_way)
    average_delivery_time.observe(avg_time)


if __name__ == "__main__":
    print(f"[INFO] Scenario: {SCENARIO}")
    print("[INFO] Starting HTTP server on port 8000...")
    start_http_server(8000, addr="0.0.0.0")
    while True:
        simulate_delivery()
        time.sleep(1)
