import journal_pickling as jp
import subprocess
from .tools import parse_pset

class Predictor(object):
    def __init__(self, ms, pred_path, fpath, pset_loc):
        self.ms = ms
        self.DEBUG = False
        self.pred_path = pred_path 
        self.fpath = fpath
        self.pset_loc = pset_loc
        self.log = jp.Locker(fpath+'log')
    
    def initialize(self):
        abbr_name, self.type = self.check_model_type()
        # Make a sourcedb if it is a skymodel, then just run either wsclean predict
        # if it is a fits file or DPPP predict if it isnt
        if self.type == 'skymodel':
            self.pickle_and_call('makesourcedb in={0}.skymodel out={0}.sourcedb'.format(abbr_name))
        if self.type == 'fits':
            self.call_string = 'wsclean -predict -name {0} {1}'.format(abbr_name, self.ms)
        elif self.type == 'skymodel' or self.type == 'sourcedb':
            self._init_pset(abbr_name+'.sourcedb')
            self.call_string = 'DPPP {0}'.format(self.dppp_predict)

    def _printrun(self):
        with open('kittens.fl', 'a') as handle:
            handle.write(self.call_string)

    def execute(self):
        if self.DEBUG:
            self._printrun()
        else:
            self._actualrun()

    def _actualrun(self):
        self.pickle_and_call(self.call_string)
    
    def pickle_and_call(self,x):
        self.log.add_calls(x)
        subprocess.call(x, shell = True)
        self.log.save()

    def check_model_type(self):
        if self.pred_path[-5:] == '.fits':
            return self.pred_path[:-5],'fits'
        elif self.pred_path[-9:] == '.skymodel':
            return self.pred_path[:-9],'skymodel'
        elif self.pred_path[-9:] == '.sourcedb':
            return self.pred_path[:-9],'sourcedb'
        else:
            raise NotImplementedError(
                'Model "{}" is in a non-recognized format'.format(self.pred_path))
    
    def _init_pset(self, sourcedb):
        predict_pset = parse_pset('{}predict.pset'.format(self.pset_loc))
        predict_pset.append('msin={}'.format(self.ms))
        predict_pset.append('predict.sourcedb={}'.format(sourcedb))
        self.dppp_predict = ' '.join(predict_pset)
