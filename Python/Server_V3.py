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
    # Thread added to active Feedback dispay
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
Movement_Range_Min = -3.000
Movement_Range_Max = 5.000
TRIAL_START = 254
TRIAL_END = 192
TRIAL_SUCCESS = 301
CALIBRATION_START = 14
CALIBRATION_STAGE2 = 15
CALIBRATION_END = 19
Max_Trials = 20
Data_Path = '../resource/Recording/'
Experiment_Date = strftime("%b-%d-%Y_",gmtime())
Experiment_ID = len(glob(Data_Path + Experiment_Date + '*_Server.mat')) + 1

if not TESTING:
    ipAddress = '169.254.0.2'
else:
    ipAddress = '127.0.0.1'
port = '/dev/OpenBCI'
Trial_Type = [[i%4] for i in range(50)]
shuffle(Trial_Type)
ShutDown = False
TaskSetting = {'Initiation':1,
               'Calibration':10,
               'Trial Start':1,
               'Fixation':5,
               'Trial Duration':8}
Configuration = {'Trial_Type':Trial_Type,
                 'TaskSetting':TaskSetting,
                 'Max_Trials':Max_Trials}
with open('Configuration.json', 'w') as outfile:
    json.dump(Configuration, outfile)

print '--------------\n'
print Experiment_Date + '\n'
print ipAddress + '\n'
print '--------------\n'

# Setup the total number of Raspberry Pi
# Current Version support only one Server and one Client
#Pi_Number = int(raw_input("How many Raspberry Pi will you use? (Including Server): "))
Pi_Number = 2
Feedback_Log = list(range(Pi_Number))

# Cleanup the content of the text files
Feature_Log = '../resource/FIFO/X_Direction.txt'
Trigger_Log = '../resource/FIFO/Trigger_Log.txt'
Trial_Info = '../resource/FIFO/Trial_Information.txt'
FIFO.Erase(Feature_Log)
FIFO.Erase(Trigger_Log)
FIFO.Erase(Trial_Info)
for n in range(Pi_Number):
    Feedback_Log[n] = '../resource/FIFO/Feedback_Log_' + str(n) + '.txt'
    FIFO.Erase(Feedback_Log[n])

# Establish the basic of server.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ipAddress,5000))
print 'The server established at ' + ipAddress + '\n'
print 'The Port is ' + str(5000) + '\n'

# Setup Queue for data
Data_Queue = Queue.Queue()

# The server now listen to 1 connection
server.listen(Pi_Number-1)

connection, client_address = server.accept()
print 'Connected\n'

Sync = Synchronize(connection)

Display_Thread = threading.Thread(target=Run_Feedback)
Display_Thread.start()

# Wait for the Feedback Display to start.
FIFO.Wait(Feedback_Log[0],"Timer on")

# Now signal the Client that the Server is ready. 
connection.sendall("Server Ready")
Sync.Wait("Client Ready")
FIFO.Rewrite(Trigger_Log,"All Set")
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


FIFO.Rewrite(Trigger_Log,"Calibration On")
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

FIFO.Rewrite(Trigger_Log,'Calibration Stage2')
print "Calibration Stage 2"
Current_Index = len(Feature)
if FIFO.Check(Feedback_Log[0],"Display End"):
    Sync.disconnect()
    Board.stop_streaming()
    sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
    Board.join()
Trigger = np.concatenate((Trigger,np.array([[len(Feature),CALIBRATION_STAGE2]])))

while len(Feature)-Current_Index < 5*TaskSetting['Calibration']:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature,EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

FIFO.Rewrite(Trigger_Log, 'Calibration End')
print "Calibration End"
Current_Index = len(Feature)
if FIFO.Check(Feedback_Log[0],"Display End"):
    Sync.disconnect()
    Board.stop_streaming()
    sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
    Board.join()
Trigger = np.concatenate((Trigger,np.array([[len(Feature),CALIBRATION_END]])))

Min_Power = 0

"""""""""""""""""""""""""""""""""""""""""""""
Trial Start. Classfication Start
"""""""""""""""""""""""""""""""""""""""""""""
for x in range(Max_Trials):
    
    if FIFO.Check(Feedback_Log[0],"Display End"):
        break
            
    # Send Trial Info and wait 1 second for display
    FIFO.Rewrite(Trial_Info,str(Trial_Type[x][0]))
    FIFO.Rewrite(Trigger_Log,'Ready')
    print 'Ready'
    
    Current_Index = len(Feature)
    while len(Feature)-Current_Index < 5*TaskSetting['Trial Start']:
        if not Data_Queue.empty():
            Sample = Data_Queue.get()
            Feature,EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)
    
    # Signal Start
    FIFO.Rewrite(Trigger_Log,"Trial Start")
    print 'Write "Trial Start"'
    Trigger = np.concatenate((Trigger,np.array([[len(Feature),TRIAL_START]])))           

    Max_Power = np.percentile(Feature[range(len(Feature)-5*TaskSetting['Fixation']-5*TaskSetting['Trial Start'],len(Feature))],90)
    print Max_Power
    if not Max_Power == Min_Power:
        Classifier, Offset = Process.Linear_Regression((Min_Power,Max_Power),(Movement_Range_Min,Movement_Range_Max))
        print Classifier
    else:
        print 'ERROR'
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
            if Trial_Type[x][0] == 0 or Trial_Type[x][0] == 2:
                X_Direction = str(int(round(Classifier*Feature[len(Feature)-1]+Offset)))+","+str(len(Feature))
            else:
                X_Direction = str(-int(round(Classifier*Feature[len(Feature)-1]+Offset)))+","+str(len(Feature))
            FIFO.Rewrite(Feature_Log,X_Direction)
            #print 'Classifier Results: ' + X_Direction
            
        if (FIFO.Check(Feedback_Log[0],"Complete")):
            Trigger = np.concatenate((Trigger,np.array([[len(Feature),TRIAL_SUCCESS]])))
            FIFO.Erase(Feedback_Log[0])

        if (FIFO.Check(Feedback_Log[0],"Display End")):
            ShutDown = True
            print 'Shut Down'
            break

    # Quit program is Shutdown
    if ShutDown:
        break

    Min_Power = np.percentile(Feature[range(len(Feature)-5*TaskSetting['Fixation']-5*TaskSetting['Trial Start'],len(Feature))],10)
    if Min_Power > Max_Power:
        Min_Power = Max_Power * 0.5
    print Min_Power
    
    # Signal the end of trial
    FIFO.Rewrite(Trigger_Log,"Trial End")
    print 'Trial End'
    Trigger = np.concatenate((Trigger,np.array([[len(Feature),TRIAL_END]])))
    Current_Index = len(Feature)
    
    # Fixation Period
    while len(Feature)-Current_Index < 5*TaskSetting['Fixation']:
        if not Data_Queue.empty():
            Sample = Data_Queue.get()
            Feature, EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

FIFO.Rewrite(Trigger_Log,"ALL FINISH")
print 'Sent "ALL FINISH"'

# Closing the ports and the serial port for BCI Board
# Saving the data
Sync.disconnect()
Board.stop_streaming()
sio.savemat(Data_Path + Experiment_Date + str(Experiment_ID) + '_Server.mat',{'EEG':EEG_Recording,
                                                                              'Trigger':Trigger,
                                                                              'Feature':Feature})
Board.join()
