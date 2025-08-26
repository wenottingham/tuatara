# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import os
import random

import m3u8

from tuatara.playlist_entry import PlaylistEntry

interesting_ext = [".flac", ".mp3", ".m4a", ".opus"]


def parse_file(path, allow_m3u=False):
    for ext in interesting_ext:
        if path.lower().endswith(ext):
            return [PlaylistEntry(path)]
    if allow_m3u:
        if path.lower().endswith(".m3u") or path.lower().endswith("m3u8"):
            playlist = []
            pl = m3u8.load(path)
            for entry in pl.segments:
                if not entry.base_uri or entry.absolute_uri == entry.uri:
                    # Is a URL, assume it's valid
                    playlist.append(PlaylistEntry(entry.uri))
                else:
                    # No URL, check file exists
                    if os.path.exists(entry.uri):
                        playlist.append(PlaylistEntry(entry.uri))
            if playlist != []:
                return playlist
    return None


def parse_directory(path):
    playlist_entries = []
    for dirpath, dirs, files in os.walk(path):
        for fname in files:
            filename = os.path.join(dirpath, fname)
            fc = parse_file(filename)
            if fc:
                playlist_entries += fc
    return playlist_entries


def shuffle(playlist):
    # Shuffles IN PLACE
    r = len(playlist) - 1
    for i in range(r):
        j = random.randint(i, r)
        temp = playlist[i]
        playlist[i] = playlist[j]
        playlist[j] = temp
