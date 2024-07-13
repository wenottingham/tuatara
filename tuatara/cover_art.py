# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0+
#

from tuatara.image_utils import image_from_file, image_from_buffer, dominant_color


class CoverArt:
    def __init__(self):
        self.imgdata = None
        self.bg_color = None
        pass

    def get_image(self):
        pass


class FileCoverArt(CoverArt):
    def __init__(self, path):
        super().__init__()
        self.kind = "file"
        if path:
            self.set_path(path)
        else:
            self.path = None

    def set_path(self, path):
        self.path = path

    def get_image(self):
        self.imgdata = image_from_file(self.path)
        self.bg_color = dominant_color(self.imgdata)
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
        self.bg_color = dominant_color(self.imgdata)

    def get_image(self):
        return self.imgdata
