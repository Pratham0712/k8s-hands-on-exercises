# Exercise 8 — Jenkins Freestyle "Hello World" Job

## Goal
Create a Jenkins Freestyle job that clones a public GitHub repo and runs a shell
script, then prove Jenkins decides build status purely from the script's exit code.

## Setup
- Jenkins: Docker container `jenkins` (from Exercise 7), `http://localhost:8080`
- Source repo: https://github.com/Pratham0712/devops-sample-code (public, no credentials)
- Script: `hello-world.sh` → `echo "Hello, Jenkins!"`
- Push auth: fine-grained PAT scoped to that one repo, Contents: read/write

## Job configuration
| Setting | Value |
|---|---|
| Type | Freestyle project |
| SCM | Git, `https://github.com/Pratham0712/devops-sample-code.git` |
| Branch Specifier | `*/main` (default `*/master` fails) |
| Build step | Execute shell → `sh hello-world.sh` |

## Builds
| Build | Commit | Result | Evidence |
|---|---|---|---|
| #1 | Add hello-world.sh | ✅ SUCCESS | `build-1-success-output.txt` |
| #2 | Deliberately fail build (`exit 1`) | ❌ FAILURE | `build-2-failure-output.txt` |
| #3 | Revert of #2 | ✅ SUCCESS | `build-3-reverted-output.txt` |

Also: `workspace-listing.txt` (cloned workspace), `job-config.xml` (the job as Jenkins stores it).

## Gotchas found (not in the original guide)
1. **Branch name mismatch** — plain `git init` creates `master`, but the guide pushes `main`
   → `src refspec main does not match any`. Fix: `git init -b main`.
2. **Branch Specifier defaults to `*/master`** → `Couldn't find any revision to build`. Fix: `*/main`.
3. **Don't initialise the GitHub repo with a README** → unrelated histories, push rejected.

## Key learnings
- Execute shell runs as `/bin/sh -xe`: `-x` prints each command (`+` lines), `-e` aborts on first error.
- Build status = exit code. Build #2 still printed "Hello, Jenkins!" but failed because of `exit 1`.
- Jenkins checks out a specific commit SHA (detached HEAD) so the build is pinned to one exact commit.
- `git revert` (new undo commit) instead of `git reset` — never rewrite pushed history.
- HTTPS push auth relies on the PAT; the username field is effectively ignored.
- A Freestyle job is just `jobs/<name>/config.xml` + a workspace folder in `JENKINS_HOME`.
