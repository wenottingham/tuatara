# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import os

from threading import Thread

from urllib3.util import parse_url

from tuatara.cover_art import FileCoverArt
from tuatara.cover_art_fetcher import fetchers
from tuatara.sanitize import sanitize_artist, sanitize_album
from tuatara.settings import cache_dir, debug, settings


class PlaylistEntry:
    def __init__(self, url):
        self.cover_art = None
        self.title = None
        self.album = None
        self.artist = None
        self.track = None
        self.track_total = None
        self.fetch_status = "not_started"
        self.set_url(url)

    def __str__(self):
        if not self.title:
            return self.url
        else:
            return f"{self.title} - {self.artist} - {self.album}"

    def set_url(self, url):
        parsed_url = parse_url(url)
        if parsed_url.scheme is None:
            # Assume file
            if url.startswith("/"):
                self.url = url
            else:
                self.url = os.path.join(os.getcwd(), url)
        else:
            self.url = url

    def find_cover_art(self):
        def fetch(fetchers, cached_art_path):
            for name, fetcher in fetchers:
                art_url = fetcher.fetch(self)
                if not art_url:
                    continue

                art = fetcher.download(art_url, cached_art_path)
                if not art:
                    continue
                self.cover_art = art
                self.fetch_status = "success"
                debug(f"Using downloaded {name} art for {self}")
                return
            self.fetch_status = "failed"

        if self.cover_art:
            return

        parsed_url = parse_url(self.url)
        # Check directory
        if parsed_url.scheme is None:
            directory = os.path.dirname(self.url)
            with os.scandir(directory) as direntries:
                for entry in direntries:
                    if entry.is_file() and (
                        entry.name == "cover.jpg" or entry.name == "cover.png"
                    ):
                        debug(f"Using in-directory {entry.name} for {self}")
                        self.cover_art = FileCoverArt(
                            os.path.join(directory, entry.name)
                        )
                        return

        if not self.album or not self.artist:
            self.fetch_status = "failed"
            return

        # Check cache
        s_artist = sanitize_artist(self.artist)
        s_album = sanitize_album(self.album)
        fname = f"{s_artist}-{s_album}.art"
        cached_art_path = os.path.join(cache_dir(), fname)
        if os.path.exists(cached_art_path):
            debug(f"Using cached {cached_art_path} for {self}")
            self.cover_art = FileCoverArt(cached_art_path)
            return

        # Try to download
        configured_fetchers = []
        for name in settings.get_art().get("fetchers"):
            fetcher = fetchers.get(name)
            if not fetcher:
                debug(f"No fetcher named {name}")
                continue
            configured_fetchers.append((name, fetcher))

        if configured_fetchers:
            self.fetch_status = "fetching"

            Thread(target=fetch, args=[configured_fetchers, cached_art_path]).start()
        else:
            debug("No configured fetchers")
            self.fetch_status = "failed"
