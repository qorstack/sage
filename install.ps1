# Knowlyx one-line installer (Windows PowerShell)
#   irm https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.ps1 | iex
#
# Or with workspace + Claude Code:
#   $env:KNOWLYX_WORKSPACE = "my-product"; $env:KNOWLYX_CLAUDE = "1"
#   irm https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$workspace = $env:KNOWLYX_WORKSPACE
$linkClaude = $env:KNOWLYX_CLAUDE -eq "1"
$repoPath = if ($env:KNOWLYX_REPO) { $env:KNOWLYX_REPO } else { (Get-Location).Path }

Write-Host "-> Knowlyx installer" -ForegroundColor Cyan

# 1. Ensure uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "-> Installing uv (https://astral.sh/uv)" -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

# 2. Install knowlyx
Write-Host "-> Installing knowlyx" -ForegroundColor Yellow
uv tool install knowlyx --upgrade

# 3. Smoke test
knowlyx --version

# 4. Optional workspace
if ($workspace) {
    $existing = knowlyx workspace list 2>$null
    if ($existing -notmatch $workspace) {
        Write-Host "-> Creating workspace '$workspace'" -ForegroundColor Yellow
        knowlyx workspace create $workspace
    }
    Write-Host "-> Linking $repoPath to '$workspace'" -ForegroundColor Yellow
    Push-Location $repoPath
    try { knowlyx init --link $workspace } finally { Pop-Location }
}

# 5. Optional Claude Code registration
if ($linkClaude) {
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        Write-Host "-> Registering MCP server with Claude Code" -ForegroundColor Yellow
        Push-Location $repoPath
        try { claude mcp add knowlyx -- uvx knowlyx mcp --repo . } finally { Pop-Location }
    } else {
        Write-Host "! claude CLI not found. Install Claude Code, then run:" -ForegroundColor DarkYellow
        Write-Host "  claude mcp add knowlyx -- uvx knowlyx mcp --repo ."
    }
}

Write-Host ""
Write-Host "Done. Try:" -ForegroundColor Green
Write-Host "  knowlyx scan ."
Write-Host "  knowlyx analyze 'add password reset' --repo ."
