import socket
import sys
import cv2
import pickle
import numpy as np
import struct ## new
import zlib
import tensorflow as tf
from align_custom import AlignCustom
from face_feature import FaceFeature
from mtcnn_detect import MTCNNDetect
from tf_graph import FaceRecGraph
import argparse
import sys
import json
import time
from threading import *

global server_socket
global FrameCounter
global frameList
global name
def createSocket():
	global server_socket
	global conn1
	global name
	server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	print('Socket created')

	server_socket.bind(('',9000))
	print('Socket bind complete')
	server_socket.listen(10)
	print('Socket now listening')

def sendName(str):
	global conn1
	global add1
	global name
	
	print("hello send")
	encdStr=str.encode()
	conn1.send(encdStr)
	time.sleep(0.01)
	print("Sending Name=str",str)
	

def create_manual_data(frame):
	global conn1
	global add1
	global name
	conn=conn1
	print("Please input new user ID:")
	new_name = input(); #ez python input()
	f = open('./facerec_128D.txt','r');
	data_set = json.loads(f.read());
	person_imgs = {"Left" : [], "Right": [], "Center": []};
	person_features = {"Left" : [], "Right": [], "Center": []};
	print("Please start turning slowly. Press 'q' to save and add this new user to the dataset");
	#sendName("Unknown")

	data = b""
	payload_size = struct.calcsize(">L")
	try:
		while True:
			time.sleep(0.050)
			while len(data) < payload_size:
				data += conn.recv(4096)
			packed_msg_size = data[:payload_size]
			data = data[payload_size:]
			msg_size = struct.unpack(">L", packed_msg_size)[0]
			while len(data) < msg_size:
				data += conn.recv(4096)
			frame_data = data[:msg_size]
			data = data[msg_size:]
			frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
			frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
			rects, landmarks = face_detect.detect_face(frame, 80);  # min face size is set to 80x80
			for i in range(len(rects)):
				rect = rects[i]
				aligned_frame, pos = aligner.align(160,frame,landmarks[:,i]);
				if len(aligned_frame) == 160 and len(aligned_frame[0]) == 160:
					person_imgs[pos].append(aligned_frame)
					cv2.imshow("Captured face", aligned_frame)
			key = cv2.waitKey(1) & 0xFF
			if key == ord("q"):
				break
	except Exception as e:
		print(e,"create_manual_data")
	for pos in person_imgs: #there r some exceptions here, but I'll just leave it as this to keep it simple
		person_features[pos] = [np.mean(extract_feature.get_features(person_imgs[pos]),axis=0).tolist()]
	data_set[new_name] = person_features;
	f = open('./facerec_128D.txt', 'w');
	f.write(json.dumps(data_set))

	
def findPeople(features_arr, positions, thres = 0.6, percent_thres = 70):
	global conn1
	global name
	f = open('./facerec_128D.txt','r')
	data_set = json.loads(f.read());
	returnRes = [];
	for i in range(len(features_arr)):
		features_128D=features_arr[i]
		result = "Unknown";
		smallest = sys.maxsize
		for person in data_set.keys():
			person_data = data_set[person][positions[i]];
			for data in person_data:
				distance = np.sqrt(np.sum(np.square(data-features_128D)))
				if(distance < smallest):
					smallest = distance;
					result = person;
		percentage =  min(100, 100 * thres / smallest)
		if percentage <= percent_thres :
			result = "Unknown"
		if(result == 'Unknown'):
			print("Unknown")					
		else:
			print('Neutralize')
	
	returnRes.append((result,percentage))
	return returnRes

def camera_recog(frame):
    global frameList
    global FrameCounter
    global conn1
    global add1

    detect_time = time.time()
    rects, landmarks = face_detect.detect_face(frame,80);#min face size is set to 80x80
    aligns = []
    positions = []
    try:
        for (i) in range(len(rects)):
            rect= rects[i]
            print('niche vala')
            aligned_face, face_pos = aligner.align(160,frame,landmarks[:,i])
            if len(aligned_face) == 160 and len(aligned_face[0]) == 160:
                aligns.append(aligned_face)
                positions.append(face_pos)
            else: 
                print("Align face failed") #log        
        if(len(aligns) > 0):
            features_arr = extract_feature.get_features(aligns)
            recog_data = findPeople(features_arr,positions)
            a,b=recog_data[0][0],recog_data[0][1]
            print("a=",a)
            sendName(a)
            if(a=="Unknown"):
                create_manual_data(frame)
                exit(30)
            print("b=",b)

            for (i) in range(len(rects)):
                rect= rects[i]
                cv2.rectangle(frame,(rect[0],rect[1]),(rect[2],rect[3]),(255,0,0)) #draw bounding box for the face
                cv2.putText(frame,recog_data[i][0]+" - "+str(recog_data[i][1])+"%",(rect[0],rect[1]),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1,cv2.LINE_AA)
        cv2.imshow("Frame",frame)
        frameList.append(frame)

    except Exception as e:
        print(e,"---------------------camera recog")
		

def recPiFrame():
	global frameList
	global server_socket
	global conn1
	frameList=[]	
	conn1,add1= server_socket.accept()
	print("conection has been established | ip "+add1[0]+" port "+str(add1[1]))

	data = b""
	payload_size = struct.calcsize(">L")
	print("payload_size: {}".format(payload_size))
	mode = args.mode
	while True:
		time.sleep(0.050)
		while len(data) < payload_size:
			data += conn1.recv(4096)
		packed_msg_size = data[:payload_size]
		data = data[payload_size:]
		msg_size = struct.unpack(">L", packed_msg_size)[0]
		while len(data) < msg_size:
			data += conn1.recv(4096)
		frame_data = data[:msg_size]
		data = data[msg_size:]
		frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
		frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
		if(mode == "camera"):
			camera_recog(frame)
			
		elif mode == "input":
			create_manual_data(frame);
		cv2.waitKey(1)


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("--mode", type=str, help="Run camera recognition", default="camera")
	args = parser.parse_args(sys.argv[1:]);
	FRGraph = FaceRecGraph();
	MTCNNGraph = FaceRecGraph();
	aligner = AlignCustom();
	extract_feature = FaceFeature(FRGraph)
	face_detect = MTCNNDetect(MTCNNGraph, scale_factor=1); #scale_factor, rescales image for faster detection		
	mode = args.mode
	if mode == "input":
		print("manual")
		#create_manual_data();
	createSocket()
	recThread=Thread(target=recPiFrame)
	recThread.start()
	recThread.join()
	

	if FrameCounter >3:
		FrameSenderThread.start()
		cmdRecThread.start()
