import movingpandas as mpd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, MultiLineString
from scipy.spatial import cKDTree
import math

#convert to a line gdf
def convertToLineGDF(data):
    traj = data
    frame = traj.to_line_gdf()
    crs_frame = traj.to_point_gdf()

    crsf = crs_frame.crs
    frame = frame.set_crs(crsf)

    if frame.crs.to_epsg() != 3857:
        frame = frame.to_crs('EPSG:3857')
    else:
        frame = frame
    frame = frame.dissolve(by='trackId').reset_index()
    if ((int(frame.total_bounds[2]) - int(frame.total_bounds[0])) > 500000) | ((int(frame.total_bounds[3]) - int(frame.total_bounds[1])) > 500000):
        print("Study size is too large, please subset your data to an area smaller than 500,000 metres by 500,000 metres and try again. Try using a smaller number of individuals from the dataset. ")
        exit()
    print(frame)
    return frame

#perform operations on the array to format it for the TrajectoryCollection
def cellPointArray(geoframe, reshaped_array, xres, yres, input_qgs_rect):           

    #get the crs of the original geoframe to return it to the user as it was given
    geo_crs = geoframe.crs

    #compute the appropriate pixel size
    pixel_x_size = (input_qgs_rect.xMaximum() - input_qgs_rect.xMinimum()) / (reshaped_array.shape[1])
    pixel_y_size = (input_qgs_rect.yMaximum() - input_qgs_rect.yMinimum()) / (reshaped_array.shape[0])
    xmin = input_qgs_rect.xMinimum()
    ymin = input_qgs_rect.yMinimum()
    data = []

    #make a grid of x and y coordinates
    x_coords = np.arange(0, xres) * pixel_x_size + xmin
    y_coords = np.arange(yres - 1, -1, -1) * pixel_y_size + ymin

    #create a meshgrid
    x_mesh, y_mesh = np.meshgrid(x_coords, y_coords)

    #flatten into 1D arrays
    x_flattened = x_mesh.flatten()
    y_flattened = y_mesh.flatten()

    #calculate midpoints
    x_midpoints = x_flattened + (pixel_x_size / 2)
    y_midpoints = y_flattened + (pixel_y_size / 2)

    #create shapely points
    geometries = [Point(x, y) for x, y in zip(x_midpoints, y_midpoints)]

    #create a dictionary:key set for the bands
    band_data = {
            'band_1': reshaped_array[:, :, 2].flatten(),
            'band_2': reshaped_array[:, :, 1].flatten(),
            'band_3': reshaped_array[:, :, 0].flatten(),
            'band_4': reshaped_array[:, :, 3].flatten()
        }

    #append the geometry and band data to a geodataframe
    data = {'geometry': geometries, **band_data}
    df = gpd.GeoDataFrame(data, crs=geo_crs)

    # remove rows with missing geometry
    df = df[~df['geometry'].isnull()]

    #reproject just in case
    if df.crs != 'EPSG:3857':
        df = df.to_crs('EPSG:3857')

    return df, pixel_x_size, pixel_y_size

#combine the dataframes together
def computePointNearest(bandGdf, geoframe, pixel_x_size, pixel_y_size):

    maxBandValue = 255
    hypotenuse = math.sqrt((pixel_x_size*pixel_x_size) + (pixel_y_size*pixel_y_size))
    # Assuming you have two GeoDataFrames: points_gdf and multilinestrings_gdf

    # Create a spatial index for the points GeoDataFrame
    points_spatial_index = bandGdf.sindex

    # Define the distance threshold and average value column name
    distance_threshold = hypotenuse  # Adjust as per your requirement

    # Iterate over each multilinestring in the multilinestrings GeoDataFrame
    for idx, row in geoframe.iterrows():
        multilinestring = row['geometry']
        
        # Create a bounding box around the multilinestring with the distance threshold
        bounding_box = multilinestring.buffer(distance_threshold).bounds
        
        # Use the spatial index to find candidate points within the bounding box
        candidate_indices = list(points_spatial_index.intersection(bounding_box))
        candidate_points = bandGdf.iloc[candidate_indices]
        
        # Filter candidate points within the distance threshold from the multilinestring
        filtered_points = candidate_points[candidate_points.distance(multilinestring) <= distance_threshold]
        
        # Count the number of points within the distance threshold
        point_count = len(filtered_points)
        
        # Calculate the average value associated with the filtered points
        average_value = filtered_points['intensity'].mean()
        
        # Assign count and average value to the respective multilinestring
        geoframe.loc[idx, 'point_count'] = point_count
        geoframe.loc[idx, 'average_value'] = average_value
    # #extract coords
    # geoframe_coords = [(geom.x, geom.y) for geom in geoframe.geometry]

    # #extract coords
    # bandGdf_coords = [(geom.x, geom.y) for geom in bandGdf.geometry]

    # #create kdtree for searching
    # tree = cKDTree(bandGdf_coords)

    # #get nearest neighbors and distances
    # distances, indices = tree.query(geoframe_coords)

    # #assign the nearest neighbor distances to a new column
    # geoframe['nearest_distance'] = distances

    # #extract band values
    # band1_values = bandGdf.loc[indices, 'band_1'].tolist()
    # band2_values = bandGdf.loc[indices, 'band_2'].tolist()
    # band3_values = bandGdf.loc[indices, 'band_3'].tolist()
    # band4_values = bandGdf.loc[indices, 'band_4'].tolist()

    # #append the band values to the geoframe
    # geoframe['band_1'] = band1_values
    # geoframe['band_2'] = band2_values
    # geoframe['band_3'] = band3_values
    # geoframe['band_4'] = band4_values
    
    # #set radius for the distance to include/exclude
    # hypotenuse = math.sqrt((pixel_x_size*pixel_x_size) + (pixel_y_size*pixel_y_size))

    # #calculate intensity based on the band values and distances
    # selected_columns = ["band_1", "band_2", "band_3"]
    # geoframe['intensity'] = (geoframe[selected_columns].sum(axis=1) / (maxBandValue*3))

    # #if the distance is too far, set the values to na
    # criterion = geoframe['nearest_distance'] > (hypotenuse / 2)
    # geoframe.loc[criterion, ['band_1', 'band_2', 'band_3', 'intensity']] = np.nan
    exit()
    return geoframe




# merged_gdf = frame.dissolve(by='trackId').reset_index()
# merged_gdf['t'] = merged_gdf['t'].dt.strftime('%Y-%m-%d %H:%M:%S')
# merged_gdf['timestamps'] = merged_gdf['timestamps'].dt.strftime('%Y-%m-%d %H:%M:%S')
# merged_gdf['prev_t'] = merged_gdf['prev_t'].dt.strftime('%Y-%m-%d %H:%M:%S')

# print(merged_gdf.crs)

# traj = mpd.TrajectoryCollection(frame, "trackId", t="timestamps", crs=frame.crs)
# print(traj)
# exit()