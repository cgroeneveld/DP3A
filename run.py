from __future__ import print_function
import numpy as np
import sys
import os
import argparse
import subprocess
import journal_pickling as jp

def writetofile(x, shell):
    with open('kittens.fl' , 'a') as handle:
        handle.write(x+'\n')

# subprocess.call = lambda x,shell: writetofile(x,shell)

def pickle_and_call(x,locker):
    locker.add_calls(x)
    subprocess.call(x, shell = True)

def init_directories(fpath, Np, Na):
    try:
        os.mkdir(fpath+'/init')
    except:
        pass
    for n in range(Np):
        try:
            os.mkdir(fpath+'/pcal{0}'.format(n))
        except:
            pass
    for n in range(Na):
        try:
            os.mkdir(fpath+'/apcal{0}'.format(n))
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
        elif 'msout.datacolumn' in x:
            raise ValueError('Please do not define msout.datacolumn - we do that ourselves')
        else:
            newdata.append(''.join(list(filter(lambda y: y != ' ', x))))
    return newdata

def parse_losoto_pset(fpath, n, type_ = 'p'):
    if type_ == 'p':
        with open('lstp.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove('lstp.pset')
        if n == 0:
            data[-1] = 'prefix = {0}/init/'.format(fpath)
        else:
            data[-1] = 'prefix = {0}/pcal{1}/'.format(fpath,n)
        with open('lstp.pset', 'w') as handle:
            for line in data:
                handle.write(line)
    elif type_ == 'ap':
        with open('lsta.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove('lsta.pset')
        data[-1] = 'prefix = {0}/apcal{1}/amp_'.format(fpath,n)
        with open('lsta.pset', 'w') as handle:
            for line in data:
                handle.write(line)

def run_losoto(fpath, ms, n, log, type_ = 'p'):
    if type_ == 'p':
        parse_losoto_pset(fpath, n, 'p')
        if n == 0:
            pickle_and_call('losoto {0}/instrument.h5 lstp.pset'.format(ms), log)
        else:
            pickle_and_call('losoto {0}/instrument_{1}.h5 lstp.pset'.format(ms, n), log)
    elif type_ == 'ap':
        parse_losoto_pset(fpath, n, 'p')
        parse_losoto_pset(fpath, n, 'ap')
        pickle_and_call('losoto {0}/instrument_p{1}.h5 lstp.pset'.format(ms, n), log)
        pickle_and_call('losoto {0}/instrument_a{1}.h5 lsta.pset'.format(ms, n), log)
    


def run_phase(ddecal, acal, imaging, n, ms, fpath,log):
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

    ddecal.append('msout.datacolumn=CORRECTED_DATA')    
    acal.append('msout.datacolumn=CORRECTED_DATA')
    fulimg = '{0} -name {1}/{2}/ws {3}'.format(imaging, fpath, imname, ms)

    pickle_and_call('DPPP {}'.format(' '.join(ddecal)), log)
    pickle_and_call('DPPP {}'.format(' '.join(acal)), log)
    pickle_and_call(fulimg, log)

    run_losoto(fpath, ms, n, log, type_ = 'p')

def run_amp(ddecal, acal, ddeamp, aamp, imaging, n, ms, fpath, log):
    ddecal.append('ddecal.h5parm={0}/instrument_p{1}.h5'.format(ms, n))
    acal.append('applycal.parmdb={0}/instrument_p{1}.h5'.format(ms, n))
    ddecal.append('msin={0}'.format(ms))
    acal.append('msin={0}'.format(ms))
    ddecal.append('msout.datacolumn=CORRECTED_PHASE')
    acal.append('msout.datacolumn=CORRECTED_PHASE')

    ddeamp.append('msin={0}'.format(ms))
    ddeamp.append('ddecal.h5parm={0}/instrument_a{1}.h5'.format(ms, n))
    ddeamp.append('msin.datacolumn=CORRECTED_PHASE')
    ddeamp.append('msout.datacolumn=CORRECTED_DATA2')

    aamp.append('applycal.parmdb={0}/instrument_a{1}.h5'.format(ms, n))
    aamp.append('msin={0}'.format(ms))
    aamp.append('msin.datacolumn=CORRECTED_PHASE')
    aamp.append('msout.datacolumn=CORRECTED_DATA2')

    imname = 'apcal{0}'.format(n)
    fulimg = '{0} -name {1}/{2}/ws {3}'.format(imaging, fpath, imname, ms)

    pickle_and_call('DPPP {}'.format(' '.join(ddecal)), log)
    pickle_and_call('DPPP {}'.format(' '.join(acal)), log)
    pickle_and_call('DPPP {}'.format(' '.join(ddeamp)), log)
    pickle_and_call('DPPP {}'.format(' '.join(aamp)), log)
    pickle_and_call(fulimg, log)

    run_losoto(fpath,ms,n, log, type_ = 'ap')

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='An automation script')
    parser.add_argument('-Np', type = int, help = "Amount of self calibration cycles it needs to perform", required = True)
    parser.add_argument('-Na', type = int, help = "Amount of self calibration (amplitude) cycles it needs to perform", default = 0)
    parser.add_argument('-p', type = str, help = "Path to where we can write the images and solution plots", default = './RESULTS/')
    parser.add_argument('-f', type = str, help = "Location of measurement set", required = True)
    parser.add_argument('-ip', type = int, help = "Label of first self calibration", default = 0)
    parser.add_argument('-ia', type = int, help = "Label of first amp self calibration", default = 0)

    parsed = parser.parse_args()

    locker = jp.Locker(parsed.p+'/log')

    init_directories(parsed.p, parsed.Np, parsed.Na)

    ddecal = parse_pset('ddecal_init.pset')
    acal = parse_pset('acal_init.pset')
    ddeamp = parse_pset('ddecal_ampself.pset')
    aamp = parse_pset('acal_ampself.pset')
    with open('imaging.sh') as handle:
        base_image = handle.read()

    if parsed.Np != 0:
        for n in range(parsed.ip, parsed.Np):
            imaging = base_image.rstrip('\n') + ' -data-column CORRECTED_DATA'
            run_phase(ddecal, acal, imaging, n, parsed.f, parsed.p,locker)
    
    if parsed.Na != 0:
        for n in range(parsed.ia, parsed.Na):
            imaging = base_image.rstrip('\n') + ' -data-column CORRECTED_DATA2'
            run_amp(ddecal, acal, ddeamp, aamp, imaging, n, parsed.f, parsed.p, locker)

    locker.save()
