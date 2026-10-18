# Exercise 7: Jenkins CI Server (Dockerized) + First Pipeline

## Goal
Run Jenkins in Docker, complete initial setup, and run a declarative pipeline
that checks out this repo, builds, and tests — then prove CI catches failures.

## What is CI?
Developers integrate changes into a shared repo frequently; every change triggers
an automated build and tests, giving fast feedback so bugs are caught early.

## Setup
```bash
docker volume create jenkins_home_ex7
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home_ex7:/var/jenkins_home -e JAVA_OPTS="-Xmx512m" \
  --restart unless-stopped jenkins/jenkins:lts
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

| Flag | Why |
|---|---|
| `-p 8080` | Web UI |
| `-p 50000` | Inbound build-agent port |
| `-v jenkins_home_ex7` | Persist jobs/plugins/users across container recreation |
| `JAVA_OPTS=-Xmx512m` | Cap JVM heap — WSL2 VM has ~3.7GB RAM |
| `--restart unless-stopped` | Survive Docker Desktop restarts |

## Pipeline (`Jenkinsfile`)
Checkout (HTTPS, public repo) → Build (`ls`) → Test (`test -f` exit code decides pass/fail) → post success/failure messages.

- Build #1: `Finished: SUCCESS` — see `pipeline-success-output.txt`
- Build #2: path changed to `exercise-99/README.md` → `Finished: FAILURE` — see `pipeline-failure-output.txt`

## Debugging log
1. **Docker socket missing** (`/var/run/docker.sock: no such file`): Docker Desktop
   WSL integration had dropped. Fixed by restarting Docker Desktop + re-enabling the integration.
2. **Container name conflict**: a leftover `jenkins` container from Exercise 6
   (custom `jenkins-docker` image). Renamed it to `jenkins-ex6` and set `--restart=no` instead of deleting it.
3. **Crash loop — `Permission denied` on `/var/jenkins_home`**: the new container reused
   Exercise 6's `jenkins_home` volume, which was root-owned. Stock Jenkins runs as UID 1000,
   so it couldn't write. Fixed with a dedicated volume `jenkins_home_ex7`.
   Lesson: UID mismatches on shared volumes are a common crash-loop cause; one volume per Jenkins instance.

## Production improvements
- GitHub webhook trigger instead of manual **Build Now**
- Jenkinsfile stored in the repo (Pipeline from SCM)
- Separate build agents; the controller shouldn't run builds
- Credentials for private repos via the Jenkins Credentials store

## Evidence
`run-output.txt`, `container-details.txt`, `pipeline-success-output.txt`,
`pipeline-failure-output.txt`, `Jenkinsfile`, screenshots
