ZIP_URL = 'https://data.geo.admin.ch/ch.bfs.gebaeude_wohnungs_register/CSV'

API_URL = 'https://api3.geo.admin.ch/rest/services/api/MapServer'
DATA_LAYER = 'ch.bfs.gebaeude_wohnungs_register'  # REA
SRC_FIELD = 'egid'
SR = '4326'

# The spatial reference. Supported values: 21781(LV03), 2056(LV95), 4326(WGS84) and 3857(Web Pseudo - Mercator).
# Defaults to “21781”.