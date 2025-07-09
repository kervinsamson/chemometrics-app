# IRIS UPLB Chemometrics Application - Distribution Guide

## Building the Application

### Prerequisites
- Python 3.9 or later
- All dependencies listed in `requirements.txt`

### Build Process

#### Option 1: Using PowerShell (Recommended)
```powershell
.\build_app.ps1
```

#### Option 2: Using Batch File
```cmd
build_app.bat
```

#### Option 3: Manual Build
```cmd
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build the application
pyinstaller --clean IRIS_UPLB_Chemometrics.spec
```

## After Building

1. The executable will be created in `dist/IRIS_UPLB_Chemometrics/`
2. You can run the app using:
   - `IRIS_UPLB_Chemometrics.exe` (directly)
   - `Launch_App.bat` (convenient launcher)

## Distribution

To distribute your application:

1. Copy the entire `dist/IRIS_UPLB_Chemometrics/` folder
2. Users can run `Launch_App.bat` or `IRIS_UPLB_Chemometrics.exe`
3. No Python installation required on target machines

## Troubleshooting

### Common Issues:

1. **Missing modules**: Add them to `hiddenimports` in the spec file
2. **Data files not found**: Ensure they're listed in `datas` in the spec file
3. **Large file size**: Consider excluding unnecessary modules in `excludes`

### Build Optimization:

- Use `--onefile` for a single executable (slower startup)
- Use `--windowed` to hide console window
- Add `--icon=icon.ico` for custom icon

### Testing the Build:

Always test the built application on a clean machine without Python installed to ensure all dependencies are properly bundled.

## File Structure After Build

```
dist/IRIS_UPLB_Chemometrics/
├── IRIS_UPLB_Chemometrics.exe    # Main executable
├── Launch_App.bat                # Convenient launcher
├── _internal/                    # Internal PyInstaller files
├── spa_data/                     # Your SPA data files
├── Cassava (HCN)/               # Cassava data files
├── Spectral data/               # Spectral data files
└── RICE_NITROGEN_PROJECT.pkl    # Model file
```
