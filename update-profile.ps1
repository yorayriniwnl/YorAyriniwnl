Write-Host "Fetching latest GitHub stats..." -ForegroundColor Cyan
python scripts/generate_stats.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Could not fetch stats. You might have hit the GitHub rate limit (60 requests/hour). Try again in an hour." -ForegroundColor Yellow
    exit
}

Write-Host "Regenerating SVG assets..." -ForegroundColor Cyan
python scripts/generate_assets.py

Write-Host "Updating output branch on GitHub..." -ForegroundColor Cyan
$currentBranch = git branch --show-current
git checkout output
Copy-Item -Path "generated\*.svg" -Destination "." -Force
git add *.svg
git commit -m "chore: manual stats and assets update"
git push origin output
git checkout $currentBranch

Write-Host "Profile successfully updated!" -ForegroundColor Green
