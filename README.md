# Brushshe - painting app

![Static Badge](https://img.shields.io/badge/Tested_on-Windows%2C_Linux-orange)

<p align="center">
	<img src="https://raw.githubusercontent.com/limafresh/Brushshe/refs/heads/main/Brushshe/assets/icons/logo.svg" alt="logo" width="100" height="100">
</p>

## Description
**Brushshe** is a simple and user-friendly raster graphics editor. Available for Windows and Linux.

![Screenshot](https://raw.githubusercontent.com/limafresh/Brushshe/main/docs/screenshot.png)

[View more screenshots](https://github.com/limafresh/Brushshe/discussions/2)

## ⬇️ Installation
### Download Brushshe for Windows 64bit
[![Static Badge](https://img.shields.io/badge/%F0%9F%AA%9F_Download-.exe_file-blue?style=for-the-badge)](https://github.com/limafresh/Brushshe/releases) or
[![Static Badge](https://img.shields.io/badge/%F0%9F%AA%9F_Download-portable_.exe_file-blue?style=for-the-badge)](https://github.com/limafresh/Brushshe/releases)

**or**
### Download Brushshe for Linux
[![Static Badge](https://img.shields.io/badge/Download-.deb_file-red?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/limafresh/Brushshe/releases) or
[![Static Badge](https://img.shields.io/badge/Download-for_Fedora-blue?style=for-the-badge&logo=fedora&logoColor=white)](https://github.com/limafresh/Brushshe/releases) or
[![Static Badge](https://img.shields.io/badge/Download-for_Mageia-blue?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/limafresh/Brushshe/releases) or
[![Static Badge](https://img.shields.io/badge/Download-for_OpenMandriva-blue?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/limafresh/Brushshe/releases)

**or**
### Run via Python
1. Install [Python 3](https://www.python.org/downloads/), if not installed;
2. Download the code and unpack downloaded archive:

[![Static Badge](https://img.shields.io/badge/Download-.zip-orange?style=for-the-badge&logo=python&logoColor=white)](https://github.com/limafresh/Brushshe/tags)

3. Install *CustomTkinter* and *Pillow* - open terminal or command line and enter:
```bash
pip install customtkinter Pillow
```
4. Run file `Brushshe/main.py`.

## 🚀 Features
+ **Open**: You can open a picture from a file or URL.
+ **Painting**: You can choose a color, change the brush thickness and shape, and paint. You can change canvas size.
+ **Recoloring brush**: Draws through contours.
+ **Save to device**: You can save picture to your PC in different formats (PNG, JPEG, GIF, BMP, DDS, DIB, EPS, ICNS, ICO, IM, MPO, PCX, PPM, SGI, TGA, TIFF, WEBP, PDF (only for save)). Autosave is supported.
+ **Undo and redo**: You can undo and redo last actions.
+ **Eraser**: Removing excess with an eraser.
+ **Fill**: You can fill areas of a drawing, including with a gradient fill.
+ **Eyedropper**: Right click on the desired place on the canvas to get its color and paint with it.
+ **Spray**: Spray paint.
+ **Background**: You can choose the background color.
+ **Stickers**: You can add stickers from Brushshe sticker set (all sticker images are drawn by [limafresh, founder of Brushshe](https://github.com/limafresh/), or created by AI) and resize them. You can also add a sticker from a file or URL.
+ **Text**: You can place text and change its size.
+ **Frames**: You can decorate the picture with frames.
+ **Shapes**: Rectangle and oval (with or without fill), line, bezier curve.
+ **Effects**: Blur, detail, contour, grayscale, inversion and other. Not work on GIF images.
+ **My Gallery**: Window showing images drawn in Brushshe and "saved to gallery". Images from the gallery are stored in `<user_home_folder>/Pictures/Brushshe Images` or `<user_home_folder>/Brushshe Images` on some minimalistic Linux distributions.
+ **Dark theme**: There is a light and dark theme.
+ **Rotate**: Rotate right, rotate left.
+ **Create screenshot**: You can take a screenshot and draw on it. Not work on Linux with Wayland.
+ **Paste image from clipboard**: You can paste image from clipboard.
+ **View**: Zoom in, zoom out, reset zoom.
+ **Change size**: You can change the size by cropping or scaling.
+ **Palettes**: There are 4 built-in palette sets in the settings, and if there are not enough of them, you can load your own from .hex files.
+ **Brush smoothing**: Brush smoothing with params.
+ **Cut, copy and insert**: Cut, copy or insert fragments. Works on Windows, but on Linux you need to install `xclip` (X11) or `wl-paste` (Wayland). If they are not installed, everything else will work, but when you try to paste from the buffer, you will get a message that this is impossible.
+ **Remove white background**: Replace white or really light gray background to transparent.
+ **Palettes**: use standard or custom HEX palettes.
+ **Select**: rectangle and polygon select, invert selected, deselect all, fuzzy select, select by color.

## Hotkeys
+ *Ctrl+Z*: undo
+ *Ctrl+Y*: redo
+ *Ctrl+S*: save to gallery
+ *Ctrl+X*: cut
+ *Ctrl+C*: copy
+ *Ctrl+V*: insert
+ *Delete*: delete
+ *Ctrl+F* or *X*: flip colors
+ *Ctrl+B* or *B*: brush
+ *Ctrl+E* or *E*: eraser
+ *=*: zoom in
+ *-*: zoom out
+ *[*: down by 1 the brush or other tools size
+ *]*: up by 1 the brush or other tools size
+ *{*: down by 10 the brush or other tools size
+ *}*: up by 10 the brush or other tools size
+ *Shift + mouse scroll*: scrolling the canvas horizontally
+ *Middle mouse button*: move canvas

## Goal of project
The goal of the project is to provide a open-source, convenient, beautiful and multifunctional painting app using the CustomTkinter toolkit.

## Contributions
All contributions are welcome!
+ Do not use third-party libraries. Only standard Python libraries, CustomTkinter and Pillow/PIL.

## Credits
+ Thanks [Akascape](https://github.com/Akascape) for CTkColorPicker, CTkMenuBar, CTkMessagebox and CTkToolTip.
+ Thanks to [a13xe](https://github.com/a13xe/) for the wonderful [CTkThemesPack](https://github.com/a13xe/CTkThemesPack).
+ Thanks [Chip Viled](https://github.com/chipviled) for contributing.
+ Thanks to our translators: [sagar12](https://github.com/Sagar1205b) (Hindi); [Sagar Sirbi](https://github.com/sagarsirbi), [iLollek](https://github.com/iLollek) (German).

## Translations
The internationalization of this program has a simple principle - it determines what the computer's localization is (for example, *en*, *ru*, etc.), and then applies the `Brushshe/assets/locales/{localization}.json` file, where *localization* is the computer's localization.

## Licenses
+ Project license - *MPL 2.0* (old code before the license change - under MPL 2.0 or GNU GPLv3)
+ Some Brushshe components or third-party components are in the *public domain* (see below for which ones)
+ Fonts - *OFL 1.1*
+ [Picture on screenshot](https://github.com/limafresh/Brushshe/pull/15) - [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), by Chip Viled, drawn in Brushshe
+ Builds (for example .exe, .deb) may contain other components
### Public domain components (paths are relative)
+ `assets/` (stickers, frames, etc., except for some subfolders with other licenses) - *CC0 1.0*
+ `docs/` - *CC0 1.0*
+ CTkMenuBar - *CC0 1.0*
+ `README.md` (this file), `main.py`, other files with the CC0 header - *CC0 1.0*

## For developers
### Linter
[Ruff](https://github.com/astral-sh/ruff) is used to maintain code cleanliness.

Starting with version 2.0.0, each version will be given a code name based on the names of cities in alphabetical order. 2.0.0 starts with "S" because it is the 19th letter of the alphabet, and since 1.0.0 there have been 18 versions. Example:

+ 2.0.0 - Skopje
+ 2.1.0 - T..
+ 2.1.1 - T..
+ 2.2.0 - U..
+ 2.x.x - Z..
+ 2.x.x - A..

## 🎨🦅💪
