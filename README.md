# nlgeojson - Next Level Geojson Abstractions off Pandas DataFrames 
 Pandas DF to geojson implementation.

Basically this module mimics a lot of the functionality of one of my older modules but its a tenth of size and the complexity as well orders of magnitudes faster.

Geopandas exists to provide geospatial abstractions / methods in a pandas dataframe with geojson objects with shapely coordinate structures handling the work for it on the back end, this is done typically by reading in a geospatial file or manipulating fields to create more geospatial objects. Its nice, however, the geojson representation in memory for objects is unnecessary for a lot of applications,when most people only use a few methods at best.


# TL;DR
In short often times we don't care about the nature of the geospatial objects involved within our analysis. Really we only need two representions of our objects a index or geospatial representation, and a sparse bare bones flat representation with nothing "geo" about it at all. This sparse representation is a regular dataframe that exist solely for spatial joins of aggregated or related fields. 

So when comparing the heaviness of geopandas > pandas > shapely represented as a geojson to manage the extra state, its heavy.

If we need to relate a point to a line or a point to a polygon I use [ult](https://github.com/murphy214/ult) its much faster and breaks up analysis into defined sections point relation, point aggregation, than joining. Ult creates the second type of representation we need a spatial index.

So it makes logical sense to bring only what we need in a dataframe (nothing more) to parse into output geojson when doing geospatial aggregations and joins. Making reading, manipulating, and 
writing out to geojson geometries much much easier, as well as [faster](https://github.com/murphy214/nlgeojson/blob/master/demo.ipynb)

# Small caveat
This module assumes you know the type of geometry your dataframe is representing by sending it in to the correct function. (i.e. make_lines,make_points,make_blocks,make_polygons) 

## Please take a look at this [ipynb](https://github.com/murphy214/nlgeojson/blob/master/demo.ipynb) for the performance advantages and the unique syntax it uses.

