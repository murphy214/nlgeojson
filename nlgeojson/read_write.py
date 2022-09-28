from io import BytesIO, StringIO
import subprocess
import pandas as pd 


# given a dataframe containg the geometry coords 
# writes a geojson file out from text
def write_file(
        df,
		filename, # name of output file
	):
    """
    """
    # fill all missing data in dataframe
    df = df.fillna(value = '')

    drop_cols = [i for i in df.columns if i in ['Geometry','Bounds','Type']]
    coords = df['Geometry'].values.tolist()
    df = df.drop(drop_cols,axis=1)

    properties = df.to_json(orient='records')
    properties = str.split(properties,'},')
    properties[0] = properties[0][1:]
    properties[-1] = properties[-1][:-1]
    # newlist = ['''{"geometry": %s, "type": "Feature", "properties": %s}}''' % (coord,props) for coord,props in zip(coords,properties)]
    total = '{"type": "FeatureCollection", "features": [' + ','.join(['''{"geometry": %s, "type": "Feature", "properties": %s}}''' % (coord,props) for coord,props in zip(coords,properties)]) + ']}'

	# replacing thte bounds signitaures made earlier

    with open(filename,'w') as f:
        f.write(total)


def read_file(filename):
    result = subprocess.run(['geobuf', 'csv','-f',filename], stdout=subprocess.PIPE)
    df = pd.read_csv(BytesIO(result.stdout))
    return df 



