# Load this project's .env into the current PowerShell session.
# Usage: . .\setup-env.ps1
[CmdletBinding()]
param(
    [string]$EnvFile
)

if ([string]::IsNullOrWhiteSpace($EnvFile)) {
    $environmentDirectory = $PSScriptRoot
    if ([string]::IsNullOrWhiteSpace($environmentDirectory)) {
        $environmentDirectory = (Get-Location).Path
    }
    $EnvFile = Join-Path $environmentDirectory '.env'
}

function Import-ProjectEnvironment {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'Missing .env. Copy .env.example to .env and configure your API key.'
    }

    $settings = @{}
    $lineNumber = 0
    foreach ($line in [IO.File]::ReadAllLines((Resolve-Path -LiteralPath $Path).Path)) {
        $lineNumber++
        if ($line -match '^\s*(#.*)?$') { continue }
        if ($line -notmatch '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
            throw "Invalid .env syntax at line $lineNumber. Expected NAME=value."
        }

        $variableName = $matches[1]
        $variableValue = $matches[2]
        if ($variableValue.Length -ge 2) {
            $first = $variableValue[0]
            $last = $variableValue[$variableValue.Length - 1]
            if (($first -eq [char]34 -and $last -eq [char]34) -or
                ($first -eq [char]39 -and $last -eq [char]39)) {
                $variableValue = $variableValue.Substring(1, $variableValue.Length - 2)
            }
        }
        $settings[$variableName] = $variableValue
    }

    foreach ($requiredName in @('PROVIDER', 'MODEL')) {
        if ([string]::IsNullOrWhiteSpace($settings[$requiredName])) {
            throw "Missing $requiredName in .env."
        }
    }
    if ($settings['PROVIDER'] -eq 'openrouter' -and
        ([string]::IsNullOrWhiteSpace($settings['OPENROUTER_API_KEY']) -or
         $settings['OPENROUTER_API_KEY'] -eq 'YOUR_KEY')) {
        throw 'Configure OPENROUTER_API_KEY in .env before loading it.'
    }

    foreach ($variableName in $settings.Keys) {
        [Environment]::SetEnvironmentVariable($variableName, $settings[$variableName], 'Process')
    }
    Write-Host ('Environment loaded: PROVIDER={0}; MODEL={1}. API keys are hidden.' -f
        $settings['PROVIDER'], $settings['MODEL'])
}

Import-ProjectEnvironment -Path $EnvFile
