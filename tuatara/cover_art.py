# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from tuatara.image_utils import (
    image_from_file,
    image_from_buffer,
    dominant_color,
    foreground_for,
)
from tuatara.settings import settings


class CoverArt:
    def __init__(self):
        self.imgdata = None
        self.bg_color = None
        self.fg_color = None

    def get_image(self): ...


class FileCoverArt(CoverArt):
    def __init__(self, path):
        super().__init__()
        self.kind = "file"
        self.path = path
        self.imgdata = image_from_file(self.path)

    def set_path(self, path):
        self.path = path

    def get_image(self):
        if settings.art.get("dynamic_background"):
            self.bg_color = dominant_color(self.imgdata)
            self.fg_color = foreground_for(self.bg_color)
        return self.imgdata


class InlineCoverArt(CoverArt):
    def __init__(self, buffer):
        super().__init__()
        self.imgdata = None
        self.kind = "inline"
        if buffer:
            self.set_from_buffer(buffer)

    def set_from_buffer(self, buffer):
        self.imgdata = image_from_buffer(buffer)
        if settings.art.get("dynamic_background"):
            self.bg_color = dominant_color(self.imgdata)
            self.fg_color = foreground_for(self.bg_color)

    def get_image(self):
        return self.imgdata
