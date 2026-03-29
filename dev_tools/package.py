# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request

script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(script_dir) != "dev_tools" or script_dir != os.getcwd():
    raise RuntimeError("ERROR: This script must be executed from the dev_tools folder!")
    sys.exit(1)

version = "2.6.0"
windows_python_license_path = None
venv_python = None

linux_desktop_file = """[Desktop Entry]
Type=Application
Version=1.0
Name=Brushshe
Name[uk]=Брашше
Name[ru]=Брашше
Comment=Painting app
Comment[uk]=Програма для малювання
Comment[ru]=Программа для рисования
Comment[de]=Mal-App
Comment[it]=Programma di disegno
Comment[hi]=पेंटिंग ऐप
Exec=python3 /opt/Brushshe/main.py %f
Icon=brushshe
Terminal=false
Categories=Graphics;
StartupWMClass=Brushshe
MimeType=image/png;image/jpeg;image/gif;image/bmp;image/vnd.ms-dds;image/x-bmp;image/x-eps;image/x-icns;image/x-icon;image/im;image/mpo;image/x-pcx;image/x-portable-pixmap;image/x-sgi;image/x-tga;image/tiff;image/webp;
"""

linux_deb_control = f"""Package: brushshe
Version: {version}
Section: graphics
Priority: optional
Depends: python3, python3-tk, python3-pil, python3-pil.imagetk
Architecture: all
Essential: no
Installed-Size: 5132
Maintainer: limafresh <173814432+limafresh@users.noreply.github.com>
Description: Raster graphical editor
"""


def install_customtkinter_to_dir(target_dir):
    print("Installing customtkinter...")
    subprocess.run(["pip", "install", "customtkinter", f"--target={target_dir}"])
    subprocess.run(r'find . | grep -E "(__pycache__|\.pyc$)" | xargs rm -rf', shell=True)


def windows_prepare():
    global venv_python, windows_python_license_path

    print("Creating a virtual environment...")
    subprocess.run(["python", "-m", "venv", "brenv"])
    venv_dir = "brenv"
    venv_python = os.path.join(venv_dir, "Scripts", "python.exe")

    print("Installing dependencies...")
    subprocess.run([venv_python, "-m", "pip", "install", "pyinstaller", "pip-licenses", "pillow", "customtkinter"])

    print("Creating a file with licenses...")
    subprocess.run(
        [
            venv_python,
            "-m",
            "piplicenses",
            "--format=plain-vertical",
            "--with-license-file",
            "--no-license-path",
            "--no-version",
            "--from=mixed",
            "--with-system",
            "--output-file=dependencies-licenses.txt",
        ]
    )
    with open("dependencies-licenses.txt", "a", encoding="utf8") as f:
        f.write(
            "\n\nThis exe file (Brushshe) uses dependencies that are dual-licensed under GPL/LGPL "
            "or permissive licenses (e.g., Apache, BSD). "
            "In all such cases, the permissive license has been selected."
        )

    print("Obtaining licenses for Python...")
    with urllib.request.urlopen("https://docs.python.org/3/license.html") as response:
        html = response.read().decode("utf-8")
    with open("python-licenses.html", "w", encoding="utf-8") as f:
        f.write(html)
    windows_python_license_path = os.path.abspath(os.path.join(sys.base_prefix, "LICENSE.txt"))


def windows_common_cleaning():
    for d in ["dist", "build", "brenv"]:
        shutil.rmtree(d)
    for f in ["dependencies-licenses.txt", "python-licenses.html"]:
        os.remove(f)


parser = argparse.ArgumentParser(description="Script for packaging Brushshe for different systems")
parser.add_argument("--deb", action="store_true", help="Create DEB")
parser.add_argument("--rpm", action="store_true", help="Create RPM")
parser.add_argument("--exe", action="store_true", help="Create EXE")
parser.add_argument("--portable-exe", action="store_true", help="Create portable EXE")

args = parser.parse_args()
if args.deb:
    print("Before running this script, make sure that python3-pip is installed: sudo apt install python3-pip")
    answer = input("Continue (y/n)?")
    if answer != "y":
        sys.exit(1)

    print("Creating control file...")
    os.makedirs("brushshe/DEBIAN")
    with open("brushshe/DEBIAN/control", "w", encoding="utf-8") as f:
        f.write(linux_deb_control)

    print("Copying program files...")
    shutil.copytree("../Brushshe", "brushshe/opt")

    print("Copying the icon...")
    os.makedirs("brushshe/usr/share/icons/hicolor/512x512/apps")
    shutil.copy("../Brushshe/assets/icons/icon.png", "brushshe/usr/share/icons/hicolor/512x512/apps/brushshe.png")

    print("Creating the .desktop file...")
    os.makedirs("brushshe/usr/share/applications")
    with open("brushshe/usr/share/applications/brushshe.desktop", "w", encoding="utf-8") as f:
        f.write(linux_desktop_file)

    print("Copying licenses and README...")
    os.makedirs("brushshe/usr/share/doc/brushshe")
    for f in ["../LICENSE", "../LICENSE-CC0", "../README.md"]:
        shutil.copy(f, "brushshe/usr/share/doc/brushshe")

    install_customtkinter_to_dir("brushshe/opt/Brushshe")

    print("Creating a .deb package...")
    subprocess.run(["dpkg-deb", "--build", "./brushshe"])

    print("Removing the package folder and moving the .deb file from the project folder...")
    shutil.rmtree("brushshe")
    shutil.move("brushshe.deb", "../../")
elif args.rpm:
    print("To build the package you need rpmbuild.")
    print("To build for Fedora or Mageia you need pip.")
    distro = input("Enter the distribution for which you want to create an .rpm package [Fedora/Mageia/OpenMandriva]:")
    if distro == "Fedora":
        requires = "python3 python3-tkinter python3-pillow python3-pillow-tk"
    elif distro == "Mageia":
        requires = "python3 tkinter3 python3-pillow python3-pillow-tk"
    elif distro == "OpenMandriva":
        requires = "python python-customtkinter python-imaging"
    else:
        print("Unsupported distribution or typo")
        sys.exit(1)

    basic_licenses = "MPL-2.0 AND CC0-1.0 AND OFL-1.1-no-RFN AND OFL-1.1-RFN"
    if distro != "OpenMandriva":
        licenses = basic_licenses + " AND MIT AND Apache-2.0 AND BSD-3-Clause AND (Apache-2.0 OR BSD-2-Clause)"
    else:
        licenses = basic_licenses

    linux_rpm_spec = f"""Name:           brushshe
Version:        {version}
Release:        1.{distro.lower()}
Summary:        Raster graphical editor
Summary(uk):    Растровий графічний редактор
Summary(ru):    Растровый графический редактор
License:        {licenses}
Source0:        brushshe.tar
BuildArch:      noarch
URL:            https://github.com/limafresh/Brushshe
Requires:       {requires}

%description
Brushshe is a simple and user-friendly raster graphics editor.

%description -l uk
Брашше - простий і дружній до користувача растровий графічний редактор.

%description -l ru
Брашше - простой и дружественный к пользователю растровый графический редактор.

%prep
%setup -q -n brushshe

%install
mkdir -p %{{buildroot}}/opt
cp -r Brushshe %{{buildroot}}/opt

mkdir -p %{{buildroot}}/usr/share/icons/hicolor/512x512/apps
cp brushshe.png %{{buildroot}}/usr/share/icons/hicolor/512x512/apps

mkdir -p %{{buildroot}}/usr/share/applications
cp brushshe.desktop %{{buildroot}}/usr/share/applications

mkdir -p %{{buildroot}}/usr/share/doc/brushshe
cp LICENSE LICENSE-CC0 README.md %{{buildroot}}/usr/share/doc/brushshe

%files
/opt/Brushshe
/usr/share/icons/hicolor/512x512/apps/brushshe.png
/usr/share/applications/brushshe.desktop
/usr/share/doc/brushshe/LICENSE
/usr/share/doc/brushshe/LICENSE-CC0
/usr/share/doc/brushshe/README.md
"""
    print("Creating spec file...")
    os.makedirs("brushshe")
    with open("brushshe/brushshe.spec", "w", encoding="utf-8") as f:
        f.write(linux_rpm_spec)

    print("Creating the .desktop file...")
    with open("brushshe/brushshe.desktop", "w", encoding="utf-8") as f:
        f.write(linux_desktop_file)

    print("Creating a folder for packaging into a tarball...")
    shutil.copytree("../Brushshe", "brushshe/Brushshe")
    for f in ["../README.md", "../LICENSE", "../LICENSE-CC0"]:
        shutil.copy(f, "brushshe")
    shutil.copy("../Brushshe/assets/icons/icon.png", "brushshe/brushshe.png")

    if distro != "OpenMandriva":
        install_customtkinter_to_dir("brushshe/Brushshe")

    print("Creating tarball...")
    with tarfile.open("brushshe.tar", "w") as tar:
        tar.add("brushshe")

    print("Creating .rpm package...")
    subprocess.run(["rpmbuild", "-tb", "brushshe.tar", "--define", "_topdir " + os.getcwd()])

    print("Cleaning and moving the .rpm package from the project folder...")
    for f in glob.glob("RPMS/noarch/*"):
        shutil.move(f, "../../")
    for d in ["BUILD", "BUILDROOT", "SPECS", "RPMS", "SRPMS", "brushshe"]:
        if os.path.exists(d):
            shutil.rmtree(d)
    os.remove("brushshe.tar")
elif args.exe:
    print("Add ISCC.exe to PATH if it is not already added before execution.")
    answer = input("Continue (y/n)?")
    if answer != "y":
        sys.exit(1)

    windows_prepare()

    print("PyInstaller packaging...")
    subprocess.run(
        [
            venv_python,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--onedir",
            "--windowed",
            "--icon",
            r"..\Brushshe\assets\icons\icon.ico",
            "--name",
            "brushshe",
            "--add-data",
            r"brenv\Lib\site-packages\customtkinter;customtkinter/",
            "--add-data",
            r"..\README.md;.",
            "--add-data",
            r"..\LICENSE;.",
            "--add-data",
            r"..\LICENSE-CC0;.",
            "--add-data",
            "dependencies-licenses.txt;.",
            "--add-data",
            f"{windows_python_license_path};.",
            "--add-data",
            "python-licenses.html;.",
            "--add-data",
            r"..\Brushshe\assets;assets/",
            r"..\Brushshe\main.py",
        ]
    )

    print("Creating an installer using Inno Setup...")
    subprocess.run(["iscc", "inno-setup-script.iss"])

    print("Cleaning...")
    windows_common_cleaning()
    os.remove("brushshe.spec")
    shutil.move("Output/Brushshe_64bit.exe", r"..\..")
    shutil.rmtree("Output")
elif args.portable_exe:
    windows_prepare()

    print("PyInstaller packaging...")
    subprocess.run(
        [
            venv_python,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--icon",
            r"..\Brushshe\assets\icons\icon.ico",
            "--name",
            "Brushshe_64bit_portable.exe",
            "--add-data",
            r"brenv\Lib\site-packages\customtkinter;customtkinter/",
            "--add-data",
            r"..\README.md;.",
            "--add-data",
            r"..\LICENSE;.",
            "--add-data",
            r"..\LICENSE-CC0;.",
            "--add-data",
            "dependencies-licenses.txt;.",
            "--add-data",
            f"{windows_python_license_path};.",
            "--add-data",
            "python-licenses.html;.",
            "--add-data",
            r"..\Brushshe\assets;assets/",
            r"..\Brushshe\main.py",
        ]
    )

    print("Cleaning...")
    shutil.move(r"dist\Brushshe_64bit_portable.exe", r"..\..")
    windows_common_cleaning()
    os.remove("Brushshe_64bit_portable.exe.spec")
else:
    parser.print_help()
    sys.exit(1)
