import sys; sys.path.append('../dependencies')
import Open_BCI_Thread as bci
import Generic_Generator as gen
import Queue
import pyautogui as gui
import threading
import subprocess
from scipy.fftpack import fft
import DataAnalysis as Process
from time import sleep, time, gmtime, strftime
import numpy as np

def Start_Chrome(screenWidth,screenHeight):
    gui.click(x=screenWidth/2, y=screenHeight/30, clicks=3)
    gui.typewrite('www.google.com\n',interval=0.05)
    sleep(2)
    gui.click(x=screenWidth*0.4, y=screenHeight*0.38)
    
port = '/dev/OpenBCI'
print '--------------------------------------------\n'
print '------- Start System... GUI Starting -------\n'
print '--------------------------------------------\n'

# Setup Queue for data
Data_Queue = Queue.Queue()

# Initialize the OpenBCI and start streaming
FS = 250
Frequency_Range = [8,12]
Feature1 = list()
Feature2 = list()
Generator = gen.Generic_Generator(Queue=Data_Queue,binSize=125)
Generator.start()
#Board = bci.OpenBCIBoard_Recording(thread=True,port=port,baud=115200,Queue=Data_Queue,binSize=125)
#Board.start()

screenWidth,screenHeight = gui.size()
gui.FAILSAFE = False
MovementRange_X = [-5.0*(screenWidth/100.0),5.0*(screenWidth/100.0)]
MovementRange_Y = [-5.0*(screenHeight/100.0),5.0*(screenHeight/100.0)]

while True:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        Sample[:,range(1,9)] = Process.Common_Average_Reference(Sample[:,range(1,9)])
        Feature1.append(Process.PowerExtraction(Sample[:,4],FS,Frequency_Range))
        Feature2.append(Process.PowerExtraction(Sample[:,7],FS,Frequency_Range))
        Classifier_X, Offset_X = Process.Linear_Regression(Feature1,MovementRange_X)
        Classifier_Y, Offset_Y = Process.Linear_Regression(Feature2,MovementRange_Y)
        if not Classifier_X == np.inf and not Classifier_Y == np.inf:
            break 

while len(Feature1)<70:
    if not Data_Queue.empty():
        Sample = Data_Queue.get()
        Sample[:,range(1,9)] = Process.Common_Average_Reference(Sample[:,range(1,9)])
        Feature1.append(Process.PowerExtraction(Sample[:,4],FS,Frequency_Range))
        Feature2.append(Process.PowerExtraction(Sample[:,7],FS,Frequency_Range))
        Distance_X = Feature1[len(Feature1)-1]*Classifier_X + Offset_X
        Distance_Y = Feature2[len(Feature2)-1]*Classifier_Y + Offset_Y
        print 'X: ' + str(Distance_X) + ', Y: ' + str(Distance_Y)

        # Movement
        gui.moveRel(Distance_X,Distance_Y,duration = 0.3, pause = 0.1)
        Classifier_X, Offset_X = Process.Linear_Regression(Feature1,MovementRange_X)
        Classifier_Y, Offset_Y = Process.Linear_Regression(Feature2,MovementRange_Y)

        
# Closing the ports and the serial port for BCI Board
#Board.stop_streaming()
#Board.join()
Generator.stop_streaming()
Generator.join()
