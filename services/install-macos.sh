#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-install}"
IMAGE="ghcr.io/petrmalina/netmeter:latest"
CONTAINER_NAME="netmeter"
PLIST_NAME="com.netmeter"
PLIST_DEST="${HOME}/Library/LaunchAgents/${PLIST_NAME}.plist"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }

if [[ "$(uname -s)" != "Darwin" ]]; then
    err "This script is for macOS only."
    exit 1
fi

if ! command -v docker &>/dev/null; then
    err "Docker is required. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

install_service() {
    echo -e "${BOLD}Installing NetMeter via Docker...${NC}"

    docker pull "${IMAGE}"
    ok "Image pulled: ${IMAGE}"

    mkdir -p "$(dirname "${PLIST_DEST}")"

    cat > "${PLIST_DEST}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker</string>
        <string>run</string>
        <string>--rm</string>
        <string>--name</string>
        <string>${CONTAINER_NAME}</string>
        <string>--network</string>
        <string>host</string>
        <string>-v</string>
        <string>netmeter-data:/app/data</string>
        <string>-v</string>
        <string>netmeter-output:/app/output</string>
        <string>${IMAGE}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
PLIST

    launchctl load "${PLIST_DEST}"

    ok "Service installed and started."
    echo ""
    echo -e "  Dashboard: ${BOLD}http://localhost:8080${NC}"
    echo -e "  Logs:      ${BOLD}docker logs -f ${CONTAINER_NAME}${NC}"
    echo -e "  Uninstall: ${BOLD}bash $0 uninstall${NC}"
}

uninstall_service() {
    echo -e "${BOLD}Uninstalling NetMeter...${NC}"

    if launchctl list | grep -q "${PLIST_NAME}"; then
        launchctl unload "${PLIST_DEST}"
        ok "Service stopped."
    else
        warn "Service not currently loaded."
    fi

    if [[ -f "${PLIST_DEST}" ]]; then
        rm "${PLIST_DEST}"
        ok "Plist file removed."
    fi

    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true
    ok "Container removed."

    echo ""
    warn "Data volumes (netmeter-data, netmeter-output) were kept."
    echo -e "  Remove them: ${BOLD}docker volume rm netmeter-data netmeter-output${NC}"
    ok "NetMeter uninstalled."
}

case "${ACTION}" in
    install)   install_service ;;
    uninstall) uninstall_service ;;
    *)
        echo "Usage: bash $0 [install|uninstall]"
        exit 1
        ;;
esac
