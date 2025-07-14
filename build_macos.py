#!/usr/bin/env python3
"""
macOS build script for IRIS-UPLB Chemometrics application
This script builds the PyInstaller application and creates a .app bundle for macOS
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Configuration
APP_NAME = "IRIS"
SPEC_FILE = "IRIS_UPLB_Chemometrics_macOS.spec"
BUILD_DIR = "build"
DIST_DIR = "dist"

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔨 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"❌ Command output: {e.stderr}")
        sys.exit(1)

def check_requirements():
    """Check if all required tools are available"""
    print("🔍 Checking for required tools...")
    
    # Check Python
    try:
        import sys
        print(f"✅ Python {sys.version} found")
    except:
        print("❌ Python not found")
        sys.exit(1)
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller found")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller installed")

def create_icns_icon():
    """Create .icns icon file for macOS from .ico file"""
    if os.path.exists("icon.icns"):
        print("✅ icon.icns already exists")
        return
    
    if not os.path.exists("icon.ico"):
        print("⚠️  No icon.ico file found, proceeding without icon")
        return
    
    print("🎨 Converting icon.ico to icon.icns...")
    
    # On macOS, we can use sips
    if platform.system() == "Darwin":
        try:
            # Create iconset directory structure
            iconset_dir = "icon.iconset"
            os.makedirs(iconset_dir, exist_ok=True)
            
            # Generate different sizes
            sizes = [16, 32, 128, 256, 512, 1024]
            for size in sizes:
                output_file = f"{iconset_dir}/icon_{size}x{size}.png"
                subprocess.run([
                    "sips", "-z", str(size), str(size), "icon.ico", "--out", output_file
                ], check=True)
                
                # Create @2x versions for retina displays
                if size <= 512:
                    output_file_2x = f"{iconset_dir}/icon_{size}x{size}@2x.png"
                    subprocess.run([
                        "sips", "-z", str(size*2), str(size*2), "icon.ico", "--out", output_file_2x
                    ], check=True)
            
            # Create .icns file
            subprocess.run(["iconutil", "-c", "icns", iconset_dir], check=True)
            shutil.rmtree(iconset_dir)
            print("✅ Created icon.icns from icon.ico")
            
        except subprocess.CalledProcessError:
            print("⚠️  Failed to convert icon, using .ico file directly")
    else:
        print("⚠️  Not running on macOS, cannot create .icns file")

def clean_build():
    """Clean previous builds"""
    print("🧹 Cleaning previous builds...")
    for dir_name in [BUILD_DIR, DIST_DIR]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Removed {dir_name}")

def build_app():
    """Build the application using PyInstaller"""
    print(f"🔨 Building application with PyInstaller...")
    
    if not os.path.exists(SPEC_FILE):
        print(f"❌ Spec file not found: {SPEC_FILE}")
        sys.exit(1)
    
    cmd = f"{sys.executable} -m PyInstaller --clean {SPEC_FILE}"
    run_command(cmd, "Running PyInstaller")
    
    # Check if app bundle was created
    app_bundle = os.path.join(DIST_DIR, f"{APP_NAME}.app")
    if not os.path.exists(app_bundle):
        print(f"❌ App bundle not found at {app_bundle}")
        sys.exit(1)
    
    print(f"✅ App bundle created at: {app_bundle}")
    
    # Get app bundle size
    try:
        import shutil
        size = shutil.disk_usage(app_bundle).used
        size_mb = size / (1024 * 1024)
        print(f"📦 App bundle size: {size_mb:.1f} MB")
    except:
        print("📦 App bundle created (size unknown)")
    
    return app_bundle

def create_dmg(app_bundle):
    """Create a DMG file for distribution (macOS only)"""
    if platform.system() != "Darwin":
        print("⚠️  DMG creation is only available on macOS")
        return
    
    print("💿 Creating DMG file for distribution...")
    
    dmg_name = f"{APP_NAME}-macOS.dmg"
    dmg_dir = "dmg_temp"
    
    # Remove existing DMG
    if os.path.exists(dmg_name):
        os.remove(dmg_name)
    
    # Create temporary directory for DMG contents
    if os.path.exists(dmg_dir):
        shutil.rmtree(dmg_dir)
    os.makedirs(dmg_dir)
    
    # Copy app bundle to DMG directory
    shutil.copytree(app_bundle, os.path.join(dmg_dir, f"{APP_NAME}.app"))
    
    # Create symlink to Applications folder
    os.symlink("/Applications", os.path.join(dmg_dir, "Applications"))
    
    # Create DMG
    try:
        cmd = f'hdiutil create -volname "{APP_NAME}" -srcfolder "{dmg_dir}" -ov -format UDZO "{dmg_name}"'
        run_command(cmd, "Creating DMG")
        
        # Clean up temporary directory
        shutil.rmtree(dmg_dir)
        
        if os.path.exists(dmg_name):
            size = os.path.getsize(dmg_name) / (1024 * 1024)
            print(f"✅ DMG created: {dmg_name} ({size:.1f} MB)")
            return dmg_name
            
    except Exception as e:
        print(f"⚠️  DMG creation failed: {e}")
        if os.path.exists(dmg_dir):
            shutil.rmtree(dmg_dir)

def main():
    """Main build function"""
    print("🍎 Building macOS application bundle for IRIS-UPLB Chemometrics")
    print("=" * 60)
    
    check_requirements()
    create_icns_icon()
    clean_build()
    app_bundle = build_app()
    
    # Create DMG on macOS
    dmg_file = create_dmg(app_bundle)
    
    print("\n" + "=" * 60)
    print("🎉 Build completed successfully!")
    print(f"📍 App bundle location: {app_bundle}")
    print(f"🚀 To run the app: open {app_bundle}")
    
    if dmg_file:
        print(f"📦 DMG file: {dmg_file}")
    
    print("\n📋 Distribution notes:")
    print("   • The .app bundle can be distributed directly")
    print("   • For App Store distribution, you'll need to sign the bundle")
    print("   • For notarization, additional steps are required")
    
    print("\n🔧 To sign the app bundle (if you have a Developer ID):")
    print(f'   codesign --force --deep --sign "Developer ID Application: Your Name" "{app_bundle}"')
    
    if dmg_file:
        print("\n📦 To sign the DMG:")
        print(f'   codesign --force --sign "Developer ID Application: Your Name" "{dmg_file}"')

if __name__ == "__main__":
    main()
