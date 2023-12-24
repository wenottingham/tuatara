#!/usr/bin/python
#
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0+
#

import argparse
import os
import random
import sys

from urllib3.util import parse_url

from gi.repository import GLib

from tuatara.interface import Interface
from tuatara.playlist import parse_directory, parse_file
from tuatara.player import Player
from tuatara.settings import settings, config_dir


def setup_config(args=sys.argv[1:]):
    def load_config(args):
        if args.file:
            return settings.load(args.file)
        if os.path.exists("tuatara.toml"):
            return settings.load("tuatara.toml")
        default_config = os.path.join(config_dir(), "tuatara.toml")
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
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    args = parser.parse_args(args)

    if not load_config(args):
        return 1
    if args.debug:
        settings.set_debug(args.debug)
    if args.debugfile:
        settings.set_debugfile(args.debugfile)

    return args


def main():
    args = setup_config()

    playlist = []
    for arg in args.content:
        if os.path.isfile(arg):
            content = parse_file(arg, True)
            if content:
                playlist += content
        elif os.path.isdir(arg):
            playlist += parse_directory(arg)
        else:
            parsed_url = parse_url(arg)
            if parsed_url.scheme:
                content = parse_file(arg, True)
                playlist += content
            else:
                sys.stderr.write(f"Error: No such file or directory: {arg}\n")
                return 1
    if args.shuffle:
        random.shuffle(playlist)
    if playlist == []:
        print("Nothing to play.")
        return 1

    player = Player()
    player.set_playlist(playlist)

    interface = Interface()
    player.set_interface(interface)

    player.cue_from_playlist()
    loop = GLib.MainLoop()
    player.set_mainloop(loop)
    GLib.unix_fd_add_full(
        GLib.PRIORITY_DEFAULT,
        sys.stdin.fileno(),
        GLib.IO_IN,
        interface.process_keys,
        player,
    )
    GLib.timeout_add(120, interface.display_info, player)
    loop.run()

    if player.error:
        interface.exit()
        print(f"Error: {player.error}")
        return 1
    else:
        interface.exit()
        print("All done.")
        return 0
