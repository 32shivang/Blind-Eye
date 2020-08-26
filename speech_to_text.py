import speech_recognition as sr
import sys
import os
import time
os.system('espeak "{}"'.format("hello shivang, we welcome you to this device, Have a great time"))
os.system('espeak "{}"'.format("When you want to close your devise please say stop"))
os.system('espeak "{}"'.format("Say start to start your devise"))
c=0
def speech_to_text():
    print("In")
    with sr.Microphone() as source:
        r = sr.Recognizer()
        # read the audio data from the default microphone
        print("Recognizing... Say Start or stop")

        audio_data = r.record(source, duration=5)
        # convert speech to text
        try:
            text = r.recognize_google(audio_data)
            return text
        except Exception as e:
            print("Waiting..")
        
while(1):
    order=speech_to_text()
    c=c+1
    if(order=="start" or order=="Start"):
        os.startfile('Server_Run.py')
        time.sleep(10)
        print(1)
        os.startfile('Client_Run.py')
    elif(order=="stop" or order=="Stop"):
        exit(0)
    if(c==100):
        os.execv(sys.executable, ['python speech_to_text.py'])
        
        
        
    
