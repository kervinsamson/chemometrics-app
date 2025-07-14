# IRIS-UPLB Chemometrics - Build Instructions

This document provides instructions for building the IRIS-UPLB Chemometrics application for different platforms.

## Prerequisites

- Python 3.8 or higher
- All dependencies listed in `requirements.txt`
- Platform-specific build tools (see below)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Building for Different Platforms

### Windows

For Windows, use the existing build system:

```powershell
# Build the application
.\build_installer.ps1

# Or build without installer
.\build_without_spec.ps1
```

The Windows build creates:
- An executable in `dist/IRIS/`
- An installer (`.exe`) in the `output/` directory

### macOS

For macOS, use the new macOS-specific build system:

```bash
# Make the build script executable
chmod +x build_macos.sh

# Build the application
./build_macos.sh

# Or use the Python build script
python3 build_macos.py
```

The macOS build creates:
- A `.app` bundle in `dist/IRIS.app`
- Optionally, a `.dmg` file for distribution

#### macOS-specific requirements:
- macOS 10.13 (High Sierra) or later
- Xcode Command Line Tools (for `sips` and `iconutil`)
- For DMG creation: `hdiutil` (included with macOS)

### Linux

For Linux, you can use PyInstaller directly:

```bash
# Build using the base spec file
python3 -m PyInstaller --clean IRIS_UPLB_Chemometrics.spec

# The result will be in dist/IRIS/
```

## Build Files

### Spec Files

- `IRIS_UPLB_Chemometrics.spec` - Windows/Linux spec file
- `IRIS_UPLB_Chemometrics_macOS.spec` - macOS-specific spec file with app bundle creation

### Build Scripts

- `build_installer.ps1` - Windows PowerShell build script with installer creation
- `build_without_spec.ps1` - Windows PowerShell build script without installer
- `build_macos.sh` - macOS Bash build script
- `build_macos.py` - Cross-platform Python build script for macOS

## Icon Files

The application supports different icon formats:
- `icon.ico` - Windows icon format
- `icon.icns` - macOS icon format (created automatically from .ico if not present)

## App Bundle Information (macOS)

The macOS app bundle includes:
- **Bundle Identifier**: `com.uplb.iris.chemometrics`
- **App Category**: Education
- **Minimum macOS Version**: 10.13 (High Sierra)
- **High DPI Support**: Yes
- **Dark Mode Support**: Yes

## Distribution

### Windows
- Distribute the installer `.exe` file
- Or distribute the entire `dist/IRIS/` folder

### macOS
- Distribute the `.app` bundle directly
- Or distribute the `.dmg` file for easier installation
- For wider distribution, consider code signing and notarization

### Linux
- Distribute the entire `dist/IRIS/` folder
- Consider creating a `.deb` or `.rpm` package for easier installation

## Code Signing (macOS)

For macOS distribution outside of personal use, you should sign the application:

```bash
# Sign the app bundle
codesign --force --deep --sign "Developer ID Application: Your Name" "dist/IRIS.app"

# Sign the DMG (if created)
codesign --force --sign "Developer ID Application: Your Name" "IRIS-macOS.dmg"
```

## Troubleshooting

### Missing Dependencies
If you encounter missing module errors, add them to the `hiddenimports` list in the appropriate spec file.

### Large Bundle Size
The app bundle may be large due to scientific libraries. This is normal for applications using NumPy, SciPy, and matplotlib.

### macOS Gatekeeper Issues
If users can't open the app due to Gatekeeper:
1. Right-click the app and select "Open"
2. Or use: `xattr -cr /path/to/IRIS.app`

### Permission Issues
Make sure build scripts have execute permissions:
```bash
chmod +x build_macos.sh
```

## Development Notes

- The application uses PySide6 for the GUI
- Scientific computing libraries: NumPy, SciPy, scikit-learn
- Data visualization: matplotlib
- Spectral data processing: spectrochempy

## Support

For build issues or questions, please refer to the main project documentation or create an issue in the project repository.
