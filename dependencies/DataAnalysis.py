import numpy as np
from scipy.fftpack import fft

# Feature Extraction
def PowerExtraction(data,FrequencyRange,SamplingFrequency):
    Power = abs(fft(data))
    Frequency = np.fft.fftfreq(data.shape[0],1.0/float(SamplingFrequency))
    Frequency_Band = np.logical_and(Frequency > FrequencyRange[0],Frequency < FrequencyRange[1])
    Average_Power_Extracted = np.mean(Power[Frequency_Band])
    return Average_Power_Extracted

def AlphaDifference(data,Channel,SamplingFrequency):
    # Use Channel as Tuble (Left channels, Right channels)
    Left_Power = np.array([])
    for x in Channel[0]:
        Left_Power = np.append(Left_Power,PowerExtraction(data[x],[9,12],SamplingFrequency))
    Left_Power = np.mean(Left_Power)

    Right_Power = np.array([])
    for x in Channel[1]:
        Right_Power = np.append(Right_Power,PowerExtraction(data[x],[9,12],SamplingFrequency))
    Right_Power = np.mean(Right_Power)

    if Right_Power > Left_Power:
        Power_Difference = Right_Power - Left_Power
    else:
        Power_Difference = 0
    return Power_Difference

def Linear_Regression(Power,Movement):
    Slope = (Movement[1]-Movement[0])/(Power[1]-Power[0])
    Offset = Movement[0] - Power[0]*Slope
    return (Slope,Offset)

# Signal Processing
def Common_Average_Reference(data):
    Filtered_Data = data-np.tile(np.mean(data,axis=1),(data.shape[1],1)).T
    return Filtered_Data
