# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © 2023 Bill Nottingham <notting@splat.cc>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from urllib3.util import parse_url

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
        self.playbin = Gst.ElementFactory.make("playbin", "player")
        self.pixbuf_sink = Gst.ElementFactory.make("gdkpixbufsink", "pixbuf_sink")
        self.pixbuf_sink.set_property("post-messages", False)
        self.playbin.set_property("video-sink", self.pixbuf_sink)
        self.vis_plugin = Gst.ElementFactory.make(
            settings.art.get("visualization", "vis")
        )
        if self.vis_plugin:
            flags = self.playbin.get_property("flags")
            flags |= GST_PLAY_FLAG_VIS
            self.playbin.set_property("flags", flags)
            self.playbin.set_property("vis-plugin", self.vis_plugin)
        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.error = None
        self.current_track = None

    def set_playlist(self, playlist):
        self.playlist = playlist
        self.index = 0

    def cue_from_playlist(self):
        entry = self.playlist[self.index]
        self.current_track = entry
        debug(f"Playing {self.current_track}")
        p = parse_url(entry.url)
        if p.scheme:
            self.playbin.set_property("uri", entry.url)
        else:
            self.playbin.set_property("uri", Gst.filename_to_uri(entry.url))
        self.play()

    def play(self):
        self.playbin.set_state(Gst.State.PLAYING)

    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)

    def play_pause(self):
        if self.playbin.current_state == Gst.State.PAUSED:
            self.play()
        else:
            self.pause()

    def seek_forward(self):
        (set, track_pos) = self.playbin.query_position(Gst.Format.TIME)
        new_pos = track_pos + 10 * Gst.SECOND
        flags = self.playbin.get_property("flags")
        flags ^= GST_PLAY_FLAG_VIS
        self.playbin.set_property("flags", flags)
        self.playbin.seek(
            1.0,
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH,
            Gst.SeekType.SET,
            new_pos,
            Gst.SeekType.NONE,
            0,
        )
        self.playbin.get_state(Gst.CLOCK_TIME_NONE)
        flags = self.playbin.get_property("flags")
        flags |= GST_PLAY_FLAG_VIS
        self.playbin.set_property("flags", flags)

    def seek_reverse(self):
        (set, track_pos) = self.playbin.query_position(Gst.Format.TIME)
        new_pos = track_pos - 10 * Gst.SECOND
        if new_pos < 0:
            new_pos = 0
        flags = self.playbin.get_property("flags")
        flags ^= GST_PLAY_FLAG_VIS
        self.playbin.set_property("flags", flags)
        self.playbin.seek(
            1.0,
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH,
            Gst.SeekType.SET,
            new_pos,
            Gst.SeekType.NONE,
            0,
        )
        self.playbin.get_state(Gst.CLOCK_TIME_NONE)
        flags = self.playbin.get_property("flags")
        flags |= GST_PLAY_FLAG_VIS
        self.playbin.set_property("flags", flags)

    def get_current_track(self):
        return self.current_track

    def next(self):
        self.playbin.set_state(Gst.State.NULL)
        self.index += 1
        if self.index >= len(self.playlist):
            self.stop()
            return
        self.cue_from_playlist()

    def prev(self):
        self.playbin.set_state(Gst.State.NULL)
        self.index -= 1
        if self.index < 0:
            self.index = 0
        self.cue_from_playlist()

    def raise_volume(self):
        volume = self.playbin.get_property("volume")
        volume += 0.1
        if volume > 1.0:
            volume = 1.0
        self.playbin.set_property("volume", volume)
        self.playbin.set_property("mute", 0)

    def lower_volume(self):
        volume = self.playbin.get_property("volume")
        volume -= 0.1
        if volume < 0.0:
            volume = 0.0
        self.playbin.set_property("volume", volume)
        self.playbin.set_property("mute", 0)

    def mute_or_unmute(self):
        mute = self.playbin.get_property("mute")
        self.playbin.set_property("mute", not mute)

    def vis_available(self):
        return bool(self.vis_plugin)

    def get_vis_frame(self):
        return image_from_pixbuf(self.pixbuf_sink.get_property("last-pixbuf"))

    def get_status(self):
        if not self.current_track:
            return "finished"
        (set, track_pos) = self.playbin.query_position(Gst.Format.TIME)
        if self.current_track.title or track_pos > (Gst.SECOND / 5):
            return "ready"
        else:
            return "not ready"

    def get_status_str(self):
        (set, track_pos) = self.playbin.query_position(Gst.Format.TIME)
        (set, track_len) = self.playbin.query_duration(Gst.Format.TIME)

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

        status_str = f"{pos_str} / {len_str}"

        if self.playbin.current_state == Gst.State.PAUSED:
            status_str = f"{status_str} [PAUSED]"

        if self.playbin.get_property("mute"):
            status_str = f"{status_str} [MUTED]"

        return status_str

    def stop(self, error=None):
        self.playbin.set_state(Gst.State.NULL)
        self.current_track = None
        if error:
            self.error = error

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

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.next()
        elif t == Gst.MessageType.TAG:
            taglist = message.parse_tag()
            taglist.foreach(self.parse_tags)
        elif t == Gst.MessageType.ERROR:
            self.playbin.set_state(Gst.State.NULL)
            err, _ = message.parse_error()
            self.stop(err)
