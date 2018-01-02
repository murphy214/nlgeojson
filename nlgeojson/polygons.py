import pandas as pd
from misc import _create_polygon_dataframe,get_first_bounds,_sniff_mask_fields,get_delimiter

# given a dataframe containg the geometry coords 
# writes a geojson file out from text
def make_polygons(
		data, # dataframe of data
		filename, # output filename
		raw=False, # raw output for small talk
		mask=False, # create mask file for html creation
		boundsbool=False, # add bounds field
		test=False, # not sure
		linebool=False, # not sure
		keep_columns=False, # columns to keep
		line_delimited=False, # whether or not return raw values by line of features
	):
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

	# converting string to utf-8 if not already
	#data['COORDS'] = data['COORDS'].str.encode('utf-8')

	# creating polygon dataframe
	data = _create_polygon_dataframe(data)

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'polygons')
		_sniff_mask_fields(data,'postgis_polygons',filename,firstbounds)

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
		if not rowtest == 'geom' and not rowtest == 'coord' and not 'st_asewkt' == rowtest:
			newheaders.append(row)
		if 'coord' in rowtest:
			coordsbool = True
			coordval = row
		if rowtest == 'st_asewkt':
			stbool = True

	# logic for keeping columns or not
	if keep_columns != False:
		drop_columns = [i for i in data.columns if not i in keep_columns]
	else:
		drop_columns = []

	drop_columns.append(coordval)
	# getting coords
	if coordsbool == True:
		coords = data[coordval].values.tolist()

	# dropping the relavant columns
	data = data.drop(drop_columns,axis=1)

	properties = data.to_json(orient='records')
	properties = str.split(properties,'},')


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

	middle = get_delimiter(line_delimited).join(newlist)
	if raw == True:
		total = middle
	else:
		total = '{"type": "FeatureCollection", "features": [' + middle + ']}'


	# logic for if line is true
	if linebool == True:
		return total[:-6]

	# replacing thte bounds signitaures made earlier
	if boundsbool == True:
		total = total.replace('"@bounds@','')
		total = total.replace('@bounds@"','')

	if test == False and raw == False:
		with open(filename,'w') as f:
			f.write(total)
		#print('Wrote %s filename to geojson file.' % filename)
	elif test == True:
		return total
	elif raw == True:
		return total