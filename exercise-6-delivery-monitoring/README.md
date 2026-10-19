# Exercise 6: Real-Time Delivery Monitoring and Alerting (ZAPPTTO)

A simulated delivery service exposes Prometheus metrics. Prometheus scrapes them and evaluates alert rules, Grafana shows them on a dashboard, and a parameterized Jenkins pipeline builds, validates, deploys and smoke-tests the whole stack. Every piece is defined in this folder, including the Grafana data source and dashboard, so one pipeline run reproduces everything.

## Architecture

```
              Docker network "monitoring" (containers find each other by name)

  delivery-metrics :8000  <-- scrape every 5s --  prometheus :9090  <-- PromQL --  grafana :3000
  (Python simulator)                              (alert rules)                    (provisioned dashboard)

              All three are built and deployed by jenkins-ex6 :8080, which drives the
              host's Docker engine through the mounted /var/run/docker.sock
```

## Files

| File | Purpose |
|---|---|
| `delivery_metrics.py` | Exposes `total_deliveries`, `pending_deliveries`, `on_the_way_deliveries` (Gauges) and `average_delivery_time` (Summary, which produces `_sum` and `_count`) on `:8000/metrics` |
| `Dockerfile` | Image for the simulator |
| `prometheus.yml` | 5s scrape and evaluation interval; target addressed by container name |
| `alert_rules.yml` | `HighPendingDeliveries` (pending > 10 for 15s, warning) and `HighAverageDeliveryTime` (1-minute average > 30s for 15s, critical) |
| `Dockerfile.prometheus` | Prometheus image with both config files copied in |
| `grafana/datasource.yml` | Provisions the Prometheus data source with a fixed uid |
| `grafana/dashboards.yml` | Tells Grafana to load dashboards from `/etc/grafana/dashboards` |
| `grafana/delivery-dashboard.json` | The "ZAPPTTO Delivery Monitoring" dashboard: firing-alert count plus the four metric panels |
| `Dockerfile.grafana` | Grafana image with the data source and dashboard copied in |
| `Dockerfile.jenkins` | Jenkins LTS plus the Docker CLI |
| `Jenkinsfile` | Pre-check Docker, Setup Workspace, Build Images, Validate Prometheus Config, Deploy Stack, Smoke Test |
| `capture-evidence.sh` | Saves stack state, metrics, the Jenkins log and an alert timeline into `evidence/` |

## Scenarios

The simulator reads `SCENARIO`, which the pipeline passes in as a build parameter, so alert behaviour is predictable:

| Scenario | pending | delivery time | Expected alerts |
|---|---|---|---|
| `normal` | 2 to 9 | 15 to 28s | None; every value is below its threshold |
| `incident` | 50 to 100 | 35 to 60s | Both go Pending, then Firing once the condition has held for 15s |

## Changes from the lab manual, and why

1. **A user-defined Docker network instead of `--network=host` and `172.17.0.1`.** On Docker Desktop with WSL2, the Docker engine runs in its own VM, so `172.17.0.1` is not the WSL distro and host networking is opt-in. Addressing containers by name works the same everywhere, and it is the same idea as Kubernetes Service DNS.
2. **Added the missing application `Dockerfile`.** The manual's pipeline runs `docker build` but never provides a Dockerfile. `PYTHONUNBUFFERED=1` makes `print()` output appear in `docker logs`.
3. **A custom Jenkins image and the Docker socket mounted into it.** The stock `jenkins/jenkins:lts` image has no Docker CLI, so the manual's first stage fails.
4. **Config files copied into images instead of `-v $WORKSPACE/...` bind mounts.** When Jenkins drives the host's Docker engine, bind-mount paths are looked up on the host, which cannot see Jenkins' internal workspace. Docker then silently creates empty directories in their place and Prometheus fails to start.
5. **A one-minute average for the delivery-time alert.** `sum / count` averages over the app's whole lifetime: after 10,000 observations a single new value moves it by about 0.0015, so it settles near 30 and the alert flips randomly. `rate(sum[1m]) / rate(count[1m])` averages only the last minute.
6. **A scenario switch instead of editing code.** The manual's normal range (pending 10 to 20) already crosses the threshold, so its "simulate alerts" step shows no change. Here normal stays quiet and incident always fires.
7. **The Grafana dashboard is provisioned from a file instead of built by hand,** so it lives in the repo and comes back on every deploy. The dashboard file is kept in `/etc/grafana/dashboards` rather than `/var/lib/grafana`, because any volume mounted at `/var/lib/grafana` would hide files copied there.
8. **A smoke test stage.** It checks from inside the Docker network that the metrics endpoint responds, Prometheus targets are UP and Grafana is healthy, so a green build means a working stack, not just running containers.

Smaller fixes: consistent `alert_rules.yml` naming, a 5s scrape interval (the default 15s misses most of the app's 1s updates), a virtualenv for local Python (Ubuntu blocks system-wide `pip install` under PEP 668), and the correct initial admin password path, `/var/jenkins_home/secrets/initialAdminPassword`.

## Running it

Docker Desktop's engine must be running; Minikube can stay stopped. This Jenkins runs as `jenkins-ex6`. Exercise 7's Jenkins (`jenkins`) also uses port 8080, so only one of them can run at a time.

### 1. Start Jenkins

```bash
docker stop jenkins 2>/dev/null            # Exercise 7 Jenkins, if running
docker build -t jenkins-docker -f Dockerfile.jenkins .
docker run -d --name jenkins-ex6 -u root \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD":/src:ro \
  jenkins-docker
```

### 2. Make sure the Pipeline plugin is installed

```bash
docker exec jenkins-ex6 jenkins-plugin-cli \
  --plugins workflow-aggregator pipeline-stage-view \
  -d /var/jenkins_home/plugins
docker restart jenkins-ex6
```

### 3. Create the job

In Jenkins, choose **New Item**, name it `delivery-monitoring`, select **Pipeline** (not Freestyle), and paste `Jenkinsfile` into the Pipeline script box.

### 4. Run both scenarios

1. Run **Build Now** once. This build fails, because Jenkins only learns the `SCENARIO` parameter from it (see the troubleshooting log).
2. **Build with Parameters**, `SCENARIO=normal`, then run `./capture-evidence.sh normal`
3. **Build with Parameters**, `SCENARIO=incident`, then run `./capture-evidence.sh incident`

| URL | What |
|---|---|
| http://localhost:8000/metrics | Raw metrics |
| http://localhost:9090/targets | Scrape targets; both should be UP |
| http://localhost:9090/alerts | Alert states |
| http://localhost:3000 | Grafana (admin/admin), folder ZAPPTTO, dashboard "ZAPPTTO Delivery Monitoring" |

To tear down without touching Exercise 7's `jenkins` container:

```bash
docker rm -f jenkins-ex6 delivery-metrics prometheus grafana
```

## Troubleshooting log

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`, with a Client section but no Server section | Three Docker installs in WSL: Snap Docker (failed), a native apt Docker Engine (inactive) and Docker Desktop's integration. A dead socket left by the first two blocked Docker Desktop. | `snap remove --purge docker`, `systemctl disable --now docker docker.socket`, delete `/var/run/docker.sock`, `wsl --shutdown`, restart Docker Desktop |
| Garbled terminal output after pasting many heredocs at once | The terminal redraws badly during a very large paste, and one failure hides the rest | Transfer files as one block with a checksum; check config with `promtool check config` |
| Jenkins rejects `admin` / `admin` | That is Grafana's default login. Jenkins uses the account created when `jenkins_home` was first set up. | Username from `ls /var/jenkins_home/users/`; with no user created, the password is in `secrets/initialAdminPassword` |
| No **Pipeline** option in New Item, and the existing job only had Build Steps / Post-build Actions | The Pipeline plugin was not installed, so the old job had been created as a Freestyle project, which cannot be converted | Installed `workflow-aggregator` and `pipeline-stage-view` with `jenkins-plugin-cli`, restarted, deleted the Freestyle job and recreated it as Pipeline |
| Build #1 failed: `Unknown SCENARIO=''` in the app logs, then `wget: bad address 'delivery-metrics:8000'` in the smoke test | On a new Pipeline job, parameters are only registered after the first run, so `SCENARIO` was empty and the app exited immediately | Used **Build with Parameters** from build #2 on. Hardening: add `SCENARIO = "${params.SCENARIO ?: 'normal'}"` to the `environment` block |
| Empty alert capture in the first attempt | Captured before the incident build had deployed | `capture-evidence.sh` checks which scenario is running before capturing, and polls until both alerts fire |

## Evidence

Produced by `capture-evidence.sh` in `evidence/`, one set per scenario:

| File | Contents |
|---|---|
| `containers-<scenario>.txt` | The running stack on the `monitoring` network |
| `metrics-<scenario>.txt` | The delivery metrics from `:8000/metrics` |
| `prometheus-targets-<scenario>.json` | Scrape-target health from the Prometheus API |
| `jenkins-console-<scenario>.txt` | Console log of the build that deployed that scenario |
| `alert-timeline-<scenario>.txt` | Alert states polled every 5s |
| `alerts-<scenario>.json` | Final alerts API response |

Screenshots in `evidence/screenshots/`:

| File | Shows |
|---|---|
| `prometheus-alerts-firing.png` | Both alerts firing during the incident |
| `prometheus-targets.png` | Both scrape targets UP |
| `grafana-dashboard-incident.png` | Dashboard during the incident, Firing Alerts = 2 |
| `jenkins-stage-view.png` | Pipeline stage view across builds |
