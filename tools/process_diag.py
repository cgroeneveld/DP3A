import numpy as np
from losoto import h5parm
import sys
import os

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


if __name__ == '__main__':
    fname = sys.argv[1]
    main(fname)
