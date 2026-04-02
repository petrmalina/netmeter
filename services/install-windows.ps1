<#
.SYNOPSIS
    Install or uninstall NetMeter as a Docker container on Windows.

.DESCRIPTION
    Pulls the NetMeter image from ghcr.io and runs it with Docker Desktop.
    Performs pre-flight checks and provides descriptive error messages.

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
$RepoUrl = "https://github.com/petrmalina/netmeter"
$PackageUrl = "$RepoUrl/pkgs/container/netmeter"

function Write-OK   { param($Msg) Write-Host "  OK " -ForegroundColor Green -NoNewline; Write-Host $Msg }
function Write-Err  { param($Msg) Write-Host "  ERR " -ForegroundColor Red -NoNewline; Write-Host $Msg }
function Write-Warn { param($Msg) Write-Host "  WARN " -ForegroundColor Yellow -NoNewline; Write-Host $Msg }
function Write-Info { param($Msg) Write-Host "     -> $Msg" }

function Test-Preflight {
    $failed = $false

    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        Write-Err "Docker is not installed."
        Write-Info "Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
        return $false
    }

    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Docker Desktop is not running."
        Write-Info "Start Docker Desktop from the Start menu and wait for it to be ready."
        if ($dockerInfo -match "pipe") {
            Write-Info "The Docker engine is not responding — ensure Docker Desktop has finished starting."
        }
        return $false
    }

    $manifest = docker manifest inspect $Image 2>&1
    if ($LASTEXITCODE -ne 0) {
        $reachable = $false
        try {
            $response = Invoke-WebRequest -Uri "https://ghcr.io/v2/" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            $reachable = $true
        } catch {}

        if (-not $reachable) {
            Write-Err "Cannot reach ghcr.io — check your internet connection."
        } else {
            Write-Err "Docker image '$Image' not found on ghcr.io."
            Write-Info "The image may not be published yet."
            Write-Info "Check: $PackageUrl"
            Write-Info "Or build locally: docker build -t $Image ."
        }
        $failed = $true
    }

    if ($failed) { return $false }

    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Warn "Not running as Administrator — this may cause issues with host networking."
        Write-Info "Re-run: powershell -ExecutionPolicy Bypass -RunAs -File $($MyInvocation.ScriptName) $Action"
    }

    return $true
}

function Pull-Image {
    Write-Host "Pulling $Image..." -ForegroundColor Gray
    $output = docker pull $Image 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to pull Docker image."
        if ($output -match "denied") {
            Write-Info "Access denied — the image may be private."
            Write-Info "Make it public: GitHub Settings -> Packages -> netmeter -> Visibility."
        } elseif ($output -match "not found") {
            Write-Info "Image tag not found."
            Write-Info "Check available tags: $PackageUrl"
        } elseif ($output -match "timeout|connection") {
            Write-Info "Network error — check your internet connection and DNS."
        } else {
            Write-Info "Docker output: $output"
        }
        return $false
    }
    Write-OK "Image pulled: $Image"
    return $true
}

function Install-NetMeter {
    Write-Host ""
    Write-Host "Installing NetMeter..." -ForegroundColor Cyan
    Write-Host ""

    if (-not (Test-Preflight)) { exit 1 }
    if (-not (Pull-Image)) { exit 1 }

    $existing = docker ps -a --filter "name=^${ContainerName}$" --format "{{.Names}}" 2>$null
    if ($existing -eq $ContainerName) {
        Write-Warn "Container already exists — removing for reinstall."
        docker rm -f $ContainerName | Out-Null
    }

    $runOutput = docker run -d `
        --name $ContainerName `
        --restart unless-stopped `
        --network host `
        -v netmeter-data:/app/data `
        -v netmeter-output:/app/output `
        $Image 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to start container."
        Write-Info "Docker output: $runOutput"
        Write-Info "Try running manually: docker run --rm --network host $Image"
        exit 1
    }

    Start-Sleep -Seconds 2
    $running = docker ps --filter "name=^${ContainerName}$" --format "{{.Status}}" 2>$null
    if ($running) {
        Write-OK "NetMeter is running."
    } else {
        Write-Warn "Container started but may have exited."
        Write-Info "Check: docker logs $ContainerName"
    }

    Write-Host ""
    Write-Host "  Dashboard  http://localhost:8080"
    Write-Host "  Logs       docker logs -f $ContainerName"
    Write-Host "  Update     docker pull $Image; docker restart $ContainerName"
    Write-Host "  Uninstall  powershell -File $($MyInvocation.MyCommand.Path) uninstall"
}

function Uninstall-NetMeter {
    Write-Host ""
    Write-Host "Uninstalling NetMeter..." -ForegroundColor Cyan
    Write-Host ""

    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        Write-Err "Docker not found — nothing to uninstall."
        exit 0
    }

    $existing = docker ps -a --filter "name=^${ContainerName}$" --format "{{.Names}}" 2>$null
    if ($existing -eq $ContainerName) {
        docker rm -f $ContainerName | Out-Null
        Write-OK "Container removed."
    } else {
        Write-Warn "Container '$ContainerName' not found — already removed."
    }

    Write-Host ""
    Write-Warn "Data volumes were kept."
    Write-Info "Remove data:  docker volume rm netmeter-data netmeter-output"
    Write-Info "Remove image: docker rmi $Image"
    Write-OK "Done."
}

switch ($Action) {
    "install"   { Install-NetMeter }
    "uninstall" { Uninstall-NetMeter }
}
