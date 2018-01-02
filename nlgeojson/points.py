import pandas as pd
from misc import get_first_bounds,_sniff_mask_fields,_make_coord,get_delimiter

# 
def make_pt_coord(x,longitude,latitude):
	return '[%s,%s]' % (str(x[longitude]),str(x[latitude]))

# makes points using text sequences
def make_points(
		data, # dataframe of data
		filename, # output filename
		raw=False, # raw output for small talk
		mask=False, # create mask file for html creation
		bounds=False, # add bounds field
		test=False, # not sure
		latitude=False, # latidude field
		longitude=False, # longitude field
		keep_columns=False, # columns to keep
		line_delimited=False, # whether or not return raw values by line of features
	):
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

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'points')		
		_sniff_mask_fields(data,'points',filename,firstbounds)

	# filling in all missing data in df
	data = data.fillna(value=0)

	# getting latitude and longitude if needed
	if latitude == False or longitude == False:
		ind1 = False
		ind2 = False
		for row in data.columns.values.tolist():
			if 'lat' in str(row).lower() and ind1 == False:
				ind1 = True
				latitude = row
			if 'lon' in str(row).lower() and ind2 == False:
				ind2 = True
				longitude = row
			if 'lng' == str(row):
				ind2 = True
				longitude = row
	coords = data.loc[:][[longitude,latitude]].apply(make_pt_coord,axis=1,latitude=latitude,longitude=longitude)
	#print coords

	#data = _make_coord(data,latlongheaders)
	if bounds == True:
		data['bounds'] = '/bounds/' + data['coord'] + '/bounds/'

	# logic for keeping columns or not
	if keep_columns != False:
		drop_columns = [i for i in data.columns if not i in keep_columns]
	else:
		drop_columns = []
	drop_columns += [latitude,longitude]
	data = data.drop(drop_columns,axis=1)

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
	middle = get_delimiter(line_delimited).join(newlist)
	if raw == False:
		# start of the geojson
		start = '{"type": "FeatureCollection", "features": ['

		# creating middle from the newlist

		total = start + middle + ']}' 
	else:

		total = middle

	if bounds == True:
		total = total.replace('"/bounds/','')
		total = total.replace('/bounds/"','')

	if test == False and raw == False:
		with open(filename,'w') as f:
			f.write(total)
		#print('Wrote %s filename to geojson file.' % filename)
	elif test == True:
		return total
	elif raw == True:
		return total