#!/bin/bash

# Configuration
APP_NAME="Nanamin"
APP_SUBTITLE="CBZ Optimizer"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
APP_PATH="dist/${APP_NAME}.app"
DMG_DIR="dist/dmg"
DMG_TEMP="dist/temp.dmg"

# Create DMG directory
mkdir -p "${DMG_DIR}"

# Copy app to DMG directory
cp -R "${APP_PATH}" "${DMG_DIR}/"

# Create symbolic link to Applications
ln -s /Applications "${DMG_DIR}/Applications"

# Create the DMG
hdiutil create -volname "${APP_NAME} - ${APP_SUBTITLE}" -srcfolder "${DMG_DIR}" -ov -format UDZO "${DMG_TEMP}"

# Convert to final DMG with proper compression
hdiutil convert "${DMG_TEMP}" -format UDZO -imagekey zlib-level=9 -o "dist/${DMG_NAME}"

# Sign the DMG
codesign --force --options runtime --sign "Apple Development: martin.kajtazi95@gmail.com (3V3T4TQDVV)" "dist/${DMG_NAME}"

# Clean up
rm -rf "${DMG_DIR}"
rm "${DMG_TEMP}"

echo "DMG created: dist/${DMG_NAME}" 