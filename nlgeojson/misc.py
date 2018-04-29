import geohash 
import sys
from future.utils import bytes_to_native_str as n
import numpy as np
import geohash
import json
import itertools
import time
import pandas as pd
import future
import geopandas as gpd
import mercantile
from shapely.geometry import mapping
import subprocess
import os
import io

# makes the cordinates for each set of pointss
def _make_coord(data,latlongheaders):
	ind1 = False
	ind2 = False
	if latlongheaders == False:
		for row in data.columns.values.tolist():
			if 'lat' in str(row).lower() and ind1 == False:
				ind1 = True
				latheader = row
			if 'long' in str(row).lower() and ind2 == False:
				ind2 = True
				longheader = row
			if 'lng' == str(row):
				ind2 = True
				longheader = row
	else:
		latheader,longheader = latlongheaders
	data['coord'] = '[' + data[longheader].astype(str) + ', ' + data[latheader].astype(str) + ']'
	return data

# extracting the raw coords from postgis output
# this is used to get the stringified cords
# and ultimately is updated as field in postgres
def _get_coordstring(geometry):
	# parsing through the text geometry to yield what will be rows
	try:
		geometry=str.split(geometry,'(')
		geometry=geometry[-1]
		geometry=str.split(geometry,')')
	except TypeError:
		return [[0,0],[0,0]] 
	# adding logic for if only 2 points are given 
	if len(geometry) == 3:
		newgeometry = str.split(str(geometry[0]),',')
		
	else:
		if not len(geometry[:-2]) >= 1:
			return [[0,0],[0,0]]
		else:
			newgeometry=geometry[:-2][0]
			newgeometry=str.split(newgeometry,',')

	coords=[]
	for row in newgeometry:
		row=str.split(row,' ')
		long=float(row[0])
		lat=float(row[1])
		coords.append([long,lat])

	return coords

# sringify the output of a line segment
def _stringify(coords):
	newlist = []
	for long,lat in coords:
		newlist.append('[%s, %s]' % (long,lat))
	return '[' + ', '.join(newlist) + ']'

# get aligns for lines
def _get_aligns(data):
	total = []
	for row in data['st_asewkt'].values.tolist():
		coords = _get_coordstring(row)

		if isinstance(coords,list):
			coords = _stringify(coords)
		else:
			coords = '[0,0]'
		total.append(coords)
	return total

# stringifies the block geometry that will be 
# used to create the blocks cords
def _stringify_blocks(coords):
	newlist = []
	for long,lat in coords:
		newlist.append('[%s, %s]' % (long,lat))
	return '[[' + ', '.join(newlist) + ']]'


# decodes each geohash forms an alignment
# and stringifies the correndents in one op
def __get_alignment_geohash_bounds(ghash):
	lat,long,latdelta,longdelta = geohash.decode_exactly(ghash)
	p1 = [long-longdelta,lat-latdelta] # ll
	p2 = [long-longdelta,lat+latdelta] # ul
	p3 = [long+longdelta,lat+latdelta] # ur
	p4 = [long+longdelta,lat-latdelta] # lr
	coords = [p1,p2,p3,p4,p1]
	extrema_bounds = {'n':lat+latdelta,'s':lat-latdelta,'e':long+longdelta,'w':long-longdelta}
	boundslist = [[extrema_bounds['w'],extrema_bounds['n']],[extrema_bounds['e'],extrema_bounds['s']]]
	boundslist = _stringify(boundslist)
	coords = '[' + _stringify(coords) + ']'
	return coords,boundslist

# decodes each geohash forms an alignment
# and stringifies the correndents in one op
def _get_alignment_geohash(ghash):
	lat,long,latdelta,longdelta = geohash.decode_exactly(ghash)
	p1 = [long-longdelta,lat-latdelta] # ll
	p2 = [long-longdelta,lat+latdelta] # ul
	p3 = [long+longdelta,lat+latdelta] # ur
	p4 = [long+longdelta,lat-latdelta] # lr
	coords = [p1,p2,p3,p4,p1]
	return '[' + _stringify(coords) + ']'

def _get_alignment_cardinals(data):
	newlist = []
	for n,s,e,w in data[['NORTH','SOUTH','EAST','WEST']].values.tolist():
		p1 = [w,s] # ll
		p2 = [w,n] # ul
		p3 = [e,n] # ur
		p4 = [e,s] # lr
		coords = [p1,p2,p3,p4,p1]
		coords = '[' + _stringify(coords) + ']'
		newlist.append(coords)
	data['COORDS'] = newlist
	return data

def _get_header_without(header,latheader,longheader):
	newlist = []
	for row in header:
		if not row == latheader and not row == longheader and not row == 'COMB':
			newlist.append(row)
	return newlist



# getting coord field for one line in dataframe
# used for make_line	
def _get_cord_one_line(data,latheader,longheader):
	# getting the combined field
	data['COMB'] = '[' + data[longheader].astype(str) + ',' + data[latheader].astype(str) + ']'
	
	# getting extrema values
	north,south,east,west = data[latheader].max(),data[latheader].min(),data[longheader].max(),data[longheader].min()
	extrema_bounds = {'n':north,'s':south,'e':east,'w':west}


	# getting bounds list
	boundslist = [[extrema_bounds['w'],extrema_bounds['n']],[extrema_bounds['e'],extrema_bounds['s']]]
	boundslist = _stringify(boundslist)

	# getting coords
	coords = ', '.join(data['COMB'].values.tolist())
	coords = '[%s]' % coords

	# slicing the first row and adding coords field
	newheader = _get_header_without(data.columns.values.tolist(),latheader,longheader)
	data = data[newheader]
	data = data[:1]
	data['coords'] = coords
	data['bounds'] = boundslist
	return data


# analyzes each column in a dataframe header
def _analyze_fields(columns):
	count = 0
	zoombool = False
	headerdict = {}
	optionsdict = {}
	properties = []
	newcolumns = []
	positionbool = False
	startval = 0
	endval = 0
	bounds = False
	for row in columns:
		usedbool = False
		compressedrow = row
		if 'lat' in str(row).lower():
			latheader = compressedrow
			optionsdict['latitude'] = latheader
			usedbool = True
			if positionbool == False:
				startval = count
				positionbool = True
			else:
				endval == count
		elif 'long' in str(row).lower():
			longheader = compressedrow
			usedbool = True
			optionsdict['longitude'] = longheader 
			if positionbool == False:
				startval = count
				positionbool = True
			else:
				endval = count
		elif 'st_asewkt' in str(row).lower() or 'coords' in str(row).lower():
			geomheader = compressedrow
			optionsdict['geometry'] = compressedrow
			usedbool = True		
		elif 'colorkey' in str(row).lower() or str(row).lower() == 'color':
			colorkeyheader = compressedrow
			optionsdict['color'] = compressedrow
		elif 'zoomkey' in str(row).lower():
			if zoombool == False:
				zoombool = True
				zoomkey1 = compressedrow
			else:
				zoomkey2 = compressedrow
				optionsdict['zooms'] = [zoomkey1,zoomkey2]	
		elif 'weight' in str(row).lower():
			weightheader = compressedrow
			optionsdict['weight'] = compressedrow 
		elif 'opacity' in str(row).lower():
			opacityheader = compressedrow
			optionsdict['opacity'] = compressedrow 
		elif 'radius' in str(row).lower():
			radiusheader = compressedrow
			optionsdict['radius'] = compressedrow 
		elif 'bounds' in str(row).lower():
			boundsheader = compressedrow
			optionsdict['bounds'] = compressedrow

		# adding entry to dictionary
		headerdict[compressedrow] = row

		if usedbool == False:
			properties.append(compressedrow)

		count += 1

		newcolumns.append(compressedrow)

	return headerdict,properties,newcolumns,optionsdict,[startval,endval]


# analyzes the type of geojson being constructed then returns adequate geometry
def _analyze_type(optionsdict,geompositions,newcolumns,type):

	if type == 'line':
		latitude,longitude = optionsdict['latitude'],optionsdict['longitude']
		geoms = [longitude,latitude]	
	elif type == 'postgis_lines' or type == 'postgis_polygons':	
		geoms =['coords']
		#geoms = [optionsdict['geometry']]
	elif type == 'polygon':
		latitude,longitude = optionsdict['latitude'],optionsdict['longitude']
		geoms = [longitude,latitude]
	elif type == 'blocks':
		geoms = newcolumns[geompositions[0]:geompositions[1]+1]
	elif type == 'points':
		latitude,longitude = optionsdict['latitude'],optionsdict['longitude']
		geoms = [longitude,latitude]

	newdict = {}
	ind = 0
	# adding optionkeys
	for row in optionsdict.keys():
		if not row == 'latitude' and not row == 'longitude' and not row == 'geometry':
			newdict[row] = optionsdict[row]
	# adding zoom key
	if ind == 2:
		newdict['zooms'] = [zoomkey1,zoomkey2]
	return geoms,newdict

# gets a bound from data that will be written into 
# mask file
def get_first_bounds(data,type,pipegl=False):
	if type == 'lines' or type == 'line':
		bounds = data['coords'][:1].values.tolist()
		bounds = bounds[0]
		bounds = bounds[1:-1]
		bounds = bounds.encode('utf-8')

		bounds = str.split(n(bounds),'],')[0]
		bounds = bounds[1:]
		long,lat = str.split(bounds,',')
		long,lat = float(long),float(lat)
		return [long,lat]
	if type == 'points':
		if pipegl == True:
			long = data['LONG'][:1].values.tolist()[0]
			lat = data['LAT'][:1].values.tolist()[0]
		
		else:
			bounds = data['coord'][:1].values.tolist()[0]
			long,lat = str.split(bounds[1:-1],',')
			long,lat = float(long),float(lat)
		return [long,lat]
	if type == 'blocks':
		try:
			ghash = data['GEOHASH'][:1].values.tolist()[0]
			lat,long = geohash.decode(ghash)
		except:
			try:
				xyz = data['XYZ'].iloc[0]
				x,y,z = str.split(xyz,'/')
				bds = mercantile.bounds(int(x),int(y),int(z))
				long,lat = bds.east,bds.north
			except:
				lat,long = data[['NORTH','EAST']][:1].values.tolist()[0]
		return [long,lat]
	if type == 'polygons':
		bounds = data.iloc[0]['COORDS']
		bounds = bounds[2:-2]
		
		# logic for bounds spacing
		if ' ' in bounds:
			bounds = str.split(bounds,'], [')
		else: 
			bounds = str.split(bounds,'],[')

		long,lat = str.split(bounds[0][1:],',')
		long,lat = 	float(long),float(lat)
		return [long,lat]


# sniffs each dataframe header and the type and constructs
# a mask file that can be used with pipeleaflet
# this mask file carries over style and formats without inputs
# on the pipeleaflet end
def _sniff_mask_fields(data,type,filename,firstbound):
	# getting columns
	columns = data.columns.values.tolist()

	# getting all values used in logic intereptation
	headerdict,properties,newcolumns,optionsdict,geompositions = _analyze_fields(columns)

	# analyzing the options dictionary for each type
	geoms,optionsdict = _analyze_type(optionsdict,geompositions,newcolumns,type)

	propertydict = {}
	for row in properties:
		propertydict[headerdict[row]] = row
	alignpos = 0
	geompos = 0

	# analyzing type if type is postgis lines
	if type == 'postgis_lines' or type == 'postgis_polygons':
		count = 0
		newpropertydict = {}
		for row in data.columns:
			if row == 'geom':
				geompos = count
			elif row == 'st_asewkt':
				alignpos = count
			elif row == 'coords':
				geompos,alignpos = count,count
			else:
				newpropertydict[str(row)] = str(row)
			count += 1
		newgeom = [geoms[0],[geompos,alignpos]]
		geoms = newgeom
		propertydict = newpropertydict

	# adding firstbounds to options dict
	optionsdict['firstbound'] = firstbound

	propertydict['options'] = optionsdict
	if type == 'points':
		maskjson = {"geometry": {"type": "Point", "coordinates": []}, "type": "Feature", "properties": propertydict}
	elif type == 'postgis_lines':
		maskjson = {"geometry": {"type": "LineString", "coordinates": []}, "type": "Feature", "properties": propertydict}
	elif type == 'postgis_polygons':
		maskjson = {"geometry": {"type": "Polygon", "coordinates": []}, "type": "Feature", "properties": propertydict}
	elif type == 'blocks':
		maskjson = {"geometry": {"type": "Polygon", "coordinates": []}, "type": "Feature", "properties": propertydict}
	elif type == 'line':
		maskjson = {"geometry": {"type": "LineString", "coordinates": []}, "type": "Feature", "properties": propertydict}
	elif type == 'polygon':
		maskjson = {"geometry": {"type": "Polygon", "coordinates": []}, "type": "Feature", "properties": propertydict}
	
	filename = str.split(str(filename),'.')[0]
	filename = filename + '.json'

	with open(filename,'w') as newgeojson:
		json.dump(maskjson,newgeojson)
	#print('Wrote %s to json.' % filename)

	data.columns = newcolumns
	
	return data,geoms



# creates a polygon dataframe ready to be used by nlgeojson
def _create_polygon_dataframe(data,idfield='AREA'):
	if 'COORDS' in data.columns.values: coordval = 'COORDS' 
	else: coordval = 'coords'
	
	# grabbing only part of df needed
	tempdf = data[data[coordval].str.contains('|',regex=False) == True]
	data = data[data[coordval].str.contains('|',regex=False) == False]


	if len(tempdf) != 0:
		dummydf = pd.DataFrame(tempdf.COORDS.str.split('|').tolist(), index=tempdf.AREA).stack()

		dummydf = dummydf.reset_index()
		dummydf = dummydf[['AREA',0]]
		dummydf.columns = ['AREA',coordval]

		# setting the index and slicing correct tempdf
		tempdf = tempdf.set_index(idfield)
		tempdf = tempdf.drop(coordval,axis=1).loc[dummydf.AREA.values]

		# setting the values from the index and dropping the index
		dummydf[tempdf.columns] = tempdf.reset_index().drop('AREA',axis=1)



		data = pd.concat([data,dummydf],ignore_index=True)
	return data

# gets the shape type of a geodataframe
def _get_shapetype(geometry):
	geometry = str(type(geometry))
	if 'LineString' in geometry:
		return 'lines'		
	elif 'Polygon' in geometry:
		return 'polygons'
	elif 'Point' in geometry:
		return 'points'


# given a point1 x,y and a point2 x,y returns distance in miles
# points are given in long,lat geospatial cordinates
def _distance(point1,point2):
	point1 = np.array(point1)
	point2 = np.array(point2)
	return np.linalg.norm(point1-point2)


def string_me(geom):
	geom = str(geom)
	return geom.replace('(','[').replace(')',']').replace('],]',']]')

def map_me(vals,total):
	index,geom = vals['index'],vals.geometry
	try:
		mapped = mapping(geom)
	except:
		print 'i pased'
	#print mapped
	if mapped['type'] == 'MultiLineString':
		newvals = [string_me(i) for i in mapped['coordinates']]
		total += zip([index]*len(newvals),newvals)
	if mapped['type'] == 'MultiPolygon':
		newvals = [string_me(i) for i in mapped['coordinates']]
		total += zip([index]*len(newvals),newvals)
	if mapped['type'] == 'MultiPoint':
		newvals = [string_me(i) for i in mapped['coordinates']]
		total += zip([index]*len(newvals),newvals)
	if mapped['type'] == 'Point':
		total += [(index,string_me(mapped['coordinates']))]
	if mapped['type'] == 'LineString':
		total += [(index,string_me(mapped['coordinates']))]
	if mapped['type'] == 'Polygon':
		total += [(index,string_me(mapped['coordinates']))]

# creating nldf from geodf
def geodf2nldf(data):
	#print data
	# resetting index and shit
	data['BOOL'] = data['geometry'].map(lambda x:str(type(x)) != '''<class 'shapely.geometry.linestring.LineString'>''')
	data = data[data.BOOL == False]

	data = data.drop('BOOL',axis=1)
	data = data.to_crs({'init': 'epsg:4326'})
	datanew = data.reset_index()[['index','geometry']]
	total = []

	# getting values
	vals = datanew[['index','geometry']].apply(map_me,total=total,axis=1).values.tolist()
	datanew = pd.DataFrame(total,columns=['index','COORDS'])

	# adding fields
	data = data.drop('geometry',axis=1)
	data = datanew.merge(data,left_on='index',right_index=True)
	data = data.drop(['index'],axis=1)
	return data

# reads a geobuf file
def read_geobuf(filename):
	p1 = subprocess.Popen(["read_geobuf", filename], shell=False,stdout=subprocess.PIPE)
	data = pd.read_csv(p1.stdout,header=None,sep=',',error_bad_lines=False)
	#data.columns = data.iloc[-1].values.tolist()
	#data = data[:-1]
	return data

# reads a geojson file
def read_geojson(filename):
	if filename.endswith('geobuf'):
		return read_geobuf(filename)
	p1 = subprocess.Popen(["read_geojson", filename], shell=False,stdout=subprocess.PIPE)
	data = pd.read_csv(p1.stdout,header=None,sep='\t',error_bad_lines=False)
	data.columns = data.iloc[-1].values.tolist()
	data = data[:-1]
	return data

# get delimter
def get_delimiter(line_delimited):
	if line_delimited:
		return '\n'
	else:
		return ', '