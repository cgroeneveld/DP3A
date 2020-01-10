import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Maps DP3A on several ms at the same time')
    parser.add_argument('-r', type = str, help = 'Location of the root directory containing the measurement sets')

    parsed = parser.parse_args()
    dirlist = os.listdir(parsed.r)
    print(dirlist)
    for val in dirlist:
        print(int(val))
