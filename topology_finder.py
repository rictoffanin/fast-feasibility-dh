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

# filename = "cluster-5192.geojson"
# # place_name = "Lugano, Ticino, Switzerland"
# address = "Via La Santa 15, Lugano, Ticino, Switzerland"
# distance = 750


def network_finder(filename, address, distance):

    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    # Get place boundary related to the place name as a geodataframe
    # area = ox.geocode_to_gdf(place_name)
    # area.to_crs(CRS.from_epsg(21781), inplace=True)

    # Fetch OSM street network from the location
    graph = ox.graph_from_address(address, simplify=False, retain_all=True, dist=distance+250, network_type='walk')
    # Project the data
    graph = ox.project_graph(graph, to_crs=CRS.from_epsg(21781))

    # Retrieve nodes and edges
    nodes, edges = ox.graph_to_gdfs(graph)

    # Project nodes and edges
    nodes.to_crs(CRS.from_epsg(21781), inplace=True)
    edges.to_crs(CRS.from_epsg(21781), inplace=True)

    # List key-value pairs for tags
    tags = {'building': True}
    # Retrieve buildings with a defined distance in meters from address
    buildings = ox.geometries_from_address(address, tags, dist=distance+250)
    # Project the buildings
    buildings.to_crs(CRS.from_epsg(21781), inplace=True)

    # Read the file containing the info regarding the buildings
    # todo: filename should be an input
    filename = fileDir + "\\output\\processed_data\\" + filename
    cluster = gpd.read_file(filename, driver="GeoJSON")

    orig_coords = ox.geocoder.geocode(address)  # (lat, lng) but gpd accepts (lng, lat)
    orig_point = Point([orig_coords[1], orig_coords[0]])

    origin_geo = gpd.GeoDataFrame({'geometry': [orig_point]})
    origin_geo.set_crs(4326, inplace=True)
    # Project the origin
    origin_geo.to_crs(21781, inplace=True)
    # Geocode addresses using Nominatim. Remember to provide a custom "application name" in the user_agent parameter!
    # origin = geocode(address, provider='nominatim', user_agent='autogis_xx', timeout=4)

    origin = cluster["geometry"].values[0]
    destination = cluster["geometry"].values[1:-1]
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
        cluster.drop(idx)

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

    convex_hull = cluster['geometry'].unary_union.convex_hull
    spatial_heat_density = cluster['fab_tot'].sum() / convex_hull.area
    print("The land heat density of the cluster is", "{:.2f}".format(spatial_heat_density), "kWh/m2 =",
          "{:.2f}".format(spatial_heat_density * 10), "MWh/ha")
    # print("The value should be higher than 350 MWh/ha.")

    building_heat_density = cluster['fab_tot'].max() / cluster.loc[cluster['fab_tot'].idxmax(), 'SRE']
    print("The maximum specific heat demand of a building is", "{:.2f}".format(building_heat_density), "kWh/m2 per year")

    spatial_heat_density = spatial_heat_density*10  # conversion to MWh / m2
    # print("The value should be higher than 70 kWh/m2 per year.")
    print("")
    if spatial_heat_density < 100:
        if building_heat_density < 40:
            print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS")
        elif 40 <= building_heat_density <= 60:
            print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS/LTDH/HTDH")
        elif building_heat_density > 60:
            print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS")
    elif 100 <= spatial_heat_density >= 200:
        if building_heat_density < 40:
            print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS/LTDH")
        elif 40 <= building_heat_density <= 60:
            print("The network might be suitable for LTDH/HTDH")
        elif building_heat_density > 60:
            print("The network might be suitable for INDIVIDUAL HEATING SYSTEMS/HTDH")
    elif spatial_heat_density > 200:
        if building_heat_density < 40:
            print("The network might be suitable for LTDH")
        elif 40 <= building_heat_density <= 60:
            print("The network might be suitable for LTDH/HTDH")
        elif building_heat_density > 60:
            print("The network might be suitable for HTDH")

    print("The length of the network is", "{:.2f}".format(network['geometry'].length.sum() / 1000), "km")
    print("The longest generator-user path is is", "{:.2f}".format(route_geom['length_m'].max()), "m")

    linear_heat_density = cluster['fab_tot'].sum() / network['geometry'].length.sum()
    print("The heat density of the network is", "{:.2f}".format(linear_heat_density/1000), "MWh/m")
    print("This value should be higher than 2.0 MWh/m")

    print("The heat density of the network is",
          "{:.2f}".format(cluster['P_tot'].sum() / network['geometry'].length.sum()), "kW/m")
    print("This value should be higher than 1.0 kW/m")

    # Plot edges and nodes
    ax = edges.plot(linewidth=0.75, color='gray')
    ax = nodes.plot(ax=ax, markersize=2, color='gray')

    # Add buildings
    ax = buildings.plot(ax=ax, facecolor='khaki', alpha=0.7)

    # ax = cluster.plot(ax=ax, markersize=24)

    # Add the route
    # ax = route_geom.plot(ax=ax, linewidth=1, linestyle='--', color='red')
    ax = network.plot(ax=ax, linewidth=2, linestyle='--', color='red')
    network['length'] = network['geometry'].length

    # Add the origin and destination nodes of the route
    # ax = dest_nodes.plot(ax=ax, markersize=12, color='green')
    # ax = orig_nodes.plot(ax=ax, markersize=48, color='black')
    route_geom['origin'] = route_geom['origin']
    ax = route_geom['destination'].plot(ax=ax, markersize=16, color='green')
    ax = route_geom['origin'].plot(ax=ax, markersize=128, color='black')
    # plt.show()

    return cluster, linear_heat_density


def economic_calc(cluster, lhd):

    p_individual = cluster.loc[0, 'P_tot']
    q_individual = cluster.loc[0, 'fab_tot']
    p_network = cluster['P_tot'].sum()  # todo: add concurrency factor
    q_network = cluster['fab_tot'].sum()

    c_inv_oil = 945  # CHF/kW_th
    k_inst_oil = 0.270  # 27% of the total investment cost
    k_equip_oil = 1 - k_inst_oil  # 73% of the total investment cost
    k_OandM_oil = 0.025  # 2.5% of total investment cost per year
    eta_oil = 0.83
    lt_oil = 20  # lifetime of the gas boiler
    p_oil = 0.078  # CHF/kWh

    print("\nLCOH for individual oil boiler")
    lcoh_calc(c_inv_oil*p_individual, k_OandM_oil, p_oil, eta_oil, q_individual, lt_oil)

    c_inv_gas = 945  # CHF/kW_th
    k_inst_gas = 0.270  # 27% of the total investment cost
    k_equip_gas = 1 - k_inst_gas  # 73% of the total investment cost
    k_OandM_gas = 0.025  # 2.5% of total investment cost per year
    eta_gas = 0.87
    lt_gas = 20  # lifetime of the gas boiler
    p_gas = 0.087

    print("\nLCOH for individual gas boiler")
    lcoh_calc(c_inv_gas*p_individual, k_OandM_gas, p_gas, eta_gas, q_individual, lt_gas)

    c_inv_ashp = lambda x: 14677 * pow(x, -0.683)
    p_max_ashp = 50  # kW
    k_inst_ashp = 0.270
    k_equip_ashp = 1 - k_inst_ashp
    k_OandM_ashp = 0.01  # 1% of the total investment cost per year
    eta_ashp = 3.00
    p_ashp = 0.201
    lt_ashp = 25  # years

    p_inv = max(p_individual, p_max_ashp)
    print("\nLCOH for ASHP")
    lcoh_calc(c_inv_ashp(p_inv) * p_individual, k_OandM_ashp, p_ashp, eta_ashp, q_individual, lt_ashp)

    c_inv_gshp = lambda x: 15962 * pow(x, -0.259)
    p_max_gshp = 500  # kW
    k_inst_gshp = 0.270
    k_equip_gshp = 1 - k_inst_ashp
    k_OandM_gshp = 0.01  # 1% of the total investment cost per year
    eta_gshp = 3.70
    lt_gshp = 25  # years
    p_gshp = p_ashp

    print("\nLCOH for GSHP")
    lcoh_calc(c_inv_gshp(p_individual) * p_individual, k_OandM_gshp, p_gshp, eta_gshp, q_individual, lt_gshp)

    c_inv_wshp = lambda x: 16625 * pow(x, -0.321)
    p_max_wshp = 500  # kW
    k_inst_wshp = 0.270
    k_equip_wshp = 1 - k_inst_ashp
    k_OandM_wshp = 0.01  # 1% of the total investment cost per year
    eta_wshp = 4.00
    lt_wshp = 25  # years
    p_wshp = p_ashp

    print("\nLCOH for WSHP")
    lcoh_calc(c_inv_wshp(p_individual) * p_individual, k_OandM_wshp, p_wshp, eta_wshp, q_individual, lt_wshp)

    # todo: calcola un cluster per ltdh e uno per htdh
    i_dis = dis_cost_calc(lhd, q_network)
    i_prod = c_inv_wshp(p_network) * p_network * 2
    i_aux = 0.18*q_network
    i_con = 0.03*q_network
    i_dhn = i_prod + i_dis + i_aux + i_con
    k_OandM_dhn = 0.04
    eta_dhn = 4.00
    lt_dhn = 40
    p_dhn = p_ashp*0.8

    print("\nLCOH for DHN")
    lcoh_calc(i_dhn, k_OandM_dhn, p_dhn, eta_dhn, q_network, lt_dhn)


def lcoh_calc(inv, k_OandM, p_e, eta, q, lt, r=0.03):

    a = annuity(lt, r)
    e = q*p_e / eta
    lcoh = (a*inv + inv*k_OandM + e) / q
    print("The LCOH is", "{:.3f}".format(lcoh), "CHF/kWh")
    return lcoh


def annuity(lt, r=0.03):

    num = pow(1+r, lt) * r
    den = pow(1+r, lt) - 1
    return num / den


def net_diam(lhd):
    lhd = lhd * (pow(10, 6) / 3600)  # kWh/m to GJ/m
    return 0.0486 * np.log(lhd) + 0.0007


def dis_cost_calc(lhd, q):
    c1 = 315  # CHF/m
    c2 = 2224  # CHF/m
    k_loss = 0.08
    a = annuity(40)
    d_ave = net_diam(lhd)

    return (a*(c1+c2*d_ave)) / lhd * q * (1 + k_loss)


# Main
if __name__ == "__main__":
    # python topology_finder.py -addr "Via La Santa 1, Lugano, Svizzera" -r 1000 -n 10

    from user_finder import com_num, clusterize

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
    fp = fileDir + "\\output\\processed_data\\data-" + str(gmd) + ".csv"

    temp = pd.read_csv(fp, sep=";", index_col='index')
    temp['geometry'] = temp['geometry'].apply(wkt.loads)
    b = gpd.GeoDataFrame(temp, crs='epsg:21781')
    # print(b.head())

    type = "HTDHN"
    clusterize(b, gmd, radius, p, n_max, type)

    fn = "cluster-%s-%s.geojson" % (gmd, type)
    c, lhd = network_finder(fn, address, radius)
    economic_calc(c, lhd)

    type = "LTDHN"
    clusterize(b, gmd, radius, p, n_max, type)

    fn = "cluster-%s-%s.geojson" % (gmd, type)
    c, lhd = network_finder(fn, address, radius)
    economic_calc(c, lhd)

    print('\nProgram ended\n')
