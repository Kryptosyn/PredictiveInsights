#!/bin/bash
set -e

echo "Starting user initialization..."

# Get the GID of the coder group (usually 1000)
CODER_GID=$(id -g coder 2>/dev/null || echo 1000)

# Split USER_LIST by comma
if [ -n "$USER_LIST" ]; then
  IFS=',' read -ra ADDR <<< "$USER_LIST"
  for u in "${ADDR[@]}"; do
    if ! id "$u" &>/dev/null; then
      echo "Creating Linux user: $u"
      useradd -m -s /bin/bash -G coder "$u"
      echo "$u:CiscoLab2026!" | chpasswd
    else
      echo "User $u already exists"
      usermod -aG coder "$u"
    fi
  done
fi

# Ensure the parent directory is traversable
chmod 755 /home/coder

# Ensure the project directory is accessible to all lab users
if [ -d "/home/coder/project" ]; then
  # Use find to change permissions but avoid .git internals if they cause issues
  # Actually, 777 on everything in project (except maybe .git) is fine for a lab
  find /home/coder/project -maxdepth 2 -not -path '*/.*' -exec chmod 777 {} +
  chmod 777 /home/coder/project/*.py || true
fi

echo "User initialization complete. Handing over to code-server..."

# Execute the command passed as arguments (usually the original entrypoint)
exec "$@"
