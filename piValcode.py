from threading import *
import time
import cv2
import socket
import io
import pickle
import struct


global connection
global address		
cam=cv2.VideoCapture(0)
#stream = io.BytesIO()
client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client_socket.connect(('192.168.1.5', 9000))#192.168.43.205


cam.set(3, 640);
cam.set(4, 480);

img_counter = 0
print('sending')

while True:
	ret, frame = cam.read()
	data = pickle.dumps(frame, 0)
	size = len(data)
	
	print("frames:","{}: {}".format(img_counter, size))
	len1=str(size)
	
	#sending frame size
	client_socket.send(len1.encode())
	
	#receiving acknowledgement
	ack=client_socket.recv(2)
	
	#sending frame 
	client_socket.send(data)

	buy=client_socket.recv(2)
	print("ack for vinnu: ",buy)
	
	
	
	img_counter += 1
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

	time.sleep(0.03)

cam.release()