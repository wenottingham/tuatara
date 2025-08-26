import os

from unittest import mock

from tuatara.playlist import parse_file, parse_directory, shuffle


def test_bad_file():
    pl = parse_file("README.txt")
    assert pl is None


def test_good_file():
    pl = parse_file("foo.flac")
    assert len(pl) == 1
    assert pl[0].url == f"{os.path.join(os.getcwd(), 'foo.flac')}"


def test_good_case_file():
    pl = parse_file("FOO.OPUS")
    assert len(pl) == 1
    assert pl[0].url == f"{os.path.join(os.getcwd(), 'FOO.OPUS')}"


def test_good_abs_file():
    pl = parse_file("/somewhere/over/the/rainbow/foo.flac")
    assert len(pl) == 1
    assert pl[0].url == "/somewhere/over/the/rainbow/foo.flac"


def test_url():
    pl = parse_file("https://example.com/foo.flac")
    assert len(pl) == 1
    assert pl[0].url == "https://example.com/foo.flac"


def test_m3u_default():
    pl = parse_file("https://example.com/playlist.m3u")
    assert pl is None


def test_good_m3u(tmp_path):
    with open(os.path.join(tmp_path, "tmp.flac"), "w") as f:
        f.close()
    playlist_text = f"""
#EXTM3U
#EXTINF:123
test1.flac
#EXTINF:234
https://example.com/test2.flac
#EXTINF:345
{tmp_path}/tmp.flac
"""
    with open(os.path.join(tmp_path, "temp.m3u"), "w") as f:
        f.write(playlist_text)
    pl = parse_file(os.path.join(tmp_path, "temp.m3u"), True)
    for item in pl:
        print(item.url)
    assert len(pl) == 2
    assert pl[0].url == "https://example.com/test2.flac"
    assert pl[1].url == f"{tmp_path}/tmp.flac"


def test_bad_m3u(tmp_path):
    with open(os.path.join(tmp_path, "tmp.flac"), "w") as f:
        f.close()
    playlist_text = f"""
test1.flac
https://example.com/test2.flac
{tmp_path}/tmp.flac
"""
    with open(os.path.join(tmp_path, "temp.m3u"), "w") as f:
        f.write(playlist_text)
    pl = parse_file(os.path.join(tmp_path, "temp.m3u"), True)
    assert pl is None


def test_directory_walk():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("/foo", ["bar", "baz"], ["file.flac"]),
            ("/foo/bar", ["cow"], ["README.txt", "file2.flac"]),
            ("/foo/baz", [], ["file3.flac", "file4.m3u"]),
            ("/foo/bar/cow", [], []),
        ]

        pl = parse_directory("fakedir")
        urls = [x.url for x in pl]
        assert len(pl) == 3
        assert "/foo/file.flac" in urls
        assert "/foo/bar/file2.flac" in urls
        assert "/foo/baz/file3.flac" in urls


def test_shuffle():
    # Technically flaky. Probability of it flaking? Low.
    testlist = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    oldlist = testlist.copy()
    shuffle(testlist)
    assert set(oldlist) == set(testlist)
    assert oldlist != testlist
