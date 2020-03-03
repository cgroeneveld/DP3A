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

def execute_run(rname):
    assert rname[-1] == '/'
    executefile = '{}parsets/execute'.format(rname)
    execlist = []
    with open(executefile, 'r') as handle:
        for line in handle:
            execlist.append(line.rstrip('\n'))
    mslist = os.listdir('measurements')
    modellist = os.listdir('models')
    if len(mslist) != 1 or len(modellist) != 1:
        raise IOError('There should only be one model and measurement set available, otherwise we can\'t autorun DP5')
    else:
        execstring = 'DP5.py -ms measurements/{0}/ -p {1} -m models/{2} -s {3} -path_wd'.format(mslist[0], rname, modellist[0], execlist[0])
        subprocess.call(execstring, shell = True)

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
        execute_run(fname)
    else:
        raise NotImplementedError
    
    

if __name__ == '__main__':
    main()
