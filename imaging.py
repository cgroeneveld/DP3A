import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
from matplotlib.patches import Ellipse
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

class Imager(object):
    def __init__(self,opts = {}, path_resolved = '', path_integrated = ''):
        self.opts = opts
        self.path_resolved = path_resolved
        self.path_integrated = path_integrated
    
    def generate_fluxscale(self):
        self.opts = _set_default(self.opts, 'size_box', 20)

        self.opts = generate_fluxscale(self.path_integrated,self.opts)
    
    def plot_MFS(self):
        self.opts = _set_default(self.opts,'thres',20)

        self.opts = plot_MFS(self.path_resolved,self.opts)
    
    def generateRegionSpectra(self):
        self.opts = _set_default(self.opts,'zoomf',1)

        self.opts = generateRegionSpectra(self.path_resolved,self.opts)
    
    def generateSingleImage(self,number):
        # First, parse the number to find the image you are interested in
        number_format = '{:04d}'.format(number)
        dirl = list(filter(lambda x: 'image' in x and 'MFS' not in x, self.path_resolved))
        examp = dirl[2]
        prefix = examp.split('-')[0]
        selected_image = '{0}-{1}-image.fits'.format(prefix,number_format)

        self.opts = _set_default(self.opts,'title','')
        self.opts = _set_default(self.opts,'outname','')
        self.opts = _set_default(self.opts,'colormap','afmhot')
        self.opts = _set_default(self.opts,'angds',500) # Should at the very least give a warning 
        self.opts = _set_default(self.opts,'lnscl',30)
        self.opts = _set_default(self.opts,'txclr','white')
        self.opts = _set_default(self.opts,'scpwr',0.5)
        self.opts = _set_default(self.opts,'zoomf',1)
        self.opts = _set_default(self.opts,'thres',20)

        if self.opts['angds'] == 500:
            print('It is actually quite important to set the angular diameter distance, that sets the scale')

        self.opts = generateSingleImage(self.path_resolved+selected_image,self.opts)
    
    def fillOpts(self):
        pass

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
    '''
        So I messed up with my reference frequency when making the bandpasses.
        This should fix it. Set reference freq to 150e6 once it is fixed.
    '''
    wrong = _evaluate_SH(frq,wrong_freq)
    right = _evaluate_SH(frq,150e6)
    return right/wrong

def _set_default(opts, key, default):
    value = input('{}: '.format(key))
    if value != ''
        opts[key] = value
    else:
        opts[key] = default
    return opts

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
        OUTPUT:
            fluxscale           :  Integrated fluxscale, as determined by the image of Dutch LOFAR
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
    delta = opts['size_box']
    
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
        
        OUTPUT:
            regions             :  Output regions as you just selected
    '''
    data = fits.getdata(path_to_resolved+'ws-MFS-image.fits')[0,0,:,:]
    head = fits.getheader(path_to_resolved+'ws-MFS-image.fits')
    frequency = float(head['CRVAL3'])
    beam_area = _compute_beam(head)
    try:
        # Correct the flux, if wanted
        flux = opts['fluxscale'](frequency)
        threshold = opts['thres']
        inmask = np.array(data > (threshold * np.mean(data)),dtype=bool)
        raw_flux = np.sum(data[inmask])/beam_area
        ratio = flux/raw_flux
        data *= ratio
    except KeyError:
        # Dont scale the data
        pass

    # Zoom in the image. Make sure that all observations after this also use the same
    # scale factor.
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

    # This generates a 'fake' grid
    xpoints,ypoints = np.mgrid[:512,:512]

    f = plt.figure()
    ax = plt.subplot(projection=coord, slices=('x','y',0,0))
    collection = ax.scatter(xpoints,ypoints,alpha=0)
    ax.imshow(data, origin='lower',vmin=0)

    sels = []
    selector = SelectFromCollection(ax,collection)
    def accept(event):
        # This thing is the weird thing that actually labels the regions
        if event.key == 'enter':
            sels.append(selector.xys[selector.ind])
            ax.set_title('Press enter to accept selected points as a region')
            f.canvas.draw()
    
    f.canvas.mpl_connect("key_press_event",accept)
    ax.set_title("Press enter to accept selected points as a region")

    plt.show()

    regionmask = np.zeros_like(data)
    # Now extract all the regions and show them
    for regnum,inds in enumerate(sels):
        for comb in inds:
            regionmask[comb[1],comb[0]] = regnum+1
    f = plt.figure()
    ax = plt.subplot(projection=coord,slices=('x','y',0,0))
    ax.imshow(regionmask,origin='lower')
    ax.set_title('Regions')
    plt.show()
    
    opts['regions'] = sels

    return opts

def generateRegionSpectra(path_to_resolved,opts={}):
    dirl_images = list(filter(lambda x: 'image' in x and 'MFS' not in x, os.listdir(path_to_resolved)))
    dirl_images_sorted = np.sort(np.array(dirl_images))
    data = [fits.getdata(path_to_resolved+dirry)[0,0,:,:] for dirry in dirl_images_sorted]
    headers = [fits.getheader(path_to_resolved+dirry) for dirry in dirl_images_sorted]
    beam_areas = [_compute_beam(head) for head in headers]
    frequencies = [head['CRVAL3'] for head in headers]

    # Try to zoom the image, just like before.
    zoomf = float(opts['zoomf'])
    zoomed_data = []
    for unzoomed in data:
        zoomed = zoom(unzoomed, zoomf)
        n,m = zoomed.shape
        xshape = (int(n/2 - 256), int(n/2 + 256))
        yshape = (int(m/2 - 256), int(m/2 + 256))
        zoomed_data.append(zoomed[xshape[0]:xshape[1],yshape[0]:yshape[1]])
    for i in range(len(headers)):
        headers[i]['CDELT1'] /= zoomf
        headers[i]['CDELT2'] /= zoomf

    try:
        regions = opts['regions']
    except KeyError:
        print("You need to declare regions first")
        return 1

    log_frequencies = np.log10(np.array(frequencies))
    region_fluxes = [] # All of these fluxes are LOGARITHMIC
    for i,reg in enumerate(regions):
        fluxes = []
        mask = np.zeros_like(data[0]) # Construct a mask, based on the coordinates
        for inds in reg:
            mask[inds[1],inds[0]] = 1
        mask = np.array(mask,dtype=bool)
        for j,img in enumerate(zoomed_data):
            fluxes.append(np.sum(img[mask])/beam_areas[j])
        region_fluxes.append(np.log10(np.array(fluxes)))
    
    f,ax = plt.subplots()
    for i,reg in enumerate(region_fluxes):
        plt.scatter(log_frequencies,reg,label = 'Region {}'.format(i))
    plt.legend()
    xticks = ax.get_xticks()
    yticks = ax.get_yticks()
    ax.set_xticklabels(np.array(10**np.array(xticks)/1e6,dtype=int))
    ax.set_yticklabels(np.array(10**np.array(yticks),dtype=int))
    plt.show()

    try:
        figdict = opts['figdict']
        figdict['region_spectra'] = f
        opts['figdict'] = figdict
    except KeyError:
        opts['figdict'] = {'region_spectra': f}
     
    return opts

def generateSingleImage(inname,opts={}):
    '''
        Define variables
        The image needs to be centered and 512x512
    '''

    FNAME = inname
    FSIZE = (10,10) # Dont change this, I suppose?
    TITLE = opts['title']
    OUTNM = opts['outname'] # Empty will just show the result
    CLMAP = opts['colormap'] # Default: afmhot
    ANGDS = opts['angds']  # Mpc
    LNSCL = opts['lnscl'] # kpc (default 30)
    ZOOMF = opts['zoomf']
    FXMAX = 0 # Lets not touch this yet
    TXCLR = opts['txclr'] # Default white


    SCPWR = opts['scpwr'] # Default 0.5
    SCALE = lambda x: ((np.abs(x)+x)/2)**SCPWR
    INVSC = lambda x: x**(1/SCPWR)

    OPTIC = opts['optical'] # J2000 (ra,dec) of optical counterpart, (0,0) doesnt show any

    '''
    =======================================================================
    '''

    # Read in data
    hdu = fits.open(FNAME)[0]
    rawdata = hdu.data[0,0,:,:]
    head = hdu.header

    # Scale the image/header
    zoomed_data = zoom(rawdata,ZOOMF)
    n,m = zoomed_data.shape
    xshape = (int(n/2 - 256), int(n/2 + 256))
    yshape = (int(m/2 - 256), int(m/2 + 256))
    data = zoomed_data[xshape[0]:xshape[1],yshape[0]:yshape[1]]
    head['CDELT1'] /= ZOOMF
    head['CDELT2'] /= ZOOMF
    coord = WCS(head)

    # Do some calculations
    ang = head['BPA']
    bmaj = head['BMAJ']
    bmin = head['BMIN']
    beam_area = _compute_beam(head)
    freq = '{:0.3} MHz'.format(head['CRVAL3']/1e6)

    scale = -head['CDELT1']

    mpl.rcParams.update({'axes.labelsize': 16, 'xtick.labelsize':14})

    # Scale the entire image to the correct fluxscale
    try:
        # But only if there is a fluxscale
        flscale = opts['fluxscale']
        logfreq = np.log10(float(head['CRVAL3']))
        logflx = flscale(logfreq)
        flux_should_be = 10** logflx

        try:
            threshold = opts['thres']
        except KeyError:
            threshold = 20
        mask = np.array(data > (threshold * np.mean(data)), dtype = bool)
        actual_flux = np.sum(data[mask])/beam_area
        ratio = flux_should_be/actual_flux
        data *= ratio
    except KeyError:
        # Dont scale if we do not have a fixed fluxscale
        pass

    # Build figure
    f = plt.figure(figsize=FSIZE)
    ax = plt.subplot(projection = coord,slices=('x','y',0,0))
    if FXMAX==0:
        vmax = np.max(SCALE(data))
    else:
        vmax = SCALE(FXMAX)
    cm = ax.imshow(SCALE(data), origin='lower', cmap=CLMAP, vmin=0,vmax = vmax)

    # Build colorbar
    cbar = plt.colorbar(cm, fraction = 0.046)
    cbar.set_label(r'Intensity (Jy/beam) $\rightarrow$')
    ticks = cbar.get_ticks()
    cbar.set_ticks(ticks)
    cbar.set_ticklabels(['{:0.3}'.format(tick) for tick in INVSC(ticks)])
    cbar.ax.tick_params(labelsize=16)

    # Put in optical counterpart
    if OPTIC[0] != 0 and OPTIC[1] != 0:
        ra_delt = OPTIC[0] - head['CRVAL1']
        dec_delt = OPTIC[1] - head['CRVAL2']
        ra_delt_pix = ra_delt / head['CDELT1']
        dec_delt_pix = dec_delt / head['CDELT2']
    
        optic_pix_ra = ra_delt_pix + head['CRPIX1']
        optic_pix_dec = dec_delt_pix + head['CRPIX2']
        ax.scatter([optic_pix_ra],[optic_pix_dec], color = TXCLR, marker = '+', s = 220)

    
    # Add distance line
    if ANGDS == 0:
        pass
    else:
        line_size = LNSCL / (1000*ANGDS) # radian
        line_size *= 180/np.pi # degrees
        pixel_size = line_size/scale

    # Add texts
    # ax.set_title(TITLE, fontsize=24, y=1.02)
    ax.text(256,480, TITLE, horizontalalignment='center', color = TXCLR, fontsize = 24)
    ax.text(40 ,50, freq, color=TXCLR, fontsize = 16)
    ax.text(40, 20, '{0:.2}"x{1:.2}"'.format(bmaj*3600, bmin*3600), color = TXCLR, fontsize = 16)
    ax.text(480,40, '{} kpc'.format(LNSCL), color = TXCLR, fontsize = 14, horizontalalignment='right')
    ax.plot([480,480-pixel_size],[20,20], color = TXCLR, lw = 4)
    beam = Ellipse((20,30), bmin/scale, bmaj/scale, ang, edgecolor=TXCLR, fill = False, lw = 2)
    ax.add_artist(beam)

    if OUTNM != '':
        f.savefig(OUTNM+'.png', format='png', bbox_inches='tight')
    else:
        plt.show()

    try:
        figdict = opts['figdict']
        try:
            spect_imgs = figdict['spectral_images']
            spect_imgs.append(f)
            figdict['spectral_images'] = spect_imgs
        except KeyError:
            # Make new list of spectral images
            figdict['spectral_images'] = [f]
    except KeyError:
        opts['figdict'] = {'spectral_images': [f]}

    return opts

def main():
    opts = {'zoomf':2.7, 'alt_reffreq': 231541442.871094}
    img_maker = Imager(opts,sys.argv[1], sys.argv[2])
    # img_maker.generate_fluxscale()
    img_maker.plot_MFS()
    img_maker.generateRegionSpectra()

if __name__ == '__main__':
    main()
