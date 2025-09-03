import json
import os
import sys
from locale import getlocale


def resource(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def load_language(language_code):
    global translations
    if language_code == "en":
        pass
    else:
        try:
            with open(
                resource(f"locales/{language_code}.json"),
                "r",
                encoding="utf-8",
            ) as f:
                translations = json.load(f)
        except FileNotFoundError:
            print(f"File for language '{language_code}' not found.")
        except json.JSONDecodeError:
            print("Localization file is corrupted. Brushshe will be in English.")


def _(key):
    return translations.get(key, key)


# Get system locale
locale = getlocale()

if isinstance(locale, tuple) and all(isinstance(item, str) for item in locale):
    language_code = locale[0][:2].lower()
elif isinstance(locale, str):
    language_code = locale[:2].lower()
else:
    language_code = None

translations = {}
load_language(language_code)
