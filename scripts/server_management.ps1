# PowerShell script for managing BibleScholarProject servers
# Usage:
# - Start DSPy API in foreground: ./scripts/server_management.ps1 -StartDspyApi
# - Start DSPy API in background: ./scripts/server_management.ps1 -StartDspyApi -Background
# - Stop DSPy API: ./scripts/server_management.ps1 -StopDspyApi
# - List running servers: ./scripts/server_management.ps1 -ListServers

param (
    [switch]$StartDspyApi = $false,
    [switch]$StopDspyApi = $false,
    [switch]$StartLmStudio = $false,
    [switch]$ListServers = $false,
    [switch]$StopAll = $false,
    [switch]$Background = $false
)

$ErrorActionPreference = "Stop"

# Define server ports
$SERVER_PORTS = @{
    "DSPy API" = 5005
    "LM Studio" = 1234
    "Old DSPy API" = 5003
    "Minimal API" = 5004
}

function Write-ColoredOutput {
    param (
        [string]$Text,
        [string]$Color = "White"
    )
    
    Write-Host $Text -ForegroundColor $Color
}

function Check-PortInUse {
    param (
        [int]$Port
    )
    
    $inUse = $false
    $portCheck = netstat -ano | Select-String ":$Port "
    
    if ($portCheck) {
        $inUse = $true
    }
    
    return $inUse
}

function Get-ProcessIdByPort {
    param (
        [int]$Port
    )
    
    $portInfo = netstat -ano | Select-String ":$Port "
    if ($portInfo) {
        $parts = $portInfo -split '\s+' | Where-Object { $_ -ne "" }
        return $parts[-1]
    }
    
    return $null
}

function Start-DspyApi {
    param (
        [switch]$Background = $false
    )
    
    $port = $SERVER_PORTS["DSPy API"]
    Write-ColoredOutput "Starting DSPy API on port $port..." "Yellow"
    
    # Check if port is already in use
    if (Check-PortInUse -Port $port) {
        $processId = Get-ProcessIdByPort -Port $port
        Write-ColoredOutput "Port $port is already in use by process ID $processId." "Red"
        Write-ColoredOutput "Please stop the existing server first." "Red"
        return
    }
    
    if ($Background) {
        Start-Process -FilePath python -ArgumentList "final_bible_qa_api.py" -WindowStyle Hidden
        Write-ColoredOutput "DSPy API started in background on port $port" "Green"
    } else {
        Write-ColoredOutput "Starting DSPy API in foreground on port $port" "Green"
        python final_bible_qa_api.py
    }
}

function Stop-DspyApi {
    $port = $SERVER_PORTS["DSPy API"]
    Write-ColoredOutput "Stopping DSPy API on port $port..." "Yellow"
    
    $processId = Get-ProcessIdByPort -Port $port
    if ($processId) {
        taskkill /PID $processId /F
        Write-ColoredOutput "Stopped server on port $port (PID: $processId)" "Green"
    } else {
        Write-ColoredOutput "No server found running on port $port" "Yellow"
    }
}

function Start-LmStudio {
    $lmStudioPath = "C:\Program Files\LM Studio\LM Studio.exe"
    if (Test-Path $lmStudioPath) {
        Write-ColoredOutput "Starting LM Studio..." "Yellow"
        Start-Process -FilePath $lmStudioPath
        Write-ColoredOutput "LM Studio started" "Green"
    } else {
        Write-ColoredOutput "LM Studio executable not found at: $lmStudioPath" "Red"
        Write-ColoredOutput "Please install LM Studio or update the path in this script." "Red"
    }
}

function List-Servers {
    Write-ColoredOutput "Checking for running servers..." "Cyan"
    Write-ColoredOutput "--------------------------------------" "Cyan"
    
    $foundAny = $false
    
    foreach ($server in $SERVER_PORTS.GetEnumerator()) {
        $port = $server.Value
        $name = $server.Name
        
        if (Check-PortInUse -Port $port) {
            $processId = Get-ProcessIdByPort -Port $port
            Write-ColoredOutput "$name is RUNNING on port $port (PID: $processId)" "Green"
            $foundAny = $true
        } else {
            Write-ColoredOutput "$name is NOT RUNNING on port $port" "Gray"
        }
    }
    
    if (-not $foundAny) {
        Write-ColoredOutput "No BibleScholarProject servers are currently running." "Yellow"
    }
    
    Write-ColoredOutput "--------------------------------------" "Cyan"
}

function Stop-AllServers {
    Write-ColoredOutput "Stopping all servers..." "Yellow"
    
    foreach ($server in $SERVER_PORTS.GetEnumerator()) {
        $port = $server.Value
        $name = $server.Name
        
        $processId = Get-ProcessIdByPort -Port $port
        if ($processId) {
            taskkill /PID $processId /F
            Write-ColoredOutput "Stopped $name on port $port (PID: $processId)" "Green"
        } else {
            Write-ColoredOutput "$name not running on port $port" "Gray"
        }
    }
    
    Write-ColoredOutput "All servers stopped" "Green"
}

# Execute the requested action
if ($StartDspyApi) {
    Start-DspyApi -Background:$Background
}
elseif ($StopDspyApi) {
    Stop-DspyApi
}
elseif ($StartLmStudio) {
    Start-LmStudio
}
elseif ($ListServers) {
    List-Servers
}
elseif ($StopAll) {
    Stop-AllServers
}
else {
    # If no parameters provided, show help
    Write-ColoredOutput "BibleScholarProject Server Management Script" "Cyan"
    Write-ColoredOutput "-----------------------------------------------" "Cyan"
    Write-ColoredOutput "Usage:" "White"
    Write-ColoredOutput "  -StartDspyApi     : Start the DSPy API server" "White"
    Write-ColoredOutput "  -Background       : Run server in background (with -StartDspyApi)" "White"
    Write-ColoredOutput "  -StopDspyApi      : Stop the DSPy API server" "White"
    Write-ColoredOutput "  -StartLmStudio    : Start LM Studio application" "White"
    Write-ColoredOutput "  -ListServers      : List all running servers" "White"
    Write-ColoredOutput "  -StopAll          : Stop all servers" "White"
    Write-ColoredOutput "" "White"
    Write-ColoredOutput "Examples:" "White"
    Write-ColoredOutput "  ./scripts/server_management.ps1 -StartDspyApi" "White"
    Write-ColoredOutput "  ./scripts/server_management.ps1 -StartDspyApi -Background" "White"
    Write-ColoredOutput "  ./scripts/server_management.ps1 -StopAll" "White"
    Write-ColoredOutput "  ./scripts/server_management.ps1 -ListServers" "White"
} 