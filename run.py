import numpy as np
import sys
import os
import argparse
import subprocess

def parse_pset(fname):
    with open(fname, 'r') as handle:
        data = [line for line in handle]
    # Just some formatting
    data = [x.rstrip('\n') for x in data]
    data = list(filter(lambda x: x != '', data))
    # Raise an error if we manually define the h5parm
    for x in data:
        if 'h5parm' in x:
            raise ValueError('Please do not define your own h5parm. We will do that for you.')
        elif 'msin = ' in x:
            raise ValueError('Please do not define msin - we do that ourselves')
        else
    return ' '.join(data)

def run_iter(ddecal, acal, imaging, n, ms, fpath):
    if n == 0:
        # First iteration
        ddecal.append('ddecal.h5parm = {0}/instrument.h5'.format(ms))
        acal.append('applycal.h5parm = {0}/instrument.h5'.format(ms))
        ddecal.append('msin = {0}'.format(ms))
        acal.append('msin = {0}'.format(ms))
        imname = 'init'
    else:
        ddecal.append('ddecal.h5parm = {0}/instrument_{1}.h5'.format(ms, n))
        acal.append('applycal.h5parm = {0}/instrument{1}.h5'.format(ms, n))
        ddecal.append('msin = {0}'.format(ms))
        acal.append('msin = {0}'.format(ms))
        imname = 'pcal{0}'.format(n)
    

    subprocess.call('DPPP {}'.format(' '.join(ddecal)))
    subprocess.call('DPPP {}'.format(' '.join(acal)))


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='An automation script')
    parser.add_argument('-N', type = int, help = "Amount of self calibration cycles it needs to perform", required = True)
    parser.add_argument('-p', type = str, help = "Path to where we can write the images and solution plots", default = './RESULTS/')
    parser.add_argument('-f', type = str, help = "Location of measurement set", required = True)

    print(parse_pset('ddecal_init.pset'))

