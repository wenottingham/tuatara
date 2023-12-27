# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0+
#

import io

import gi

from PIL import Image, ImageEnhance, UnidentifiedImageError

from tuatara.settings import settings

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402, F401


def _argb(image):
    if image.mode == "RGB":
        image = image.convert("RGBA")
    if image.mode == "RGBA":
        r, g, b, a = image.split()
        image = Image.merge("RGBA", (b, g, r, a))
    return image


def _enhance(image):
    image = ImageEnhance.Brightness(image).enhance(settings.art.get("brightness_adj"))
    image = ImageEnhance.Contrast(image).enhance(settings.art.get("contrast_adj"))
    return image


def image_from_file(path):
    try:
        img = Image.open(path)
    except UnidentifiedImageError:
        return None
    img.load()
    img = _argb(img)
    img = _enhance(img)
    return img


def image_from_buffer(buffer):
    iobuffer = io.BytesIO(buffer)
    try:
        img = Image.open(iobuffer)
    except UnidentifiedImageError:
        return None
    img.load()
    img = _argb(img)
    img = _enhance(img)
    return img


def image_from_pixbuf(pixbuf):
    data = pixbuf.get_pixels()
    mode = "RGB"
    if pixbuf.props.has_alpha is True:
        mode = "RGBA"
    img = Image.frombytes(mode, (pixbuf.props.width, pixbuf.props.height), data, "raw")
    img = _argb(img)
    return img
