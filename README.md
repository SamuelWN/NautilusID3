# NautilusID3
Python plugin for nautilus to enable the display of ID3 tags

This script can installed to the current user account by running the following commands:
    
    sudo apt-get install python-nautilus python-mutagen python-pyexiv2 mediainfo
    pip install pymediainfo
    mkdir -p ~/.local/share/nautilus-python/extensions/
    cp bsc-v2.py ~/.local/share/nautilus-python/extensions/
    chmod a+x ~/.local/share/nautilus-python/extensions/bsc-v2.py

You will need to restart nautilus for the changes to take effect:
    
    nautilus -q
