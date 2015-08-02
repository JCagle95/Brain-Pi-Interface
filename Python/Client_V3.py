############################################################
# This is the Server End of the Raspberry Pi Network
# The connection and temporary text file will be established
# Jackson Cagle, 2015
############################################################

import sys; sys.path.append('../dependencies')
from glob import glob
import Queue
import Generic_Generator as gen
import Open_BCI_Thread as bci
import scipy.io as sio
import socket
import subprocess
import threading
from random import shuffle
from scipy.fftpack import fft
from time import sleep, time, gmtime, strftime
import timeit
import numpy as np
from BCI_Modules import *
import DataAnalysis as Process
import json

def Run_Feedback():
    # Thread added to active eedback dispay
    subprocess.call(['../bin/FeedbackDisplay'])

def FeatureExtraction(Sample,Feature,Data_Array):
    # Append the data
    Data_Array = np.append(Data_Array,Sample,axis=0)
           
    # Common Average Reference
    Sample[:,range(1,9)] = Process.Common_Average_Reference(Sample[:,range(1,9)])

    # Feature Extraction
    if ALPHA:
        Feature = np.append(Feature,Process.AlphaDifference(Sample,([5,6],[7,8]),250))
    else:
        Feature = np.append(Feature,Process.PowerExtraction(Sample[:,3],[8,12],250))

    return (Feature,Data_Array)

# Defined Task variable
#### Edit for Testing/Experimenting
TESTING = True
ALPHA = False
####
with open('Configuration.json', 'r') as infile:
    Configuration = json.load(infile)
Movement_Range_Min = -3.000
Movement_Range_Max = 5.000
Channel = 4
TRIAL_START = 254
TRIAL_END = 192
TRIAL_SUCCESS = 301
CALIBRATION_START = 14
CALIBRATION_STAGE2 = 15
CALIBRATION_END = 19
Max_Trials = 50
Data_Path = '../resource/Recording/'
Experiment_Date = strftime("%b-%d-%Y_",gmtime())
Experiment_ID = len(glob(Data_Path + Experiment_Date + '*_Server.mat')) + 1
Trial_Type = Configuration['Trial_Type']
TaskSetting = Configuration['TaskSetting']

if not TESTING:
    ipAddress = '169.254.0.2'
else:
    ipAddress = '127.0.0.1'
port = '/dev/OpenBCI'
ShutDown = False

print '--------------\n'
print Experiment_Date + '\n'
print '--------------\n'

# Cleanup the content of the text files
Feature_Log = '../resource/FIFO/Y_Direction.txt'
Client_Log = '../resource/FIFO/Feedback_Log_0.txt'
FIFO.Erase(Feature_Log)

# Establish the basic of server.
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ipAddress,5000))
print 'Connected\n'
Sync = Synchronize(client)

# Setup Queue for data
Data_Queue = Queue.Queue()

# Wait for the Feedback Display to start.
#FIFO.Wait(Feedback_Log[0],"Timer on")

# Now signal the Client that the Server is ready. 
client.sendall("Client Ready")
Sync.Wait("Server Ready")
print "All Set"

# Initialize the OpenBCI and start streaming
EEG_Recording = np.arange(0.000,dtype=np.float32)
Frequency = np.fft.fftfreq(50,0.004)
Frequency_Band = np.logical_and(Frequency>8,Frequency<12)
Feature = np.array([])
if not TESTING:
    Board = bci.OpenBCIBoard_Recording(port=port,baud=115200,Queue=Data_Queue,thread=True)
    Board.start()
else:
    Random_Data = sio.loadmat('GenericData.mat')
    SamplingData = Random_Data['GenericData']
    Board = gen.Generic_Generator(Queue=Data_Queue,binSize=50,Data=SamplingData)
    Board.start()

while len(Feature) < 5*TaskSetting['Initiation']:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        if not EEG_Recording.any():
            EEG_Recording = Sample
        else:
            EEG_Recording = np.append(EEG_Recording,Sample,axis=0)

        # Common Average Reference
        Sample[:,range(1,9)] = Process.Common_Average_Reference(Sample[:,range(1,9)])

        # Feature Extraction
        if ALPHA:
            Feature = np.append(Feature,Process.AlphaDifference(Sample,([5,6],[7,8]),250))
        else:
            Feature = np.append(Feature,Process.PowerExtraction(Sample[:,3],[8,12],250))


Trigger = np.array([[len(Feature),CALIBRATION_START]])

print "Calibration Stage 1"
Current_Index = len(Feature)

"""""""""""""""""""""""""""""""""""""""""""""
Resting State. Movement Range Calculation.
"""""""""""""""""""""""""""""""""""""""""""""
while len(Feature)-Current_Index < 5*TaskSetting['Calibration']:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature,EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

print "Calibration Stage 2"
Current_Index = len(Feature)
if FIFO.Check(Client_Log,"Display End"):
    Sync.disconnect()
    Board.stop_streaming()
    sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
    Board.join()
Trigger = np.concatenate((Trigger,np.array([[len(Feature),CALIBRATION_STAGE2]])))

while len(Feature)-Current_Index < 5*TaskSetting['Calibration']:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature,EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

print "Calibration End"
Current_Index = len(Feature)
if FIFO.Check(Client_Log,"Display End"):
    Sync.disconnect()
    Board.stop_streaming()
    sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
    Board.join()
Trigger = np.concatenate((Trigger,np.array([[len(Feature),CALIBRATION_END]])))

# Artificial Power Setting
Min_Power = 0

"""""""""""""""""""""""""""""""""""""""""""""
Trial Start. Classfication Start
"""""""""""""""""""""""""""""""""""""""""""""
for x in range(Max_Trials):
    
    if FIFO.Check(Client_Log,"Display End"):
        break
    
    Current_Index = len(Feature)
    while len(Feature)-Current_Index < 5*TaskSetting['Trial Start']:
        if not Data_Queue.empty():
            Sample = Data_Queue.get()
            Feature,EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)
    
    Trigger = np.concatenate((Trigger,np.array([[len(Feature),TRIAL_START]])))           

    Max_Power = np.percentile(Feature[range(len(Feature)-5*TaskSetting['Fixation']-5*TaskSetting['Trial Start'],len(Feature))],90)
    if not Max_Power == Min_Power:
        Classifier, Offset = Process.Linear_Regression((Min_Power,Max_Power),(Movement_Range_Min,Movement_Range_Max))
    else:
        Classifier = 0
        Offset = 0

    # Clean up the Queue to keep Data in real time
    if Data_Queue.empty():
        print 'No Left Behind'
    else:
        while not Data_Queue.empty():
            Sample = Data_Queue.get()
            Feature, EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)
    Current_Index = len(Feature)

    # Actual Trial Duration
    while len(Feature)-Current_Index < 5*TaskSetting['Trial Duration']:
        if not Data_Queue.empty():
            Sample = Data_Queue.get()
            Feature, EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

            # Classification
            if Trial_Type[x][0] == 0 or Trial_Type[x][0] == 1:
                Y_Direction = str(int(round(Classifier*Feature[len(Feature)-1]+Offset)))+","+str(len(Feature))
            else:
                Y_Direction = str(-int(round(Classifier*Feature[len(Feature)-1]+Offset)))+","+str(len(Feature))
            FIFO.Rewrite(Feature_Log,Y_Direction)
            print 'Classifier Results: ' + Y_Direction
            
        if (FIFO.Check(Client_Log,"Complete")):
            Trigger = np.concatenate((Trigger,np.array([[len(Feature),TRIAL_SUCCESS]])))
            FIFO.Erase(Client_Log)

        if (FIFO.Check(Client_Log,"Display End")):
            ShutDown = True
            print 'Shut Down'
            break

    # Quit program is Shutdown
    if ShutDown:
        break

    Min_Power = np.percentile(Feature[range(len(Feature)-5*TaskSetting['Fixation']-5*TaskSetting['Trial Start'],len(Feature))],10)
    if Min_Power > Max_Power:
        Min_Power = Max_Power * 0.5

    Trigger = np.concatenate((Trigger,np.array([[len(Feature),TRIAL_END]])))
    Current_Index = len(Feature)
    
    # Fixation Period
    while len(Feature)-Current_Index < 5*TaskSetting['Fixation']:
        if not Data_Queue.empty():
            Sample = Data_Queue.get()
            Feature, EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

# Closing the ports and the serial port for BCI Board
# Saving the data
Sync.disconnect()
Board.stop_streaming()
sio.savemat(Data_Path + Experiment_Date + str(Experiment_ID) + '_Client.mat',{'EEG':EEG_Recording,
                                                                              'Trigger':Trigger,
                                                                              'Feature':Feature})
Board.join()
