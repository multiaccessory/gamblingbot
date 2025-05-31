# This script sets up a Python virtual environment, installs required packages,
# and runs a Python script for a Discord bot.
# Ensure the script is run from the directory where it is located
$BotScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed. Please install Python and try again."
    exit 1
}
# Create a Python virtual environment if it doesn't exist
if (-not (Test-Path "$BotScriptRoot\.venv")) {
    Write-Host "Creating Python virtual environment..."
    & python -m venv "$BotScriptRoot\.venv"
} else {
    Write-Host "Python virtual environment already exists."
}
# Ensure the Python virtual environment is activated
if (-not (Get-Command "$BotScriptRoot\.venv\Scripts\Activate.ps1" -ErrorAction SilentlyContinue)) {
    Write-Host "Virtual environment activation script not found. Please check the virtual environment setup."
    exit 1
}
# Upgrade pip to the latest version
& "$BotScriptRoot\.venv\Scripts\python.exe" -m pip install --upgrade pip
# Install required Python packages
& "$BotScriptRoot\.venv\Scripts\python.exe" -m pip install discord.py python-dotenv psutil
# Run the Python script
& "$BotScriptRoot\.venv\Scripts\python.exe" "$BotScriptRoot\main.py" -i "$BotScriptRoot\input" -o "$BotScriptRoot\output"
#remove the virtual environment after execution
Write-Host "Cleaning up the virtual environment..."
Remove-Item -Recurse -Force "$BotScriptRoot\.venv"
Write-Host "Bot execution completed and virtual environment removed."
# End of script