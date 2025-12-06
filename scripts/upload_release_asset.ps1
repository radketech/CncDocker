<#
PowerShell script to create (if needed) a GitHub release for a given tag
and upload a release asset (exe) using a Personal Access Token (PAT).

Usage (interactive token prompt):
  powershell -ExecutionPolicy Bypass -File .\scripts\upload_release_asset.ps1

Usage (pass token as parameter - more convenient for automation):
  powershell -ExecutionPolicy Bypass -File .\scripts\upload_release_asset.ps1 -Token <YOUR_PAT>

Security note: Prefer entering token interactively. Do not commit your PAT.
#>
param(
    [string]$Token,
    [string]$Owner = "radketech",
    [string]$Repo = "CncDocker",
    [string]$Tag = "v1.0.1",
    [string]$AssetPath = ".\dist\CnCDocker.exe",
    [string]$AssetName = "CnCDocker.exe",
    [string]$ReleaseNotesFile = "CHANGELOG.md"
)

function Read-TokenInteractive {
    $ss = Read-Host -Prompt "Enter GitHub Personal Access Token (repo scope)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ss)
    try { [Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

if (-not $Token) {
    $Token = Read-TokenInteractive
}

if (-not (Test-Path $AssetPath)) {
    Write-Error "Asset path not found: $AssetPath"
    exit 2
}

$headers = @{ Authorization = "token $Token"; Accept = "application/vnd.github.v3+json" }

# Attempt to get an existing release for the tag
$release = $null
try {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/releases/tags/$Tag" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "Found existing release for tag $Tag (id=$($release.id))."
} catch {
    # If not found (404), create it
    Write-Host "Release for tag $Tag not found. Creating new release..."
    $notes = ""
    if (Test-Path $ReleaseNotesFile) { $notes = Get-Content -Raw $ReleaseNotesFile } else { $notes = "Release $Tag" }
    $payload = @{ tag_name = $Tag; name = "$Repo $Tag"; body = $notes; draft = $false; prerelease = $false } | ConvertTo-Json -Depth 10
    try {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/releases" -Method Post -Headers $headers -Body $payload -ErrorAction Stop
        Write-Host "Created release id=$($release.id)."
    } catch {
        Write-Error "Failed to create release: $($_.Exception.Message)"
        exit 3
    }
}

# Determine upload URL
$uploadUrl = $release.upload_url -replace '\{\?name,label\}', ''

# If an asset with the same name exists, delete it
$existingAsset = $null
if ($release.assets) { $existingAsset = $release.assets | Where-Object { $_.name -eq $AssetName } }
if ($existingAsset) {
    Write-Host "An asset named $AssetName already exists (id=$($existingAsset.id)). Deleting it first..."
    try {
        Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/releases/assets/$($existingAsset.id)" -Method Delete -Headers $headers -ErrorAction Stop
        Write-Host "Deleted existing asset."
    } catch {
        Write-Error "Failed to delete existing asset: $($_.Exception.Message)"
        exit 4
    }
}

# Upload the asset
$uploadUri = "$uploadUrl?name=$AssetName"
Write-Host "Uploading $AssetPath to release $($release.id) as $AssetName..."
try {
    Invoke-RestMethod -Uri $uploadUri -Method Post -Headers @{ Authorization = "token $Token"; "Content-Type" = "application/octet-stream" } -InFile $AssetPath -ErrorAction Stop
    Write-Host "Upload complete."
} catch {
    Write-Error "Upload failed: $($_.Exception.Message)"
    exit 5
}

Write-Host "Done. Visit: https://github.com/$Owner/$Repo/releases/tag/$Tag"
