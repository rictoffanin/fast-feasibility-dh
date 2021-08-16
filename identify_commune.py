import requests
import json
import geojson
import dload
import time
import argparse
import sys
import os

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopandas.tools import geocode

# absFilePath = os.path.abspath(__file__)
# fileDir = os.path.dirname(os.path.abspath(__file__))
# parentDir = os.path.dirname(fileDir)

def commune_number_from_address(address):

    geo = geocode(addr, provider='nominatim', user_agent='autogis_xx', timeout=4)

    coords = str(geo.loc[0, 'geometry'].x) + "," + str(geo.loc[0, 'geometry'].y)

    url = 'https://api3.geo.admin.ch/rest/services/api/MapServer/identify?'
    params = dict(
        sr='4326',
        geometryType='esriGeometryPoint',
        geometry=coords,
        imageDisplay='0,0,0',
        mapExtent='0,0,0,0',
        tolerance='0',
        layers='all:ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill'
        )

    # Fetch data from WFS using requests
    res = requests.get(url, params=params)
    temp = json.loads(res.text)
    gmd_nbr = temp['results'][0]['id']
    print("The official municipality number of the address", address, "is", gmd_nbr)

# Main
if __name__ == "__main__":
    # python identify_commune.py -addr "Via La Santa 1, Lugano, Ticino, Svizzera"

    print('\nProgram started\n')

    # Input args
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-addr', help='address example: Via La Santa 1, Lugano, Ticino, Svizzera')

    args = arg_parser.parse_args()
    addr = args.addr

    commune_number_from_address(addr)

    print('\nProgram ended')
