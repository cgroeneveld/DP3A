# import print_function
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import argparse
import journal_pickling as jp
import shutil
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
    return np.max(arra)/np.abs(np.min(arra))

def snr(arra):
    return np.max(arra)/calcrms(arra)

def copy_images(pth, run):
    if os.path.isdir(pth+'IMAGES'):
        pass
    else:
        os.mkdir(pth+'IMAGES')
    shutil.copyfile(pth+run+'/ws-image.fits', pth+'IMAGES/{}.fits'.format(run))

def rebuild_dirlist(dirlist):
    '''
        This function is basically a sorter. It formats the different steps in 
        such a way, that the resulting plot will be in chronological sequence,
        that is, beginning from "init"
    '''
    apcals = list(filter(lambda x: 'apcal' in x, dirlist))
    pcals = list(filter(lambda x: 'pcal' in x and 'apcal' not in x, dirlist))
    numbs_pcal = np.array([int(pcal[4:]) for pcal in pcals])
    numbs_apcal = np.array([int(apcal[5:]) for apcal in apcals])
    rebuild_pcals = ['pcal'+str(num) for num in np.sort(numbs_pcal)]
    rebuild_apcals = ['apcal'+str(num) for num in np.sort(numbs_apcal)]
    return ['init'] + rebuild_pcals + rebuild_apcals

def plotter(text, x, y, path):
    fig,ax = plt.subplots(figsize = (10,7))
    ax.plot(y)
    ax.set_xticks(np.arange(len(y)))
    ax.set_xticklabels(x, rotation = 30, ha = 'right')
    fig.suptitle(text, y = 0.92, size = 16)
    fig.savefig(path, format = 'pdf', bbox_inches = 'tight')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Measures the quality improvement over time for a certain run")
    parser.add_argument('-p', type = str, help = "Path to the location of the core run")

    parsed = parser.parse_args()
    
    logger = jp.Locker(parsed.p+'/log')
    logger.add_calls('quality_check')

    dirlist = rebuild_dirlist(os.listdir(parsed.p))
    rms = []
    maxmin = []
    snrs = []
    for run in dirlist:
        data = fits.getdata(parsed.p+run+'/ws-image.fits')[0,0,:,:]
        rms.append(calcrms(data))
        maxmin.append(max_min(data))
        snrs.append(snr(data))
        copy_images(parsed.p, run)
    
    logger.rms = rms
    logger.maxmin = maxmin
    logger.snrs = snrs

    plotter('RMS', dirlist, rms, parsed.p+'rms.pdf')
    plotter('I_max/I_min', dirlist, maxmin, parsed.p+'maxmin.pdf')
    plotter('Signal to noise (max/rms)', dirlist, snrs, parsed.p+'snr.pdf')

    logger.save()
