# Start the PhishLens UI from the repository root: .\frontend.ps1
Set-Location "$PSScriptRoot\frontend"
if (-not (Test-Path ".\node_modules")) {
    Write-Host "frontend\node_modules is missing. Run: npm --prefix frontend install"
    exit 1
}
npm run dev
