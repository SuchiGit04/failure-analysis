Write-Host "Starting deployment for Failure Analysis..."

# Go to project folder
Set-Location "C:\Users\Administrator\Documents\Failure Analysis"

# Discard any local changes and pull latest code
git reset --hard
git pull origin main

# Activate virtual environment and install dependencies
Write-Host "Installing dependencies..."
& "C:\Users\Administrator\Documents\Failure Analysis\venv\Scripts\activate.ps1"
pip install -r requirements.txt

# Stop only the app running on port 5006
Write-Host "Stopping existing Flask app on port 5006..."
$port = 5006
$pid = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess
if ($pid) {
    Stop-Process -Id $pid -Force
    Write-Host "Stopped process using port $port (PID: $pid)"
} else {
    Write-Host "No process found on port $port."
}

# Restart Flask app in background
Write-Host "Starting Flask app..."
Start-Process "cmd.exe" "/c start /min python app.py" -WorkingDirectory "C:\Users\Administrator\Documents\Failure Analysis"

Write-Host "Deployment completed successfully."
