from __future__ import print_function
import numpy as np
import sys
import os
import subprocess
import journal_pickling as jp
from .tools import parse_pset
from astropy.io import fits

def suppressNegatives(pth):
    '''
        Sets all negative values in a particular model image to 0
        c.f. RvW
    '''
    models = list(filter(lambda x: 'model' in x and 'MFS' not in x, os.listdir(pth)))
    model_paths = ['{0}/{1}'.format(pth,model) for model in models]
    for mp in model_paths:
        hdul = fits.open(mp)
        data = hdul[0].data
        negmask = data<0
        data[negmask] = 0
        hdul[0].data = data
        hdul.writeto(mp, overwrite=True)
        hdul.close()

def scaleModels(pth, readlist):
    '''
        lets not do this anymore
    '''
    reffreq = float(readlist[0])
    termlist = [float(x) for x in readlist[1].split(',')]
    models = list(filter(lambda x: 'model' in x and 'MFS' not in x, os.listdir(pth)))
    model_paths = ['{0}/{1}'.format(pth, model) for model in models]
    psfs = list(filter(lambda x: 'psf' in x and 'MFS' not in x, os.listdir(pth)))
    psf_paths = ['{0}/{1}'.format(pth,psf) for psf in psfs]
    for mp,psfp in zip(model_paths,psf_paths):
        hdul = fits.open(mp)
        psf = fits.open(psfp)
        psf_flux = np.sum(psf[0].data)
        psf.close()
        data = hdul[0].data
        freq = hdul[0].header['CRVAL3']
        lg_freq = np.log10(freq/reffreq)
        sum_flx = np.sum(data)
        lg_target_flx = np.sum([term*lg_freq**n for n,term in enumerate(termlist)])
        target_flx = 10**lg_target_flx
        scaling = target_flx/(sum_flx*psf_flux)
        new_data = data * scaling
        hdul[0].data = new_data
        hdul.writeto(mp, overwrite=True)
        hdul.close()

class DiagonalCalibrator(object):
    def __init__(self, n, ms, fpath, pset_loc = './'):
        self.n = n
        self.ms = ms
        self.fpath = fpath
        self.initialized = False
        self.pset_loc = pset_loc
        self.log = jp.Locker(fpath+'log')
        self.DEBUG = False
        assert fpath[-1] == '/'
        assert ms[-1] == '/'
        assert pset_loc[-1] == '/'
        assert n > 0
    
    def initialize(self):
        self._init_parsets()
        self._init_dir()
        self._init_img()
        self.initialized = True

    def _init_dir(self):
        try:
            os.mkdir('{0}apcal{1}'.format(self.fpath,self.n))
        except OSError:
            pass

    def _init_losoto(self):
        '''
            This needs to be ran right before calling it.
            It changes the losoto parset and can conflict if not ran
            immediately afterwards.
        '''
        np.random.seed(np.abs(hash(self.ms))%2**31)
        self.prephasename = '{:05d}'.format(np.random.randint(20000))
        self.ampname = '{:05d}'.format(np.random.randint(20000))
        self.slowphasename = '{:05d}'.format(np.random.randint(20000))
        with open(self.pset_loc + 'lstp.pset', 'r') as handle:
            data = [line for line in handle]
        os.mkdir('{0}/losoto/apcal{1}/'.format( self.ms, self.n))
        data[-1] = 'prefix = {0}/losoto/apcal{1}/prephase'.format(self.ms, self.n)
        self.losoto_p = 'losoto {0}instrument_p{1}.h5 {2}'.format(self.ms, self.n, self.prephasename)
        with open(self.prephasename, 'w') as handle:
            for line in data:
                handle.write(line)

        with open(self.pset_loc + 'lsta.pset', 'r') as handle:
            data = [line for line in handle]
        data[-1] = 'prefix = {0}/losoto/apcal{1}/amp'.format(self.ms, self.n)
        self.losoto_a = 'losoto {0}instrument_a{1}.h5 {2}'.format(self.ms, self.n,self.ampname)
        with open(self.ampname, 'w') as handle:
            for line in data:
                handle.write(line)

        with open(self.pset_loc + 'lsslow.pset', 'r') as handle:
            data = [line for line in handle]
        data[-1] = 'prefix = {0}/losoto/apcal{1}/slowphase'.format(self.ms, self.n)
        self.losoto_slow = 'losoto {0}instrument_a{1}.h5 {2}'.format(self.ms, self.n, self.slowphasename)
        with open(self.slowphasename, 'w') as handle:
            for line in data:
                handle.write(line)

    def _init_parsets(self):
        ddecal = parse_pset(self.pset_loc + 'ddecal_init.pset')
        acal = parse_pset(self.pset_loc + 'acal_init.pset')
        ddecal.append('msin={}'.format(self.ms))
        acal.append('msin={}'.format(self.ms))
        ddecal.append('ddecal.h5parm={0}instrument_p{1}.h5'.format(self.ms,self.n))
        acal.append('applycal.parmdb={0}instrument_p{1}.h5'.format(self.ms,self.n))
        ddecal.append('msout.datacolumn=CORRECTED_PHASE')
        acal.append('msout.datacolumn=CORRECTED_PHASE')
        self.ddephase = ' '.join(ddecal)
        self.aphase = ' '.join(acal)

        ddeamp = parse_pset(self.pset_loc + 'ddecal_ampself.pset')
        aamp = parse_pset(self.pset_loc + 'acal_ampself.pset')
        ddeamp.append('msin={}'.format(self.ms))
        aamp.append('msin={}'.format(self.ms))
        ddeamp.append('ddecal.h5parm={0}instrument_a{1}.h5'.format(self.ms, self.n))
        aamp.append('applycal.parmdb={0}instrument_a{1}.h5'.format(self.ms, self.n))
        ddeamp.append('msin.datacolumn=CORRECTED_PHASE')
        aamp.append('msin.datacolumn=CORRECTED_PHASE')
        aamp.append('msout.datacolumn=CORRECTED_DATA2')
        self.ddeamp = ' '.join(ddeamp)
        self.aamp = ' '.join(aamp)

    def _init_img(self):
        with open(self.pset_loc+'imaging.sh') as handle:
            base_image = handle.read()[:-2]
        if self.n == 0:
            imname = 'init'
        else:
            imname = 'apcal{}'.format(self.n)
        if os.path.isfile('{}casamask.fits'.format(self.pset_loc)):
            self.fulimg = '{0} -no-update-model-required -data-column CORRECTED_DATA2 -fits-mask {4}casamask.fits -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms, self.pset_loc)
        else:
            self.fulimg = '{0} -no-update-model-required -data-column CORRECTED_DATA2 -auto-mask 5 -auto-threshold 1.5 -name {1}{2}/ws {3}'.format(base_image, self.fpath, imname, self.ms)
    
    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

    def run_img(self, mslist):
        '''
            Does three things:
            Firstly, it runs wsclean to generate a model.
            Next, it modifies the model to suppress negative flux
            and to make sure the total flux matches a model (if avail)
        '''
        fulimg = self.prep_img()
        imgcall = fulimg + ' '.join(mslist)
        self.pickle_and_call(imgcall)
        suppressNegatives('{0}/apcal{1}'.format(self.fpath, self.n))
        with open(self.pset_loc+'predicting.sh') as handle:
            base_predict = handle.read()[:-2]
        base_predict += ' -name {0}/apcal{1}/ws {2}'.format(self.fpath, self.n, ' '.join(mslist))
        self.pickle_and_call(base_predict)

    def calibrate(self):
        self._init_parsets()
        self._init_losoto()
        self.pickle_and_call('DPPP {}'.format(self.ddephase))
        self.pickle_and_call('DPPP {}'.format(self.aphase))
        self.pickle_and_call('DPPP {}'.format(self.ddeamp))
        self.pickle_and_call('DPPP {}'.format(self.aamp))
        self.pickle_and_call(self.losoto_p)
        self.pickle_and_call(self.losoto_a)
        self.pickle_and_call(self.losoto_slow)
        os.remove(self.prephasename)
        os.remove(self.ampname)
        os.remove(self.slowphasename)
    
    def prep_img(self):
        self._init_dir()
        self.ms = ''
        self._init_img()
        return self.fulimg

    def _printrun(self):
        '''
            Basically prints all commands, without running it
        '''
        with open('kittens.fl', 'a') as handle:
            handle.write('DPPP {}\n'.format(self.ddephase))
            handle.write('DPPP {}\n'.format(self.aphase))
            handle.write('DPPP {}\n'.format(self.ddeamp))
            handle.write('DPPP {}\n'.format(self.aamp))
            handle.write(self.fulimg+'\n')
            self._init_losoto()
            handle.write(self.losoto_p+'\n')
            handle.write(self.losoto_a)

    def _actualrun(self):
        self.pickle_and_call('DPPP {}'.format(self.ddephase))
        self.pickle_and_call('DPPP {}'.format(self.aphase))
        self.pickle_and_call('DPPP {}'.format(self.ddeamp))
        self.pickle_and_call('DPPP {}'.format(self.aamp))
        self.pickle_and_call(self.fulimg)
        self._init_losoto()
        self.pickle_and_call(self.losoto_p)
        self.pickle_and_call(self.losoto_a)
        self.pickle_and_call(self.losoto_slow)


    def execute(self):
        if self.DEBUG:
            self._printrun()
        else:
            self._actualrun()
    
