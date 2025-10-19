# HealthSync Auto-Fix Script
# This script will backup and replace your server file

Write-Host "🚀 HealthSync Auto-Fix Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
$currentDir = Get-Location
Write-Host "📂 Current directory: $currentDir" -ForegroundColor Yellow

# Check if files exist
if (-Not (Test-Path "mcp-server.js")) {
    Write-Host "❌ ERROR: mcp-server.js not found!" -ForegroundColor Red
    Write-Host "   Make sure you're in the correct directory:" -ForegroundColor Red
    Write-Host "   d:\healthsync\frontend\hugging_face_access" -ForegroundColor Yellow
    exit 1
}

if (-Not (Test-Path "mcp-server-fixed.js")) {
    Write-Host "❌ ERROR: mcp-server-fixed.js not found!" -ForegroundColor Red
    Write-Host "   The fixed file must be in this directory." -ForegroundColor Red
    exit 1
}

# Ask for confirmation
Write-Host "⚠️  This will:" -ForegroundColor Yellow
Write-Host "   1. Backup mcp-server.js to mcp-server.backup.js" -ForegroundColor White
Write-Host "   2. Replace mcp-server.js with the fixed version" -ForegroundColor White
Write-Host ""
$confirmation = Read-Host "Do you want to continue? (y/n)"

if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "❌ Operation cancelled." -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🔄 Creating backup..." -ForegroundColor Cyan

# Create backup
try {
    Copy-Item -Path "mcp-server.js" -Destination "mcp-server.backup.js" -Force
    Write-Host "✅ Backup created: mcp-server.backup.js" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create backup: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🔄 Applying fix..." -ForegroundColor Cyan

# Replace with fixed version
try {
    Copy-Item -Path "mcp-server-fixed.js" -Destination "mcp-server.js" -Force
    Write-Host "✅ Server file updated successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to update server: $_" -ForegroundColor Red
    Write-Host "🔄 Restoring backup..." -ForegroundColor Yellow
    Copy-Item -Path "mcp-server.backup.js" -Destination "mcp-server.js" -Force
    exit 1
}

Write-Host ""
Write-Host "✨ Fix applied successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Stop your current server (Ctrl+C)" -ForegroundColor White
Write-Host "   2. Start the server: node mcp-server.js" -ForegroundColor White
Write-Host "   3. Test at: http://localhost:4000/html_pages/chat.html" -ForegroundColor White
Write-Host ""

# Ask if user wants to start the server now
$startNow = Read-Host "Do you want to start the server now? (y/n)"

if ($startNow -eq 'y' -or $startNow -eq 'Y') {
    Write-Host ""
    Write-Host "🚀 Starting server..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    node mcp-server.js
} else {
    Write-Host "👍 You can start the server manually with: node mcp-server.js" -ForegroundColor Yellow
}
