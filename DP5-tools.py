#!/usr/bin/env python2.7
import os
import sys
import wget
import tarfile
import argparse
import shutil
import subprocess
import datetime
import re

def init_folder(fname):
    assert fname[-1] == '/'
    os.mkdir(fname)
    os.mkdir('{}/measurements'.format(fname))
    os.mkdir('{}/models'.format(fname))
    os.mkdir('{}/runs'.format(fname))
    os.mkdir('{}/images'.format(fname))

def init_run(rname):
    assert rname[-1] == '/'
    os.mkdir('runs/{}'.format(rname))
    parset_name  = wget.download('https://home.strw.leidenuniv.nl/~groeneveld/parsets.tar.gz')
    print(parset_name)
    tf = tarfile.open(parset_name)
    tf.extractall('runs/{}'.format(rname))
    tf.close()
    os.remove(parset_name)


def copy_run(rnamefrom, rnameto):
    assert rnamefrom[-1] == '/'
    assert rnameto[-1] == '/'
    os.mkdir('runs/{}'.format(rnameto))
    shutil.copytree('runs/{}/parsets'.format(rnamefrom), 'runs/{}/parsets'.format(rnameto))

def copy_images(rname):
    assert rname[-1] == '/'
    shutil.copytree('runs/{}IMAGES'.format(rname), 'images/{}'.format(rname))

def copy_losotoplots(ms_root, calibration):
    names = os.listdir(ms_root)
    dirl = [ms_root+dirry+'/losoto/'+calibration for dirry in names]
    if 'ap' in calibration:
        for ms_name, path in zip(names,dirl):
            ampplotname = list(filter(lambda x: 'amp' in x and 'XX' in x, os.listdir(path)))[0]
            shutil.copyfile(path+'/prephasedirpointing_polXX.png', 'p{}.png'.format(ms_name))
            shutil.copyfile(path+'/'+ampplotname, 'a{}.png'.format(ms_name))
    else:
        # So phase only calibration
        for ms_name, path in zip(names,dirl):
            shutil.copyfile(path+'/dirpointing_polXX.png', '{}.png'.format(ms_name))

def execute_run(rname, noms = False, nocompress = False, savesky = False, multims = False):
    assert rname[-1] == '/'
    if multims:
        nocompress = True
    executefile = '{}parsets/execute'.format(rname)
    execlist = []
    with open(executefile, 'r') as handle:
        for line in handle:
            execlist.append(line.rstrip('\n'))
    mslist = os.listdir('measurements')
    modellist = os.listdir('models')

    iso_date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
    logname = 'DP5_{}.log'.format(iso_date)

    if len(modellist) != 1:
        raise IOError('There should only be one model available, otherwise we can\'t autorun DP5')
    else:
        # Copy measurements folder
        shutil.copytree('measurements/', '{}/measurements/'.format(rname))
        for ms in mslist:
            os.mkdir('{0}/measurements/{1}/losoto'.format(rname,ms))
        # Run DP5.py
        if len(mslist) == 1:
            execstring = 'DP5.py -y -ms {1}/measurements/{0}/ -p {1} -m models/{2} -s {3} -path_wd | tee {4}'.format(mslist[0], rname, modellist[0], execlist[0], logname)
        else:
            execstring = 'DP5.py -y -ms {0}/measurements/ -p {0} -m models/{1} -s {2} -path_wd -multims | tee {3}'.format(rname, modellist[0], execlist[0], logname)
        subprocess.call(execstring, shell = True)
        # If -no-ms is given, run another wsclean run
        if noms or savesky:
            print('==== RUNNING NOMS WSCLEAN')
            with open('{}parsets/imaging.sh'.format(rname), 'r') as handle:
                base_image = handle.read()[:-2]
            os.mkdir('{}/noms'.format(rname))
            if os.path.isfile('{}parsets/casamask.fits'.format(rname)):
                fulimg = '{0} -data-column CORRECTED_DATA2 -fits-mask {1}parsets/casamask.fits -name {1}noms/ws '.format(base_image, rname)
            else:
                fulimg = '{0} -data-column CORRECTED_DATA2 -auto-mask 5 -auto-threshold 1.5 -name {1}noms/ws '.format(base_image, rname)
            if noms:
                fulimg += '-no-mf-weighting '
            if savesky:
                fulimg += '-save-source-list -fit-spectral-log-pol 3 '
            ms_appendices = ['{0}/measurements/{1}'.format(rname, ms) for ms in mslist]
            fulimg +=  ' '.join(ms_appendices)
            subprocess.call(fulimg, shell = True)
            shutil.copyfile('{}/noms/ws-MFS-image.fits'.format(rname), '{}/IMAGES/noms.fits'.format(rname))
        # Run DP5-compress - lets not do this
        # Does not (fully) support multi-ms runs yet
        # if not nocompress:
            # print('==== RUNNING DP5-COMPRESS')
            # subprocess.call('DP5-compress.py -ms {1}/measurements/{0}/ -r {1}'.format(mslist[0],rname), shell = True)
        # Remove instruments
        print('==== REMOVING INSTRUMENTS')
        '''
        for ms in mslist:
            ms_loc = '{0}/measurements/{1}'.format(rname,ms)
            instruments = list(filter(lambda x: 'instrument' in x, os.listdir(ms_loc)))
            instrument_locs = ['{2}/measurements/{0}/{1}'.format(ms, inst, rname) for inst in instruments]
            for inst in instrument_locs:
                os.remove(inst)
        '''
        # copy images
        print('==== COPYING IMAGES')
        run_name_nopref = re.sub(r'.*/','/',rname.rstrip('/'))
        os.mkdir('images/{}'.format(run_name_nopref))
        imgs = os.listdir('{}IMAGES'.format(rname))
        imgs_old = ['{0}IMAGES/{1}'.format(rname, img) for img in imgs]
        imgs_new = ['images/{0}/{1}'.format(run_name_nopref, img) for img in imgs]
        for old,new in zip(imgs_old, imgs_new):
            shutil.copyfile(old,new)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('step', help = 'What do you want to do?', default = 'help')
    parser.add_argument('folders', nargs = '*' , default = os.getcwd())
    parser.add_argument('-no-ms', help = 'Add an additional imaging run without MF weighting',action='store_true', dest = 'noms')
    parser.add_argument('-no-compress', help = "Don't run DP5-compress afterwards",action = 'store_true', dest = 'nocomp')
    parser.add_argument('-save-sources', help = "Saves a skymodel afterwards", action = 'store_true', dest = 'savesky')
    parser.add_argument('-multi-ms', help = "Run with multi measurement sets", action = 'store_true', dest = 'multims')
    parsed = parser.parse_args()

    step = parsed.step
    fname = parsed.folders[0]
    try:
        folder2 = parsed.folders[1]
    except IndexError:
        folder2 = 'run'
    
    if step == 'help':
        print('''
                The following tools are supported:
                init       |  Initializes a laboratory folder. Requires a folder
                           |  name directly following. The laboratory is empty
                newrun     |  Creates a new run in the current laboratory.
                           |  Requires a name for the run. Should be initialized
                           |  in the root folder of the laboratory
                copyrun    |  Copies the parsets from a previous run to a new
                           |  run. Needs the name of the new run and the old run.
                copyimg    |  Copies all images to the image-folder. Not necessary,
                           |  just makes your life easier
                execute    |  Execute the parameters that are loaded in parsets/
                           |  execute
                help       |  Print this message
        ''')
    elif step == 'init':
        init_folder(fname)
    elif step == 'newrun':
        init_run(fname)
    elif step == 'copyrun':
        copy_run(fname,folder2)
    elif step == 'copyimg':
        copy_images(fname)
    elif step == 'execute':
        execute_run(fname,parsed.noms,parsed.nocomp,parsed.savesky, parsed.multims)
    elif step == 'losotocopy':
         copy_losotoplots(fname, folder2)
    else:
        raise NotImplementedError
    
    
if __name__ == '__main__':
    main()
