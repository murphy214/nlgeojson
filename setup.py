#!/usr/bin/env python

from distutils.core import setup

setup(name='nlgeojson',
      version='1.1',
      description="Next-level geojson parsing using pandas dataframes. SUPERFAST.",
      author='Bennett Murphy',
      author_email='murphy214@live.marshall.edu',
      url='https://github.com/murphy214/nlgeojson',
      packages=['nlgeojson'],
      scripts=['bin/read_geojson','bin/read_geobuf'],
      dependency_links= ['http://github.com/murphy214/pipegeohash/tarball/master#egg=pipegeohash-1.2.0',
      ],
	  install_requires=['pandas',
		'shapely',
		'geopandas',
		'mercantile',
		'future',
	]
     )


