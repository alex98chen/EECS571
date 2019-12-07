import io
import os
import time
import json
import sys
import socket
import struct
import traceback
import colorlog
import logging
import logging.config

import cv2
import numpy as np

import spotipy
from spotipy import util
from spotipy.oauth2 import SpotifyClientCredentials

from exceptions import (
  CredentialsException,
)

logger = logging.getLogger()

SPOTIPY_CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI")
USERNAME = os.environ.get("SPOTIPY_USERNAME")

CREDENTIALS_MANAGER = SpotifyClientCredentials()
SIFT = cv2.xfeatures2d.SIFT_create()

SCOPES = 'user-library-read playlist-modify-private user-read-currently-playing user-read-playback-state streaming'

class Server():
  def __init__(self, sift_keypoints):
    logger.info("Server::init")
    self.sift_keypoints = sift_keypoints
    self.token = util.prompt_for_user_token(USERNAME, SCOPES, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)
    if not self.token:
      raise CredentialsException("Unable to get spotify token")

    self.socket = socket.socket()
    self.socket.bind(('0.0.0.0', 4321))
    self.socket.listen(0)
    
    self.sp = spotipy.Spotify(auth=self.token, client_credentials_manager=CREDENTIALS_MANAGER)


  def run(self):
    logger.info("Server::run")
    frameNum = 0
    countMatch = 0
    imageThere = False
    playing = False

    #Accept a single connection and make a file-like object out of it
    self.connection = self.socket.accept()[0].makefile('rb')

    try:
      while True:
        logger.info(f"Waiting on frame {frameNum}...")
        initial = time.time()
        frame_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        if not frame_len:
            break

        frameNum += 1
        frame_stream = io.BytesIO()
        frame_stream.write(connection.read(frame_len))
        frame_stream.seek(0)
        frame = cv2.imdecode(np.fromstring(frame_stream.read(), np.uint8), 1)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        maxMatches = 0
        maxTrack = None
        for kp, des, track in self.sift_keypoints[USERNAME]:
          numberOfMatches = numMatches(frame, kp, des)
          if numberOfMatches > maxMatches:
            maxTrack = track

        device_id = getDevice(self.sp)

        if maxMatches > MIN_MATCH_COUNT:
            if countMatch >= BUFFER_AMOUNT:
                imageThere = True
                if not playing and device_id != '':
                    sp.start_playback(device_id=device_id, context_uri=None, uris=[maxTrack], offset=None)
                playing = True
            else:
                countMatch += 1
        else:
            if countMatch < 1:
                imageThere = False
                if playing and device_id != '':
                    sp.pause_playback(device_id=device_id)
                playing = False
            else:
                countMatch -= 1
        if imageThere:
            print("-------------Image is there-----------------")
        else:
            print("*************Image is not there*************")
        print("Time: ", time.time() - initial)
    finally:
      connection.close()
      server_socket.close()

def getDevice(sp):
    devs = sp.devices()
    logger.info(f"Devices: {devs}")

    for device in devs['devices']:
        if device['type'] == 'Smartphone':
            return device['id']
    return ''


def numMatches(frame, kp1, des1):
    start = time.time()
    kp2, des2 = sift.detectAndCompute(frame, None)
    
    #Fast nearest neighbors
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 10)
    search_params = dict(checks = 100)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    # Compute number of matches
    goodMatches = 0
    for m,n in matches:
        if m.distance < 0.7 * n.distance:
            goodMatches += 1
    endTime = time.time() - start
    print("Time for algo: ", endTime)
    return goodMatches

LOGGING = {
    "version": 1,
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
            'stream': 'ext://sys.stdout',
        },
    },
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': "[%(log_color)s%(levelname)-8s%(reset)s] %(message)s",
            'log_colors': {
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            },
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': True
        },
    },
}

logging.config.dictConfig(LOGGING)

if __name__ == "__main__":
  print("test")
  logger.info("Starting server")

  if any(x is None for x in [SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, USERNAME]):
    logger.error("Error: invalid credentials")
    sys.exit(1)

  # Compile image mappings
  user_data = None
  with open('user_data.json', 'r') as infile:
    user_data = json.loads(infile.read())

  sift_keypoints = {}
  for user, data in user_data['users'].items():
    logger.info(f"Processing user {user}")
    kp_dest = []
    for img, track in data.items():
      img = cv2.imread(img, 1).astype('uint8')
      img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
      kp, dest = SIFT.detectAndCompute(img, None)
      kp_dest.append((kp, dest, track))
    sift_keypoints[user] = kp_dest

  while True:
    try:
      server = Server(sift_keypoints)
      server.run()
    except CredentialsException:
      logger.error("Error: unable to start server... invalid credentials")
      time.sleep(5)
    except Exception as e:
      logger.critical("Encountered unexpected error:")
      logger.critical(traceback.format_exc())
      time.sleep(10)


