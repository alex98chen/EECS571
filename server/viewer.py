import cv2
#import zmq
#import base64
#import numpy as np

print("setting up context")
#context = zmq.Context()
print("making socket")
"""
footage_socket = context.socket(zmq.SUB)
print("binding socket")
footage_socket.bind('tcp://*:5555')
print("setting up sockopt")
footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))

while True:
    counter = 0
    try:
        print("Waiting for frame")
        frame = footage_socket.recv_string()
        img = base64.b64decode(frame)
        npimg = np.fromstring(img, dtype=np.uint8)
        source = cv2.imdecode(npimg, 1)
        cv2.imwrite("./imgs/file-" + str(counter), source)
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        break
"""
