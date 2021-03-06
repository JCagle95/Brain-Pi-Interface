#!/bin/bash

# Install Essential Packages
sudo apt-get update
sudo apt-get upgrade

sudo apt-get install build-essential libfreeimage-dev libopenal-dev libpango1.0-dev libsndfile-dev libudev-dev libasound2-dev libjpeg8-dev libtiff5-dev libwebp-dev automake

# Install SDL Packages: SDL2 and SDL2-image
mkdir SDL && cd SDL
wget https://www.libsdl.org/release/SDL2-2.0.3.tar.gz
tar zxvf SDL2-2.0.3.tar.gz
cd SDL2-2.0.3 && mkdir build && cd build

../configure --host=armv7l-raspberry-linux-gnueabihf --disable-pulseaudio --disable-esd --disable-video-mir --disable-video-wayland --disable-video-x11 --disable-video-opengl
make -j 4
sudo make install
cd ../..

wget http://www.libsdl.org/projects/SDL_image/release/SDL2_image-2.0.0.tar.gz
tar zxvf SDL2_image-2.0.0.tar.gz
cd SDL2_image-2.0.0 && mkdir build && cd build
../configure
make -j 4
sudo make install
cd ../..

# Copying Essential Files for OpenBCI

sudo cp ../RPi/openbci-usb-serial.rules /etc/udev/rules.d/openbci-usb-serial.rules
sudo cp ../RPi/cmdline.direct /etc/cmdline.direct
sudo cp ../RPi/cmdline.normal /etc/cmdline.normal
sudo cp ../RPi/cmdline.txt /boot/cmdline.txt

# Install Python Essential Packages

sudo apt-get install python-scipy python-numpy python-serial

# Share Folder:

sudo apt-get install sshfs openssh-server
sudo gpasswd -a pi fuse
sudo mkdir /home/pi/Brain-Pi-Interface