# Activate Python virtual environment
. "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# Install required Python packages
& "$PSScriptRoot\.venv\Scripts\python.exe" -m pip install discord.py python-dotenv psutil

# Run the Python script
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\main.py" -i "$PSScriptRoot\input" -o "$PSScriptRoot\output"