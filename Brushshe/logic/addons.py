import importlib.util
from types import SimpleNamespace

from ui.file_dialog import FileDialog
from utils.translator import _


class Addons:
    def open_addon(self):
        dialog = FileDialog(self.ui, title=_("Open addon"))
        if dialog.path:
            self.run_addon(dialog.path)

    def run_addon(self, path: str):
        api = SimpleNamespace(draw_line=self.draw_line)
        spec = importlib.util.spec_from_file_location("addon", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "register"):
            module.register(api)
