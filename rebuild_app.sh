#!/bin/bash

# Clean up previous build
rm -rf build dist

# Build the app
pyinstaller Nanamin.spec

# Create plugins directories
mkdir -p dist/Nanamin.app/Contents/PlugIns/styles/
mkdir -p dist/Nanamin.app/Contents/PlugIns/platforms/

# Copy Info.plist
cp Info.plist dist/Nanamin.app/Contents/

# Patch Info.plist to ensure icon is set
if /usr/libexec/PlistBuddy -c "Print :CFBundleIconFile" dist/Nanamin.app/Contents/Info.plist 2>/dev/null; then
  /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile nanamin_icon" dist/Nanamin.app/Contents/Info.plist
else
  /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string nanamin_icon" dist/Nanamin.app/Contents/Info.plist
fi

# Copy Qt plugins
cp -R /opt/homebrew/Cellar/qt/6.9.0/share/qt/plugins/styles/libqmacstyle.dylib dist/Nanamin.app/Contents/PlugIns/styles/
cp -R /opt/homebrew/Cellar/qt/6.9.0/share/qt/plugins/platforms/libqcocoa.dylib dist/Nanamin.app/Contents/PlugIns/platforms/

# Sign the plugins
codesign --force --options runtime --sign "Apple Development: martin.kajtazi95@gmail.com (3V3T4TQDVV)" dist/Nanamin.app/Contents/PlugIns/styles/libqmacstyle.dylib
codesign --force --options runtime --sign "Apple Development: martin.kajtazi95@gmail.com (3V3T4TQDVV)" dist/Nanamin.app/Contents/PlugIns/platforms/libqcocoa.dylib

# Re-sign the app
codesign --force --options runtime --entitlements entitlements.plist --sign "Apple Development: martin.kajtazi95@gmail.com (3V3T4TQDVV)" dist/Nanamin.app

# Create DMG
./create_dmg.sh 