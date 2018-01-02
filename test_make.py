import nlgeojson as nl
import pandas as pd

def add_fields(data):
	columns = data.columns.values.tolist()
	for i in 'abcdefg':
		data[i] = i
	return data,columns


# tests the make_lines function
def test_make_lines():
	# getting test output file
	with open('test_data/test_lines.geojson','rb') as f:
		expected = f.read()

	data = pd.read_csv('test_data/roads.csv')
	vals = nl.make_lines(data,'',test=True)
	assert expected == vals

# tests the make_lines function
def test_make_points():
	# getting test output file
	with open('test_data/test_points.geojson','rb') as f:
		expected = f.read()

	data = pd.read_csv('test_data/points.csv')
	vals = nl.make_points(data,'',test=True)
	assert expected == vals

# tests the make_blocks function
def test_make_blocks():
	# getting test output file
	with open('test_data/test_blocks.geojson','rb') as f:
		expected = f.read()

	data = pd.read_csv('test_data/points.csv')
	vals = nl.make_blocks(data,'',test=True)
	assert expected == vals

# tests the make_blocks function
def test_make_polygons():
	# getting test output file
	with open('test_data/test_polygons.geojson','rb') as f:
		expected = f.read()

	data = pd.read_csv('test_data/polygons.csv')
	vals = nl.make_polygons(data,'',test=True)
	assert expected == vals


# tests the make_lines function
def test_make_lines_keep():
	# getting test output file
	with open('test_data/test_lines.geojson','rb') as f:
		expected = f.read()

	data = pd.read_csv('test_data/roads.csv')
	data,columns = add_fields(data)
	vals = nl.make_lines(data,'',test=True,keep_columns=columns)
	assert expected == vals

# tests the make_lines function
def test_make_points_keep():
	# getting test output file
	with open('test_data/test_points.geojson','rb') as f:
		expected = f.read()

	data = pd.read_csv('test_data/points.csv')
	data,columns = add_fields(data)
	vals = nl.make_points(data,'',test=True,keep_columns=columns)
	assert expected == vals

# tests the make_blocks function
def test_make_blocks_keep():
	# getting test output file
	with open('test_data/test_blocks.geojson','rb') as f:
		expected = f.read()

	data = pd.read_csv('test_data/points.csv')
	data,columns = add_fields(data)
	vals = nl.make_blocks(data,'',test=True,keep_columns=columns)
	assert expected == vals

# tests the make_blocks function
def test_make_polygons_keep():
	# getting test output file
	with open('test_data/test_polygons.geojson','rb') as f:
		expected = f.read()

	data = pd.read_csv('test_data/polygons.csv')
	data,columns = add_fields(data)
	vals = nl.make_polygons(data,'',test=True,keep_columns=columns)
	assert expected == vals