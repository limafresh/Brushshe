# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request

script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(script_dir) != "dev_tools" or script_dir != os.getcwd():
    sys.exit("ERROR: This script must be executed from the dev_tools folder!")

parser = argparse.ArgumentParser(description="Script for packaging Brushshe for different systems")

parser.add_argument("--deb", action="store_true", help="Create DEB")
parser.add_argument("--rpm", action="store_true", help="Create RPM")
parser.add_argument("--exe", action="store_true", help="Create EXE")
parser.add_argument("--portable-exe", action="store_true", help="Create portable EXE")

args = parser.parse_args()

if args.deb or args.rpm:
    try:
        from ctkdeb import Packager
    except ModuleNotFoundError:
        print("CTkDeb is required to create DEB and RPM ('pip install ctkdeb').")
        sys.exit(1)

    packager = Packager("ctkdeb.json", project_folder="../Brushshe", output_folder="../../")

    if args.deb:
        packager.create_deb()
    elif args.rpm:
        supported_distros = ["fedora", "mageia", "openmandriva"]
        distro = input(
            f"Enter the distribution for which you want to create an .rpm package [{'/'.join(supported_distros)}]:"
        )
        if distro not in supported_distros:
            print("Invalid distro name.")
            sys.exit(1)

        packager.create_rpm(distro)

elif args.exe or args.portable_exe:
    if args.exe:
        print("Add ISCC.exe to PATH if it is not already added before execution.")
        answer = input("Continue (y/n)?")
        if answer != "y":
            sys.exit(1)

    print("Creating a virtual environment...")

    subprocess.run(["python", "-m", "venv", "brenv"], check=True)
    venv_python = os.path.join("brenv", "Scripts", "python.exe")

    print("Installing dependencies...")

    subprocess.run(
        [venv_python, "-m", "pip", "install", "pyinstaller", "pip-licenses", "pillow", "customtkinter"], check=True
    )

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
        ],
        check=True,
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

    python_license_path = os.path.abspath(os.path.join(sys.base_prefix, "LICENSE.txt"))

    print("PyInstaller packaging...")

    subprocess.run(
        [
            venv_python,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--onedir" if args.exe else "--onefile",
            "--windowed",
            "--icon",
            r"..\Brushshe\assets\icons\icon.ico",
            "--name",
            "brushshe" if args.exe else "Brushshe_64bit_portable.exe",
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
            f"{python_license_path};.",
            "--add-data",
            "python-licenses.html;.",
            "--add-data",
            r"..\Brushshe\assets;assets/",
            r"..\Brushshe\main.py",
        ],
        check=True,
    )

    if args.exe:
        print("Creating an installer using Inno Setup...")
        subprocess.run(["iscc", "inno-setup-script.iss"], check=True)

    print("Cleaning...")

    for d in ["build", "brenv"]:
        shutil.rmtree(d)
    for f in ["dependencies-licenses.txt", "python-licenses.html"]:
        os.remove(f)

    if args.exe:
        shutil.rmtree("dist")
        os.remove("brushshe.spec")
        shutil.move("Output/Brushshe_64bit.exe", r"..\..")
        shutil.rmtree("Output")
    elif args.portable_exe:
        shutil.move(r"dist\Brushshe_64bit_portable.exe", r"..\..")
        shutil.rmtree("dist")
        os.remove("Brushshe_64bit_portable.exe.spec")

else:
    parser.print_help()
    sys.exit(1)
