
tuatara
=======

tuatara is a text-mode music player, written in Python.

# Description

tuatara plays local music files. It can play single files, or play
an entire music library.

# Requirements and installation

System requirements:
- Python >= 3.11
- GStreamer (with appropriate plugins)
- GObject-introspection

Python requirements:
- PyGObject
- Pillow
- urllib3
- m3u8
- blessed

tuatara can be installed from the [Releases](https://github.com/wenottingham/tuatara/releases) page on GitHub.

Download and install the .whl file with pip, or download and use the pex file
for your system's python interpreter.

tuatara is only tested on Linux. macOS or Windows may theoretically work.

# Usage

To start with tuatara, just pass a file, directory of music files, or a URL
on the commandline.

Example:
```
tuatara /path/to/my/music/library /path/to/some/other/files
```

Full usage:

```
usage: tuatara [-h] [-f FILE] [-s] [-d] [--debugfile DEBUGFILE] [--version]
               PATH [PATH ...]
```

Options:
- `-h`, `--help`: show a list of commandline options
- `-f <FILENAME>`, `--file <FILENAME>`:  Load configuration from a particular file. See "Configuration" below.
- `-s`, `--shuffle`: Shuffle content
- `-d`, `--debug`: Log debugging output to a log file
- `--debugfile <FILENAME>`: Filename to use when logging debug output
- `--version`: Show version and exit

# Configuration

tuatara is configured by a TOML-formatted configuration file.
Configuration is read from the first file found in the following manner:

- Any filename passed via `-f` on the commandline
- `tuatara.toml` in the current working directory
- `.config/tuatara.toml` in the user's home directory (or XDG_CONFIG_HOME, if set)

## Sample configuration

```
debug = false
debugfile = 'tuatara.log'

[art]
fetchers = ['apple', 'musicbrainz']
dynamic_background = true
font_ratio = 2.0
brightness_adj = 0.75
contrast_adj = 1.25
visualization = 'synaescope'
```

Valid configuration parameters are:

### Main section

- debug: Whether to log debugging information. Default is `false`
- debugfile: File to use for debugging. Default is `tuatara-<timestamp>.log` in the current directory

### [art] section
- fetchers: A list of services to use to fetch cover art. Options can include 'apple' and 'musicbrainz'. See "Cover art", below.
- dynamic_background: Whether to automatically set the background color based on the track's cover art. Default is `true`.
- font_ratio: In order to keep cover art in a normal aspect ratio, we must approximate the ratio of the terminal font height to its width. Default is `2.0`.
- brightness_adj: Percentage adjustment (in decimal) of the cover art image's brightness before converting to ASCII art. For no adjustment, set to `1.0`. Default is `0.75`.
- contrast_adj: Percentage adjustment (in decimal) of the cover art image's contrast before converting to ASCII art. For no adjustment, set to `1.0`. Default is `0.75`.
- visualization: Visualization plugin to use. Set to `'none'` to disable visualization. Options include `'synaescope'`, `'spectrascope'`, `'spacescope'`, `'wavescope'`, and `'goom'`. See "Visualization", below. Default is `synaescope`.

# Controls

tuatara is controlled by the keyboard.

Key controls are:

- ?, h: Show a help screen
- Escape: Dismiss the help screen
- Space: Toggle play/pause
- Left arrow: Seek backwards 10 seconds
- Right arrow: Seek forwards 10 seconds
- p, PageUp: Go to previous track
- n, PageDown: Go to next track
- m: Toggle mute/unmute
- v: Toggle display of visualization/cover art
- +, =: Volume up
- -, _: Volume down
- q: Quit the program

Key controls are not case-sensitive.

# Features

## Cover art

tuatara shows cover art for the currently playing track. Cover art comes
from the following locations:

- Inline as a tag in the currently playing file
- `cover.png` or `cover.jpg` (not case sensitive) in the directory of the currently playing file
- Retrieved via a cover art source and stored in tuatara's cache directory (`.cache/tuatara/artwork` in the user's home directory, subject to the environment variable XDG_CACHE_HOME.)

Cover art is stored in the cache directory as:

```
{artist}-{album title}.art
```

Artist and album title are lowercased, and certain punctuation and special characters are removed.

Cover art can come from one of two sources:
- apple: Apple Music/iTunes cover art archive
- musicbrainz: Cover Art Archive / Musicbrainz

Care is taken to find cover art in most cases, but it is possible that it
may not always be correctly fetched. If you need more comprehensive support,
we recommend the use of a tool like [beets](https://beets.io) to
retrieve cover art and embed it directly in the file or place it in the music
directory.

Cover art fetching is controlled by the `fetchers` parameter in the
configuration file. You can adjust the priority, remove a source, or set it
to `[]` to disable art fetching entirely.

## Visualization

tuatara optionally shows a visualization of the playing track instead of
cover art.

The following visualization options are available:

- spacescope: Simple stereo visualizer
- spectrascope: Simple frequency spectrum scope
- synaescope: Creates video visualizations of audio input, using stereo and pitch information
- wavescope: Simple waveform oscilloscope
- goom: Creates warping structures based on the audio input

For more information, see the [gstreamer documentation](https://gstreamer.freedesktop.org/documentation/audiovisualizers/index.html).

Visualization is controlled by the `visualization` parameter in the
configuration file. Set it to your preferred visualization, or set it to
`none` to disable it.

#### NOTE: Visualization requires running on a truecolor terminal.

## Dynamic background color

tuatara will set the background color dynamically based on the cover art's
color palette.

To disable this, adjust the `dynamic_background` parameter in the
configuration file.

#### NOTE: Dynamic background color requires running on a truecolor terminal.

## Playlist support

m3u files are supported as input. They can contain either local files, or
HTTP URLs.
