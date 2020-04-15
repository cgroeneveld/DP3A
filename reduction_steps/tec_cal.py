from __future__ import print_function
import numpy as np
import sys
import os
import subprocess
import journal_pickling as jp
from .tools import parse_pset

class TecCalibrator(object):
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
    
    def initialize(self):
        self._init_parsets()
        self._init_dir()
        self._init_img()
        self.initialized = True

    def _init_dir(self):
        os.mkdir('{0}teccal{1}'.format(self.fpath,self.n))

    def _init_losoto(self):
        '''
            This needs to be ran right before calling it.
            It changes the losoto parset and can conflict if not ran
            immediately afterwards.
        '''
        with open(self.pset_loc + 'lsta.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove(self.pset_loc + 'lsta.pset')
        data[-1] = 'prefix = {0}teccal{1}/'.format(self.fpath, self.n)
        self.losoto = 'losoto {0}instrument_t{1}.h5 {2}lsta.pset'.format(self.ms, self.n, self.pset_loc)
        with open(self.pset_loc + 'lsta.pset', 'w') as handle:
            for line in data:
                handle.write(line)
    
    def _init_parsets(self):
        ddecal = parse_pset(self.pset_loc + 'ddecal_teconly.pset')
        acal = parse_pset(self.pset_loc + 'acal_teconly.pset')
        ddecal.append('msin={}'.format(self.ms))
        acal.append('msin={}'.format(self.ms))
        acal.append('msout.datacolumn=CORRECTED_DATA')

        ddecal.append('ddecal.h5parm={0}instrument_t{1}.h5'.format(self.ms,self.n))
        acal.append('applycal.parmdb={0}instrument_t{1}.h5'.format(self.ms,self.n))
        self.ddecal = ' '.join(ddecal)
        self.acal = ' '.join(acal)

    def _init_img(self):
        with open(self.pset_loc+'imaging.sh') as handle:
            base_image = handle.read()[:-2]
        imname = 'teccal{}'.format(self.n)
        if os.path.isfile('{}casamask.fits'.format(self.pset_loc)):
            self.fulimg = '{0} -data-column CORRECTED_DATA -fits-mask {4}casamask.fits -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms, self.pset_loc)
        else:
            self.fulimg = '{0} -data-column CORRECTED_DATA -auto-mask 5 -auto-threshold 1.5 -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms)
    
    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

    def calibrate(self):
        self._init_parsets()
        self.pickle_and_call('DPPP {}'.format(self.ddecal))
        self.pickle_and_call('DPPP {}'.format(self.acal))
    
    def prep_img(self):
        self._init_dir()
        self.ms = ''
        self._init_img()
        return self.fulimg
   
    def _printrun(self):
        '''
            Basically prints all commands, without running it
        '''
        with open('kittens.fl', 'a') as handle:
            handle.write('DPPP {}\n'.format(self.ddecal))
            handle.write('DPPP {}\n'.format(self.acal))
            handle.write(self.fulimg+'\n')
            self._init_losoto()
            handle.write(self.losoto+'\n')

    def _actualrun(self):
        self.pickle_and_call('DPPP {}'.format(self.ddecal))
        self.pickle_and_call('DPPP {}'.format(self.acal))
        self.pickle_and_call(self.fulimg)
        self._init_losoto()
        self.pickle_and_call(self.losoto)


    def execute(self):
        if self.DEBUG:
            self._printrun()
        else:
            self._actualrun()
    
