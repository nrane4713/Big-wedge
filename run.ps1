<#
.SYNOPSIS
    Sets up and runs the oncall agent end to end.

.DESCRIPTION
    Creates a virtual environment if needed, installs dependencies, fetches
    wiki articles, builds the vector index, and launches the Chainlit app.

.EXAMPLE
    ./run.ps1
    ./run.ps1 -SkipFetch -SkipIndex   # just relaunch the chat UI
#>

param(
    [switch]$SkipFetch,
    [switch]$SkipIndex
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv) ..."
    python -m venv .venv
}

Write-Host "Activating virtual environment ..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies ..."
pip install -e . | Out-Null

if (-not (Test-Path ".env")) {
    Write-Host "No .env found. Copying .env.example -> .env"
    Write-Host "Fill in your credentials in .env before continuing."
    Copy-Item ".env.example" ".env"
    exit 1
}

if (-not $SkipFetch) {
    Write-Host "Fetching wiki articles ..."
    python fetch_articles.py
}

if (-not $SkipIndex) {
    Write-Host "Building vector index ..."
    python build_index.py
}

Write-Host "Launching Chainlit app ..."
chainlit run app.py -w
