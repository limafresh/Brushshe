# Brushshe - painting app

<p align="center">
  <img src="https://raw.githubusercontent.com/limafresh/Brushshe/refs/heads/main/Brushshe/icons/logo.svg" alt="logo" width="100" height="100">
</p>

## Description
**Brushshe** is a simple graphical editor, written on Python 3 та CustomTkinter.

![Screenshot](https://raw.githubusercontent.com/limafresh/Brushshe/main/screenshot.png)

## Usage
1. Install [Python 3](https://www.python.org/downloads/), if not installed;
2. Download the code and unpack downloaded archive:

[![Download the code](https://img.shields.io/badge/Download_the_code-ZIP-orange?style=for-the-badge&logo=Python&logoColor=white)](https://github.com/limafresh/Brushshe/archive/refs/heads/main.zip)

3. Install CustomTkinter, if not installed - open terminal or command line and enter:
```bash
pip install customtkinter
```
4. Launch Python IDLE, open file `brushshe.py` and launch it.
### Possible errors
1. If Python cannot find the `PIL` library, install `Pillow`, which is compatible with `PIL`:
```bash
pip install Pillow
```

## Functionality
### Painting
You can choose a color, change the brush thickness, and paint.
### Eraser
Removing excess with an eraser.
### Background
You can choose the background color.
### Stickers
You can add stickers and resize them. All sticker images are drawn by me or created by AI.
### Text
You can place text and change its size.
### Frames
You can decorate the picture with frames.
### Shapes
Rectangle, oval (with or without fill), line.
### My Gallery
Window showing images drawn in Brushshe and "saved to gallery". Images from the gallery are stored in `<user_home_folder>/Pictures/Brushshe Images`.
### Dark theme
There is a light and dark theme.
### File
You can open a picture from a file and save it outside the gallery.

## Dependency versions used during development
+ Python 3.11.2
+ customtkinter 5.2.2

## Credits
Thanks [Akascape](https://github.com/Akascape) for libraries [CTkColorPicker](https://github.com/Akascape/CTkColorPicker), [CTkMenuBar](https://github.com/Akascape/CTkMenuBar) and [CTkMessagebox](https://github.com/Akascape/CTkMessagebox).

## Translations
The internationalization of this program has a simple principle - it determines what the computer's localization is (for example, *en*, *ru*, etc.), and then applies the `Brushshe/locales/{localization}.json` file, where *localization* is the computer's localization.

## License
+ Project license - *GNU GPL v3*
+ CTkColorPicker, CTkMenuBar and CTkMessagebox license - *CC0*
+ License for program translations (`Brushshe/locales/*.json`) - *CC0*

## For developers
### Linter
[Ruff](https://github.com/astral-sh/ruff) is used to maintain code cleanliness

## 🎨🦅💪
