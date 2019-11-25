import io
import socket
import struct
import time
import picamera
import cv2


# Connect a client socket to my_server:8000 (change my_server to the
# hostname of your server
while True:
    client_socket = socket.socket()
    client_socket.connect(('138.68.230.179', 4321))

    # Make a file-like object out of the connection
    connection = client_socket.makefile('wb')
    try:
        with picamera.PiCamera() as camera:
            camera.resolution = (480, 360)
            camera.framerate = 60
            camera.exposure_mode = 'sports'
            # Start a preview and let the camera warm up for 2 seconds
            camera.start_preview()
            time.sleep(2)

            # Note the start time and construct a stream to hold image data
            # temporarily (we could write it directly to connection but in this
            # case we want to find out the size of each capture first to keep
            # our protocol simple)
            start = time.time()
            stream = io.BytesIO()
            for foo in camera.capture_continuous(stream, 'jpeg', quality =60):
                # Write the length of the capture to the stream and flush to
                # ensure it actually gets sent
                length = stream.tell()
                print(length)
                struct.pack('<L', length)
                connection.write(struct.pack('<L', length))
                connection.flush()
                # Rewind the stream and send the image data over the wire
                stream.seek(0)
                connection.write(stream.read())
                #print(time.time())
                # If we've been capturing for more than 30 seconds, quit
                #if time.time() - start > 60:
                #    break
                # Reset the stream for the next capture
                stream.seek(0)
                stream.truncate()
        # Write a length of zero to the stream to signal we're done
        connection.write(struct.pack('<L', 0))
    finally:
        connection.close()
        client_socket.close()
