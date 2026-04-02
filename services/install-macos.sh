#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-install}"
IMAGE="ghcr.io/petrmalina/netmeter:latest"
CONTAINER_NAME="netmeter"
PLIST_NAME="com.netmeter"
PLIST_DEST="${HOME}/Library/LaunchAgents/${PLIST_NAME}.plist"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
info() { echo -e "  ${BOLD}→${NC} $*"; }

preflight_checks() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        err "This installer requires macOS."
        info "On Linux use: sudo bash services/install-systemd.sh install"
        info "On Windows use: powershell services/install-windows.ps1 install"
        exit 1
    fi

    if ! command -v docker &>/dev/null; then
        err "Docker is not installed."
        info "Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
        exit 1
    fi

    if ! docker info &>/dev/null 2>&1; then
        err "Docker Desktop is not running."
        info "Open Docker Desktop from Applications and wait for it to start."
        exit 1
    fi

    local docker_path
    docker_path=$(command -v docker)
    if [[ "${docker_path}" != "/usr/local/bin/docker" && "${docker_path}" != "/opt/homebrew/bin/docker" ]]; then
        warn "Docker found at ${docker_path} — launchd plist will use this path."
    fi

    if ! docker manifest inspect "${IMAGE}" &>/dev/null 2>&1; then
        if ! curl -sf "https://ghcr.io/v2/petrmalina/netmeter/tags/list" &>/dev/null; then
            err "Cannot reach ghcr.io — check your internet connection."
        else
            err "Docker image '${IMAGE}' not found on ghcr.io."
            info "The image may not be published yet."
            info "Check: https://github.com/petrmalina/netmeter/pkgs/container/netmeter"
            info "Or build locally: docker build -t ${IMAGE} ."
        fi
        exit 1
    fi
}

pull_image() {
    echo -e "Pulling ${BOLD}${IMAGE}${NC}..."
    if ! docker pull "${IMAGE}" 2>&1; then
        err "Failed to pull Docker image."
        local output
        output=$(docker pull "${IMAGE}" 2>&1 || true)
        if echo "${output}" | grep -qi "denied"; then
            info "Access denied — the image may be private."
            info "Make the package public: GitHub Settings → Packages → netmeter → Visibility."
        elif echo "${output}" | grep -qi "not found"; then
            info "Image tag not found."
            info "Check available tags: https://github.com/petrmalina/netmeter/pkgs/container/netmeter"
        elif echo "${output}" | grep -qi "timeout\|connection"; then
            info "Network error — check your internet connection and DNS."
        fi
        exit 1
    fi
    ok "Image pulled: ${IMAGE}"
}

install_service() {
    echo -e "${BOLD}Installing NetMeter...${NC}"
    echo ""

    preflight_checks
    pull_image

    if launchctl list 2>/dev/null | grep -q "${PLIST_NAME}"; then
        warn "Service already loaded — unloading for reinstall."
        launchctl unload "${PLIST_DEST}" 2>/dev/null || true
    fi

    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

    local docker_path
    docker_path=$(command -v docker)

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
        <string>${docker_path}</string>
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
    ok "Plist created at ${PLIST_DEST}"

    launchctl load "${PLIST_DEST}"

    sleep 2
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        ok "Service installed and running."
    else
        warn "Service loaded but container may still be starting."
        info "Check: docker ps | grep ${CONTAINER_NAME}"
    fi

    echo ""
    echo -e "  ${BOLD}Dashboard${NC}  http://localhost:9280"
    echo -e "  ${BOLD}Logs${NC}       docker logs -f ${CONTAINER_NAME}"
    echo -e "  ${BOLD}Update${NC}     docker pull ${IMAGE} && launchctl unload ${PLIST_DEST} && launchctl load ${PLIST_DEST}"
    echo -e "  ${BOLD}Uninstall${NC}  bash $0 uninstall"
}

uninstall_service() {
    echo -e "${BOLD}Uninstalling NetMeter...${NC}"
    echo ""

    if launchctl list 2>/dev/null | grep -q "${PLIST_NAME}"; then
        launchctl unload "${PLIST_DEST}" 2>/dev/null || true
        ok "Service unloaded."
    fi

    if [[ -f "${PLIST_DEST}" ]]; then
        rm "${PLIST_DEST}"
        ok "Plist removed."
    fi

    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
        docker rm -f "${CONTAINER_NAME}" >/dev/null
        ok "Container removed."
    fi

    echo ""
    warn "Data volumes were kept."
    info "Remove data:  docker volume rm netmeter-data netmeter-output"
    info "Remove image: docker rmi ${IMAGE}"
    ok "Done."
}

case "${ACTION}" in
    install)   install_service ;;
    uninstall) uninstall_service ;;
    *)
        echo -e "${BOLD}NetMeter — Service Installer (macOS/launchd)${NC}"
        echo ""
        echo "Usage: bash $0 [install|uninstall]"
        echo ""
        echo "  install    Pull Docker image and register launchd service"
        echo "  uninstall  Stop service and remove launchd plist"
        exit 1
        ;;
esac
