import requests
import json
import pandas as pd
import geopandas as gpd
import argparse
from math import pi, pow
import dload
import time
import os
from tqdm import trange, tqdm
from identify_commune import commune_number_from_address as com_num
from shapely import wkt
from shapely.geometry import Point
from pyproj import CRS
from matplotlib import pyplot as plt

def read_param(fn):

    absFilePath = os.path.abspath(__file__)
    fd = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fd)

    fp = fd + "\\support_data\\" + fn

    # Opening JSON file
    f = open(fp)
    # returns JSON object as a dictionary
    param = json.load(f)
    # Closing file
    f.close()

    print(param)

    return param


def clusterize(buildings, commune, radius, point, n):

    buildings = buildings.loc[buildings["fab_tot"] > 0].copy()

    point = {'geometry': [point]}
    # point = buildings.iloc[0, buildings.columns.get_loc('geometry')]
    point = gpd.GeoDataFrame(point, crs='epsg:4326')
    point.to_crs(CRS.from_epsg(21781), inplace=True)

    buildings["distance"] = buildings['geometry'].distance(point.loc[0, 'geometry'])

    cluster = buildings.loc[buildings["distance"] < radius].copy()
    cluster = cluster.head(n)

    buildings.sort_values("fab_tot", inplace=True, ascending=False, ignore_index=True)

    area = pi * pow(radius, 2)
    convex_hull = cluster['geometry'].unary_union.convex_hull
    density = cluster['fab_tot'].sum() / convex_hull.area
    print("The heat density of the cluster is", "{:.2f}".format(density), "kWh/m2")

    plt.show()

    # saving the results in a .csv file
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    folder = "\\output\\processed_data"
    filename = fileDir + folder + "\\cluster-%s.geojson" % commune
    cluster.to_file(filename, driver="GeoJSON", show_bbox=True, indent=4)

# Main
if __name__ == "__main__":
    # python network_creator.py -addr "Via La Santa 1, Lugano, Svizzera" -r 100 -n 10

    print('\nProgram started\n')

    # Input args
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-addr', help='address of the generation plant')
    arg_parser.add_argument('-r', help='radius in meters around the generation plant', type=float)
    arg_parser.add_argument('-n', help='maximum number of customers in the network', type=int)
    # arg_parser.add_argument('-com', help='commune: number of the Swiss official commune register')

    args = arg_parser.parse_args()
    address = args.addr
    radius = args.r
    n_max = args.n
    # commune = args.com

    gmd, p = com_num(address)
    fp = "D:\SUPSI\geodata-ch\src\output\processed_data\data-" + str(gmd) + ".csv"

    temp = pd.read_csv(fp, sep=";", index_col='index')
    temp['geometry'] = temp['geometry'].apply(wkt.loads)
    b = gpd.GeoDataFrame(temp, crs='epsg:21781')
    # print(b.head())

    clusterize(b, gmd, radius, p, n_max)


    print('\nProgram ended\n')