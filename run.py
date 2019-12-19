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
import reduction_steps.tec_cal as tc
import reduction_steps.phase_up as pu
import datetime
import quality_check as qc

parser = argparse.ArgumentParser(description='An automation script')
parser.add_argument('-p', type = str, help = "Path to where we can write the images and solution plots", default = './RESULTS/')
parser.add_argument('-ms', type = str, help = "Location of measurement set", required = True)
parser.add_argument('-s', type = str, help = "String representing the reduction steps. Use h for more help", required = True)
parser.add_argument('-d', action = 'store_true', help = 'Enables debug mode')
parser.add_argument('-y', action = 'store_true', help = 'Automatically accept phase-up warning')
parser.add_argument('-m', type = str, help = "Path to the location of a model FITS file, used whenever we need to predict the model", default = None)

parsed = parser.parse_args()

if parsed.s == 'h':
    print('''
        The following reduction steps have (so far) been implemented:
        p  |   Phase only calibration
        d  |   Diagonal calibration, meaning one phase and one diagonal calibration
        t  |   TEC calibration for the ionosphere, basically a constraint on the
           |   phase-only calibration
        u  |   Phase-up: mash all short baselines together to one single base station
           |   Requires a model.
        _____________________________________________________________________________

        These have not yet been implemented:
        r  |   Correction for rotation measure. Important for low frequencies
        m  |   Predict using a new model - requires a model
    ''')

redsteps = list(parsed.s)
uni_redsteps = np.unique(redsteps)
nlist = np.zeros(len(redsteps))
for chara in uni_redsteps: 
    mask = chara == np.asarray(redsteps)
    nlist[mask] = np.arange(1, int(1+sum(mask)))

if 'u' in redsteps and not parsed.y:
    print("This reduction strings contains a phase-up. Phase-ups are destructive - so please make sure that you have backed your system up. Type 'ok' to continue: ")
    ans = raw_input()
    if ans != 'ok':
        sys.exit()

if 'u' in redsteps or 'm' in redsteps:
    assert parsed.m != None

for red, n in zip(redsteps, nlist):
    n = int(n)
    if red == 'p':
        cal = pc.PhaseCalibrator(n, parsed.ms, parsed.p, './parsets/')
    elif red == 'd':
        cal = dc.DiagonalCalibrator(n, parsed.ms, parsed.p, './parsets/')
    elif red == 't':
        cal = tc.TecCalibrator(n, parsed.ms, parsed.p, './parsets/')
    elif red == 'u':
        cal = pu.PhaseUp(n, parsed.ms, parsed.p, './parsets/', parsed.m)
    else:
        print("Reduction step {} not implemented".format(red))
    if parsed.d:
        cal.DEBUG = True
    cal.initialize()
    cal.execute()

qc.main(parsed.p, redsteps, nlist)

log = jp.Locker(parsed.p + 'log')
log['ms'] = parsed.ms
log['last_edit'] = datetime.datetime.now().strftime("%Y_%m_%d_%H_$M")
log.save()
