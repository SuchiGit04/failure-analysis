# =========================================================
# PowerShell Deployment Script (Safe for Multiple Projects)
# =========================================================

# ----------- Configuration -----------
$projectName = "FailureAnalysis"
$projectPath = "C:\Users\Administrator\Documents\Failure Analysis"
$pythonExe = "$projectPath\venv\Scripts\python.exe"
$appFile = "app.py"
# (Optional) assign a port number for reference
$port = 5006

# -------------------------------------

Write-Host "🚀 Starting deployment for $projectName..."

# Go to project directory
Set-Location $projectPath

# Pull latest code
Write-Host "📥 Pulling latest code..."
git reset --hard
git clean -fd
git pull origin main

# Ensure virtual environment
if (-not (Test-Path "$projectPath\venv")) {
    Write-Host "🧱 Creating virtual environment..."
    python -m venv venv
}

# Install dependencies
Write-Host "📦 Installing dependencies..."
& "$projectPath\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$projectPath\venv\Scripts\python.exe" -m pip install -r requirements.txt

# Stop only this project's Flask process (by app path)
Write-Host "🛑 Stopping existing Flask instance (if any)..."
Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match "$projectPath\\$appFile" } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
}

# Start new Flask app in fully detached CMD window
Write-Host "🚀 Starting new Flask app for $projectName..."
Start-Process -FilePath "cmd.exe" -ArgumentList "/c start python `"$projectPath\$appFile`"" -WorkingDirectory $projectPath -WindowStyle Minimized

Write-Host "✅ Deployment complete! $projectName is running on port $port."
