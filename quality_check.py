# import print_function
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import argparse
from astropy.io import fits

def calcrms(arra):
    xcenter = 40
    ycenter = 40
    rad = 30
    grid = np.mgrid[:np.shape(arra)[0], :np.shape(arra)[1]]
    xdists = grid[1] - xcenter
    ydists = grid[0] - ycenter
    dists2 = xdists**2 + ydists**2
    mask = dists2 < rad**2
    selected = arra[mask]
    return np.sqrt(np.mean(selected**2))

def max_min(arra):
    return np.max(arra)/np.min(arra)

def snr(arra):
    return np.max(arra)/calcrms(arra)

def rebuild_dirlist(dirlist):
    '''
        This function is basically a sorter. It formats the different steps in 
        such a way, that the resulting plot will be in chronological sequence,
        that is, beginning from "init"
    '''
    pcals = list(filter(lambda x: 'pcal' in x, dirlist))
    numbs = np.array([int(pcal[4:]) for pcal in pcals])
    rebuild_pcals = ['pcal'+str(num) for num in np.sort(numbs)]
    return ['init'] + rebuild_pcals

def plotter(text, x, y, path):
    fig,ax = plt.subplots()
    ax.plot(y)
    ax.set_xticklabels(['..']+x)
    fig.suptitle(text)
    fig.savefig(path, format = 'pdf')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Measures the quality improvement over time for a certain run")
    parser.add_argument('-p', type = str, help = "Path to the location of the core run")

    parsed = parser.parse_args()

    dirlist = rebuild_dirlist(os.listdir(parsed.p))
    rms = []
    maxmin = []
    snrs = []
    for run in dirlist:
        data = fits.getdata(parsed.p+run+'/ws-image.fits')[0,0,:,:]
        rms.append(calcrms(data))
        maxmin.append(max_min(data))
        snrs.append(snr(data))
    
    plotter('RMS', dirlist, rms, parsed.p+'rms.pdf')
    plotter('I_max/I_min', dirlist, maxmin, parsed.p+'maxmin.pdf')
    plotter('Signal to noise (max/rms)', dirlist, snrs, parsed.p+'snr.pdf')
