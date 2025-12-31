import os
import sys
import time

import urllib3
from unittest import mock

from tuatara.cover_art_fetcher import AppleArtFetcher, MusicBrainzArtFetcher
from tuatara.playlist_entry import PlaylistEntry
from tuatara.sanitize import sanitize_artist, sanitize_album
from tuatara.settings import settings

settings.set_debug(True)


def entry(artist, album, tracks=None, path=None):
    p = PlaylistEntry(path or "foo.flac")
    p.artist = artist
    p.album = album
    p.title = None
    p.track_total = tracks
    return p


def sync_find_cover_art(e):
    e.find_cover_art()
    timeout = 15
    while timeout > 0 and e.cover_art is None and e.fetch_status != "failed":
        time.sleep(1)
        timeout -= 1


def test_http_response_handling_apple(capsys):
    with mock.patch("urllib3.PoolManager.request") as urllib3_request:
        urllib3_request.return_value = urllib3.response.HTTPResponse(
            status=403, body=""
        )
        f = AppleArtFetcher()
        settings._debugobj = sys.stderr

        not_a_thing = entry("🐕➕🌈", "🐕➕🌈")
        result = f.fetch(not_a_thing)
        cap = capsys.readouterr()
        assert result is None
        assert "failed with 403" in cap.err


def test_http_response_handling_musicbrainz(capsys):
    with mock.patch("urllib3.PoolManager.request") as urllib3_request:
        urllib3_request.return_value = urllib3.response.HTTPResponse(
            status=403, body=""
        )
        f = MusicBrainzArtFetcher()
        settings._debugobj = sys.stderr

        not_a_thing = entry("🐕➕🌈", "🐕➕🌈")
        result = f.fetch(not_a_thing)
        cap = capsys.readouterr()
        assert result is None
        assert "failed with 403" in cap.err


def test_download_failure(tmp_path, capsys):
    with mock.patch("tuatara.cover_art_fetcher.AppleArtFetcher.fetch") as fetch:
        fetch.return_value = "https://somewhere.over/the/rainbow"
        with mock.patch("urllib3.PoolManager.request") as urllib3_request:
            urllib3_request.return_value = urllib3.response.HTTPResponse(
                status=403, body=""
            )
            settings._settings["art"]["fetchers"] = ["apple"]
            settings._debugobj = sys.stderr

            playlist_entry = entry("🐕➕🌈", "🐕➕🌈")
            sync_find_cover_art(playlist_entry)
            cap = capsys.readouterr()
            assert playlist_entry.cover_art is None
            assert playlist_entry.fetch_status == "failed"
            assert "failed with 403" in cap.err


def test_exception_handling(capsys):
    with mock.patch(
        "urllib3.PoolManager.request",
        side_effect=urllib3.exceptions.HTTPError("Kablooie"),
    ):
        f = AppleArtFetcher()
        settings._debugobj = sys.stderr

        not_a_thing = entry("🐕➕🌈", "🐕➕🌈")
        result = f.fetch(not_a_thing)
        cap = capsys.readouterr()
        assert result is None
        assert "failed with an exception" in cap.err


def test_apple_not_found(capsys):
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    not_a_thing = entry("🤦🤦🤦̣", "")
    result = f.fetch(not_a_thing)
    cap = capsys.readouterr()
    assert "No results found" in cap.err
    assert result is None


def test_apple_false_positive(capsys):
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    no_close_enough_matches = entry("I", "Mother Earth")
    result = f.fetch(no_close_enough_matches)
    cap = capsys.readouterr()
    assert "No results found" in cap.err
    assert result is None


def test_apple_escaped_artist():
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    escaped_artist = entry("Rodrigo y Gabriela & C.U.B.A", "Area 52", tracks=9)
    result = f.fetch(escaped_artist)
    assert "67ce177e-2cbe-967f-b426-b8b1211ca9f0/mzm.tjfoszpj.jpg" in result


def test_apple_artist_match_without_tracks():
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    artist_no_tracks = entry("They Might Be Giants", "Apollo 18")
    result = f.fetch(artist_no_tracks)
    assert "4e2509f-d89f-3309-4653-468f5342a477/603497844593.jpg" in result


def test_apple_artist_match_with_tracks():
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    artist_with_tracks = entry("Janelle Monáe", "The ArchAndroid", tracks=18)
    result = f.fetch(artist_with_tracks)
    assert "9d7e78d-545f-55b3-5991-d51e8ab18970/mzi.xhtuvgtj.jpg" in result


def test_apple_artist_fuzzy_match():
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    fuzzy_match = entry("Janelle Monáe", "The ArchAndroid")
    result = f.fetch(fuzzy_match)
    assert "9d7e78d-545f-55b3-5991-d51e8ab18970/mzi.xhtuvgtj.jpg" in result


def test_apple_closest_match():
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    fuzzy_track_match = entry("Florence + the Machine", "Ceremonials", tracks=16)
    result = f.fetch(fuzzy_track_match)
    assert "43d59e0c-6a9e-7f1a-e41d-badced2f40b4/11UMGIM28690.rgb.jpg" in result


def test_musicbrainz_no_artist(capsys):
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    not_an_artist = entry("🐕➕🌈", "🐕➕🌈")
    result = f.fetch(not_an_artist)
    cap = capsys.readouterr()
    assert result is None
    assert "No artists found" in cap.err


def test_musicbrainz_artist_no_album(capsys):
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    artist_but_not_album = entry("Nine Inch Nails", "🐕➕🌈")
    result = f.fetch(artist_but_not_album)
    cap = capsys.readouterr()
    assert result is None
    assert "No albums found" in cap.err


def test_musicbrainz_escaped_artist():
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    escaped_artist = entry("Rodrigo y Gabriela & C.U.B.A", "Area 52", tracks=9)
    result = f.fetch(escaped_artist)
    assert "mbid-022a1668-525d-427f-bab3-5380701e7108-7245530744.jpg" in result


def test_musicbrainz_artist_without_tracks():
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    artist_no_tracks = entry("Florence + the Machine", "Ceremonials")
    result = f.fetch(artist_no_tracks)
    assert (
        "mbid-11973ebc-0f5a-4aa4-ad79-e194f88d23e6-12512633102.jpg" in result
        or "mbid-35d9978e-a50f-4a36-b437-c371453bc663-39452793011.jpg" in result
    )


def test_musicbrainz_artist_with_tracks():
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    artist_with_tracks = entry("Florence + the Machine", "Ceremonials", tracks=16)
    result = f.fetch(artist_with_tracks)
    assert "mbid-71754346-9a28-4617-ba8d-feb7287e04ad-39453304024.jpg" in result


def test_musicbrainz_multidisc():
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    multidisc = entry(
        "Phish",
        "Live Phish, Volume 03: 2000-09-14: Darien Lake Performing Arts Center, Darien Center, NY, USA (disc 1)",
        tracks=7,
    )
    result = f.fetch(multidisc)
    assert "mbid-e76385ff-427e-4e52-9628-f81350d56d5b-27135810077.jpg" in result


def test_musicbrainz_valid_no_art(capsys):
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    valid_no_art = entry("Terami Hirsch", "Stickfigures")
    result = f.fetch(valid_no_art)
    cap = capsys.readouterr()
    assert result is None
    assert "d0d12752-aa03-4dc2-b391-aa2b40a4b573" in cap.err
    assert "No art found" in cap.err


def test_async_apple(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    settings._settings["art"]["fetchers"] = ["apple"]
    settings.set_debug(False)

    playlist_entry = entry(
        "Rodrigo y Gabriela & C.U.B.A",
        "Area 52",
        tracks=9,
        path="https://example.com/foo.flac",
    )

    sync_find_cover_art(playlist_entry)
    cached_file = f"{sanitize_artist(playlist_entry.artist)}-{sanitize_album(playlist_entry.album)}.art"
    assert playlist_entry.cover_art is not None
    assert playlist_entry.cover_art.path == os.path.join(
        tmp_path, "tuatara", "artwork", cached_file
    )


def test_async_apple_not_found():
    settings._settings["art"]["fetchers"] = ["apple"]
    settings.set_debug(False)

    playlist_entry = entry("🐕➕🌈", "🐕➕🌈")

    sync_find_cover_art(playlist_entry)
    assert playlist_entry.cover_art is None
    assert playlist_entry.fetch_status == "failed"


def test_async_musicbrainz(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    settings._settings["art"]["fetchers"] = ["musicbrainz"]
    settings.set_debug(False)

    playlist_entry = entry(
        "Rodrigo y Gabriela & C.U.B.A",
        "Area 52",
        tracks=9,
        path="https://example.com/foo.flac",
    )

    sync_find_cover_art(playlist_entry)
    cached_file = f"{sanitize_artist(playlist_entry.artist)}-{sanitize_album(playlist_entry.album)}.art"
    assert playlist_entry.cover_art is not None
    assert playlist_entry.cover_art.path == os.path.join(
        tmp_path, "tuatara", "artwork", cached_file
    )


def test_async_musicbrainz_not_found():
    settings._settings["art"]["fetchers"] = ["musicbrainz"]
    settings.set_debug(False)

    playlist_entry = entry("🐕➕🌈", "🐕➕🌈")

    sync_find_cover_art(playlist_entry)
    assert playlist_entry.cover_art is None
    assert playlist_entry.fetch_status == "failed"


def test_no_fetchers(capsys):
    settings._settings["art"]["fetchers"] = ["blep"]
    settings.set_debug(True)
    settings._debugobj = sys.stderr

    playlist_entry = entry("🐕➕🌈", "🐕➕🌈")

    playlist_entry.find_cover_art()
    cap = capsys.readouterr()
    assert playlist_entry.cover_art is None
    assert playlist_entry.fetch_status == "failed"
    assert "No fetcher named blep" in cap.err
    assert "No configured fetchers" in cap.err


def test_no_album_so_dont_bother():
    settings._settings["art"]["fetchers"] = ["apple"]
    settings.set_debug(True)
    settings._debugobj = sys.stderr

    playlist_entry = entry("🐕➕🌈", "")

    playlist_entry.find_cover_art()
    assert playlist_entry.cover_art is None
    assert playlist_entry.fetch_status == "failed"


def test_use_existing_art():
    settings._settings["art"]["fetchers"] = ["apple"]

    playlist_entry = entry("🐕➕🌈", "")

    assert playlist_entry.cover_art is None
    assert playlist_entry.fetch_status == "not_started"

    playlist_entry.cover_art = "Hello"
    playlist_entry.find_cover_art()
    assert playlist_entry.fetch_status == "not_started"
    assert playlist_entry.cover_art == "Hello"


def test_use_cached_art(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    settings._settings["art"]["fetchers"] = ["apple"]
    settings.set_debug(True)
    settings._debugobj = sys.stderr

    playlist_entry = entry(
        "Rodrigo y Gabriela & C.U.B.A",
        "Area 52",
        tracks=9,
        path="https://example.com/foo.flac",
    )

    cached_file = f"{sanitize_artist(playlist_entry.artist)}-{sanitize_album(playlist_entry.album)}.art"
    cache_path = os.path.join(tmp_path, "tuatara", "artwork")
    os.makedirs(cache_path)
    with open(os.path.join(cache_path, cached_file), "w+") as f:
        f.close()
    playlist_entry.find_cover_art()
    cap = capsys.readouterr()
    assert "Using cached" in cap.err
    assert playlist_entry.cover_art is not None
    assert playlist_entry.cover_art.path == os.path.join(cache_path, cached_file)


def test_use_dir_art(tmp_path, capsys):
    settings._settings["art"]["fetchers"] = ["apple"]
    settings.set_debug(True)
    settings._debugobj = sys.stderr

    playlist_entry = entry(
        "Hello",
        "Anyone",
        tracks=9,
        path=f"{tmp_path}/foo.flac",
    )

    with open(os.path.join(tmp_path, "cover.jpg"), "w+") as f:
        f.close()
    playlist_entry.title = "Hi"
    playlist_entry.find_cover_art()
    cap = capsys.readouterr()
    assert "Using in-directory" in cap.err
    assert f"{playlist_entry}" == "Hi - Hello - Anyone"
    assert playlist_entry.cover_art is not None
    assert playlist_entry.cover_art.path == os.path.join(tmp_path, "cover.jpg")


def test_bad_dir_art(tmp_path, capsys):
    settings._settings["art"]["fetchers"] = ["apple"]
    settings.set_debug(True)
    settings._debugobj = sys.stderr

    playlist_entry = entry(
        "Hello",
        "Anyone",
        tracks=9,
        path=f"{tmp_path}/foo.flac",
    )

    with open(os.path.join(tmp_path, "cover.jpg"), "w+") as f:
        f.close()
    os.chmod(os.path.join(tmp_path, "cover.jpg"), 0o000)
    playlist_entry.title = "Hi"
    playlist_entry.find_cover_art()
    cap = capsys.readouterr()
    assert "Cannot read in-directory art" in cap.err
    assert f"{playlist_entry}" == "Hi - Hello - Anyone"
    assert playlist_entry.cover_art is None
