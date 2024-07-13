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
    img = _enhance(img)
    return img


def image_from_buffer(buffer):
    iobuffer = io.BytesIO(buffer)
    try:
        img = Image.open(iobuffer)
    except UnidentifiedImageError:
        return None
    img.load()
    img = _enhance(img)
    return img


def image_from_pixbuf(pixbuf):
    if not pixbuf:
        return None
    data = pixbuf.get_pixels()
    mode = "RGB"
    if pixbuf.props.has_alpha is True:
        mode = "RGBA"
    img = Image.frombytes(mode, (pixbuf.props.width, pixbuf.props.height), data, "raw")
    return img


def dominant_color(img):
    # Reasonably fast colorthief using just Pillow
    #
    # Quantize the image, throw out "mostly white", pick the most used
    quantimg = img.quantize().convert("RGB")
    colors = quantimg.getcolors()
    colors = list(filter(lambda x: sum(x[1][0:3]) < 700, colors))
    colors.sort(reverse=True)
    color = None
    for i in range(len(colors)):
        # Avoid black unless it's really dominant
        if sum(colors[i][1][0:3]) > 100 or colors[i][0] / colors[i + 1][0] > 20:
            color = colors[i][1]
            break
    if not color:
        color = (0, 0, 0)
    return color
