# Brushshe - painting app

![Static Badge](https://img.shields.io/badge/Tested_on-Windows%2C_Linux-orange)

<p align="center">
  <img src="https://raw.githubusercontent.com/limafresh/Brushshe/refs/heads/main/Brushshe/icons/logo.svg" alt="logo" width="100" height="100">
</p>

## Description
**Brushshe** is a raster graphical editor, written on Python 3, CustomTkinter and PIL.

![Screenshot](https://raw.githubusercontent.com/limafresh/Brushshe/main/screenshot.png)

[View more screenshots](https://github.com/limafresh/Brushshe/discussions/2)

## ⬇️ Installation
### Download Brushshe for Windows 64bit
[![Static Badge](https://img.shields.io/badge/Download-portable_.exe_file-blue?style=for-the-badge)](https://github.com/limafresh/Brushshe/releases)

**or**
### Download Brushshe for Linux .deb
[![Static Badge](https://img.shields.io/badge/Download-.deb_file-red?style=for-the-badge&logo=linux)](https://github.com/limafresh/Brushshe/releases)

**or**
### Run via Python
1. Install [Python 3](https://www.python.org/downloads/), if not installed;
2. Download the code and unpack downloaded archive:

[![Download the code](https://img.shields.io/badge/Download_the_code-ZIP-orange?style=for-the-badge&logo=Python&logoColor=white)](https://github.com/limafresh/Brushshe/tags)

3. Install *CustomTkinter* and *Pillow* - open terminal or command line and enter:
```bash
pip install customtkinter Pillow
```
4. Run file `Brushshe/brushshe.py`.

## 🚀 Features
+ **Open**: You can open a picture from a file.
+ **Painting**: You can choose a color, change the brush thickness, and paint. You can change canvas size.
+ **Recoloring brush (new!)**: Draws through contours.
+ **Save to device**: You can save picture to your PC in different formats (PNG, JPG, GIF, BMP, TIFF, WEBP, ICO, PPM, PGM, PBM).
+ **Undo and redo**: You can undo and redo 10 last actions.
+ **Eraser**: Removing excess with an eraser.
+ **Fill**: Can fill areas of a drawing. Can work slowly on large areas, and not work on RGBA-images.
+ **Eyedropper**: Right click on the desired place on the canvas to get its color and paint with it.
+ **Spray**: Spray paint.
+ **Background**: You can choose the background color.
+ **Stickers**: You can add stickers from Brushshe sticker set (all sticker images are drawn by me or created by AI) and resize them. You can also add a sticker from a file.
+ **Text**: You can place text and change its size.
+ **Frames**: You can decorate the picture with frames.
+ **Shapes**: Rectangle and oval (with or without fill), line, bezier curve.
+ **Effects**: Blur, detail, contour, grayscale, inversion and other. Not work on GIF images.
+ **My Gallery**: Window showing images drawn in Brushshe and "saved to gallery". Images from the gallery are stored in `<user_home_folder>/Pictures/Brushshe Images` or `<user_home_folder>/Brushshe Images` on some minimalistic Linux distributions.
+ **Dark theme**: There is a light and dark theme.
+ **Rotate**: Rotate right, rotate left.
+ **Create screenshot**: You can take a screenshot and draw on it. Not work on Linux with Wayland.
+ **View**: Zoom in, zoom out, reset zoom.
+ **Change size**: You can change the size by cropping or scaling.

## Hotkeys
+ *Ctrl+Z*: undo
+ *Ctrl+Y*: redo
+ *Ctrl+S*: save to gallery
+ *X*: flip colors
+ *B*: brush
+ *E*: eraser
+ *=*: zoom in
+ *-*: zoom out
+ *[*: down by 1 the brush or other tools size
+ *]*:  by 1 the brush or other tools size
+ *{*: down by 10 the brush or other tools size
+ *}*: up by 10 the brush or other tools size
+ *Shift + mouse scroll*: scrolling the canvas horizontally

## Goal of project
The goal of the project is to provide a open-source, convenient, beautiful and multifunctional painting app using the CustomTkinter toolkit.

## Contributions
All contributions are welcome!
+ Do not use third-party libraries. Only standard Python libraries, CustomTkinter and Pillow/PIL.

## Credits
+ Thanks [Akascape](https://github.com/Akascape) for CTkColorPicker, CTkMenuBar, CTkMessagebox and CTkToolTip.
+ Thanks [Chip Viled](https://github.com/chipviled) for conributing.

## Translations
The internationalization of this program has a simple principle - it determines what the computer's localization is (for example, *en*, *ru*, etc.), and then applies the `Brushshe/locales/{localization}.json` file, where *localization* is the computer's localization.

## License
+ Project license - *GNU GPL v3*
+ CTkColorPicker and CTkMenuBar license - *CC0 1.0*
+ License for program translations (`Brushshe/locales/*.json`) - *CC0 1.0*
+ Fonts - *OFL*
+ Picture on screenshot - [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), by Chip Viled, drawn in Brushshe

## For developers
### Linter
[Ruff](https://github.com/astral-sh/ruff) is used to maintain code cleanliness.

## 🎨🦅💪
