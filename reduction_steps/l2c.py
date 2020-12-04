from __future__ import print_function
import numpy as np
import sys
import os
import lin2circ
import shutil
import subprocess
import journal_pickling as jp
from .tools import parse_pset

class FakeLinParser(object):
    def __init__(self, inms, column, back, poltable, outcol, lincol):
        self.inms = inms
        self.column = column
        self.back = back
        self.poltable = poltable
        self.outcol = outcol
        self.lincol = lincol

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
        options = FakeLinParser(self.ms, 'DATA', False, False, 'DATA_CIRC', 'DATA_LIN')
        lin2circ.main(options)
        sys.stdout.flush()
        self.pickle_and_call("DPPP msin={0} msout={0}CRC msout.storagemanager=dysco msout.writefullresflag=false msin.datacolumn=DATA_CIRC msout.datacolumn=DATA steps=[]".format(self.ms[:-1]))
        shutil.move('{}CRC'.format(self.ms[:-1]),self.ms)
    
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
    
