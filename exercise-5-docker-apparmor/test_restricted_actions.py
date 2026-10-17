import docker

client = docker.from_env()

# (name, command, expected exit code under the profile)
# Note: the exec deny applies to execs made BY a confined process.
# The command docker exec starts is itself launched by unconfined runc,
# so each exec test has a confined process attempt the exec.
TESTS = [
    ("Confinement label", ["python", "-c", "print(open('/proc/self/attr/current').read())"], 0),
    ("Read own app file", ["python", "-c", "open('/app/app.py').read(); print('ok')"],        0),
    ("Read /etc/passwd",  ["python", "-c", "open('/etc/passwd').read()"],                    1),
    ("Write /etc/x",      ["python", "-c", "open('/etc/x', 'w').write('x')"],                1),
    ("Python spawns bash",
        ["python", "-c", "import subprocess; subprocess.run(['/bin/bash', '-c', 'echo pwned'])"], 1),
    ("Bash execs id",     ["/bin/bash", "-c", "/usr/bin/id"],                                126),
]


def last_line(raw_bytes):
    lines = raw_bytes.decode(errors="replace").strip().splitlines()
    return lines[-1][:70] if lines else ""


def run_suite(label, security_opt):
    print(f"\n=== {label} ===")
    container = client.containers.run(
        "flask-apparmor",
        security_opt=security_opt,
        detach=True,
    )
    try:
        for name, cmd, expected in TESTS:
            exit_code, output = container.exec_run(cmd)
            status = "PASS" if exit_code == expected else "DIFF"
            print(
                f"[{status}] {name:<18} exit={exit_code:<4} "
                f"expected={expected:<4} {last_line(output)}"
            )
    finally:
        container.stop(timeout=2)
        container.remove()


run_suite("With my-apparmor-profile", ["apparmor=my-apparmor-profile"])
run_suite("Unconfined (control)", ["apparmor=unconfined"])
