# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import platform
from configparser import ConfigParser
from pathlib import Path


def write_config():
    with open(config_file_path, "w", encoding="utf-8") as config_file:
        config.write(config_file)


def load_config():
    config.read(config_file_path)

    default_options = {
        "theme": "System",
        "undo_levels": "10",
        "smoothing": "False",
        "brush_smoothing_factor": "10",
        "brush_smoothing_quality": "20",
        "palette": "default",
        "autosave": "False",
        "color_theme": "brushshe_theme",
    }

    if not config.has_section("Brushshe"):
        config.add_section("Brushshe")

    for option, default_value in default_options.items():
        if not config.has_option("Brushshe", option):
            config.set("Brushshe", option, default_value)

    write_config()


if platform.system() == "Linux":
    config_dir = Path.home() / ".config" / "brushshe"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file_path = config_dir / "brushshe_config.ini"
else:
    config_file_path = Path.home() / ".brushshe_config.ini"

config = ConfigParser()

load_config()
