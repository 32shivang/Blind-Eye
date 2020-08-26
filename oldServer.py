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

class MainClass:
    global conn1
    global add1
    global frameList
    global FrameCounter
    global server_socket
    global conn2
    global add2
   
    def connectPi():
        global conn1
        global add1
        
        conn1,add1= server_socket.accept()
        time.sleep(0.050)
        print("conection has been established | ip "+add1[0]+" port "+str(add1[1]))
        return conn1

    def connectController():
        global conn2
        global add2
        global FrameCounter
        FrameCounter=0

        conn2,add2= server_socket.accept()
        time.sleep(0.050)
        print("conection has been established | ip "+add2[0]+" port "+str(add2[1]))
        return conn2

    def create_manual_data(frame):
        print("Please input new user ID:")
        new_name = input(); #ez python input()
        f = open('./facerec_128D.txt','r');
        data_set = json.loads(f.read());
        person_imgs = {"Left" : [], "Right": [], "Center": []};
        person_features = {"Left" : [], "Right": [], "Center": []};
        print("Please start turning slowly. Press 'q' to save and add this new user to the dataset");
        
        data = b""
        payload_size = struct.calcsize(">L")
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
            for (i, rect) in enumerate(rects):
                aligned_frame, pos = aligner.align(160,frame,landmarks[:,i]);
                if len(aligned_frame) == 160 and len(aligned_frame[0]) == 160:
                    person_imgs[pos].append(aligned_frame)
                    cv2.imshow("Captured face", aligned_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        for pos in person_imgs: #there r some exceptions here, but I'll just leave it as this to keep it simple
            person_features[pos] = [np.mean(extract_feature.get_features(person_imgs[pos]),axis=0).tolist()]
        data_set[new_name] = person_features;
        f = open('./facerec_128D.txt', 'w');
        f.write(json.dumps(data_set))
        
    def findPeople(features_arr, positions, thres = 0.6, percent_thres = 70):
        '''
        :param features_arr: a list of 128d Features of all faces on screen
        :param positions: a list of face position types of all faces on screen
        :param thres: distance threshold
        :return: person name and percentage
        '''
        f = open('./facerec_128D.txt','r')
        data_set = json.loads(f.read());
        returnRes = [];
        for (i,features_128D) in enumerate(features_arr):
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

        for (i, rect) in enumerate(rects):
            aligned_face, face_pos = aligner.align(160,frame,landmarks[:,i])
            if len(aligned_face) == 160 and len(aligned_face[0]) == 160:
                aligns.append(aligned_face)
                positions.append(face_pos)
            else: 
                print("Align face failed") #log        
        if(len(aligns) > 0):
            features_arr = extract_feature.get_features(aligns)
            recog_data = findPeople(features_arr,positions)
            for (i,rect) in enumerate(rects):
                cv2.rectangle(frame,(rect[0],rect[1]),(rect[2],rect[3]),(255,0,0)) #draw bounding box for the face
                cv2.putText(frame,recog_data[i][0]+" - "+str(recog_data[i][1])+"%",(rect[0],rect[1]),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1,cv2.LINE_AA)
        cv2.imshow("Frame",frame)
        frameList.append(frame)
        FrameCounter=FrameCounter+1
        if FrameCounter >1020:
            frameList.clear()
            FrameCounter=0

    def recPiFrame():
        global conn1
        global add1
        global frame
        global frameList
        global FrameCounter
        FrameCounter=0
        
        conn1,add1= server_socket.accept()
        time.sleep(0.050)
        print("connection has been established | ip "+add1[0]+" port "+str(add1[1]))
        
        data = b""
        payload_size = struct.calcsize(">L")
        print("payload_size: {}".format(payload_size))
        #mode = args.mode
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
            
            camera_recog(frame)
                
           
            cv2.waitKey(1)

    def sendVideoFrame():
        global conn2
        global add2		
        global frameList
        global FrameCounter
        
        conn2=connectController()
        img_counter = 0
        pr=conn2.recv(1024)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        print('sending')
        
        while True:
            time.sleep(0.050)
            if FrameCounter > 3:
                frame =frameList[FrameCounter-2]
                #cv2.imshow('fcontroller',frame)
                result, frame = cv2.imencode('.jpg', frame, encode_param)
                #data = zlib.compress(pickle.dumps(frame, 0))
                data = pickle.dumps(frame, 0)
                size = len(data)

                print("frames:","{}: {}".format(img_counter, size))
                conn2.send(frame)			
                
                img_counter += 1
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break				
        cam.release() 
    def RecCommand():
        
        while True:	
            global conn2
            global add2
            pr=conn2.recv(1024)
            time.sleep(0.050)
            print(pr)

    if __name__ == '__main__':
        global FrameCounter
        global server_socket
        parser = argparse.ArgumentParser()
        parser.add_argument("--mode", type=str, help="Run camera recognition", default="camera")
        args = parser.parse_args(sys.argv[1:]);
        FRGraph = FaceRecGraph();
        MTCNNGraph = FaceRecGraph();
        aligner = AlignCustom();
        extract_feature = FaceFeature(FRGraph)
        face_detect = MTCNNDetect(MTCNNGraph, scale_factor=1); #scale_factor, rescales image for faster detection
        
        server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                
        server_socket.bind(('',9000))
        print('Socket bind complete')
        server_socket.listen(10)
        print('Socket now listening')


        RecPiFrameThread=Thread(target=recPiFrame)
        RecPiFrameThread.start()
        
        FrameCounter=0
        FrameSenderThread=Thread(target=sendVideoFrame)
        cmdRecThread=Thread(target=RecCommand)
        
        if FrameCounter>3:
            FrameSenderThread.start()
            cmdRecThread.start()
        