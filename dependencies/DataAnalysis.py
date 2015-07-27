import numpy as np
from scipy.fftpack import fft

# Feature Extraction
def PowerExtraction(data,SamplingFrequency,FrequencyRange):
    Power = abs(fft(data))
    Frequency = np.fft.fftfreq(data.shape[0],1.0/SamplingFrequency)
    Frequency_Band = np.logical_and(Frequency > FrequencyRange[0],Frequency < FrequencyRange[1])
    Average_Power_Extracted = np.mean(Power[Frequency_Band])
    return Average_Power_Extracted

def Linear_Regression(Power,Movement):
    Slope = (Movement[1]-Movement[0])/(Power[1]-Power[0])
    Offset = Movement[0] - Power[0]*Slope
    return (Slope,Offset)

# Signal Processing
def Common_Average_Reference(data):
    Filtered_Data = data-np.tile(np.mean(data,axis=1),(data.shape[1],1)).T
    return Filtered_Data
