#!/usr/bin/env python2.7
import os
import sys
import wget
import tarfile
import argparse
import shutil
import subprocess

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

def close_run(rname, ms):
    assert rname[-1] == '/'
    assert ms[-1] == '/'
    try:
        os.mkdir('runs/{}instruments'.format(rname))
    except OSError:
        pass
    try:
        os.mkdir('runs/{}models'.format(rname))
    except OSError:
        pass
    dirlist = os.listdir('measurements/{}'.format(ms))
    instruments = list(filter(lambda x: 'instrument' in x, dirlist))
    for inst in instruments:
        shutil.copy2('measurements/{0}{1}'.format(ms,inst), 'runs/{0}instruments/{1}'.format(rname,inst))
    os.copytree('models/', 'runs/{}models'.format(rname))
    if False:
        # Copy the measurement set compressed. You can re-gain the correction
        # by applying the applycal step again
        callstring = 'DPPP msin=measurements/{0} msout=runs/{1}{0} msout.storagemanager=dysco msout.datacolumn=DATA msin.datacolumn=DATA'.format(ms, rname)
        subprocess.call(callstring, shell = True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('step', help = 'What do you want to do?', default = 'help')
    parser.add_argument('folders', nargs = '*' , default = os.getcwd())
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
    elif step == 'closerun':
        close_run(fname,folder2)
    else:
        raise NotImplementedError
    
    

if __name__ == '__main__':
    main()
