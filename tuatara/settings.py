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

    def validate_art_settings(self, data):
        errors = []
        for item in data.keys():
            datum = data[item]
            match item:
                case "fetchers":
                    if isinstance(datum, list):
                        continue
                    errors.append(
                        "'fetchers' must be a list. Use '[]' to disable art fetching\n"
                    )
                case "dynamic_background" | "ascii_truecolor":
                    if isinstance(datum, bool):
                        continue
                    errors.append(f"'{item}' must be true or false\n")
                case "font_ratio":
                    if isinstance(datum, (float, int)) and datum > 0:
                        continue
                    errors.append("'font_ratio' must be a positive number\n")
                case "visualization":
                    if isinstance(datum, str):
                        continue
                    errors.append(f"'{item}' must be a string\n")
                case "brightness_adj" | "contrast_adj":
                    if isinstance(datum, (float, int)) and datum >= 0:
                        continue
                    errors.append(f"'{item}' must be a non-negative number\n")
        for error in errors:
            sys.stderr.write(f"Error: {error}")
        return len(errors) == 0

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
            self._debugobj = open(self._settings["debugfile"], "w")
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
