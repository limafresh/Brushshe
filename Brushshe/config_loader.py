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
    }

    if not config.has_section("Brushshe"):
        config.add_section("Brushshe")

    for option, default_value in default_options.items():
        if not config.has_option("Brushshe", option):
            config.set("Brushshe", option, default_value)

    write_config()


# FIXME: It's wrong way. It can be only for portable version.
#   On linux the config must be on some like ~/.config/brushshe/brushshe_config.ini
config_file_path = Path.home() / ".brushshe_config.ini"
config = ConfigParser()

load_config()
