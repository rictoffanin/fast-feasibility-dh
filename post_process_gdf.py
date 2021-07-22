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


def get_dataframe(commune):

    filename = "raw_data-%s.csv" % commune
    print("Reading the raw data file: " + filename)
    df = pd.read_csv(filename, low_memory=False)
    buildings = df[['attributes.egid', 'attributes.gebnr', 'attributes.gbez', 'attributes.strname_deinr',
             'attributes.dplzname',
             'attributes.dplz4', 'attributes.ggdename', 'attributes.gkat', 'attributes.gklas', 'attributes.gbaup',
             'attributes.garea', 'attributes.gastw', 'attributes.gkode', 'attributes.gkodn']]

    return buildings


def get_dataframe_gdf(commune):

    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    folder = "\\output\\raw_data"
    filename_json = fileDir + folder + "\\raw-gdf-%s.geojson" % commune
    print("Reading the raw data file: " + filename_json)

    gdf = gpd.read_file(filename_json)
    gdf.set_crs(crs='epsg:21781', inplace=True, allow_override=True)
    buildings = gdf[['geometry', 'egid', 'gebnr', 'gbez', 'strname_deinr',
             'dplzname', 'dplz4', 'ggdename', 'gkat', 'gklas', 'gbaup',
             'garea', 'gastw', 'gkode', 'gkodn']]

    return buildings


def get_demand_coefficients():
    print("Retrieving space heating and domestic hot water demand coefficients.")
    print("The coefficients are taken from SUPSI-DACD-ISAAC report: Mappatura delle aree idonee alle reti di "
          "teleriscaldamento")

    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    folder = "\\support_data"
    filename = fileDir + folder
    # reading consumption data for SH and DHW per type of building and construction time
    data_sh = pd.read_csv(filename+"\\demand_SH.csv", header=0, index_col=0)
    data_dhw = pd.read_csv(filename+"\\demand_DHW.csv", header=0, index_col=0)

    return data_sh, data_dhw


def post_processing(buildings, data_sh, data_dhw, COMMUNE):

    print("Post-processing the raw data file.")
    # renaming the columns of the dataframe
    buildings.set_axis(['geometry', 'EGID', 'mappale', 'nome', 'indirizzo', 'quartiere', 'NPA', 'comune', 'categoria', 'classe',
                        'epoca_costruzione', 'superficie', 'num_piani', 'coord_e', 'coord_n'], axis='columns', inplace=True)
    buildings.sort_values('quartiere', axis='index')
    buildings.drop_duplicates(subset="EGID", keep='first', inplace=True)

    print("Filling blank entries with median or average values.")
    # fill blank entries with median or average values
    buildings['epoca_costruzione'].fillna(buildings['epoca_costruzione'].median(), inplace=True)
    buildings['classe'].fillna(buildings['classe'].median(), inplace=True)
    buildings['superficie'].fillna(buildings['superficie'].mean(), inplace=True)
    buildings['num_piani'].fillna(buildings['num_piani'].median(), inplace=True)

    k_SH = [data_sh.at[int(iRow), str(int(iCol))] for iRow, iCol in
            zip(buildings['epoca_costruzione'], buildings['classe'])]
    k_DHW = [data_dhw.at[int(iRow), str(int(iCol))] for iRow, iCol in
             zip(buildings['epoca_costruzione'], buildings['classe'])]

    print("Calculating the demand of the buildings.")
    # calculating building attributes and demand
    buildings['SRE'] = buildings['superficie']*buildings['num_piani']
    buildings['k_SH'] = k_SH
    buildings['fab_SH'] = k_SH*buildings['SRE']
    buildings['k_DHW'] = k_DHW
    buildings['fab_DHW'] = k_DHW*buildings['SRE']
    buildings['fab_tot'] = buildings['fab_SH'] + buildings['fab_DHW']

    # saving the results in a .csv file
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    folder = "\\output\\processed_data"
    filename = fileDir + folder + "\\data-%s.csv" % COMMUNE
    print("Writing the results file to: " + filename)
    buildings.to_csv(filename, encoding='utf-8-sig', index_label='index')

    return buildings


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


# Main
if __name__ == "__main__":
    # python post_process_gdf.py -com 5192
    print('\nProgram started\n')

    # Input args
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-com', help='commune: number of the Swiss official commune register')

    args = arg_parser.parse_args()
    commune = args.com

    k = get_demand_coefficients()

    b = get_dataframe_gdf(commune)
    # print(b)

    b = post_processing(b, k[0], k[1], commune)

    clusterize(b, commune)

    print('\nProgram ended')
