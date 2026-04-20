#!/usr/bin/env bash
# Install Docker Engine inside WSL2 Ubuntu (Windows 11 Home).
# This only needs to be run once per machine. Docker persists across reboots.
#
# Run from a WSL terminal (not Git Bash — sudo needs a TTY for the password):
#   wsl -d Ubuntu
#   bash /mnt/c/Git/CLISpecBench/scripts/install-docker-wsl.sh
#
# After the script finishes, run the post-install steps printed at the end.
set -euo pipefail

echo "=== Installing Docker Engine in WSL2 Ubuntu ==="

sudo apt-get update
sudo apt-get install -y ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin

# Add current user to docker group so sudo isn't needed for docker commands.
# This is required for the harness to call docker from Git Bash via
# "wsl -d Ubuntu -- docker ..." without interactive sudo.
sudo usermod -aG docker "$USER"

# Configure Docker to also listen on TCP so the Python harness (running on
# Windows) can connect via tcp://localhost:2375. The Unix socket is kept for
# local WSL usage (e.g. smoke test scripts).
sudo mkdir -p /etc/docker
if [ ! -f /etc/docker/daemon.json ] || ! grep -q '"hosts"' /etc/docker/daemon.json; then
    echo '{"hosts": ["unix:///var/run/docker.sock", "tcp://127.0.0.1:2375"]}' | sudo tee /etc/docker/daemon.json > /dev/null
    echo "Configured Docker to listen on TCP 127.0.0.1:2375"
fi

# Docker's systemd unit file passes -H fd:// by default, which conflicts with
# the "hosts" key in daemon.json. Create a systemd override that clears the
# default ExecStart so daemon.json controls the listen addresses.
OVERRIDE_DIR="/etc/systemd/system/docker.service.d"
if [ ! -f "$OVERRIDE_DIR/override.conf" ]; then
    sudo mkdir -p "$OVERRIDE_DIR"
    printf '[Service]\nExecStart=\nExecStart=/usr/bin/dockerd\n' | sudo tee "$OVERRIDE_DIR/override.conf" > /dev/null
    sudo systemctl daemon-reload
    echo "Created systemd override to let daemon.json control Docker hosts"
fi

sudo service docker start

echo "=== Verifying (with sudo, group change takes effect after restart) ==="
sudo docker run --rm hello-world

echo ""
echo "=== Done. Post-install steps: ==="
echo "1. Exit WSL:  exit"
echo "2. Restart WSL so the docker group takes effect:  wsl --shutdown"
echo "3. Verify docker works without sudo:"
echo "     wsl -d Ubuntu -- docker run --rm hello-world"
