import os
import wget
import tarfile
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', help = 'Name of your new lab folder')
    parsed = parser.parse_args()

    fname = parsed.folder
    assert fname[-1] == '/'
    os.mkdir(fname)
    os.mkdir('{}/measurements'.format(fname))
    os.mkdir('{}/runs'.format(fname))
    os.mkdir('{}/images'.format(fname))

    parset_name  = wget.download('https://home.strw.leidenuniv.nl/~groeneveld/parsets.tar.gz')
    print(parset_name)
    tf = tarfile.open(parset_name)
    tf.extractall(fname)
    tf.close()
    os.remove(parset_name)

if __name__ == '__main__':
    main()
