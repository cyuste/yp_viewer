#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = "Viktor Petersson & Carlos Yuste"
__copyright__ = "Copyright 2012-2014, WireLoad Inc"
__license__ = "Dual License: GPLv2 and Commercial License"

from datetime import datetime, timedelta
from os import path, getenv, utime, walk
from platform import machine
from random import shuffle
from requests import get as req_get
from requests import head as req_head
from time import sleep, time
from json import load as json_load
from json import loads as json_loads
from signal import signal, SIGUSR1, SIGUSR2
from chromote import Chromote
import logging
import subprocess
import sh
import urllib2 as urllib
import math
#import urllib.request as urllib #Python3

from settings import settings
import html_templates
from utils import url_fails


SPLASH_DELAY = 60  # secs
EMPTY_PL_DELAY = 5  # secs

BLACK_PAGE = '/yustplayit/black_page.html' # relative to $HOME
WATCHDOG_PATH = '/tmp/yustplayit.watchdog'
SCREENLY_HTML = '/tmp/yustplayit_html/'
LOAD_SCREEN = '/yustplayit/loading.gif'  # relative to $HOME
UZBLRC = '/yustplayit/misc/uzbl.rc'  # relative to $HOME
INTRO = '/yustplayit/intro-template.html'
PLAYLIST_URL = 'http://clients.yustplayit.com/getContentList/'
USERID_URL = 'http://clients.yustplayit.com/getUser/' # ID is in config file


current_browser_url = None
chromebin = None
chrome = None
chrometab = None

VIDEO_TIMEOUT = 20  # secs


def sigusr1(signum, frame):
    """
    The signal interrupts sleep() calls, so the currently playing web or image asset is skipped.
    omxplayer is killed to skip any currently playing video assets.
    """
    logging.info('USR1 received, skipping.')
    sh.killall('omxplayer.bin', _ok_code=[1])


def sigusr2(signum, frame):
    """Reload settings"""
    logging.info("USR2 received, reloading settings.")
    load_settings()


class Scheduler(object):
    def __init__(self, *args, **kwargs):
        logging.debug('Scheduler init')
        self.update_playlist()

    def get_next_asset(self):
        logging.debug('get_next_asset')
        self.refresh_playlist()
        logging.debug('get_next_asset after refresh')
        if self.nassets == 0:
            return None
        idx = self.index
        self.index = (self.index + 1) % self.nassets
        logging.debug('get_next_asset counter %s returning asset %s of %s', self.counter, idx + 1, self.nassets)
        if settings['shuffle_playlist'] and self.index == 0:
            self.counter += 1
        return self.assets[idx]

    def refresh_playlist(self):
        logging.debug('refresh_playlist')
        time_cur = datetime.utcnow()
        logging.debug('refresh: counter: (%s) timecur (%s)', self.counter, time_cur)
        if self.index == 0:
            logging.debug('updating playlist ')
            self.update_playlist()

    def update_playlist(self):
        logging.debug('update_playlist')
        self.generate_asset_list()
        self.nassets = len(self.assets)
        self.counter = 0
        self.index = 0
        logging.debug('update_playlist done, count %s, counter %s, index %s', self.nassets, self.counter, self.index)

    def generate_asset_list(self):
        logging.info('Generating asset-list...')

        dev_id = settings['deviceId']
        try:
            response = urllib.urlopen(PLAYLIST_URL+str(dev_id))
        except:
            logging.info("No internet connection. Keeping old list")
            return 
        json = response.read()
        playlist = json_loads(json)   

        if settings['shuffle_playlist']:
            shuffle(playlist)
        
        logging.debug("Replacing asset-list")
        self.assets = playlist

def dummy_true(asset):
    """
    To be replaced with a function that actually does something,
    for example check validity
    """
    return True

def watchdog():
    """Notify the watchdog file to be used with the watchdog-device."""
    if not path.isfile(WATCHDOG_PATH):
        open(WATCHDOG_PATH, 'w').close()
    else:
        utime(WATCHDOG_PATH, None)

def load_browser(url=None):
    global chromebin, chrome, chrometab, current_browser_url
    logging.info('Loading browser...')

    if not url is None:
        current_browser_url = url

    # --config=-       read commands (and config) from stdin
    # --print-events   print events to stdout
    bashCommand = "google-chrome --password-store=basic --kiosk --remote-debugging-port=9222"
    chromebin = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    logging.info('Browser loading %s. Running as PID %s.', current_browser_url, chromebin.pid)
   
    i=1 
    while i < 7:
        try:
            chrome = Chromote()
            break
        except:
            sleep(5)
            i += 1
    chrometab = chrome.tabs[0]
    chrometab.set_url(current_browser_url)


def browser_url(url):
    global current_browser_url

    if url == current_browser_url and not force:
        logging.debug('Already showing %s, keeping it.', current_browser_url)
    else:
        current_browser_url = url
        chrometab.set_url(url)
        logging.info('current url is %s', current_browser_url)


def view_image(uri):
    browser_url('file://' + uri)

def view_video(uri, duration):
    filename = uri + '.mp4'
    browser_url('file://' + filename)
   


def check_update():
    """
    Check if there is a later version of viewer
    available. Only do this update once per day.

    Return True if up to date was written to disk,
    False if no update needed and None if unable to check.
    """

    sha_file = path.join(settings.get_configdir(), 'latest_screenly_sha')

    if path.isfile(sha_file):
        sha_file_mtime = path.getmtime(sha_file)
        last_update = datetime.fromtimestamp(sha_file_mtime)
    else:
        last_update = None

    logging.debug('Last update: %s' % str(last_update))

    if last_update is None or last_update < (datetime.now() - timedelta(days=1)):

        if not url_fails('http://stats.screenlyapp.com'):
            latest_sha = req_get('http://stats.screenlyapp.com/latest')

            if latest_sha.status_code == 200:
                with open(sha_file, 'w') as f:
                    f.write(latest_sha.content.strip())
                return True
            else:
                logging.debug('Received non 200-status')
                return
        else:
            logging.debug('Unable to retreive latest SHA')
            return
    else:
        return False


def load_settings():
    """Load settings and set the log level."""
    settings.load()
    logging.getLogger().setLevel(logging.DEBUG if settings['debug_logging'] else logging.INFO)


def asset_loop(scheduler):
    #check_update()
    asset = scheduler.get_next_asset()

    if asset is None:
        logging.info('Playlist is empty. Sleeping for %s seconds', EMPTY_PL_DELAY)
        view_image(HOME + LOAD_SCREEN)
        sleep(EMPTY_PL_DELAY)

    elif path.isfile(asset['uri']) or path.isfile(asset['uri'] + '.mp4') or path.isdir(asset['uri']) or not url_fails(asset['name']):
        name, mime, uri = asset['name'], asset['mimetype'], asset['uri']
        logging.info('Showing asset %s (%s)', name, mime)
        logging.debug('Asset URI %s', uri)

        if 'image' in mime:
            logging.debug('Showing image %s', uri)
            view_image(uri)
        elif 'web' in mime:
            logging.debug('Showing web %s', uri)
            browser_url(name)
        elif 'video' in mime:
            duration = asset['duration']
            view_video(uri, duration)
            if duration == 0:
                logging.debug('Video will play complete')
                filename = uri + '.mp4'
                duration = subprocess.check_output(['ffprobe', '-i', filename, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
            logging.info('Sleeping for %s', duration)
            sleep(math.ceil(float(duration)))
        elif 'presentation' in mime:
            view_slides(uri, asset['duration'])
        else:
            logging.error('Unknown MimeType %s', mime)

        if 'image' in mime or 'web' in mime:
            duration = int(asset['duration'])
            logging.info('Sleeping for %s', duration)
            sleep(duration)

    else:
        logging.info('Asset %s at %s is not available, skipping.', asset['name'], asset['uri'])
        run = sh.Command('/home/pi/sync_assets.sh')
        run(settings['user'], _bg=True)
        sleep(0.5)


def setup():
    global HOME, arch, db_conn, user
    HOME = getenv('HOME', '/home/pi')
    arch = machine()
    
    signal(SIGUSR1, sigusr1)
    signal(SIGUSR2, sigusr2)

    load_settings()

    sh.mkdir(SCREENLY_HTML, p=True)
    #html_templates.black_page(BLACK_PAGE)


def wait_for_splash_page(url):
    max_retries = 20
    retries = 0
    while retries < max_retries:
        fetch_head = req_head(url)
        if fetch_head.status_code == 200:
            break
        else:
            sleep(1)
            retries += 1
            logging.debug('Waiting for splash-page. Retry %d') % retries


def main():
    setup()
    # check_update()
    url = 'file://' + HOME + BLACK_PAGE
    load_browser(url=url)

    scheduler = Scheduler()
    logging.debug('Entering infinite loop.')
    while True:
        asset_loop(scheduler)


if __name__ == "__main__":
    main()
