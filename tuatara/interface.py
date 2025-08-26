# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import os
import signal
import sys
import traceback

from functools import lru_cache

from urllib3.util import parse_url

import blessed

from gi.repository import GLib

from tuatara.image_utils import downconvert

from tuatara.settings import settings, debug, version


class Window:
    def __init__(self):
        self._width = None
        self._height = None
        self._x = None
        self._y = None

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        self._width = width

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        self._height = height

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, left):
        self._left = left

    @property
    def top(self):
        return self._top

    @top.setter
    def top(self, top):
        self._top = top


class Interface:
    def __init__(self):
        self.term = blessed.Terminal()
        if "number_of_colors" in settings.art:
            self.term.number_of_colors = settings.art.get("number_of_colors")
        if self.term.number_of_colors < 256 and settings.art.get("dynamic_background"):
            art = {}
            debug("Dynamic background color unavailable due to limited colors")
            art["dynamic_background"] = False
            settings.merge_art(art)
        if settings.art.get("ascii_truecolor"):
            art = {}
            debug("Dynamic background color unavailable due to `ascii_truecolor`")
            art["dynamic_background"] = False
            settings.merge_art(art)
        self.set_title(f"Tutatara {version}")
        self.help_canvas = self.populate_help()
        self.art_shown = None
        self.help_shown = False
        self.vis_shown = False
        self.current_track = None
        self.mainloop = None
        self.need_resize = True
        self.error = None
        self.colorstr = ""
        signal.signal(signal.SIGWINCH, self.sigwinch_handler)
        signal.signal(signal.SIGINT, self.stop)

    def set_title(self, title):
        sys.stdout.write("\x1b]0;" + title + "\x07")

    def sigwinch_handler(self, signum=None, stack=None):
        self.need_resize = True

    @lru_cache(maxsize=256)
    def set_color(self, colortuple):
        (r, g, b) = colortuple
        return self.term.color_rgb(r, g, b)

    @lru_cache(maxsize=256)
    def set_bg_color(self, colortuple):
        (r, g, b) = colortuple
        return self.term.on_color_rgb(r, g, b)

    def set_size(self):
        text_box = Window()
        art_box = Window()

        ratio = settings.art.get("font_ratio")
        if self.term.width > self.term.height * ratio:
            text_box.width = max(
                self.term.width - int(ratio * self.term.height),
                36,
            )
            text_box.height = self.term.height
            text_box.left = self.term.width - text_box.width
            text_box.top = 0

            art_box.width = self.term.width - text_box.width - 2
            art_box.height = min(
                int(art_box.width // ratio),
                self.term.height - 2,
            )
            art_box.left = 1
            art_box.top = (self.term.height - art_box.height) // 2
        else:
            text_box.width = self.term.width
            text_box.height = max(
                self.term.height - int(self.term.width // ratio),
                7,
            )
            text_box.top = self.term.height - text_box.height
            text_box.left = 0

            art_box.height = self.term.height - text_box.height - 2
            art_box.width = int(art_box.height * ratio)
            art_box.top = 1
            art_box.left = (self.term.width - art_box.width) // 2
        self.art_box = art_box
        self.text_box = text_box
        self.clear_display = True

    def bold_with_bg(self, text):
        text = self.term.bold(text) + self.colorstr
        return text

    def display_info(self, player):
        def display_ascii(image, clear=False):
            RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

            if not image:
                return

            if self.term.number_of_colors < 256 or settings.art.get("ascii_truecolor"):
                ramp = RAMP
                colorfunc = self.set_color
            else:
                ramp = " "
                colorfunc = self.set_bg_color
            output = self.colorstr
            if clear:
                output += self.term.clear

            img = downconvert(
                image,
                self.art_box.width,
                self.art_box.height,
                self.term.number_of_colors,
            )

            grayscale_img = img.convert("L")

            for h in range(self.art_box.height):
                output += self.term.move_xy(self.art_box.left, self.art_box.top + h)
                output += self.colorstr
                for w in range(self.art_box.width):
                    brightness = grayscale_img.getpixel((w, h)) / 255
                    r, g, b = img.getpixel((w, h))[:3]
                    ascii_char = ramp[int(brightness * (len(ramp) - 1))]

                    output += colorfunc((r, g, b)) + ascii_char
                output += self.term.normal

            sys.stdout.write(output)

        def display_str(text, offset):
            def fitted(text):
                if self.term.length(text) <= (self.text_box.width - 2):
                    return text
                else:
                    return self.term.truncate(text, self.text_box.width - 3) + "…"

            text = fitted(text)
            output = self.term.move_xy(
                self.text_box.left,
                self.text_box.top + self.text_box.height // 2 + offset,
            )
            output += self.colorstr
            text += self.colorstr
            output += self.term.center(text, self.text_box.width)
            sys.stdout.write(output)

        if self.need_resize:
            self.set_size()
            self.need_resize = False

        status = player.get_status()
        if status == "finished":
            self.stop()
            return False

        track = player.get_current_track()

        if track != self.current_track:
            self.clear_display = True
            self.art_shown = False
            self.colorstr = ""
        self.current_track = track

        if not track:
            sys.stdout.write(self.term.normal + self.term.clear)
            sys.stdout.flush()
            return True

        if status == "not ready":
            return True

        if self.clear_display:
            self.art_shown = False
            sys.stdout.write(self.term.normal + self.term.clear)
            self.clear_display = False

        if track.title:
            titlestr = track.title
            windowtitle = f"{track.artist} - {track.title}"
        else:
            parsed_url = parse_url(track.url)
            titlestr = os.path.basename(parsed_url.path)
            windowtitle = titlestr
        display_str(self.bold_with_bg(titlestr), -2)
        self.set_title(windowtitle)

        if track.artist:
            display_str(track.artist, -1)

        if track.album:
            display_str(track.album, 0)

        display_str(player.get_status_str(), 2)

        if not track.cover_art and track.fetch_status == "not_started":
            track.find_cover_art()
        if self.vis_shown:
            self.colorstr = ""
            display_ascii(player.get_vis_frame())
        else:
            if not self.art_shown and track.cover_art:
                img = track.cover_art.get_image()
                if track.cover_art.bg_color:
                    self.colorstr = self.set_bg_color(track.cover_art.bg_color)
                if track.cover_art.fg_color:
                    self.colorstr += self.set_color(track.cover_art.fg_color)
                display_ascii(img, clear=True)
                self.art_shown = True

        if self.help_shown:
            self.display_help()

        sys.stdout.flush()
        return True

    def populate_help(self):
        help_entries = [
            ("?, h    ", ": Show this help screen"),
            ("Space   ", ": Toggle play/pause"),
            ("Left    ", ": Seek backwards 10 seconds"),
            ("Right   ", ": Seek forwards 10 seconds"),
            ("p, PgUp ", ": Previous track"),
            ("n, PgDn ", ": Next track"),
            ("m       ", ": Toggle mute/unmute"),
            ("v       ", ": Toggle visualization"),
            ("+, =    ", ": Volume up"),
            ("-, _    ", ": Volume down"),
            ("Esc     ", ": Close help screen"),
            ("q       ", ": Quit"),
        ]
        help_width = max([len(x[0]) + len(x[1]) for x in help_entries])

        def help_entry(txt):
            txt = self.term.ljust(txt, help_width)
            return "│ " + txt + " │"

        helptext = []

        helptext.append(self.term.normal + "┌" + "─" * (help_width + 2) + "┐")
        helptext.append(help_entry(""))
        helptext.append(
            help_entry(
                self.term.center(
                    self.term.bold(f"Tuatara {version}"),
                    help_width,
                )
            )
        )
        helptext.append(help_entry(""))
        for key, value in help_entries:
            helptext.append(help_entry(self.term.bold(key) + value))
        helptext.append(help_entry(""))
        helptext.append("└" + "─" * (help_width + 2) + "┘")
        return helptext

    def display_help(self):
        h = len(self.help_canvas)
        w = self.term.length(self.help_canvas[0])
        offset = (self.term.height - h) // 2
        output = ""
        for line in range(h):
            output += self.term.move_xy((self.term.width - w) // 2, offset + line)
            output += self.help_canvas[line]
        sys.stdout.write(output)

    def toggle_vis(self):
        self.vis_shown = not self.vis_shown
        self.clear_display = True

    def show_help(self):
        self.help_shown = True

    def hide_help(self):
        self.help_shown = False
        self.clear_display = True

    def process_keys(self, fd, condition, player):
        while True:
            key = self.term.inkey(timeout=0)
            if not key:
                break
            if key.is_sequence:
                match key.name:
                    case "KEY_ESCAPE":
                        self.hide_help()
                        self.display_info(player)
                    case "KEY_PGUP":
                        player.prev()
                    case "KEY_PGDOWN":
                        player.next()
                    case "KEY_LEFT":
                        player.seek_reverse()
                    case "KEY_RIGHT":
                        player.seek_forward()
            else:
                keychar = key.lower()
                match keychar:
                    case "q":
                        self.stop()
                        return False
                    case " ":
                        player.play_pause()
                    case "n":
                        player.next()
                    case "p":
                        player.prev()
                    case "m":
                        player.mute_or_unmute()
                    case "v":
                        if player.vis_available():
                            self.toggle_vis()
                        else:
                            debug(
                                "Visualization plugin not available or not configured!"
                            )
                    case "+" | "=":
                        player.raise_volume()
                    case "-" | "_":
                        player.lower_volume()
                    case "?" | "h":
                        self.show_help()
        return True

    def excepthook(self, ex_type, ex_value, tb):
        if settings.debug:
            traceback.print_exception(ex_type, ex_value, tb, file=settings._debugobj)
            settings._debugobj.flush()
        self.error = "Unexpected error, check debug logs for details."
        self.stop()

    def run(self, player):
        with self.term.cbreak(), self.term.hidden_cursor(), self.term.fullscreen():
            self.mainloop = GLib.MainLoop()
            GLib.unix_fd_add_full(
                GLib.PRIORITY_DEFAULT,
                sys.stdin.fileno(),
                GLib.IO_IN,
                self.process_keys,
                player,
            )
            GLib.timeout_add(20, self.display_info, player)
            self.mainloop.run()
        player.stop(self.error)

    def stop(self, signum=None, stack=None):
        self.mainloop.quit()
