#!/usr/bin/env python2.7
import argparse
import os
import shutil
import subprocess
import sys
import numpy as np
import tarfile

'''
    This code will allow for compression and decompression of labs. This will make archiving runs much easier.
    Currently, the run archived will contain the measurement set with uncorrected data,
    he h5parms for the corrected data and models. These are tarred, so they can be compressed using
    pigz afterwards.
'''

def close_run(rname, ms):
    assert rname[-1] == '/'
    assert ms[-1] == '/'
    try:
        os.mkdir('{}instruments'.format(rname))
    except OSError:
        pass
    try:
        os.mkdir('{}/lastrun'.format(rname))
    except OSError:
        pass
    dirlist = os.listdir('measurements/{}'.format(ms))
    instruments = list(filter(lambda x: 'instrument' in x, dirlist))
    for inst in instruments:
        shutil.copy2('measurements/{0}{1}'.format(ms,inst), '{0}instruments/{1}'.format(rname,inst))
    shutil.copytree('models/', '{}models'.format(rname))
    # Copy the measurement set compressed. You can re-gain the correction
    # by applying the applycal step again
    callstring = 'DPPP msin=measurements/{0} msout={1}{0} msout.storagemanager=dysco msout.datacolumn=DATA msin.datacolumn=DATA steps=[]'.format(ms, rname)
    subprocess.call(callstring, shell = True)
    dirlist = os.listdir(rname)
    callist = list(filter(lambda x: 'cal' in x, dirlist))
    for cal in callist:
        try:
            shutil.copyfile('{0}{1}/ws-MFS-model.fits'.format(rname,cal), '{0}models/{1}-model.fits'.format(rname, cal))
        except IOError:
            print('Missing: {0}{1}/ws-MFS-model.fits'.format(rname,cal))
    print('\n+-----------------------------------------+\n')
    print('| Compression complete                    |\n')
    print('| Please fill the lastrun folder manually |\n')
    print('| After that, use tar+pigz -1             |\n')
    print('+-----------------------------------------+')


def uncompress_diag(rname):
    assert rname[-1] == '/'
    dirlist = os.listdir(rname)
    ms_name = list(filter(lambda x: '.ms' in x, dirlist))[0] # probably the worst way to find a ms
    model_full = list(filter(lambda x: '-model.fits' in x, os.listdir('{}lastrun/'.format(rname))))[0] # find the model in an equally shitty way
    model = model_full.rstrip('-model.fits')
    callstring = 'wsclean -predict -name {2}lastrun/{0} {2}{1}'.format(model,ms_name, rname)
    subprocess.call(callstring, shell = True)
    instrumentlist = list(filter(lambda x: 'instrument' in x, os.listdir('{}lastrun'.format(rname))))
    if len(instrumentlist) > 1:
        h5_p = list(filter(lambda x: 'instrument_p' in x, instrumentlist))[0]
        h5_a = list(filter(lambda x: 'instrument_a' in x, instrumentlist))[0]
        phasestring = 'DPPP msin={2}{0} msout=. steps=[applycal] msout.datacolumn=CORRECTED_PHASE msout.storagemanager=dysco applycal.parmdb={2}lastrun/{1} applycal.correction=phase000'.format(ms_name, h5_p, rname)
        ampstring = 'DPPP msin={2}{0} msout=. steps=[applycal1,applycal2] msin.datacolumn=CORRECTED_PHASE msout.datacolumn=CORRECTED_DATA2 msout.storagemanager=dysco applycal1.parmdb={2}lastrun/{1} applycal1.correction=phase000 applycal2.parmdb={2}lastrun/{1} applycal2.correction=amplitude000'.format(ms_name, h5_a,rname)
        subprocess.call(phasestring, shell = True)
        subprocess.call(ampstring, shell = True)
    else:
        print('not implemented')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', help = 'location of the run')
    parser.add_argument('-ms', help = 'which measurement set to use', default = '.')
    parser.add_argument('-d', action = 'store_true', help = 'Decompresses set')
    parsed = parser.parse_args()

    if parsed.d:
        uncompress_diag(parsed.r)
    else:
        close_run(parsed.r, parsed.ms)