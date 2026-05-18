# ═══════════════════════════════════════════════════════════════════════════
# Flush DNS Cache - Force Windows to Use New DNS Records
# ═══════════════════════════════════════════════════════════════════════════
#
# RUN THIS SCRIPT AS ADMINISTRATOR in PowerShell
# ═══════════════════════════════════════════════════════════════════════════

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Flush DNS Cache - Force New DNS Records" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Step 1: Show current DNS cache for smartriskfx.com
Write-Host "[1/5] Current DNS cache for smartriskfx.com:" -ForegroundColor Yellow
nslookup smartriskfx.com
Write-Host ""

# Step 2: Flush DNS cache
Write-Host "[2/5] Flushing DNS cache..." -ForegroundColor Yellow
ipconfig /flushdns
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ DNS cache flushed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to flush DNS cache (are you running as Administrator?)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Clear browser DNS cache (Chrome/Edge)
Write-Host "[3/5] Instructions to clear browser DNS cache:" -ForegroundColor Yellow
Write-Host "   Chrome/Edge: Visit chrome://net-internals/#dns and click 'Clear host cache'" -ForegroundColor White
Write-Host "   Firefox: Restart Firefox" -ForegroundColor White
Write-Host ""

# Step 4: Restart DNS Client service
Write-Host "[4/5] Restarting DNS Client service..." -ForegroundColor Yellow
Restart-Service -Name "Dnscache" -Force
if ($LASTEXITCODE -eq 0 -or $?) {
    Write-Host "✅ DNS Client service restarted" -ForegroundColor Green
} else {
    Write-Host "⚠️  Could not restart DNS Client service (may require manual restart)" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Verify new DNS
Write-Host "[5/5] Verifying new DNS (should show 13.250.19.107):" -ForegroundColor Yellow
Start-Sleep -Seconds 2
nslookup smartriskfx.com
Write-Host ""

# Check if it worked
$dnsResult = nslookup smartriskfx.com 2>&1 | Select-String "13.250.19.107"
if ($dnsResult) {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  ✅ SUCCESS! DNS now points to Singapore server" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Clear browser cache (Ctrl+Shift+Delete)" -ForegroundColor White
    Write-Host "2. Clear browser DNS cache:" -ForegroundColor White
    Write-Host "   - Chrome/Edge: chrome://net-internals/#dns → Clear host cache" -ForegroundColor White
    Write-Host "   - Firefox: Restart browser" -ForegroundColor White
    Write-Host "3. Hard refresh website (Ctrl+F5)" -ForegroundColor White
    Write-Host "4. Check console - warnings should be much fewer" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host "  ⚠️  DNS still showing old IP" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Additional steps to try:" -ForegroundColor Cyan
    Write-Host "1. Wait 5 more minutes (DNS propagation can take time)" -ForegroundColor White
    Write-Host "2. Use Google DNS: nslookup smartriskfx.com 8.8.8.8" -ForegroundColor White
    Write-Host "3. Check online: https://dnschecker.org/#A/smartriskfx.com" -ForegroundColor White
    Write-Host "4. Restart your computer (last resort)" -ForegroundColor White
    Write-Host ""
}

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Script Complete" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
