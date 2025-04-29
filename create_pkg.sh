#!/bin/bash

# Configuration
APP_NAME="Nanamin"
APP_SUBTITLE="CBZ Optimizer"
VERSION="1.0.0"
PKG_NAME="${APP_NAME}-${VERSION}.pkg"
APP_PATH="dist/${APP_NAME}.app"
IDENTITY="Developer ID Installer: MARTIN KAJTAZI (YS8D2GW7DN)"
APP_IDENTITY="Developer ID Application: MARTIN KAJTAZI (YS8D2GW7DN)"
BUNDLE_ID="com.martinkajtazi.nanamin"

# Ensure the app bundle exists
if [ ! -d "${APP_PATH}" ]; then
    echo "Error: App bundle not found at ${APP_PATH}"
    exit 1
fi

# Create a temporary directory for the package
TEMP_DIR="dist/temp_pkg"
mkdir -p "${TEMP_DIR}"

# Copy the app to the temporary directory
cp -R "${APP_PATH}" "${TEMP_DIR}/"

# Ensure Info.plist is in the correct location
cp Info.plist "${TEMP_DIR}/${APP_NAME}.app/Contents/"

# Sign the app
codesign --force --options runtime --sign "${APP_IDENTITY}" --deep "${TEMP_DIR}/${APP_NAME}.app"

# Create the package
pkgbuild --root "${TEMP_DIR}" \
         --identifier "${BUNDLE_ID}" \
         --version "${VERSION}" \
         --install-location "/Applications" \
         "dist/${PKG_NAME}"

# Sign the package
productsign --sign "${IDENTITY}" \
            "dist/${PKG_NAME}" \
            "dist/${PKG_NAME}.signed"

# Move the signed package to the final name
mv "dist/${PKG_NAME}.signed" "dist/${PKG_NAME}"

# Notarize the package
xcrun notarytool submit "dist/${PKG_NAME}" \
    --apple-id "martin.kajtazi95@gmail.com" \
    --password "fgyd-wcnx-hsbl-kiiz" \
    --team-id "YS8D2GW7DN" \
    --wait

# Staple the notarization ticket
xcrun stapler staple "dist/${PKG_NAME}"

# Clean up temporary directory
rm -rf "${TEMP_DIR}"

echo "Package created and notarized: dist/${PKG_NAME}"

# Verify the package
spctl --assess --verbose=4 --type install "dist/${PKG_NAME}"

# Check available installer certificates
security find-identity -v -p installer 