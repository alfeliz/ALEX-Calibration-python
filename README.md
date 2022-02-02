# ALEX-Calibration-python

Python calibration script for the ALEX exploding wire system.

This python script calibrates the ALEX Rogowski coil, the RC integrator and the lumped elements R and C of tha ALEX exploding wire from short circuit data stroed in the actual *elec* format: with a folder named __shot_name_RAW__ within, with the raw data and some file in the shot folder. One of them, the HTML shot info and the others, scopes fotographs.


## Usage

First, there must exist a folder with all the shot to be used inside. Then, just run the script from the upper folder and the exit, PNG images with the fitted shor circuit data and a TXT with parameters and erros calculated will be saved in the folder with the shots.
