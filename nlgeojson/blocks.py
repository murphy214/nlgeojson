import pandas as pd
from misc import get_first_bounds,_sniff_mask_fields,_get_alignment_cardinals,_get_alignment_geohash,get_delimiter

# given a dataframe containg the geometry coords 
# writes a geojson file out from text
def make_blocks(
		data, # dataframe data
		filename, # filename of output file
		raw=False, # raw output for smalltalk
		mask=False, # makes a mask file
		bounds=False, # creates a bounds field
		test=False, # not sure
		keep_columns=False, # keeps columns
		line_delimited=False, # whether or not return raw values by line of features
	):
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
 	cardinals,tilebool = False,False

	# lazy
	if filename == '':
		filename = 'blocks.geojson'

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'blocks')		
		_sniff_mask_fields(data,'blocks',filename,firstbounds)

	# testing for north east, south cardinal directonals
	for row in data.columns.values.tolist():
		if str(row).lower() == 'north':
			cardinals = True
		if str(row).lower() == 'xyz':
			# nto a good place at all to put it but trying to avoid 
			# circular imports if at all possible
			from mapkit import map_cards
			data = map_cards(data)
			tilebool = True


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
		elif tilebool == True:
			pass
		else:
			coords = data['GEOHASH'].map(_get_alignment_geohash).values.tolist()

	# logic for keeping columns or not
	if keep_columns != False:
		drop_columns = [i for i in data.columns if not i in keep_columns]
	else:
		drop_columns = []

	# logic for whether its needed to expicitly drop cardinals
	if cardinals == True or tilebool == True:
		drop_columns += ['NORTH','SOUTH','EAST','WEST']

	data = data.drop(drop_columns,axis=1)
	properties = data.to_json(orient='records')
	properties = str.split(properties,'},')
	#coords = data['COORDS'].values.tolist()

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

	if raw == False:
		total = '{"type": "FeatureCollection", "features": [' + middle + ']}'
	else:
		total = middle

	# replacing thte bounds signitaures made earlier
	if bounds == True:
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