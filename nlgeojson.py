import sys
from future.utils import bytes_to_native_str as n
import numpy as np
import geohash
import json
import itertools
import time
import pandas as pd
import future

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
			lat,long = data[['NORTH','EAST']][:1].values.tolist()[0]
		return [long,lat]
	if type == 'polygons':
		print(data)
		bounds = data.iloc[0]['COORDS']
		bounds = bounds[2:-2]
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
	# creating dummy datafrrame
	dummydf = pd.DataFrame(data.COORDS.str.split('|').tolist(), index=data.AREA).stack()

	dummydf = dummydf.reset_index()
	dummydf = dummydf[['AREA',0]]
	dummydf.columns = ['AREA','COORDS']

	# setting the index and slicing correct data
	data = data.set_index(idfield)
	data = data.drop('COORDS',axis=1).loc[dummydf.AREA.values]

	# setting the values from the index and dropping the index
	dummydf[data.columns] = data.reset_index().drop('AREA',axis=1)

	return dummydf

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


# given a dataframe containg the geometry coords 
# writes a geojson file out from text
def make_blocks(data,filename,**kwargs):
	""" Creates and writes blocks geojson from either geohashs or extrema columns.
	(SEE NOTES.)

	Args:
		data: a dataframe with a properly configured coords column (SEE NOTES)
		filename: the filename of either geojson or kml filetype
		*mask: kwarg that writes a json mask for output geojson for quick html parsing.

	Returns:
		Writes a geojson file to disk

	NOTES: This function accepts two types of input column(s). Either a 'GEOHASH' column
	which will decode your square within the function. Or having the fields:
	'NORTH','SOUTH','EAST','WEST' in your dataframe is also acceptable.
 	"""
	# lazy
	if filename == '':
		filename = 'blocks.geojson'

	mask = False
	bounds = False
	cardinals = False
	test = False
	for key,value in kwargs.items():
		if key == 'mask':
			mask = value
		if key == 'bounds':
			bounds = value
		if 'test' == key:
			test = value

	# testing for north east, south cardinal directonals
	for row in data.columns.values.tolist():
		if str(row).lower() == 'north':
			cardinals = True



	# filling in missing data
	data = data.fillna(value = 0)
	# logic for if bounds is equal to true
	if bounds == True:
		holder = pd.DataFrame(holder.values.tolist(),columns=['COORDS','bounds'])
		data[['COORDS','bounds']] = holder[['COORDS','bounds']]
		data['bounds'] = '@bounds@' + data['bounds'] + '@bounds@'
	else:
		if cardinals == True:
			data = _get_alignment_cardinals(data)
		else:
			data['COORDS'] = data['GEOHASH'].map(_get_alignment_geohash)

	newheaders = []
	# removing fields that don't matter
	for row in data.columns.values.tolist():
		if not row == 'geom' and not row == 'COORDS' and not 'st_asewkt' == row:
			if not 'north' in str(row).lower() and not 'south' in str(row).lower():
				if not 'west' in str(row).lower() and not 'east' in str(row).lower():
					newheaders.append(row)

	#bl.make_postgis_lines(data[:10],'lines.geojson')

	properties = data[newheaders].to_json(orient='records')
	properties = str.split(properties,'},')
	coords = data['COORDS'].values.tolist()

	newlist = []
	count = 0
	for coord,props in zip(coords,properties):
		if count == 0:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[1:]+'}')
		elif count == len(properties)-1:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[:-1])
		else:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props+'}')

		count += 1
		newlist.append(line)
		

	middle = ', '.join(newlist)
	total = '{"type": "FeatureCollection", "features": [' + middle + ']}'


	# replacing thte bounds signitaures made earlier
	if bounds == True:
		total = total.replace('"@bounds@','')
		total = total.replace('@bounds@"','')

	if test == False:
		with open(filename,'w') as f:
			f.write(total)
		#print('Wrote %s filename to geojson file.' % filename)
	elif test == True:
		return total

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'blocks')		
		_sniff_mask_fields(data,'blocks',filename,firstbounds)
	

# given a dataframe containg the geometry coords 
# writes a geojson file out from text
def make_lines(data,filename,**kwargs):
	""" Creates and writes lines geojson from a postgis / coords table.
	(SEE NOTES.)

	Args:
		data: a dataframe with a properly configured coords column (SEE NOTES)
		filename: the filename of either geojson or kml filetype
		*mask: kwarg that writes a json mask for output geojson for quick html parsing.

	Returns:
		Writes a geojson file to disk

	NOTES: This function uses the coords column or a column using postgis st_asewkt function as
	your column title to extract coordinates for just place them in cleanly if your coordinates are already in
	[[x1,y1],[x2,y2]] format within a string.
 	"""
	# lazy
	if filename == '':
		filename = 'lines.geojson'

	mask = False
	boundsbool = False
	linebool = False
	test = False
	for key,value in kwargs.items():
		if 'mask' == key:
			mask = value
		if 'linebool' == key:
			linebool = value
		if 'test' == key:
			test = value

	# checking for the bounds bool
	for row in data.columns.values.tolist():
		if row == 'bounds':
			boundsbool = True

	# adding mask to bounds bool so it can be replace later
	if boundsbool == True:
		data['bounds'] = '@bounds@' + data['bounds'] + '@bounds@'
	# fill all missing data in dataframe
	data = data.fillna(value = 0)

	newheaders = []
	stbool = False
	coordsbool = False
	# removing fields that don't matter
	for row in data.columns.values.tolist():
		if not row == 'geom' and not row == 'coords' and not 'st_asewkt' == row:
			newheaders.append(row)
		if row == 'coords':
			coordsbool = True
		if row == 'st_asewkt':
			stbool = True


	properties = data[newheaders].to_json(orient='records')
	properties = str.split(properties,'},')
	if coordsbool == True:
		coords = data['coords'].values.tolist()
	elif coordsbool == False and stbool == True:
		coords = _get_aligns(data)

	newlist = []
	count = 0
	for coord,props in zip(coords,properties):
		if count == 0:
			line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[1:]+'}')
		elif count == len(properties)-1:
			line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[:-1])
		else:
			line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props+'}')

		count += 1
		newlist.append(line)

	middle = ', '.join(newlist)
	total = '{"type": "FeatureCollection", "features": [' + middle + ']}'

	# replacing thte bounds signitaures made earlier
	if boundsbool == True:
		total = total.replace('"@bounds@','')
		total = total.replace('@bounds@"','')

	# logic for if line is true
	if linebool == True:
		return total[:-6]

	if test == False:
		with open(filename,'w') as f:
			f.write(total)
		#print('Wrote %s filename to geojson file.' % filename)
	elif test == True:
		return total

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'lines')
		_sniff_mask_fields(data,'postgis_lines',filename,firstbounds)

# makes a line using 'lat' and 'long' fields
def make_line(data,filename,**kwargs):
	""" Creates and writes line geojson from either geohashs or extrema columns.
	(SEE NOTES.)

	Args:
		data: a dataframe with a properly configured lat/long fields (SEE NOTES)
		filename: the filename of either geojson or kml filetype
		*mask: kwarg that writes a json mask for output geojson for quick html parsing.

	Returns:
		Writes a geojson file to disk

	NOTES: This function creates a single line from the LAT / LONG fields and carries
	repeated fields into the geojson.
 	"""
	mask = False
	test = False
	for key,value in kwargs.items():
		if 'mask' == key:
			mask = value
		if 'test' == key:
			test = value

	# getting lat and long header respectively
	for row in data.columns.values.tolist():
		if 'lat' in str(row).lower():	
			latheader = row
		if 'long' in str(row).lower():	
			longheader = row

	# adding the cord field and slicing the size to 1
	# this assumes all fields are duplicate which they should be anyway
	data = _get_cord_one_line(data,latheader,longheader)
	total = make_lines(data,filename,linebool=True)
	total = total + '}}]}'

	if test == False:
		with open(filename,'w') as f:
			f.write(total)
		#print('Wrote %s filename to geojson file.' % filename)
	elif test == True:
		return total

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'line')		
		_sniff_mask_fields(data,'postgis_lines',filename,firstbounds)

# makes points using text sequences
def make_points(data,filename,**kwargs):
	""" Creates and writes points geojson from LAT and LONG FIELDS.
	(SEE NOTES.)

	Args:
		data: a dataframe with a properly configured lat/long column (SEE NOTES)
		filename: the filename of either geojson or kml filetype
		*mask: kwarg that writes a json mask for output geojson for quick html parsing.

	Returns:
		Writes a geojson file to disk

	NOTES: This function searches each column header for fields that look 'LAT' or
	'LONG' respectively to create a point from the dataframe input.
 	"""
	# lazy
	if filename == '':
		filename = 'points.geojson'
	mask = False
	latlongheaders = False
	bounds = False
	test = False
	for key,value in kwargs.items():
		if key == 'mask':
			mask = value
		if key == 'latlongheaders':
			latlongheaders = value
		if key == 'bounds':
			bounds = value
		if 'test' == key:
			test = value

	# filling in all missing data in df
	data = data.fillna(value=0)

	data = _make_coord(data,latlongheaders)
	if bounds == True:
		data['bounds'] = '/bounds/' + data['coord'] + '/bounds/'


	coords = data['coord'].values.tolist()
	properties = str(data.to_json(orient='records')).replace('\/','/')
	properties = str.split(properties[1:-1],'},')
	newlist = []
	count = 0
	for coord,props in zip(coords,properties):
		if count == 0:
			pointline = '''{"geometry": {"type": "Point", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props+'}')
			#line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[1:]+'}')
		elif count == len(properties)-1:
			pointline = '''{"geometry": {"type": "Point", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props)		
			#line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[:-1])
		else:
			pointline = '''{"geometry": {"type": "Point", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props+'}')
			#line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props+'}')
		count += 1
		newlist.append(pointline)

	# start of the geojson
	start = '{"type": "FeatureCollection", "features": ['

	# creating middle from the newlist
	middle = ', '.join(newlist)

	total = start + middle + ']}' 

	if bounds == True:
		total = total.replace('"/bounds/','')
		total = total.replace('/bounds/"','')

	if test == False:
		with open(filename,'w') as f:
			f.write(total)
		#print('Wrote %s filename to geojson file.' % filename)
	elif test == True:
		return total

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'points')		
		_sniff_mask_fields(data,'points',filename,firstbounds)



# given a dataframe containg the geometry coords 
# writes a geojson file out from text
def make_polygons(data,filename,**kwargs):
	""" Creates and writes polygonstring for geojson from a polygon flat table.
	(SEE NOTES.)

	Args:
		data: a dataframe with a properly configured coords column (SEE NOTES)
		filename: the filename of either geojson or kml filetype
		*mask: kwarg that writes a json mask for output geojson for quick html parsing.

	Returns:
		Writes a geojson file to disk

	NOTES: This function accepts a flat dataframe output from polygon index
	which has a column configured like normal geojson coordinates as a _stringify
	but instead of configuring as a multipolygon uses '|' in the coordstirng to denote a newlist
	polygon area this abstraction allows for polygon usage and know need for a make_multipolygon()
	function when it really doesn't do much.
	"""
	# lazy
	if filename == '':
		filename = 'polygons.geojson'


	mask = False
	boundsbool = False
	linebool = False
	test = False
	for key,value in kwargs.items():
		if 'mask' == key:
			mask = value
		if 'linebool' == key:
			linebool = value
		if 'test' == key:
			test = value


	# converting string to utf-8 if not already
	#data['COORDS'] = data['COORDS'].str.encode('utf-8')

	# creating polygon dataframe
	data = _create_polygon_dataframe(data)
	print(data,'polygondf')

	# checking for the bounds bool
	for row in data.columns.values.tolist():
		if row == 'bounds':
			boundsbool = True

	# adding mask to bounds bool so it can be replace later
	if boundsbool == True:
		data['bounds'] = '@bounds@' + data['bounds'] + '@bounds@'
	# fill all missing data in dataframe
	data = data.fillna(value = 0)

	newheaders = []
	stbool = False
	coordsbool = False
	# removing fields that don't matter
	for row in data.columns.values.tolist():
		rowtest = str(row).lower()
		if not rowtest == 'geom' and not rowtest == 'coords' and not 'st_asewkt' == rowtest:
			newheaders.append(row)
		if rowtest == 'coords':
			coordsbool = True
		if rowtest == 'st_asewkt':
			stbool = True

	properties = data[newheaders].to_json(orient='records')
	properties = str.split(properties,'},')
	if coordsbool == True:
		coords = data['COORDS'].values.tolist()


	newlist = []
	count = 0
	for coord,props in zip(coords,properties):
		if count == 0:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[1:]+'}')
		elif count == len(properties)-1:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[:-1])
		else:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props+'}')

		count += 1
		newlist.append(line)

	middle = ', '.join(newlist)
	total = '{"type": "FeatureCollection", "features": [' + middle + ']}'


	# logic for if line is true
	if linebool == True:
		return total[:-6]

	# replacing thte bounds signitaures made earlier
	if boundsbool == True:
		total = total.replace('"@bounds@','')
		total = total.replace('@bounds@"','')

	if test == False:
		with open(filename,'w') as f:
			f.write(total)
		#print('Wrote %s filename to geojson file.' % filename)
	elif test == True:
		return total

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'polygons')
		_sniff_mask_fields(data,'postgis_polygons',filename,firstbounds)


def geodf_to_nldf(data,filename=False):
	""" From a geodataframe from geopandas returns a nlgeojson usable dataframe.
	(SEE NOTES.)

	Args:
		data: a geodataframe with consitantly typed shapes (i.e. eithe all points, all lines, or all polygons)
		filename: the outfile csv name if desired
	Returns:
		Either a nlgeojson dataframe or a nothing if written to disk.

	"""
	# getting the geometry
	geometry = data['geometry'].values.tolist()
	
	# getting the actual dataframe chunk
	newlist = []
	for i in data.columns:
		if not i == 'geometry':
			newlist.append(i)
	
	# getting all but the geometry
	data = data[newlist]
	
	# getting type
	shapetype = _get_shapetype(geometry[0])

	# logic for making a lines df
	if shapetype == 'lines':
		boolthing = False
		for i in data.columns:
			if 'gid' == i:
				boolthing = True
		if boolthing == False:
			data['gid'] = range(len(data))

		newlist = []
		count = 0
		for i in geometry:
			count += 1
			west,south,east,north = i.bounds 
			coords = []
			count = 0
			totaldistance = 0.
			for point in i.coords:
				if count == 0:
					count = 1
				else:
					dist = _distance(oldpoint,point)
					totaldistance += dist
				oldpoint = point
				coords.append([point[0],point[1]])

			newgeometries = '[%s]' % coords
			newlist.append([west,south,east,north,str(coords),totaldistance])
		newcolumns = ['WEST','SOUTH','EAST','NORTH','COORDS','MAXDISTANCE']
		data[newcolumns] = pd.DataFrame(newlist,columns=newcolumns)
	
	# logic for making a points df
	elif shapetype == 'points':
		newlist = []
		for i in geometry:
			newlist.append(i.coords[0])
		data[['LONG','LAT']] = pd.DataFrame(newlist,columns=['LONG','LAT'])
	# logic for making a polygons df
	elif shapetype == 'polygons':
		boolthing = False
		for i in data.columns:
			if 'AREA' == i:
				boolthing = True
		if boolthing == False:
			data['AREA'] = range(len(data))

		newlist = []
		count = 0
		ids = []
		for eacharea in geometry:
			geoms = []
			if 'MultiPolygon' in str(type(eacharea)):		
				for eachgeom in list(eacharea.geoms):
					exterior = str([list(i) for i in list(eachgeom.exterior.coords)])
					interior = str([(list([list(ii) for ii in list(i.coords)])) for i in list(eachgeom.interiors)])[1:-1]
					total = '[%s,%s]' % (exterior,interior)
					if total[-2] == ',':
						total = total[:-2] + ']'				
					geoms.append(total)
				total = '|'.join(geoms)
			else:
				exterior = str([list(i) for i in list(eacharea.exterior.coords)])
				interior = str([(list([list(ii) for ii in list(i.coords)])) for i in list(eacharea.interiors)])[1:-1]
				total = '[%s,%s]' % (exterior,interior)
				
				if total[-2] == ',':
					total = total[:-2] + ']'

			newlist.append(total)
			count += 1

		data['COORDS'] = newlist

	# outputting to csv if filename is input
	if not filename == False:
		data.to_csv(filename,index=False,encoding='utf-8')
	else:
		return data

	