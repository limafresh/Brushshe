# Brushshe - painting app

![Static Badge](https://img.shields.io/badge/Tested_on-Windows%2C_Linux-orange)

<p align="center">
  <img src="https://raw.githubusercontent.com/limafresh/Brushshe/refs/heads/main/Brushshe/icons/logo.svg" alt="logo" width="100" height="100">
</p>

## Description
**Brushshe** is a simple graphical editor, written on Python 3 та CustomTkinter.

![Screenshot](https://raw.githubusercontent.com/limafresh/Brushshe/main/screenshot.png)

[View more screenshots](https://github.com/limafresh/Brushshe/discussions/2)

*Due to the fact that Brushshe switched to PIL.ImageDraw in v1.0.0, some functions, especially shapes and fonts, have undergone changes. But now the program is more optimized and does not start to slow down if you draw for a long time.*

## Usage
### Download Brushshe for Windows 64bit
[![Static Badge](https://img.shields.io/badge/Download-portable_.exe_file-blue?style=for-the-badge)](https://github.com/limafresh/Brushshe/releases)

**or**
### Run via Python
1. Install [Python 3](https://www.python.org/downloads/), if not installed;
2. Download the code and unpack downloaded archive:

[![Download the code](https://img.shields.io/badge/Download_the_code-ZIP-orange?style=for-the-badge&logo=Python&logoColor=white)](https://github.com/limafresh/Brushshe/archive/refs/heads/main.zip)

3. Install *CustomTkinter* and *Pillow* - open terminal or command line and enter:
```bash
pip install customtkinter Pillow
```
4. Run file `Brushshe/brushshe.py`.

## Functionality
### Open
You can open a picture from a file.
### Painting
You can choose a color, change the brush thickness, and paint. You can change canvas size.
### Save to device
You can save picture to your PC in different formats (PNG, JPG, GIF, BMP, TIFF, WEBP, ICO, PPM, PGM, PBM).
### Undo
You can undo 10 last actions.
### Eraser
Removing excess with an eraser.
### Eyedropper
Right click on the desired place on the canvas to get its color and paint with it.
### Background
You can choose the background color.
### Stickers
You can add stickers from Brushshe sticker set (all sticker images are drawn by me or created by AI) and resize them. You can also add a sticker from a file.
### Text
You can place text and change its size.
### Frames
You can decorate the picture with frames.
### Shapes
Rectangle, oval (with or without fill); line.
### Effects
Blur, detail, contour and grayscale with adjustment slider.
### My Gallery
Window showing images drawn in Brushshe and "saved to gallery". Images from the gallery are stored in `<user_home_folder>/Pictures/Brushshe Images` or `<user_home_folder>/Brushshe Images` on some minimalistic Linux distributions.
### Dark theme
There is a system, light and dark theme.

## Credits
Thanks [Akascape](https://github.com/Akascape) for libraries [CTkColorPicker](https://github.com/Akascape/CTkColorPicker), [CTkMenuBar](https://github.com/Akascape/CTkMenuBar) and [CTkMessagebox](https://github.com/Akascape/CTkMessagebox).

## Translations
The internationalization of this program has a simple principle - it determines what the computer's localization is (for example, *en*, *ru*, etc.), and then applies the `Brushshe/locales/{localization}.json` file, where *localization* is the computer's localization.

## License
+ Project license - *GNU GPL v3*
+ CTkColorPicker and CTkMenuBar license - *CC0*
+ License for program translations (`Brushshe/locales/*.json`) - *CC0*

## For developers
### Linter
[Ruff](https://github.com/astral-sh/ruff) is used to maintain code cleanliness

## 🎨🦅💪
