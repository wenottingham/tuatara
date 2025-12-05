# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import json
import os
import traceback

from difflib import SequenceMatcher
from urllib.parse import quote

import urllib3

from tuatara.cover_art import FileCoverArt
from tuatara.sanitize import sanitize_artist, sanitize_album
from tuatara.settings import settings, debug, version


class ArtFetcher:
    def __init__(self):
        self.http = urllib3.PoolManager()

    def fetch(self, track): ...

    def request(self, url, log, method="GET", statuses=[200], **kwargs):
        try:
            response = self.http.request(method, url=url, **kwargs)
        except urllib3.exceptions.HTTPError as ex:
            debug(f"{log} of {url} failed with an exception")
            if settings.debug:
                traceback.print_exception(ex, file=settings._debugobj)
                settings._debugobj.flush()
            return None
        if response.status not in statuses:
            debug(f"{log} of {url} failed with {response.status}")
            return None
        return response

    def download(self, url, dest):
        directory = os.path.dirname(dest)
        os.makedirs(directory, mode=0o755, exist_ok=True)
        resp = self.request(url, "Download")
        if resp is None:
            return None
        with open(dest, "wb") as f:
            f.write(resp.data)
        return FileCoverArt(dest)


class AppleArtFetcher(ArtFetcher):
    def __init__(self):
        super().__init__()
        self.headers = {
            "Accept": "application/json",
            # We're totally a web browser!
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        }

    def fetch(self, track):
        def download_url(result):
            return result["artworkUrl100"].replace("100x100bb", "2000x2000bb")

        artist = sanitize_artist(track.artist)
        album = sanitize_album(track.album)
        tracks = track.track_total

        debug(f"Finding art for {track} via Apple Music…")
        querystr = quote(f"{artist} {album}")
        path = (
            f"https://itunes.apple.com/search?media=music&entity=album&term={querystr}"
        )

        resp = self.request(path, "Initial search", headers=self.headers)
        if resp is None:
            return None
        jsondata = resp.json()
        url = None
        fallback_url = None
        fuzzy_url = None
        results = jsondata["results"]
        debug("Search results returned:")
        debug(json.dumps(jsondata, indent=4))

        if tracks:
            results = sorted(
                results, key=lambda x: abs(x.get("trackCount") - tracks), reverse=True
            )

        for result in results:
            r_artist = sanitize_artist(result["artistName"])
            r_album = sanitize_album(result["collectionName"])
            r_tracks = result["trackCount"]

            if SequenceMatcher(None, artist, r_artist).ratio() < 0.6:
                continue
            if SequenceMatcher(None, album, r_album).ratio() < 0.6:
                continue

            if tracks:
                if artist == r_artist and album == r_album:
                    if tracks == r_tracks:  # exact match
                        url = download_url(result)
                        break
                    else:
                        fallback_url = download_url(result)
                else:
                    fuzzy_url = download_url(result)
            else:
                if artist == r_artist and album == r_album:  # exact match
                    url = download_url(result)
                    break
                else:
                    fuzzy_url = download_url(result)

        url = url or fallback_url or fuzzy_url
        if not url:
            debug("No results found")
            return None

        debug(f"Using art from {url}")
        return url


class MusicBrainzArtFetcher(ArtFetcher):
    def __init__(self):
        super().__init__()
        self.headers = {
            "Accept": "application/json",
            # These folks care, we'll be truthful.
            "User-Agent": f"Tuatara/{version} (notting@splat.cc)",
        }

    def fetch(self, track):
        artist = sanitize_artist(track.artist)
        album = sanitize_album(track.album)
        tracks = track.track_total

        debug(f"Finding art for {track} via MusicBrainz…")
        path = f"https://musicbrainz.org/ws/2/artist?limit=5&query={artist}"
        resp = self.request(path, "Artist search", headers=self.headers)
        if resp is None:
            return None
        jsondata = resp.json()
        if jsondata["count"] == 0:
            debug("No artists found")
            return None

        debug("Artist search returned:")
        debug(json.dumps(jsondata, indent=4))

        # Go with the first artist
        artist_id = jsondata["artists"][0]["id"]

        path = f'https://musicbrainz.org/ws/2/release?query=release:"{album}" AND arid:{artist_id}'
        if tracks:
            path += f" AND tracksmedium:{tracks}"
        resp = self.request(path, "Album search", headers=self.headers)
        if resp is None:  # pragma: no cover
            return None
        jsondata = resp.json()

        if jsondata["count"] == 0:
            debug("No albums found")
            return None

        debug("Album search returned:")
        debug(json.dumps(jsondata, indent=4))

        # Filter to the good matches
        results = list(filter(lambda x: x["score"] > 90, jsondata["releases"]))

        # MusicBrainz search isn't idempotent for multiple score=100 entries
        results = sorted(results, key=lambda x: (x["score"], x["id"]))

        ids = [x["id"] for x in results]
        debug(f"Filtered album search yielded {ids}")

        url = None
        for mbid in ids:
            path = f"https://coverartarchive.org/release/{mbid}/front"

            resp = self.request(
                path,
                "Musicbrainz art redirect",
                method="HEAD",
                statuses=[200, 307],
                headers=self.headers,
                redirect=False,
            )

            if resp and resp.status == 307:
                url = resp.get_redirect_location()
                break

        if not url:
            debug("No art found for album IDs")
            return None

        debug(f"Using art from {url}")
        return url


fetchers = {"apple": AppleArtFetcher(), "musicbrainz": MusicBrainzArtFetcher()}
