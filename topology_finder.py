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

# filename = "cluster-5192.geojson"
# # place_name = "Lugano, Ticino, Switzerland"
# address = "Via La Santa 15, Lugano, Ticino, Switzerland"
# distance = 750


def user_finder(filename, address, distance):

    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    # Get place boundary related to the place name as a geodataframe
    # area = ox.geocode_to_gdf(place_name)
    # area.to_crs(CRS.from_epsg(21781), inplace=True)

    # Fetch OSM street network from the location
    graph = ox.graph_from_address(address, simplify=False, retain_all=True, dist=distance+250, network_type='all')
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

    origin = origin_geo.geometry.values[0]
    destination = cluster["geometry"].values[:]
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
    land_heat_density = cluster['fab_tot'].sum() / convex_hull.area
    print("The land heat density of the cluster is", "{:.2f}".format(land_heat_density), "kWh/m2 =",
          "{:.2f}".format(land_heat_density * 10), "MWh/ha")
    print("The value should be higher than 350 MWh/ha.")

    building_heat_density = cluster['fab_tot'].sum() / cluster['SRE'].sum()
    print("The building heat density of the cluster is", "{:.2f}".format(building_heat_density), "kWh/m2 per year")
    print("The value should be higher than 70 kWh/m2 per year.")
    print("The length of the network is", "{:.2f}".format(network['geometry'].length.sum() / 1000), "km")
    print("The heat density of the network is", "{:.2f}".format(cluster['fab_tot'].sum() / 1000 / network['geometry'].length.sum()), "MWh/m")
    print("This value should be higher than 2.0 MWh/m")

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
    plt.show()


# Main
if __name__ == "__main__":
    # python topology_finder.py -addr "Via La Santa 1, Lugano, Svizzera" -r 100 -n 10

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

    clusterize(b, gmd, radius, p, n_max)

    fn = "cluster-5192.geojson"
    user_finder(fn, address, radius)

    print('\nProgram ended\n')
