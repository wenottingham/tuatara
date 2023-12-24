import sys

from tuatara.cover_art_fetcher import AppleArtFetcher, MusicBrainzArtFetcher
from tuatara.playlist_entry import PlaylistEntry
from tuatara.settings import settings

settings.set_debug(True)


def entry(artist, album, tracks=None):
    p = PlaylistEntry("foo.flac")
    p.artist = artist
    p.album = album
    p.track_total = tracks
    return p


def test_apple_not_found(capsys):
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    not_a_thing = entry("🐕➕🌈", "")
    f.fetch(not_a_thing)
    cap = capsys.readouterr()
    assert "No results found" in cap.err


def test_apple_not_found_but_real(capsys):
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    not_found_for_some_reason = entry(
        "Marnie Stern",
        "This Is It and I Am It and You Are It and So Is That and He Is It and She Is It and It Is It and That Is That",
        9,
    )
    f.fetch(not_found_for_some_reason)
    cap = capsys.readouterr()
    assert "No results found" in cap.err


def test_apple_escaped_artist(capsys):
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    escaped_artist = entry("Rodrigo y Gabriela & C.U.B.A", "Area 52", 9)
    f.fetch(escaped_artist)
    cap = capsys.readouterr()
    assert "67ce177e-2cbe-967f-b426-b8b1211ca9f0/mzm.tjfoszpj.jpg" in cap.err


def test_apple_artist_match_without_tracks(capsys):
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    artist_no_tracks = entry("Tori Amos", "Under the Pink")
    f.fetch(artist_no_tracks)
    cap = capsys.readouterr()
    assert "620df5c5-5cf9-9937-4ef1-8acb5338a217/603497892914.jpg" in cap.err


def test_apple_artist_match_with_tracks(capsys):
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    artist_with_tracks = entry("Tori Amos", "Under the Pink", 12)
    f.fetch(artist_with_tracks)
    cap = capsys.readouterr()
    assert "2ad99479-ebca-7699-81bd-0270270a1829/603497892921.jpg" in cap.err


def test_apple_closest_match(capsys):
    f = AppleArtFetcher()
    settings._debugobj = sys.stderr

    fuzzy_track_match_fetch = entry("Florence + the Machine", "Ceremonials", 16)
    f.fetch(fuzzy_track_match_fetch)
    cap = capsys.readouterr()
    assert "43d59e0c-6a9e-7f1a-e41d-badced2f40b4/11UMGIM28690.rgb.jpg" in cap.err


def test_musicbrainz_no_artist(capsys):
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    not_an_artist = entry("🐕➕🌈", "")
    f.fetch(not_an_artist)
    cap = capsys.readouterr()
    assert "No artists found" in cap.err


def test_musicbrainz_artist_no_album(capsys):
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    artist_but_not_album = entry("Nine Inch Nails", "🐕➕🌈")
    f.fetch(artist_but_not_album)
    cap = capsys.readouterr()
    assert "No albums found" in cap.err


def test_musicbrainz_escaped_artist(capsys):
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    escaped_artist = entry("Rodrigo y Gabriela & C.U.B.A", "Area 52", 9)
    f.fetch(escaped_artist)
    cap = capsys.readouterr()
    assert "mbid-9a5f7dd2-0044-4506-b835-83028cc45a90-15578294208.jpg" in cap.err


def test_musicbrainz_artist_without_tracks(capsys):
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    artist_no_tracks = entry("Florence + the Machine", "Ceremonials")
    f.fetch(artist_no_tracks)
    cap = capsys.readouterr()
    assert "mbid-5e06f918-f14d-44be-bd97-5ffdd9f35d31-19577602268.jpg" in cap.err


def test_musicbrainz_artist_with_tracks(capsys):
    f = MusicBrainzArtFetcher()
    settings._debugobj = sys.stderr

    artist_with_tracks = entry("Florence + the Machine", "Ceremonials", 16)
    f.fetch(artist_with_tracks)
    cap = capsys.readouterr()
    assert "mbid-addc312e-3c20-400e-bbd4-69946bb82a2b-7697873196.jpg" in cap.err
