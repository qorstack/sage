# Sage installer — one command, any repo. Sets up (or updates) Sage:
#   irm https://raw.githubusercontent.com/qorstack/sage/main/install.ps1 | iex
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
    cursor   = @{ src = '.cursor';     dest = '.cursor';     name = 'Cursor' }
    windsurf = @{ src = '.windsurf';   dest = '.windsurf';   name = 'Windsurf' }
    cline    = @{ src = '.clinerules'; dest = '.clinerules'; name = 'Cline' }
    copilot  = @{ src = '.github';     dest = '.github';     name = 'GitHub Copilot' }
    codex    = @{ src = '.codex';      dest = '.codex';      name = 'Codex' }
    gemini   = @{ src = 'gemini';      dest = 'GEMINI.md';   name = 'Gemini CLI' }
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

  # Interactive arrow-key checkbox. Returns $null if no interactive console
  # (then the caller falls back to a typed prompt / SAGE_TOOLS / all).
  function Select-ToolsTui {
    try { $null = [Console]::CursorTop } catch { return $null }
    $checked = @{}; foreach ($k in $keys) { $checked[$k] = $false }
    $pos = 0
    try {
      [Console]::WriteLine('Sage: select AI tools  (Up/Down move - Space toggle - A all - Enter confirm)')
      $top = [Console]::CursorTop
      foreach ($k in $keys) { [Console]::WriteLine('') }
      $width = [Math]::Max(20, [Console]::WindowWidth - 1)
      while ($true) {
        for ($i = 0; $i -lt $keys.Count; $i++) {
          [Console]::SetCursorPosition(0, $top + $i)
          $mark = if ($checked[$keys[$i]]) { '[x]' } else { '[ ]' }
          $ptr = if ($i -eq $pos) { '>' } else { ' ' }
          $line = '{0} {1} {2}' -f $ptr, $mark, $tools[$keys[$i]].name
          [Console]::Write($line.PadRight($width))
        }
        $key = [Console]::ReadKey($true)
        switch ($key.Key) {
          'UpArrow' { $pos = ($pos - 1 + $keys.Count) % $keys.Count }
          'DownArrow' { $pos = ($pos + 1) % $keys.Count }
          'Spacebar' { $checked[$keys[$pos]] = -not $checked[$keys[$pos]] }
          'Enter' {
            [Console]::SetCursorPosition(0, $top + $keys.Count)
            return @($keys | Where-Object { $checked[$_] })
          }
          default {
            if ($key.KeyChar -eq 'a' -or $key.KeyChar -eq 'A') {
              $allOn = -not ($keys | Where-Object { -not $checked[$_] })
              foreach ($k in $keys) { $checked[$k] = -not $allOn }
            }
          }
        }
      }
    }
    catch { return $null }
  }

  # --- choose tools: env override, else checkbox TUI, else typed prompt / all ---
  if ($env:SAGE_TOOLS) {
    $picked = Parse-Tools $env:SAGE_TOOLS
  }
  else {
    $picked = Select-ToolsTui
    if ($null -eq $picked) {
      try {
        Write-Host ''
        Write-Host 'Sage: which AI tools should I wire up?'
        for ($i = 0; $i -lt $keys.Count; $i++) { Write-Host ('  {0}) {1}' -f ($i + 1), $tools[$keys[$i]].name) }
        $picked = Parse-Tools (Read-Host 'Enter numbers (e.g. 1,2,5), names, or "a" for all')
      }
      catch { $picked = $keys }
    }
  }
  $picked = @($picked)
  if ($picked.Count -eq 0) { Write-Host 'Sage: no tools selected. Nothing to do.'; return }

  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host 'Sage: git is required but was not found. Install Git, then re-run.'; return
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
  if (-not $cloneOk) { Write-Host "Sage: git clone failed (exit $LASTEXITCODE). Check your network and try again."; return }

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
      if ($k -eq 'gemini') { Copy-Item "$tmp/integrations/gemini.md" './GEMINI.md' -Force }
      else {
        New-Item -ItemType Directory -Force -Path $t.dest | Out-Null
        Copy-Item "$tmp/integrations/$($t.src)/*" $t.dest -Recurse -Force
      }
      $installed += $t.name
    }

    Write-Host ('Sage: installed. AGENTS.md + agents/sage/ + adapters for: ' + ($installed -join ', '))
    Write-Host 'Next: run  /sage-learning  to seed knowledge from your codebase.'
  }
  finally { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
}
