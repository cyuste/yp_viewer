#!/usr/bin/env python
# -*- coding: utf8 -*-

from os import path, getenv
from sys import exit
import ConfigParser
import logging
import urllib2
import urllib
import sh
from UserDict import IterableUserDict

CONFIG_DIR = '.yustplayit/'
CONFIG_FILE = 'viewer.conf'
GETCONFIG_URL = 'http://clients.yustplayit.com/getConfig'
DEFAULTS = {
    'main': {
        'assetdir': 'yustplayit_assets',
        'user': 'demo',
        'deviceId': '1',
    },
    'viewer': {
        'show_splash': True,
        'audio_output': 'hdmi',
        'shuffle_playlist': False,
        'resolution': '1920x1080',
        'default_duration': '10',
        'debug_logging': False,
        'verify_ssl': True,
        'use_24_hour_clock': False
    }
}

# Initiate logging
logging.basicConfig(level=logging.DEBUG,
                    filename='/tmp/yustplayit_viewer.log',
                    format='%(asctime)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

# Silence urllib info messages ('Starting new HTTP connection')
# that are triggered by the remote url availability check in view_web
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.DEBUG)

logging.debug('Starting viewer.py')


class ScreenlySettings(IterableUserDict):
    "Screenly OSE's Settings."

    def __init__(self, *args, **kwargs):
        rv = IterableUserDict.__init__(self, *args, **kwargs)
        self.home = getenv('HOME')
        self.conf_file = self.get_configfile()

        if not path.isfile(self.conf_file):
            logging.debug('Config-file %s missing. Trying to download', self.conf_file)
            
            rsaPub = open(self.home+'/.ssh/id_rsa.pub','r')
            publicId = rsaPub.readline(512)
            rsaPub.close()
            values = {'publicId' : publicId}
            data = urllib.urlencode(values)
            req = urllib2.Request(GETCONFIG_URL, data)
            response = urllib2.urlopen(req)
            html = response.read()
            pos = html.find('\r\n\r\n')
            config = html[pos+4:]
            
            confFile = open(self.conf_file,'w')
            confFile.write(config)
            confFile.close()
            
            self.load()
        else:
            self.load()
        return rv

    def _get(self, config, section, field, default):
        try:
            if isinstance(default, bool):
                self[field] = config.getboolean(section, field)
            elif isinstance(default, int):
                self[field] = config.getint(section, field)
            else:
                self[field] = config.get(section, field)
        except ConfigParser.Error as e:
            logging.debug("Could not parse setting '%s.%s': %s. Using default value: '%s'." % (section, field, unicode(e), default))
            self[field] = default
        if field in ['database', 'assetdir']:
            self[field] = str(path.join(self.home, self[field]))

    def _set(self, config, section, field, default):
        if isinstance(default, bool):
            config.set(section, field, self.get(field, default) and 'on' or 'off')
        else:
            config.set(section, field, unicode(self.get(field, default)))

    def load(self):
        "Loads the latest settings from screenly.conf into memory."
        logging.debug('Reading config-file...')
        config = ConfigParser.ConfigParser()
        config.read(self.conf_file)

        for section, defaults in DEFAULTS.items():
            for field, default in defaults.items():
                self._get(config, section, field, default)
                
    def save(self):
        # Write new settings to disk.
        config = ConfigParser.ConfigParser()
        for section, defaults in DEFAULTS.items():
            config.add_section(section)
            for field, default in defaults.items():
                self._set(config, section, field, default)
        with open(self.conf_file, "w") as f:
            config.write(f)
        self.load()

    def get_configdir(self):
        return path.join(self.home, CONFIG_DIR)

    def get_configfile(self):
        return path.join(self.home, CONFIG_DIR, CONFIG_FILE)


settings = ScreenlySettings()
