from __future__ import print_function
import numpy as np
import sys
import os
import subprocess
import journal_pickling as jp
import tools

class PhaseCalibrator(object):
    def __init__(self, n, ms, fpath, pset_loc = './'):
        self.n = n
        self.ms = ms
        self.fpath = fpath
        self.initialized = False
        self.pset_loc = pset_loc
        self.log = jp.Locker(fpath+'log')
        self.DEBUG = True
        assert fpath[-1] == '/'
        assert ms[-1] == '/'
        assert pset_loc[-1] == '/'
    
    def initialize(self):
        self._init_parsets()
        self._init_img()
        self.initialized = True

    def _init_losoto(self):
        '''
            This needs to be ran right before calling it.
            It changes the losoto parset and can conflict if not ran
            immediately afterwards.
        '''
        with open(self.pset_loc + 'lstp.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove(self.pset_loc + 'lstp.pset')
        if self.n == 0:
            data[-1] = 'prefix = {0}init/'.format(self.fpath)
            self.losoto = 'losoto {0}instrument.h5 lstp.pset'.format(self.ms)
        else:
            data[-1] = 'prefix = {0}pcal{1}/'.format(self.fpath, self.n)
            self.losoto = 'losoto {0}instrument_{1}.h5 lstp.pset'.format(self.ms, self.n)
        with open(self.pset_loc + 'lstp.pset', 'w') as handle:
            for line in data:
                handle.write(line)
    
    def _init_parsets(self):
        ddecal = tools.parse_pset(self.pset_loc + 'ddecal_init.pset')
        acal = tools.parse_pset(self.pset_loc + 'acal_init.pset')
        ddecal.append('msin={}'.format(self.ms))
        acal.append('msin={}'.format(self.ms))

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
        self.fulimg = '{0} -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms)
    
    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

   
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
    
