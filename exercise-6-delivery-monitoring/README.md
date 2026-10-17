# SecureGroup-IoT

A self-healing secure group communication framework for resource-constrained IoT devices, extending Group OSCORE with automated blackhole attacker detection and cryptographic eviction using Logical Key Hierarchy (LKH) and Subjective Logic-based trust voting.

> **Paper:** "A Self-Healing Secure Group Communication Framework for Resource-Constrained IoT Devices Using Decentralised Key Management and Trust-Based Voting"
> **Journal:** Scientific Reports (Nature Portfolio)
> **Authors:** Pratham Patil, Ravi Teja S, Praveen Kumar Y, Rishikesh Bulagouda, Anitha H M, Nalina V
> **Institution:** B.M.S. College of Engineering, Bengaluru, India

---

## What This Does

SecureGroup-IoT detects and evicts blackhole attackers from IoT group communication networks automatically:

1. **LKH (lkh.c / lkh.h)** — Manages group encryption keys in a binary tree. When a device is kicked out, only O(log N) keys are refreshed, not all of them.
2. **BLET-IoT Watchdog (trust.c / trust.h)** — Monitors each device's forwarding behaviour using Subjective Logic to distinguish attackers from devices with bad radio links.
3. **Consensus Voting Engine (trust.c)** — Multiple watchdogs vote before any eviction is triggered, preventing false positives.

---

## Repository Contents

```
SecureGroup-IoT/
├── lkh.c               # Logical Key Hierarchy implementation (Group Controller)
├── lkh.h               # LKH header file
├── trust.c             # BLET-IoT watchdog + Subjective Logic voting engine
├── trust.h             # Trust module header file
├── udp-server.c        # Group Controller / Server node (runs LKH + watchdog)
├── udp-client.c        # Legitimate client node
├── udp-attacker.c      # Blackhole attacker node (activates at t=30s)
├── simulation.csc      # Cooja simulation configuration (5 nodes)
├── gen_figures.py      # Python script to regenerate all 8 paper figures
└── README.md           # This file
```

---

## Platform and Dependencies

| Item | Version |
|------|---------|
| OS | Contiki-NG 4.0 |
| Simulator | Cooja (bundled with Contiki-NG) |
| Hardware target | Zolertia Zoul (ARM Cortex-M3, 32 kB RAM, 512 kB ROM) |
| Container | Docker — `contiker/contiki-ng` |
| Python | 3.8+ (for figure generation only) |

---

## How to Run the Simulation

### Step 1 — Start the Docker container

```bash
sudo docker run --privileged --sysctl net.ipv6.conf.all.disable_ipv6=0 \
  -v $(pwd):/home/user/contiki-ng/examples/SecureGroup-IoT \
  -it contiker/contiki-ng
```

> **Important:** Always reuse the same container. Do not create a new one each time or the Gradle cache will be lost.
> Use `sudo docker start -ai <container_id>` to resume.

### Step 2 — Open Cooja

```bash
cd /home/user/contiki-ng/tools/cooja
./gradlew run
```

### Step 3 — Load the simulation

In Cooja: **File → Open Simulation → Browse to `simulation.csc`**

### Step 4 — Run

Click **Start** in the Cooja toolbar. The simulation runs for 180 seconds.

- Blackhole attack activates at **t ≈ 30s** (packet counter threshold)
- Attacker is evicted at **t ≈ 52s** (median)
- Group key is rotated immediately after eviction

### Step 5 — Collect logs

```bash
grep "LKH\|TRUST\|EVICT\|PDR" COOJA.testlog > results.txt
```

---

## Simulation Scenarios

Run the simulation three times with different builds:

| Scenario | How to run | What it shows |
|----------|-----------|---------------|
| A — Baseline | Comment out `#define ATTACKER_NODE` and `#define ENABLE_SECURITY` | Normal PDR without attack |
| B — Undefended | Uncomment `#define ATTACKER_NODE`, keep security disabled | PDR collapse without defence |
| C — SecureGroup-IoT | Uncomment both `ATTACKER_NODE` and `ENABLE_SECURITY` | Full system with detection and eviction |

Repeat each scenario **10 times** with different Cooja random seeds for statistical validity.

---

## Generate Figures

```bash
pip install matplotlib numpy
python3 gen_figures.py
```

All 8 figures are saved into `./figures/`.

---

## Key Results

| Metric | Value |
|--------|-------|
| PDR recovered | 43.7% → 93.4% |
| Median Time-to-Isolation | 22.4 seconds |
| Energy overhead | 6.4% |
| RAM used | 17.9 kB / 32 kB |
| Forward secrecy tests passed | 10 / 10 |
| Backward secrecy tests passed | 10 / 10 |

---

## Licence

MIT Licence — free to use, modify, and distribute with attribution.

---

## Citation

If you use this code in your research, please cite:

```
Patil, P., Ravi Teja, S., Praveen Kumar, Y., Bulagouda, R., Anitha, H. M., & Nalina, V.
A Self-Healing Secure Group Communication Framework for Resource-Constrained IoT Devices
Using Decentralised Key Management and Trust-Based Voting.
Scientific Reports, Nature Portfolio (2025).
```
