#!/usr/bin/env bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

set -e

# A simple script to create a .deb package of the Brushshe application
echo 'WARNING: this script must be executed from the dev_tools folder!'
echo 'Before running this script, make sure that python3-pip is installed: sudo apt install python3-pip'
echo 'Continue (y/n)?'
read answer
if [ "$answer" != 'y' ]; then exit 0; fi

echo 'Creating control file...'
mkdir -p brushshe/DEBIAN
cat <<EOF > brushshe/DEBIAN/control
Package: brushshe
Version: 2.5.0
Section: graphics
Priority: optional
Depends: python3, python3-tk, python3-pil, python3-pil.imagetk
Architecture: all
Essential: no
Installed-Size: 5132
Maintainer: limafresh <173814432+limafresh@users.noreply.github.com>
Description: Raster graphical editor
EOF

echo 'Copying program files...'
mkdir -p brushshe/opt
cp -r ../Brushshe brushshe/opt

echo 'Copying the icon...'
mkdir -p brushshe/usr/share/icons/hicolor/512x512/apps
cp ../Brushshe/assets/icons/icon.png brushshe/usr/share/icons/hicolor/512x512/apps/brushshe.png

echo 'Copying the .desktop file...'
mkdir -p brushshe/usr/share/applications
cp brushshe.desktop brushshe/usr/share/applications/brushshe.desktop

echo 'Copying licenses and README...'
mkdir -p brushshe/usr/share/doc/brushshe
cp ../LICENSE brushshe/usr/share/doc/brushshe
cp ../LICENSE-CC0 brushshe/usr/share/doc/brushshe
cp ../README.md brushshe/usr/share/doc/brushshe

echo 'Installing customtkinter...'
pip install customtkinter --target=brushshe/opt/Brushshe
find . | grep -E "(__pycache__|\.pyc$)" | xargs rm -rf

echo 'Creating a .deb package...'
dpkg-deb --build ./brushshe

echo 'Removing the package folder and moving the .deb file from the project folder...'
rm -rf brushshe
mv brushshe.deb ../../
