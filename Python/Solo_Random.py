############################################################
# This is the Server End of the Raspberry Pi Network
# The connection and temporary text file will be established
# Jackson Cagle, 2015
############################################################

import sys; sys.path.append('../dependencies')
import Generic_Generator as gen
import Queue
import scipy.io as sio
import socket
import threading
import subprocess
from random import shuffle
from scipy.fftpack import fft
from time import sleep, time, gmtime, strftime
import timeit
import numpy as np
from BCI_Modules import *

def Run_Feedback():
    # Thread added to active Feedback dispay
    subprocess.call(['../bin/Solo_FeedbackDisplay.exe'])

def FeatureExtraction(Sample,Feature1,Feature2,Data_Array):
    # Append the data
    Data_Array = np.append(Data_Array,Sample,axis=0)
        
    # Common Average Reference
    Sample[:,range(1,9)] = Sample[:,range(1,9)]-np.tile(np.mean(Sample[:,range(1,9)],axis=1),(Sample.shape[1]-1,1)).T

    # Power after Referece
    Power1 = abs(fft(Sample[:,Channel[3]]))
    Power2 = abs(fft(Sample[:,Channel[7]]))
    Feature1.append(np.sum(Power1[Frequency_Band]))
    Feature2.append(np.sum(Power2[Frequency_Band]))
    return (Feature1,Feature2,Data_Array)

# Defined Task variable
Movement_Range_Min = -5.000
Movement_Range_Max = 5.000
Channel = range(1,9)
TRIAL_START = 254
TRIAL_END = 192
TRIAL_SUCCESS = 301
CALIBRATION_START = 14
CALIBRATION_STAGE2 = 15
CALIBRATION_END = 19
Max_Trials = 50
Experiment_ID = strftime("%b-%d-%Y_%H-%M-%S",gmtime())
Trial_Type = [[i%4] for i in range(50)]
shuffle(Trial_Type)
shuffle(Trial_Type)

print '--------------\n'
print Experiment_ID + '\n'
print '--------------\n'

# Cleanup the content of the text files
Classifier_Results = '../resource/FIFO/Classifier_Results.txt'
Trigger_Log = '../resource/FIFO/Trigger_Log.txt'
Trial_Info = '../resource/FIFO/Trial_Information.txt'
Feedback_Log = '../resource/FIFO/Solo_Feedback_Log.txt'
FIFO.Erase(Classifier_Results)
FIFO.Erase(Trigger_Log)
FIFO.Erase(Trial_Info)
FIFO.Erase(Feedback_Log)

# Setup Queue for data
Data_Queue = Queue.Queue()

Display_Thread = threading.Thread(target=Run_Feedback)
Display_Thread.start()

# Wait for the Feedback Display to start.
FIFO.Wait(Feedback_Log,"Timer on")
print 'Receive "Timer on"'
FIFO.Rewrite(Trigger_Log,"All Set")
print 'Sent "All Set"'

# Initialize the Generic Generator and start streaming
EEG_Recording = np.arange(0.000)
Frequency = np.fft.fftfreq(50,0.004)
Frequency_Band = np.logical_and(Frequency>8,Frequency<12)
Feature1 = list()
Feature2 = list()
Generator = gen.Generic_Generator(Queue=Data_Queue,binSize=50)
EEG_Time = timeit.default_timer()
Generator.start()

FIFO.Rewrite(Trigger_Log,"Calibration On")
Trigger = np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_START]])

"""""""""""""""""""""""""""""""""""""""""""""
Resting State. Movement Range Calculation.
"""""""""""""""""""""""""""""""""""""""""""""

print 'Calibration Stage 1'

while len(EEG_Recording) < 250*5:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        if not EEG_Recording.any():
            EEG_Recording = Sample
        else:
            EEG_Recording = np.append(EEG_Recording,Sample,axis=0)

        # Common Average Reference
        Sample[:,range(1,9)] = Sample[:,range(1,9)]-np.tile(np.mean(Sample[:,range(1,9)],axis=1),(Sample.shape[1]-1,1)).T

        # Power after Referece
        Power1 = abs(fft(Sample[:,Channel[3]]))
        Power2 = abs(fft(Sample[:,Channel[7]]))
        Feature1.append(np.sum(Power1[Frequency_Band]))
        Feature2.append(np.sum(Power2[Frequency_Band]))

FIFO.Rewrite(Trigger_Log,'Calibration Stage2')
if FIFO.Check(Feedback_Log,"Display End"):
    Sync.disconnect()
    Generator.stop_streaming()
    sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
    Generator.join()

print 'Calibration Stage 2'

Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_STAGE2]])))

while len(EEG_Recording) < 250*10:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature1,Feature2,EEG_Recording = FeatureExtraction(Sample,Feature1,Feature2,EEG_Recording)

Classifier1 = (Movement_Range_Max-Movement_Range_Min)/(np.array(Feature1).max()-np.array(Feature1).min())
Classifier2 = (Movement_Range_Max-Movement_Range_Min)/(np.array(Feature2).max()-np.array(Feature2).min())

print str(np.array(Feature1).max()) + ',' + str(np.array(Feature1).min())
print str(np.array(Feature2).max()) + ',' + str(np.array(Feature2).min())

FIFO.Rewrite(Trigger_Log, 'Calibration End')
if FIFO.Check(Feedback_Log,"Display End"):
    Sync.disconnect()
    Generator.stop_streaming()
    sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
    Generator.join()

Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_END]])))

print 'Calibration End'

"""""""""""""""""""""""""""""""""""""""""""""
Trial Start. Classfication Start
"""""""""""""""""""""""""""""""""""""""""""""

for x in range(Max_Trials):
    
    if FIFO.Check(Feedback_Log,"Display End"):
        break
    
    # Send Trial Info and wait 1 second for display
    FIFO.Rewrite(Trial_Info,str(Trial_Type[x][0]))
    FIFO.Rewrite(Trigger_Log,'Ready')
    print 'Ready'
    
    # Clean up the Queue to keep Data in real time
    while not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature1, Feature2, EEG_Recording = FeatureExtraction(Sample,Feature1,Feature2,EEG_Recording)

    # Signal Start
    Start_Point = time()
    FIFO.Rewrite(Trigger_Log,"Trial Start")
    print 'Trial Start'
    sleep(3)
    Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_START]])))           
    
    while ((time()-Start_Point) < 10):
        # Extract Feature
        while True:
            if not Data_Queue.empty():
                Sample = Data_Queue.get()
                Feature1, Feature2, EEG_Recording = FeatureExtraction(Sample,Feature1,Feature2,EEG_Recording)
                break

        # Classification
        X_Direction = int(round(Classifier1*Feature1[len(Feature1)-1]+Movement_Range_Min))
        Y_Direction = int(round(Classifier2*Feature2[len(Feature2)-1]+Movement_Range_Min))

        # Data Sharing
        DataString = str(X_Direction) + "," + str(Y_Direction) + "," + str(len(Feature1)) + "\n"
        FIFO.Rewrite(Classifier_Results, DataString)
        if (FIFO.Check(Feedback_Log,"Complete")):
            Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_SUCCESS]])))
            FIFO.Erase(Feedback_Log)
            break
        
    Classifier1 = (Movement_Range_Max-Movement_Range_Min)/(np.array(Feature1).max()-np.array(Feature1).min())
    Classifier2 = (Movement_Range_Max-Movement_Range_Min)/(np.array(Feature2).max()-np.array(Feature2).min())

    FIFO.Rewrite(Trigger_Log,"Trial End")
    print 'Sent "Trial End"'
    sleep(1)
    Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_END]])))
    
FIFO.Rewrite(Trigger_Log,"ALL FINISH")
print 'Sent "ALL FINISH"'

# Closing the ports and the serial port for BCI Board
# Saving the data
Generator.stop_streaming()
sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
Generator.join()
