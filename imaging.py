import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.modeling import fitting,models
import argparse
import os
import sys

def _compute_beam(head):
    beam_area = np.pi/(4*np.log(2)) * head['BMAJ'] * head['BMIN']
    area_pixels = beam_area / head['CDELT2']**2
    return area_pixels

def _evaluate_SH(frq, reffrq):
    SH = models.Polynomial1D(degree=2)
    SH.parameters=[np.log10(83.084),-0.699,-0.11]
    x = np.log10(frq/reffrq)
    return 10**SH(x)

def _converter(frq,wrong_freq=231541442.871094):
    wrong = _evaluate_SH(frq,wrong_freq)
    right = _evaluate_SH(frq,150e6)
    return right/wrong

def generate_fluxscale(path_to_int, opts={}):
    '''
        Generates an integrated spectrum from an image.
        It is important to note that this requires an image made with low resolution
        and only including Dutch LOFAR. Typically, we use a ~5km (=~1000 lambda) UVcut
        so we do not see the entire sky.

        INPUT:
            path_to_int         :  Path to the spectrum of the integrated spectra.
                                   File must contain ws-*.fits

        OPTS:
            size_box            :  size of the input box. Default=20 pixels
                                   Needs to be changed with different beams!
            alt_reffreq         :  Needs to be set if we need to shift the spectrum.
                                   Because I was stupid, I accidentally used the wrong reffreq
                                   when computing the bandpasses. Put that reffreq here.
                                   Default: no correction. Reffreq I used: 231541442.871094
                                   
    '''
    dirl = list(filter(lambda x: 'image' in x and 'MFS' not in x, os.listdir(path_to_int)))
    sorted_images = np.sort(np.array(dirl)) # Returns the paths to images, all sorted.
    datalist = [fits.getdata(path_to_int+imgpath)[0,0,:,:] for imgpath in sorted_images]
    headlist = [fits.getheader(path_to_int+imgpath) for imgpath in sorted_images]
    beam_areas = [_compute_beam(header) for header in headlist] # Beam sizes per image
    frequencies = [head['CRVAL3'] for head in headlist]

    # From here we assume all images have the same size (in pixels)
    # Also assume the image is a nice square
    example_image = datalist[0]
    middle = int(np.shape(example_image)[0]/2)
    try:
        delta = opts['size_box']
    except KeyError:
        delta = 20
    
    raw_fluxes = [np.sum(data[middle-delta:middle+delta,middle-delta:middle+delta]) for data in datalist]
    beam_corrected_fluxes = [raw_flux/beam_area for raw_flux,beam_area in zip(raw_fluxes,beam_areas)]
    try:
        # Frequency-bandpass correction required
        wrong_freq = opts['alt_reffreq']
        correction_factors = np.array([_converter(freq,wrong_freq) for freq in frequencies])
        beam_corrected_fluxes *= correction_factors
    except KeyError:
        # no correction needed
        pass

    # Now fit a high-parameter model against this data
    # This is NOT a physical model, only here for interpolation
    fitter = fitting.LevMarLSQFitter()
    model = models.Polynomial1D(degree=len(beam_corrected_fluxes)-1)
    results = fitter.fit(model,np.log10(frequencies),np.log10(beam_corrected_fluxes))

    # Generate figure if it is wanted
    fig, ax = plt.subplots()
    plt.scatter(np.log10(frequencies), np.log10(beam_corrected_fluxes))
    resamp_x = np.linspace(np.min(np.log10(frequencies)), np.max(np.log10(frequencies)), 1000)
    ax.plot(resamp_x, results(resamp_x))
    xticks = ax.get_xticks()
    ax.set_xticklabels(np.array(10**xticks, dtype=int))
    yticks = ax.get_yticks()
    ax.set_yticklabels(np.array(10**yticks, dtype=int))
    plt.show()
    

def main():
    generate_fluxscale(sys.argv[1], {'alt_reffreq':231541442.871094})         

if __name__ == '__main__':
    main()