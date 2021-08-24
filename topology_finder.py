import osmnx as ox
import matplotlib.pyplot as plt
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import LineString, Point, MultiLineString

# Specify the name that is used to search for the data
place_name = "Lugano, Ticino, Switzerland"
address = "Via La Santa 1, Lugano, Svizzera"

# Get place boundary related to the place name as a geodataframe
area = ox.geocode_to_gdf(place_name)
area.to_crs(CRS.from_epsg(21781), inplace=True)

# Fetch OSM street network from the location
graph = ox.graph_from_address(address, simplify=False, retain_all=True, dist=500, network_type='walk')
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

# Plot the municipality with the buildings
# fig, ax = plt.subplots(figsize=(12,8))
#
# # Plot the footprint
# area.plot(ax=ax, facecolor='silver')
#
# # Plot street edges
# edges.plot(ax=ax, linewidth=1, edgecolor='white')
#
# # Plot buildings
# buildings.plot(ax=ax, facecolor='grey', alpha=0.7)
#
# # Plot cluster
# cluster.plot(ax=ax, facecolor='red', alpha=0.7)
#
# plt.tight_layout()
# plt.show()

# define the origin of the network
origin = cluster["geometry"].values[0]
# todo: it should be the address given in the beginning (coordinates can be obtained with geocoding)
destination = cluster["geometry"].values[1:-1]

# Find the node in the graph that is closest to the origin point (node id)
orig_node_id = ox.distance.nearest_nodes(graph, origin.x, origin.y)
# Find the node in the graph that is closest to the target point (node id)
target_node_id = ox.distance.nearest_nodes(graph, destination.x, destination.y)

# duplicated the orig_node_id so that it has the same lengths of destination
orig_node_id = [orig_node_id for x in range(len(target_node_id))]

# Calculate the shortest paths (route contains the node IDs of the graph)
route = ox.shortest_path(G=graph, orig=orig_node_id, dest=target_node_id, weight='length')
# removing None from list (none = no path found)
route = [i for i in route if i]
# todo: keep the IDs of the None and identify the user

# Retrieve the rows from the nodes GeoDataFrame based on the node id (node id is the index label)
orig_node = nodes.loc[orig_node_id]
target_node = nodes.loc[target_node_id]

# Create a GeoDataFrame from the origin and target points
orig_nodes = gpd.GeoDataFrame(orig_node, geometry='geometry', crs=nodes.crs)
dest_nodes = gpd.GeoDataFrame(target_node, geometry='geometry', crs=nodes.crs)

# Get the nodes along the shortest path
# route_nodes = nodes.loc[route]
# route_lines = nodes.loc[route[0]].unary_union

# creating a list containing every paths from origin to destination
route_lines = []
for i in route:
    route_lines.append(LineString(list(nodes.loc[i].geometry.values)))

# todo: append to every paths the origin and the destination
# creating a geodataframe with the linestring of # creating a list containing every paths from origin to destination
route_geom = gpd.GeoDataFrame(route_lines, crs=edges.crs, columns=['geometry'])
# Calculate the route length
route_geom['length_m'] = route_geom.length
# fixme: add these two to the cluster

# Add a list of osmids associated with the route
# route_nodes['osmid'] = route_nodes.index
# route_geom.loc[0, 'osmids'] = str(list(route_nodes['osmid'].values))

# Plot edges and nodes
ax = edges.plot(linewidth=0.75, color='gray')
ax = nodes.plot(ax=ax, markersize=2, color='gray')

# Add buildings
ax = buildings.plot(ax=ax, facecolor='khaki', alpha=0.7)

ax = cluster.plot(ax=ax, markersize=24)

# Add the route
ax = route_geom.plot(ax=ax, linewidth=1, linestyle='--', color='red')

# Add the origin and destination nodes of the route
ax = dest_nodes.plot(ax=ax, markersize=12, color='green')
ax = orig_nodes.plot(ax=ax, markersize=48, color='black')
plt.show()