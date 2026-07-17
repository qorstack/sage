# Sage installer — one command, any repo. Sets up (or updates) Sage:
#   irm https://cdn.jsdelivr.net/gh/qorstack/sage@latest/install.ps1 | iex
#
# It shows a checkbox picker of AI tools (Up/Down move, Space toggle, A all,
# Enter confirm), fetches the protocol + commands, and drops the adapters you
# pick. It NEVER touches your own knowledge under agents/sage/<domain>/.
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
    codex    = @{ src = '.codex';      dest = '.codex';      name = 'Codex' }
    cursor   = @{ src = '.cursor';     dest = '.cursor';     name = 'Cursor' }
    copilot  = @{ src = '.github';     dest = '.github';     name = 'GitHub Copilot' }
    gemini   = @{ src = 'gemini';      dest = 'GEMINI.md';   name = 'Gemini CLI' }
    windsurf = @{ src = '.windsurf';   dest = '.windsurf';   name = 'Windsurf' }
    cline    = @{ src = '.clinerules'; dest = '.clinerules'; name = 'Cline' }
  }
  $keys = @($tools.Keys)

  function Parse-Tools([string]$raw) {
    if ([string]::IsNullOrWhiteSpace($raw) -or $raw.Trim().ToLower() -in @('a', 'all')) { return $keys }
    $out = @()
    foreach ($tok in ($raw -split '[,\s]+')) {
      $t = $tok.Trim().ToLower()
      if ($t -eq '') { continue }
      if ($t -match '^\d+$') { $i = [int]$t - 1; if ($i -ge 0 -and $i -lt $keys.Count) { $out += $keys[$i] } }
      elseif ($tools.Contains($t)) { $out += $t }
    }
    return @($out | Select-Object -Unique)
  }

  # Interactive arrow-key checkbox. Returns a comma-joined key string (may be
  # empty), or $null if there is no usable console (caller then falls back).
  function Select-ToolsTui {
    # Arrow keys need a real console: bail (to the number-toggle menu) when input
    # is redirected or ReadKey is unavailable (e.g. VSCode Integrated Console).
    try {
      if ([Console]::IsInputRedirected) { return $null }
      $null = [Console]::KeyAvailable
      $null = [Console]::CursorTop; $null = [Console]::WindowWidth
    }
    catch { return $null }
    $checked = @{}; foreach ($k in $keys) { $checked[$k] = $false }
    $curVis = $true
    try {
      [Console]::WriteLine('')
      [Console]::WriteLine('Sage: select AI tools - press 1-7 to toggle, A = all, Enter = confirm')
      [Console]::WriteLine('')
      # reserve one line per tool, then derive the true top row (scroll-safe)
      foreach ($k in $keys) { [Console]::WriteLine('') }
      $top = [Console]::CursorTop - $keys.Count
      try { $curVis = [Console]::CursorVisible } catch {}
      try { [Console]::CursorVisible = $false } catch {}
      while ($true) {
        $width = [Math]::Max(20, [Console]::WindowWidth - 1)
        for ($i = 0; $i -lt $keys.Count; $i++) {
          [Console]::SetCursorPosition(0, $top + $i)
          if ($checked[$keys[$i]]) {
            [Console]::ForegroundColor = 'Cyan'
            [Console]::Write(('  [x] {0}) {1}' -f ($i + 1), $tools[$keys[$i]].name).PadRight($width))
            [Console]::ResetColor()
          }
          else {
            [Console]::Write(('  [ ] {0}) {1}' -f ($i + 1), $tools[$keys[$i]].name).PadRight($width))
          }
        }
        $key = [Console]::ReadKey($true)
        if ($key.Key.ToString() -eq 'Enter') {
          [Console]::SetCursorPosition(0, $top + $keys.Count)
          return (($keys | Where-Object { $checked[$_] }) -join ',')
        }
        $ch = "$($key.KeyChar)".ToLower()
        if ($ch -eq 'a') {
          $allOn = @($keys | Where-Object { -not $checked[$_] }).Count -eq 0
          foreach ($k in $keys) { $checked[$k] = -not $allOn }
        }
        elseif ($ch -match '^[1-7]$') {
          $idx = [int]$ch - 1
          $checked[$keys[$idx]] = -not $checked[$keys[$idx]]
        }
      }
    }
    catch { return $null }
    finally { try { [Console]::CursorVisible = $curVis; [Console]::ResetColor() } catch {} }
  }

  # [x] checkbox by number-toggle. Runs when the arrow TUI can't (e.g. the VSCode
  # PowerShell Integrated Console, where ReadKey is unavailable). Uses Read-Host,
  # so it works wherever the shell can prompt. Returns a comma-joined key string.
  function Select-ToolsMenu {
    $checked = @{}; foreach ($k in $keys) { $checked[$k] = $false }
    Write-Host ''
    Write-Host 'Sage: select AI tools - type a number to toggle, "a" for all, Enter when done.'
    while ($true) {
      for ($i = 0; $i -lt $keys.Count; $i++) {
        $mark = if ($checked[$keys[$i]]) { '[x]' } else { '[ ]' }
        Write-Host ('  {0} {1}) {2}' -f $mark, ($i + 1), $tools[$keys[$i]].name)
      }
      $line = ''
      try { $line = Read-Host 'toggle (number) / a=all / Enter=confirm' }
      catch { foreach ($k in $keys) { $checked[$k] = $true }; break }
      if ([string]::IsNullOrWhiteSpace($line)) { break }
      if ($line.Trim().ToLower() -in @('a', 'all')) { foreach ($k in $keys) { $checked[$k] = $true } }
      else {
        foreach ($tok in ($line -split '[,\s]+')) {
          if ($tok -match '^\d+$') {
            $idx = [int]$tok - 1
            if ($idx -ge 0 -and $idx -lt $keys.Count) { $checked[$keys[$idx]] = -not $checked[$keys[$idx]] }
          }
        }
      }
      Write-Host ''
    }
    return (($keys | Where-Object { $checked[$_] }) -join ',')
  }

  # --- choose tools: env override, else arrow TUI, else [x] number-toggle menu ---
  if ($env:SAGE_TOOLS) {
    $picked = Parse-Tools $env:SAGE_TOOLS
  }
  else {
    $sel = Select-ToolsTui
    if ($null -eq $sel) { $sel = Select-ToolsMenu }
    $picked = @()
    foreach ($k in ($sel -split ',')) { if ($k -ne '') { $picked += $k } }
  }
  $picked = @($picked)
  if ($picked.Count -eq 0) { Write-Host 'Sage: no tools selected. Nothing to do.'; return }

  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host 'Sage: git is required but was not found. Install Git, then re-run.'; return
  }

  $tmp = Join-Path $env:TEMP ('sage-' + [guid]::NewGuid().ToString('N'))
  Write-Host 'Sage: fetching latest from qorstack/sage ...'
  # git writes progress to stderr even on success; in PowerShell 5.1 that would
  # otherwise abort the script. Run it non-terminating and check the real exit code.
  $eap = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  git clone --depth 1 --quiet $repo $tmp 2>&1 | Out-Null
  $cloneOk = ($LASTEXITCODE -eq 0)
  $ErrorActionPreference = $eap
  if (-not $cloneOk) { Write-Host "Sage: git clone failed (exit $LASTEXITCODE). Check your network and try again."; return }
  Write-Host '  + fetched'

  try {
    # --- protocol + Sage-owned files. Clears only what Sage owns; your knowledge
    #     (agents/sage/<domain>/, roles/, flows/, index.md), generated docs, and
    #     .sage-local.json are never touched. ---
    Write-Host 'Sage: writing protocol + commands ...'
    Copy-Item "$tmp/AGENTS.md" './AGENTS.md' -Force
    Write-Host '  + AGENTS.md'
    if (Test-Path 'agents/sage/commands') { Remove-Item 'agents/sage/commands' -Recurse -Force -ErrorAction SilentlyContinue }
    New-Item -ItemType Directory -Force -Path 'agents/sage' | Out-Null
    Copy-Item "$tmp/agents/sage/commands" 'agents/sage/commands' -Recurse -Force
    $cmdCount = @(Get-ChildItem "$tmp/agents/sage/commands/*.md" -ErrorAction SilentlyContinue).Count
    Write-Host ("  + agents/sage/commands/ ($cmdCount commands)")
    Copy-Item "$tmp/agents/sage/docs-style-template.md" 'agents/sage/docs-style-template.md' -Force
    Write-Host '  + agents/sage/docs-style-template.md'
    # migrate old layout: remove only the old Sage assets from agents/sage/docs/, keep the folder.
    Remove-Item 'agents/sage/docs/docs-style-template.md', 'agents/sage/docs/sage-docs.css', 'agents/sage/docs/sage-docs.js' -Force -ErrorAction SilentlyContinue

    # --- starter knowledge (seed only if absent: never clobber the team's edits) ---
    if (-not (Test-Path 'agents/sage/index.md')) { Copy-Item "$tmp/agents/sage/index.md" 'agents/sage/index.md' -Force }
    if (-not (Test-Path 'agents/sage/roles')) { Copy-Item "$tmp/agents/sage/roles" 'agents/sage/' -Recurse -Force }

    # --- install the selected tools' thin adapters ---
    Write-Host 'Sage: wiring up adapters ...'
    $installed = @()
    foreach ($k in $picked) {
      $t = $tools[$k]
      if ($k -eq 'gemini') { Copy-Item "$tmp/integrations/gemini.md" './GEMINI.md' -Force }
      else {
        New-Item -ItemType Directory -Force -Path $t.dest | Out-Null
        Get-ChildItem $t.dest -Recurse -Filter 'sage*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
        Copy-Item "$tmp/integrations/$($t.src)/*" $t.dest -Recurse -Force
      }
      Write-Host ('  + ' + $t.name)
      $installed += $t.name
    }

    Write-Host ''
    Write-Host ('Sage installed. Adapters for: ' + ($installed -join ', '))
    Write-Host ''
    Write-Host 'Commands now available:'
    Write-Host '  /sage                 run before any code change (plan, test, review, capture)'
    Write-Host '  /sage-grill           resolve single-session fog + glossary/checkpoint decisions'
    Write-Host '  /sage-wayfinder       map multi-session fog as durable decision tickets'
    Write-Host '  /sage-flow            design + verify an implementation-ready flow before coding'
    Write-Host '  /sage-unit-test       write unit tests that match this repo''s stack'
    Write-Host '  /sage-e2e-test        drive the app end-to-end (Playwright/Cypress/k6/...) and prove the flow'
    Write-Host '  /sage-security-review review a change for real, exploitable security holes'
    Write-Host '  /sage-docs            turn a spec/flow into a plain-Markdown doc in docs/'
    Write-Host '  /sage-learning        learn this repo''s patterns + research best practices for its stack'
    Write-Host '  /sage-setting         change how /sage runs (mode: auto/ask, default steps)'
    Write-Host '  /sage-update          re-run this installer to update Sage'
    Write-Host ''
    Write-Host 'Next: run  /sage-learning  to seed knowledge from your codebase.'
  }
  finally { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
}
