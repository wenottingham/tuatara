# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0+
#


from tuatara.cover_art import InlineCoverArt
from tuatara.image_utils import image_from_pixbuf
from tuatara.settings import settings, debug

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

GST_PLAY_FLAG_VIS = 1 << 3


class Player:
    def __init__(self):
        Gst.init()
        self.playlist = []
        self.player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("gdkpixbufsink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        plugin = settings.art.get("visualization")
        if plugin is not None:
            self.vis_plugin = Gst.ElementFactory.make(plugin, "vis")
        else:
            self.vis_plugin = None
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.status = "prep"
        self.vis_frame = None
        self.mainloop = None
        self.error = None
        self.interface = None
        self.current_track = None

    def set_playlist(self, playlist):
        self.playlist = playlist
        self.index = 0

    def set_interface(self, interface):
        self.interface = interface

    def cue_from_playlist(self):
        entry = self.playlist[self.index]
        self.current_track = entry
        debug(f"Playing {self.current_track}")
        self.player.set_property("uri", entry.url)
        self.play()

    def play(self):
        self.player.set_state(Gst.State.PLAYING)
        self.status = "playing"

    def pause(self):
        self.player.set_state(Gst.State.PAUSED)
        self.status = "paused"

    def seek_forward(self):
        (set, track_pos) = self.player.query_position(Gst.Format.TIME)
        new_pos = track_pos + 10 * Gst.SECOND
        self.player.seek(
            1.0,
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH,
            Gst.SeekType.SET,
            new_pos,
            Gst.SeekType.NONE,
            0,
        )

    def seek_reverse(self):
        (set, track_pos) = self.player.query_position(Gst.Format.TIME)
        new_pos = track_pos - 10 * Gst.SECOND
        if new_pos < 0:
            new_pos = 0
        self.player.seek(
            1.0,
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH,
            Gst.SeekType.SET,
            new_pos,
            Gst.SeekType.NONE,
            0,
        )

    def clear_current_track(self):
        self.current_track = None
        if self.interface:
            self.interface.clear()

    def get_current_track(self):
        return self.current_track

    def next(self):
        self.player.set_state(Gst.State.NULL)
        self.clear_current_track()
        self.index += 1
        if self.index >= len(self.playlist):
            self.stop()
            return
        self.cue_from_playlist()

    def prev(self):
        self.player.set_state(Gst.State.NULL)
        self.clear_current_track()
        self.index -= 1
        if self.index < 0:
            self.index = 0
        self.cue_from_playlist()

    def raise_volume(self):
        volume = self.player.get_property("volume")
        volume += 0.1
        if volume > 1.0:
            volume = 1.0
        self.player.set_property("volume", volume)
        self.player.set_property("mute", 0)

    def lower_volume(self):
        volume = self.player.get_property("volume")
        volume -= 0.1
        if volume < 0.0:
            volume = 0.0
        self.player.set_property("volume", volume)
        self.player.set_property("mute", 0)

    def mute_or_unmute(self):
        mute = self.player.get_property("mute")
        self.player.set_property("mute", not mute)

    def visualization_active(self):
        flags = self.player.get_property("flags")
        return flags & GST_PLAY_FLAG_VIS

    def toggle_visualization(self):
        flags = self.player.get_property("flags")
        if flags & GST_PLAY_FLAG_VIS:
            # Turn it off
            flags ^= GST_PLAY_FLAG_VIS
            self.player.set_property("flags", flags)
            self.player.set_property("vis-plugin", None)
            self.vis_frame = None
            self.interface.clear()
        else:
            # Turn it on
            if not self.vis_plugin:
                debug("Visualization plugin not available or not configured")
                return
            flags |= GST_PLAY_FLAG_VIS
            self.player.set_property("flags", flags)
            self.player.set_property("vis-plugin", self.vis_plugin)
            self.interface.clear()

    def get_status_str(self):
        (set, track_pos) = self.player.query_position(Gst.Format.TIME)
        (set, track_len) = self.player.query_duration(Gst.Format.TIME)

        if track_pos > 0:
            pos_sec = track_pos / Gst.SECOND
            pos_min = pos_sec / 60
            pos_str = "%01d:%02d:%02d" % (pos_min / 60, pos_min % 60, pos_sec % 60)
        else:
            pos_str = "-"

        if track_len > 0:
            len_sec = track_len / Gst.SECOND
            len_min = len_sec / 60
            len_str = "%01d:%02d:%02d" % (len_min / 60, len_min % 60, len_sec % 60)
        else:
            len_str = "-"

        if self.current_track.title or track_pos > (Gst.SECOND / 5):
            ready = True
        else:
            ready = False

        status_str = f"{pos_str} / {len_str}"

        if self.status == "paused":
            status_str = f"{status_str} [PAUSED]"

        if self.player.get_property("mute"):
            status_str = f"{status_str} [MUTED]"

        return (ready, status_str)

    def stop(self, error=None):
        self.player.set_state(Gst.State.NULL)
        self.error = error
        self.mainloop.quit()

    def parse_tags(self, taglist, tagtype):
        match tagtype:
            case Gst.TAG_TITLE:
                self.current_track.title = taglist.get_string(Gst.TAG_TITLE).value
            case Gst.TAG_ARTIST:
                self.current_track.artist = taglist.get_string(Gst.TAG_ARTIST).value
            case Gst.TAG_ALBUM:
                self.current_track.album = taglist.get_string(Gst.TAG_ALBUM).value
            case Gst.TAG_TRACK_NUMBER:
                self.current_track.track = Gst.tag_list_copy_value(
                    taglist, Gst.TAG_TRACK_NUMBER
                )[1]
            case Gst.TAG_TRACK_COUNT:
                self.current_track.track_total = Gst.tag_list_copy_value(
                    taglist, Gst.TAG_TRACK_COUNT
                )[1]
            case Gst.TAG_IMAGE:
                (dummy, sample) = taglist.get_sample(Gst.TAG_IMAGE)
                if sample:
                    buffer = sample.get_buffer()
                    (dummy, mapping) = buffer.map(Gst.MapFlags.READ)
                    if mapping:
                        if (
                            not self.current_track.cover_art
                            or self.current_track.cover_art.kind != "inline"
                        ):
                            debug(f"Using inline cover art for {self.current_track}")
                            self.current_track.cover_art = InlineCoverArt(mapping.data)
                        buffer.unmap(mapping)
            case _:
                pass

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.next()
        elif t == Gst.MessageType.TAG:
            taglist = message.parse_tag()
            taglist.foreach(self.parse_tags)
        elif t == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            self.stop(err)
        elif t == Gst.MessageType.ELEMENT:
            s = message.get_structure()
            if not s or not s.has_name("pixbuf"):
                return
            pixbuf = s.get_value("pixbuf")
            self.vis_frame = image_from_pixbuf(pixbuf)

    def set_mainloop(self, loop):
        self.mainloop = loop
