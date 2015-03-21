#!/bin/bash

YUSTPLAYIT="/home/pi/yustplayit"

echo "Upgrading Yustplayit viewer..."

echo "Ensuring proper permission is set..."
sudo chown -R pi:pi $YUSTPLAYIT
sudo chown -R pi:pi /home/pi/yustplayit_assets
sudo chown -R pi:pi /home/pi/.yustplayit

echo "Removing feh (no longer needed)..."
sudo apt-get -y -qq remove feh

echo "Installing libx11-dev (if missing)..."
sudo apt-get -y -qq install libx11-dev

echo "Removing 'unclutter' and replacing it with a better hack."
sudo apt-get -y -qq remove unclutter
sudo killall unclutter
sudo sed -e 's/^#xserver-command=X$/xserver-command=X -nocursor/g' -i /etc/lightdm/lightdm.conf

echo "Fetching the latest update..."
cd $YUSTPLAYIT
git pull

echo "Ensuring all Python modules are installed..."
sudo pip install -r $YUSTPLAYIT/requirements.txt -q

echo "Restarting viewer module..."
pkill -f "viewer.py"

# Make sure we have proper framebuffer depth.
if grep -q framebuffer_depth /boot/config.txt; then
  sudo sed 's/^framebuffer_depth.*/framebuffer_depth=32/' -i /boot/config.txt
else
  echo 'framebuffer_depth=32' | sudo tee -a /boot/config.txt > /dev/null
fi

# Fix framebuffer bug
if grep -q framebuffer_ignore_alpha /boot/config.txt; then
  sudo sed 's/^framebuffer_ignore_alpha.*/framebuffer_ignore_alpha=1/' -i /boot/config.txt
else
  echo 'framebuffer_ignore_alpha=1' | sudo tee -a /boot/config.txt > /dev/null
fi

echo "Done! Please reboot."
