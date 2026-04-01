# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import webbrowser
from collections import deque

import customtkinter as ctk
import data
from ui.scroll import scroll
from ui.spinbox import IntSpinbox
from utils.config_loader import config, write_config
from utils.resource import resource
from utils.translator import _


class Settings:
    def settings(self):
        def change_theme(value):
            mode = {_("Light"): "light", _("Dark"): "dark"}.get(value, "system")
            ctk.set_appearance_mode(mode)
            config.set("Brushshe", "theme", mode)
            write_config()

        def change_undo_levels():
            data.undo_stack = deque(data.undo_stack, maxlen=undo_levels_spinbox.get())
            data.redo_stack = deque(data.redo_stack, maxlen=undo_levels_spinbox.get())
            config.set("Brushshe", "undo_levels", str(undo_levels_spinbox.get()))
            write_config()

        def smooth_switch_event():
            data.is_brush_smoothing = smooth_var.get()
            config.set("Brushshe", "smoothing", str(data.is_brush_smoothing))
            write_config()

        def bsq_event(value):
            data.brush_smoothing_quality = int(value)
            config.set("Brushshe", "brush_smoothing_quality", str(data.brush_smoothing_quality))
            write_config()

        def bsf_event(value):
            data.brush_smoothing_factor = int(value)
            config.set("Brushshe", "brush_smoothing_factor", str(data.brush_smoothing_factor))
            write_config()

        def mask_radiobutton_callback():
            self.logic.set_mask_type(mask_var.get())
            config.set("Brushshe", "mask", str(mask_var.get()))
            write_config()

        def palette_radiobutton_callback():
            self.logic.import_palette(resource(f"assets/palettes/{palette_var.get()}_palette.hex"))
            config.set("Brushshe", "palette", palette_var.get())
            write_config()

        def autosave_switch_event():
            config.set("Brushshe", "autosave", str(data.autosave_var.get()))
            write_config()

        def ct_optionmenu_callback(choice):
            config.set("Brushshe", "color_theme", choice)
            write_config()

        def language_optionmenu_callback(value):
            config.set("Brushshe", "language", data.languages.get(value))
            write_config()

        settings_tl = ctk.CTkToplevel(self)
        settings_tl.geometry("400x650")
        settings_tl.title(_("Settings"))
        settings_tl.wm_iconbitmap()
        settings_tl.after(300, lambda: settings_tl.iconphoto(False, self.iconpath))
        settings_tl.transient(self)

        settings_frame = ctk.CTkScrollableFrame(settings_tl, fg_color="transparent")
        settings_frame.pack(padx=10, pady=10, fill="both", expand=True)
        scroll(settings_frame)

        theme_frame = ctk.CTkFrame(settings_frame)
        theme_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(theme_frame, text=_("Theme")).pack(padx=10, pady=10)

        theme_btn = ctk.CTkSegmentedButton(
            theme_frame,
            values=[_("System"), _("Light"), _("Dark")],
            command=change_theme,
        )
        theme_btn.set(_(config.get("Brushshe", "theme").capitalize()))
        theme_btn.pack(padx=10, pady=10)

        undo_levels_frame = ctk.CTkFrame(settings_frame)
        undo_levels_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(undo_levels_frame, text=_("Maximum undo/redo levels")).pack(padx=10, pady=10)

        undo_levels_spinbox = IntSpinbox(undo_levels_frame, width=150)
        undo_levels_spinbox.pack(padx=10, pady=10)
        undo_levels_spinbox.set(data.undo_stack.maxlen)

        ctk.CTkButton(undo_levels_frame, text=_("Apply"), command=change_undo_levels).pack(padx=10, pady=10)

        smooth_frame = ctk.CTkFrame(settings_frame)
        smooth_frame.pack(padx=10, pady=10, fill="x")

        smooth_var = ctk.BooleanVar(value=data.is_brush_smoothing)
        ctk.CTkSwitch(
            smooth_frame,
            text=_("Smoothing for brush/eraser"),
            variable=smooth_var,
            onvalue=True,
            offvalue=False,
            command=smooth_switch_event,
        ).pack(padx=10, pady=10)

        ctk.CTkLabel(smooth_frame, text=_("Brush smoothing quality")).pack(padx=10, pady=10)

        bsq_slider = ctk.CTkSlider(smooth_frame, from_=1, to=64, command=bsq_event)
        bsq_slider.set(data.brush_smoothing_quality)
        bsq_slider.pack(padx=10, pady=10)

        ctk.CTkLabel(smooth_frame, text=_("Brush smoothing factor (weight)")).pack(padx=10, pady=1)

        bsf_slider = ctk.CTkSlider(smooth_frame, from_=3, to=64, command=bsf_event)
        bsf_slider.set(data.brush_smoothing_factor)
        bsf_slider.pack(padx=10, pady=10)

        mask_frame = ctk.CTkFrame(settings_frame)
        mask_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(mask_frame, text=_("Mask")).pack(padx=10, pady=10)

        mask_var = ctk.IntVar(value=config.getint("Brushshe", "mask"))
        mask_types = [("Display as fill", 0), ("Display as ants", 1)]
        for name, value in mask_types:
            ctk.CTkRadioButton(
                mask_frame,
                text=_(name),
                variable=mask_var,
                value=value,
                command=mask_radiobutton_callback,
            ).pack(padx=10, pady=10)

        palette_frame = ctk.CTkFrame(settings_frame)
        palette_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(palette_frame, text=_("Palette")).pack(padx=10, pady=10)

        palette_var = ctk.StringVar(value=config.get("Brushshe", "palette"))
        for palette_name in data.standard_palettes:
            ctk.CTkRadioButton(
                palette_frame,
                text=_(palette_name.capitalize()),
                variable=palette_var,
                value=palette_name,
                command=palette_radiobutton_callback,
            ).pack(padx=10, pady=10)

        autosave_frame = ctk.CTkFrame(settings_frame)
        autosave_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkSwitch(
            autosave_frame,
            text=_("Autosave"),
            variable=data.autosave_var,
            onvalue=True,
            offvalue=False,
            command=autosave_switch_event,
        ).pack(padx=10, pady=10)

        color_theme_frame = ctk.CTkFrame(settings_frame)
        color_theme_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(color_theme_frame, text=_("Color theme")).pack(padx=10, pady=10)

        color_theme_optionmenu = ctk.CTkOptionMenu(
            color_theme_frame, values=data.color_themes, command=ct_optionmenu_callback
        )
        color_theme_optionmenu.pack(padx=10, pady=10)
        color_theme_optionmenu.set(config.get("Brushshe", "color_theme"))

        ctk.CTkLabel(color_theme_frame, text=_("A restart is required")).pack(padx=10, pady=10)

        language_frame = ctk.CTkFrame(settings_frame)
        language_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(language_frame, text=_("Language")).pack(padx=10, pady=10)

        language_optionmenu = ctk.CTkOptionMenu(
            language_frame, values=list(data.languages.keys()), command=language_optionmenu_callback
        )
        language_optionmenu.pack(padx=10, pady=10)
        language_key = next((k for k, v in data.languages.items() if v == config.get("Brushshe", "language")), None)
        language_optionmenu.set(language_key)

        ctk.CTkLabel(language_frame, text=_("A restart is required")).pack(padx=10, pady=10)

        last_frame = ctk.CTkFrame(settings_frame)
        last_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkButton(
            last_frame,
            text=f"{_('Check new versions (yours is')} {data.version_full})",
            command=lambda: webbrowser.open(r"https://github.com/limafresh/Brushshe/releases"),
        ).pack(padx=10, pady=10)

        ctk.CTkButton(
            last_frame, text=_("Reset settings after exiting"), command=self.logic.reset_settings_after_exiting
        ).pack(padx=10, pady=10)
