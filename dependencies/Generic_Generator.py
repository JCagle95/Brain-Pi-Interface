import threading
import time
import numpy as np
import random

class Generic_Generator(threading.Thread):
    def __init__(self,Queue=None,binSize=50,Animation=False,Data=None):
        threading.Thread.__init__(self)
        self.Queue = Queue
        self.binSize = binSize
        self.streaming = False
        self.start_time = time.time()
        self.Animation = Animation
        self.Display_Block = 1250
        if not Data == None:
            self.Data = Data
            self.File = True
            
    def run(self):
        self.streaming = True
        Random_Results = np.tile(np.arange(self.binSize,dtype=np.float32),(9,1)).T

        if self.File:
            x = 1
            while self.streaming:
                self.Queue.put(self.Data[range((x-1)*50,x*50)])
                x += 1
                time.sleep(0.2)
                
        elif self.Animation:
            Display = np.tile(np.arange(self.Display_Block,dtype=np.float32),(9,1)).T
            while self.streaming:
                for n in range(self.binSize):
                    Random_Results[n,0] = time.time()-self.start_time
                    Random_Results[n,range(1,9)] = np.array([random.random() for _ in xrange(8)])*100
                Display = np.append(Display,Random_Results,axis=0)
                self.Queue.put(Display[range(len(Display)-1250,len(Display)),:])
                time.sleep(0.2)
                
        else:
            while self.streaming:
                for n in range(self.binSize):
                    Random_Results[n,0] = time.time()-self.start_time
                    Random_Results[n,range(1,9)] = np.array([random.random() for _ in xrange(8)])*100
                self.Queue.put(Random_Results)
                time.sleep(0.2)

    def stop_streaming(self):
        self.streaming = False
                
