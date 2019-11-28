#!/usr/bin/env python2.7
from __future__ import print_function
import numpy as np
import sys
import os
import argparse
import subprocess
import journal_pickling as jp
import reduction_steps.diag_cal as dc
import reduction_steps.phase_cal as pc
import quality_check as qc

parser = argparse.ArgumentParser(description='An automation script')
parser.add_argument('-Np', type = int, help = "Amount of self calibration cycles it needs to perform", default = 0)
parser.add_argument('-Nd', type = int, help = "Amount of self calibration (amplitude) cycles it needs to perform", default = 0)
parser.add_argument('-p', type = str, help = "Path to where we can write the images and solution plots", default = './RESULTS/')
parser.add_argument('-ms', type = str, help = "Location of measurement set", required = True)
parser.add_argument('-ip', type = int, help = "Label of first self calibration", default = 0)
parser.add_argument('-id', type = int, help = "Label of first diagonal self calibration", default = 1)

parsed = parser.parse_args()

for i in range(parsed.ip, parsed.ip + parsed.Np):
    phasecal = pc.PhaseCalibrator(i, parsed.ms,parsed.p, './')
    phasecal.initialize()
    phasecal.execute()

for i in range(parsed.id, parsed.id + parsed.Nd):
    diagcal = dc.DiagonalCalibrator(i, parsed.ms, parsed.p, './')
    diagcal.initialize()
    diagcal.execute()

qc.main(parsed.p)
