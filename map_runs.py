import run
import os
import argparse
import multiprocessing as mp

RUNSTRING = 'uppdd'

def single_reduction(combi_tuple):
    ms, p, s, m, n = combi_tuple
    fp = run.FakeParser(ms+n, p+n, s, False, True, m)
    print(fp)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Maps DP3A on several ms at the same time')
    parser.add_argument('-r', type = str, help = 'Location of the root directory containing the measurement sets')
    parser.add_argument('-p', type = str, help = 'Location of the root run directory')
    parser.add_argument('-m', type = str, help = 'Location of the model')

    parsed = parser.parse_args()
    assert parsed.r[-1] == '/'
    assert parsed.p[-1] == '/'
    dirlist = os.listdir(parsed.r)
    number_dirs = []
    for val in dirlist:
        try:
            _ = int(val)
            number_dirs.append(val)
        except ValueError:
            pass
    
    pl = mp.Pool(mp.cpu_count())
    combi_tuples = []
    for n in number_dirs:
        combi_tuples.append((parsed.r, parsed.p, RUNSTRING, parsed.m, n))
    pl.map(single_reduction, combi_tuples)