# Source
```sh
git clone https://github.com/snes9xgit/snes9x.git
cd snes9x
git checkout gcemanager
```

# Libraries
```sh
sudo apt-get install build-essential intltool autoconf automake libglib2.0-dev gawk libgtk-3-dev libxml2-dev libxv-dev libsdl1.2-dev libpulse-dev portaudio19-dev
```

# Compile
```sh
cd gtk
./autogen.sh
./configure --with-gtk3
make
```

# Install
```
sudo make install
```
