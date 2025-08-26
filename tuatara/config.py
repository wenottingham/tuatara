#!/usr/bin/python
#
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import argparse
import os
import sys

from tuatara.settings import settings, config_dir, version

CONFIG_FILE = "tuatara.toml"


def setup_config(args=sys.argv[1:]):
    def load_config(args):
        if args.file:
            return settings.load(args.file)
        if os.path.exists(CONFIG_FILE):
            return settings.load(CONFIG_FILE)
        default_config = os.path.join(config_dir(), CONFIG_FILE)
        if os.path.exists(default_config):
            return settings.load(default_config)
        return True

    parser = argparse.ArgumentParser(
        prog="tuatara", description="Text-mode music player"
    )
    parser.add_argument(
        "content", metavar="PATH", type=str, nargs="+", help="What to play"
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Load configuration from file",
        action="store",
        default=None,
    )
    parser.add_argument("-s", "--shuffle", help="Shuffle content", action="store_true")
    parser.add_argument(
        "-d", "--debug", help="Log debugging information", action="store_true"
    )
    parser.add_argument("--debugfile", help="Debug log file name", action="store")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    args = parser.parse_args(args)

    if not load_config(args):
        return 1
    if args.debug:
        settings.set_debug(args.debug)
    if args.debugfile:
        settings.set_debugfile(args.debugfile)

    return args
