import requests
import json
import geojson
import pandas as pd
import geopandas as gpd
import dload
import time
import argparse
import sys
import os
from tqdm import trange, tqdm


import constants as c


def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print("\n")
    print(text)
    print("\n")


def save_rea_data(canton, commune):
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    # downloading the list of EGIDs of a commune.
    # the commune must be specified using the federal numbering system (e.g. 5192 is Lugano)
    print("Downloading data from Swiss official commune register for", commune, "(BFS gemeinde-nummer)")
    url = "%s/%s/%s.zip" % (c.ZIP_URL, canton, commune)

    old_stdout = sys.stdout  # backup current stdout
    old_stderr = sys.stderr  # backup current stderr
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")
    folder = "/data_from_rea"
    extraction_path = fileDir + folder
    string = dload.save_unzip(url, extract_path=extraction_path, delete_after=True)
    sys.stdout = old_stdout  # reset old stdout
    sys.stderr = old_stderr  # reset old stderr

    if not string:
        print("The number does not correspond to an existing Swiss commune. The list is available at: "
              "https://www.agvchapp.bfs.admin.ch/it/home")
        print("Please check your inputs and re-run the code")
        print('\nProgram ended')
        exit()

    path = fileDir + folder + "\\%s.csv" % commune

    # parsing the downloaded .csv file
    list_clean = pd.read_csv(path, sep=';')
    list_clean = list_clean['EGID']

    # deleting duplicated entries
    i = list_clean.duplicated(keep='first')
    list_dirty = list_clean.loc[i]
    list_dirty.reset_index(drop=True, inplace=True)
    list_clean.drop_duplicates(keep=False, inplace=True)

    return list_clean, list_dirty


def group_clean_list(list_clean, n=20):
    # creating a list for the lookup by FEATURE_ID. The entries are grouped by 20 EGIDs (max number on the server per
    # request). The FEATURE_ID is usually the EGID followed by the suffix "_0"
    temp = []
    for index, value in list_clean.items():
        temp.append(str(value) + '_0')

    list_clean_grouped = []
    for x in range(0, int(list_clean.count()), n):
        list_clean_grouped.append(','.join(temp[x:x + n]))

    return list_clean_grouped


def download_clean_list(list_clean_grouped, list_dirty):
    # downloading data by group of EGIDs
    print("Downloading data of 'clean' EGIDs")

    for index in trange(0, len(list_clean_grouped)):
        feature_id = list_clean_grouped[index]
        url = "%s/%s/%s" % (c.API_URL, c.DATA_LAYER, feature_id)
        res = requests.get(url)

        if res.status_code == 200:
            temp = json.loads(res.text)
            # jprint(temp)
            if not 'features' in temp or len(temp['features']) == 0:
                print("No data was retrieved. Please enter different inputs")
                print('\nProgram ended')
                exit()
        elif res.status_code == 404:

            while res.status_code == 404:
                # extrapolating the problematic EGID
                i_a = res.text.find('id')+3
                i_b = res.text.rfind("_")+2
                i_c = res.text.rfind("_")
                egid_id = res.text[i_a:i_b]
                egid_id.strip()
                list_dirty.loc[list_dirty.count()] = res.text[i_a:i_c]
                feature_id = feature_id.replace(egid_id + ',', '')
                url = "%s/%s/%s" % (c.API_URL, c.DATA_LAYER, feature_id)
                res = requests.get(url)

        url = "%s/%s/%s?geometryFormat=geojson" % (c.API_URL, c.DATA_LAYER, feature_id)
        res = requests.get(url)
        temp = json.loads(res.text)
        # print(temp)
        temp_gdf = gpd.GeoDataFrame.from_features(temp)
        # print(temp_gdf)

        if index < 1:
            gdf = temp_gdf.copy()
        else:
            gdf = gdf.append(temp_gdf)

    list_dirty.drop_duplicates(keep='first', inplace=True)
    gdf.reset_index(drop=True, inplace=True)

    return gdf, list_dirty


def download_dirty_list(list_dirty, gdf, commune):
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    # downloading data by single EGID (for problematic entries)
    print("Downloading data of 'dirty' EGIDs (names that needed post-processing for retrieval)")

    with tqdm(total=list_dirty.count()) as pbar:
        for index, value in list_dirty.items():
            src_text = str(value)
            main_url = "%s/find?layer=%s&searchText=%s&searchField=%s&geometryFormat=geojson" % (c.API_URL, c.DATA_LAYER, src_text, c.SRC_FIELD)
            param_url = "&contains=false" #% c.SR
            url = main_url + param_url
            # print(url)
            res = requests.get(url)
            temp = json.loads(res.text)
            temp['type'] = "FeatureCollection"
            temp['features'] = temp['results']

            # jprint(temp['features'])
            if len(temp['results']) > 0:
                temp_gdf = gpd.GeoDataFrame.from_features(temp["features"])
                gdf = gdf.append(temp_gdf)

            pbar.update(1)

    gdf.reset_index(drop=True, inplace=True)
    gdf.set_crs(crs='epsg:21781', inplace=True)

    print("Download ended")

    return gdf


def gdf_to_file(gdf, commune):
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    folder = "\\output\\raw_data"
    filename_json = fileDir + folder + "\\raw-gdf-%s.geojson" % commune
    gdf_json = gdf.to_json(indent=4)

    with open(filename_json, "w") as text_file:
        text_file.write(gdf_json)

    filename_csv = fileDir + folder + "\\raw-gdf-%s.csv" % commune
    gdf.to_csv(filename_csv)

    print("The dataframe containing the raw data was written to: " + fileDir + "\\" + filename_json)

    return gdf

# todo: aggiungere la creazione di un immagine con gli edifici colorati per consumo


# Main
if __name__ == "__main__":
    # python download_rea_gdf.py -can TI -com 5195

    print('\nProgram started\n')

    # Input args
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-can', help='canton: two-letter acronym')
    arg_parser.add_argument('-com', help='commune: number of the Swiss official commune register')

    args = arg_parser.parse_args()
    canton = args.can
    commune = args.com

    clean_list, dirty_list = save_rea_data(canton, commune)

    clean_list_grouped = group_clean_list(clean_list)

    gdf, dirty_list = download_clean_list(clean_list_grouped, dirty_list)

    gdf = download_dirty_list(dirty_list, gdf, commune)

    gdf_to_file(gdf, commune)

    print('\nProgram ended')

