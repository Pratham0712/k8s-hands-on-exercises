# Exercise 5: Docker Security with AppArmor + Docker SDK for Python

Confine a Flask container with a custom AppArmor profile, apply it with the Docker CLI and the Python Docker SDK, and prove enforcement with restricted-action tests against an unconfined control.

## Environment
- Windows + WSL2 (Ubuntu 24.04), kernel `6.18.x-microsoft-standard-WSL2`
- AppArmor enabled in the WSL kernel via `.wslconfig`: `kernelCommandLine = apparmor=1 security=apparmor`
- **Native Docker Engine inside Ubuntu** (Docker Desktop integration disabled for this exercise; see Findings)
- Image: `python:3.12-slim` + Flask 3.x · Docker SDK for Python 7.x

## Files
| File | Purpose |
|---|---|
| `app.py` | Minimal Flask app |
| `Dockerfile` | Builds `flask-apparmor` |
| `my-apparmor-profile` | Custom AppArmor profile (loaded into `/etc/apparmor.d/`) |
| `apply_apparmor.py` | Builds and runs the container via the SDK, verifies the profile *actually applied* |
| `test_restricted_actions.py` | 6 restricted-action tests, confined vs `apparmor=unconfined` control |
| `aa-status-output.txt` | Profile loaded in the kernel |
| `native-engine-enforces-apparmor.txt` | Native engine refuses a nonexistent profile |
| `apply-output.txt` | SDK run: requested vs applied profile |
| `restricted-actions-output.txt` | Test results |

## Profile design
- Named profile (`profile my-apparmor-profile`): Docker resolves `--security-opt apparmor=<name>` by **name**
- `flags=(attach_disconnected,mediate_deleted)`: container paths appear disconnected from the host's view of the filesystem
- Allowlist baseline (`file,`, `capability,`, `network inet/inet6 stream`), then targeted `deny` rules (deny always wins):
  - read: `/etc/{passwd,shadow,gshadow,group}` · write: `/etc/**` · read/write: `/var/**`
  - exec: `/{,usr/}{,s}bin/**` (Python lives in `/usr/local/bin`, so it's unaffected)
  - `capability sys_admin`, `mount`, writes to `/proc/sys/kernel/**`
- `signal (receive) peer=unconfined` so `docker stop` can deliver SIGTERM

## Results
| Test | Confined | Unconfined control |
|---|---|---|
| Confinement label | `my-apparmor-profile (enforce)` | `unconfined` |
| Read own app file | ✅ allowed | allowed |
| Read `/etc/passwd` | ❌ EACCES (exit 1) | allowed |
| Write `/etc/x` | ❌ EACCES (exit 1) | allowed |
| Python spawns bash (simulated RCE) | ❌ EACCES (exit 1) | `pwned` |
| Bash execs `/usr/bin/id` | ❌ exit 126 | `uid=0(root)` |

## Findings (bugs in the original exercise and environment traps)
1. **Docker Desktop silently ignored the profile.** It advertised `name=apparmor` in `docker info`, yet a container started with `--security-opt apparmor=my-apparmor-profile` reported `unconfined`, with no error. Its engine runs in a separate distro and never sees profiles loaded from Ubuntu. The native engine instead **refuses to start** a container whose profile doesn't exist (the correct, fail-closed behaviour).
2. **`HostConfig.SecurityOpt` is not verification.** It echoes the requested flag. The applied profile is in the container's top-level `AppArmorProfile` field, or inside the container in `/proc/self/attr/current`.
3. **Path-attached header** (`/usr/bin/python3 { ... }`) names the profile `/usr/bin/python3`, so `apparmor=my-apparmor-profile` can't resolve. A named profile is required.
4. **Allowlist without a baseline** blocks Python from loading its own libraries, so the container can't start.
5. **Exec denials apply to execs made BY a confined process.** `docker exec <ctr> /bin/bash -c 'echo pwned'` succeeds because unconfined `runc` performs that exec, and bash only becomes confined once it's running. The meaningful test is a confined process (e.g. the Python app after an RCE) trying to launch a shell, and that is blocked.
6. `cat /etc/passwd` can't test the read rule: `cat` is in `/usr/bin` and is blocked from executing first. The read is tested with Python instead.
7. `python:3.8` has been EOL since Oct 2024, so this exercise uses `python:3.12-slim`.

## Exercise questions
1. **Purpose:** Mandatory access control around the container process. Even root inside the container is bound by kernel-enforced rules, which adds defense-in-depth beyond namespaces, cgroups and seccomp.
2. **How profiles secure it:** They restrict file paths (r/w/x per path), capabilities, network families, mounts, signals and ptrace. Deny rules override any allow.
3. **Why `/etc` and `/var`:** Account databases, credentials, configuration, logs and runtime state live there. Blocking reads stops reconnaissance; blocking writes stops persistence and tampering.
4. **Other restrictions:** Capabilities (`sys_admin`, `sys_module`, `net_raw`), `mount`/`umount`/`pivot_root`, ptrace, signals, raw sockets, `/proc` and `/sys` writes, execution of specific binaries.
5. **Verification:** `docker inspect --format '{{.AppArmorProfile}}' <ctr>`, the SDK's `container.attrs["AppArmorProfile"]`, `/proc/self/attr/current` inside the container, `aa-status` on the host, plus a control run with `apparmor=unconfined` to prove the profile causes the denials.

## Run it
```bash
sudo mount -t securityfs securityfs /sys/kernel/security 2>/dev/null
sudo cp my-apparmor-profile /etc/apparmor.d/
sudo apparmor_parser -r -W /etc/apparmor.d/my-apparmor-profile
python3 -m venv .venv && source .venv/bin/activate && pip install docker
python apply_apparmor.py
python test_restricted_actions.py
```
