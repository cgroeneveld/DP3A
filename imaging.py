import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
from astropy.io import fits
from astropy.modeling import fitting,models
from astropy.wcs import WCS
import argparse
import os
import sys
from scipy.ndimage import zoom

class SelectFromCollection(object):
    """Select indices from a matplotlib collection using `LassoSelector`.

    Selected indices are saved in the `ind` attribute. This tool fades out the
    points that are not part of the selection (i.e., reduces their alpha
    values). If your collection has alpha < 1, this tool will permanently
    alter the alpha values.

    Note that this tool selects collection objects based on their *origins*
    (i.e., `offsets`).

    Parameters
    ----------
    ax : :class:`~matplotlib.axes.Axes`
        Axes to interact with.

    collection : :class:`matplotlib.collections.Collection` subclass
        Collection you want to select from.

    alpha_other : 0 <= float <= 1
        To highlight a selection, this tool sets all selected points to an
        alpha value of 1 and non-selected points to `alpha_other`.
    """

    def __init__(self, ax, collection, alpha_other=0.3):
        self.canvas = ax.figure.canvas
        self.collection = collection
        self.alpha_other = alpha_other

        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))

        self.lasso = LassoSelector(ax, onselect=self.onselect)
        self.ind = []

    def onselect(self, verts):
        path = Path(verts)
        self.ind = np.nonzero(path.contains_points(self.xys))[0]
        self.fc[:, -1] = self.alpha_other
        self.fc[self.ind, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

    def disconnect(self):
        self.lasso.disconnect_events()
        self.fc[:, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()


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
            figdict             :  Dictionary of previous figures. Adds it into the list.
                                   Default: makes its own dict. Returns at the end                       
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
    results = fitter(model,np.log10(frequencies),np.log10(beam_corrected_fluxes))

    # Generate figure if it is wanted
    fig, ax = plt.subplots()
    plt.scatter(np.log10(frequencies), np.log10(beam_corrected_fluxes))
    resamp_x = np.linspace(np.min(np.log10(frequencies)), np.max(np.log10(frequencies)), 1000)
    ax.plot(resamp_x, results(resamp_x))
    xticks = ax.get_xticks()
    ax.set_xticklabels(np.array(10**xticks/1e6, dtype=int))
    yticks = ax.get_yticks()
    ax.set_yticklabels(np.array(10**yticks, dtype=int))
    
    try:
        figdict = opts['figdict']
        figdict['integrated'] = fig
    except KeyError:
        opts['figdict'] = {'integrated': fig}
    
    opts['fluxscale'] = results

    return opts

def plot_MFS(path_to_resolved, opts={}):
    '''
        Plots a picture of the resolved image.
        Allows you to set regions for resolved spectra

        INPUT:
            path_to_resolved    :  Path to the images of the resolved data
        
        OPTS:
            fluxscale           :  If a fluxscale is determined, fix the fluxscale
                                   Needs an astropy model that takes frequency (and returns a flux)
            zoomf               :  Zoom factor of the final image, default = 1
    '''
    data = fits.getdata(path_to_resolved+'ws-MFS-image.fits')[0,0,:,:]
    head = fits.getheader(path_to_resolved+'ws-MFS-image.fits')
    frequency = float(head['CRVAL3'])
    beam_area = _compute_beam(head)
    try:
        # Correct the flux, if wanted
        flux = opts['fluxscale'](frequency)
        try:
            threshold = opts['thres']
        except KeyError:
            threshold = 20
        inmask = np.array(data > (threshold * np.mean(data)),dtype=bool)
        raw_flux = np.sum(data[inmask])/beam_area
        ratio = flux/raw_flux
        data *= ratio
    except KeyError:
        # Dont scale the data
        pass

    try:
        zoomf = float(opts['zoomf'])
    except KeyError:
        zoomf = 1
    zoomed_data = zoom(data,zoomf) # Zoom the data, so it is a bit clearer
    n,m = zoomed_data.shape
    xshape = (int(n/2 - 256), int(n/2 + 256))
    yshape = (int(m/2 - 256), int(m/2 + 256))
    data = zoomed_data[xshape[0]:xshape[1],yshape[0]:yshape[1]]
    head['CDELT1'] /= zoomf
    head['CDELT2'] /= zoomf
    coord = WCS(head) # And generate WCS headers for the axes
    mpl.rcParams.update({'axes.labelsize': 16, 'xtick.labelsize':14})

    xpoints,ypoints = np.mgrid[:512,:512]

    f = plt.figure()
    ax = plt.subplot(projection=coord, slices=('x','y',0,0))
    collection = ax.scatter(xpoints,ypoints,alpha=0)
    ax.imshow(data, origin='lower',vmin=0)

    sels = []
    selector = SelectFromCollection(ax,collection)
    def accept(event):
        if event.key == 'enter':
            sels.append(selector.xys[selector.ind])
            ax.set_title('Press enter to accept selected points as a region')
            f.canvas.draw()
    
    f.canvas.mpl_connect("key_press_event",accept)
    ax.set_title("Press enter to accept selected points as a region")

    plt.show()

    opts['regions'] = sels
    return opts

def main():
    # generate_fluxscale(sys.argv[1], {'alt_reffreq':231541442.871094})         
    plot_MFS(sys.argv[1], {'zoomf':2.7})

if __name__ == '__main__':
    main()
