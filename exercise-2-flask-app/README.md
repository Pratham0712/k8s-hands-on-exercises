# Exercise 2: Deploy a Flask App on Minikube

## What I did
- Built a custom Docker image for a simple Flask app
- Deployed it to Minikube via a Kubernetes Deployment (not a bare Pod)
- Exposed it externally using a NodePort Service
- Verified the app was reachable via `minikube service --url` + curl

## Key concepts learned
- **Deployment vs Pod**: A Deployment manages a ReplicaSet of Pods, giving self-healing/restart behavior that a bare Pod doesn't have.
- **Minikube's isolated Docker daemon**: `eval $(minikube docker-env)` points the local Docker CLI at Minikube's internal daemon, so images built locally are visible to the cluster.
- **imagePullPolicy: Never**: Required for locally-built images not pushed to any registry — tells Kubernetes to use the local image instead of trying (and failing) to pull from Docker Hub.
- **Service port vs targetPort**: `port` is what the Service exposes; `targetPort` is what the container listens on. Kubernetes maps external requests → Service → Pod.
- **Debugging DNS issues in Minikube's Docker daemon**: hit a `pip install` failure due to broken DNS inside build containers after a Docker Desktop restart — resolved with `minikube stop && minikube start` to reset networking.

## Files
- `app.py` — Flask application
- `Dockerfile` — image build definition
- `flask-deployment.yaml` — Deployment + NodePort Service
- `evidence-*.txt` — command outputs proving successful deployment

## Output
curl http://127.0.0.1:40445 > evidence-curl-output.txt
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    31  100    31    0     0   1476      0 --:--:-- --:--:-- --:--:--  1550
