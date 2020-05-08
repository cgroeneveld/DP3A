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
import reduction_steps.predict as pr
import reduction_steps.tecphase as tp
import datetime
import quality_check as qc
import multiprocessing as mp

class FakeParser(object):
    def __init__(self, ms, p, s, d, y, m, multi):
        self.ms = ms
        self.p = p
        self.s = s
        self.d = d
        self.y = y
        self.m = m
        self.multims = multi

def executeCalibration(cal):
    cal.calibrate()

def executePredict(cal):
    cal.initialize()
    cal.execute()

def main(parsed, cwd):
    os.environ['OMP_NUM_THREADS']= '1'
    if parsed.s == 'h':
        print('''
            The following reduction steps have (so far) been implemented:
            p  |   Phase only calibration
            d  |   Diagonal calibration, meaning one phase and one diagonal calibration
            t  |   TEC calibration for the ionosphere, basically a constraint on the
               |   phase-only calibration
            u  |   Phase-up: mash all short baselines together to one single base station
               |   Requires a model.
            m  |   Predict using a new model - requires a model
            a  |   Solve for both TEC and Phase at the same time 
            _____________________________________________________________________________
        ''')

    # Load the sequence of reductions
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

    # Load all ms
    if parsed.multims:
        mslist = [parsed.ms+ms+'/' for ms in os.listdir(parsed.ms)]
    else:
        mslist = [parsed.ms]

    pool = mp.Pool(3) # Maybe make this a function or something?
    # Perform the reductions
    # TODO: need to fix all the necessary reductions, at least 'd' and 'm'
    for red, n in zip(redsteps, nlist):
        n = int(n)
        if red == 'p':
            callist = [pc.PhaseCalibrator(n,ms,parsed.p, '{}/parsets/'.format(cwd)) for ms in mslist]
            pool.map(executeCalibration, callist)
            imgcall = callist[0].prep_img()
            imgcall += ' '.join(mslist)
            callist[0].pickle_and_call(imgcall)
        elif red == 'd':
            callist = [dc.DiagonalCalibrator(n, ms, parsed.p, '{}/parsets/'.format(cwd)) for ms in mslist]
            pool.map(executeCalibration, callist)
            imgcall = callist[0].prep_img()
            imgcall += ' '.join(mslist)
            callist[0].pickle_and_call(imgcall)
        elif red == 't':
            callist = [tc.TecCalibrator(n, ms, parsed.p, '{}/parsets/'.format(cwd)) for ms in mslist]
            pool.map(executeCalibration, callist)
            imgcall = callist[0].prep_img()
            imgcall += ' '.join(mslist)
            callist[0].pickle_and_call(imgcall)
        elif red == 'u':
            for ms in mslist:
                cal = pu.PhaseUp(n, ms, parsed.p, '{}/parsets/'.format(cwd), parsed.m)
                cal.initialize()
                cal.execute()
        elif red == 'm':
            callist = [pr.Predictor(ms, parsed.m, parsed.p, '{}/parsets/'.format(cwd)) for ms in mslist]
            pool.map(executePredict, callist)
        elif red == 'a':
            callist=[tp.TecPhaseCalibrator(n, ms, parsed.p, '{}/parsets/'.format(cwd)) for ms in mslist]
            pool.map(executeCalibration, callist)
            imgcall = callist[0].prep_img()
            imgcall += ' '.join(mslist)
            callist[0].pickle_and_call(imgcall)
        else:
            print("Reduction step {} not implemented".format(red))
        if parsed.d:
            cal.DEBUG = True
        #if not parsed.multims:
        #    cal.initialize()
        #    cal.execute()

    qc.main(parsed.p, redsteps, nlist)

    log = jp.Locker(parsed.p + 'log')
    log['ms'] = parsed.ms
    log['last_edit'] = datetime.datetime.now().strftime("%Y_%m_%d_%H_$M")
    log.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='An automation script')
    parser.add_argument('-p', type = str, help = "Path to where we can write the images and solution plots", default = './RESULTS/')
    parser.add_argument('-ms', type = str, help = "Location of measurement set", required = True)
    parser.add_argument('-s', type = str, help = "String representing the reduction steps. Use h for more help", required = True)
    parser.add_argument('-d', action = 'store_true', help = 'Enables debug mode')
    parser.add_argument('-y', action = 'store_true', help = 'Automatically accept phase-up warning')
    parser.add_argument('-m', type = str, help = "Path to the location of a model FITS file, used whenever we need to predict the model", default = None)
    parser.add_argument('-path_wd', action = 'store_true', help = argparse.SUPPRESS)
    parser.add_argument('-multims', action = 'store_true', help="Enable multiple ms to be read. This will change ms to be the root folder now.")

    parsed = parser.parse_args()
    if parsed.path_wd:
        main(parsed, parsed.p)
    else:
        main(parsed, os.getcwd())
