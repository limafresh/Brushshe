# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


def shorten_filename(filename: str, max_length: int = 20) -> str:
    if len(filename) > max_length:
        return filename[: max_length - 3] + "..."
    else:
        return filename
