import cv2
import io
import socket
import struct
import time
import pickle
import zlib
import time
global connected
connected = True
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#socket creation
client_socket.connect(('192.168.1.5', 9000))
connection = client_socket.makefile('wb')
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

cam = cv2.VideoCapture(0)

cam.set(3, 640);
cam.set(4, 480);

img_counter = 0			
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
while True:
	ret, frame = cam.read()
	result, frame = cv2.imencode('.jpg', frame, encode_param)
	
	data = pickle.dumps(frame, 0)
	size = len(data)


	print("{}: {}".format(img_counter, size))
	try :
		client_socket.sendall(struct.pack(">L", size) + data)
		#cv2.imshow("f",frame)
		print("sent")
		'''encodeStr=client_socket.recv(1024)
		decodeStr=encodeStr.decode()
		print("unknown person=",decodeStr)'''
		
	except Exception as e:
		connected=False
		print("disconnected")
		break
		
	img_counter += 1
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
	time.sleep(0.01)
        

cam.release()

