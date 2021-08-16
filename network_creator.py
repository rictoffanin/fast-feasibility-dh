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

def read_param(fp):
    # to be defined

def clusterize(buildings, commune):

    buildings = buildings.loc[buildings["fab_tot"] > 0].copy()
    buildings.sort_values("fab_tot", inplace=True, ascending=False, ignore_index=True)

    point = buildings.iloc[0, buildings.columns.get_loc('geometry')]
    radius = 150

    buildings["distance"] = buildings['geometry'].distance(point)
    cluster = buildings.loc[buildings["distance"] < radius].copy()
    cluster = cluster.head(10)
    area = pi * pow(radius, 2)
    density = cluster['fab_tot'].sum() / area
    print("The heat density of the cluster is", "{:.2f}".format(density), "kWh/m2")

    # saving the results in a .csv file
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    folder = "\\output\\processed_data"
    filename = fileDir + folder + "\\cluster-%s.geojson" % commune
    cluster.to_file(filename, driver="GeoJSON", show_bbox=True, indent=4)