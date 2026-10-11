# Exercise 4 — Docker Networking with Multiple Containers

## Objective
Connect a Flask API, MySQL, and Redis on a user-defined Docker bridge network and prove
that containers discover each other by name through Docker's embedded DNS.

## Architecture
        host (WSL2 / Docker Desktop)
               |  -p 5001:5001

## Steps
1. `docker network create --driver bridge my-bridge-net`
2. Build the Flask image: `docker build -t flask-api .`
3. Run containers on the network:
   - `docker run -d --name mysql --net my-bridge-net -e MYSQL_ROOT_PASSWORD=devpass mysql:8.4`
   - `docker run -d --name redis --net my-bridge-net redis:7-alpine`
   - `docker run -d --name flask --net my-bridge-net -p 5001:5001 flask-api`
4. Verify host → Flask (`curl localhost:5001/about`), then container → container by name.

## Results
| Test | Result | Evidence |
|---|---|---|
| Host → Flask via published port | JSON returned | `curl-about.txt` |
| Container IPs assigned in start order | .2 mysql, .3 redis, .4 flask | `container-ips.txt` |
| Resolver inside containers | `nameserver 127.0.0.11` | `resolv-conf.txt` |
| flask → mysql:3306, redis:6379 (TCP) | both OPEN | `port-check.txt` |
| ICMP by name on my-bridge-net | 0% loss | `ping-mysql.txt`, `ping-redis.txt` |
| ICMP by name on **default** bridge | `bad address 'mysql'` | `ping-default-bridge.txt` |

## Bugs fixed from the original exercise
1. **Flask bound to 127.0.0.1** → port publishing could not reach it. Fixed with `host="0.0.0.0"`.
2. **`Flask==2.0.1` + latest Werkzeug** → `ImportError: url_quote`. Upgraded to Flask 3.0.3 / Python 3.12.
3. **`mysql:latest` without `MYSQL_ROOT_PASSWORD`** → container exits on init, so no DNS entry exists. Added env var, pinned `mysql:8.4` LTS.
4. **No `ping` in `python:*-slim`** → used a throwaway `busybox` container for ICMP and a Python socket test for real port reachability.

## Key learnings
- **User-defined bridge = name-based discovery.** Docker runs an embedded DNS server (127.0.0.11) only on user-defined networks; the default `bridge` has none — proven by the failed ping.
- **`-p` is for host → container only.** Container-to-container traffic on the same network needs no published ports; MySQL/Redis stay unreachable from the host.
- **`EXPOSE` publishes nothing** — it is documentation; `-p` does the forwarding, and the app must listen on `0.0.0.0`.
- **"Running" ≠ "ready."** MySQL logged `ready for connections` twice: first a temporary init server on `port: 0` (networking disabled), then the real server on 3306. Production equivalents: Compose healthchecks, Kubernetes readiness probes.
- **Kubernetes parallel:** container names + embedded DNS ≈ Service names + CoreDNS from Exercises 1–2.

## Q&A
1. **`--net`** attaches a container to a named network at creation (default: `bridge`).
2. **Same-network communication:** by container name via embedded DNS, directly over the bridge subnet.
3. **Bridge vs host:** bridge = own network namespace + private IP behind NAT, ports must be published. Host = shares the host's network stack, no isolation, `-p` ignored.
4. **Expose to host:** `-p HOST:CONTAINER` (or `-P` for all `EXPOSE`d ports), with the app listening on `0.0.0.0`.
