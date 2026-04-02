#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-install}"
IMAGE="ghcr.io/petrmalina/netmeter:latest"
SERVICE_NAME="netmeter"
CONTAINER_NAME="netmeter"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_DIR="/etc/netmeter"
ENV_FILE="${ENV_DIR}/env"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
info() { echo -e "  ${BOLD}→${NC} $*"; }

preflight_checks() {
    local failed=0

    if [[ "$(uname -s)" != "Linux" ]]; then
        err "This installer requires Linux with systemd."
        info "On macOS use: bash services/install-macos.sh install"
        info "On Windows use: powershell services/install-windows.ps1 install"
        exit 1
    fi

    if [[ $EUID -ne 0 ]]; then
        err "This script must be run as root."
        info "Run: sudo bash $0 ${ACTION}"
        exit 1
    fi

    if ! command -v systemctl &>/dev/null; then
        err "systemctl not found — systemd is required."
        exit 1
    fi

    if ! command -v docker &>/dev/null; then
        err "Docker is not installed."
        info "Install Docker Engine: https://docs.docker.com/engine/install/"
        exit 1
    fi

    if ! docker info &>/dev/null; then
        err "Docker daemon is not running."
        info "Start it with: sudo systemctl start docker"
        exit 1
    fi

    if ! docker manifest inspect "${IMAGE}" &>/dev/null 2>&1; then
        if ! curl -sf "https://ghcr.io/v2/petrmalina/netmeter/tags/list" &>/dev/null; then
            err "Cannot reach ghcr.io — check your internet connection."
            ((failed++))
        else
            err "Docker image '${IMAGE}' not found on ghcr.io."
            info "The image may not be published yet."
            info "Check: https://github.com/petrmalina/netmeter/pkgs/container/netmeter"
            info "Or build locally: docker build -t ${IMAGE} ."
            ((failed++))
        fi
    fi

    if [[ ${failed} -gt 0 ]]; then
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
            info "If this is your image, make the package public in GitHub Settings → Packages."
        elif echo "${output}" | grep -qi "not found"; then
            info "Image tag not found. Available tags:"
            info "https://github.com/petrmalina/netmeter/pkgs/container/netmeter"
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

    if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
        warn "Service already running — stopping for reinstall."
        systemctl stop "${SERVICE_NAME}"
    fi

    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

    mkdir -p "${ENV_DIR}"
    if [[ ! -f "${ENV_FILE}" ]]; then
        if [[ -f "${SCRIPT_DIR}/../.env.example" ]]; then
            cp "${SCRIPT_DIR}/../.env.example" "${ENV_FILE}"
        else
            cat > "${ENV_FILE}" <<'ENVFILE'
NETMETER_INTERVAL=600
NETMETER_LOG_LEVEL=INFO
NETMETER_DASHBOARD_PORT=8080
ENVFILE
        fi
        ok "Config created at ${ENV_FILE} — edit as needed."
    else
        ok "Config exists at ${ENV_FILE}."
    fi

    if [[ ! -f "${SCRIPT_DIR}/netmeter.service" ]]; then
        err "Service unit file not found at ${SCRIPT_DIR}/netmeter.service"
        info "Re-clone the repository: git clone https://github.com/petrmalina/netmeter.git"
        exit 1
    fi
    cp "${SCRIPT_DIR}/netmeter.service" "${SERVICE_FILE}"

    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}" --quiet
    systemctl start "${SERVICE_NAME}"

    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        ok "Service installed and running."
    else
        err "Service installed but failed to start."
        info "Check logs: journalctl -u ${SERVICE_NAME} --no-pager -n 20"
        exit 1
    fi

    echo ""
    echo -e "  ${BOLD}Dashboard${NC}  http://localhost:8080"
    echo -e "  ${BOLD}Config${NC}     ${ENV_FILE}"
    echo -e "  ${BOLD}Status${NC}     systemctl status ${SERVICE_NAME}"
    echo -e "  ${BOLD}Logs${NC}       journalctl -u ${SERVICE_NAME} -f"
    echo -e "  ${BOLD}Update${NC}     sudo systemctl restart ${SERVICE_NAME}"
    echo -e "  ${BOLD}Uninstall${NC}  sudo bash $0 uninstall"
}

uninstall_service() {
    echo -e "${BOLD}Uninstalling NetMeter...${NC}"
    echo ""

    if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
        systemctl stop "${SERVICE_NAME}"
        ok "Service stopped."
    fi

    if systemctl is-enabled --quiet "${SERVICE_NAME}" 2>/dev/null; then
        systemctl disable "${SERVICE_NAME}" --quiet
        ok "Service disabled."
    fi

    if [[ -f "${SERVICE_FILE}" ]]; then
        rm "${SERVICE_FILE}"
        systemctl daemon-reload
        ok "Service file removed."
    fi

    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker rm -f "${CONTAINER_NAME}" >/dev/null
        ok "Container removed."
    fi

    echo ""
    warn "Data volumes and config were kept."
    info "Remove data:   docker volume rm netmeter-data netmeter-output"
    info "Remove config: rm -rf ${ENV_DIR}"
    info "Remove image:  docker rmi ${IMAGE}"
    ok "Done."
}

case "${ACTION}" in
    install)   install_service ;;
    uninstall) uninstall_service ;;
    *)
        echo -e "${BOLD}NetMeter — Service Installer (Linux/systemd)${NC}"
        echo ""
        echo "Usage: sudo bash $0 [install|uninstall]"
        echo ""
        echo "  install    Pull Docker image and register systemd service"
        echo "  uninstall  Stop service and remove systemd unit"
        exit 1
        ;;
esac
