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
import copy

import threading
import cv2
import numpy as np

import spotipy
from spotipy import util
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime

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

#MIN_MATCH_COUNT = 70
MIN_MATCH_RATIO = 0.05
BUFFER_AMOUNT = 1

SCOPES = 'user-library-read playlist-modify-private user-read-currently-playing user-read-playback-state streaming'



class Server():
  def __init__(self, sift_keypoints):
    logger.info("Server::init")
    self.newestFrameLock = threading.Lock()
    self.newestFrame = None
    self.frameAvailable = False
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
    connection = self.socket.accept()[0].makefile('rb')

    try:
      listenThread = threading.Thread(target=self.listenForFrame, args=(connection,))
      listenThread.start()

      while True:
        frameData = None
        with self.newestFrameLock:
          if self.newestFrame is None:
            continue
          logger.info(f"length of newestFrame: {len(self.newestFrame)}")
          frameData = copy.deepcopy(self.newestFrame)

        logger.info(f"length of frameData: {len(frameData)}")
        initial = time.time()
        frameStream = io.BytesIO()
        frameStream.write(frameData)
        frameStream.seek(0)

        frameTest = np.fromstring(frameStream.read(), np.uint8)
        if frameTest is None:
          logger.critical("test")

        logger.info(f"length of frameTest: {len(frameTest)}")

        frame = cv2.imdecode(frameTest, cv2.IMREAD_GRAYSCALE)


        


        #blurriness = cv2.Laplacian(frame, cv2.CV_64F).var()
        #if frame is None or blurriness < 100:
        #  logger.info(f"Frame was ignored because blurry: {blurriness}")
        #  continue
        maxMatches = 0
        maxRatio = 0.
        maxTrack = None
        maxImgPath = None
        for kp, des, imgPath, track in self.sift_keypoints[USERNAME]:
          numberOfMatches = numMatches(frame, kp, des)
          ratioOfMatches = numberOfMatches / len(kp)
          logger.info(f"Image: {imgPath} -> {numberOfMatches}/{len(kp)} = {ratioOfMatches}")
          #logger.info(f"Received {numberOfMatches} matches")
          #if numberOfMatches > maxMatches:
          #  maxMatches = numberOfMatches
          #  maxTrack = track
          if ratioOfMatches > maxRatio:
            maxRatio = ratioOfMatches
            maxTrack = track
            maxImgPath = imgPath

        device_id = getDevice(self.sp)
        #if maxMatches > MIN_MATCH_COUNT:
        if maxRatio > MIN_MATCH_RATIO:
            if countMatch >= BUFFER_AMOUNT:
                imageThere = True
                if not playing and device_id != '':
                    logger.info(f"Playing song for image {maxImgPath}")
                    self.sp.start_playback(device_id=device_id, context_uri=None, uris=[maxTrack], offset=None)
                    playing = True
            else:
                countMatch += 1
        else:
            if countMatch < 1:
                imageThere = False
                if playing and device_id != '':
                    logger.info(f"Stopping song for image {maxImgPath}")
                    self.sp.pause_playback(device_id=device_id)
                    playing = False
            else:
                countMatch -= 1
        #if imageThere:
            #print("-------------Image is there-----------------")
        #else:
            #print("*************Image is not there*************")
        print("Time: ", time.time() - initial)
    finally:
      connection.close()
      self.socket.close()


  def listenForFrame(self, connection):
    frameNum = 0
    while True:
    
      initial = time.time()
      #frame_time = struct.unpack('<q', connection.read(8))[0]
      #logger.info(f"Waiting on frame {frameNum}...")
      frame_len = struct.unpack('<L', connection.read(4))[0]
      data = connection.read(frame_len)


      #now = int(datetime.utcnow().timestamp() * 1000)
      #age = now - frame_time

      #logger.info(f"Received frame {frameNum}, len: {frame_len}")

      #if age > 300:
      #  logger.info("Dropping frame {frameNum} - too old by {age} ms")
      #  continue

      #data = connection.read(200000)
      #frame_len = struct.unpack('<L', data[0:4])[0]
      if not frame_len:
        logger.info("bad")
        break

      frameNum += 1
      #frame_stream.write(data[4:4+frame_len])
      with self.newestFrameLock:
        #logger.info("writing to newest frame")
        self.newestFrame = data
        #self.newestFrame = cv2.cvtColor(self.newestframe.astype('uint8'), cv2.COLOR_BGR2GRAY)
      print(f"Time to read data {time.time() - initial}")


def getDevice(sp):
    devs = sp.devices()
    for device in devs['devices']:
        if device['type'] == 'Smartphone':
            return device['id']
    return ''


def numMatches(frame, kp1, des1):
    start = time.time()
    kp2, des2 = SIFT.detectAndCompute(frame, None)
    if len(kp1) <= 1 or len(kp2) <= 1:
      return 0
    if des2 is None:
      return 0
    
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
    #print("Time for algo: ", endTime)
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
    for imgPath, track in data.items():
      img = cv2.imread(imgPath, 1).astype('uint8')
      img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
      kp, dest = SIFT.detectAndCompute(img, None)
      if len(kp) >= 500:
        kp_dest.append((kp, dest, imgPath, track))
        logger.info(f'Number of keypoints for {imgPath}: {len(kp)}')
      else:
        logger.info(f"Image {imgPath} rejected: {len(kp)} < 500")
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
      time.sleep(5)


