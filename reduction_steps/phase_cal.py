from __future__ import print_function
import numpy as np
import sys
import os
import subprocess
import journal_pickling as jp
from .tools import parse_pset

class PhaseCalibrator(object):
    def __init__(self, n, ms, fpath, pset_loc = './'):
        self.n = n
        self.ms = ms
        self.fpath = fpath
        self.initialized = False
        self.pset_loc = pset_loc
        self.log = jp.Locker(fpath+'log')
        self.DEBUG = False
        self.callist = []
        assert fpath[-1] == '/'
        assert ms[-1] == '/'
        assert pset_loc[-1] == '/'
    
    def initialize(self):
        self._init_parsets()
        self._init_dir()
        self._init_img()
        self.initialized = True

    def _init_dir(self):
        try:
            if self.n == 0:
                os.mkdir('{0}init'.format(self.fpath))
            else:
                os.mkdir('{0}pcal{1}'.format(self.fpath,self.n))
        except OSError:
            pass

    def _init_losoto(self):
        '''
            This needs to be ran right before calling it.
            It changes the losoto parset and can conflict if not ran
            immediately afterwards.
        '''
        np.random.seed(np.abs(hash(self.ms)%2**31))
        with open(self.pset_loc + 'lstp.pset', 'r') as handle:
            data = [line for line in handle]
        self.psetname = '{:05d}'.format(np.random.randint(20000))
        print(self.psetname)
        os.mkdir('{0}/losoto/pcal{1}/'.format(self.ms, self.n))
        if self.n == 0:
            data[-1] = 'prefix = {0}/losoto/pcal{1}/'.format(self.ms, self.n)
            self.losoto = 'losoto {0}instrument.h5 {1}'.format(self.ms, self.psetname)
        else:
            data[-1] = 'prefix = {0}/losoto/pcal{1}/'.format(self.ms, self.n)
            self.losoto = 'losoto {0}instrument_{1}.h5 {2}'.format(self.ms, self.n, self.psetname)
        with open(self.psetname, 'w') as handle:
            for line in data:
                handle.write(line)

    def _init_parsets(self):
        ddecal = parse_pset(self.pset_loc + 'ddecal_init.pset')
        acal = parse_pset(self.pset_loc + 'acal_init.pset')
        ddecal.append('msin={}'.format(self.ms))
        acal.append('msin={}'.format(self.ms))
        acal.append('msout.datacolumn=CORRECTED_DATA')

        if self.n == 0:
            ddecal.append('ddecal.h5parm={0}instrument.h5'.format(self.ms))
            acal.append('applycal.parmdb={0}instrument.h5'.format(self.ms))
        else:
            ddecal.append('ddecal.h5parm={0}instrument_{1}.h5'.format(self.ms,self.n))
            acal.append('applycal.parmdb={0}instrument_{1}.h5'.format(self.ms,self.n))
        self.ddecal = ' '.join(ddecal)
        self.acal = ' '.join(acal)

    def _init_img(self):
        with open(self.pset_loc+'imaging.sh') as handle:
            base_image = handle.read()[:-2]
        if self.n == 0:
            imname = 'init'
        else:
            imname = 'pcal{}'.format(self.n)
        if os.path.isfile('{}casamask.fits'.format(self.pset_loc)):
            self.fulimg = '{0} -data-column CORRECTED_DATA -fits-mask {4}casamask.fits -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms, self.pset_loc)
        else:
            self.fulimg = '{0} -data-column CORRECTED_DATA -auto-mask 5 -auto-threshold 1.5 -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms)

    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

    def calibrate(self):
        '''
            Only run the calibration, not any imaging 
        '''
        self._init_parsets()
        self._init_losoto()
        self.pickle_and_call('DPPP {}'.format(self.ddecal))
        self.pickle_and_call('DPPP {}'.format(self.acal))
        self.pickle_and_call(self.losoto)
        os.remove(self.psetname)
   
    def prep_img(self):
        '''
            This will generate a directory and give the imaging command to be called.
            It will not have any msses, you need to give that yourself.
        '''
        self._init_dir()
        self.ms = '' # Now we dont get any ms at the end'
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
    
