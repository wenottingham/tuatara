# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import os
import random
import sys

import m3u8
from urllib3.util import parse_url

from tuatara.playlist_entry import PlaylistEntry

interesting_ext = [".flac", ".mp3", ".m4a", ".opus"]


def parse_m3u(path):
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


def parse_file(path, allow_m3u=False):
    for ext in interesting_ext:
        if path.lower().endswith(ext):
            return [PlaylistEntry(path)]
    if allow_m3u:
        if path.lower().endswith(".m3u") or path.lower().endswith("m3u8"):
            return parse_m3u(path)
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


def create_playlist(items):
    playlist = []
    for item in items:
        if os.path.isfile(item):
            content = parse_file(item, True)
            if content:
                playlist += content
        elif os.path.isdir(item):
            playlist += parse_directory(item)
        else:
            parsed_url = parse_url(item)
            if parsed_url.scheme:
                content = parse_file(item, True)
                playlist += content
            else:
                sys.stderr.write(f"Error: No such file or directory: {item}\n")
                return []
    return playlist


def shuffle(playlist):
    # Shuffles IN PLACE
    r = len(playlist) - 1
    for i in range(r):
        j = random.randint(i, r)
        temp = playlist[i]
        playlist[i] = playlist[j]
        playlist[j] = temp
