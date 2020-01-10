from __future__ import print_function
import numpy as np
import sys
import os
import subprocess
import journal_pickling as jp
import shutil as shu
import diag_cal as dc
from losoto import h5parm
from .tools import parse_pset


class PhaseUp(object):
    def __init__(self, n, ms, fpath, pset_loc = './', predict_path = './model.fits'):
        self.ms = ms
        self.fpath = fpath
        self.initialized = False
        self.pset_loc = pset_loc
        self.log = jp.Locker(fpath+'log')
        self.predict_path = predict_path
        self.DEBUG = False
        assert fpath[-1] == '/'
        assert ms[-1] == '/'
        assert pset_loc[-1] == '/'
        assert n == 1

    def initialize(self):
        self._init_parsets()
        self._init_dir()
        self._init_calibrate()
        self.initialized = True
    
    def _init_dir(self):
        os.mkdir('{}phaseup'.format(self.fpath))

    def _init_parsets(self):
        ddecal = parse_pset(self.pset_loc + 'phaseup.pset')
        ddecal.append('msin={}'.format(self.ms))
        ddecal.append('msout={}_pu/'.format(self.ms[:-1]))
        self.ddecal_pu = ' '.join(ddecal)

        ddecal2 = parse_pset(self.pset_loc + 'ddecal_prephase.pset')
        ddecal2.append('msin={}'.format(self.ms))
        ddecal2.append('ddecal.h5parm={}prephase.h5'.format(self.ms))
        ddecal2.append('msout.datacolumn=CORRECTED_PHASE')
        self.ddecal2 = ' '.join(ddecal2)

        acal2 = parse_pset(self.pset_loc + 'acal_prephase.pset')
        acal2.append('msin={}'.format(self.ms))
        acal2.append('applycal.parmdb={}prephase.h5'.format(self.ms))
        acal2.append('msout.datacolumn=CORRECTED_PHASE')
        self.acal2 = ' '.join(acal2)

        ddecal_diag = parse_pset(self.pset_loc + 'ddecal_ampself.pset')
        ddecal_diag.append('msin={}'.format(self.ms))
        ddecal_diag.append('ddecal.h5parm={}prephase2.h5'.format(self.ms))
        ddecal_diag.append('msin.datacolumn=CORRECTED_PHASE')
        ddecal_diag.append('msout.datacolumn=CORRECTED_DATA2')
        self.ddecal_diag = ' '.join(ddecal_diag)

        acal_diag = parse_pset(self.pset_loc + 'acal_ampself.pset')
        acal_diag.append('msin={}'.format(self.ms))
        acal_diag.append('msin.datacolumn=CORRECTED_PHASE')
        acal_diag.append('msout.datacolumn=CORRECTED_DATA2')
        acal_diag.append('applycal.parmdb={}prephase2.h5'.format(self.ms))
        self.acal_diag = ' '.join(acal_diag)

    def _init_losoto(self):
        '''
            This needs to be ran right before calling it.
            It changes the losoto parset and can conflict if not ran
            immediately afterwards.
        '''
        with open(self.pset_loc + 'lsupp.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove(self.pset_loc + 'lsupp.pset')
        data[-1] = 'prefix = {0}phaseup/'.format(self.fpath)
        self.losoto_p = 'losoto {0}prephase2.h5 {1}lsupp.pset'.format(self.ms, self.pset_loc)
        with open(self.pset_loc + 'lsupp.pset', 'w') as handle:
            for line in data:
                handle.write(line)

        with open(self.pset_loc + 'lsupa.pset', 'r') as handle:
            data = [line for line in handle]
        os.remove(self.pset_loc + 'lsupa.pset')
        data[-1] = 'prefix = {0}phaseup/amp'.format(self.fpath)
        self.losoto_a = 'losoto {0}prephase2.h5 {1}lsupa.pset'.format(self.ms,self.pset_loc)
        with open(self.pset_loc + 'lsupa.pset', 'w') as handle:
            for line in data:
                handle.write(line)

    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

    def fix_folders(self):
        shu.rmtree(self.ms)
        shu.copytree('{}_pu/'.format(self.ms[:-1]), self.ms)
        shu.rmtree('{}_pu/'.format(self.ms[:-1]))

    def _init_calibrate(self):
        self.predict_call = 'wsclean -predict -name {0} {1}'.format(self.predict_path, self.ms)

    def fix_h5(self, parmname, also_amp = False):
        '''
            THIS FUNCTION IS MISBEHAVING
        '''
        H5 = h5parm.h5parm(self.ms + parmname, readonly = False) 
        phases = H5.getSolset('sol000').getSoltab('phase000').getValues()
        phasevals = phases[0]
        antennas = phases[1]['ant']
        # Select ids of international, remote and both
        idx_rem_int = np.where([not 'CS' in ant for ant in antennas])
        idx_int = np.where([not ('CS' in ant or 'RS' in ant) for ant in antennas])
        idx_rem = np.where(['RS' in ant for ant in antennas])
        phasevals[:,:,idx_rem_int,:,:] = 0.0 # Try setting all directions?
        if also_amp:
            ampvals = H5.getSolset('sol000').getSoltab('amplitude000').getValues()[0]
            ampvals[:,:,idx_rem,0,:] = 1.0 
            ampvals[:,:,idx_int,0,:] = 2.0
            H5.getSolset('sol000').getSoltab('amplitude000').setValues(ampvals)
        H5.getSolset('sol000').getSoltab('phase000').setValues(phasevals)
        H5.close()

    def _printrun(self):
        '''
            Basically prints all commands, without running it
        '''
        with open('kittens.fl', 'a') as handle:
            handle.write('DPPP {}\n'.format(self.ddecal2))
            handle.write('DPPP {}\n'.format(self.acal2))
            handle.write(self.fulimg1+'\n')
            handle.write('DPPP {}\n'.format(self.ddecal_diag))
            handle.write('DPPP {}\n'.format(self.acal_diag))
            handle.write(self.fulimg2+'\n')
            self._init_losoto()
            handle.write(self.losoto_p+'\n')
            handle.write(self.losoto_a+'\n')
            handle.write('DPPP {}\n'.format(self.ddecal_pu))
            handle.write(self.predict_call+'\n')

    def _actualrun(self):
        self.pickle_and_call('DPPP {}'.format(self.ddecal2))
        self.fix_h5('prephase.h5')
        self.pickle_and_call('DPPP {}'.format(self.acal2))
        self.pickle_and_call('DPPP {}'.format(self.ddecal_diag))
        self.fix_h5('prephase2.h5', True)
        self.pickle_and_call('DPPP {}'.format(self.acal_diag))
        self._init_losoto()
        self.pickle_and_call(self.losoto_p)
        self.pickle_and_call(self.losoto_a)
        self.pickle_and_call('DPPP {}'.format(self.ddecal_pu))
        # self.fix_folders()
        self.pickle_and_call(self.predict_call)


    def execute(self):
        if self.DEBUG:
            self._printrun()
        else:
            self._actualrun()
    
