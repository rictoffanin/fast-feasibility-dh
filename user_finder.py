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


def clusterize(buildings, commune, radius, point, n, type_dhn):

    assert type_dhn == 'LTDHN' or 'HTDHN', "The network type must be 'LTDHN' or 'HTDHN'"

    buildings = buildings.loc[buildings["fab_tot"] > 0].copy()

    point = {'geometry': [point]}
    # point = buildings.iloc[0, buildings.columns.get_loc('geometry')]
    point = gpd.GeoDataFrame(point, crs='epsg:21781')
    # point.to_crs(CRS.from_epsg(21781), inplace=True)

    buildings["distance"] = buildings['geometry'].distance(point.loc[0, 'geometry'])
    buildings.sort_values("fab_tot", inplace=True, ascending=False, ignore_index=True)

    if type_dhn == "LTDHN":
        buildings = buildings.loc[buildings["k_SH"] < 60].copy()

    cluster = buildings.loc[buildings["distance"] < radius].copy()
    cluster = cluster.head(n)
    cluster.sort_values("distance", inplace=True, ignore_index=True)

    # area = pi * pow(radius, 2)
    convex_hull = cluster['geometry'].unary_union.convex_hull

    land_heat_density = cluster['fab_tot'].sum() / convex_hull.area
    # print("The land heat density of the cluster is", "{:.2f}".format(land_heat_density), "kWh/m2 =", "{:.2f}".format(land_heat_density*10), "MWh/ha")
    # print("The value should be higher than 350 MWh/ha.")

    building_heat_density = cluster['fab_tot'].sum() / cluster['SRE'].sum()
    # print("The building heat density of the cluster is", "{:.2f}".format(building_heat_density), "kWh/m2 per year")
    # print("The value should be higher than 70 kWh/m2 per year.")

    # saving the results in a .csv file
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    x_coord = round(point.geometry.x.values[0], 3)
    y_coord = round(point.geometry.y.values[0], 3)

    folder = "\\output\\results"
    filename = fileDir + folder + "\\cluster-%s-x%s-y%s-r%s-n%s-%s.geojson" % (commune, x_coord, y_coord, int(radius), n, type_dhn)
    cluster.to_file(filename, driver="GeoJSON", show_bbox=True, indent=4)
    print("Writing the results file to:", filename)


def check_origin_within(pnt, df):
    convex_hull = df['geometry'].unary_union.convex_hull
    assert pnt.within(convex_hull), "Address is not within the area (convex hull) of the buildings"
    print("Address is within the area (convex hull) of the buildings")


# Main
if __name__ == "__main__":
    # python user_finder.py -addr "Via La Santa 1, Lugano, Svizzera" -r 250 -n 10 -t LTDHN

    # fixme: given a file with processed data, check if the address is within the area, then find the most suitable
    #  users for the type of the network within the radius
    print('\nProgram started\n')

    # Input args
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-addr', help='address of the generation plant')
    arg_parser.add_argument('-r', help='radius in meters around the generation plant', type=float)
    arg_parser.add_argument('-n', help='maximum number of customers in the network', type=int)
    arg_parser.add_argument('-t', help='type: low-temperature (LTDHN) or high-temperature (HTDHN) district heating')

    args = arg_parser.parse_args()
    address = args.addr
    radius = args.r
    n_max = args.n
    net_type = args.t

    gmd, p = com_num(address)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    fp = fileDir + "\\output\\processed_data\\data-" + str(gmd) + ".csv"

    temp = pd.read_csv(fp, sep=";", index_col='index')
    temp['geometry'] = temp['geometry'].apply(wkt.loads)
    b = gpd.GeoDataFrame(temp, crs='epsg:21781')

    check_origin_within(p, b)

    clusterize(b, gmd, radius, p, n_max, net_type)

    print('\nProgram ended\n')