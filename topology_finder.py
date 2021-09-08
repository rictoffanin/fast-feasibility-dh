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


def network_finder(filename, address, distance):

    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    # Get place boundary related to the place name as a geodataframe
    # area = ox.geocode_to_gdf(place_name)
    # area.to_crs(CRS.from_epsg(21781), inplace=True)

    # Fetch OSM street network from the location
    graph = ox.graph_from_address(address, simplify=False, retain_all=True, dist=distance+250, network_type="all_private")
    # Project the data
    graph = ox.project_graph(graph, to_crs=CRS.from_epsg(21781))

    # Retrieve nodes and edges
    nodes, edges = ox.graph_to_gdfs(graph)

    # Project nodes and edges
    nodes.to_crs(CRS.from_epsg(21781), inplace=True)
    edges.to_crs(CRS.from_epsg(21781), inplace=True)

    # tags for buildings
    tags = {'building': True}
    # Retrieve buildings with a defined distance in meters from address
    buildings = ox.geometries_from_address(address, tags, dist=distance+250)
    # Project the buildings
    buildings.to_crs(CRS.from_epsg(21781), inplace=True)

    # Read the file containing the info regarding the buildings
    fn = fileDir + "\\output\\raw_data\\" + filename
    users = gpd.read_file(fn, driver="GeoJSON")

    orig_coords = ox.geocoder.geocode(address)  # (lat, lng) but gpd accepts (lng, lat)
    orig_point = Point([orig_coords[1], orig_coords[0]])

    origin_geo = gpd.GeoDataFrame({'geometry': [orig_point]})
    origin_geo.set_crs(4326, inplace=True)
    # Project the origin
    origin_geo.to_crs(21781, inplace=True)
    # Geocode addresses using Nominatim. Remember to provide a custom "application name" in the user_agent parameter!
    # origin = geocode(address, provider='nominatim', user_agent='autogis_xx', timeout=4)

    origin = origin_geo["geometry"].values[0]  # users["geometry"].values[0]
    destination = users["geometry"].values[:]
    destination = gpd.GeoSeries(destination)

    # Find the node in the graph that is closest to the origin point (node id)
    orig_node_id = ox.distance.nearest_nodes(graph, origin.x, origin.y)
    orig_node_id_single = orig_node_id

    # Find the node in the graph that is closest to the target points (node id)
    target_node_id = ox.distance.nearest_nodes(graph, destination.x, destination.y)

    # duplicated the orig_node_id so that it has the same lengths of target_node_id
    orig_node_id = [orig_node_id_single for x in range(len(target_node_id))]

    # Calculate the shortest paths (route contains the node IDs of the graph)
    route = ox.shortest_path(G=graph, orig=orig_node_id, dest=target_node_id, weight='length')
    # finding the index of None from list (None = no path found)
    index = [i for i, e in enumerate(route) if e is None]

    # workaround for creating fake paths for user with no path found
    for idx in index:
        route[idx] = [orig_node_id[idx], orig_node_id[idx]]
        # destination.loc[idx] = origin.loc[0]
        destination.loc[idx] = origin
        users.drop(idx, inplace=True)

    # Retrieve the rows from the nodes GeoDataFrame based on the node id (node id is the index label)
    orig_node = nodes.loc[orig_node_id]
    target_node = nodes.loc[target_node_id]

    # Create a GeoDataFrame from the origin and target points
    orig_nodes = gpd.GeoDataFrame(orig_node, geometry='geometry', crs=nodes.crs)
    dest_nodes = gpd.GeoDataFrame(target_node, geometry='geometry', crs=nodes.crs)

    # creating a list containing every paths from origin to destination
    route_lines = []
    for i in route:
        if len(list(nodes.loc[i].geometry.values)) < 2:
            i = [i[0], i[0]]
        route_lines.append(LineString(list(nodes.loc[i].geometry.values)))

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

    # creating a geodataframe with the linestring of # creating a list containing every paths from origin to destination
    route_geom = gpd.GeoDataFrame(r_od, crs=edges.crs, columns=['geometry'])

    # adding origin & destination
    route_geom['origin'] = origin_geo.geometry
    route_geom['destination'] = destination

    # calculate the route length
    route_geom['length_m'] = route_geom.length

    convex_hull = users['geometry'].unary_union.convex_hull
    shd = users['fab_tot'].sum() / convex_hull.area
    print("The land heat density of the cluster is", "{:.2f}".format(shd), "kWh/m2 =",
          "{:.2f}".format(shd * 10), "MWh/ha")
    # print("The value should be higher than 350 MWh/ha.")

    bhd_max = users['fab_tot'].max() / users.loc[users['fab_tot'].idxmax(), 'SRE']
    bhd_ave = users['fab_tot'].sum() / users['SRE'].sum()
    print("The maximum specific heat demand of a building is", "{:.2f}".format(bhd_max), "kWh/m2 per year")

    shd = shd * 10  # conversion to MWh / m2
    # print("The value should be higher than 70 kWh/m2 per year.")

    print("The length of the network is", "{:.2f}".format(network['geometry'].length.sum() / 1000), "km")
    print("The longest generator-user path is is", "{:.2f}".format(route_geom['length_m'].max()), "m")

    lhd_energy = users['fab_tot'].sum() / network['geometry'].length.sum()
    print("The heat density of the network is", "{:.2f}".format(lhd_energy / 1000), "MWh/m")
    print("This value should be higher than 2.0 MWh/m")

    lhd_power = users['P_tot'].sum() / network['geometry'].length.sum()
    print("The heat density of the network is",
          "{:.2f}".format(lhd_power), "kW/m")
    print("This value should be higher than 1.0 kW/m")

    res = suitability(shd, bhd_ave)
    dict = {'bhd': bhd_ave, 'shd': shd, 'lhd_energy': lhd_energy, 'lhd_power': lhd_power, "suitable-for": res}
    # origin point, radius, number of buildings, length of the network, land area, building area, costs
    kpi = pd.DataFrame([dict], index=['HTDH'])
    print(kpi)

    network['length'] = network['geometry'].length

    folder = "\\output\\processed_data\\"
    fn = fileDir + folder + filename
    users.to_file(fn, driver="GeoJSON", show_bbox=True, indent=4)

    return users, lhd_energy


def plot(edges, nodes, buildings, users, network, route_geom, dest_nodes, orig_nodes, origin_geo, destination):

    edges_wm = edges.to_crs(epsg=3857)
    nodes_wm = nodes.to_crs(epsg=3857)
    buildings_wm = buildings.to_crs(epsg=3857)
    cluster_wm = users.to_crs(epsg=3857)
    network_wm = network.to_crs(epsg=3857)
    route_geom_wm = route_geom.to_crs(epsg=3857)
    dest_nodes_wm = dest_nodes.to_crs(epsg=3857)
    orig_nodes_wm = orig_nodes.to_crs(epsg=3857)
    origin_geo_wm = origin_geo.to_crs(epsg=3857)
    destination_wm = destination.to_crs(epsg=3857)

    # define figure and subplots
    fig, ax = plt.subplots()

    # plot edges and nodes
    # ax = edges_wm.plot(linewidth=0.75, color='gray')
    # ax = nodes_wm.plot(ax=ax, markersize=2, color='gray')

    # add buildings from OpenStreetMap
    ax = buildings_wm.plot(ax=ax, facecolor='khaki', alpha=0.01)

    # add cluster of users
    ax = cluster_wm.plot(ax=ax, markersize=24, color='red')

    # add the route
    ax = route_geom_wm.plot(ax=ax, linewidth=1, linestyle='--', color='red')
    # ax = network_wm.plot(ax=ax, linewidth=2, linestyle='--', color='red')

    # add the origin and destination nodes of the route
    # ax = dest_nodes_wm.plot(ax=ax, markersize=12, color='green')
    # ax = orig_nodes_wm.plot(ax=ax, markersize=48, color='black')

    ax = destination_wm.plot(ax=ax, markersize=16, color='green')
    ax = origin_geo_wm.plot(ax=ax, markersize=128, color='black')

    cx.add_basemap(ax, source=cx.providers.OpenStreetMap.CH, zoom=17)
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
    elif 100 <= shd >= 200:
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


<<<<<<< HEAD
=======

>>>>>>> d62882a7625edd439084599311c2ca04005f4392
# Main
if __name__ == "__main__":
    # python topology_finder.py -addr "Via La Santa 1, Lugano, Svizzera" -r 1000 -n 10

    from user_finder import com_num, clusterize
    from economics import economic_calc, parameters_with_calc, lcoh_calculator

    print('\nProgram started\n')

    # Input args
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-addr', help='address of the generation plant')
    arg_parser.add_argument('-r', help='radius in meters around the generation plant', type=float)
    arg_parser.add_argument('-n', help='maximum number of customers in the network', type=int)

    args = arg_parser.parse_args()
    address = args.addr
    radius = args.r
    n_max = args.n

    gmd, p = com_num(address)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    fp = fileDir + "\\output\\raw_data\\data-" + str(gmd) + ".csv"

    temp = pd.read_csv(fp, sep=";", index_col='index')
    temp['geometry'] = temp['geometry'].apply(wkt.loads)
    b = gpd.GeoDataFrame(temp, crs='epsg:21781')
    # print(b.head())

    type = "HTDHN"
    clusterize(b, gmd, radius, p, n_max, type)

    fn = "cluster-%s-%s.geojson" % (gmd, type)
    c, lhd = network_finder(fn, address, radius)
    economic_calc(c, lhd)  # todo: to be removed

    type = "LTDHN"
    clusterize(b, gmd, radius, p, n_max, type)

    fn = "cluster-%s-%s.geojson" % (gmd, type)
    c, lhd = network_finder(fn, address, radius)

    # todo: to be added to the economics main
    p_individual = c.loc[0, 'P_tot']
    q_individual = c.loc[0, 'fab_tot']
    p_network = c['P_tot'].sum()  # todo: add concurrency factor
    q_network = c['fab_tot'].sum()

    # economic_calc(c, lhd)

    # par = parameters_with_calc(type, q_network, p_network, lhd)
    lcoh, par = lcoh_calculator(type, q_network, p_network, lhd)
    print("The LCOH for", type, "is", "{:.3f}".format(lcoh), "CHF/kWh")
    df = pd.DataFrame([par])
    print(df)

    print('\nProgram ended\n')
