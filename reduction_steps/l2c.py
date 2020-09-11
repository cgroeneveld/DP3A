from __future__ import print_function
import numpy as np
import sys
import os
import lin2circ
import shutil
import subprocess
import journal_pickling as jp
from .tools import parse_pset

class LinToCirc(object):
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

    def run_lin2circ(self):
        options = {'inms': self.ms, 'column': 'DATA', 'back': False, 'poltable': False, 'outcol': 'DATA_CIRC', 'lincol': 'DATA_LIN'}
        lin2circ.main(options)
        self.pickle_and_call("DPPP msin={0} msout={0}CRC msout.storagemanager=dysco msout.writefullresflag=false msin.datacolumn=DATA_CIRC msout.datacolumn=DATA steps=[]".format(self.ms))
        shutil.move('{}CRC'.format(self.ms),self.ms)
    
    def calibrate(self):
        self.run_lin2circ()

    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

    def execute(self):
        if self.DEBUG:
            self._printrun()
        else:
            self._actualrun()
    
