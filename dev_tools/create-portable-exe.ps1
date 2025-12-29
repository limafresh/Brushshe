Write-Host 'Python is required to run the script. ONLY RUN FROM THE dev_tools FOLDER!' -ForegroundColor Cyan

$answer = Read-Host 'Continue (y/n)?'
if ($answer -ne 'y') {
    exit 0
}

Write-Host 'Creating a virtual environment...' -ForegroundColor Blue
python -m venv brenv

Write-Host 'Switching to the virtual environment...' -ForegroundColor Blue
& .\brenv\Scripts\Activate.ps1

Write-Host 'Installing dependencies...' -ForegroundColor Blue
pip install pyinstaller pip-licenses pillow customtkinter

Write-Host 'Creating a file with licenses...' -ForegroundColor Blue
pip-licenses --format=plain-vertical --with-license-file --no-license-path --no-version --from=mixed --with-system --output-file=dependencies-licenses.txt
Add-Content -Path "dependencies-licenses.txt" -Value ''
Add-Content -Path "dependencies-licenses.txt" -Value 'This exe file (Brushshe) uses dependencies that are dual-licensed under GPL/LGPL or permissive licenses (e.g., Apache, BSD). In all such cases, the permissive license has been selected.'

Write-Output 'Obtaining licenses for Python...' -ForegroundColor Blue
Invoke-WebRequest -Uri 'https://docs.python.org/3/license.html' -OutFile 'python-licenses.html'
$licensePath = python -c "import os, sys; print(os.path.abspath(os.path.join(sys.base_prefix, 'LICENSE.txt')))"

Write-Host 'PyInstaller packaging...' -ForegroundColor Blue
pyinstaller --noconfirm --onefile --windowed --icon "..\Brushshe\assets\icons\icon.ico" --name "Brushshe_64bit_portable.exe" --add-data "brenv\Lib\site-packages\customtkinter;customtkinter/" --add-data "..\README.md;." --add-data "..\LICENSE;." --add-data "..\LICENSE-CC0;." --add-data "dependencies-licenses.txt;." --add-data "$licensePath;." --add-data "python-licenses.html;." --add-data "..\Brushshe\assets;assets/"  "..\Brushshe\main.py"

Write-Host 'Cleaning...' -ForegroundColor Blue
Move-Item -Path "dist\Brushshe_64bit_portable.exe" -Destination "..\.."
Remove-Item -Path "dist" -Recurse -Force
Remove-Item -Path "build" -Recurse -Force
Remove-Item -Path "brenv" -Recurse -Force
Remove-Item -Path "Brushshe_64bit_portable.exe.spec"
Remove-Item -Path "dependencies-licenses.txt"
Remove-Item -Path "python-licenses.html"
