def parse_pset(fname):
    with open(fname, 'r') as handle:
        data = [line for line in handle]
    # Just some formatting
    data = [x.rstrip('\n') for x in data]
    data = list(filter(lambda x: x != '', data))
    # Raise an error if we manually define the h5parm
    newdata = []
    for x in data:
        if 'h5parm' in x:
            raise ValueError('Please do not define your own h5parm. We will do that for you.')
        elif 'msin = ' in x:
            raise ValueError('Please do not define msin - we do that ourselves')
        elif 'msout.datacolumn' in x:
            raise ValueError('Please do not define msout.datacolumn - we do that ourselves')
        else:
            newdata.append(''.join(list(filter(lambda y: y != ' ', x))))
    return newdata