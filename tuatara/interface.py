# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0+
#

import os

from urllib3.util import parse_url

import caca
from caca.canvas import Canvas, NullCanvas
from caca.display import Display, Event
from caca.dither import Dither

from tuatara.settings import settings


class Interface:
    def __init__(self):
        self.canvas = Canvas(0, 0)
        self.display = Display(self.canvas, driver="ncurses")
        self.display.set_title("Tuatara")
        self.set_size()
        self.canvas.set_color_ansi(caca.COLOR_LIGHTGRAY, caca.COLOR_BLACK)
        self.current_art = None
        self.help_canvas = self.populate_help()
        self.help_shown = False

    def set_size(self):
        self.width = self.canvas.get_width()
        self.height = self.canvas.get_height()
        if self.width > self.height * settings.art.get("font_ratio"):
            self.horizontal = True
            self.window_width = self.width - int(
                settings.art.get("font_ratio") * self.height
            )
            self.window_height = self.height
            if self.window_width < 20:
                self.window_width = 20
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

    def clear(self):
        self.current_art = None
        self.canvas.clear()
        self.display.refresh()

    def display_cover_art(self, cover_art):
        if self.horizontal:
            width = self.width - self.window_width - 2
            height = int(width // settings.art.get("font_ratio")) - 2
            offsetx = 1
            offsety = (self.height - height) // 2
        else:
            height = self.height - self.window_height - 2
            width = int(height * settings.art.get("font_ratio")) - 2
            offsety = 1
            offsetx = (self.width - width) // 2

        art = cover_art.get_image()
        if not art:
            return

        ditherer = Dither(
            32,
            art.size[0],
            art.size[1],
            4 * art.size[0],
            0x00FF0000,
            0x0000FF00,
            0x000000FF,
            0xFF000000,
        )
        ditherer.set_algorithm(bytes(settings.art.get("dither"), "utf-8"))
        ditherer.set_charset(bytes(settings.art.get("charset"), "utf-8"))
        ditherer.bitmap(self.canvas, offsetx, offsety, width, height, art.tobytes())
        self.current_art = cover_art

    def display_visualization(self, vis_frame):
        if self.horizontal:
            width = self.width - self.window_width
            height = self.window_height
        else:
            width = self.width
            height = self.height - self.window_height

        if not vis_frame:
            return

        ditherer = Dither(
            32,
            vis_frame.size[0],
            vis_frame.size[1],
            4 * vis_frame.size[0],
            0x00FF0000,
            0x0000FF00,
            0x000000FF,
            0xFF000000,
        )
        ditherer.set_algorithm(bytes(settings.art.get("dither"), "utf-8"))
        ditherer.set_charset(bytes(settings.art.get("charset"), "utf-8"))

        ditherer.bitmap(self.canvas, 0, 0, width, height, vis_frame.tobytes())

    def display_info(self, player):
        def fitted_text(text):
            if len(text) > (self.window_width - 2):
                trunc_text = text[: self.window_width - 3]
                return f"{trunc_text}…"
            else:
                return text

        def centered_position(text):
            return self.width_offset + (self.window_width - len(text)) // 2

        def display_str(text, offset, attr=0x00):
            self.canvas.set_attr(attr)
            self.canvas.put_str(
                self.width_offset,
                self.height_offset + self.window_height // 2 + offset,
                " " * (self.width - self.width_offset),
            )
            self.canvas.put_str(
                centered_position(text),
                self.height_offset + self.window_height // 2 + offset,
                text,
            )

        track = player.get_current_track()
        if not track:
            return True

        (ready, status_str) = player.get_status_str()
        if not ready:
            return True

        if track.title:
            titlestr = fitted_text(track.title)
        else:
            parsed_url = parse_url(track.url)
            titlestr = os.path.basename(parsed_url.path)
        display_str(fitted_text(titlestr), -2, caca.STYLE_BOLD)
        self.display.set_title(f"Tuatara - {titlestr}")

        if track.artist:
            display_str(fitted_text(track.artist), -1)

        if track.album:
            display_str(fitted_text(track.album), 0)

        display_str(status_str, 2)

        if not track.cover_art and track.fetch_status == "not_started":
            track.find_cover_art()
        if player.visualization_active():
            self.display_visualization(player.vis_frame)
        else:
            if not self.current_art and track.cover_art:
                self.display_cover_art(track.cover_art)

        if self.help_shown:
            self.blit_help()

        self.display.refresh()
        return True

    def populate_help(self):
        hc = Canvas(39, 16)
        helptext = [
            "?, h    : Show this help screen",
            "Space   : Toggle play/pause",
            "Left    : Seek backwards 10 seconds",
            "Right   : Seek forwards 10 seconds",
            "p, PgUp : Previous track",
            "n, PgDn : Next track",
            "m       : Toggle mute/unmute",
            "v       : Toggle visulization",
            "+, =    : Volume up",
            "-, _    : Volume down",
            "Esc     : Close help screen",
            "q       : Quit",
        ]

        hc.draw_cp437_box(0, 0, hc.get_width(), hc.get_height())

        for line in helptext:
            hc.put_str(2, 2 + helptext.index(line), line)

        hc.set_handle(hc.get_width() // 2, hc.get_height() // 2)
        return hc

    def blit_help(self):
        self.canvas.blit(
            self.canvas.get_width() // 2,
            self.canvas.get_height() // 2,
            self.help_canvas,
            NullCanvas(),
        )

    def show_help(self):
        self.help_shown = True

    def hide_help(self):
        self.help_shown = False
        self.current_art = False
        self.canvas.clear()

    def process_keys(self, fd, condition, player):
        ev = Event()
        while self.display.get_event(caca.EVENT_ANY, ev, 100):
            if ev.get_type() != caca.EVENT_KEY_PRESS:
                continue
            key = ev.get_key_ch()
            if key > 0x80 or key < 0x1F:
                match key:
                    case caca.KEY_ESCAPE:
                        self.hide_help()
                        self.display_info(player)
                    case caca.KEY_PAGEUP:
                        player.prev()
                    case caca.KEY_PAGEDOWN:
                        player.next()
                    case caca.KEY_LEFT:
                        player.seek_reverse()
                    case caca.KEY_RIGHT:
                        player.seek_forward()
                    case _:
                        pass
            else:
                keychar = chr(key).lower()
                match keychar:
                    case "q":
                        player.stop()
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
                        player.toggle_visualization()
                    case "+" | "=":
                        player.raise_volume()
                    case "-" | "_":
                        player.lower_volume()
                    case "?" | "h":
                        self.show_help()
                    case _:
                        pass
        return True

    def exit(self):
        self.canvas.clear()
        self.display.refresh()
        del self.display
        del self.canvas
