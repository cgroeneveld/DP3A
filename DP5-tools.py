#!/usr/bin/env python2.7
import os
import sys
import wget
import tarfile
import argparse
import shutil

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
                help       |  Print this message
        ''')
    elif step == 'init':
        init_folder(fname)
    elif step == 'newrun':
        init_run(fname)
    elif step == 'copyrun':
        copy_run(fname,folder2)
    else:
        raise NotImplementedError
    
    

if __name__ == '__main__':
    main()
