import io
import socket
import struct
from PIL import Image
import cv2
import numpy as np

#Start a socket listening for connections on 0.0.0.0:6969
server_socket = socket.socket()
server_socket.bind(('0.0.0.0',6969))
server_socket.listen(0)

#Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb')
try:
    while True:
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        if not image_len:
            break
        
        image_stream = io.BytesIO()
        print("Image length: ", image_len)
        image_stream.write(connection.read(image_len))

        image_stream.seek(0)
        #image = Image.open(image_stream)
        #file_bytes = np.asarray(bytearray(image_stream.read()), dtype = np.uint8)

        #image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        image = cv2.imdecode(np.fromstring(image_stream.read(), np.uint8), 1)
        print('image is %dx%dx%d' % image.shape)
        

finally:
    connection.close()
    server_socket.close()
