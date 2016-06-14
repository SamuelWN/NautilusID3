#!/usr/bin/python

# this script can installed to the current user account by running the following commands:

# sudo apt-get install python-nautilus python-mutagen python-pyexiv2 python-kaa-metadata ffmpeg
# mkdir ~/.local/share/nautilus-python/extensions/
# cp bsc-v2.py ~/.local/share/nautilus-python/extensions/
# chmod a+x ~/.local/share/nautilus-python/extensions/bsc-v2.py

# alternatively, you can be able to place the script in:
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

import os
import urllib
#import nautilus
from gi.repository import Nautilus, GObject, Gtk, GdkPixbuf
# for id3 support
from mutagen.easyid3 import EasyID3
# for exif support
from mutagen.mp3 import MPEGInfo
# for reading image dimensions
import pyexiv2
# for reading pdf
import Image
# Used to trigger ffprobe for reading videos
import subprocess as sp
import string
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
            # info, error =sp.call(['ffprobe', '-show_format', '-show_streams', '-pretty', '-loglevel', 'quiet', filename])

            command=['ffprobe', '-show_format', '-show_streams', '-pretty', '-loglevel', 'quiet', filename]

            p = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
            out, err = p.communicate()

            info = out.split('\n')
            try:
                # info=kaa.metadata.parse(filename)
                # command = ['ffprobe', '-show_format', '-show_streams', '-pretty', '-loglevel', 'quiet', filename]
                # info=sp.Popen(command, stdout=sp.PIPE).communicate()[0].split('\n')

                width = '[n/a]'
                height = '[n/a]'

                # for line in info:
                    # if line.startswith('duration='):
                    #     try: file.add_string_attribute('length', str(line[10:]))
                    #     except: file.add_string_attribute('length','[n/a]')
                    # elif line.startswith('width='):
                    #     width = line[6:]
                    # elif line.startswith('height='):
                    #     height = line[7:]
                    # elif line.startswith('bit_rate='):
                    #     try: file.add_string_attribute('bitrate', str(line[9:]))
                    #     except: file.add_string_attribute('bitrate','[n/a]')
                    # elif line.startswith('sample_rate='):
                    #     try: file.add_string_attribute('samplerate', str(line[12:]))
                    #     except: file.add_string_attribute('samplerate','[n/a]')
                    # elif line.startswith('TAG:title='):
                    #     try: file.add_string_attribute('title', str(line[10:]))
                    #     except: file.add_string_attribute('title','[n/a]')
                    # elif line.startswith('TAG:artist='):
                    #     try: file.add_string_attribute('artist', str(line[11:]))
                    #     except: file.add_string_attribute('artist','[n/a]')
                    # elif line.startswith('TAG:genre='):
                    #     try: file.add_string_attribute('genre', str(line[10:]))
                    #     except: file.add_string_attribute('genre','[n/a]')
                    # elif line.startswith('TAG:track='):
                    #     try: file.add_string_attribute('tracknumber', str(line[10:]))
                    #     except: file.add_string_attribute('tracknumber','[n/a]')
                    # elif line.startswith('TAG:date='):
                    #     try: file.add_string_attribute('date', str(line[9:]))
                    #     except: file.add_string_attribute('date','[n/a]')
                    # elif line.startswith('TAG:album='):
                    #     try: file.add_string_attribute('album', str(line[10:]))
                    #     except: file.add_string_attribute('album','[n/a]')
                for line in info:
                    if line.startswith('duration='):
                        file.add_string_attribute('length', str(line[9:]))
                    elif line.startswith('width='):
                        width = line[6:]
                    elif line.startswith('height='):
                        height = line[7:]
                    elif line.startswith('bit_rate='):
                        file.add_string_attribute('bitrate', str(line[9:]))
                    elif line.startswith('sample_rate='):
                        file.add_string_attribute('samplerate', str(line[12:]))
                    elif line.startswith('TAG:title='):
                        file.add_string_attribute('title', str(line[10:]))
                    elif line.startswith('TAG:artist='):
                        file.add_string_attribute('artist', str(line[11:]))
                    elif line.startswith('TAG:genre='):
                        file.add_string_attribute('genre', str(line[10:]))
                    elif line.startswith('TAG:track='):
                        file.add_string_attribute('tracknumber', str(line[10:]))
                    elif line.startswith('TAG:date='):
                        file.add_string_attribute('date', str(line[9:]))
                    elif line.startswith('TAG:album='):
                        file.add_string_attribute('album', str(line[10:]))
                if height != '[n/a]' and width != '[n/a]':
                    print "pixeldimensions = " + width + 'x'+ height

                if height != '[n/a]' and width != '[n/a]':
                    file.add_string_attribute('pixeldimensions', str(width) + 'x'+ str(height))

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
