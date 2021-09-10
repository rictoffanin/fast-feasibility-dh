import osmnx as ox
import matplotlib.pyplot as plt
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import LineString, Point, MultiLineString
from geopandas.tools import geocode
from shapely.ops import unary_union
import os
import argparse
import pandas as pd
from shapely import wkt
import numpy as np
import contextily as cx
from pathlib import Path


def network_finder(file_suffix, addr, distance):
    # todo: separate in smaller functions

    def get_graph_from_address(addr_arg, osm_net_type="walk", epsg_num=21781):
        # fetch OSM street network from the location
        g = ox.graph_from_address(addr_arg, simplify=False, dist=distance+50, network_type=osm_net_type)
        # project the graph
        g = ox.project_graph(g, to_crs=CRS.from_epsg(epsg_num))

        return g

    graph = get_graph_from_address(addr)

    def get_nodes_edges_from_graph(g, epsg_num=21781):
        # retrieve nodes and edges
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(g)
        # Project nodes and edges
        nodes_gdf.to_crs(CRS.from_epsg(epsg_num), inplace=True)
        edges_gdf.to_crs(CRS.from_epsg(epsg_num), inplace=True)

        return nodes_gdf, edges_gdf

    nodes, edges = get_nodes_edges_from_graph(graph)

    def get_buildings_from_address(addr_arg):
        # tags for buildings
        tags = {'building': True}
        # Retrieve buildings with a defined distance in meters from address
        b = ox.geometries_from_address(addr_arg, tags, dist=distance+50)
        # Project the buildings
        b.to_crs(CRS.from_epsg(21781), inplace=True)

        return b

    buildings = get_buildings_from_address(addr)

    # Read the file containing the info regarding the buildings
    fn = fileDir + "\\output\\results\\" + "cluster" + file_suffix + ".geojson"
    users = gpd.read_file(fn, driver="GeoJSON")

    # geocoding the address
    orig_coords = ox.geocoder.geocode(addr)  # (lat, lng) but gpd accepts (lng, lat)

    def define_origin(users_gdf, epsg_num=21781):
        # the origin is the building closest to the geocoded address
        org = users_gdf["geometry"].values[users_gdf['distance'].idxmin()]
        # creating a GDF from the origin for easier plotting
        org_geo = gpd.GeoDataFrame({'geometry': [org]}, crs=epsg_num)

        return org, org_geo

    origin, origin_geo = define_origin(users, epsg_num=21781)

    def define_destination(users_gdf, epsg_num=21781):
        # defining the location of the users as the destinations
        dest = users["geometry"].values[:]
        # creating a GDF from the destinations for easier plotting
        dest_geo = gpd.GeoDataFrame({'geometry': dest}, crs=epsg_num)

        return dest, dest_geo

    destination, destination_geo = define_destination(users)

    def get_nearest_nodes(g, x, y):
        node_ids = ox.distance.nearest_nodes(g, x, y)
        return node_ids

    # Find the node in the graph that is closest to the origin point (node id)
    orig_node_id = get_nearest_nodes(graph, origin.x, origin.y)

    # Find the node in the graph that is closest to the target points (node id)
    target_node_id = get_nearest_nodes(graph, destination.x, destination.y)

    def compare_length_origin_destination(org_node_ids, trg_node_ids):
        assert type(org_node_ids) is int, "The length of the origin node IDs is %s" % len(org_node_ids)
        assert len(trg_node_ids) >= 1, "The length of the destination node IDs is %s" % len(trg_node_ids)
        # duplicated the orig_node_id so that it has the same lengths of target_node_id
        orig_node_id_single = org_node_ids
        org_node_ids = [orig_node_id_single for x in range(len(trg_node_ids))]

        return org_node_ids, trg_node_ids

    orig_node_id, target_node_id = compare_length_origin_destination(orig_node_id, target_node_id)

    # Calculate the shortest paths (route contains the node IDs of the graph)
    route = ox.shortest_path(G=graph, orig=orig_node_id, dest=target_node_id, weight='length')

    # todo: check if it is necessary
    # finding the index of None from list (None = no path found)
    # index = [i for i, e in enumerate(route) if e is None]
    #
    # # workaround for creating fake paths for user with no path found
    # for idx in index:
    #     route[idx] = [orig_node_id[idx], orig_node_id[idx]]
    #     # destination.loc[idx] = origin.loc[0]
    #     # destination.loc[idx] = origin
    #     # users.drop(idx, inplace=True)

    # creating a list containing every paths from origin to destination
    # route_lines = []
    # for i in route:
    #     if len(list(nodes.loc[i].geometry.values)) < 2:
    #         i = [i[0], i[0]]
    #     route_lines.append(LineString(list(nodes.loc[i].geometry.values)))

    def create_route_paths(r, n):
        # creating a list containing every paths from origin to destination
        r_lines = []
        for i in r:
            if len(list(n.loc[i].geometry.values)) < 2:
                i = [i[0], i[0]]
            r_lines.append(LineString(list(n.loc[i].geometry.values)))
        return r_lines

    route_lines = create_route_paths(route, nodes)

    # work-around to append each origin and destination to every path
    r_od = []
    for idx in range(len(route_lines)):
        temp = []
        temp.append(origin)
        for coord in route_lines[idx].coords:
            temp.append(coord)
        temp.append(destination[idx])

        line = LineString(temp)
        r_od.append(line)

        del temp

    # unary_union allows to separate the line into segments and remove duplicates
    network = unary_union(r_od)

    # creating geodataframe containing the branches of the network
    network = gpd.GeoDataFrame(network, columns=['geometry'], crs=nodes.crs)
    # calculate the route length
    network['length'] = network['geometry'].length

    # creating a geodataframe with the linestring of every paths from origin to destination
    paths = gpd.GeoDataFrame(r_od, crs=edges.crs, columns=['geometry'])
    # calculate the route length
    paths['length_m'] = paths.length

    users["path"] = paths["geometry"]
    users["path_length"] = paths["length_m"]

    plot(edges, nodes, buildings, users, network, paths, origin_geo, destination)

    return users, network


def kpi_calc(file_suffix, addr, r, users, network, type_dhn):
    # the convex hull of the users is used to calculate the land area
    convex_hull = users['geometry'].unary_union.convex_hull
    land_area = convex_hull.area

    # calculating the SPATIAL HEAT DENSITY (SHD) in kWh/m2 per year
    shd = users['fab_tot'].sum() / land_area
    shd = shd * 10  # conversion to MWh / ha

    # calculating the maximum BUILDING HEAT DENSITY in kWh/m2 per year
    bhd_max = users['k_SH'].max() + users.loc[users['k_SH'].idxmax(), 'k_DHW']
    # calculating the maximum BUILDING HEAT DENSITY in kWh/m2 per year
    bhd_min = users['k_SH'].min() + users.loc[users['k_SH'].idxmin(), 'k_DHW']
    # calculating the average BUILDING HEAT DENSITY in kWh/m2 per year
    bhd_ave = users['fab_tot'].sum() / users['SRE'].sum()

    # calculating the LINEAR HEAT DENSITY in kWh/m
    lhd_energy = users['fab_tot'].sum() / network['length'].sum()
    # calculating the LINEAR HEAT DENSITY in kW/m
    lhd_power = users['P_tot'].sum() / network['length'].sum()

    res = suitability(shd, bhd_ave)
    dict_kpi = {
        'origin': addr, 'radius': r, 'n_buildings': len(users), 'length': network['length'].sum(),
        'land_area': land_area, 'building_area': users['SRE'].sum(),
        'bhd': bhd_ave, 'shd': shd, 'lhd_energy': lhd_energy, 'lhd_power': lhd_power, "suitable-for": res,
    }

    kpi = pd.DataFrame([dict_kpi], index=[type_dhn])

    return kpi


def write_data_to_file(data, folder, name, suffix):

    fileDir = os.path.dirname(os.path.abspath(__file__)) + folder + suffix + "\\"
    Path(fileDir).mkdir(parents=True, exist_ok=True)

    fn = fileDir + name + ".csv"
    data.to_csv(fn, sep=";", encoding='utf-8-sig', index_label='index')


def plot(edges, nodes, buildings, users, network, route_geom, origin_geo, destination):
    edges_wm = edges.to_crs(epsg=3857)
    nodes_wm = nodes.to_crs(epsg=3857)
    buildings_wm = buildings.to_crs(epsg=3857)
    cluster_wm = users.to_crs(epsg=3857)
    network_wm = network.to_crs(epsg=3857)
    route_geom_wm = route_geom.to_crs(epsg=3857)
    # dest_nodes_wm = dest_nodes.to_crs(epsg=3857)
    # orig_nodes_wm = orig_nodes.to_crs(epsg=3857)
    origin_geo_wm = origin_geo.to_crs(epsg=3857)
    destination_wm = destination.to_crs(epsg=3857)

    # define figure and subplots
    fig, ax = plt.subplots()

    # plot edges and nodes
    # ax = edges_wm.plot(linewidth=0.75, color='gray')
    # ax = nodes_wm.plot(ax=ax, markersize=2, color='gray')

    # add buildings from OpenStreetMap
    ax = buildings_wm.plot(ax=ax, facecolor='khaki', alpha=0.00)

    # add cluster of users

    ax = cluster_wm.plot(ax=ax, markersize=32, color='forestgreen')

    # add the route
    # ax = route_geom_wm.plot(ax=ax, linewidth=4, linestyle='--', color='red')
    ax = network_wm.plot(ax=ax, linewidth=2, linestyle='solid', color='darkred')

    # add the origin and destination nodes of the route
    # ax = dest_nodes_wm.plot(ax=ax, markersize=12, color='green')
    # ax = orig_nodes_wm.plot(ax=ax, markersize=48, color='black')
    ax = origin_geo_wm.plot(ax=ax, markersize=64, color='black')
    # ax = destination_wm.plot(ax=ax, markersize=1, color='green')

    cx.add_basemap(ax, source=cx.providers.OpenStreetMap.CH, zoom=17, alpha=0.8)
    # ax.set_axis_off()
    plt.show()


def suitability(shd, bhd):
    if shd < 100:
        if bhd < 40:
            # print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS")
            out_str = "IHS"
        elif 40 <= bhd <= 60:
            # print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS/LTDH/HTDH")
            out_str = "IHS/LTDH/HTDH"
        elif bhd > 60:
            # print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS")
            out_str = "IHS"
    elif 100 <= shd <= 200:
        if bhd < 40:
            # print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS/LTDH")
            out_str = "IHS/LDTH"
        elif 40 <= bhd <= 60:
            # print("The network might be suitable for LTDH/HTDH")
            out_str = "LTDH/HTDH"
        elif bhd > 60:
            # print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS/HTDH")
            out_str = "IHS/HTDH"
    elif shd > 200:
        if bhd < 40:
            # print("The network might be suitable for LTDH")
            out_str = "LTDH"
        elif 40 <= bhd <= 60:
            # print("The network might be suitable for LTDH/HTDH")
            out_str = "LTDH/HTDH"
        elif bhd > 60:
            # print("The network might be suitable for HTDH")
            out_str = "HTDH"

    return out_str


# Main
if __name__ == "__main__":
    # python topology_finder.py -addr "Via La Santa 1, Lugano, Svizzera" -r 250 -n 10 -t LTDHN

    from user_finder import com_num, clusterize
    from economics import economic_calc, parameters_with_calc, lcoh_calculator

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
    point = {'geometry': [p]}
    point = gpd.GeoDataFrame(point, crs='epsg:21781')

    # saving the results in a .csv file
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    x_coord = round(point.geometry.x.values[0], 3)
    y_coord = round(point.geometry.y.values[0], 3)

    folder = "\\output\\results"
    suffix = "-%s-x%s-y%s-r%s-n%s-%s" % (gmd, x_coord, y_coord, int(radius), n_max, net_type)
    c, net = network_finder(suffix, address, radius)

    res_kpi = kpi_calc(suffix, address, radius, c, net, net_type)
    write_data_to_file(res_kpi, "\\output\\results", "network-energy-kpi", suffix)
    write_data_to_file(c, "\\output\\results", "users", suffix)
    write_data_to_file(net, "\\output\\results", "network", suffix)

    print('\nProgram ended\n')
