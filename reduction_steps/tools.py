import numpy as np
from losoto import h5parm
import sys
import os

def parse_pset(fname):
    with open(fname, 'r') as handle:
        data = [line for line in handle]
    # Just some formatting
    data = [x.rstrip('\n') for x in data]
    data = list(filter(lambda x: x != '', data))
    # Raise an error if we manually define the h5parm
    newdata = []
    for x in data:
        if 'h5parm' in x:
            raise ValueError('Please do not define your own h5parm. We will do that for you.')
        elif 'msin = ' in x:
            raise ValueError('Please do not define msin - we do that ourselves')
        elif 'msout.datacolumn' in x:
            raise ValueError('Please do not define msout.datacolumn - we do that ourselves')
        else:
            newdata.append(''.join(list(filter(lambda y: y != ' ', x))))
    return newdata

def process_diag(fname):
    H5 = h5parm.h5parm(fname,readonly=False)
    stb = H5.getSolset('sol000').getSoltab('amplitude000').getValues()
    stb_shape = stb[0].shape
    num_freqs = stb_shape[1]
    for freq in range(num_freqs):
        print(np.nanmean(stb[0][:,freq,:,:,:]))
        mean_amp = np.nanmean(stb[0][:,freq,:,:,:])
        stb[0][:,freq,:,:,:] *= 1/mean_amp
    H5.getSolset('sol000').getSoltab('amplitude000').setValues(stb[0])
    H5.close()
