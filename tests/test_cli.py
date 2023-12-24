import os
import sys
import tomllib

from argparse import ArgumentParser


if not sys.warnoptions:
    import warnings

    warnings.simplefilter("ignore")  # silence gi import warning

from tuatara.main import setup_config
from tuatara.settings import settings


def mockexit(parser, status=0, message=""):
    sys.stdout.write(message)
    return status


def test_help_in_readme(capsys, monkeypatch):
    monkeypatch.setattr(ArgumentParser, "exit", mockexit)
    with open("README.md", "r") as f:
        readme = f.read()

    setup_config(["-h", "dummy.flac"])
    cap = capsys.readouterr()
    assert cap.out in readme


def test_cli_args(tmp_path):
    newfile = """
[art]
dither = "random"
"""
    conf_file = os.path.join(tmp_path, "test.toml")
    with open(conf_file, "w") as f:
        f.write(newfile)

    setup_config(["-d", "--debugfile", "foo.log", "-f", conf_file, "dummy.flac"])

    assert settings._settings.get("debug") is True
    assert settings._settings.get("debugfile") == "foo.log"
    assert settings._settings.get("art").get("dither") == "random"


def test_version(capsys, monkeypatch):
    monkeypatch.setattr(ArgumentParser, "exit", mockexit)

    with open("pyproject.toml", "rb") as f:
        pyproj = tomllib.load(f)
    version = pyproj.get("tool").get("poetry").get("version")

    setup_config(["--version", "dummy.flac"])

    cap = capsys.readouterr()
    assert cap.out == f"tuatara {version}\n"
