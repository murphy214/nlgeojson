import numpy as np
import geohash

# makes the cordinates for each set of pointss
def make_coord(data):
	ind1 = False
	ind2 = False
	for row in data.columns.values.tolist():
		if 'lat' in str(row).lower() and ind1 == False:
			ind1 = True
			latheader = row
		if 'long' in str(row).lower() and ind2 == False:
			ind2 = True
			longheader = row
	data['coord'] = '[' + data[longheader].astype(str) + ', ' + data[latheader].astype(str) + ']'
	return data

# extracting the raw coords from postgis output
# this is used to get the stringified cords
# and ultimately is updated as field in postgres
def get_coordstring(geometry):
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
def stringify(coords):
	newlist = []
	for long,lat in coords:
		newlist.append('[%s, %s]' % (long,lat))
	return '[' + ', '.join(newlist) + ']'

# get aligns for lines
def get_aligns(data):
	total = []
	for row in data['st_asewkt'].values.tolist():
		coords = get_coordstring(row)

		if isinstance(coords,list):
			coords = stringify(coords)
		else:
			coords = '[0,0]'
		total.append(coords)
	return total

# stringifies the block geometry that will be 
# used to create the blocks cords
def stringify_blocks(coords):
	newlist = []
	for long,lat in coords:
		newlist.append('[%s, %s]' % (long,lat))
	return '[[' + ', '.join(newlist) + ']]'


# decodes each geohash forms an alignment
# and stringifies the correndents in one op
def get_alignment_geohash(ghash):
	lat,long,latdelta,longdelta = geohash.decode_exactly(ghash)
	p1 = [long-longdelta,lat-latdelta] # ll
	p2 = [long-longdelta,lat+latdelta] # ul
	p3 = [long+longdelta,lat+latdelta] # ur
	p4 = [long+longdelta,lat-latdelta] # lr
	coords = [p1,p2,p3,p4,p1]
	return stringify(coords) 


# given a dataframe containg the geometry coords 
# writes a geojson file out from text
def make_blocks(data,filename):
	data = data.fillna(value = 0)
	data['COORDS'] = data['GEOHASH'].map(get_alignment)

	newheaders = []
	# removing fields that don't matter
	for row in data.columns.values.tolist():
		if not row == 'geom' and not row == 'COORDS' and not 'st_asewkt' == row:
			newheaders.append(row)

	#bl.make_postgis_lines(data[:10],'lines.geojson')

	properties = data[newheaders].to_json(orient='records')
	properties = str.split(properties,'},')
	coords = data['COORDS'].values.tolist()

	args = zip(coords,properties)
	newlist = []
	count = 0
	for coord,props in args:
		if count == 0:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[1:]+'}')
		elif count == len(args)-1:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[:-1])
		else:
			line = '''{"geometry": {"type": "Polygon", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props+'}')

		count += 1
		newlist.append(line)
		

	middle = ', '.join(newlist)
	total = '{"type": "FeatureCollection", "features": [' + middle + ']}'


	with open(filename,'wb') as f:
		f.write(total)
	print 'Wrote %s filename to csv file.' % filename


# given a dataframe containg the geometry coords 
# writes a geojson file out from text
def make_lines(data,filename):
	data = data.fillna(value = 0)

	newheaders = []
	# removing fields that don't matter
	for row in data.columns.values.tolist():
		if not row == 'geom' and not row == 'COORDS' and not 'st_asewkt' == row:
			newheaders.append(row)

	#bl.make_postgis_lines(data[:10],'lines.geojson')

	properties = data[newheaders].to_json(orient='records')
	properties = str.split(properties,'},')
	coords = data['coords'].values.tolist()

	args = zip(coords,properties)
	newlist = []
	count = 0
	for coord,props in args:
		if count == 0:
			line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[1:]+'}')
		elif count == len(args)-1:
			line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[:-1])
		else:
			line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props+'}')

		count += 1
		newlist.append(line)

	middle = ', '.join(newlist)
	total = '{"type": "FeatureCollection", "features": [' + middle + ']}'

	with open(filename,'wb') as f:
		f.write(total)
	print 'Wrote %s filename to csv file.' % filename


# makes points using text sequences
def make_points(data,filename):
	data = data.fillna(value=0)

	data = make_coord(data)
	coords = data['coord'].values.tolist()
	properties = str(data.to_json(orient='records')).replace('\/','/')
	properties = str.split(properties[1:-1],'},')
	args = zip(coords,properties)
	newlist = []
	count = 0
	for coord,props in args:
		if count == 0:
			pointline = '''{"geometry": {"type": "Point", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[1:]+'}')
			#line = '''{"geometry": {"type": "LineString", "coordinates": %s}, "type": "Feature", "properties": %s}''' % (coord,props[1:]+'}')
		elif count == len(args)-1:
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
	total = total[:152] + '{' + total[152:]
	with open(filename,'w') as f:
		f.write(total)
	print 'Wrote geojson file to %s.' % filename

