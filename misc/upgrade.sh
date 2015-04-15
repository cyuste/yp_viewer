#!/bin/bash

YUSTPLAYIT="/home/pi/yustplayit"

echo "Upgrading Yustplayit viewer..."

echo "Ensuring proper permission is set..."
sudo chown -R pi:pi $YUSTPLAYIT
sudo chown -R pi:pi /home/pi/yustplayit_assets
sudo chown -R pi:pi /home/pi/.yustplayit


echo "Installing libx11-dev (if missing)..."
sudo apt-get -y -qq install libx11-dev


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

# Restart
sudo pkill shutdown
sudo shutdown -r now
