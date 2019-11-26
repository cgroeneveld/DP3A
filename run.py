from __future__ import print_function
import numpy as np
import sys
import os
import argparse
import subprocess
import journal_pickling as jp
import diag_cal as dc
import phase_cal as pc

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='An automation script')
    parser.add_argument('-Np', type = int, help = "Amount of self calibration cycles it needs to perform", required = True)
    parser.add_argument('-Na', type = int, help = "Amount of self calibration (amplitude) cycles it needs to perform", default = 0)
    parser.add_argument('-p', type = str, help = "Path to where we can write the images and solution plots", default = './RESULTS/')
    parser.add_argument('-ms', type = str, help = "Location of measurement set", required = True)
    parser.add_argument('-ip', type = int, help = "Label of first self calibration", default = 0)
    parser.add_argument('-ia', type = int, help = "Label of first amp self calibration", default = 1)

    parsed = parser.parse_args()

    locker = jp.Locker(parsed.p+'/log')

    # TODO: FORMAT IT TO WORK WITH THE CLASSES:w

    if parsed.Np != 0:
        for n in range(parsed.ip, parsed.Np):
            imaging = base_image.rstrip('\n') + ' -data-column CORRECTED_DATA'
            run_phase(ddecal, acal, imaging, n, parsed.f, parsed.p,locker)
    
    if parsed.Na != 0:
        for n in range(parsed.ia, parsed.Na):
            imaging = base_image.rstrip('\n') + ' -data-column CORRECTED_DATA2'
            run_amp(ddecal, acal, ddeamp, aamp, imaging, n, parsed.f, parsed.p, locker)

    locker.save()
