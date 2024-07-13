# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0+
#

import os
import signal
import sys
import traceback

from urllib3.util import parse_url

import blessed

from gi.repository import GLib

from tuatara.settings import settings, debug, version


class Interface:
    def __init__(self):
        self.term = blessed.Terminal()
        self.set_title(f"Tutatara {version}")
        self.current_art = None
        self.help_canvas = self.populate_help()
        self.help_shown = False
        self.vis_shown = False
        self.last_track = None
        self.mainloop = None
        self.need_resize = True
        self.error = None
        signal.signal(signal.SIGWINCH, self.sigwinch_handler)
        signal.signal(signal.SIGINT, self.stop)

    def set_title(self, title):
        sys.stdout.write("\x1b]0;" + title + "\x07")

    def sigwinch_handler(self, signum=None, stack=None):
        self.need_resize = True

    def set_size(self):
        self.width = self.term.width
        self.height = self.term.height
        if self.width > self.height * settings.art.get("font_ratio"):
            self.horizontal = True
            self.window_width = self.width - int(
                settings.art.get("font_ratio") * self.height
            )
            self.window_height = self.height
            if self.window_width < 36:
                self.window_width = 36
            self.width_offset = self.width - self.window_width
            self.height_offset = 0
        else:
            self.horizontal = False
            self.window_width = self.width
            self.window_height = self.height - int(
                self.width // settings.art.get("font_ratio")
            )
            if self.window_height < 7:
                self.window_height = 7
            self.height_offset = self.height - self.window_height
            self.width_offset = 0
        self.clear_display = True

    def display_info(self, player):
        def display_ascii(image):
            if self.horizontal:
                width = self.width - self.window_width - 2
                height = min(
                    int(width // settings.art.get("font_ratio")),
                    self.height - 2,
                )
                offsetx = 1
                offsety = (self.height - height) // 2
            else:
                height = self.height - self.window_height - 2
                width = int(height * settings.art.get("font_ratio"))
                offsety = 1
                offsetx = (self.width - width) // 2
            CHAR_RAMP = "   ...',;:clodxkO0KXNWM"

            output = ""
            img = image.resize((width, height))

            grayscale_img = img.convert("L")

            for h in range(height):
                output += self.term.move_xy(offsetx, h + offsety)
                for w in range(width):
                    brightness = grayscale_img.getpixel((w, h)) / 255
                    r, g, b = img.getpixel((w, h))[:3]
                    ascii_char = CHAR_RAMP[int(brightness * (len(CHAR_RAMP) - 1))]

                    output += self.term.on_color_rgb(r, g, b) + ascii_char
                output += self.term.normal

            sys.stdout.write(output)

        def fitted_text(text):
            if len(text) > (self.window_width - 2):
                trunc_text = text[: self.window_width - 3]
                return f"{trunc_text}…"
            else:
                return text

        def centered_position(text):
            return self.width_offset + (self.window_width - self.term.length(text)) // 2

        def display_str(text, offset):
            output = self.term.move_xy(
                self.width_offset, self.height_offset + self.window_height // 2 + offset
            )
            output += self.term.clear_eol
            output += self.term.move_xy(
                centered_position(text),
                self.height_offset + self.window_height // 2 + offset,
            )
            output += text
            sys.stdout.write(output)

        if self.need_resize:
            self.set_size()
            self.need_resize = False

        status = player.get_status()
        if status == "finished":
            self.stop()
            return False

        track = player.get_current_track()

        if track != self.last_track:
            self.clear_display = True
        self.last_track = track

        if not track:
            sys.stdout.write(self.term.clear)
            sys.stdout.flush()
            return True

        if status == "not_ready":
            return True

        if self.clear_display:
            self.current_art = False
            sys.stdout.write(self.term.clear)
            self.clear_display = False

        if track.title:
            titlestr = fitted_text(track.title)
            windowtitle = f"{track.artist} - {track.title}"
        else:
            parsed_url = parse_url(track.url)
            titlestr = os.path.basename(parsed_url.path)
            windowtitle = titlestr
        display_str(self.term.bold(fitted_text(titlestr)), -2)
        self.set_title(windowtitle)

        if track.artist:
            display_str(fitted_text(track.artist), -1)

        if track.album:
            display_str(fitted_text(track.album), 0)

        display_str(player.get_status_str(), 2)

        if not track.cover_art and track.fetch_status == "not_started":
            track.find_cover_art()
        if self.vis_shown:
            display_ascii(player.get_vis_frame())
        else:
            if not self.current_art and track.cover_art:
                display_ascii(track.cover_art.get_image())
                self.current_art = track.cover_art

        if self.help_shown:
            self.blit_help()

        sys.stdout.flush()
        return True

    def populate_help(self):
        hw = 37
        helpentries = [
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

        def helpline(txt, centered=False):
            length = self.term.length(txt)
            offset1 = (hw - length) // 2 if centered else 1
            offset2 = (hw - length - offset1) if centered else hw - length - 1
            return "│" + " " * offset1 + txt + " " * offset2 + "│"

        helptext = []

        helptext.append("┌" + "─" * hw + "┐")
        helptext.append(helpline(""))
        helptext.append(helpline(self.term.bold(f"Tuatara {version}"), centered=True))
        helptext.append(helpline(""))
        for key, value in helpentries:
            helptext.append(helpline(self.term.bold(key) + value))
        helptext.append(helpline(""))
        helptext.append("└" + "─" * hw + "┘")
        return helptext

    def blit_help(self):
        h = len(self.help_canvas)
        w = self.term.length(self.help_canvas[0])
        offset = (self.height - h) // 2
        output = ""
        for line in self.help_canvas:
            output += self.term.move_xy((self.width - w) // 2, offset) + line
            offset += 1
        sys.stdout.write(output)

    def toggle_vis(self):
        if not self.vis_shown and self.term.number_of_colors != 1 << 24:
            debug("Visualiazion not available when not on a truecolor terminal")
            return
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
                        if player.status == "playing":
                            player.pause()
                        else:
                            player.play()
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
                    case _:
                        pass
        return True

    def excepthook(self, ex_type, ex_value, tb):
        if settings.debug:
            traceback.print_exception(ex_type, ex_value, tb, None, settings._debugobj)
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
