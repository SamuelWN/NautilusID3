# NautilusID3
Python plugin for nautilus to enable the display of ID3 tags

This script can installed to the current user account by running the following commands:

    sudo apt-get install python-nautilus python-mutagen python-pyexiv2 ffmpeg
    mkdir -p ~/.local/share/nautilus-python/extensions/
    cp bsc-v2.py ~/.local/share/nautilus-python/extensions/
    chmod a+x ~/.local/share/nautilus-python/extensions/bsc-v2.py

#####To Do:
- Switch from  use of `ffprobe` to `MediaInfo`
    - Current implementation is unreasonably computationally intensive
- Determine whether to continue with subprocess implementation or utilization of [pymediainfo](https://github.com/sbraz/pymediainfo/ "A Python wrapper around the MediaInfo CLI")
    - `pip install pymediainfo`
