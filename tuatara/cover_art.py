# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0+
#

import io


from PIL import Image, ImageEnhance, UnidentifiedImageError

from tuatara.settings import settings


class CoverArt:
    def __init__(self):
        self.imgdata = None
        pass

    def get_image(self):
        pass

    def argb_and_enhance(self, image):
        if image.mode == "RGB":
            image = image.convert("RGBA")
        if image.mode == "RGBA":
            r, g, b, a = image.split()
            image = Image.merge("RGBA", (b, g, r, a))
        image = ImageEnhance.Brightness(image).enhance(
            settings.art.get("brightness_adj")
        )
        image = ImageEnhance.Contrast(image).enhance(settings.art.get("contrast_adj"))
        return image


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
        try:
            img = Image.open(self.path)
        except UnidentifiedImageError:
            return None
        img.load()
        self.imgdata = self.argb_and_enhance(img)
        return self.imgdata


class InlineCoverArt(CoverArt):
    def __init__(self, buffer):
        super().__init__()
        self.imgdata = None
        self.kind = "inline"
        if buffer:
            self.set_from_buffer(buffer)

    def set_from_buffer(self, buffer):
        iobuffer = io.BytesIO(buffer)
        try:
            img = Image.open(iobuffer)
        except UnidentifiedImageError:
            return
        img.load()
        self.imgdata = self.argb_and_enhance(img)

    def get_image(self):
        return self.imgdata
