<#
.SYNOPSIS
    Install or uninstall NetMeter as a Docker container on Windows.

.DESCRIPTION
    Pulls the NetMeter image from ghcr.io and runs it with Docker.
    Requires Docker Desktop to be installed and running.

.PARAMETER Action
    install   — Pull image and start the container.
    uninstall — Stop and remove the container.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File install-windows.ps1 install
    powershell -ExecutionPolicy Bypass -File install-windows.ps1 uninstall
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("install", "uninstall")]
    [string]$Action
)

$Image = "ghcr.io/petrmalina/netmeter:latest"
$ContainerName = "netmeter"

function Install-NetMeter {
    Write-Host "Installing NetMeter via Docker..." -ForegroundColor Cyan

    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        Write-Host "ERROR: Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
        exit 1
    }

    $existing = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
    if ($existing -eq $ContainerName) {
        Write-Host "Container already exists. Removing..." -ForegroundColor Yellow
        docker rm -f $ContainerName | Out-Null
    }

    Write-Host "Pulling image..." -ForegroundColor Gray
    docker pull $Image

    docker run -d `
        --name $ContainerName `
        --restart unless-stopped `
        --network host `
        -v netmeter-data:/app/data `
        -v netmeter-output:/app/output `
        $Image | Out-Null

    Write-Host "OK: NetMeter is running." -ForegroundColor Green
    Write-Host ""
    Write-Host "  Dashboard: http://localhost:8080"
    Write-Host "  Logs:      docker logs -f $ContainerName"
    Write-Host "  Update:    docker pull $Image && docker restart $ContainerName"
    Write-Host "  Uninstall: powershell -File $($MyInvocation.MyCommand.Path) uninstall"
}

function Uninstall-NetMeter {
    Write-Host "Uninstalling NetMeter..." -ForegroundColor Cyan

    $existing = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
    if ($existing -eq $ContainerName) {
        docker rm -f $ContainerName | Out-Null
        Write-Host "OK: Container removed." -ForegroundColor Green
    } else {
        Write-Host "Container '$ContainerName' not found." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Data volumes (netmeter-data, netmeter-output) were kept." -ForegroundColor Yellow
    Write-Host "  Remove them: docker volume rm netmeter-data netmeter-output"
}

switch ($Action) {
    "install"   { Install-NetMeter }
    "uninstall" { Uninstall-NetMeter }
}
