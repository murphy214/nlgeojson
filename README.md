# nlgeojson - Next Level Geojson Abstractions off Pandas DataFrames 
**Fastest Pandas DF to geojson implementation.**

# What is it?
Nlgeojson is a module that parses raw json using a vanilla pandas dataframe to make parsing geojson as fast as possible. Often times when doing data analysis the geometry isn't explicitly required within the actual analysis so formatting a dataframe to take advantage of this fact allows you to skip things like hard serialization of json object as dictionary objects in python which get you massive speedups when taking into account we can use to the to_json() method off the dataframe to get out a string representation of the properties. 

**Basically this module parses geojson anywhere from 30-80x times faster then normal json serialization making data visualization, algorithm prototyping, and anything else much much easier.** 

# Install
``` 
pip install git+https://github.com/murphy214/nlgeojson
```

# Main Functions 

```python 
import nlgeojson as nl

# reading in a geojson
dataframe = nl.read_geojson(geojsonfilename)

# Current implementations require data types to be homogenous
# make polygons
nl.make_polygons(dataframe,filename)

# make lines 
nl.make_lines(dataframe,filename)

# make points 
nl.make_points(dataframe,filename)

# make_blocks (say if you ahve a geohash column or XYZ tileid column)
mk.make_blocks(dataframe,filename) # in the implementation is just a polygon but looks for the two fields
```

#### Output Benchmarks can be seen below:
![](https://cloud.githubusercontent.com/assets/10904982/22404494/e74c89b0-e5ff-11e6-92c3-f628cda9a6ae.png)

# What about just using Geopandas?

Geopandas exists to provide geospatial abstractions / methods in a pandas dataframe with geojson objects with shapely coordinate structures handling the work for it on the back end, this is done typically by reading in a geospatial file or manipulating fields to create more geospatial objects.

Basically if you output the vanilla nl formatted dataframe to csv it will make both reading in the geometry / writing out geojson much faster and easier to work with. 



# Example Code / Usage
```python
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
```
## Output Can be Seen Below
![](https://cloud.githubusercontent.com/assets/10904982/22404535/a643bb22-e600-11e6-8451-f0ac7c4ad112.png)

