import io
import socket
import struct
import cv2
import numpy as np
import time 
import spotipy
import spotipy.util as util
import sys
from spotipy.oauth2 import SpotifyClientCredentials

#matchImage = cv2.imread('images/Test480360.jpg', 1)
matchImage = cv2.imread('images/MichiganCoaster640480.jpeg', 1)
matchImage = matchImage.astype('uint8')
matchImage = cv2.cvtColor(matchImage, cv2.COLOR_BGR2GRAY)
MIN_MATCH_COUNT = 15
BUFFER_AMOUNT = 1
sift = cv2.xfeatures2d.SIFT_create()
#orb = cv2.ORB_create()
#sift = cv2.FastFeatureDetector_create()
#sift = cv2.ORB_create()
kp1, des1 = sift.detectAndCompute(matchImage, None)
print("number of key points and des")
print(len(kp1))
print(len(des1))
#des1 = np.float32(des1)


client_id = '685a1af809f94ac881016d869898d0fa'
client_secret = '20fd967fac724a9d80307f622fa43618'
uri = 'http://mysite.com/callback/'

scope = 'user-library-read playlist-modify-private user-read-currently-playing user-read-playback-state streaming'
username = 'alex98chen4'

client_credentials_manager = SpotifyClientCredentials()

token = util.prompt_for_user_token(username, scope, client_id = client_id, client_secret = client_secret, redirect_uri = uri)
    
uriArr = {"uris" : ["spotify:track:6wVbHLCBOCqp6052WcWXLG"]} 


def numMatches(streamImage):
    start = time.time()
    #print(matchImage)
    kp2, des2 = sift.detectAndCompute(streamImage, None)
    """
    kp1, des1 = orb.detectAndCompute(matchImage, None)
    kp2, des2 = orb.detectAndCompute(streamImage, None)
    """
    #des2 = np.float32(des2)
    #endTime = time.time() - start
    #print("Detect for algo: ", endTime)
    
    #Fast nearest neighbors
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 10)
    search_params = dict(checks = 100)

    flann = cv2.FlannBasedMatcher(index_params, search_params)
    #endTime = time.time() - start
    #print("Flann matcher for algo: ", endTime)

    matches = flann.knnMatch(des1, des2, k=2)

    goodMatches = 0
    for m,n in matches:
        if m.distance < 0.7 * n.distance:
            goodMatches += 1
    endTime = time.time() - start
    print("Time for algo: ", endTime)
    return goodMatches

def getDevice(sp):
    devs = sp.devices()
    print(devs)
    #print(devs['devices'][0]['id'])
    for device in devs['devices']:
        if device['type'] == 'Smartphone':
            return device['id']
    return ''

def main():
    if not token:
        print("Can't get token for ", username)
        return 1
    #Start a socket listening for connections on 0.0.0.0:6969
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0',4321))
    server_socket.listen(0)

    #Accept a single connection and make a file-like object out of it
    connection = server_socket.accept()[0].makefile('rb')
    imageNum = 0
    countMatch = 0
    imageThere = False
    
    #make spotify stuff
    sp = spotipy.Spotify(auth=token, client_credentials_manager = client_credentials_manager)
    device_id = getDevice(sp)
    playing = False
    

    try:
        while True:
            initial = time.time()
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break
            #print("Time to get image1: ", time.time() - initial)
            
            image_stream = io.BytesIO()
            #print("Image length: ", image_len)
            image_stream.write(connection.read(image_len))

            image_stream.seek(0)
            #image = Image.open(image_stream)
            #file_bytes = np.asarray(bytearray(image_stream.read()), dtype = np.uint8)
            #print("Time to get image: ", time.time() - initial)

            #image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            #print(time.time()) 
            image = cv2.imdecode(np.fromstring(image_stream.read(), np.uint8), 1)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            #print("Time to decode: ", time.time() - initial)
            #print('image is %dx%d' % image.shape)
            imageNum += 1
            numberOfMatches = numMatches(image)
            #numberOfMatches = 0
            print(numberOfMatches)
            if numberOfMatches > MIN_MATCH_COUNT:
                if countMatch >= BUFFER_AMOUNT:
                    imageThere = True
                    if not playing:
                        sp.start_playback(device_id = device_id, context_uri = None, uris = uriArr['uris'], offset = None)
                    playing = True
                else:
                    countMatch += 1
                
            else:
                if countMatch < 1:
                    imageThere = False
                    if playing:
                        sp.pause_playback(device_id = device_id)
                    playing = False
                else:
                    countMatch -= 1
            if imageThere:
                print("-------------Image is there-----------------")
            else:
                print("*************Image is not there*************")
            #print("image written? ", succ)
            print("Time: ", time.time() - initial)

    finally:
        connection.close()
        server_socket.close()

if __name__ == "__main__":
    main()
