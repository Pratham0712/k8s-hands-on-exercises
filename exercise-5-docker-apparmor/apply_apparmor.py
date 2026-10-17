import docker

PROFILE = "my-apparmor-profile"

client = docker.from_env()

# 1. Build the image and stream the build log
print("Building image...")
image, logs = client.images.build(path=".", tag="flask-apparmor", rm=True)
for chunk in logs:
    if "stream" in chunk:
        print(chunk["stream"], end="")

# 2. Run the container with the AppArmor profile
print("\nRunning container with AppArmor profile...")
container = client.containers.run(
    "flask-apparmor",
    ports={"5000/tcp": 5000},
    security_opt=[f"apparmor={PROFILE}"],
    detach=True,
)
print(f"Container started: {container.short_id}")

try:
    # 3. Verify. reload() refreshes attrs after the container has started.
    container.reload()
    requested = container.attrs["HostConfig"]["SecurityOpt"]  # just echoes our flag
    applied = container.attrs["AppArmorProfile"]              # what the daemon actually applied

    print(f"Requested (HostConfig.SecurityOpt): {requested}")
    print(f"Applied   (AppArmorProfile)       : {applied!r}")

    if applied == PROFILE:
        print("RESULT: profile is enforced")
    else:
        print("WARNING: profile NOT enforced (host AppArmor missing, or Docker ignored it)")
finally:
    # 4. Always clean up, so later runs don't collide on port 5000
    print("Stopping and removing the container...")
    container.stop(timeout=2)
    container.remove()
