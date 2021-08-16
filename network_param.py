import argparse
import json
import os


def write_network_param(r, n):

    assert type(r) in [int, float], "Input 'r' needs to be integer or floating point number! Found: %s" % type(r)
    assert type(n) in [int, float], "Input 'n' needs to be integer or floating point number! Found: %s" % type(n)
    param = {"radius": r, "n_max_user": n}
    # json_object = json.loads(param)
    # the json file where the output must be stored

    fd = os.path.dirname(os.path.abspath(__file__)) + r'\support_data'
    fp = fd +  r'\param.json'
    out_file = open(fp, "w")
    json.dump(param, out_file, indent=4)
    out_file.close()
    print('The network parameters were written to', fp)



# Main
if __name__ == "__main__":
    # python network_param.py -r 100 -n 10

    print('\nProgram started\n')

    # Input args
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-r', help='radius in meters around the generation plant', type=float)
    arg_parser.add_argument('-n', help='maximum number of customers in the network', type=float)

    args = arg_parser.parse_args()
    radius = args.r
    n_max = args.n

    write_network_param(radius, n_max)

    print('\nProgram ended\n')