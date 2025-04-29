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

# Sign all binaries recursively
find dist/Nanamin.app -type f -name "*.so" -o -name "*.dylib" | while read -r binary; do
    codesign --force --options runtime --timestamp --sign "Developer ID Application: MARTIN KAJTAZI (YS8D2GW7DN)" "$binary"
done

# Sign frameworks
find dist/Nanamin.app/Contents/Frameworks -type f -name "Python" -o -name "Qt*" | while read -r framework; do
    codesign --force --options runtime --timestamp --sign "Developer ID Application: MARTIN KAJTAZI (YS8D2GW7DN)" "$framework"
done

# Sign the app bundle
codesign --force --options runtime --timestamp --entitlements entitlements.plist --sign "Developer ID Application: MARTIN KAJTAZI (YS8D2GW7DN)" dist/Nanamin.app

# Create DMG
./create_dmg.sh 