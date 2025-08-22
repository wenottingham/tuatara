# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import json
import os
import re
import traceback

from urllib.parse import quote

import urllib3

from tuatara.cover_art import FileCoverArt
from tuatara.sanitize import sanitize_artist, sanitize_album
from tuatara.settings import settings, debug, version


class ArtFetcher:
    def __init__(self):
        self.http = urllib3.PoolManager()

    def fetch(self, track):
        # implemented in subclasses
        pass

    def get(self, url, log, headers=None):
        try:
            response = self.http.request("GET", url=url, headers=headers)
        except urllib3.exceptions.HTTPError as ex:
            debug(f"{log} of {url} failed with an exception")
            if settings.debug:
                traceback.print_exception(ex, file=settings._debugobj)
                settings._debugobj.flush()
            return None
        if response.status != 200:
            debug(f"{log} of {url} failed with {response.status}")
            return None
        return response

    def download(self, url, dest):
        directory = os.path.dirname(dest)
        os.makedirs(directory, mode=0o755, exist_ok=True)
        resp = self.get(url, "Download")
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

        s_artist = sanitize_artist(track.artist)
        s_album = sanitize_album(track.album)
        tracks = track.track_total

        debug(f"Finding art for {track} via Apple Music…")
        querystr = quote(f"{s_artist} {s_album}")
        path = (
            f"https://itunes.apple.com/search?media=music&entity=album&term={querystr}"
        )

        resp = self.get(path, "Initial search", headers=self.headers)
        if resp is None:
            return None
        jsondata = resp.json()
        if jsondata["resultCount"] < 1:
            debug("No results found")
            return None
        url = None
        fallback_url = None
        fuzzy_url = None
        results = jsondata["results"]
        debug("Search results returned:")
        debug(json.dumps(jsondata, indent=4))

        if tracks:
            results = reversed(
                sorted(results, key=lambda x: abs(x.get("trackCount") - tracks))
            )

        for result in results:
            r_artist = sanitize_artist(result["artistName"])
            r_album = sanitize_album(result["collectionName"])
            r_tracks = result["trackCount"]

            if s_artist not in r_artist:
                continue
            if s_album not in r_album:
                continue

            if tracks:
                if s_artist == r_artist and s_album == r_album:
                    if tracks == r_tracks:  # exact match
                        url = download_url(result)
                        break
                    else:
                        fallback_url = download_url(result)
                else:
                    fuzzy_url = download_url(result)
            else:
                if s_artist == r_artist and s_album == r_album:  # exact match
                    url = download_url(result)
                    break
                else:
                    fuzzy_url = download_url(result)

        url = url or fallback_url or fuzzy_url
        if not url:
            debug("No suitable album found")
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
        def multi_filter(collection_item, tracks):
            for disc in collection_item["media"]:
                if disc["track-count"] == tracks:
                    return True
            return False

        s_artist = sanitize_artist(track.artist)
        s_album = sanitize_album(track.album)
        tracks = track.track_total
        multidisc = False
        if re.search(r" [\(\[{]disc [^\)\]}]+[\)\]}]", track.album, re.IGNORECASE):
            multidisc = True

        debug(f"Finding art for {track} via MusicBrainz…")
        path = f"https://musicbrainz.org/ws/2/artist?limit=5&query={s_artist}"
        resp = self.get(path, "Artist search", headers=self.headers)
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

        path = f'https://musicbrainz.org/ws/2/release?query=release:"{s_album}" AND arid:{artist_id}'
        if tracks:
            path += f" AND tracksmedium:{tracks}"
        resp = self.get(path, "Album search", headers=self.headers)
        if resp is None:
            return None
        jsondata = resp.json()

        if jsondata["count"] == 0:
            debug("No albums found")
            return None

        debug("Album search returned:")
        debug(json.dumps(jsondata, indent=4))

        # Filter to the good matches
        results = list(filter(lambda x: x["score"] > 90, jsondata["releases"]))

        # Filter by number of tracks
        if tracks and multidisc:
            debug(f"Filtering by {tracks} tracks in a multidisc collection")
            filtered_results = list(filter(lambda x: multi_filter(x, tracks), results))
        else:
            filtered_results = results

        # MusicBrainz search isn't idempotent for multiple score=100 entries
        filtered_results = sorted(filtered_results, key=lambda x: (x["score"], x["id"]))

        ids = list(map(lambda x: x["id"], filtered_results))
        debug(f"Filtered album search yielded {ids}")

        url = None
        for mbid in ids:
            path = f"https://coverartarchive.org/release/{mbid}/front"

            try:
                resp = self.http.request(
                    "HEAD", path, headers=self.headers, redirect=False
                )
            except urllib3.exceptions.HTTPError:
                debug(f"HEAD of {mbid} failed with an exception")
                continue

            if resp.status == 307:
                url = resp.get_redirect_location()
                break

        if not url:
            debug("No art found for album IDs")
            return None

        debug(f"Using art from {url}")
        return url


fetchers = {"apple": AppleArtFetcher(), "musicbrainz": MusicBrainzArtFetcher()}
