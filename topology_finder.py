import osmnx as ox
import matplotlib.pyplot as plt
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import LineString, Point

# Specify the name that is used to seach for the data
place_name = "Lugano, Ticino, Switzerland"
address = "Via La Santa 1, Lugano, Svizzera"

# Get place boundary related to the place name as a geodataframe
area = ox.geocode_to_gdf(place_name)
area.to_crs(CRS.from_epsg(21781), inplace=True)

# Fetch OSM street network from the location
graph = ox.graph_from_address(address, simplify=True, retain_all=True, dist=500)
# Project the data
graph = ox.project_graph(graph, to_crs=CRS.from_epsg(21781))
# graph.to_crs(CRS.from_epsg(21781), inplace=True)

# Retrieve nodes and edges
nodes, edges = ox.graph_to_gdfs(graph)
nodes.to_crs(CRS.from_epsg(21781), inplace=True)
edges.to_crs(CRS.from_epsg(21781), inplace=True)

# List key-value pairs for tags
tags = {'building': True}
buildings = ox.geometries_from_address(address, tags, dist=500)
buildings.to_crs(CRS.from_epsg(21781), inplace=True)

filename = "D:\SUPSI\geodata-ch\src\output\processed_data\cluster-5192.geojson"
cluster = gpd.read_file(filename, driver="GeoJSON")
print("Cluster crs is", cluster.crs)
print("Buildings crs is", buildings.crs)

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
#
# plt.tight_layout()
# plt.show()

# Get centroid as shapely point
origin = cluster["geometry"].values[0]

destination = cluster["geometry"].values[40]
# Get origin x and y coordinates
orig_xy = (origin.y, origin.x)

# Get target x and y coordinates
target_xy = (destination.y, destination.x)

# Find the node in the graph that is closest to the origin point (here, we want to get the node id)
orig_node_id = ox.distance.nearest_nodes(graph, origin.x, origin.y)
# Find the node in the graph that is closest to the target point (here, we want to get the node id)
target_node_id = ox.distance.nearest_nodes(graph, destination.x, destination.y)

# Retrieve the rows from the nodes GeoDataFrame based on the node id (node id is the index label)
orig_node = nodes.loc[orig_node_id]
target_node = nodes.loc[target_node_id]

# Create a GeoDataFrame from the origin and target points
od_nodes = gpd.GeoDataFrame([orig_node, target_node], geometry='geometry', crs=nodes.crs)

# Calculate the shortest path
route = ox.shortest_path(G=graph, orig=orig_node_id, dest=target_node_id, weight='length')
print(type(route))


# Get the nodes along the shortest path
route_nodes = nodes.loc[route]

# Create a geometry for the shortest path
route_line = LineString(list(route_nodes.geometry.values))

# Create a GeoDataFrame
route_geom = gpd.GeoDataFrame([[route_line]], geometry='geometry', crs=edges.crs, columns=['geometry'])

# Add a list of osmids associated with the route
route_nodes['osmid'] = route_nodes.index
route_geom.loc[0, 'osmids'] = str(list(route_nodes['osmid'].values))

# Calculate the route length
route_geom['length_m'] = route_geom.length

# Plot edges and nodes
ax = edges.plot(linewidth=0.75, color='gray')
ax = nodes.plot(ax=ax, markersize=2, color='gray')

# Add buildings
ax = buildings.plot(ax=ax, facecolor='khaki', alpha=0.7)

# Add the route
ax = route_geom.plot(ax=ax, linewidth=2, linestyle='--', color='red')

# Add the origin and destination nodes of the route
ax = od_nodes.plot(ax=ax, markersize=24, color='green')

plt.show()