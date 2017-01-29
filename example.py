import pandas as pd
import geopandas as gpd
import nlgeojson as nl
import pipeleaflet as pl

# reading into memory a counties shapefile
data = gpd.read_file('example_shp/cb_2015_us_county_500k.shp')

# making the nldataframe the geodataframe
# and creating counties csv file now red
data = nl.geodf_to_nldf(data,filename='counties.csv')

# reading in the csv just made and adding a colorkey field
data = pd.read_csv('counties.csv')

# writing out the geojson file
nl.make_polygons(data,'polygons.geojson')

# creating map visualization
#pl.b()

