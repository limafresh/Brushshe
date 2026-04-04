# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import customtkinter as ctk
from gui import BrushsheGui
from utils.common import resource
from utils.config_loader import config

ctk.set_appearance_mode(config.get("Brushshe", "theme"))

color_theme = config.get("Brushshe", "color_theme")
if color_theme in ("blue", "green", "dark-blue"):
    ctk.set_default_color_theme(color_theme)
else:
    ctk.set_default_color_theme(resource(f"assets/themes/{config.get('Brushshe', 'color_theme')}.json"))

app = BrushsheGui()
app.mainloop()
