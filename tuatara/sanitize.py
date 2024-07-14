# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import re


def sanitize_artist(item):
    item = item.lower()
    item = re.sub("&", " and ", item, re.IGNORECASE)
    item = re.sub(r"\+", " and ", item, re.IGNORECASE)
    return " ".join(item.split())


def sanitize_album(item):
    item = sanitize_artist(item)
    item = re.sub(r" [\(\[{]disc [^\)\]}]+[\)\]}]", "", item, re.IGNORECASE)
    return " ".join(item.split())
