# nlgeojson - Next Level Geojson Abstractions off Pandas DataFrames 
 Pandas DF to geojson implementation.

Basically this module mimics a lot of the functionality of one of my older modules but its a tenth of size and the complexity as well orders of magnitudes faster.

Geopandas exists to provide geospatial abstractions / methods in a pandas dataframe with geojson objects with shapely coordinate structures handling the work for it on the back end, this is done typically by reading in a geospatial file or manipulating fields to create more geospatial objects. Its nice however, the geojson representation in memory for objects is unnecessary for a lot of applications,when most people only use a few methods at best.



# TL;DR
In short often times we don't care about the nature of the geospatial objects involved witihin this module. If we need to relate a point to a line or a point to a polygon I use [ult]() its much faster and breaks up analysis into defined sections point relation, point aggregation, than joining. So it makes logical sense to bring only what we need in a dataframe (nothing more) to parse into output geojson when doing geospatial aggregations and joins. By adding a field in my postgres database to lines databases that essentially is a coordinate x,y list stringified (exactly what goes into geojson lines)  and compeletey reworking my polygon tables as flat string representations of multipolygon heirarchies already housed inside the string, making reading, manipulating, and 
writing out to geojson geometries much much easier, as well as [faster](https://github.com/murphy214/nlgeojson/blob/master/demo.ipynb)

For points we simply assume a lat / long field exists in the columns of a points df and search for it. Blocks are assumed to either have a geojson field or a NORTH,SOUTH,EAST,WEST field.

# Small caveat
This module assumes you know the type of geometry your dataframe is representing by sending it in to the correct function. (i.e. make_lines,make_points,make_blocks,make_polygons) 

## Please take a look at this [ipynb](https://github.com/murphy214/nlgeojson/blob/master/demo.ipynb) for the performance advantages and the unique syntax it uses.

