#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='nlgeojson',
      version='1.3',
      description="Next-level geojson parsing using pandas dataframes. SUPERFAST.",
      author='Bennett Murphy',
      author_email='murphy214@live.marshall.edu',
      url='https://github.com/murphy214/nlgeojson',
      packages=['nlgeojson'],
      dependency_links= [
      'http://github.com/hkwi/python-geohash/tarball/master#egg=python-geohash-0.8.5',
      ],
	install_requires=['pandas',
		'shapely',
		'geopandas',
		'mercantile',
		'future',

	]
     )


