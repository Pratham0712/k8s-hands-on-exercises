# Exercise 10: Multi-Node Cluster with Replicas and Pod Anti-Affinity

Two Flask services on a 3-node Minikube cluster (profile `devops-multinode`, Kubernetes v1.35.1, docker driver on WSL2):

| Service | Replicas | Spread rule |
|---|---|---|
| Product Catalog (`/products`) | 2 | required pod anti-affinity on `kubernetes.io/hostname` |
| Shopping Cart (`/cart` GET/POST) | 3 | required pod anti-affinity on `kubernetes.io/hostname` |

Both are exposed as NodePort Services.

## Image distribution in a multi-node cluster
`eval $(minikube docker-env)` only targets one node's daemon, so images were built on Docker Desktop and copied to every node with `minikube image load`. `imagePullPolicy: Never` makes every node use its local copy. Verified on all 3 nodes (same image IDs).

## Fixes to the original guide
1. Shopping-cart Deployment used `namespace: devops-exercise` while its Service was in `default`, so the Service would select no pods. Unified to `default`.
2. Dropped `--force` (only needed when running as root).
3. Skipped the registry addon: unused when images are loaded directly and pulled with `Never`.
4. Image verification now checks every node with `minikube ssh -n <node>`, not just the control plane.
5. `python:3.9-slim` (end of life Oct 2025) replaced by `python:3.12-slim`; `pip install` moved before `COPY` so the dependency layer is cached.
6. Cluster sized for a ~3.7GB WSL2 VM: `--memory=1800` per node as a cgroup ceiling (actual idle usage: ~890MB control plane, ~300MB per worker).

## Results
- **Spread** (`pods-distribution.txt`): 3 cart pods on 3 distinct nodes, 2 catalog pods on 2 distinct nodes.
- **Services** (`services-output.txt`): catalog Service has 2 endpoints, cart Service has 3.
- **Catalog API** (`products-output.txt`): returns the 3-product list.

### Finding: in-memory state breaks with replicas (`curl-output.txt`)
The cart is a Python list held in each pod's memory. The single POST landed on pod `nhrhl`. Of the 8 GETs that followed, the 2 routed to `nhrhl` returned the Laptop and the 6 routed to the other two pods returned `[]`; the per-pod logs confirm this request by request. kube-proxy (iptables mode) picks a backend at random, so a stateful service cannot be scaled by adding replicas. The state must move to shared storage (e.g. Redis or a database).

The logs also show NodePort SNAT. Pods on other nodes saw the client as `192.168.49.2` (control-plane node IP, leaving via eth0); the pod on the same node saw `10.244.0.1` (the local pod-bridge gateway). The real client IP is lost unless `externalTrafficPolicy: Local` is set.

(Note: the `/products` line in `curl-output.txt` failed because that tunnel had exited; the product check was re-run into `products-output.txt`.)

### Node-failure simulation (`drain-test.txt`)
`kubectl drain devops-multinode-m03` evicted one pod of each service:
- **Product Catalog** rescheduled to the free control-plane node and stayed at 2/2 (replicas < nodes, so there was a spare node).
- **Shopping Cart** replacement stayed **Pending**: `0/3 nodes are available: 1 node(s) were unschedulable, 2 node(s) didn't match pod anti-affinity rules`. With replicas == nodes and a *required* rule, losing a node means running at 2/3.
- After `kubectl uncordon`, the Pending pod scheduled onto m03 immediately. The catalog pod did **not** move back: Kubernetes never rebalances running pods (that is the descheduler's job).

## Takeaways
- `requiredDuringScheduling` anti-affinity guarantees spread but trades away capacity under failure. `preferredDuringScheduling`, or `topologySpreadConstraints` with `whenUnsatisfiable: ScheduleAnyway`, keep the replica count by allowing pods to double up.
- Keep replicas below the number of failure domains if a replacement must always find a home.
- Pod IPs change on every reschedule; clients depend on Services.
- `minikube service` tunnels on the docker driver are SSH port-forwards that live only as long as their terminal.

## Files
| File | Contents |
|---|---|
| `product_catalog.py`, `shopping_cart.py` | Flask apps |
| `Dockerfile.product`, `Dockerfile.shopping` | Images |
| `*_deployment.yaml`, `*_service.yaml` | Kubernetes manifests |
| `nodes-output.txt` | 3 Ready nodes |
| `pods-distribution.txt` | Pod-to-node placement |
| `services-output.txt` | Services and endpoints |
| `products-output.txt`, `curl-output.txt` | API tests and per-pod logs |
| `drain-test.txt` | Drain, Pending pod events, uncordon recovery |
