import os
import sys
import tomllib

from datetime import datetime

import pytest

from tuatara.settings import Settings, cache_dir, config_dir, debug, settings


def test_sample_matches_defaults():
    defaults = Settings()
    with open("sample-tuatara.toml", "rb") as f:
        sample = tomllib.load(f)
    defaults._settings["debugfile"] = "tuatara.log"
    assert defaults._settings == sample


def test_debug_setting():
    defaults = Settings()

    for value in (True, False):
        defaults.set_debug(value)
        assert defaults._settings.get("debug") == value


def test_debugfile(capsys):
    defaults = Settings()

    now = datetime.now().replace(microsecond=0).isoformat()
    logname = f"tuatara-{now}"
    assert defaults._settings.get("debugfile").startswith(logname)

    defaults.set_debugfile("tt.log")
    assert defaults._settings.get("debugfile") == "tt.log"

    defaults.set_debugfile(3)
    cap = capsys.readouterr()
    assert "Error: debugfile must be a string" in cap.err


def test_validation(capsys):
    defaults = Settings()

    bad_data = {
        "fetchers": 3,
        "font_ratio": -1,
        "dither": True,
        "charset": 32,
        "brightness_adj": 10,
        "contrast_adj": True,
        "visualization": 3.14159,
    }
    error_msgs = (
        "Error: 'fetchers' must be a list of fetchers. Set to [] to disable fetching\n",
        "Error: 'font_ratio' must be a positive number\n",
        "Error: 'dither' must be a string\n",
        "Error: 'charset' must be a string\n",
        "Error: 'brightness_adj' must be between 0 and 2\n",
        "Error: 'contrast_adj' must be between 0 and 2\n",
        "Error: 'visualization' must be a string\n",
    )

    old_settings = defaults._settings
    defaults.merge_art(bad_data)
    cap = capsys.readouterr()
    assert defaults._settings == old_settings
    for msg in error_msgs:
        assert msg in cap.err


def test_override():
    defaults = Settings()

    good_data = {
        "fetchers": ["apple"],
        "font_ratio": 3.14159,
        "dither": "random",
        "charset": "blocks",
        "brightness_adj": 1.0,
        "contrast_adj": 1.99,
        "visualization": "goom",
    }

    defaults.merge_art(good_data)
    for key in good_data.keys():
        assert defaults._settings.get("art").get(key) == good_data.get(key)


def test_load_good(tmp_path):
    defaults = Settings()

    newfile = """
debug = true
debugfile = "tt.log"

[art]
dither = "random"
"""
    conf_file = os.path.join(tmp_path, "test.toml")
    with open(conf_file, "w") as f:
        f.write(newfile)

    defaults.load(conf_file)

    assert defaults._settings.get("debug") is True
    assert defaults._settings.get("debugfile") == "tt.log"
    assert defaults._settings.get("art").get("dither") == "random"


def test_load_bad_file(tmp_path):
    defaults = Settings()

    newfile = """
 🐕➕🌈  🐕➕🌈  🐕➕🌈 
"""
    conf_file = os.path.join(tmp_path, "test.toml")
    with open(conf_file, "w") as f:
        f.write(newfile)

    with pytest.raises(tomllib.TOMLDecodeError):
        defaults.load(conf_file)


def test_load_bad_settings(tmp_path):
    defaults = Settings()

    newfile = """
[art]
dither = true
"""
    conf_file = os.path.join(tmp_path, "test.toml")
    with open(conf_file, "w") as f:
        f.write(newfile)

    old = defaults._settings
    defaults.load(conf_file)
    assert old == defaults._settings


def test_cache_dir(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "/somewhere/over/the/rainbow")
    assert cache_dir() == "/somewhere/over/the/rainbow/tuatara/artwork"

    monkeypatch.delenv("XDG_CACHE_HOME")
    monkeypatch.setenv("HOME", "/myhomedir")
    assert cache_dir() == "/myhomedir/.cache/tuatara/artwork"


def test_config_dir(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/somewhere/over/the/rainbow")
    assert config_dir() == "/somewhere/over/the/rainbow"

    monkeypatch.delenv("XDG_CONFIG_HOME")
    monkeypatch.setenv("HOME", "/myhomedir")
    assert config_dir() == "/myhomedir/.config"


def test_debug(capsys):
    settings.set_debug(True)
    settings._debugobj = sys.stderr

    debug("Test message")
    cap = capsys.readouterr()
    assert cap.err == "DEBUG: Test message\n"
