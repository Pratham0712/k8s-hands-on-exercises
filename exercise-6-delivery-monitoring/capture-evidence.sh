#!/usr/bin/env bash
# Captures evidence for the scenario currently deployed by the Jenkins pipeline.
#
# Usage:  ./capture-evidence.sh normal      (after a SCENARIO=normal build)
#         ./capture-evidence.sh incident    (after a SCENARIO=incident build)
#
# Everything is written to ./evidence/ with the scenario in the file name.
set -euo pipefail

SCENARIO="${1:-}"
JENKINS_CONTAINER="jenkins-ex6"
JOB="delivery-monitoring"
OUT="evidence"

if [[ "$SCENARIO" != "normal" && "$SCENARIO" != "incident" ]]; then
    echo "Usage: $0 normal|incident"
    exit 1
fi
mkdir -p "$OUT"

# --- 1. Guard: the running app must be in the scenario we are documenting -----
deployed=$(docker logs delivery-metrics 2>&1 | grep -m1 'Scenario:' | awk '{print $3}' || true)
if [[ "$deployed" != "$SCENARIO" ]]; then
    echo "The running app is in scenario '${deployed:-unknown}', not '$SCENARIO'."
    echo "Run the Jenkins build with SCENARIO=$SCENARIO first, then re-run this script."
    exit 1
fi
echo "[1/4] App is running in scenario: $deployed"

# --- 2. Stack state and metrics ---------------------------------------------------
docker ps --filter network=monitoring \
    --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' \
    > "$OUT/containers-$SCENARIO.txt"
curl -s localhost:8000/metrics \
    | grep -E '^(total_|pending_|on_the_way_|average_)' \
    > "$OUT/metrics-$SCENARIO.txt"
curl -s localhost:9090/api/v1/targets | python3 -m json.tool > "$OUT/prometheus-targets-$SCENARIO.json"
echo "[2/4] Saved containers, metrics and target health"

# --- 3. Jenkins console log of the latest build ----------------------------------
build=$(docker exec "$JENKINS_CONTAINER" sh -c \
    "ls /var/jenkins_home/jobs/$JOB/builds | grep -E '^[0-9]+$' | sort -n | tail -1")
# Strip Jenkins' hidden console annotations (ESC[8mha:...ESC[0m) so the log is readable
docker exec "$JENKINS_CONTAINER" cat "/var/jenkins_home/jobs/$JOB/builds/$build/log" \
    | sed 's/\x1b\[8mha:[^\x1b]*\x1b\[0m//g' \
    > "$OUT/jenkins-console-$SCENARIO.txt"
echo "[3/4] Saved Jenkins console log of build #$build"

# --- 4. Alert timeline: poll every 5s ---------------------------------------------
# normal:   watch for 30s to show alerts stay inactive
# incident: watch until both alerts are firing (max 90s)
timeline="$OUT/alert-timeline-$SCENARIO.txt"
: > "$timeline"
firing=0
for i in $(seq 1 18); do
    states=$(curl -s localhost:9090/api/v1/alerts | grep -o '"state":"[a-z]*"' | tr '\n' ' ' || true)
    echo "poll $i (+$(( (i - 1) * 5 ))s)  ${states:-no active alerts}" | tee -a "$timeline"
    firing=$(echo "$states" | grep -o 'firing' | wc -l || true)

    if [[ "$SCENARIO" == "incident" && "$firing" -ge 2 ]]; then break; fi
    if [[ "$SCENARIO" == "normal"   && "$i" -ge 7 ]]; then break; fi
    sleep 5
done
curl -s localhost:9090/api/v1/alerts | python3 -m json.tool > "$OUT/alerts-$SCENARIO.json"

if [[ "$SCENARIO" == "incident" && "$firing" -lt 2 ]]; then
    echo "[4/4] Only $firing alert(s) firing after 90s. Check http://localhost:9090/alerts"
    exit 1
fi
if [[ "$SCENARIO" == "normal" && "$firing" -gt 0 ]]; then
    echo "[4/4] $firing alert(s) firing in normal mode, which should not happen. Check http://localhost:9090/alerts"
    exit 1
fi
echo "[4/4] Alert check passed for scenario '$SCENARIO'"
echo
ls -1 "$OUT"
