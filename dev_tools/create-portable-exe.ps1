Write-Host 'Creating a virtual environment...'
python -m venv brenv

Write-Host 'Switching to the virtual environment...'
& .\brenv\Scripts\Activate.ps1

Write-Host 'Installing dependencies...'
pip install pyinstaller pip-licenses pillow customtkinter

Write-Host 'Creating a file with licenses...'
pip-licenses --format=plain-vertical --with-license-file --no-license-path --no-version --from=mixed --output-file=dependencies-licenses.txt

Write-Host 'PyInstaller packaging...'
pyinstaller --noconfirm --onefile --windowed --icon "..\Brushshe\icons\icon.ico" --name "Brushshe_64bit_portable.exe" --add-data "..\Brushshe\brushshe_theme.json;." --add-data "brenv\Lib\site-packages\customtkinter;customtkinter/" --add-data "..\Brushshe\icons;icons/" --add-data "..\Brushshe\locales;locales/" --add-data "..\README.md;." --add-data "..\LICENSE;." --add-data "dependencies-licenses.txt;." --add-data "..\Brushshe\assets;assets/"  "..\Brushshe\brushshe.py"

Write-Host 'Cleaning...'
if (Test-Path "..\..\dist") {
    Remove-Item "..\..\dist" -Recurse -Force
}
Move-Item -Path "dist" -Destination "..\.."

Remove-Item -Path "build" -Recurse -Force
Remove-Item -Path "brenv" -Recurse -Force
Remove-Item -Path "Brushshe_64bit_portable.exe.spec"
Remove-Item -Path "dependencies-licenses.txt"