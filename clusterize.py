# clusterize.py

# install the dependencies (shapely, fiona, pyproj and rtree) manually from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/

# install gdal from:
# https://sandbox.idre.ucla.edu/sandbox/tutorials/installing-gdal-for-windows

# install geopandas
# https://geopandas.org/getting_started/install.html

# 1. analyze data with geopandas
# 2. identify all buildings within a certain distance (100 m) of a chosen building
# 3. calculate the area created by unifying the building o simply area of the radius
# https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
# 4. calculate the demand per unit area of land
# 5. repeat for every building
# 6. identify clusters above a certain heat density threshold
# 7. unify clusters that intersect each other
# 8. identify roads
# https://github.com/oemof/DHNx/blob/dev/examples/investment_optimisation/import_osm_invest/import_osm_invest.py
# map of switzerland
# https://www.geocat.ch/geonetwork/srv/ita/md.viewer#/full_view/b495f369-9262-4269-8532-27b06591e33a/tab/complete
# roads in switzerland
# https://www.geocat.ch/geonetwork/srv/eng/md.viewer#/full_view/be285f33-0373-4882-b911-de402bcdfeb4
# 9. connect building to roads and back to the generator
# https://towardsdatascience.com/connecting-pois-to-a-road-network-358a81447944
#
