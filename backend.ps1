# Start the PhishLens API from the repository root: .\backend.ps1
Set-Location "$PSScriptRoot\backend"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "backend\.venv is missing. See AGENTS.md for setup."
    exit 1
}
$version = & .\.venv\Scripts\python.exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$version -lt [version]"3.11") {
    Write-Host "backend\.venv uses Python $version. Recreate it with: py -3.11 -m venv backend\.venv"
    exit 1
}
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
