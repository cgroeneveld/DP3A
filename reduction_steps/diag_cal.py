from __future__ import print_function
import numpy as np
import sys
import os
import subprocess
import journal_pickling as jp
from .tools import parse_pset

class DiagonalCalibrator(object):
    def __init__(self, n, ms, fpath, pset_loc = './'):
        self.n = n
        self.ms = ms
        self.fpath = fpath
        self.initialized = False
        self.pset_loc = pset_loc
        self.log = jp.Locker(fpath+'log')
        self.DEBUG = False
        assert fpath[-1] == '/'
        assert ms[-1] == '/'
        assert pset_loc[-1] == '/'
        assert n > 0
    
    def initialize(self):
        self._init_parsets()
        self._init_dir()
        self._init_img()
        self.initialized = True

    def _init_dir(self):
        try:
            os.mkdir('{0}apcal{1}'.format(self.fpath,self.n))
        except OSError:
            pass

    def _init_losoto(self):
        '''
            This needs to be ran right before calling it.
            It changes the losoto parset and can conflict if not ran
            immediately afterwards.
        '''
        with open(self.pset_loc + 'lstp.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove(self.pset_loc + 'lstp.pset')
        data[-1] = 'prefix = {0}apcal{1}/prephase'.format(self.fpath, self.n)
        self.losoto_p = 'losoto {0}instrument_p{1}.h5 {2}lstp.pset'.format(self.ms, self.n, self.pset_loc)
        with open(self.pset_loc + 'lstp.pset', 'w') as handle:
            for line in data:
                handle.write(line)

        with open(self.pset_loc + 'lsta.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove(self.pset_loc + 'lsta.pset')
        data[-1] = 'prefix = {0}apcal{1}/amp'.format(self.fpath,self.n)
        self.losoto_a = 'losoto {0}instrument_a{1}.h5 {2}lsta.pset'.format(self.ms, self.n,self.pset_loc)
        with open(self.pset_loc + 'lsta.pset', 'w') as handle:
            for line in data:
                handle.write(line)

        with open(self.pset_loc + 'lsslow.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove(self.pset_loc + 'lsslow.pset')
        data[-1] = 'prefix = {0}apcal{1}/slowphase'.format(self.fpath, self.n)
        self.losoto_slow = 'losoto {0}instrument_a{1}.h5 {2}lsslow.pset'.format(self.ms, self.n, self.pset_loc)
        with open(self.pset_loc + 'lsslow.pset', 'w') as handle:
            for line in data:
                handle.write(line)

    def _init_parsets(self):
        ddecal = parse_pset(self.pset_loc + 'ddecal_init.pset')
        acal = parse_pset(self.pset_loc + 'acal_init.pset')
        ddecal.append('msin={}'.format(self.ms))
        acal.append('msin={}'.format(self.ms))
        ddecal.append('ddecal.h5parm={0}instrument_p{1}.h5'.format(self.ms,self.n))
        acal.append('applycal.parmdb={0}instrument_p{1}.h5'.format(self.ms,self.n))
        ddecal.append('msout.datacolumn=CORRECTED_PHASE')
        acal.append('msout.datacolumn=CORRECTED_PHASE')
        self.ddephase = ' '.join(ddecal)
        self.aphase = ' '.join(acal)

        ddeamp = parse_pset(self.pset_loc + 'ddecal_ampself.pset')
        aamp = parse_pset(self.pset_loc + 'acal_ampself.pset')
        ddeamp.append('msin={}'.format(self.ms))
        aamp.append('msin={}'.format(self.ms))
        ddeamp.append('ddecal.h5parm={0}instrument_a{1}.h5'.format(self.ms, self.n))
        aamp.append('applycal.parmdb={0}instrument_a{1}.h5'.format(self.ms, self.n))
        ddeamp.append('msin.datacolumn=CORRECTED_PHASE')
        aamp.append('msin.datacolumn=CORRECTED_PHASE')
        aamp.append('msout.datacolumn=CORRECTED_DATA2')
        self.ddeamp = ' '.join(ddeamp)
        self.aamp = ' '.join(aamp)

    def _init_img(self):
        with open(self.pset_loc+'imaging.sh') as handle:
            base_image = handle.read()[:-2]
        if self.n == 0:
            imname = 'init'
        else:
            imname = 'apcal{}'.format(self.n)
        if os.path.isfile('{}casamask.fits'.format(self.pset_loc)):
            self.fulimg = '{0} -data-column CORRECTED_DATA2 -fits-mask {4}casamask.fits -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms, self.pset_loc)
        else:
            self.fulimg = '{0} -data-column CORRECTED_DATA2 -auto-mask 5 -auto-threshold 1.5 -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms)
    
    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

    def _printrun(self):
        '''
            Basically prints all commands, without running it
        '''
        with open('kittens.fl', 'a') as handle:
            handle.write('DPPP {}\n'.format(self.ddephase))
            handle.write('DPPP {}\n'.format(self.aphase))
            handle.write('DPPP {}\n'.format(self.ddeamp))
            handle.write('DPPP {}\n'.format(self.aamp))
            handle.write(self.fulimg+'\n')
            self._init_losoto()
            handle.write(self.losoto_p+'\n')
            handle.write(self.losoto_a)

    def _actualrun(self):
        self.pickle_and_call('DPPP {}'.format(self.ddephase))
        self.pickle_and_call('DPPP {}'.format(self.aphase))
        self.pickle_and_call('DPPP {}'.format(self.ddeamp))
        self.pickle_and_call('DPPP {}'.format(self.aamp))
        self.pickle_and_call(self.fulimg)
        self._init_losoto()
        self.pickle_and_call(self.losoto_p)
        self.pickle_and_call(self.losoto_a)
        self.pickle_and_call(self.losoto_slow)


    def execute(self):
        if self.DEBUG:
            self._printrun()
        else:
            self._actualrun()
    
