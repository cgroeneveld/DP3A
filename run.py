from __future__ import print_function
import numpy as np
import sys
import os
import argparse
import subprocess


def init_directories(fpath, N):
    try:
        os.mkdir(fpath+'/init')
    except:
        pass
    for n in range(N):
	try:
	    os.mkdir(fpath+'/pcal{0}'.format(n+1))
	except:
	    pass
"""
    Yes, I know I am using shell=True. Please don't do anything bad.
"""


def parse_pset(fname):
    with open(fname, 'r') as handle:
        data = [line for line in handle]
    # Just some formatting
    data = [x.rstrip('\n') for x in data]
    data = list(filter(lambda x: x != '', data))
    # Raise an error if we manually define the h5parm
    newdata = []
    for x in data:
        if 'h5parm' in x:
            raise ValueError('Please do not define your own h5parm. We will do that for you.')
        elif 'msin = ' in x:
            raise ValueError('Please do not define msin - we do that ourselves')
        else:
            newdata.append(''.join(list(filter(lambda y: y != ' ', x))))
    return newdata

def run_losoto(fpath, ms, n):
    # Losoto is always a problem because it demands a parset.
    # Well, then we give it a parset.
    with open('lst.pset', 'r') as handle:
        data = [line for line in handle]
    if n == 0:
        data[-1] = 'prefix = {0}/init/'.format(fpath)
    else:
        data[-1] = 'prefix = {0}/pcal{1}/'.format(fpath,n)
    os.remove('lst.pset')
    with open('lst.pset', 'w') as handle:
        for line in data:
            handle.write(line)
    if n ==0:
        subprocess.call('losoto {0}/instrument.h5 lst.pset'.format(ms), shell = True)
    else:
        subprocess.call('losoto {0}/instrument_{1}.h5 lst.pset'.format(ms,n), shell=True)



def run_iter(ddecal, acal, imaging, n, ms, fpath):
    if n == 0:
        # First iteration
        ddecal.append('ddecal.h5parm={0}/instrument.h5'.format(ms))
        acal.append('applycal.parmdb={0}/instrument.h5'.format(ms))
        ddecal.append('msin={0}'.format(ms))
        acal.append('msin={0}'.format(ms))
        imname = 'init'
    else:
        ddecal.append('ddecal.h5parm={0}/instrument_{1}.h5'.format(ms, n))
        acal.append('applycal.parmdb={0}/instrument_{1}.h5'.format(ms, n))
        ddecal.append('msin={0}'.format(ms))
        acal.append('msin={0}'.format(ms))
        imname = 'pcal{0}'.format(n)
    
    fulimg = '{0} -name {1}/{2}/ws {3}'.format(imaging, fpath, imname, ms)

    subprocess.call('DPPP {}'.format(' '.join(ddecal)), shell=True)
    subprocess.call('DPPP {}'.format(' '.join(acal)), shell=True)
    subprocess.call(fulimg, shell=True)
    run_losoto(fpath, ms, n)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='An automation script')
    parser.add_argument('-N', type = int, help = "Amount of self calibration cycles it needs to perform", required = True)
    parser.add_argument('-p', type = str, help = "Path to where we can write the images and solution plots", default = './RESULTS/')
    parser.add_argument('-f', type = str, help = "Location of measurement set", required = True)

    parsed = parser.parse_args()

    init_directories(parsed.p, parsed.N)

    ddecal = parse_pset('ddecal_init.pset')
    acal = parse_pset('acal_init.pset')
    with open('imaging.sh') as handle:
        line = handle.read()
    imaging = line.rstrip('\n') + ' -data-column CORRECTED_DATA'

    for n in range(parsed.N):
        run_iter(ddecal, acal, imaging, n, parsed.f, parsed.p)
