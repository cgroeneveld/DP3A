import numpy as np
import sys
import argparse
import os
import h5py
import datetime

def init_parse(fname):
    if os.path.isfile(fname):
        pass
    else:
        fl = h5py.File(fname, 'a')
        fl.create_dataset('Reduction calls', data = [])
        fl.attrs['absolute_path'] = os.path.abspath()
        fl.attrs['n_runs'] = 0

def parse_call(fname, call):
    init_parse(fname)
    fl = h5py.File(fname, 'a')
    calllist = list(fl['Reduction calls'])
    fl['Reduction calls'].append((str(datetime.datetime.today()), call))
    fl.attrs['n_runs'] += 1

def yield_last_call(fname):
    fl = h5py.File(fname, 'r')
    calllist = list(fl['Reduction calls'])