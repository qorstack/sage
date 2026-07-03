# Sage installer — one command, any repo. Sets up (or updates) Sage:
#   irm https://raw.githubusercontent.com/qorstack/sage/main/install.ps1 | iex
#
# It fetches the protocol + commands, detects which AI tools this repo uses, and
# drops the matching thin adapters. It NEVER touches your own knowledge under
# agents/sage/<domain>/ — only Sage's own system files are overwritten.
$ErrorActionPreference = 'Stop'

$repo = 'https://github.com/qorstack/sage'
$tmp  = Join-Path $env:TEMP ('sage-' + [guid]::NewGuid().ToString('N'))

Write-Host 'Sage · fetching…'
git clone --depth 1 $repo $tmp 2>$null | Out-Null

try {
  # --- protocol + shared system files (always overwrite: these are Sage itself) ---
  Copy-Item "$tmp/AGENTS.md" './AGENTS.md' -Force
  New-Item -ItemType Directory -Force -Path 'agents/sage/commands', 'agents/sage/docs' | Out-Null
  Copy-Item "$tmp/agents/sage/commands/*.md" 'agents/sage/commands/' -Force
  Copy-Item "$tmp/agents/sage/docs/docs-style-template.md" 'agents/sage/docs/' -Force

  # --- starter knowledge (seed only if absent: never clobber the team's edits) ---
  if (-not (Test-Path 'agents/sage/index.md')) { Copy-Item "$tmp/agents/sage/index.md" 'agents/sage/index.md' -Force }
  if (-not (Test-Path 'agents/sage/roles'))    { Copy-Item "$tmp/agents/sage/roles" 'agents/sage/' -Recurse -Force }

  # --- detect tools present in this repo, install each one's thin adapters ---
  $found = @()
  foreach ($t in '.claude', '.cursor', '.windsurf', '.clinerules', '.github', '.codex') {
    if (Test-Path $t) {
      Copy-Item "$tmp/integrations/$t/*" $t -Recurse -Force
      $found += $t
    }
  }
  if ((Test-Path 'GEMINI.md') -or (Test-Path '.gemini/GEMINI.md')) {
    Copy-Item "$tmp/integrations/gemini.md" './GEMINI.md' -Force
    $found += 'GEMINI.md'
  }

  # --- none found → default to Claude Code ---
  if ($found.Count -eq 0) {
    New-Item -ItemType Directory -Force -Path '.claude' | Out-Null
    Copy-Item "$tmp/integrations/.claude/*" '.claude' -Recurse -Force
    $found += '.claude (default)'
  }

  Write-Host ("Sage · installed. AGENTS.md + agents/sage/ + adapters for: " + ($found -join ', '))
  Write-Host 'Next: run  /sage-learning  to seed knowledge from your codebase.'
}
finally {
  Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
