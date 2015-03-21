Viewer code, based on Screenly OSE solution.

INSTALLATION NOTES:

First, flash the SD card and install Raspbian Wheezy. Instructions are available here.

During the first boot, you should be presented with a configuration screen (raspi-config). In raspi-config, make sure you make the following changes:

Expand the root file system (required)
Disable overscan (depends on your display)
Change keyboard mapping (optional)
Change time zone (optional, but Screenly’s scheduling uses this)
Enable SSH (optional)
Configure boot behavior to boot into X (required)
Change password for 'pi’ user (recommended)
Change memory split to 50%/50% (ie. 128/128 or 256/256 depending on your Raspberry Pi version (recommended)
Once you’ve made all these changes, you must restart your Raspberry Pi


Install Yustplayit viewer

logged as the user 'pi’ run:

$ curl -sL https://raw.github.com/cyuste/yp_viewer/master/misc/install.sh | bash
(If you’re running the installation over SSH, running the installation through a 'screen’ session is highly recommended.)

Assuming everything went well, reboot your system. The viewer should now load. Be patient, at first it has to download the contents, so it can take a long time to start showing the images/videos.

