# PowerShell script to build installer using Inno Setup
# This script builds the PyInstaller application and creates an installer

param(
    [switch]$Clean = $false,
    [switch]$SkipBuild = $false,
    [switch]$OpenOutput = $true
)

# Set error handling
$ErrorActionPreference = "Stop"

# Configuration
$AppName = "IRIS"
$BuildDir = "build"
$DistDir = "dist"
$OutputDir = "output"
$InnoScript = "installer.iss"

Write-Host "Building installer for $AppName using Inno Setup" -ForegroundColor Green

# Function to check if a command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to find Inno Setup
function Find-InnoSetup {
    $InnoSetupPaths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 5\ISCC.exe"
    )
    
    foreach ($Path in $InnoSetupPaths) {
        if (Test-Path $Path) {
            Write-Host "Found Inno Setup at: $Path" -ForegroundColor Green
            return $Path
        }
    }
    
    return $null
}

# Check for required tools
Write-Host "Checking for required tools..." -ForegroundColor Yellow

# Check for Python
if (-not (Test-Command "python")) {
    Write-Error "Python is not installed or not in PATH"
    exit 1
}

# Check for Inno Setup
$InnoSetupPath = Find-InnoSetup
if ($null -eq $InnoSetupPath) {
    Write-Host "Inno Setup not found. Please install Inno Setup from:" -ForegroundColor Red
    Write-Host "https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "After installation, run this script again." -ForegroundColor Yellow
    
    # Try to open the download page
    try {
        Start-Process "https://jrsoftware.org/isdl.php"
    } catch {
        Write-Host "Failed to open browser. Please manually visit the URL above." -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "All required tools are available" -ForegroundColor Green

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
    if (Test-Path $OutputDir) { Remove-Item -Recurse -Force $OutputDir }
}

# Create output directory
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Step 1: Build the application with PyInstaller (unless skipped)
if (-not $SkipBuild) {
    Write-Host "Building application with PyInstaller..." -ForegroundColor Yellow
    
    # Use the spec file if it exists, otherwise use the build script
    if (Test-Path "IRIS_UPLB_Chemometrics.spec") {
        Write-Host "Using spec file..." -ForegroundColor Cyan
        $BuildCommand = "python -m PyInstaller --clean IRIS_UPLB_Chemometrics.spec"
    } elseif (Test-Path "build_without_spec.ps1") {
        Write-Host "Using build script..." -ForegroundColor Cyan
        .\build_without_spec.ps1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Build script failed"
            exit 1
        }
    } else {
        Write-Error "Neither IRIS_UPLB_Chemometrics.spec nor build_without_spec.ps1 found"
        exit 1
    }
    
    # Only run PyInstaller if we used the spec file
    if (Test-Path "IRIS_UPLB_Chemometrics.spec") {
        Write-Host "Running PyInstaller..." -ForegroundColor Cyan
        try {
            Invoke-Expression $BuildCommand
            if ($LASTEXITCODE -ne 0) {
                Write-Error "PyInstaller build failed"
                exit 1
            }
        } catch {
            Write-Error "PyInstaller build failed: $_"
            exit 1
        }
    }
    
    Write-Host "PyInstaller build completed successfully" -ForegroundColor Green
}

# Verify the built application exists
$AppPath = Join-Path $DistDir $AppName
if (-not (Test-Path $AppPath)) {
    Write-Error "Built application not found at $AppPath"
    Write-Host "Expected structure: $AppPath\$AppName.exe" -ForegroundColor Yellow
    exit 1
}

Write-Host "Application found at: $AppPath" -ForegroundColor Green

# Step 2: Build the installer with Inno Setup
Write-Host "Building installer with Inno Setup..." -ForegroundColor Yellow

if (-not (Test-Path $InnoScript)) {
    Write-Error "Inno Setup script not found: $InnoScript"
    exit 1
}

Write-Host "Running Inno Setup Compiler..." -ForegroundColor Cyan
try {
    $InnoCommand = "`"$InnoSetupPath`" `"$InnoScript`""
    Write-Host "Command: $InnoCommand" -ForegroundColor Gray
    
    $InnoResult = cmd /c $InnoCommand 2>&1
    Write-Host "Inno Setup Output:" -ForegroundColor Gray
    Write-Host $InnoResult -ForegroundColor Gray
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Inno Setup compilation failed with exit code $LASTEXITCODE"
        Write-Error "Output: $InnoResult"
        exit 1
    }
    
    Write-Host "Inno Setup compilation completed successfully" -ForegroundColor Green
    
} catch {
    Write-Error "Inno Setup compilation failed: $_"
    exit 1
}

# Check for the generated installer
$InstallerPattern = Join-Path $OutputDir "*Setup*.exe"
$GeneratedInstallers = Get-ChildItem -Path $InstallerPattern -ErrorAction SilentlyContinue

if ($GeneratedInstallers.Count -eq 0) {
    Write-Error "No installer found in output directory"
    Write-Host "Looking for files in $OutputDir..." -ForegroundColor Yellow
    Get-ChildItem $OutputDir | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
    exit 1
}

$InstallerPath = $GeneratedInstallers[0].FullName
$InstallerSize = (Get-Item $InstallerPath).Length
$InstallerSizeMB = [math]::Round($InstallerSize / 1MB, 2)

Write-Host "Installer created successfully!" -ForegroundColor Green
Write-Host "Location: $InstallerPath" -ForegroundColor Green
Write-Host "Size: $InstallerSizeMB MB" -ForegroundColor Green

# Copy to root directory for convenience
$RootInstallerName = "$AppName-Setup.exe"
$RootInstallerPath = Join-Path (Get-Location) $RootInstallerName
Copy-Item $InstallerPath $RootInstallerPath -Force
Write-Host "Installer copied to: $RootInstallerPath" -ForegroundColor Green

# Optional: Open the output directory
if ($OpenOutput) {
    Write-Host "Opening output directory..." -ForegroundColor Yellow
    Start-Process -FilePath "explorer.exe" -ArgumentList $OutputDir
}

Write-Host "`nBuild process completed successfully!" -ForegroundColor Green
Write-Host "You can now run the installer: $RootInstallerPath" -ForegroundColor Cyan
Write-Host "`nTo install silently: `"$RootInstallerPath`" /SILENT" -ForegroundColor Cyan
Write-Host "To install with minimal UI: `"$RootInstallerPath`" /VERYSILENT" -ForegroundColor Cyan