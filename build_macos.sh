#!/bin/bash
# macOS build script for IRIS-UPLB Chemometrics application
# This script builds the PyInstaller application and creates a .app bundle

set -e  # Exit on any error

# Configuration
APP_NAME="IRIS"
SPEC_FILE="IRIS_UPLB_Chemometrics_macOS.spec"
BUILD_DIR="build"
DIST_DIR="dist"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"

echo "🍎 Building macOS application bundle for $APP_NAME"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo "🔍 Checking for required tools..."

if ! command_exists python3; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

if ! command_exists pip3; then
    echo "❌ pip3 is not installed or not in PATH"
    exit 1
fi

echo "✅ All required tools are available"

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$BUILD_DIR"
rm -rf "$DIST_DIR"

# Create icon file for macOS if it doesn't exist
if [ ! -f "icon.icns" ] && [ -f "icon.ico" ]; then
    echo "🎨 Converting icon.ico to icon.icns for macOS..."
    if command_exists sips; then
        # Use macOS built-in sips tool
        mkdir -p icon.iconset
        sips -z 16 16 icon.ico --out icon.iconset/icon_16x16.png
        sips -z 32 32 icon.ico --out icon.iconset/icon_16x16@2x.png
        sips -z 32 32 icon.ico --out icon.iconset/icon_32x32.png
        sips -z 64 64 icon.ico --out icon.iconset/icon_32x32@2x.png
        sips -z 128 128 icon.ico --out icon.iconset/icon_128x128.png
        sips -z 256 256 icon.ico --out icon.iconset/icon_128x128@2x.png
        sips -z 256 256 icon.ico --out icon.iconset/icon_256x256.png
        sips -z 512 512 icon.ico --out icon.iconset/icon_256x256@2x.png
        sips -z 512 512 icon.ico --out icon.iconset/icon_512x512.png
        sips -z 1024 1024 icon.ico --out icon.iconset/icon_512x512@2x.png
        iconutil -c icns icon.iconset
        rm -rf icon.iconset
        echo "✅ Created icon.icns from icon.ico"
    else
        echo "⚠️  sips not found, using icon.ico directly"
    fi
fi

# Build the application
echo "🔨 Building application with PyInstaller..."
python3 -m PyInstaller --clean "$SPEC_FILE"

# Verify the app bundle was created
if [ ! -d "$APP_BUNDLE" ]; then
    echo "❌ App bundle not found at $APP_BUNDLE"
    exit 1
fi

echo "✅ App bundle created at: $APP_BUNDLE"

# Get app bundle size
APP_SIZE=$(du -sh "$APP_BUNDLE" | cut -f1)
echo "📦 App bundle size: $APP_SIZE"

# Optional: Create a DMG file for distribution
if command_exists hdiutil; then
    echo "💿 Creating DMG file for distribution..."
    DMG_NAME="$APP_NAME-macOS.dmg"
    rm -f "$DMG_NAME"
    
    # Create temporary directory for DMG contents
    DMG_DIR="dmg_temp"
    rm -rf "$DMG_DIR"
    mkdir "$DMG_DIR"
    
    # Copy app bundle to DMG directory
    cp -R "$APP_BUNDLE" "$DMG_DIR/"
    
    # Create symlink to Applications folder
    ln -s /Applications "$DMG_DIR/Applications"
    
    # Create DMG
    hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_NAME"
    
    # Clean up temporary directory
    rm -rf "$DMG_DIR"
    
    if [ -f "$DMG_NAME" ]; then
        DMG_SIZE=$(du -sh "$DMG_NAME" | cut -f1)
        echo "✅ DMG created: $DMG_NAME ($DMG_SIZE)"
    fi
else
    echo "⚠️  hdiutil not found, skipping DMG creation"
fi

# Display final information
echo ""
echo "🎉 Build completed successfully!"
echo "📍 App bundle location: $APP_BUNDLE"
echo "🚀 To run the app: open $APP_BUNDLE"
echo ""
echo "📋 Distribution notes:"
echo "   • The .app bundle can be distributed directly"
echo "   • For App Store distribution, you'll need to sign the bundle"
echo "   • For notarization, additional steps are required"
echo ""
echo "🔧 To sign the app bundle (if you have a Developer ID):"
echo "   codesign --force --deep --sign \"Developer ID Application: Your Name\" \"$APP_BUNDLE\""
echo ""
echo "📦 To create a signed DMG:"
echo "   codesign --force --sign \"Developer ID Application: Your Name\" \"$DMG_NAME\""
