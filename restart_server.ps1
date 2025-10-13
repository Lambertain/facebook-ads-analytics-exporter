# Restart FastAPI server

Write-Host "Stopping old uvicorn processes..." -ForegroundColor Yellow
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*8000*"
} | Stop-Process -Force

Start-Sleep -Seconds 2

Write-Host "Starting new server..." -ForegroundColor Green
Set-Location "D:\Automation\Development\projects\ecademy"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WindowStyle Minimized

Start-Sleep -Seconds 3

Write-Host "Server started! Checking availability..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Server is running!" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Server may still be starting. Wait 10 seconds." -ForegroundColor Yellow
}
