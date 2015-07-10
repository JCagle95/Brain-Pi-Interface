############################################################
# This is the Client End of the Raspberry Pi Network
# Client will stream OpenBCI data but will not perform any FIFO operation for C++
# Jackson Cagle, 2015
############################################################

import sys; sys.path.append('../dependencies')
import Open_BCI_Thread as bci
import Queue
import scipy.io as sio
import socket
from scipy.fftpack import fft
from time import sleep, time, gmtime, strftime
import timeit
import numpy as np
from BCI_Modules import *

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
Movement_Range_Min = -20.000
Movement_Range_Max = 20.000
Channel = 5
TRIAL_START = 254
TRIAL_END = 192
TRIAL_SUCCESS = 301
CALIBRATION_START = 14
CALIBRATION_STAGE2 = 15
CALIBRATION_END = 19
Experiment_ID = strftime("%b_%d_%Y_%H",gmtime())
ipAddress = '<Server IP Address>'
bci_port = '/dev/OpenBCI'

print '--------------\n'
print Experiment_ID + '\n'
print ipAddress + '\n'
print '--------------\n'

# Setup Client Log
Client_Log = '../resource/FIFO/Feedback_Log_1.txt'
Trigger_Log = '../resource/FIFO/Trigger_Log.txt'

# Establish the basic of server.
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ipAddress,5000))
print 'Connected\n'
Sync = Synchronize(client)

# Setup Queue for data
Data_Queue = Queue.Queue()

# Wait for the Feedback Display to start.
FIFO.Wait(Client_Log,"Timer on")

# Now signal the Server that the Client is ready. 
connection.sendall("Server Ready")
Sync.Wait("Client Ready")

# Initialize the OpenBCI and start streaming
EEG_Recording = np.arange(0.000)
Frequency = np.fft.fftfreq(50,0.004)
Frequency_Band = np.logical_and(Frequency>8,Frequency<12)
Feature = list()
Board = bci.OpenBCIBoard_Recording(port=bci_port,baud=115200,thread=True,Queue=Data_Queue,binSize=50)
EEG_Time = timeit.default_timer()
Board.start()

Trigger = np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_START]])

"""""""""""""""""""""""""""""""""""""""""""""
Resting State. Movement Range Calculation.
"""""""""""""""""""""""""""""""""""""""""""""

while len(EEG_Recording) < 250*SectionLength:
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

Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_STAGE2]])))

while len(EEG_Recording) < 250*2*SectionLength:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature,EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

Max_Movement = np.array(Feature).max()
Min_Movement = np.array(Feature).min()
Classifier = (Movement_Range_Max-Movement_Range_Min)/(Max_Movement-Min_Movement)

Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,CALIBRATION_END]])))

"""""""""""""""""""""""""""""""""""""""""""""
Trial Start. Classfication Start
"""""""""""""""""""""""""""""""""""""""""""""

for x in range(1,Max_Trials):
    # Clean up the Queue to keep Data in real time
    while not Data_Queue.empty():
        Sample = Data_Queue.get()
        Feature, EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)

    # Signal Start
    FIFO.Wait(Trigger_Log,'Trial Start')
    Start_Point = time()
    Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_START]])))

    if FIFO.Check(Client_Log,"Display End"):
        break
              
    while ((time()-Start_Point) < 5):
        # Extract Feature
        while True:
            if not Data_Queue.empty():
                Sample = Data_Queue.get()
                Feature, EEG_Recording = FeatureExtraction(Sample,Feature,EEG_Recording)
                break

        # Classification
        Feature_Direction = int(round(Classifier*Feature[len(Feature)-1]+Movement_Range_Min))

        # Data Sharing
        client.sendall(str(Feature_Direction))
        if Sync.Check('Done','End') == 2:
            Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_SUCCESS]])))
            break

    Trigger = np.concatenate((Trigger,np.array([[timeit.default_timer()-EEG_Time,TRIAL_END]])))

# Closing the ports and the serial port for BCI Board
# Saving the data
Sync.disconnect()
Board.stop_streaming()
sio.savemat(Experiment_ID + '.mat',{'EEG':EEG_Recording,'Trigger':Trigger})
Board.join()
