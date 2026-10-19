# Exercise 9 — Jenkins Multi-Stage Pipeline (Python Flask)

## Objective
Build a declarative Jenkins Pipeline, loaded from SCM, that builds, tests, deploys, runs and
smoke-tests a Flask app, and that blocks deployment when tests fail.

## Setup
- Jenkins: Docker container `jenkins` (volume `jenkins_home_ex7`), on WSL2 + Docker Desktop
- Python 3.13 + `python3-venv` installed in the container (Debian, PEP 668 externally-managed)
- Source repo (what Jenkins builds): https://github.com/Pratham0712/devops-sample-code
- Job: `Python-MultiStage-Pipeline`, Definition = **Pipeline script from SCM**, branch `*/main`, Script Path `Jenkinsfile`
- Visualisation: Pipeline Graph View plugin (successor to the classic Stage View)

## Pipeline stages
| Stage | What it does | Why |
|---|---|---|
| Build | Create venv, `pip install -r requirements.txt`, `pip freeze` | Isolated, reproducible deps; system pip is blocked by PEP 668 |
| Test | `python -m unittest discover -v` | Unit test via Flask `test_client` (no server needed) |
| Deploy | Copy `app.py` + `requirements.txt` to `python-app-deploy/` | Mock deployment target |
| Run Application | Start app with `nohup ... &`, save PID via `$!` | Real running process |
| Smoke Test | `curl` http://127.0.0.1:5000/ with retries, assert exact response | Verifies the *deployed, running* app over HTTP |
| post/always | Kill app via saved PID | Cleanup; Jenkins' ProcessTreeKiller would kill it anyway |

## Fixes vs. the original handout
| Handout | Problem | Fix |
|---|---|---|
| `flask==2.1.2` | Unpinned Werkzeug resolves to 3.x, which removed `url_quote` → `ImportError` | `flask==3.1.1` (resolved Werkzeug 3.1.9) |
| Build stage only echoed | Relied on manual `apt install python3-flask` in the container | venv + `pip install -r requirements.txt` in the pipeline |
| `app.run(debug=True)` | Reloader forks a child, so the saved PID is the wrong process | `app.run(port=5000)` |
| "Test Application" re-ran `test_app.py` | Never touched the running server | HTTP smoke test with `curl` |

## Results
- **Build #1 — SUCCESS** (`build-success-output.txt`): all stages green; smoke test passed on attempt 1; app killed in post.
- **Build #2 — FAILURE, deliberate** (`build-failure-output.txt`): changed response to `Hello, BROKEN!`.
  Test stage failed with an AssertionError; Deploy, Run Application and Smoke Test were **skipped**;
  `post { always }` and `post { failure }` still ran. Proves the pipeline is a quality gate.
- **Build #3 — SUCCESS** after `git revert`.

## Learnings
- Each `sh` step is a new shell, so the venv must be re-activated per stage.
- `sh '''...'''` (single quotes) lets the shell, not Groovy, expand `$!` and `$(...)`.
- The workspace persists between builds: the venv was reused in build #2, which is fast but risks stale deps (fix: `cleanWs()` / `rm -rf venv`).
- Packages installed via `docker exec` live in the container layer, not the volume, and are lost on `docker rm`.
  Proper fix: custom image `FROM jenkins/jenkins:lts` with Python baked in.
- The Branch Specifier defaults to `*/master`; it must match the repo's `main`.

## Files
- `Jenkinsfile`: copy of the pipeline definition
- `build-success-output.txt`, `build-failure-output.txt`: console logs
- `pipeline-overview-success.png`, `pipeline-overview-failure.png`, `build-history.png`: screenshots
