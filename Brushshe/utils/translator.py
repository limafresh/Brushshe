# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
from locale import getlocale

from utils.common import resource
from utils.config_loader import config, write_config

is_english = True
translations = {}


def load_language(file_path, language_code: str | None):
    global translations, is_english
    if language_code == "en":
        pass
    else:
        try:
            with open(
                resource(file_path),
                "r",
                encoding="utf-8",
            ) as f:
                translations = json.load(f)
                is_english = False
        except FileNotFoundError:
            if language_code:
                print(f"File for language '{language_code}' not found.")
            else:
                print("File not found")
        except json.JSONDecodeError:
            print("Localization file is corrupted. Brushshe will be in English.")


def _(key):
    if not is_english and key in translations:
        return translations[key]
    else:
        if not is_english:
            print(f"Translation for '{key}' not found!")
        return key


if config.get("Brushshe", "language") == "None":
    # Get system locale
    locale = getlocale()

    if isinstance(locale, tuple) and all(isinstance(item, str) for item in locale):
        language_code = locale[0][:2].lower()
    elif isinstance(locale, str):
        language_code = locale[:2].lower()
    else:
        language_code = None

    config.set("Brushshe", "language", language_code)
    write_config()

    file_path = f"assets/locales/{language_code}.json"
else:
    language_value = config.get("Brushshe", "language")

    if len(language_value) == 2:
        file_path = f"assets/locales/{language_value}.json"
        language_code = language_value
    else:
        file_path = language_value
        language_code = None

load_language(file_path, language_code)
