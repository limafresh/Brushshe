# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
from locale import getlocale

from data import resource


def load_language(language_code):
    global translations
    if language_code == "en":
        pass
    else:
        try:
            with open(
                resource(f"assets/locales/{language_code}.json"),
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
