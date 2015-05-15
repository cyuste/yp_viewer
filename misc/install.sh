#!/bin/bash -x

echo "Installing Yustplayit"

## Simple disk storage check. Naively assumes root partition holds all system data.
ROOT_AVAIL=$(df -k / | tail -n 1 | awk {'print $4'})
MIN_REQ="512000"

if [ $ROOT_AVAIL -lt $MIN_REQ ]; then
	echo "Insufficient disk space. Make sure you have at least 500MB available on the root partition."
	exit 1
fi

## Hackish solution to support both the new and old file structure.
## TL;DR: the 'new style' system adds '-pi' to various files and folders.
## See https://github.com/wireload/screenly-ose/pull/266
if [ -f "$HOME/.config/openbox/lxde-pi-rc.xml" ]; then
    SUFFIX="-pi"
else
    SUFFIX=""
fi

echo "Updating system package database..."
sudo apt-get -qq update > /dev/null

echo "Upgrading the system..."
echo "(This might take a while.)"
sudo apt-get -y -qq upgrade > /dev/null

echo "Installing dependencies..."
sudo apt-get -y -qq install \
    git-core python-pip python-netifaces python-simplejson python-imaging \
    python-dev uzbl omxplayer x11-xserver-utils libx11-dev \
    watchdog chkconfig > /dev/null

echo "Downloading..."
git clone -q https://github.com/cyuste/yp_viewer.git "$HOME/yustplayit" > /dev/null

echo "Installing more dependencies..."
sudo pip install -r "$HOME/yustplayit/requirements.txt" -q > /dev/null

echo "Adding Viewer to X auto start..."
mkdir -p "$HOME/.config/lxsession/LXDE$SUFFIX/"
echo "@$HOME/yustplayit/misc/xloader.sh" > "$HOME/.config/lxsession/LXDE$SUFFIX/autostart"
chmod u+x "@$HOME/yustplayit/misc/xloader.sh"

echo "Increasing swap space to 500MB..."
echo "CONF_SWAPSIZE=500" > "$HOME/dphys-swapfile"
sudo cp /etc/dphys-swapfile /etc/dphys-swapfile.bak
sudo mv "$HOME/dphys-swapfile" /etc/dphys-swapfile

echo "Adding config-file"
mkdir -p "$HOME/.yustplayit"
cp "$HOME/yustplayit/misc/viewer_template.conf" "$HOME/.yustplayit/viewer.conf"

echo "Copying sync script"
cp "$HOME/yustplayit/misc/sync_assets.sh" "$HOME/sync_assets.sh"
chmod u+x "@$HOME/sync_assets.sh"

echo "Creating assets folder"
mkdir "$HOME/yustplayit_assets"

echo "Creating public key"
ssh-keygen -t rsa -N '' -f "$HOME/.ssh/id_rsa"

echo "Disabling overscan"
sudo sed -i '/#disable_overscan=1/c\disable_overscan=1' /boot/config.txt

echo "Enabling Watchdog..."
sudo modprobe bcm2708_wdog > /dev/null # This fails, attempts to access a non-existing file. Reboot helps
sudo cp /etc/modules /etc/modules.bak
sudo sed '$ i\bcm2708_wdog' -i /etc/modules
sudo chkconfig watchdog on
sudo cp /etc/watchdog.conf /etc/watchdog.conf.bak
sudo sed -e 's/#watchdog-device/watchdog-device/g' -i /etc/watchdog.conf
sudo /etc/init.d/watchdog start


echo "Making modifications to X..."
[ -f "$HOME/.gtkrc-2.0" ] && rm -f "$HOME/.gtkrc-2.0"
ln -s "$HOME/yustplayit/misc/gtkrc-2.0" "$HOME/.gtkrc-2.0"
[ -f "$HOME/.config/openbox/lxde$SUFFIX-rc.xml" ] && \
    mv "$HOME/.config/openbox/lxde$SUFFIX-rc.xml" "$HOME/.config/openbox/lxde$SUFFIX-rc.xml.bak"
[ -d "$HOME/.config/openbox" ] || mkdir -p "$HOME/.config/openbox"
ln -s "$HOME/yustplayit/misc/lxde-rc.xml" "$HOME/.config/openbox/lxde$SUFFIX-rc.xml"
[ -f "$HOME/.config/lxpanel/LXDE$SUFFIX/panels/panel" ] && \
    mv "$HOME/.config/lxpanel/LXDE$SUFFIX/panels/panel" "$HOME/.config/lxpanel/LXDE$SUFFIX/panels/panel.bak"

# Cover both situations, as there have been traces of both in recent versions.
[ -f "/etc/xdg/lxsession/LXDE/autostart" ] && \
    sudo mv "/etc/xdg/lxsession/LXDE/autostart" "/etc/xdg/lxsession/LXDE/autostart.bak"
[ -f "/etc/xdg/lxsession/LXDE$SUFFIX/autostart" ] && \
    sudo mv "/etc/xdg/lxsession/LXDE$SUFFIX/autostart" "/etc/xdg/lxsession/LXDE$SUFFIX/autostart.bak"

sudo sed -e 's/^#xserver-command=X$/xserver-command=X -nocursor/g' -i /etc/lightdm/lightdm.conf

# Make sure we have proper framebuffer depth.
if grep -q framebuffer_depth /boot/config.txt; then
  sudo sed 's/^framebuffer_depth.*/framebuffer_depth=32/' -i /boot/config.txt
else
  echo 'framebuffer_depth=32' | sudo tee -a /boot/config.txt > /dev/null
fi

# Fix frame buffer bug
if grep -q framebuffer_ignore_alpha /boot/config.txt; then
  sudo sed 's/^framebuffer_ignore_alpha.*/framebuffer_ignore_alpha=1/' -i /boot/config.txt
else
  echo 'framebuffer_ignore_alpha=1' | sudo tee -a /boot/config.txt > /dev/null
fi

echo "Quiet the boot process..."
sudo cp /boot/cmdline.txt /boot/cmdline.txt.bak
sudo sed 's/$/ quiet/' -i /boot/cmdline.txt

echo "Assuming no errors were encountered, go ahead and restart your computer."
