# PowerShell deployment script for Failure Analysis
Write-Host "Starting deployment..."

# Go to project folder
Set-Location "C:\Users\Administrator\Documents\Failure Analysis"

# Discard any local changes and pull latest code
git reset --hard
git pull origin main

# Activate virtual environment and install dependencies
Write-Host "Installing dependencies..."
& "C:\Users\Administrator\Documents\Failure Analysis\venv\Scripts\activate.ps1"
pip install -r requirements.txt

# Stop any existing Flask process running on port 5006
Write-Host "Stopping existing Flask app (if any)..."
Get-Process | Where-Object { $_.ProcessName -eq "python" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Restart Flask app in background
Write-Host "Starting Flask app..."
Start-Process python "app.py"

Write-Host "Deployment completed successfully."
