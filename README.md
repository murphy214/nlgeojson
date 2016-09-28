# nlgeojson - Next Level Geojson Abstractions off Pandas DataFrames 
Dope Pandas DF to geojson implementation.

Basically this module mimics a lot of the functionality of one of my older modules but its a tenth of size and the complexity as well orders of magnitudes faster.

Still a working progress but this shit flies.

Polygons are coming later I don't have any postgis databases handy to mess or experiment with but the implementation will probably look like line segments with a field in df for whether the winding order isn't yielding a whole. In other words a truth in a field will dictate styling of a polygons winding order. (propably)


# Screenshots of Benchmarks Against Old Functions
![](https://cloud.githubusercontent.com/assets/10904982/18922836/44658e14-8578-11e6-90de-668237ab5ba9.png)
![](https://cloud.githubusercontent.com/assets/10904982/18922878/538c063e-8578-11e6-9ef1-050de21f26d3.png)
![](https://cloud.githubusercontent.com/assets/10904982/18922892/62d1aa5e-8578-11e6-84e7-511a683fd4f7.png)
