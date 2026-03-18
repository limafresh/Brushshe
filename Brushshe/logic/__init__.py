# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from .canvas import CanvasOperations
from .common import Common
from .decorations import Decorations
from .docker_and_palette import DockerAndPalette
from .edit_tools import EditTools
from .paint_tools import PaintTools
from .screenshot import Screenshot
from .selection import Selection
from .shapes import Shapes
from .tool_operations import ToolOperations


class BrushsheLogic(
    Common,
    CanvasOperations,
    PaintTools,
    Shapes,
    EditTools,
    Selection,
    Screenshot,
    DockerAndPalette,
    Decorations,
    ToolOperations,
):
    pass
