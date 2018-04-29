import pandas as pd
from misc import get_first_bounds,_sniff_mask_fields,_get_aligns,get_delimiter

# given a dataframe containg the geometry column 
# writes a geojson file out from text
def make_geojson(
		data, # dataframe of data
		filename, # name of output file
		raw=False, # outputs the json in raw for smalltalk
		boundsbool=False, # boundsbool for whether or not to add bools
		linebool=False, # linebool 
		test=False, # not sure 
		mask=False, # creates a mask representive json for reading for html creation
		keep_columns=False, # columns to keep
		line_delimited=False, # whether or not return raw values by line of features
	):
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
		filename = 'fc.geojson'

	# handling if a styling mask will be used
	if mask == True:
		firstbounds = get_first_bounds(data,'blocks')		
		_sniff_mask_fields(data,'blocks',filename,firstbounds)

	# checking for the bounds bool
	for row in data.columns.values.tolist():
		if row == 'bounds':
			boundsbool = True

	# fill all missing data in dataframe
	data = data.fillna(value = "")

	# logic for keeping columns or not
	if keep_columns != False:
		drop_columns = [i for i in data.columns if not i in keep_columns]
	else:
		drop_columns = []

	# adding additoinal columns to drop
	drop_columns.append('Geometry')


	# dropping the columns and getting cooords
	coords = data['Geometry'].values.tolist()
	data = data.drop(drop_columns,axis=1)

    # creating the middle form a list compresion
    # dataframe to json lines 
	#print data.to_json(orient='records',lines=True)
	middle = get_delimiter(line_delimited).join(
        ['''{"geometry": %s, "type": "Feature", "properties": %s}''' % (geom,prop) \
            for prop,geom in zip(
                                    data.to_json(orient='records',lines=True).splitlines(),
                                    coords
                                )
        ])
    
	#properties = str.split(properties,'},')
    
	if raw == True:
		total = middle
	else:
		total = '{"type": "FeatureCollection", "features": [' + middle + ']}'

	if test == False and raw == False:
		with open(filename,'w') as f:
			f.write('{"type": "FeatureCollection", "features": [' + middle + ']}')
	elif test == True:
		return total
	if raw == True:
		return total



# makes a line using 'lat' and 'long' fields
def make_line(
		data, # datafraem data of a line
		filename, # filename of output file
		mask=True, # mask for creating mask file
		test=False, # not sure
	):
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


