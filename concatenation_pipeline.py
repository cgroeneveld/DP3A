#!/usr/bin/env python2.7
import DP5 as run
import numpy as np
import os
import reduction_steps.lin2circ as lc
import argparse
import multiprocessing as mp
import subprocess

class FakeOptionParserL2C(object):
    def __init__(self, inms='', column='DATA', outcol='DATA_CIRC', poltable=False, back=False, lincol='DATA_LIN'):
        self.inms = inms
        self.column = column
        self.outcol = outcol
        self.poltable = poltable
        self.back = back
        self.lincol = lincol

# Important! check parsets beforehand - so all numthreads are 1
def average(loc, timestep, freqstep):
    call = 'DPPP msin={0} msout={0}AVG steps=[applybeam,average] average.timestep={1} average.freqstep={2}'.format(loc, timestep, freqstep)
    subprocess.call(call, shell = True)

def lin2circ(loc):
    '''
        Contains both the conversion to circular, as well as copying the 
        data columns back
    '''
    FOP = FakeOptionParserL2C(loc)
    lc.main(FOP)
    call = 'DPPP msin={0} msout={0}CIR steps=[] msin.datacolumn=DATA_CIR msout.datacolumn=DATA'.format(loc)
    subprocess.call(call, shell = True)

def phaseup_step(loc, model, num, p):
    fakeparser = run.FakeParser(loc, p+str(num), 'mu', False, True, model)
    run.main(fakeparser, os.getcwd())

def parset_reduction(combo):
    loc, timestep, freqstep, model, p, num = combo
    average(loc, timestep, freqstep)
    lin2circ('{}AVG'.format(loc))

def parset_reduction_phaseup(combo):
    loc, timestep, freqstep, model, p, num = combo
    parset_reduction(combo)
    phaseup_step('{}AVGCIR', model, num, p)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocessing pipeline - combines several measurement sets together')
    parser.add_argument('-r', type = str, help = 'Location of the root directory')
    parser.add_argument('-p', type = str, help = 'Location of destination progress folder')
    parser.add_argument('-m', type = str, help = 'Location of the model')
    parser.add_argument('-t', type = int, help = 'Timestep for averaging')
    parser.add_argument('-f', type = int, help = 'Frequency step for averaging')
    parser.add_argument('-pu', action = 'store_true', help = 'Phase-up each subband afterwards')

    parsed = parser.parse_args()
    assert parsed.r[-1] == '/'
    assert parsed.r[-1] == '/'

    dirlist = os.listdir(parsed.r)
    # Make sure that there are only numbers in this directory - not even . files!
    sorted_list = np.sort([int(fil) for fil in dirlist])
    combi_tuples = []
    for filnum in sorted_list:
        combi_tuples.append((parsed.r+str(filnum), parsed.t, parsed.f, parsed.m, parsed.p, filnum))
    
    pl = mp.Pool(mp.cpu_count())
    if parsed.pu:
        pl.map(parset_reduction_phaseup, combi_tuples)
    else:
        pl.map(parset_reduction, combi_tuples)
