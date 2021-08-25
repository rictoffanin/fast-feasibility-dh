import osmnx as ox
import matplotlib.pyplot as plt
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import LineString, Point, MultiLineString
# Import the geocoding tool
from geopandas.tools import geocode


# Specify the name that is used to search for the data
from shapely.ops import unary_union

place_name = "Lugano, Ticino, Switzerland"
address = "Via La Santa 1, Lugano, Ticino, Switzerland"

# Get place boundary related to the place name as a geodataframe
area = ox.geocode_to_gdf(place_name)
area.to_crs(CRS.from_epsg(21781), inplace=True)

# Fetch OSM street network from the location
graph = ox.graph_from_address(address, simplify=False, retain_all=True, dist=500)
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
buildings = ox.geometries_from_address(address, tags, dist=500)
# Project the buildings
buildings.to_crs(CRS.from_epsg(21781), inplace=True)

# Read the file containing the info regarding the buildings
# todo: filename should be an input
filename = "D:\SUPSI\geodata-ch\src\output\processed_data\cluster-5192.geojson"
cluster = gpd.read_file(filename, driver="GeoJSON")

# todo: it should be the address given in the beginning (coordinates can be obtained with geocoding). non funziona la
#  conversione fra CRS define the origin of the network
orig_coords = ox.geocoder.geocode(address)
orig_point = Point([orig_coords[1], orig_coords[0]])
dict = {'geometry': [orig_point]}
origin = gpd.GeoDataFrame(dict)
# Geocode addresses using Nominatim. Remember to provide a custom "application name" in the user_agent parameter!
# origin = geocode(address, provider='nominatim', user_agent='autogis_xx', timeout=4)
origin.set_crs(4326, inplace=True)
print(nodes['geometry'].iloc[0], nodes.crs)
# print(origin)
# Project the origin
# print("The point", origin.loc[0,'geometry'], "in CRS", origin.crs)
origin.to_crs(21781, inplace=True)
# print("The point", origin.loc[0,'geometry'], "in CRS", origin.crs)
# Plot the municipality with the buildings
origin = cluster["geometry"].values[0]
origin = gpd.GeoSeries(origin)

destination = cluster["geometry"].values[1:-1]
destination = gpd.GeoSeries(destination)

# Find the node in the graph that is closest to the origin point (node id)
orig_node_id = ox.distance.nearest_nodes(graph, origin.x, origin.y)
orig_node_id_single = orig_node_id

# Find the node in the graph that is closest to the target points (node id)
target_node_id = ox.distance.nearest_nodes(graph, destination.x, destination.y)

# duplicated the orig_node_id so that it has the same lengths of target_node_id
orig_node_id = [orig_node_id[0] for x in range(len(target_node_id))]

# Calculate the shortest paths (route contains the node IDs of the graph)
route = ox.shortest_path(G=graph, orig=orig_node_id, dest=target_node_id, weight='length')
# finding the index of None from list (None = no path found)
index = [i for i, e in enumerate(route) if e is None]

# workaround for creating fake paths for user with no path found
for idx in index:
    route[idx] = [orig_node_id[idx], orig_node_id[idx]]
    destination.loc[idx] = origin.loc[0]

# Retrieve the rows from the nodes GeoDataFrame based on the node id (node id is the index label)
orig_node = nodes.loc[orig_node_id]
target_node = nodes.loc[target_node_id]

# Create a GeoDataFrame from the origin and target points
orig_nodes = gpd.GeoDataFrame(orig_node, geometry='geometry', crs=nodes.crs)
dest_nodes = gpd.GeoDataFrame(target_node, geometry='geometry', crs=nodes.crs)

# creating a list containing every paths from origin to destination
route_lines = []
for i in route:
    route_lines.append(LineString(list(nodes.loc[i].geometry.values)))


# work-around to append each origin and destination to every path
r_od = []
for idx in range(len(route_lines)):
    temp = []
    temp.append(origin[0])
    for coord in route_lines[idx].coords:
        temp.append(coord)
    temp.append(destination[idx])

    line = LineString(temp)
    r_od.append(line)

    del temp

# unary_union allows to separate the line into segments and remove duplicates
out = unary_union(r_od)

# creating geodataframe containing the branches of the network
out = gpd.GeoDataFrame(out, columns=['geometry'], crs=nodes.crs)

# creating a geodataframe with the linestring of # creating a list containing every paths from origin to destination
route_geom = gpd.GeoDataFrame(r_od, crs=edges.crs, columns=['geometry'])

# adding origin & destination
# orig_points = []
# for i in range(len(destination)):
#     orig_points.append(origin)

route_geom['origin'] = origin.geometry
route_geom['destination'] = destination

# calculate the route length
route_geom['length_m'] = route_geom.length

# Plot edges and nodes
ax = edges.plot(linewidth=0.75, color='gray')
ax = nodes.plot(ax=ax, markersize=2, color='gray')

# Add buildings
ax = buildings.plot(ax=ax, facecolor='khaki', alpha=0.7)

# ax = cluster.plot(ax=ax, markersize=24)

# Add the route
# ax = route_geom.plot(ax=ax, linewidth=1, linestyle='--', color='red')
ax = out.plot(ax=ax, linewidth=2,  linestyle='--', color='red')
out['length'] = out['geometry'].length

# Add the origin and destination nodes of the route
# ax = dest_nodes.plot(ax=ax, markersize=12, color='green')
# ax = orig_nodes.plot(ax=ax, markersize=48, color='black')
route_geom['origin'] = route_geom['origin']
ax = route_geom['destination'].plot(ax=ax, markersize=12, color='green')
ax = route_geom['origin'].plot(ax=ax, markersize=48, color='black')
plt.show()

print("The length of the network is", out['geometry'].length.sum()/1000, "km")
print("The heat density of the network is", cluster['fab_tot'].sum()/1000/out['geometry'].length.sum(), "MWh/m")