from __future__ import print_function
import numpy as np
import sys
import os
import subprocess
import journal_pickling as jp
import shutil as shu
from .tools import parse_pset

class PhaseUp(object):
    def __init__(self, n, ms, fpath, pset_loc = './', prev_iter='p1'):
        self.ms = ms
        self.fpath = fpath
        self.initialized = False
        self.pset_loc = pset_loc
        self.log = jp.Locker(fpath+'log')
        self.DEBUG = False
        self.prev_iter = prev_iter
        assert fpath[-1] == '/'
        assert ms[-1] == '/'
        assert pset_loc[-1] == '/'
        assert n == 1
    
    def initialize(self):
        self._init_parsets()
        self._init_calibrate()
        self.initialized = True
    
    def _init_parsets(self):
        ddecal = parse_pset(self.pset_loc + 'phaseup.pset')
        ddecal.append('msin={}'.format(self.ms))
        ddecal.append('msout={}_pu/'.format(self.ms[:-1]))
        self.ddecal = ' '.join(ddecal)

    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

    def fix_folders(self):
        shu.rmtree(self.ms)
        shu.copytree('{}_pu/'.format(self.ms[:-1]), self.ms)
        shu.rmtree('{}_pu/'.format(self.ms[:-1]))

    def _init_calibrate(self):
        if self.prev_iter[0] == 'p':
            folder = 'pcal{}'.format(self.prev_iter[1])
        elif self.prev_iter[1] == 'd':
            folder = 'apcal{}'.format(self.prev_iter[1])
        elif self.prev_iter[1] == 't':
            folder = 'teccal{}'.format(self.prev_iter[1])
        predict_path = '{0}{1}/ws'.format(self.fpath, folder)
        self.predict_call = 'wsclean -predict -name {0} {1}'.format(predict_path, self.ms)

   
    def _printrun(self):
        '''
            Basically prints all commands, without running it
        '''
        with open('kittens.fl', 'a') as handle:
            handle.write('DPPP {}\n'.format(self.ddecal))
            handle.write(self.predict_call)

    def _actualrun(self):
        self.pickle_and_call('DPPP {}'.format(self.ddecal))
        self.fix_folders()
        self.pickle_and_call(self.predict_call)


    def execute(self):
        if self.DEBUG:
            self._printrun()
        else:
            self._actualrun()
    
