import numpy as np
import datetime
import pickle
import os
import sys

class Locker(object):
    def __init__(self, fname):
        self.fname = fname
        if os.path.isfile(fname):
            self._load()
        else:
            self.reduction_calls = []
            self.ncalls = 0
        
    def add_calls(self, call):
        self.reduction_calls.append((datetime.datetime.today(), call))
        self.ncalls += 1
    
    def return_last(self):
        return self.reduction_calls[-1][1]
    
    def save(self):
        with open(self.fname, 'wb') as fl:
            pickle.dump(self.__dict__, fl, 2)
    
    def _load(self):
        with open(self.fname, 'rb') as fl:
            tempdict = pickle.load(fl)
            self.__dict__.update(tempdict)
    