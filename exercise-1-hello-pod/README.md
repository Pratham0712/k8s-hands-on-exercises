# Exercise 1: Hello Pod

## Goal
Deploy a containerized web app (nginx, simulating Zepto's storefront page) on Kubernetes 
using Minikube, and expose it so it's reachable from outside the cluster.

## What I did
1. Started a local single-node cluster: `minikube start --driver=docker`
2. Created a Pod running nginx: `kubectl run hello-k8s --image=nginx --port=80`
3. Verified it reached Running state: `kubectl get pods`
4. Exposed the Pod via a NodePort Service: `kubectl expose pod hello-k8s --type=NodePort --port=80`
5. Accessed it in-browser: `minikube service hello-k8s`

## What I learned
- A Pod is the smallest deployable unit — it wraps the container and gets a cluster-internal IP.
- A Service doesn't "know" a Pod directly — it finds it via label matching. The Service's 
  `selector: run=hello-k8s` matched the Pod's `label: run=hello-k8s`, and `kubectl describe svc` 
  confirmed this by showing the Service's Endpoint (`10.244.0.4:80`) was exactly the Pod's IP.
- NodePort opens a fixed port (here, `30395`) on the node so traffic can reach the Service from 
  outside the cluster.

## Evidence
- `pods-output.txt` — output of `kubectl get pods -o wide`
- `svc-output.txt` — output of `kubectl get svc -o wide`
- `pod-details.txt` — output of `kubectl describe pod hello-k8s`
- `svc-details.txt` — output of `kubectl describe svc hello-k8s`
