#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-install}"
IMAGE="ghcr.io/petrmalina/netmeter:latest"
SERVICE_NAME="netmeter"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_DIR="/etc/netmeter"
ENV_FILE="${ENV_DIR}/env"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }

if [[ "$(uname -s)" != "Linux" ]]; then
    err "systemd is only available on Linux."
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root (use sudo)."
    exit 1
fi

if ! command -v docker &>/dev/null; then
    err "Docker is required. Install it first: https://docs.docker.com/engine/install/"
    exit 1
fi

install_service() {
    echo -e "${BOLD}Installing NetMeter systemd service...${NC}"

    docker pull "${IMAGE}"
    ok "Image pulled: ${IMAGE}"

    mkdir -p "${ENV_DIR}"
    if [[ ! -f "${ENV_FILE}" ]]; then
        cp "${SCRIPT_DIR}/../.env.example" "${ENV_FILE}"
        ok "Default config created at ${ENV_FILE} — edit as needed."
    else
        warn "Config already exists at ${ENV_FILE}, skipping."
    fi

    cp "${SCRIPT_DIR}/netmeter.service" "${SERVICE_FILE}"

    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}"
    systemctl start "${SERVICE_NAME}"

    ok "Service installed and started."
    echo ""
    echo -e "  Dashboard: ${BOLD}http://localhost:8080${NC}"
    echo -e "  Config:    ${BOLD}${ENV_FILE}${NC}"
    echo -e "  Status:    ${BOLD}systemctl status ${SERVICE_NAME}${NC}"
    echo -e "  Logs:      ${BOLD}journalctl -u ${SERVICE_NAME} -f${NC}"
    echo -e "  Update:    ${BOLD}sudo systemctl restart ${SERVICE_NAME}${NC}"
    echo -e "  Uninstall: ${BOLD}sudo bash $0 uninstall${NC}"
}

uninstall_service() {
    echo -e "${BOLD}Uninstalling NetMeter systemd service...${NC}"

    if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
        systemctl stop "${SERVICE_NAME}"
        ok "Service stopped."
    fi

    if systemctl is-enabled --quiet "${SERVICE_NAME}" 2>/dev/null; then
        systemctl disable "${SERVICE_NAME}"
        ok "Service disabled."
    fi

    if [[ -f "${SERVICE_FILE}" ]]; then
        rm "${SERVICE_FILE}"
        systemctl daemon-reload
        ok "Service file removed."
    fi

    docker rm -f netmeter 2>/dev/null || true
    ok "Container removed."

    echo ""
    warn "Data volumes (netmeter-data, netmeter-output) were kept."
    echo -e "  Remove them: ${BOLD}docker volume rm netmeter-data netmeter-output${NC}"
    echo -e "  Remove config: ${BOLD}rm -rf ${ENV_DIR}${NC}"
    ok "NetMeter service uninstalled."
}

case "${ACTION}" in
    install)   install_service ;;
    uninstall) uninstall_service ;;
    *)
        echo "Usage: sudo bash $0 [install|uninstall]"
        exit 1
        ;;
esac
