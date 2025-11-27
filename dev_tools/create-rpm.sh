#!/usr/bin/env bash

set -e

# Script for creating .rpm package Brushshe
echo 'WARNING: this script must be executed from the dev_tools folder!'
echo 'To build the package you need rpmbuild.'
echo 'To build for Fedora or Mageia you need pip.'
echo 'Enter the distribution for which you want to create an .rpm package [Fedora/Mageia/OpenMandriva]:'
read distro

if [ "$distro" == 'Fedora' ]; then
	requires='python3 python3-tkinter python3-pillow python3-pillow-tk'
elif [ "$distro" == 'Mageia' ]; then
	requires='python3 tkinter3 python3-pillow python3-pillow-tk'
elif [ "$distro" == 'OpenMandriva' ]; then
	requires='python python-customtkinter python-imaging'
else
	echo 'Unsupported distribution or typo'
	exit 1
fi
release_name="${distro,,}"
if [ "$distro" != 'OpenMandriva' ]; then
	licenses='MPL-2.0 AND CC0-1.0 AND (MPL-2.0 OR CC-BY-4.0) AND OFL-1.1-no-RFN AND OFL-1.1-RFN AND MIT AND Apache-2.0 AND BSD-3-Clause AND (Apache-2.0 OR BSD-2-Clause)'
else
	licenses='MPL-2.0 AND CC0-1.0 AND (MPL-2.0 OR CC-BY-4.0) AND OFL-1.1-no-RFN AND OFL-1.1-RFN'
fi

echo 'Creating a .desktop file...'
cat <<EOF > brushshe.desktop
[Desktop Entry]
Type=Application
Version=1.0
Name=Brushshe
Name[uk]=Брашше
Name[ru]=Брашше
Comment=Painting app
Comment[uk]=Програма для малювання
Comment[ru]=Программа для рисования
Comment[de]=Mal-App
Comment[hi]=पेंटिंग ऐप
Exec=python3 /opt/Brushshe/brushshe.py %f
Icon=brushshe
Terminal=false
Categories=Graphics;
StartupWMClass=Brushshe
MimeType=image/png;image/jpeg;image/gif;image/bmp;image/vnd.ms-dds;image/x-bmp;image/x-eps;image/x-icns;image/x-icon;image/im;image/mpo;image/x-pcx;image/x-portable-pixmap;image/x-sgi;image/x-tga;image/tiff;image/webp;
EOF

echo 'Creating spec file...'
cat <<EOF > brushshe.spec
Name:           brushshe
Version:        2.4.0
Release:        1.$release_name
Summary:        Raster graphical editor
Summary(uk):    Растровий графічний редактор
Summary(ru):    Растровый графический редактор
License:        $licenses
Source0:        brushshe.tar
BuildArch:      noarch
URL:            https://github.com/limafresh/Brushshe
Requires:       $requires

%description
Brushshe is a simple and user-friendly raster graphics editor.

%description -l uk
Брашше - простий і дружній до користувача растровий графічний редактор.

%description -l ru
Брашше - простой и дружественный к пользователю растровый графический редактор.

%prep
%setup -q -n brushshe

%install
mkdir -p %{buildroot}/opt
cp -r Brushshe %{buildroot}/opt

mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
cp brushshe.png %{buildroot}/usr/share/icons/hicolor/256x256/apps

mkdir -p %{buildroot}/usr/share/applications
cp brushshe.desktop %{buildroot}/usr/share/applications

mkdir -p %{buildroot}/usr/share/doc/brushshe
cp LICENSE LICENSE_CC0 README.md %{buildroot}/usr/share/doc/brushshe

%files
/opt/Brushshe
/usr/share/icons/hicolor/256x256/apps/brushshe.png
/usr/share/applications/brushshe.desktop
/usr/share/doc/brushshe/LICENSE
/usr/share/doc/brushshe/LICENSE_CC0
/usr/share/doc/brushshe/README.md
EOF

echo 'Creating a folder for packaging into a tarball...'
mkdir brushshe
cp -r ../Brushshe brushshe/Brushshe
cp ../README.md ../LICENSE ../LICENSE_CC0 brushshe
cp ../Brushshe/icons/icon.png brushshe/brushshe.png
mv brushshe.desktop brushshe.spec brushshe

if [ "$distro" != 'OpenMandriva' ]; then
	echo 'Installing customtkinter...'
	pip install customtkinter --target=brushshe/Brushshe
fi

echo 'Creating tarball...'
find . | grep -E "(__pycache__|\.pyc$)" | xargs rm -rf
tar -cvf brushshe.tar brushshe

echo 'Creating .rpm package...'
rpmbuild -tb brushshe.tar --define "_topdir $PWD"

echo 'Deleting files and folders created during the build process and moving the .rpm package from the project folder...'
mv RPMS/noarch/* ../../
rm -rf BUILD BUILDROOT SPECS RPMS SRPMS brushshe
rm brushshe.tar 
