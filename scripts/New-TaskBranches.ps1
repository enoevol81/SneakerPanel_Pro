<# 
Creates a set of task branches from main, optionally pushes them, and (optionally)
opens draft PRs for each via GitHub CLI.

USAGE:
  # Local branches only
  pwsh -File .\scripts\New-TaskBranches.ps1

  # Create + push
  pwsh -File .\scripts\New-TaskBranches.ps1 -Push

  # Create + push + draft PRs
  pwsh -File .\scripts\New-TaskBranches.ps1 -Push -CreatePRs
#>

param(
  [switch]$Push,
  [switch]$CreatePRs
)

# ---- CONFIG: edit your branch list here ----
$Branches = @(
  'feat/ui-polish',
  'feat/helper-tooltips',
  'feat/collapsible-steps',
  'chore/tooltips-audit',
  'chore/ui-consistency',
  'chore/comment-normalization',
  'chore/compat-4-5',
  'chore/repo-clean'
)

# Optional labels for PRs
$PrLabels = @('task','addon','spp')

# Draft PR body (customize freely)
$PrBody = @"
This is an initialization PR for the scoped task branch.

**Definition of Done**
- Panel/UI changes are consistent with existing design language
- Operators have \`bl_description\` and property descriptions
- Comment headers follow H1/H2 convention
- Black + isort applied
- No console warnings in Blender 4.4.3
- Version guards in place for 4.5 (where applicable)

Please attach before/after screenshots if UI changed.
"@

function Assert-CleanTree {
  $status = git status --porcelain
  if ($status) {
    Write-Error "Working tree is not clean. Commit or stash changes first."
    exit 1
  }
}

function Ensure-MainUpToDate {
  git fetch --all --prune
  git switch main | Out-Null
  git pull --ff-only
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Could not fast-forward main. Resolve manually."
    exit 1
  }
}

function Branch-Exists($name) {
  git rev-parse --verify $name 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}

function Create-Branch($name) {
  if (Branch-Exists $name) {
    Write-Host "✓ Branch exists: $name"
  } else {
    git branch $name main
    if ($LASTEXITCODE -ne 0) { throw "Failed to create $name" }
    Write-Host "✔ Created: $name"
  }
}

function Push-Branch($name) {
  git push -u origin $name
  if ($LASTEXITCODE -ne 0) { throw "Failed to push $name" }
  Write-Host "⇧ Pushed: $name"
}

function Create-DraftPR($name) {
  if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) not found. Install from https://cli.github.com and run 'gh auth login'."
  }
  $labelArgs = @()
  foreach ($l in $PrLabels) { $labelArgs += @('--label', $l) }

  gh pr create `
    --base main `
    --head $name `
    --title "Init: $name" `
    --body $PrBody `
    --draft `
    @labelArgs

  if ($LASTEXITCODE -ne 0) { throw "Failed to create PR for $name" }
  Write-Host "Ⓟ Draft PR opened: $name"
}

# ---- Run ----
Assert-CleanTree
Ensure-MainUpToDate

foreach ($b in $Branches) {
  try {
    Create-Branch $b
    if ($Push) {
      Push-Branch $b
      if ($CreatePRs) { Create-DraftPR $b }
    }
  } catch {
    Write-Warning $_
  }
}

Write-Host "`nDone."
if ($Push -and $CreatePRs) {
  Write-Host "All branches pushed and draft PRs opened."
} elseif ($Push) {
  Write-Host "All branches pushed to origin."
} else {
  Write-Host "Local branches created. Use '-Push' to push next time."
}
