#!/usr/bin/env bash

set -e

# A simple script to create a .deb package of the Brushshe application
echo 'WARNING: this script must be executed from the dev_tools folder!'
echo 'Before running this script, make sure that python3-pip is installed: sudo apt install python3-pip'
echo 'Continue (y/n)?'
read answer
if [ "$answer" == 'y' ]; then
	:
else
	exit 0
fi

echo 'Creating control file...'
mkdir -p brushshe/DEBIAN
cat <<EOF > brushshe/DEBIAN/control
Package: brushshe
Version: 2.0.0
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
cp ../Brushshe/icons/icon.png brushshe/usr/share/icons/hicolor/512x512/apps/brushshe.png

echo 'Creating a .desktop file...'
mkdir -p brushshe/usr/share/applications
cat <<EOF > brushshe/usr/share/applications/brushshe.desktop
[Desktop Entry]
Type=Application
Version=1.0
Name=Brushshe
Name[uk]=Брашше
Name[ru]=Брашше
Comment=Painting app
Comment[uk]=Програма для малювання
Comment[ru]=Программа для рисования
Exec=python3 /opt/Brushshe/brushshe.py %f
Icon=brushshe
Terminal=false
Categories=Graphics;
StartupWMClass=Brushshe
MimeType=image/png;image/jpeg;image/gif;image/bmp;image/tiff;image/webp;image/x-icon;image/x-portable-pixmap;image/x-portable-graymap;image/x-portable-bitmap;
EOF

echo 'Copying licenses and README...'
mkdir -p brushshe/usr/share/doc/brushshe
cp -a ../LICENSE brushshe/usr/share/doc/brushshe
cp -a ../LICENSE_CC0 brushshe/usr/share/doc/brushshe
cp -a ../README.md brushshe/usr/share/doc/brushshe

echo 'Installing customtkinter...'
pip install customtkinter --target=brushshe/opt/Brushshe
find . | grep -E "(__pycache__|\.pyc$)" | xargs rm -rf

echo 'Creating a .deb package...'
dpkg-deb --build ./brushshe

echo 'Removing the package folder and moving the .deb file from the project folder...'
rm -rf brushshe
mv brushshe.deb ../../
