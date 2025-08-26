#!/usr/bin/python
#
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import sys

from tuatara.config import setup_config
from tuatara.interface import Interface
from tuatara.playlist import create_playlist, shuffle
from tuatara.player import Player


def main():
    args = setup_config()

    playlist = create_playlist(args.content)

    if playlist == []:
        print("Nothing to play.")
        return 1

    if args.shuffle:
        shuffle(playlist)

    interface = Interface()
    sys.excepthook = interface.excepthook

    player = Player()
    player.set_playlist(playlist)
    player.cue_from_playlist()
    interface.run(player)

    if player.error:
        print(f"Error: {player.error}")
        return 1
    else:
        print("All done.")
        return 0
