############################################################
# This is the Server End of the Raspberry Pi Network
# The connection and temporary text file will be established
# Jackson Cagle, 2015
############################################################

import sys; sys.path.append('../dependencies')
import Queue
import Generic_Generator as gen
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

def Run_Feedback():
    # Thread added to active Feedback dispay
    subprocess.call(['../bin/FeedbackDisplay.exe'])

def FeatureExtraction(Sample,Feature,Data_Array):
    # Append the data
    Data_Array = np.append(Data_Array,Sample,axis=0)
        
    # Common Average Reference
    Sample[:,range(1,9)] = Sample[:,range(1,9)]-np.tile(np.mean(Sample[:,range(1,9)],axis=1),(Sample.shape[1]-1,1)).T

    # Power after Referece
    Power = abs(fft(Sample[:,Channel]))
    Feature.append(np.sum(Power[Frequency_Band]))
    return (Feature,Data_Array)

# Defined Task variable
Movement_Range_Min = -5.000
Movement_Range_Max = 5.000
Channel = 4
TRIAL_START = 254
TRIAL_END = 192
TRIAL_SUCCESS = 301
CALIBRATION_START = 14
CALIBRATION_STAGE2 = 15
CALIBRATION_END = 19
Max_Trials = 50
Experiment_ID = strftime("%b_%d_%Y_%H",gmtime())
ipAddress = '127.0.0.1'
port = '/dev/OpenBCI'
Trial_Type = [[i%4] for i in range(50)]
shuffle(Trial_Type)
shuffle(Trial_Type)
ShutDown = False

print '--------------\n'
print Experiment_ID + '\n'
print ipAddress + '\n'
print '--------------\n'

# Setup the total number of Raspberry Pi
# Current Version support only one Server and one Client
#Pi_Number = int(raw_input("How many Raspberry Pi will you use? (Including Server): "))
Pi_Number = 2
Feedback_Log = list(range(Pi_Number))

# Cleanup the content of the text files
Classifier_Results = '../resource/FIFO/Classifier_Results.txt'
Trigger_Log = '../resource/FIFO/Trigger_Log.txt'
Trial_Info = '../resource/FIFO/Trial_Information.txt'
FIFO.Erase(Classifier_Results)
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
Feature = list()
Generator = gen.Generic_Generator(Queue=Data_Queue,binSize=50)
EEG_Time = timeit.default_timer()
Generator.start()
sleep(1)

FIFO.Rewrite(Trigger_Log,"Calibration On")
Trigger = np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_START]])

print "Calibration Stage 1"

"""""""""""""""""""""""""""""""""""""""""""""
Resting State. Movement Range Calculation.
"""""""""""""""""""""""""""""""""""""""""""""

while len(EEG_Recording) < 250*10:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        if not EEG_Recording.any():
            EEG_Recording = Sample
        else:
            EEG_Recording = np.append(EEG_Recording,Sample,axis=0)

        # Common Average Reference
        Sample[:,range(1,9)] = Sample[:,range(1,9)]-np.tile(np.mean(Sample[:,range(1,9)],axis=1),(Sample.shape[1]-1,1)).T

        # Power after Referece
        Power = abs(fft(Sample[:,Channel]))
        Feature.append(np.sum(Power[Frequency_Band]))

FIFO.Rewrite(Trigger_Log,'Calibration Stage2')
print "Calibration Stage 2"

if FIFO.Check(Feedback_Log[0],"Display End"):
    Sync.disconnect()
    Generator.stop_streaming()
    sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
    Generator.join()

Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_STAGE2]])))

while len(EEG_Recording) < 250*20:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature,EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

Max_Movement = np.array(Feature).max()
Min_Movement = np.array(Feature).min()
Classifier = (Movement_Range_Max-Movement_Range_Min)/(Max_Movement-Min_Movement)

FIFO.Rewrite(Trigger_Log, 'Calibration End')
print "Calibration End"

if FIFO.Check(Feedback_Log[0],"Display End"):
    Sync.disconnect()
    Generator.stop_streaming()
    sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
    Generator.join()

Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_END]])))

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
    sleep(1)

    # Signal Start
    FIFO.Rewrite(Trigger_Log,"Trial Start")
    sleep(2)
    Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_START]])))           
    connection.sendall('Start')
    
    # Clean up the Queue to keep Data in real time
    while not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature, EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)
    Start_Point = time()
    
    while ((time()-Start_Point) < 5):
        # Extract Feature
        while True:
            if not Data_Queue.empty():
                Sample = Data_Queue.get()
                Feature, EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)
                break

        # Classification
        X_Direction = int(round(Classifier*Feature[len(Feature)-1]+Movement_Range_Min))

        # Data Sharing
        Y_Direction = connection.recv(32)
        DataString = str(X_Direction) + "," + str(Y_Direction) + "," + str(len(Feature)) + "\n"
        print 'Classifier Results: ' + DataString
        FIFO.Rewrite(Classifier_Results, DataString)
        if (FIFO.Check(Feedback_Log[0],"Complete")):
            Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_SUCCESS]])))
            FIFO.Erase(Feedback_Log[0])
            connection.sendall('End')
            Sync.Wait('Client End')
            ShutDown = True
            print 'Shut Down'
            sleep(1)
            break
        connection.sendall('Done')
        
    if not ShutDown:
        connection.sendall('End')
        Sync.Wait('Client End')
    FIFO.Rewrite(Trigger_Log,"Trial End")
    print 'Trial End'
    sleep(2)
    Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_END]])))
    
FIFO.Rewrite(Trigger_Log,"ALL FINISH")
print 'Sent "ALL FINISH"'
connection.sendall('ALL FINISH')

# Closing the ports and the serial port for BCI Board
# Saving the data
Sync.disconnect()
Generator.stop_streaming()
sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
Generator.join()
