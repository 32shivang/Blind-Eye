import cv2
import sys
import io
import socket
import struct
import time
import pickle
import zlib
import time
global connected
from threading import *
import time
import speech_recognition as sr
import os
import pyttsx3
engine=pyttsx3.init('sapi5')

voices=engine.getProperty('voices')
engine.setProperty('voice',voices[0].id)

def speak(audio):
	engine.say(audio)
	engine.runAndWait()
	


connected = True
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#socket creation
client_socket.connect(('192.168.0.105', 9000))
connection = client_socket.makefile('wb')
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

cam = cv2.VideoCapture(0)

cam.set(3, 640);
cam.set(4, 480);

		
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
def sendFrame():

    while True:
        ret, frame = cam.read()
        result, frame = cv2.imencode('.jpg', frame, encode_param)
        print(frame)
        time.sleep(0.01)
        data = pickle.dumps(frame, 0)
        size = len(data)
        img_counter = 0	
        
        print("{}: {}".format(img_counter, size))
        try :
            client_socket.sendall(struct.pack(">L", size) + data)
            #cv2.imshow("f",frame)
            print("sent")
            
        except Exception as e:
            connected=False
            print("disconnected")
            break
            
        img_counter += 1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        time.sleep(0.01)
            

    cam.release()

def recName():
    encodeStr=client_socket.recv(1024)
    time.sleep(0.01)
    decodeStr=encodeStr.decode()
    print("client")
    '''if(decodeStr=="unknown" or decodeStr=="Unknown"):
        speak("Did you want to save his Name. Please say Yes or NO")
        with sr.Microphone() as source:
            r = sr.Recognizer()
            # read the audio data from the default microphone
            speak("Recognizing... Say Yes or NO")
            audio_data = r.record(source, duration=5)
            # convert speech to text
            text = r.recognize_google(audio_data)
            if(text=="yes" or text=="Yes"):
                speak("Sending the data please wait..")
                client_socket.sendall(text)
            elif(text=="No" or text=="no"):
                speak("Thanks for choosing us. Bye for now.")
                exit(0)
            else:
                speak("Data not recognized properly")
    else:
        speak("Person name is", decodeStr)
        speak("Thanks for choosing us. Bye for now.")
        exit(0)'''
    if(decodeStr=="exit"):
        exit(0)
    if(decodeStr=="restart"):
        print("restarting..")
        os.execv(sys.executable, ['python Client_Run.py'])
            
	
   


if __name__ == '__main__':
	sender=Thread(target=sendFrame)
	sender.start()
	reciever=Thread(target=recName)
	reciever.start()
		
