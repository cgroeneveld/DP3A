#!/usr/bin/env python2.7
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

def copy_images(pth,redsteps):
    '''
        Standalone version. Will need the reduction string, but figures
        the rest by itself.
    '''
    if os.path.isdir(pth+'IMAGES'):
        pass
    else:
        os.mkdir(pth+'IMAGES')
    nums = [i+1 for i in range(len(redsteps))]
    lendict = {char: [i+1 for i in range(len(list(filter(lambda x: x==char, redsteps))))] for char in np.unique(redsteps)}
    iternums = [lendict[char].pop(0) for char in redsteps]
    dirlist = []
    for fulnum,step,iternum in zip(nums,redsteps,iternums):
        if step == 't':
            dirlist.append('teccal{0}'.format(iternum))
        elif step == 'd':
            dirlist.append('apcal{0}'.format(iternum))
        elif step == 'p':
            dirlist.append('pcal{0}'.format(iternum))
        elif step == 'a':
            dirlist.append('tpcal{0}'.format(iternum))
    tolist = ['{0:02d}{1}'.format(num,dirry) for num,dirry in zip(nums,dirlist)]
    for to,fro in zip(tolist, dirlist):
        try:
            shutil.copyfile(pth+fro+'/ws-MFS-image.fits', pth+'IMAGES/{}.fits'.format(to))
        except IOError:
            shutil.copyfile(pth+fro+'/ws-image.fits', pth+'IMAGES/{}.fits'.format(to))

def copy_images_backup(pth, run):
    if os.path.isdir(pth+'IMAGES'):
        pass
    else:
        os.mkdir(pth+'IMAGES')
    try:
        shutil.copyfile(pth+run+'/ws-image.fits', pth+'IMAGES/{}.fits'.format(run))
    except IOError:
        shutil.copyfile(pth+run+'/ws-MFS-image.fits', pth+'IMAGES/{}.fits'.format(run))

def rebuild_dirlist(redsteps, nlist):
    dirlist = []
    for m, step in zip(nlist,redsteps):
        n = int(m)
        if step == 't':
            dirlist.append('teccal{}'.format(n))
        elif step == 'd':
            dirlist.append('apcal{}'.format(n))
        elif step == 'p':
            dirlist.append('pcal{}'.format(n))
        elif step == 'a':
            dirlist.append('tpcal{}'.format(n))
    return dirlist

def plotter(text, x, y, path):
    fig,ax = plt.subplots(figsize = (10,7))
    ax.plot(y)
    ax.set_xticks(np.arange(len(y)))
    ax.set_xticklabels(x, rotation = 30, ha = 'right')
    fig.suptitle(text, y = 0.92, size = 16)
    fig.savefig(path, format = 'pdf', bbox_inches = 'tight')


def main(fpath, redsteps, nlist):
    logger = jp.Locker(fpath+'log')
    logger.add_calls('quality_check')

    dirlist = rebuild_dirlist(redsteps, nlist)
    rms = []
    maxmin = []
    snrs = []
    for run in dirlist:
        try:
            data = fits.getdata(fpath+run+'/ws-image.fits')[0,0,:,:]
        except:
            data = fits.getdata(fpath+run+'/ws-MFS-image.fits')[0,0,:,:]
        rms.append(calcrms(data))
        maxmin.append(max_min(data))
        snrs.append(snr(data))
    copy_images(fpath,redsteps)
    
    logger.rms = rms
    logger.maxmin = maxmin
    logger.snrs = snrs

    plotter('RMS', dirlist, rms, fpath+'rms.pdf')
    plotter('I_max/I_min', dirlist, maxmin, fpath+'maxmin.pdf')
    plotter('Signal to noise (max/rms)', dirlist, snrs, fpath+'snr.pdf')

    logger.save()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
