
tuatara
=======

tuatara is a text-mode music player, written in Python.

# Description

tuatara plays local music files. It can play single files, or play
an entire music library.

## Features

- Simple keyboard controls
- Shuffle mode
- Basic playlist support via .m3u files
- Integrated cover art display

tuatara is not intended for interactive browsing of your library;
tell it what to play, and it plays it.

# Usage

```
usage: tuatara [-h] [-f FILE] [-s] [-d] [--debugfile DEBUGFILE] [--version]
               PATH [PATH ...]

Text-mode music player

positional arguments:
  PATH                  What to play

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Load configuration from file
  -s, --shuffle         Shuffle content
  -d, --debug           Log debugging information
  --debugfile DEBUGFILE
                        Debug log file name
  --version             show program's version number and exit
```

You can pass multiple files or directories to play on the command line.

## Controls

tuatara is controlled by the keyboard. Basic keys are:

- Space bar: toggle Play/Pause
- 'p', PageUp: Previous track
- 'n', PageDown: Next track
- 'm': Toggle mute
- 'h', '?': Show full keybindings
- 'q': Quit

Controls are not case-sensitive.

# Requirements

System requirements:
- GStreamer (with appropriate plugins)
- GObject-introspection
- libcaca

Python requirements:
- PyGObject
- Pillow
- urllib3
- m3u8

libcaca Python bindings are bundled for convenience.

tuatara is only tested on Linux. macOS or Windows may theoretically work.

# Development

When submitting changes:
- Please add tests in tests/ if it is a testable change
- Ensure code passes both lint and formatting with `ruff` (https://docs.astral.sh/ruff/)

# License & Credits

tuatara is licensed under the GPL, version 3.0 or later.

libcaca bindings by Alex Foulon <alxf@lavabit.com>, originally licensed
under WTFPL-2.0.

# Why 'tuatara'?

The tuatara is a reptile, native to New Zealand. It is the sole surviving
member of the Rhynchocephalia order; its lineage split from modern snakes
and lizards well over 200 million years ago.

Hence, despite existing to this day, it appears to be a relic of a far bygone
era. Much like this software.
