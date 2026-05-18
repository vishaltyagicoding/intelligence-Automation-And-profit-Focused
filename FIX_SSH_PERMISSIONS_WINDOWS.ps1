# ═══════════════════════════════════════════════════════════════════════════
# Fix SSH Key Permissions for Singapore Server (Windows PowerShell)
# ═══════════════════════════════════════════════════════════════════════════
#
# PROBLEM: SSH key has too many permissions, causing "bad permissions" error
# SOLUTION: Remove all permissions except your user account (read-only)
#
# RUN THIS SCRIPT AS ADMINISTRATOR in PowerShell
# ═══════════════════════════════════════════════════════════════════════════

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Fix SSH Key Permissions for Singapore Server" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Step 1: Navigate to project directory
Write-Host "[1/5] Navigating to project directory..." -ForegroundColor Yellow
$projectPath = "D:\intelligence-Automation-And-profit-Focused\intelligence-Automation-And-profit-Focused"
Set-Location $projectPath
Write-Host "✅ Current directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Step 2: Check if PEM file exists
Write-Host "[2/5] Checking if smartriskfx-singapore.pem exists..." -ForegroundColor Yellow
$pemFile = "smartriskfx-singapore.pem"
if (-Not (Test-Path $pemFile)) {
    Write-Host "❌ ERROR: $pemFile not found in current directory!" -ForegroundColor Red
    Write-Host "   Please ensure the file exists before running this script." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Found: $pemFile" -ForegroundColor Green
Write-Host ""

# Step 3: Remove all inherited permissions
Write-Host "[3/5] Removing all inherited permissions..." -ForegroundColor Yellow
icacls $pemFile /inheritance:r
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Failed to remove inherited permissions" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Inherited permissions removed" -ForegroundColor Green
Write-Host ""

# Step 4: Grant read-only access to ONLY your user account
Write-Host "[4/5] Granting read-only access to your user account..." -ForegroundColor Yellow
$currentUser = $env:USERNAME
icacls $pemFile /grant:r "$($currentUser):(R)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Failed to grant permissions to $currentUser" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Read-only access granted to: $currentUser" -ForegroundColor Green
Write-Host ""

# Step 5: Remove NT AUTHORITY\Authenticated Users explicitly
Write-Host "[5/5] Removing NT AUTHORITY\Authenticated Users..." -ForegroundColor Yellow
icacls $pemFile /remove "NT AUTHORITY\Authenticated Users" 2>$null
# Ignore errors if this user doesn't exist
Write-Host "✅ Removed NT AUTHORITY\Authenticated Users (if existed)" -ForegroundColor Green
Write-Host ""

# Verify final permissions
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Final Permissions (should show ONLY your username)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
icacls $pemFile
Write-Host ""

# Test SSH connection
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Testing SSH Connection to Singapore Server" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Attempting to connect to: ubuntu@13.250.19.107" -ForegroundColor Yellow
Write-Host "If successful, you'll see the Ubuntu welcome message." -ForegroundColor Yellow
Write-Host ""

ssh -i $pemFile ubuntu@13.250.19.107

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ SUCCESS! SSH connection works!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Update GitHub Actions secrets (EC2_HOST and EC2_SSH_KEY)" -ForegroundColor White
    Write-Host "2. Update DNS records to point to 13.250.19.107" -ForegroundColor White
    Write-Host "3. Obtain SSL certificate" -ForegroundColor White
    Write-Host "4. Test production website" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ SSH connection failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible reasons:" -ForegroundColor Yellow
    Write-Host "1. Security group not allowing your IP address" -ForegroundColor White
    Write-Host "2. Server is down or unreachable" -ForegroundColor White
    Write-Host "3. PEM file content is incorrect" -ForegroundColor White
    Write-Host ""
    Write-Host "Check AWS Console: https://console.aws.amazon.com/ec2/" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Script Complete" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
