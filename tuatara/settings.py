# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import os
import sys
import tomllib

from datetime import datetime

version = "0.6.1"


class Settings:
    def __init__(self):
        self._settings = {
            "debug": False,
            "debugfile": f"tuatara-{datetime.now().isoformat()}.log",
            "art": {
                "fetchers": ["apple", "musicbrainz"],
                "dynamic_background": True,
                "ascii_truecolor": False,
                "font_ratio": 2.0,
                "brightness_adj": 0.75,
                "contrast_adj": 1.25,
                "visualization": "synaescope",
            },
        }
        self._debugobj = None

    def validate_fetchers(self, datum):
        if isinstance(datum, list) and set(datum).issubset(("apple", "musicbrainz")):
            return 0
        sys.stderr.write(
            "Error: 'fetchers' must be a list of fetchers. Set to [] to disable fetching\n"
        )
        return 1

    def validate_dynamic_background(self, datum):
        if isinstance(datum, bool):
            return 0
        sys.stderr.write("Error: 'dynamic_background' must be true or false\n")
        return 1

    def validate_ascii_truecolor(self, datum):
        if isinstance(datum, bool):
            return 0
        sys.stderr.write("Error: 'ascii_truecolor' must be true or false\n")
        return 1

    def validate_font_ratio(self, datum):
        if (isinstance(datum, float) or isinstance(datum, int)) and datum > 0:
            return 0
        sys.stderr.write("Error: 'font_ratio' must be a positive number\n")
        return 1

    def validate_visualization(self, datum):
        if isinstance(datum, str):
            return 0
        sys.stderr.write("Error: 'visualization' must be a string\n")
        return 1

    def validate_brightness_adj(self, datum):
        if isinstance(datum, float) and datum >= 0 and datum <= 2:
            return 0
        sys.stderr.write("Error: 'brightness_adj' must be between 0 and 2\n")
        return 1

    def validate_contrast_adj(self, datum):
        if isinstance(datum, float) and datum >= 0 and datum <= 2:
            return 0
        sys.stderr.write("Error: 'contrast_adj' must be between 0 and 2\n")
        return 1

    def validate_art_settings(self, data):
        errors = 0
        for item in data.keys():
            datum = data[item]
            func = getattr(self, f"validate_{item}")
            errors += func(datum)
        return errors == 0

    def load(self, path):
        with open(path, "rb") as f:
            data = tomllib.load(f)
        if not self.validate_art_settings(data["art"]):
            sys.stderr.write(f"Error reading {path}\n")
            return False
        if "debugfile" in data.keys():
            self.set_debugfile(data.get("debugfile"))
        if "debug" in data.keys():
            self.set_debug(data.get("debug"))
        if "art" in data.keys():
            self.merge_art(data.get("art"))
        return True

    def get_debug(self):
        return self._settings["debug"]

    def set_debug(self, value):
        self._settings["debug"] = value

    def set_debugfile(self, value):
        if isinstance(value, str):
            self._settings["debugfile"] = value
        else:
            sys.stderr.write("Error: debugfile must be a string\n")
            return False

    def open_debugfile(self):
        if not self._debugobj:
            fname = self._settings["debugfile"]
            try:
                self._debugobj = open(fname, "w")
            except Exception as e:
                sys.stderr.write(f"Error: cannot open {fname}: {e}")
                return None
        return self._debugobj

    def get_art(self):
        return self._settings["art"]

    def merge_art(self, data):
        if self.validate_art_settings(data):
            self._settings["art"] = self._settings["art"] | data

    debug = property(fget=get_debug, fset=set_debug)

    art = property(fget=get_art, fset=merge_art)


def config_dir():
    return os.getenv("XDG_CONFIG_HOME") or os.path.join(os.getenv("HOME"), ".config")


def cache_dir():
    prefix = os.getenv("XDG_CACHE_HOME") or os.path.join(os.getenv("HOME"), ".cache")
    return os.path.join(prefix, "tuatara", "artwork")


def debug(message):
    if not settings.debug:
        return
    debugfile = settings.open_debugfile()
    if not debugfile:
        return
    for line in message.split("\n"):
        debugfile.write(f"DEBUG: {line}\n")
    debugfile.flush()


settings = Settings()
