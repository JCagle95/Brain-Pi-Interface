# Brain-Pi-Interface
The project for EEG-Based Brain Computer Interface implemented on Raspberry Pi 2. Applied to University of Florida Biomedical Engineering Department Honor Graduation Project for undergraduate. 

## Major Development Theory
1. Python (Signal Acquisition, Signal Processing, Feature Selection, Feature Conditioning)
2. Threading (Parallel Process of Signal Acquisition and Signal Procsessing)
3. File in File out method (Shareing Trigger information and features between Python and C++)
4. C++ with Simple Directmedia Layer 2 (Visual Feedback)

### Copyright Disclaimer:
**OpenBCI**: Library for OpenBCI is directly fetched from OpenBCI Repo and modified from *open_bci_v3.py*. 
https://github.com/OpenBCI/OpenBCI_Python

*Note*: The only modification is converting OpenBCI class into thread object and the run function for thread.

**SDL Headers**: Various headers (res_path.h and renderingFunctions.h) used for SDL2 visual display are obtained from SDL2 Tutorial found here:
https://github.com/Twinklebear/TwinklebearDev-Lessons
