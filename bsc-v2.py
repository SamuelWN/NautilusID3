#!/usr/bin/python

# this script can installed to the current user account by running the following commands:

# sudo apt-get install python-nautilus python-mutagen python-pyexiv2 mediainfo
# pip install pymediainfo
# mkdir ~/.local/share/nautilus-python/extensions/
# ln bsc-v2.py ~/.local/share/nautilus-python/extensions/
# chmod a+x ~/.local/share/nautilus-python/extensions/bsc-v2.py

# alternatively, you can place the script in:
# /usr/share/nautilus-python/extensions/

# change log:
# geb666: original bsc.py, based on work by Giacomo Bordiga
# jmdsdf: version 2 adds extra ID3 and EXIF tag support
# jmdsdf: added better error handling for ID3 tags, added mp3 length support, distinguished
#         between exif image size and true image size
# SabreWolfy: set consistent hh:mm:ss format, fixed bug with no ID3 information
#             throwing an unhandled exception
# jmdsdf: fixed closing file handles with mpinfo (thanks gueba)
# jmdsdf: fixed closing file handles when there's an exception (thanks Pitxyoki)
# jmdsdf: added video parsing (work based on enbeto, thanks!)
# jmdsdf: added FLAC audio parsing through kaa.metadata (thanks for the idea l-x-l)
# jmdsdf: added trackno, added mkv file support (thanks ENigma885)
# jmdsdf: added date/album for flac/video (thanks eldon.t)
# jmdsdf: added wav file support thru pyexiv2
# jmdsdf: added sample rate file support thru mutagen and kaa (thanks for the idea N'ko)
# jmdsdf: fix with tracknumber for FLAC, thanks l-x-l
# draxus: support for pdf files
# arun (engineerarun@gmail.com): made changes to work with naulitus 3.x
# Andrew@webupd8.org: get EXIF support to work with Nautilus 3
# samuelwn: changed video metadata extraction to use ffprobe instead of kaa.metadata
# samuelwn: changed video metadata extraction to use pymediainfo instead of ffprobe
# samuelwn: added column for video codec information


from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
import urllib
#import nautilus
from gi.repository import Nautilus, GObject, Gtk, GdkPixbuf
# gi.require_version('Nautilus', '3.0')
# for id3 support
from mutagen.easyid3 import EasyID3
# for exif support
from mutagen.mp3 import MPEGInfo
# for reading image dimensions
import pyexiv2
# for reading pdf
import Image
# for reading video
from pymediainfo import MediaInfo


try:
    from pyPdf import PdfFileReader
except:
    pass

class ColumnExtension(GObject.GObject, Nautilus.ColumnProvider, Nautilus.InfoProvider):
    def __init__(self):
        pass

    def get_columns(self):
        return (
            Nautilus.Column(name="NautilusPython::title_column",attribute="title",label="Title",description="Song title"),
            Nautilus.Column(name="NautilusPython::album_column",attribute="album",label="Album",description="Album"),
            Nautilus.Column(name="NautilusPython::artist_column",attribute="artist",label="Artist",description="Artist"),
            Nautilus.Column(name="NautilusPython::tracknumber_column",attribute="tracknumber",label="Track",description="Track number"),
            Nautilus.Column(name="NautilusPython::genre_column",attribute="genre",label="Genre",description="Genre"),
            Nautilus.Column(name="NautilusPython::date_column",attribute="date",label="Date",description="Date"),
            Nautilus.Column(name="NautilusPython::bitrate_column",attribute="bitrate",label="Bitrate",description="Audio Bitrate in kilo bits per second"),
            Nautilus.Column(name="NautilusPython::samplerate_column",attribute="samplerate",label="Sample rate",description="Sample rate in Hz"),
            Nautilus.Column(name="NautilusPython::length_column",attribute="length",label="Length",description="Length of audio"),
            Nautilus.Column(name="NautilusPython::exif_datetime_original_column",attribute="exif_datetime_original",label="EXIF Dateshot ",description="Get the photo capture date from EXIF data"),
            Nautilus.Column(name="NautilusPython::exif_software_column",attribute="exif_software",label="EXIF Software",description="EXIF - software used to save image"),
            Nautilus.Column(name="NautilusPython::exif_flash_column",attribute="exif_flash",label="EXIF flash",description="EXIF - flash mode"),
            Nautilus.Column(name="NautilusPython::exif_pixeldimensions_column",attribute="exif_pixeldimensions",label="EXIF Image Size",description="Image size - pixel dimensions as reported by EXIF data"),
            Nautilus.Column(name="NautilusPython::pixeldimensions_column",attribute="pixeldimensions",label="Image Size",description="Image/video size - actual pixel dimensions"),
            Nautilus.Column(name="NautilusPython::codec_column",attribute="codec",label="Video Codec",description="Video encoding codec"),
            Nautilus.Column(name="NautilusPython::comment_column",attribute="comment",label="Comments",description="Image/video comments"),
        )

    def update_file_info(self, file):
        # set defaults to blank
        file.add_string_attribute('title', '')
        file.add_string_attribute('album', '')
        file.add_string_attribute('artist', '')
        file.add_string_attribute('tracknumber', '')
        file.add_string_attribute('genre', '')
        file.add_string_attribute('date', '')
        file.add_string_attribute('bitrate', '')
        file.add_string_attribute('samplerate', '')
        file.add_string_attribute('length', '')
        file.add_string_attribute('exif_datetime_original', '')
        file.add_string_attribute('exif_software', '')
        file.add_string_attribute('exif_flash', '')
        file.add_string_attribute('exif_pixeldimensions', '')
        file.add_string_attribute('pixeldimensions', '')
        file.add_string_attribute('codec', '')
        file.add_string_attribute('comment', '')

        if file.get_uri_scheme() != 'file':
            return

        # strip file:// to get absolute path
        filename = urllib.unquote(file.get_uri()[7:])

        # mp3 handling
        if file.is_mime_type('audio/mpeg'):
            # attempt to read ID3 tag
            try:
                audio = EasyID3(filename)
                # sometimes the audio variable will not have one of these items defined, that's why
                # there is this long try / except attempt
                try: file.add_string_attribute('title', audio["title"][0])
                except: file.add_string_attribute('title', "[n/a]")
                try: file.add_string_attribute('album', audio["album"][0])
                except: file.add_string_attribute('album', "[n/a]")
                try: file.add_string_attribute('artist', audio["artist"][0])
                except: file.add_string_attribute('artist', "[n/a]")
                try: file.add_string_attribute('tracknumber', audio["tracknumber"][0])
                except: file.add_string_attribute('tracknumber', "[n/a]")
                try: file.add_string_attribute('genre', audio["genre"][0])
                except: file.add_string_attribute('genre', "[n/a]")
                try: file.add_string_attribute('date', audio["date"][0])
                except: file.add_string_attribute('date', "[n/a]")
            except:
                # [SabreWolfy] some files have no ID3 tag and will throw this exception:
                file.add_string_attribute('title', "[no ID3]")
                file.add_string_attribute('album', "[no ID3]")
                file.add_string_attribute('artist', "[no ID3]")
                file.add_string_attribute('tracknumber', "[no ID3]")
                file.add_string_attribute('genre', "[no ID3]")
                file.add_string_attribute('date', "[no ID3]")

            # try to read MP3 information (bitrate, length, samplerate)
            try:
                mpfile = open (filename)
                mpinfo = MPEGInfo (mpfile)
                file.add_string_attribute('bitrate', str(mpinfo.bitrate/1000) + " Kbps")
                file.add_string_attribute('samplerate', str(mpinfo.sample_rate) + " Hz")
                # [SabreWolfy] added consistent formatting of times in format hh:mm:ss
                # [SabreWolfy[ to allow for correct column sorting by length
                mp3length = "%02i:%02i:%02i" % ((int(mpinfo.length/3600)), (int(mpinfo.length/60%60)), (int(mpinfo.length%60)))
                mpfile.close()
                file.add_string_attribute('length', mp3length)
            except:
                file.add_string_attribute('bitrate', "[n/a]")
                file.add_string_attribute('length', "[n/a]")
                file.add_string_attribute('samplerate', "[n/a]")
                try:
                    mpfile.close()
                except: pass

        # image handling
        if file.is_mime_type('image/jpeg') or file.is_mime_type('image/png') or file.is_mime_type('image/gif') or file.is_mime_type('image/bmp'):
            # EXIF handling routines
            try:
                metadata = pyexiv2.ImageMetadata(filename)
                metadata.read()
                exif_datetimeoriginal = metadata['Exif.Photo.DateTimeOriginal']
                exif_imagesoftware = metadata['Exif.Image.Software']
                exif_photoflash = metadata['Exif.Photo.Flash']
                exif_pixelydimension = metadata['Exif.Photo.PixelYDimension']
                exif_pixelxdimension = metadata['Exif.Photo.PixelXDimension']
                file.add_string_attribute('exif_datetime_original',str(exif_datetimeoriginal.raw_value))
                file.add_string_attribute('exif_software',str(exif_imagesoftware.raw_value))
                file.add_string_attribute('exif_flash',str(exif_photoflash.raw_value))
                file.add_string_attribute('exif_pixeldimensions',str(exif_pixelydimension.raw_value)+'x'+str(exif_pixelxdimension.raw_value))
            except:
                # no exif data?
                file.add_string_attribute('exif_datetime_original',"")
                file.add_string_attribute('exif_software',"")
                file.add_string_attribute('exif_flash',"")
                file.add_string_attribute('exif_pixeldimensions',"")
            # try read image info directly
            try:
                im = Image.open(filename)
                file.add_string_attribute('pixeldimensions',str(im.size[0])+'x'+str(im.size[1]))
            except:
                file.add_string_attribute('pixeldimensions',"[image read error]")

        # video/flac handling
        if file.is_mime_type('video/x-msvideo') | file.is_mime_type('video/mpeg') | file.is_mime_type('video/x-ms-wmv') | file.is_mime_type('video/mp4') | file.is_mime_type('audio/x-flac') | file.is_mime_type('video/x-flv') | file.is_mime_type('video/x-matroska') | file.is_mime_type('audio/x-wav'):
            media_info = MediaInfo.parse(filename)

            try:
                for track in media_info.tracks:
                    if track.track_type == 'General':
                        try: file.add_string_attribute('artist', track.performer)
                        except: file.add_string_attribute('artist', '[n/a]')
                        try: file.add_string_attribute('title', track.movie_name)
                        except:
                            try: file.add_string_attribute('title', track.title)
                            except: file.add_string_attribute('title', '[n/a]')
                        try: file.add_string_attribute('album',track.album)
                        except: file.add_string_attribute('album', '[n/a]')
                        try: file.add_string_attribute('date',track.recorded_date)
                        except: file.add_string_attribute('date', '[n/a]')
                        try: file.add_string_attribute('tracknumber',str(track.track_name_position) + "/" + str(track.track_name_total))
                        except: file.add_string_attribute('tracknumber', '[n/a]')
                        try: file.add_string_attribute('comment', track.comment)
                        except: file.add_string_attribute('comment', '[n/a]')
                    elif track.track_type == 'Video':
                        try: file.add_string_attribute('length',"%02i:%02i:%02i" % ((int(track.duration/3600)), (int(track.duration/60%60)), (int(track.duration%60))))
                        except: file.add_string_attribute('length','[n/a]')
                        try: file.add_string_attribute('pixeldimensions', str(track.width) + 'x'+ str(track.height))
                        except: file.add_string_attribute('pixeldimensions','[n/a]')
                        try: file.add_string_attribute('bitrate',str(round(track.bit_rate/1000)))
                        except: file.add_string_attribute('bitrate','[n/a]')
                        try: file.add_string_attribute('samplerate',str(int(track.sampling_rate))+' Hz')
                        except: file.add_string_attribute('samplerate','[n/a]')
                        try: file.add_string_attribute('genre', track.genre)
                        except: file.add_string_attribute('genre', '[n/a]')
                        try: file.add_string_attribute('codec', track.format)
                        except: file.add_string_attribute('codec', '[n/a]')


            except:
                file.add_string_attribute('length','error')
                file.add_string_attribute('pixeldimensions','error')
                file.add_string_attribute('bitrate','error')
                file.add_string_attribute('samplerate','error')
                file.add_string_attribute('title','error')
                file.add_string_attribute('artist','error')
                file.add_string_attribute('genre','error')
                file.add_string_attribute('track','error')
                file.add_string_attribute('date','error')
                file.add_string_attribute('album','error')
                file.add_string_attribute('codec','error')
                file.add_string_attribute('comment','error')

        # pdf handling
        if file.is_mime_type('application/pdf'):
            try:
                f = open(filename, "rb")
                pdf = PdfFileReader(f)
                try: file.add_string_attribute('title', pdf.getDocumentInfo().title)
                except: file.add_string_attribute('title', "[n/a]")
                try: file.add_string_attribute('artist', pdf.getDocumentInfo().author)
                except: file.add_string_attribute('artist', "[n/a]")
                f.close()
            except:
                file.add_string_attribute('title', "[no info]")
                file.add_string_attribute('artist', "[no info]")

        self.get_columns()
