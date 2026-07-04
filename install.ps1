# Sage installer — one command, any repo. Sets up (or updates) Sage:
#   irm https://raw.githubusercontent.com/qorstack/sage/main/install.ps1 | iex
#
# It asks which AI tools to wire up (multi-select), fetches the protocol +
# commands, and drops the matching thin adapters. It NEVER touches your own
# knowledge under agents/sage/<domain>/ — only Sage's own system files.
#
# Non-interactive? Set $env:SAGE_TOOLS first, e.g.
#   $env:SAGE_TOOLS='claude,cursor'; irm .../install.ps1 | iex   (or 'all')

# Wrapped in & { } so nothing leaks into your shell when piped through iex.
& {
  $ErrorActionPreference = 'Stop'
  $repo = 'https://github.com/qorstack/sage'

  # key -> adapter source dir under integrations/ + destination + label
  $tools = [ordered]@{
    claude   = @{ src = '.claude';     dest = '.claude';     name = 'Claude Code' }
    cursor   = @{ src = '.cursor';     dest = '.cursor';     name = 'Cursor' }
    windsurf = @{ src = '.windsurf';   dest = '.windsurf';   name = 'Windsurf' }
    cline    = @{ src = '.clinerules'; dest = '.clinerules'; name = 'Cline' }
    copilot  = @{ src = '.github';     dest = '.github';     name = 'GitHub Copilot' }
    codex    = @{ src = '.codex';      dest = '.codex';      name = 'Codex' }
    gemini   = @{ src = 'gemini';      dest = 'GEMINI.md';   name = 'Gemini CLI' }
  }
  $keys = @($tools.Keys)

  # --- choose tools: $env:SAGE_TOOLS override, else interactive multi-select ---
  if ($env:SAGE_TOOLS) {
    $raw = $env:SAGE_TOOLS
  }
  else {
    Write-Host ''
    Write-Host 'Sage: which AI tools should I wire up?'
    for ($i = 0; $i -lt $keys.Count; $i++) {
      Write-Host ('  {0}) {1}' -f ($i + 1), $tools[$keys[$i]].name)
    }
    $raw = Read-Host 'Enter numbers (e.g. 1,2,5), names, or "a" for all'
  }

  $picked = @()
  if ([string]::IsNullOrWhiteSpace($raw) -or $raw.Trim().ToLower() -in @('a', 'all')) {
    $picked = $keys
  }
  else {
    foreach ($tok in ($raw -split '[,\s]+')) {
      $t = $tok.Trim().ToLower()
      if ($t -eq '') { continue }
      if ($t -match '^\d+$') {
        $idx = [int]$t - 1
        if ($idx -ge 0 -and $idx -lt $keys.Count) { $picked += $keys[$idx] }
      }
      elseif ($tools.Contains($t)) { $picked += $t }
    }
    $picked = @($picked | Select-Object -Unique)
  }
  if ($picked.Count -eq 0) {
    Write-Host 'Sage: no valid tools selected. Nothing to do.'
    return
  }

  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host 'Sage: git is required but was not found. Install Git, then re-run.'
    return
  }

  $tmp = Join-Path $env:TEMP ('sage-' + [guid]::NewGuid().ToString('N'))
  Write-Host 'Sage: fetching...'
  # git writes progress to stderr even on success; in PowerShell 5.1 that would
  # otherwise abort the script. Run it non-terminating and check the real exit code.
  $eap = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  git clone --depth 1 --quiet $repo $tmp 2>&1 | Out-Null
  $cloneOk = ($LASTEXITCODE -eq 0)
  $ErrorActionPreference = $eap
  if (-not $cloneOk) {
    Write-Host "Sage: git clone failed (exit $LASTEXITCODE). Check your network and try again."
    return
  }

  try {
    # --- protocol + shared system files (always overwrite: these are Sage itself) ---
    Copy-Item "$tmp/AGENTS.md" './AGENTS.md' -Force
    New-Item -ItemType Directory -Force -Path 'agents/sage/commands', 'agents/sage/docs' | Out-Null
    Copy-Item "$tmp/agents/sage/commands/*.md" 'agents/sage/commands/' -Force
    Copy-Item "$tmp/agents/sage/docs/docs-style-template.md" 'agents/sage/docs/' -Force

    # --- starter knowledge (seed only if absent: never clobber the team's edits) ---
    if (-not (Test-Path 'agents/sage/index.md')) { Copy-Item "$tmp/agents/sage/index.md" 'agents/sage/index.md' -Force }
    if (-not (Test-Path 'agents/sage/roles')) { Copy-Item "$tmp/agents/sage/roles" 'agents/sage/' -Recurse -Force }

    # --- install the selected tools' thin adapters ---
    $installed = @()
    foreach ($k in $picked) {
      $t = $tools[$k]
      if ($k -eq 'gemini') {
        Copy-Item "$tmp/integrations/gemini.md" './GEMINI.md' -Force
      }
      else {
        New-Item -ItemType Directory -Force -Path $t.dest | Out-Null
        Copy-Item "$tmp/integrations/$($t.src)/*" $t.dest -Recurse -Force
      }
      $installed += $t.name
    }

    Write-Host ('Sage: installed. AGENTS.md + agents/sage/ + adapters for: ' + ($installed -join ', '))
    Write-Host 'Next: run  /sage-learning  to seed knowledge from your codebase.'
  }
  finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
  }
}
